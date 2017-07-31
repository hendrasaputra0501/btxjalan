from openerp.osv import fields, osv
import time
from tools.translate import _

class sale_order_delivery_wizard(osv.TransientModel):
	_name = "sale.order.delivery.wizard"
	_columns = {
		'name':fields.char("Description",size=64),
		"order_id":fields.many2one('sale.order',"Sale Order"),
		"order_line":fields.one2many('sale.order.delivery.line.wizard',"order_id","Order Line"),
		"move_id":fields.many2one('stock.picking',"Picking ID"),
		"delivery_date":fields.date('Estimated Delivery Date'),
	}
	_defaults = {
	    'order_id': lambda self,cr,uid,context: context.get('active_id',False),
	}
	def default_get(self, cr, uid, fields, context=None):
		""" To get default values for the object.
		 @param self: The object pointer.
		 @param cr: A database cursor
		 @param uid: ID of the user currently logged in
		 @param fields: List of fields for which we want default values
		 @param context: A standard dictionary
		 @return: A dictionary which of fields with values.
		"""
		if not context:context={}
		res = super(sale_order_delivery_wizard, self).default_get(cr, uid, fields, context=context)

		if 'active_id' in context:
			order_id = context.get('active_id', False)
			if order_id:
				order = self.pool.get('sale.order').browse(cr,uid,order_id,context)
				res['name']=order.name
				res['order_id']=order.id
				res['order_line']=[]
				res['delivery_date']=time.strftime('%Y-%m-%d')
				for line in order.order_line:
					res['order_line'].append((0,0,{
						"sequence_line":line.sequence_line,
						"name":line.name or (line.product_id and line.product_id.name) or "-",
						"line_id":line and line.id,
						"product_id":line.product_id and line.product_id.id or False,
						"product_qty":line.product_uom_qty,
						"product_uom":line.product_uom and line.product_uom.id or False,
						"product_uos_qty":line.product_uos_qty,
						"product_uos":line.product_uos and line.product_uos.id or False,
						}))
		return res
	def make_manual(self,cr,uid,ids,context=None):
		for manual in self.browse(cr,uid,ids,context):
			created_id = self.pool.get('sale.order.delivery').create(cr, uid, {
				'name':manual.order_id.name,
				"order_id":manual.order_id.id,
				"order_line":[],
				"delivery_date":manual.delivery_date or time.strftime('%Y-%m-%d')
				})
			vals=[{
				"sequence_line":line.sequence_line,
				"name":line.name or (line.product_id and line.product_id.name) or "-",
				"order_id":created_id,
				"line_id":line and line.line_id.id,
				"product_id":line.product_id and line.product_id.id or False,
				"product_qty":line.product_qty,
				"product_uom":line.product_uom and line.product_uom.id or False,
				"product_uos_qty":line.product_uos_qty,
				"product_uos":line.product_uos and line.product_uos.id or False,
				} for line in manual.order_line]
			for val in vals:
				self.pool.get('sale.order.delivery.line').create(cr,uid,val,context)
		return True

class sale_order_delivery_line_wizard(osv.TransientModel):
	_name = "sale.order.delivery.line.wizard"
	_columns = {
		"sequence_line":fields.char('Delivery Ref.',size=50),
		"name":fields.char('Description',size=128,),
		"line_id":fields.many2one('sale.order.line',"Order Line"),
		"order_id":fields.many2one("sale.order.delivery.wizard","Order ID"),
		"product_id":fields.many2one('product.product',"Product",required=True, ),
		"product_qty":fields.float("UoM Qty",required=True, ),
		"product_uom":fields.many2one("product.uom","Unit of Measure",required=True, ),
		"product_uos_qty":fields.float("UoS Qty",required=False, ),
		"product_uos":fields.many2one("product.uom","Unit of Sales",required=False, ),

	}




