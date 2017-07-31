# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from datetime import datetime

class stock_partial_picking_line(osv.TransientModel):

	_inherit = "stock.partial.picking.line"
	_columns = {
		'cost' : fields.float("Cost", help="Unit Cost for this product line", digits=(2,8)),
		'uop_quantity' : fields.float("Quantity UoP", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
		'product_uop': fields.many2one('product.uom', 'Unit of Picking', required=True, ondelete='CASCADE'),
		'tracking_id' : fields.many2one('stock.tracking','Pack'),
	}

	# Modify this method if the product can be changed, and you want to change the UoP too
	# def onchange_product_id(self, cr, uid, ids, product_id, context=None):
	#     uom_id = False
	#     if product_id:
	#         product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
	#         uom_id = product.uom_id.id
	#     return {'value': {'product_uom': uom_id}}


class stock_partial_picking(osv.osv_memory):
	_inherit = "stock.partial.picking"
	
	_columns = {
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(stock_partial_picking, self).view_init(cr, uid, fields_list, context=context)
		pick_obj = self.pool.get('stock.picking')
		count = 0
		active_ids = context.get('active_ids',[])
		for pick in pick_obj.browse(cr, uid, active_ids, context=context):
			if (pick.date_done == 'False' or pick.date_done is None or not pick.date_done) and (pick.date_done_2 == 'False' or pick.date_done_2 is None or not pick.date_done_2):
				raise osv.except_osv(_('Warning!'), _('Please Input Transfer/Receipt Date on Additional Info'))
			picking_date = pick.date_done!='False' and datetime.strptime(pick.date_done,"%Y-%m-%d %H:%M:%S") or False
			diff = datetime.now()- picking_date
			if diff.days >5 and not pick.allow_back_date_release:
				raise osv.except_osv(_('Back Date Entry Error!'), _('You are not allow to release this document. Please ask for the permission to release this document'))
		return res

	def _partial_move_for(self, cr, uid, move):
		partial_move=super(stock_partial_picking, self)._partial_move_for(cr, uid, move)
		partial_move.update({
			'uop_quantity' : move.state == 'assigned' and move.product_uop_qty or 0.0,
			'product_uop' : move.product_uop and move.product_uop.id or False,
			'tracking_id' : move.tracking_id and move.tracking_id.id or False,
		})
		return partial_move

	def do_partial(self, cr, uid, ids, context=None):
		assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
		stock_picking = self.pool.get('stock.picking')
		stock_move = self.pool.get('stock.move')
		uom_obj = self.pool.get('product.uom')
		partial = self.browse(cr, uid, ids[0], context=context)
		partial_data = {
			'delivery_date' : partial.date
		}
		picking_type = partial.picking_id.type
		for wizard_line in partial.move_ids:
			line_uom = wizard_line.product_uom
			move_id = wizard_line.move_id.id

			#Quantiny must be Positive
			if wizard_line.quantity < 0:
				raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))

			#Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
			qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)
			if line_uom.factor and line_uom.factor <> 0:
				if float_compare(qty_in_line_uom, wizard_line.quantity, precision_rounding=line_uom.rounding) != 0:
					raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only rounding of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
			if move_id:
				#Check rounding Quantity.ex.
				#picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
				#partial delivery: 253g
				#=> result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
				initial_uom = wizard_line.move_id.product_uom
				#Compute the quantity for respective wizard_line in the initial uom
				qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
				without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
				if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
					raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only rounding of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
			else:
				seq_obj_name =  'stock.picking.' + picking_type
				move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
													'product_id': wizard_line.product_id.id,
													'product_qty': wizard_line.quantity,
													'product_uom': wizard_line.product_uom.id,
													'prodlot_id': wizard_line.prodlot_id and wizard_line.prodlot_id.id or False,
													'location_id' : wizard_line.location_id.id,
													'location_dest_id' : wizard_line.location_dest_id.id,
													'picking_id': partial.picking_id.id,
													'tracking_id' : wizard_line.tracking_id and wizard_line.tracking_id.id or False,
													},context=context)
				stock_move.action_confirm(cr, uid, [move_id], context)
			partial_data['move%s' % (move_id)] = {
				'product_id': wizard_line.product_id.id,
				'product_uop_qty': wizard_line.uop_quantity,
				'product_uop': wizard_line.product_uop.id,
				'product_qty': wizard_line.quantity,
				'product_uom': wizard_line.product_uom.id,
				'prodlot_id': wizard_line.prodlot_id and wizard_line.prodlot_id.id or False,
				'tracking_id' : wizard_line.tracking_id and wizard_line.tracking_id.id or False,
			}
			# if (picking_type == 'in') and (wizard_line.product_id.cost_method != 'standard'):
			#     partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
			#                                                       product_currency=wizard_line.currency.id)
			if (picking_type == 'in'):
				if partial.picking_id.is_retur or (wizard_line.product_id.cost_method != 'standard'):
					partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
																  product_currency=wizard_line.currency.id)
			elif (picking_type == 'out'):
				if partial.picking_id.is_retur or (wizard_line.product_id.cost_method != 'standard'):
					partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
																  product_currency=wizard_line.currency.id)
			elif (picking_type == 'internal'):
				if (wizard_line.move_id.location_id.usage!='internal' and wizard_line.move_id.location_dest_id.usage=='internal') and (wizard_line.product_id.cost_method !='standard'):
					partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
																	product_currency=wizard_line.currency.id)
		stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
		return {'type': 'ir.actions.act_window_close'}

	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
