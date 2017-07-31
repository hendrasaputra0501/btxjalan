from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class stock_picking(osv.Model):
	_inherit = "stock.picking"
	_columns = {
		"contract_purchase_number" : fields.char('Contract Purchase Number', size=50),
		"supplier_delicery_slip" : fields.char('Delivery Slip Number', size=50),
		"date_delivery_slip" : fields.date('Delivery Slip Date'),
		"supplier_bc_reference" : fields.char('Supplier BC Number', size=50),
		'purchase_type'	: fields.selection([('import','Import'),('local','Local')],"Purchase Type",required=False),
		'transport_rate' : fields.float('Transport Rate',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information to compute cost tranportation of MRR"),
		'transport_rate_uom' : fields.many2one('product.uom','Transport Rate Uom'),
		# 'goods_type' : fields.selection([('finish','Finish Goods'),
		# 	('finish_others','Finish Goods(Others)'),
		# 	('raw','Raw Material'),
		# 	('service','Services'),
		# 	('stores','Stores'),
		# 	('waste','Waste'),
		# 	('scrap','Scrap'),
		# 	('packing','Packing Material'),
		# 	('asset','Fixed Asset')],
		# 	'Goods Type',required=True),
	}
	_defaults = {
		'purchase_type':lambda *a:'import',
	}

	
	def _get_price_unit_invoice(self, cursor, user, move_line, type):
		if move_line.purchase_line_id:
			return move_line.purchase_line_id.price_unit
		return super(stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)

	def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
		invoice_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: move_line: move_line object
			@param: invoice_id: ID of the related invoice
			@param: invoice_vals: dict used to created the invoice
			@return: dict that will be used to create the invoice line
		"""

		res=super(stock_picking,self)._prepare_invoice_line(cr, uid, group, picking, move_line,invoice_id, invoice_vals, context=context)
		res.update(
			{
				'discount_ids': move_line.purchase_line_id and move_line.purchase_line_id.discount_ids and [(6,0,map(lambda x:x.id, move_line.purchase_line_id.discount_ids))] or []
			}
		)
		return res
		
	# def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):

	# 	if context is None:
	# 		context = {}
		
	# 	invoice_vals = super(stock_picking,self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)

	# 	if picking:
	# 		if picking.sale_id:
	# 			invoice_vals.update({'goods_type':picking.sale_id.goods_type})
	# 			invoice_vals.update({'sale_type':picking.sale_id.sale_type})
	# 			invoice_vals.update({'locale_sale_type':picking.sale_id.locale_sale_type})

	# 	return invoice_vals

	def do_partial(self, cr, uid, ids, partial_datas, context=None):
		if context is None:
			context = {}
		res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas,context=context)
		delivered_picking_id = [int(val['delivered_picking']) for val in res.values() if val.get('delivered_picking',False)]
		picking = self.browse(cr, uid, delivered_picking_id[0])
		mrr_name_set = ''
		company_pooler = self.pool.get('res.company')
		company_code = ''
		goods_code = ''
		company_id = False
		month = ''

		# only for puchase
		order = picking.purchase_id
		if order and not picking.surat_jalan_number:
			if order.company_id:
				company_id = order.company_id		
			if company_id:
				company_code=company_id.prefix_sequence_code
			
			goods_type = order.goods_type
			if goods_type == 'raw':
				goods_code = 'R'
			elif goods_type == 'stores':
				goods_code = 'S'
			elif goods_type == 'packing':
				goods_code = 'P'
			else:
				goods_code = 'O'

			date = picking.date_done!='False' and picking.date_done or time.strftime('%Y-%m-%d %H:%M:%S')
			month = datetime.datetime.strptime(date,DEFAULT_SERVER_DATETIME_FORMAT).strftime('%b').lower()

			po_type = order.purchase_type
			mrr_name_set = ''
			mrr_code = ''
			if order.use_bc_on_mrr:
				mrr_code = 'X'
			else:
				mrr_code = 'M'
			if goods_type == 'raw':
				if po_type=='import':
					mrr_name_set = (mrr_code+ company_code + 'I-' + goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in.'+po_type+'.'+month, context={'date':picking.date_done}) or '/'))
				elif po_type=='local':
					mrr_name_set = (mrr_code+ company_code +'L-'+ goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in.'+po_type+'.'+month, context={'date':picking.date_done}) or '/'))
			else:
				mrr_name_set = self.pool.get('ir.sequence').get(cr, uid, 'picking.in.'+goods_type+'.'+po_type+'.'+month, context={'date':picking.date_done}) or '/'
			# look for related valuation account move and change the reference
			move_ids = self.pool.get('account.move').search(cr, uid, [('ref','=',picking.name)])
			if move_ids:
				self.pool.get('account.move').write(cr, uid, move_ids, {'ref':mrr_name_set})
			move_line_ids = self.pool.get('account.move.line').search(cr, uid, [('ref','=',picking.name)])
			if move_line_ids:
				self.pool.get('account.move.line').write(cr, uid, move_line_ids, {'reference':mrr_name_set})

			self.write(cr, uid, picking.id, {'name':mrr_name_set,'surat_jalan_number':mrr_name_set})
		return res

class stock_picking_in(osv.osv):
	_inherit = "stock.picking.in"
	_columns = {
		# 'show_partner_address' : fields.boolean('Show Customer Address'),
		# 'partner_name' : fields.char('Customer Name', size=128),
		# 'street': fields.char('Street', size=128),
		# 'street2': fields.char('Street2', size=128),
		# 'street3': fields.char('Street3', size=128),
		# 'zip': fields.char('Zip', change_default=True, size=24),
		# 'city': fields.char('City', size=128),
		# 'state_id': fields.many2one("res.country.state", 'State'),
		# 'country_id': fields.many2one('res.country', 'Country'),
		# 'notify' : fields.related('sale_id','notify',type='many2one',relation='res.partner',string='Notify Party', store=True),
		
		# 'show_notify_address' : fields.boolean('Show Notify Address'),
		# 'n_name' : fields.char('Notify', size=128),
		# 'n_street': fields.char('Street', size=128),
		# 'n_street2': fields.char('Street2', size=128),
		# 'n_street3': fields.char('Street3', size=128),
		# 'n_zip': fields.char('Zip', change_default=True, size=24),
		# 'n_city': fields.char('City', size=128),
		# 'n_state_id': fields.many2one("res.country.state", 'State'),
		# 'n_country_id': fields.many2one('res.country', 'Country'),

		'forwading' : fields.many2one('stock.transporter','Forwading', required=False),
		"forwading_charge":fields.many2one("stock.transporter.charge","Forwading Charge"),
		"shipping_lines":fields.many2one("stock.transporter","Shipping Lines"),
		'teus' : fields.char('TEUS.', help="Container Type Code Bitratex",size=50),
		'container_number' : fields.char('Container No.', size=50),
		'truck_number' : fields.char('Truck No.', size=50),
		'seal_number' : fields.char('Seal No.', size=50),
		"driver_id":fields.many2one("driver","Driver"),
		"trucking_company":fields.many2one("stock.transporter","Transport Vendor"),
		"trucking_charge":fields.many2one("stock.transporter.charge","Trucking Charge"),
		'truck_type' : fields.many2one('stock.transporter.truck','Truck Type'),
		"porters":fields.many2one("stock.porters","Porters"),
		"porters_charge":fields.many2one("stock.porters.charge","Porters Charge"),
		# 'goods_type' : fields.selection([('finish','Finish Goods'),
		# 	('finish_others','Finish Goods(Others)'),
		# 	('raw','Raw Material'),
		# 	('service','Services'),
		# 	('stores','Stores'),
		# 	('waste','Waste'),
		# 	('scrap','Scrap'),
		# 	('packing','Packing Material'),
		# 	('asset','Fixed Asset')],
		# 	'Goods Type',required=True),
		"contract_purchase_number" : fields.char('Contract Purchase Number', size=50),
		"supplier_bc_reference" : fields.char('Supplier BC Number', size=50),
		"supplier_delicery_slip" : fields.char('Delivery Slip Number', size=50),
		"date_delivery_slip" : fields.date('Delivery Slip Date'),
		'purchase_type'	: fields.selection([('import','Import'),('local','Local')],"Purchase Type",required=False),
		'transport_rate' : fields.float('Transport Rate',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information to compute cost tranportation of MRR"),
		'transport_rate_uom' : fields.many2one('product.uom','Transport Rate Uom'),
	}

	def onchange_trucking_company(self, cr, uid, uds, trucking_company, context=None):
		res = {'truck_type':False}
		if trucking_company:
			truck_ids = self.pool.get('stock.transporter.truck').search(cr, uid, [('transporter_id','=',trucking_company)])
			if truck_ids:
				res['truck_type'] = truck_ids[0]
		return {'value':res}

	_defaults = {
		"purchase_type" : lambda *a:'import'
	}

class stock_move(osv.osv):
	_inherit = "stock.move"

	_columns = {
		"purchase_id": fields.related('purchase_line_id','order_id',type="many2one", relation='purchase.order', string='Purchase Order', store=True),
		"gross_weight" : fields.float('Gross Weight',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information for bitratex MRR"),
		"net_weight" : fields.float('Net Weight',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information for bitratex MRR"),
		"moisturity" : fields.float('Moisturity',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information for bitratex MRR"),
	}