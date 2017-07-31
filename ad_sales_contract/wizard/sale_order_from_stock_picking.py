# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler
import time
import openerp.addons.decimal_precision as dp
class stock_picking_order_line(osv.TransientModel):

	_name = "stock.picking.order.line"
	_rec_name = 'product_id'
	_columns = {
		'product_id' : fields.many2one('product.product', string="Product", required=True, ondelete='CASCADE'),
		'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
		'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True, ondelete='CASCADE'),
		'uop_quantity' : fields.float("Quantity UoP", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
		'product_uop': fields.many2one('product.uom', 'Unit of Picking', required=True, ondelete='CASCADE'),
		'prodlot_id' : fields.many2one('stock.production.lot', 'Serial Number', ondelete='CASCADE'),
		'tracking_id' : fields.many2one('stock.tracking', 'Pack', ondelete='CASCADE'),
		'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete='CASCADE', domain = [('usage','<>','view')]),
		# 'move_id' : fields.many2one('stock.move', "Move", ondelete='CASCADE'),
		'wizard_id' : fields.many2one('sale.order.from.stock.picking', string="Wizard", ondelete='CASCADE'),
		'price_unit' : fields.float("Price", required=True),
		'taxes_id': fields.many2many('account.tax','wizard_sale_pick_tax_rel','wizard_id','tax_id',string='Taxes'),
	}

	def onchange_product_id(self, cr, uid, ids, product_id, context=None):
		uom_id = False
		if product_id:
			product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
			uom_id = product.uom_id.id
		return {'value': {'product_uom': uom_id}}

class sale_order_from_stock_picking(osv.osv_memory):
	_name = "sale.order.from.stock.picking"

	_columns = {
		'partner_id':fields.many2one('res.partner','Customer', required=True),
		'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True, help="Pricelist for current sales order."),
		'date_order':fields.date('Date Order',required=True),
		'goods_type' : fields.selection([
			('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],'Goods Type',required=True),
		'sale_type'				: fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		'locale_sale_type'		: fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
		'order_lines'			: fields.one2many('stock.picking.order.line','wizard_id','Order Lines'),
	}

	_defaults = {
		'date_order': time.strftime("%Y-%m-%d"),
		'goods_type': lambda *g:'finish_others',
		'sale_type': lambda *s:'local',
		'locale_sale_type' : lambda *l:'okb',
	}

	def _get_default_shop(self, cr, uid, context=None):
		company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
		shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
		if not shop_ids:
			raise osv.except_osv(_('Error!'), _('There is no default shop for the current user\'s company!'))
		return shop_ids[0]

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = super(sale_order_from_stock_picking, self).default_get(cr, uid, fields, context=context)
		picking_ids = context.get('active_ids', [])
		active_model = context.get('active_model')

		if not picking_ids:
			return res
		
		assert active_model in ('stock.picking'), 'Bad context propagation'
		
		if 'order_lines' in fields:
			pickings = self.pool.get('stock.picking').browse(cr, uid, picking_ids, context=context)
			move_lines = [y for x in pickings if x.move_lines for y in x.move_lines]
			lines_grouped = {}
			for move in move_lines:
				key = move.product_id.id, move.product_uom.id, move.location_dest_id.id, (move.tracking_id and move.tracking_id.id or False)
				if key not in lines_grouped.keys():
					lines_grouped.update({key:{
						'product_id' : move.product_id.id,
						'quantity' : 0.0,
						'product_uom' : move.product_uom.id,
						'uop_quantity' : 0.0,
						'product_uop' : move.product_uop and move.product_uop.id or False,
						'tracking_id' : move.tracking_id and move.tracking_id.id or False,
						'prodlot_id' : move.prodlot_id and move.prodlot_id.id or False,
						'location_id' : move.location_dest_id.id,
						'price_unit' : move.product_id and move.product_id.list_price or 0.0,
						'taxes_id' : [(6, 0, [x.id for x in move.product_id.taxes_id])]
						}})
				lines_grouped[key]['quantity']+=move.product_qty
				lines_grouped[key]['uop_quantity']+=move.product_uop_qty
			res.update(order_lines=[x for x in lines_grouped.values()])
		return res

	def create_so(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		wf_service = netsvc.LocalService("workflow")
		sale_order_obj = self.pool.get('sale.order')
		sale_order_line_obj = self.pool.get('sale.order.line')
		picking_obj = self.pool.get('stock.picking')
		move_obj = self.pool.get('stock.move')

		if not ids:
			return {'type': 'ir.actions.act_window_close'}
		datas = self.browse(cr, uid, ids[0], context=context)
		order_lines = []
		grouped_order_lines = {}
		default_vals = {
			'partner_id' : datas.partner_id.id,
			'partner_invoice_id' : datas.partner_id.id,
			'partner_shipping_id' : datas.partner_id.id,
			'pricelist_id' : datas.pricelist_id.id,
			'date_order' : datas.date_order,
			'goods_type' : datas.goods_type,
			'sale_type' : datas.sale_type,
			'shop_id' : self._get_default_shop(cr, uid, context=context),
			'locale_sale_type' : datas.locale_sale_type,
			'payment_method' : 'cash',
			# 'order_line' : map(lambda x:(0,0,x),order_lines),
		}
		sale_id = sale_order_obj.create(cr, uid, default_vals, context=context)

		# for picking in picking_obj.browse(cr, uid, context['active_ids'], context=context):		
		for line in datas.order_lines:
			dict = {
				'product_id' : line.product_id.id,
				'product_uom_qty' : line.quantity or 0.0,
				'product_uom' : line.product_uom.id,
				'product_uos_qty' : line.quantity or 0.0,
				'product_uos' : line.product_uom.id,
				'product_uop_qty' : line.uop_quantity or 0.0,
				'product_uop' : line.product_uop and line.product_uop.id or False,
				'tracking_id' : line.tracking_id and line.tracking_id.id or False,
				'price_unit' : line.price_unit or 0.0,
				'tax_id' : [(6, 0, [x.id for x in line.taxes_id])],
				'name' : line.product_id.name,
				'default_location_id' : line.location_id.id,
				'sale_type' : datas.sale_type,
				'order_id' : sale_id,
				}
			order_lines.append(dict)
			
		for line in order_lines:
			sale_order_line_obj.create(cr, uid, line)

		data_pool = self.pool.get('ir.model.data')
		action_model = False
		action = {}
		if not sale_id:
			raise osv.except_osv(_('Error!'), _('Please create Sales Order.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'sale', "action_quotations")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','=', "+str(sale_id)+")]"
		return action

sale_order_from_stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
