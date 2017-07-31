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

from openerp.osv import fields, osv

from openerp.tools.translate import _

class stock_invoice_onshipping(osv.osv_memory):
	def _get_shipment_date(self, cr, uid, context=None):
		if context is None:
			context = {}

		model = context.get('active_model')
		if not model or 'stock.picking' not in model:
			return []

		model_pool = self.pool.get(model)
		res_ids = context and context.get('active_ids', [])
		vals = []
		browse_picking = model_pool.browse(cr, uid, res_ids, context=context)
		date_done = False
		for pick in browse_picking:
			if not pick.move_lines:
				continue
			date_done = pick.date_done
		return date_done
		
	_inherit = "stock.invoice.onshipping"
	
	_columns = {
	}

	_defaults = {
		'group' : True,
		'invoice_date' : _get_shipment_date,
	}