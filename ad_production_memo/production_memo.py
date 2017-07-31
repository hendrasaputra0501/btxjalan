from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class production_memo(osv.osv):
	_name = "production.memo"
	_columns = {
		'name' : fields.char('No',size=50, readonly=True),
		'manufacturer' : fields.many2one('res.partner','Manufacturer'),
		'date_instruction' : fields.date('Date Order'),
		'sale_id' : fields.many2one('sale.order','Sales Order',readonly=True),
		'goods_lines' : fields.one2many('production.memo.line','memo_id','Goods'),
		'note' : fields.text('Note'),
		'state' : fields.selection([
			('cancel','Cancelled'),
			('draft','Draft'),
			('confirmed','Confirmed By Marketing'),
			('received','Received By Production')],'Status')
	}

	def _production_line_for(self, cr, uid, order_line):
		lsd = order_line.est_delivery_date!='False' and order_line.est_delivery_date or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		lsd = datetime.datetime.strptime(lsd,DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=-5)
		lsd = lsd.strftime(DEFAULT_SERVER_DATE_FORMAT)

		production_line = {
			'sale_line_id':order_line.id,
			'sequence_line':order_line.sequence_line,
			'name': order_line.name,
			'uom_id': order_line.product_uom.id,
			'product_id': order_line.product_id.id,
			'manufacturer' : order_line.product_id.manufacturer and order_line.product_id.manufacturer.id or False,
			'product_uom_qty': order_line.product_uom_qty,
			'other_description' : order_line.other_description,
			'cone_weight' : order_line.cone_weight,
			'count_number' : order_line.count_number,
			'bom_id' : order_line.bom_id.id,
			'wax' : order_line.wax,
			'est_delivery_date' : lsd,
			'remarks' : order_line.remarks,
			'application' : order_line.application,
			'tpi' : order_line.tpi,
			'tpm' : order_line.tpm,
		}
		return production_line

	def default_get(self, cr, uid, fields, context):
		if context is None: context = {}
		res = super(production_memo, self).default_get(cr, uid, fields, context=context)
		sale_id = context.get('sale_id', False)

		if sale_id:
			sale=self.pool.get('sale.order').browse(cr, uid, sale_id)

			if 'sale_id' in fields:
				res.update(sale_id=sale.id)
			if 'date_instruction' in fields:
				res.update(date_instruction=time.strftime(DEFAULT_SERVER_DATE_FORMAT))
			if 'goods_lines' in fields:
				line_ids = [self._production_line_for(cr, uid, order_line) for order_line in sale.order_line if order_line.state not in ('done')]
				res.update(goods_lines=line_ids)
		
		return res

	_defaults = {
		'state' : 'draft',
		'name' : '/'
	}
	_order = "id desc"

	def action_confirm(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'confirmed'})

	def action_receive(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'received'})

	def action_cancel(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'cancel'})

	def create(self,cr,uid,vals,context=None):
		if vals.get('name','/')=='/':
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'production.memo') or '/'
		return super(production_memo, self).create(cr, uid, vals, context=context) 

production_memo()

class production_memo_line(osv.osv):
	_name = "production.memo.line"
	_columns = {
		'sale_line_id'			: fields.many2one('sale.order.line','Sale Line'),
		'sequence_line'			: fields.char('Delivery Ref.',size=50),
		'product_id'			: fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
		'manufacturer'			: fields.related('product_id','manufacturer',type='many2one',relation='res.partner',string='Manufacturer'),
		'name'					: fields.text('Description', required=True),
		'uom_id'				: fields.many2one('product.uom', 'UoM', ondelete='set null', select=True),
		'product_uom_qty'		: fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
		'other_description'	 	: fields.text('Other Description'),
		'cone_weight'		   	: fields.float('Cone Weight',digits=(1, 3),required=False),
		'count_number'		  	: fields.float('Count Number',required=False,help="Yarn Count Number"),
		'bom_id'				: fields.many2one('mrp.bom','Blend',required=False,help="Yarn Blend Code"),
		'wax'					: fields.selection([('none','None'),('waxed',"Waxed"),('unwaxed',"Unwaxed")],'Wax',help="Select waxed if the product that will be sold is using wax"),
		'est_delivery_date'	 	: fields.date('Last Shipment Date'),
		'memo_id' 				: fields.many2one('production.memo','Memo ID'),
		'remarks'				: fields.text('Remarks Contract', help="Remarks for additional Information of this contract order"),
		'application'			: fields.selection([('knitting',"Knitting"),('weaving',"Weaving")],'Application'),
		'tpi' 					: fields.char('TPI',size=10,help='Turn per Inch'),
		'tpm' 					: fields.char('TPM',size=10,help='Turn per Meter'),
	}
production_memo_line()