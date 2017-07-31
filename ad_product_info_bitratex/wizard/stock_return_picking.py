from openerp import netsvc
import time

from openerp.osv import osv,fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class stock_move(osv.Model):
	_inherit = "stock.move"
	_columns = {
		"return_ref_id" : fields.many2one("stock.move","Stock Move Retur Reference"),
	}


class stock_return_picking(osv.osv_memory):
	_inherit = 'stock.return.picking'
	_columns = {

	}

	def create_returns(self, cr, uid, ids, context=None):
		""" 
		 Creates return picking.
		 @param self: The object pointer.
		 @param cr: A database cursor
		 @param uid: ID of the user currently logged in
		 @param ids: List of ids selected
		 @param context: A standard dictionary
		 @return: A dictionary which of fields with values.
		"""
		if context is None:
			context = {} 
		record_id = context and context.get('active_id', False) or False
		move_obj = self.pool.get('stock.move')
		pick_obj = self.pool.get('stock.picking')
		uom_obj = self.pool.get('product.uom')
		data_obj = self.pool.get('stock.return.picking.memory')
		act_obj = self.pool.get('ir.actions.act_window')
		model_obj = self.pool.get('ir.model.data')
		wf_service = netsvc.LocalService("workflow")
		pick = pick_obj.browse(cr, uid, record_id, context=context)
		data = self.read(cr, uid, ids[0], context=context)
		date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
		set_invoice_state_to_none = True
		returned_lines = 0
		
#		Create new picking for returned products

		seq_obj_name = 'stock.picking'
		new_type = 'internal'
		if pick.type =='out':
			new_type = 'in'
			seq_obj_name = 'stock.picking.in'
		elif pick.type =='in':
			new_type = 'out'
			seq_obj_name = 'stock.picking.out'
		new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
		new_picking = pick_obj.copy(cr, uid, pick.id, {
										'name': _('%s-%s-return') % (new_pick_name, pick.name),
										'move_lines': [], 
										'state':'draft', 
										'type': new_type,
										'date':date_cur, 
										'invoice_state': data['invoice_state'],
		})
		
		val_id = data['product_return_moves']
		for v in val_id:
			data_get = data_obj.browse(cr, uid, v, context=context)
			mov_id = data_get.move_id.id
			if not mov_id:
				raise osv.except_osv(_('Warning !'), _("You have manually created product lines, please delete them to proceed"))
			new_qty = data_get.quantity
			move = move_obj.browse(cr, uid, mov_id, context=context)
			new_location = move.location_dest_id.id
			returned_qty = move.product_qty
			for rec in move.move_history_ids2:
				returned_qty -= rec.product_qty

			if returned_qty != new_qty:
				set_invoice_state_to_none = False
			if new_qty:
				returned_lines += 1
				new_move=move_obj.copy(cr, uid, move.id, {
											'product_qty': new_qty,
											'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
											'picking_id': new_picking, 
											'state': 'draft',
											'location_id': new_location, 
											'location_dest_id': move.location_id.id,
											'date': date_cur,
											'prodlot_id': data_get.prodlot_id.id,
											'price_unit' : move.price_unit and move.price_unit or 0.0,
											'return_ref_id': mov_id or False,
				})
				move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]}, context=context)
		if not returned_lines:
			raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))

		# if set_invoice_state_to_none:
		# 	pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
		# Beacouse of spesific requirement, we change the rule so that everytime they created a new return, it should be to be refunded and the prev incoming shipment should remain to be invoice
		if set_invoice_state_to_none and pick.type!='in':
			pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
		wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
		pick_obj.force_assign(cr, uid, [new_picking], context)
		# Update view id in context, lp:702939
		model_list = {
				'out': 'stock.picking.out',
				'in': 'stock.picking.in',
				'internal': 'stock.picking',
		}
		return {
			'domain': "[('id', 'in', ["+str(new_picking)+"])]",
			'name': _('Returned Picking'),
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model': model_list.get(new_type, 'stock.picking'),
			'type':'ir.actions.act_window',
			'context':context,
		}