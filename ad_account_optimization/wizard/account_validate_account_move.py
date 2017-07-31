# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class validate_account_move(osv.osv_memory):
	_inherit = "validate.account.move"
	_description = "Validate Account Move"
	_columns = {
		'journal_id': fields.many2one('account.journal', 'Journal', required=False),
		# 'period_id': fields.many2one('account.period', 'Period', required=True, domain=[('state','<>','done')]),
		"journal_ids" : fields.many2many("account.journal","validate_account_move_rel_journal","wizard_id","journal_id", "Journals"),
	}

	def validate_move(self, cr, uid, ids, context=None):
		obj_move = self.pool.get('account.move')
		if context is None:
			context = {}
		data = self.browse(cr, uid, ids, context=context)[0]
		for journal in data.journal_ids:
			ids_move = obj_move.search(cr, uid, [('state','=','draft'),('journal_id','=',journal.id),('period_id','=',data.period_id.id)], order="date")
			# if not ids_move:
			# 	raise osv.except_osv(_('Warning!'), _('Specified journal does not have any account move entries in draft state for this period.'))
			if ids_move:
				obj_move.button_validate(cr, uid, ids_move, context=context)
		return {'type': 'ir.actions.act_window_close'}

validate_account_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

