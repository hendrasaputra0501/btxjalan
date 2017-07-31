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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp import pooler

class lc_product_line_knock_off(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft invoices
	"""

	_name = "lc.product.line.knock.off"
	_description = "Knock Off LC"
	_columns = {
		'date':fields.date('Date Knock Off', required=True),
	}

	_defaults = {
		'date': time.strftime("%Y-%m-%d"),
	}
	def order_knock_off(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		# wf_service = netsvc.LocalService("workflow")
		pool_obj = self.pool.get('letterofcredit.product.line')
		date = self.browse(cr, uid, ids[0], context=context).date or time.strftime("%Y-%m-%d")
		pool_obj.write(cr, uid, context['active_ids'], {'knock_off':True,'date_knock_off': date}, context=context)
		# for line in pool_obj.browse(cr, uid, context['active_ids'], context=context):
		# 	wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)

		return {'type': 'ir.actions.act_window_close'}

lc_product_line_knock_off()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
