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

from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp import pooler

class commission_knock_off(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft invoices
	"""

	_name = "commission.knock.off"
	_description = "Knock Off Commission"

	def comm_knock_off(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		# wf_service = netsvc.LocalService("workflow")
		pool_obj = self.pool.get('account.invoice.commission')
		pool_obj.write(cr, uid, context['active_ids'], {'knock_off':True,'date_knock_off': time.strftime("%Y-%m-%d")}, context=context)
		# for line in pool_obj.browse(cr, uid, context['active_ids'], context=context):
		# 	wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)

		return {'type': 'ir.actions.act_window_close'}

commission_knock_off()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
