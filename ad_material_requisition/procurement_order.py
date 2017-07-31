from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import time
import openerp.addons.decimal_precision as dp

class procurement_order(osv.osv):
	_inherit = "procurement.order"
	_columns = {
		"analytic_account_id": fields.many2one('account.analytic.account',"Analytic Account"),
	}

	def action_confirm(self, cr, uid, ids, context=None):
		if not context:context={}
		res = super(procurement_order,self).action_confirm(cr, uid, ids, context=context)
		move_obj = self.pool.get('stock.move')
		for procurement in self.browse(cr, uid, ids, context=context):
			if procurement.product_qty <= 0.00:
				raise osv.except_osv(_('Data Insufficient!'),
					_('Please check the quantity in procurement order(s) for the product "%s", it should not be 0 or less!' % procurement.product_id.name))
			if procurement.product_id.type in ('product', 'consu'):
				if not procurement.move_id:
					source = procurement.location_id.id
					if procurement.procure_method == 'make_to_order':
						source = procurement.product_id.property_stock_procurement.id
					id = move_obj.create(cr, uid, {
						'name': procurement.name,
						'location_id': source,
						'location_dest_id': procurement.location_id.id,
						'product_id': procurement.product_id.id,
						'product_qty': procurement.product_qty,
						'product_uom': procurement.product_uom.id,
						'date_expected': procurement.date_planned,
						'state': 'draft',
						'company_id': procurement.company_id.id,
						'auto_validate': True,
					})
					move_obj.action_confirm(cr, uid, [id], context=context)
					self.write(cr, uid, [procurement.id], {'move_id': id, 'close_move': 1})
		self.write(cr, uid, ids, {'state': 'confirmed', 'message': ''})
		return res