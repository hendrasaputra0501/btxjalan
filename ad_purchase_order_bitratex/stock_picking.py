from openerp.osv import fields,osv

class stock_partial_picking(osv.osv_memory):
	_inherit = "stock.partial.picking"
	_columns ={

	}
	# def _partial_move_for(self, cr, uid, move):
	# 	partial_move=super(stock_partial_picking, self)._partial_move_for(cr, uid, move)
	# 	partial_move.update({
	# 		"cost":move.purchase_line_id and move.purchase_line_id.price_unit or 0.0,
	# 		"currency": move.purchase_line_id and move.purchase_line_id.order_id and move.purchase_line_id.order_id.pricelist_id \
	# 				and move.purchase_line_id.order_id.pricelist_id.currency_id and move.purchase_line_id.order_id.pricelist_id.currency_id.id or False, 
	# 		#'uop_quantity' : move.product_uop_qty if move.state == 'assigned' or move.picking_id.type == 'in' else 0,
	# 		#'product_uop' : move.product_uop and move.product_uop.id,
	# 	})
	# 	return partial_move