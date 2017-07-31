from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler

from openerp.tools.translate import _

class account_invoice_default_expense(osv.osv_memory):
	_name = "account.invoice.default.expense"
	
	_columns = {
		'default_expense_account': fields.many2one('account.account', 'Default Expense Account',domain="[('type','not in',('view','closed'))]",required=True),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_default_expense, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def set_default_expense_account(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['default_expense_account'])
		invoice_line_ids = invoice_line_pool.search(cr, uid, [('invoice_id','in',active_ids)])
		invoice_pool.write(cr, uid, active_ids, {'default_expense_account_id':data[0]['default_expense_account'][0]})
		invoice_line_pool.write(cr, uid, invoice_line_ids, {'account_id':data[0]['default_expense_account'][0]})
		return True

account_invoice_default_expense()

class account_invoice_default_account(osv.osv_memory):
	_name = "account.invoice.default.account"
	
	_columns = {
		'default_account_id': fields.many2one('account.account', 'Default Account AR/AP',domain="[('type','not in',('view','closed')),('type','in',('receivable','payable'))]",required=True),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_default_account, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def set_default_account(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['default_account_id'])
		invoice_line_ids = invoice_line_pool.search(cr, uid, [('invoice_id','in',active_ids)])
		invoice_pool.write(cr, uid, active_ids, {'account_id':data[0]['default_account_id'][0]})
		return True

account_invoice_default_account()

class account_invoice_default_date_effective(osv.osv_memory):
	_name = "account.invoice.default.date.effective"
	
	_columns = {
		'default_date_effective': fields.date('Effective Date', required=True),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_default_date_effective, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def set_default_date_effective(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['default_date_effective'])
		invoice_line_ids = invoice_line_pool.search(cr, uid, [('invoice_id','in',active_ids)])
		invoice_pool.write(cr, uid, active_ids, {'date_effective':data[0]['default_date_effective']})
		return True

account_invoice_default_date_effective()

class account_invoice_default_journal(osv.osv_memory):
	_name = "account.invoice.default.journal"
	
	_columns = {
		'default_journal_id': fields.many2one('account.journal', 'Default Journal',domain="[('type','in',('sale','sale_refund'))]",required=True),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_default_journal, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def set_default_journal(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['default_journal_id'])
		invoice_line_ids = invoice_line_pool.search(cr, uid, [('invoice_id','in',active_ids)])
		invoice_pool.write(cr, uid, active_ids, {'journal_id':data[0]['default_journal_id'][0]})
		return True

account_invoice_default_journal()

class account_invoice_default_taxes(osv.osv_memory):
	_name = "account.invoice.default.taxes"
	
	_columns = {
		'override' : fields.boolean("Do you want to override current taxes?"), 
		'tax_ids': fields.many2many('account.tax', 'default_taxes_account_tax_rel', 'wizard_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_default_taxes, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def set_default_taxes(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['override','tax_ids'])
		if active_ids:
			invoice_line_ids = invoice_line_pool.search(cr, uid, [('invoice_id','in',active_ids)])
			if invoice_line_ids:
				for line in invoice_line_pool.browse(cr, uid, invoice_line_ids):
					if data[0]['override']:
						invoice_line_pool.write(cr, uid, line.id, {'invoice_line_tax_id':[(6,0,data[0]['tax_ids'])]})
					else:
						curr_tax_ids = map(lambda c:c.id, [tax for tax in line.invoice_line_tax_id if tax.id not in data[0]['tax_ids']])
						invoice_line_pool.write(cr, uid, line.id, {'invoice_line_tax_id':[(6,0,data[0]['tax_ids']+curr_tax_ids)]})
				
				invoice_pool.button_reset_taxes(cr, uid, active_ids)
		return True

account_invoice_default_taxes()

class account_invoice_reset_taxes(osv.osv_memory):
	_name = "account.invoice.reset.taxes"
	
	_columns = {
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(account_invoice_reset_taxes, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in invoice_pool.browse(cr, uid, active_ids, context=context):
			if inv.state in ('open','paid','cancel'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Invoices was already generate Journal Entries'))
		return res

	def reset_taxes(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		
		active_ids = context.get('active_ids', [])
		if active_ids:
			invoice_pool.button_reset_taxes(cr, uid, active_ids)
		return True

account_invoice_reset_taxes()

class account_invoice_draft(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft invoices
	"""

	_name = "account.invoice.draft"
	_description = "Set to Draft the selected invoices"

	def invoice_set_draft(self, cr, uid, ids, context=None):
		wf_service = netsvc.LocalService('workflow')
		if context is None:
			context = {}
		pool_obj = pooler.get_pool(cr.dbname)
		data_inv = pool_obj.get('account.invoice').read(cr, uid, context['active_ids'], ['state'], context=context)

		for record in data_inv:
			if record['state']!='cancel':
				raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be set to draft as they are not in 'Cancelled' state."))
		
		self.pool.get('account.invoice').action_cancel_draft(cr, uid, context['active_ids'])
		return {'type': 'ir.actions.act_window_close'}

account_invoice_draft()

class account_invoice_proforma(osv.osv_memory):
	"""
	This wizard will confirm the all the selected draft invoices
	"""

	_name = "account.invoice.proforma"
	_description = "Set to Draft the selected invoices"

	def invoice_proforma(self, cr, uid, ids, context=None):
		wf_service = netsvc.LocalService('workflow')
		if context is None:
			context = {}
		pool_obj = pooler.get_pool(cr.dbname)
		data_inv = pool_obj.get('account.invoice').read(cr, uid, context['active_ids'], ['state'], context=context)

		for record in data_inv:
			if record['state']!='draft':
				raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be release as they are not in 'Draft' state."))
		
		for record in data_inv:
			wf_service.trg_validate(uid, 'account.invoice', record['id'], 'invoice_proforma2', cr)
		return {'type': 'ir.actions.act_window_close'}

account_invoice_proforma()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: