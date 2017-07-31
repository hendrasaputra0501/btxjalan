from openerp.osv import fields, osv

from openerp.tools.translate import _

class wizard_bpa_commission(osv.osv_memory):
	_name = "wizard.bpa.commission"
	_description = "Wizard BPA Commission"

	_columns = {
		# 'journal_id': fields.many2one('account.journal', 'Destination Journal',domain="[('type','in',('bank','cash'))]",required=True),
		'currency_id' : fields.many2one('res.currency','Currency', required=True),
		'use_kmk_rate' : fields.boolean('Use KMK rate?'),
		'date_supplier_invoice': fields.date('Debit Note Date', required=True),
		'bpa_date': fields.date('BPA Request date', required=True),
		'due_date': fields.date('BPA Due date'),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(wizard_bpa_commission, self).view_init(cr, uid, fields_list, context=context)
		comm_pool = self.pool.get('account.invoice.commission')
		active_ids = context.get('active_ids',[])
		count = 0
		if active_ids and context.get('provision',False):
			comms = comm_pool.browse(cr, uid, active_ids, context=context)
			for comm in comms:
				if comm.invoice_prov_id or \
					comm.invoice_prov_line_id or \
					not comm.amount_outstanding or \
					comm.amount_outstanding<0 or \
					comm.amount_invoiced>=round(comm.commission_amount,2):
					count += 1
			if len(active_ids) == 1 and count:
				raise osv.except_osv(_('Warning!'), _('This Agents does not require Provision.'))
			if count:
				raise osv.except_osv(_('Warning!'), _('There are agents that doesnt require Provision'))
		elif active_ids:
			comms = comm_pool.browse(cr, uid, active_ids, context=context)
			for comm in comms:
				if not comm.amount_outstanding or \
					comm.amount_outstanding<0 :
					count += 1
			if len(active_ids) == 1 and count:
				raise osv.except_osv(_('Warning!'), _('This Agents does not require BPA.'))
			if count:
				raise osv.except_osv(_('Warning!'), _('There are agents that doesnt require BPA'))
		return res

	def open_bpa_commission(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		bpa_ids = []
		data_pool = self.pool.get('ir.model.data')
		res = self.create_bpa(cr, uid, ids, context=context)
		bpa_ids += res.values()
		action_model = False
		action = {}
		if not bpa_ids:
			raise osv.except_osv(_('Error!'), _('Please create BPA Commission.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_sales_agent_bitratex', 'action_account_bill_passing')
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,bpa_ids))+"])]"
		return action

	def create_bpa(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		comm_pool = self.pool.get('account.invoice.commission')
		oncommission_obj = self.read(cr, uid, ids, ['currency_id', 'bpa_date', 'due_date', 'use_kmk_rate','date_supplier_invoice'])
		context['bpa_date'] = oncommission_obj[0]['bpa_date']
		context['due_date'] = oncommission_obj[0]['due_date']
		context['use_kmk_rate'] = oncommission_obj[0]['use_kmk_rate']
		context['date_supplier_invoice'] = oncommission_obj[0]['date_supplier_invoice']
		active_ids = context.get('active_ids', [])
		if isinstance(oncommission_obj[0]['currency_id'], tuple):
			oncommission_obj[0]['currency_id'] = oncommission_obj[0]['currency_id'][0]
		if context.get('provision',False):
			res = comm_pool.action_create_bpa_provision(cr, uid, active_ids,
				  currency_id = oncommission_obj[0]['currency_id'],
				  context=context)
		else:
			res = comm_pool.action_create_bpa(cr, uid, active_ids,
				  currency_id = oncommission_obj[0]['currency_id'],
				  context=context)

		return res

wizard_bpa_commission()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: