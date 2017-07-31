from openerp.osv import fields, osv
import time
from tools.translate import _

class invoice_print_journal_items(osv.TransientModel):
	_name = "invoice.print.journal.items"
	_columns = {
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(invoice_print_journal_items, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if not inv.move_id:
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice has not yet have a Journal Entry'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('One/None of these Invoices has not yet have Journal Entries'))
		return res
	
	def print_journal_item(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('account.invoice')
		move_line_obj = self.pool.get('account.move.line')
		
		active_ids = context.get('active_ids',[])
		move_line_ids = []
		for inv in pool_obj.browse(cr, uid, active_ids, context=context):
			if inv.move_id:
				for line in inv.move_id.line_id:
					move_line_ids.append(line.id)
		ctx = context.copy()
		ctx.update({'header':"AR/AP Journal Entry for Released"})
		return move_line_obj.print_journal_item(cr, uid, move_line_ids, context=ctx)

invoice_print_journal_items()