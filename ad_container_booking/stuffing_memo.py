from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class stuffing_memo(osv.osv):
	_name = "stuffing.memo"
	_columns = {
		'manufacturer' : fields.many2one('res.partner','Manufacturer'),
		'name' : fields.char('Name',size=200),
		'origin' : fields.char('Source Document',size=400),
		'creation_date' : fields.date('Date'),
		'stuffing_date' : fields.date('Stuffing Date',required=True),
		'goods_lines' : fields.one2many('stuffing.memo.line','stuffing_id','Goods'),
		'pic_id_1'	: fields.many2one('hr.department',"CC-1"),
		'pic_id_2'	: fields.many2one('hr.department',"CC-2"),
		'note' : fields.text('Note'),
		'picking_ids' : fields.many2many('stock.picking','stock_picking_stuffing_rel','picking_id','stuffing_id','Related Picking(s)',readonly=True),
		# 'picking_ids' : fields.one2many('stock.picking','stuffing_id','Delivery Order(s)',readonly=False),
		'state' : fields.selection([
			('cancel','Cancelled'),
			('draft','New'),
			('confirm1','Inform By Marketing'),
			('confirm2','Confrim By Production'),],'Status'),
	}
	_defaults = {
		'state' : 'draft'
	}
	_order = "id desc"

	def action_confirm1(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'confirm1'})

	def action_confirm2(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'confirm2'})
	
	def action_cancel(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'cancel'})

stuffing_memo()

class stuffing_memo_line(osv.osv):
	_name = "stuffing.memo.line"
	_columns = {
		'name': fields.char('Description'),
		'product_id': fields.many2one('product.product', 'Product'),
		'manufacturer': fields.related('product_id','manufacturer',type='many2one',relation='res.partner',string='Manufacturer'),
		'product_qty': fields.float('Quantity UoM', digits_compute=dp.get_precision('Product Unit of Measure'),
			help="This is the quantity of products from an inventory "
				"point of view. For moves in the state 'done', this is the "
				"quantity of products that were actually moved. For other "
				"moves, this is the quantity of product that is planned to "
				"be moved. Lowering this quantity does not generate a "
				"backorder. Changing this quantity on assigned moves affects "
				"the product reservation, and should be done with care."
		),
		'product_uom': fields.many2one('product.uom', 'Unit of Measure'),
		'product_uop_qty': fields.float('Quantity UoP', digits_compute=dp.get_precision('Product Unit of Measure'),
			help="This is the quantity of products from an inventory "
				"point of view. For moves in the state 'done', this is the "
				"quantity of products that were actually moved. For other "
				"moves, this is the quantity of product that is planned to "
				"be moved. Lowering this quantity does not generate a "
				"backorder. Changing this quantity on assigned moves affects "
				"the product reservation, and should be done with care."
		),
		'product_uop': fields.many2one('product.uom', 'Unit of Packaging'),
		'stock_move_id': fields.many2one('stock.move', 'Stock Move'),

		# 'picking_id' : fields.related('stock_move_id','picking_id',type='many2one',relation='stock.picking',string='Delivery Order', store=True),
		'picking_id' : fields.many2one('stock.picking',string='Delivery Order'),
		'sale_id' : fields.related('picking_id','sale_id',type='many2one',relation='sale.order',string='SC', store=True),
		'booking_id' : fields.related('picking_id','container_book_id',type='many2one',relation='container.booking',string='SI No.', store=True),
		'partner_id': fields.related('picking_id','partner_id',type='many2one',relation='res.partner',string='Customer', store=True),
		'dest_port_id': fields.related('booking_id','port_to',type='many2one',relation='res.port',string='Destination', store=True),

		'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number'),
		'tracking_id': fields.many2one('stock.tracking', 'Pack'),
		'stuffing_id' : fields.many2one('stuffing.memo','Stuffing Memo'),

		'priority' : fields.selection([('red','Priority 1'),('orange','Priority 2')],'Priority',required=False),
		'priority_reason' : fields.text('Priority Reason'),
		'container_size' : fields.many2one('container.size','Container Size'),
		'remark' : fields.text('Remark'),

	}
stuffing_memo_line()
