from openerp.osv import fields, osv
import time
from tools.translate import _

class statement_print_journal_items(osv.TransientModel):
	_name = "statement.print.journal.items"
	_columns = {
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(statement_print_journal_items, self).view_init(cr, uid, fields_list, context=context)
		statement_pool = self.pool.get('account.bank.statement')
		count = 0
		active_ids = context.get('active_ids',[])
		for statement in statement_pool.browse(cr, uid, active_ids, context=context):
			if not statement.move_id:
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Bank Statement has not yet have a Journal Entry'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('One/None of these Bank Statements has not yet have Journal Entries'))
		return res
	
	def print_journal_item(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('account.bank.statement')
		move_line_obj = self.pool.get('account.move.line')
		
		active_ids = context.get('active_ids',[])
		if not active_ids:
			return False

		move_line_ids = move_line_obj.search(cr, uid, [('statement_id','=',active_ids[0])])
		if not move_line_ids:
			return False
		ctx = context.copy()
		ctx.update({'header':"Bank Statements Cash Voucher for Released"})
		return move_line_obj.print_journal_item(cr, uid, move_line_ids, context=ctx)

statement_print_journal_items()