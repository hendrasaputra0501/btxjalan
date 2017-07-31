from openerp.osv import fields, osv
import time
from tools.translate import _

class desc_invoice_line_wizard(osv.TransientModel):
	_name = "desc.invoice.line.wizard"
	_columns = {
		'desc':fields.text("Desc"),
	}

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		# no call to super!
		res = {}
		line_id = context.get('active_id', [])
		if not line_id or not context.get('active_model') == 'account.invoice.line':
			return res
		if 'desc' in fields:
			line = self.pool.get('account.invoice.line').browse(cr, uid, line_id, context=context)
			res.update(desc=line.name)
		return res
	
	def set_desc(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('account.invoice.line')
		desc = self.browse(cr, uid, ids[0], context=context).desc or ''
		pool_obj.write(cr, uid, context['active_ids'], {'name':desc}, context=context)
		return {'type': 'ir.actions.act_window_close'}

desc_invoice_line_wizard()