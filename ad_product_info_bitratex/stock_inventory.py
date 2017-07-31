from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class stock_inventory_line(osv.Model):
	_inherit = "stock.inventory.line"
	_columns = {
		'product_uom': fields.many2one('product.uom', 'UoM', required=True),
		'prod_lot_id': fields.many2one('stock.production.lot', 'Serial', domain="[('product_id','=',product_id)]"),
		"pack_id"	: fields.many2one("stock.tracking","Pack"),
		"uop_id"	: fields.many2one("product.uom","UoP"),
		"uop_qty"	: fields.float("UoP Qty",),
		'product_qty': fields.float('Quantity', digits=(2,16)),
		'price_unit': fields.float("Price Unit",digits= (2,8),required=False,),
		'currency_id': fields.many2one("res.currency","Currency"),

	}

	def _get_company_currency(self,cr,uid,context=None):
		if not context:context={}
		user = self.pool.get("res.users").browse(cr,uid,uid,context)
		currency_id = user and user.company_id and user.company_id.id and user.company_id.currency_id and user.company_id.currency_id.id or False
		return currency_id

	_defaults = {
		"currency_id":_get_company_currency
	}
class stock_inventory(osv.Model):
	_inherit = "stock.inventory"
	_columns = {

	}
	def action_done(self, cr, uid, ids, context=None):
		""" Finish the inventory
		@return: True
		"""
		if context is None:
			context = {}
		move_obj = self.pool.get('stock.move')
		for inv in self.browse(cr, uid, ids, context=context):
			move_obj.action_done(cr, uid, [x.id for x in inv.move_ids], context=context)
			print "invsssssssssssss",inv.date
			self.write(cr, uid, [inv.id], {'state':'done', 'date_done': inv.date or time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
		return True

	def action_confirm(self, cr, uid, ids, context=None):
		""" Confirm the inventory and writes its finished date
		@return: True
		"""
		if context is None:
			context = {}
		# to perform the correct inventory corrections we need analyze stock location by
		# location, never recursively, so we use a special context
		product_context = dict(context, compute_child=False)

		location_obj = self.pool.get('stock.location')
		for inv in self.browse(cr, uid, ids, context=context):
			move_ids = []
			for line in inv.inventory_line_id:
				pid = line.product_id.id
				product_context.update(uom=line.product_uom.id, to_date=inv.date, date=inv.date, prodlot_id=line.prod_lot_id.id)
				#amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]
				#change = line.product_qty - amount
				lot_id = line.prod_lot_id.id
				if line.product_id:
					location_id = line.product_id.property_stock_inventory.id
					value = {
						'name': _('INV:') + (line.inventory_id.name or ''),
						'product_id': line.product_id.id,
						'product_uom': line.product_uom.id,
						'prodlot_id': lot_id,
						'date': inv.date,
					}

					if line.product_qty > 0:
						value.update( {
							'product_qty': line.product_qty,
							'location_id': location_id,
							'location_dest_id': line.location_id.id,
							'tracking_id':line.pack_id and line.pack_id.id or False,
							"product_uop_qty": line.uop_qty or 0.0,
							"product_uop": line.uop_id and line.uop_id.id or False,
							'date': inv.date,
							'price_unit': line.price_unit,
							'price_currency_id':line.currency_id and line.currency_id.id or False,
						})
					else:
						value.update({
							'product_qty': -line.product_qty,
							'location_id': line.location_id.id,
							'location_dest_id': location_id,
							'tracking_id':line.pack_id and line.pack_id.id or False,
							"product_uop_qty": -line.uop_qty or 0.0,
							"product_uop": line.uop_id and line.uop_id.id or False,
							'date': inv.date,
							'price_unit': line.price_unit,
							'price_currency_id':line.currency_id and line.currency_id.id or False,
						})
					move_ids.append(self._inventory_line_hook(cr, uid, line, value))
			self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
			self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)
		return True