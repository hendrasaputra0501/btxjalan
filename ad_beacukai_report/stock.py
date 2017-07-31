from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _
class stock_move(osv.Model):
	_inherit = "stock.move"
	
	_columns = {
# 		"freight_unit":fields.float("Freight",digits_compute=dp.get_precision('Account')),
# 		"insurance_unit":fields.float("Insurance",digits_compute=dp.get_precision('Account')),
# 		"freight_total":fields.float("Freight Total",digits_compute=dp.get_precision('Account')),
# 		"insurance_total":fields.float("Insurance Total",digits_compute=dp.get_precision('Account')),
	}

	_defaults = {
# 		'freight_unit':0.0,
# 		'insurance_unit':0.0,
# 		'freight_total':0.0,
# 		'insurance_total':0.0,
	}
# 	def onchange_freight_unit(self,cr,uid,ids,freight_unit,qty,context=None):
# 		if not context:
# 			context={}
# 		val = {}
# 		if freight_unit and qty:
# 			val.update({'freight_total':freight_unit*qty})
# 		return val
# 
# 	def onchange_insurance_unit(self,cr,uid,ids,insurance_unit,qty,context=None):
# 		if not context:
# 			context={}
# 		val = {}
# 		if insurance_unit and qty:
# 			val.update({'insurance_total':insurance_unit*qty})
# 		return val

	def action_scrap(self, cr, uid, ids, quantity, location_id, context=None):
		""" Move the scrap/damaged product into scrap location
		@param cr: the database cursor
		@param uid: the user id
		@param ids: ids of stock move object to be scrapped
		@param quantity : specify scrap qty
		@param location_id : specify scrap location
		@param context: context arguments
		@return: Scraped lines
		"""
		#quantity should in MOVE UOM
		if quantity <= 0:
			raise osv.except_osv(_('Warning!'), _('Please provide a positive quantity to scrap.'))
		res = []
		for move in self.browse(cr, uid, ids, context=context):
			source_location = move.location_id
			if move.state == 'done':
				source_location = move.location_dest_id
			if move.type == 'in':
				source_location = move.location_dest_id
			if source_location.usage != 'internal':
				#restrict to scrap from a virtual location because it's meaningless and it may introduce errors in stock ('creating' new products from nowhere)
				raise osv.except_osv(_('Error!'), _('Forbidden operation: it is not allowed to scrap products from a virtual location.'))
			move_qty = move.product_qty
			uos_qty = quantity / move_qty * move.product_uos_qty
			default_val = {
				'location_id': source_location.id,
				'product_qty': quantity,
				'product_uos_qty': uos_qty,
				'state': move.state,
				'scrapped': True,
				'location_dest_id': location_id,
				'tracking_id': move.tracking_id.id,
				'prodlot_id': move.prodlot_id.id,
			}
			new_move = self.copy(cr, uid, move.id, default_val)

			res += [new_move]
			product_obj = self.pool.get('product.product')
			for product in product_obj.browse(cr, uid, [move.product_id.id], context=context):
				if move.picking_id:
					uom = product.uom_id.name if product.uom_id else ''
					message = _("%s %s %s has been <b>moved to</b> scrap.") % (quantity, uom, product.name)
					move.picking_id.message_post(body=message)

		self.action_done(cr, uid, res, context=context)
		return res