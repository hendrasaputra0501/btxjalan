from openerp.osv import fields, osv
import time
from tools.translate import _

class ext_transaksi_print_journal_items(osv.TransientModel):
	_name = "ext.transaksi.print.journal.items"
	_columns = {
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(ext_transaksi_print_journal_items, self).view_init(cr, uid, fields_list, context=context)
		ext_transaksi_pool = self.pool.get('ext.transaksi')
		count = 0
		active_ids = context.get('active_ids',[])
		for ext in ext_transaksi_pool.browse(cr, uid, active_ids, context=context):
			if not ext.move_id:
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This extra transaksi has not yet have a Journal Entry'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('One/None of these extra transaksis has not yet have Journal Entries'))
		return res
	
	def print_journal_item(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('ext.transaksi')
		move_line_obj = self.pool.get('account.move.line')
		
		active_ids = context.get('active_ids',[])
		move_line_ids = []
		for ext in pool_obj.browse(cr, uid, active_ids, context=context):
			if ext.move_id:
				for line in ext.move_id.line_id:
					if line.id not in move_line_ids:
						move_line_ids.append(line.id)
			if ext.tax_move_id:
				for line in ext.tax_move_id.line_id:
					if line.id not in move_line_ids:
						move_line_ids.append(line.id)
		ctx = context.copy()
		ctx.update({'header':"Journal Entry for Released"})
		return move_line_obj.print_journal_item(cr, uid, move_line_ids, context=ctx)

ext_transaksi_print_journal_items()