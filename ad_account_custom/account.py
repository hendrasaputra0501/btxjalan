import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import decimal_precision as dp
import tools

class account_move_line(osv.osv):
	_inherit = "account.move"

	def post(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice = context.get('invoice', False)
		valid_moves = self.validate(cr, uid, ids, context)

		if not valid_moves:
			raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
		obj_sequence = self.pool.get('ir.sequence')
		for move in self.browse(cr, uid, valid_moves, context=context):
			if move.name =='/':
				new_name = False
				journal = move.journal_id

				if invoice and invoice.internal_number:
					new_name = invoice.internal_number
				else:
					if journal.sequence_id:
						date = datetime.strptime(move.date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
						c = {'fiscalyear_id': move.period_id.fiscalyear_id.id, 'date':date}
						new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
					else:
						raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))

				if new_name:
					self.write(cr, uid, [move.id], {'name':new_name})

		cr.execute('UPDATE account_move '\
				   'SET state=%s '\
				   'WHERE id IN %s',
				   ('posted', tuple(valid_moves),))
		return True