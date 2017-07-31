from openerp.osv import fields,osv


class sale_order_delivery(osv.Model):
	_name = "sale.order.delivery"
	def _get_move_id(self,cr,uid,ids,fieldname,arg,context=None):
		if not context:
			context={}
		
		pick_ids = self.pool.get('stock.picking').search(cr,uid,[('sale_delivery_id','in',ids)])
		pick = self.pool.get('stock.picking').read(cr,uid,pick_ids,['sale_delivery_id','id'],context)
		temp = {}
		res = dict((x, False) for x in ids)
		for p in pick:
			print "p-----------",p
			res.update({p['sale_delivery_id'][0]:p['id']})
		return res

	_columns = {
		'name':fields.char("Description",size=64),
		"order_id":fields.many2one('sale.order',"Sale Order"),
		"order_line":fields.one2many('sale.order.delivery.line',"order_id","Order Line"),
		"move_id":fields.function(_get_move_id,type="many2one",relation="stock.picking",string="Picking ID"),
		"delivery_date":fields.date('Estimated Delivery Date'),
	}
	_defaults = {
	    'order_id': lambda self,cr,uid,context: context.get('active_id',False),
	}

	def make_delivery(self,cr,uid,ids,context=None):
		for manual in self.browse(cr,uid,ids,context):
			move_id = self.pool.get('sale.order').action_ship_create_manual(cr, uid, [manual.order_id.id],manual.order_line,context)
		return True

class sale_order_delivery_line(osv.Model):
	_name = "sale.order.delivery.line"
	_columns = {
		"sequence_line":fields.char('Delivery Ref.',size=50),
		"name":fields.char('Description',size=128,),
		"line_id":fields.many2one('sale.order.line',"Order Line"),
		"order_id":fields.many2one("sale.order.delivery","Order ID"),
		"product_id":fields.many2one('product.product',"Product",required=True, ),
		"product_qty":fields.float("UoM Qty",required=True, ),
		"product_uom":fields.many2one("product.uom","Unit of Measure",required=True, ),
		"product_uos_qty":fields.float("UoS Qty",required=False, ),
		"product_uos":fields.many2one("product.uom","Unit of Sales",required=False, ),

		
	}

class sale_order(osv.Model):
	_inherit = 'sale.order'
	_columns = {
	    "manual_pick_ids":fields.one2many("sale.order.delivery",'order_id',"Manual Delivery")
	}

class stock_picking(osv.Model):
	_inherit = "stock.picking"
	_columns = {
		"sale_delivery_id":fields.many2one("sale.order.delivery","Sale Delivery"),
	}

class stock_move(osv.Model):
	_inherit = "stock.move"
	_columns = {
		"sale_delivery_line_id":fields.many2one("sale.order.delivery.line","Sale Delivery Line"),   
	}