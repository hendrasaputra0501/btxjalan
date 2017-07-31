import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools

class account_move_line(osv.osv):
	_inherit = "account.move.line"
	_columns = {
		'other_ref' : fields.char('Other Reference', size=100, help="additional reference that can be use to marking the accounting statement"),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		result = []
		for line in self.browse(cr, uid, ids, context=context):
			if line.ref:
				result.append((line.id, (line.move_id.name or '')+' ('+line.ref+')'))
			else:
				if line.other_ref:
					result.append((line.id, (line.move_id.name or '')+' ('+line.other_ref+')'))
				else:
					result.append((line.id, line.move_id.name))
		return result

	def print_journal_item(self, cr, uid, ids, context=None):
		if context is None:
			context={}
		datas = {
			'model': 'account.move.line',
			'ids': ids,
			'form': self.read(cr, uid, ids[0], context=context),
		}
		if context.get('header',False):
			datas.update({'header':context.get('header',False)})
		return {'type': 'ir.actions.report.xml', 'report_name': 'journal.item', 'datas': datas}