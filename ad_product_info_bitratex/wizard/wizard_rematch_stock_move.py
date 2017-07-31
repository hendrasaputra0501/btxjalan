from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

from tools.translate import _

class wizard_rematch_stock_move(osv.osv_memory):
	_name = "wizard.rematch.stock.move"
	
	def do_rematch(self, cr, uid, ids, context=None):
		picking_obj = self.pool.get('stock.picking')
		move_obj = self.pool.get('stock.move')
		product_obj = self.pool.get('product.product')

		# product_ids = product_obj.search(cr, uid, [('internal_type','=','Raw Material'),('cost_method','in',('fifo','lifo'))])

		query = "(SELECT a.id,a.date_done \
				FROM \
				stock_picking a \
				INNER JOIN stock_move b ON b.picking_id=a.id \
				INNER JOIN stock_location c ON c.id=b.location_id and c.usage='internal' \
				INNER JOIN stock_location d ON d.id=b.location_dest_id and d.usage='production' \
				INNER JOIN product_product e ON e.id=b.product_id and e.internal_type='Raw Material' \
				INNER JOIN product_template f ON f.id=e.product_tmpl_id \
				INNER JOIN \
					(select \
						cast(substring(g1.res_id from 18 for (char_length(g1.res_id)-16)) as integer) as prod_tmpl_id \
					from ir_property g1 \
					where g1.name='cost_method' and g1.value_text in ('fifo','lifo') \
					) g on g.prod_tmpl_id=f.id \
				WHERE a.state='done' \
				GROUP BY a.id \
				ORDER BY a.date_done ASC) \
				UNION ALL\
				(SELECT a.id,a.date_done \
				FROM \
				stock_picking a \
				INNER JOIN stock_move b ON b.picking_id=a.id \
				INNER JOIN stock_location c ON c.id=b.location_id and c.usage='production' \
				INNER JOIN stock_location d ON d.id=b.location_dest_id and d.usage='internal' \
				INNER JOIN product_product e ON e.id=b.product_id and e.internal_type='Raw Material' \
				INNER JOIN product_template f ON f.id=e.product_tmpl_id \
				INNER JOIN \
					(select \
						cast(substring(g1.res_id from 18 for (char_length(g1.res_id)-16)) as integer) as prod_tmpl_id \
					from ir_property g1 \
					where g1.name='cost_method' and g1.value_text in ('fifo','lifo') \
					) g on g.prod_tmpl_id=f.id \
				WHERE a.state='done' \
				GROUP BY a.id \
				ORDER BY a.date_done ASC)"
		cr.execute(query)
		picking_ids = cr.dictfetchall()
		picking_ids = sorted(picking_ids, key = lambda k:k['date_done'])
		if picking_ids:
			picking_ids = [x['id'] for x in picking_ids]
		
		if not picking_ids:
			raise osv.except_osv(_('Error'),
				 _('None'))

		picking_obj.action_revert_done(cr, uid, picking_ids)
		picking_obj.action_move(cr, uid, picking_ids)
		picking_obj.action_done(cr, uid, picking_ids)
		return True