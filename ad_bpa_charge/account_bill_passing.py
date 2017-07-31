from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp

class account_bill_passing(osv.Model):
	_name = "account.bill.passing"
	_description = "Bill Passing Advice"

	_columns = {
		"name" : fields.char('Number', size=120, readonly=True, states={'draft':[('readonly',False)]}),
		"date_entry" : fields.date('Date Entry', readonly=True, states={'draft':[('readonly',False)]}),
		"date_due" : fields.date('Date Due', readonly=True, states={'draft':[('readonly',False)]}),
		"date_effective" : fields.date('Effective Due', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'account_id' : fields.many2one('account.account', 'Account', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		"journal_id" : fields.many2one('account.journal', 'Journal', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		"currency_id" : fields.many2one('res.currency', 'Currency', readonly=True, states={'draft':[('readonly',False)]}),
		"state" : fields.selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('cancelled','Cancelled')], 'State', readonly=True),
		"bill_lines" : fields.one2many('account.bill.passing.line','bill_id','Bill Lines', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		"company_id" : fields.many2one('res.company','Company',required=True),
		'invoice_ids' : fields.one2many('account.invoice','bill_id','Invoice(s)'),
		'default_expense_account_id': fields.many2one('account.account', 'Default Expense Account' , readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}, ),
		'default_tax_ids': fields.many2many('account.tax', 'account_bill_passing_tax_rel', 'bill_id', 'tax_id', 'Default Taxes', domain=[('parent_id','=',False)], readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
	}
	_defaults = {
		'state' : lambda *a:'draft',
		'date_entry' : time.strftime("%Y-%m-%d"),
		'name' : lambda *a:'/',
		'company_id' : lambda self, cr, uid, ids, context=None: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
	}

	def button_set_expense_account(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ctx = context.copy()
		
		bill = self.browse(cr, uid, ids, context=ctx)[0]
		if not bill.default_expense_account_id:
			raise osv.except_osv(_('Update Error!'), _('Please define Default Expense Account on this Bill Passing if you want to use this method'))

		account_id = bill.default_expense_account_id.id
		for line in bill.bill_lines:
			self.pool.get('account.bill.passing.line').write(cr, uid, line.id, {'account_id':account_id}, context=ctx)

		return True

	def button_set_taxes_on_line(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ctx = context.copy()
		
		bill = self.browse(cr, uid, ids, context=ctx)[0]
		if not bill.default_tax_ids:
			raise osv.except_osv(_('Update Error!'), _('Please define Default Expense Account on this Bill Passing if you want to use this method'))
		
		tax_ids = [x.id for x in bill.default_tax_ids]
		for line in bill.bill_lines:
			self.pool.get('account.bill.passing.line').write(cr, uid, line.id, {'bill_line_tax_id':[(6,0,tax_ids)]}, context=ctx)

		return True

	def action_confirm(self, cr, uid, ids, context=None):
		if context is None: 
			context={}
		self.write(cr, uid, ids, {'state':'confirmed'})	
		return True

	def action_approve(self, cr, uid, ids, context=None):
		if context is None: 
			context={}

		ai_obj = self.pool.get('account.invoice')
		ail_obj = self.pool.get('account.invoice.line')
		abpl_obj = self.pool.get('account.bill.passing.line')
		aic_obj = self.pool.get('account.invoice.commission')
		wf_service = netsvc.LocalService("workflow")
		for bill in self.browse(cr, uid, ids, context=context):
			cr.execute("\
				SELECT a.id, a.comm_id, a.invoice_id, a.invoice_line_id, a.type_of_charge, a.invoice_related_id, a.desciption, a.partner_id, a.account_id, a.amount, b.bill_prov_id\
				FROM account_bill_passing_line a \
				LEFT JOIN account_invoice_commission b ON b.bill_prov_id=a.id \
				WHERE bill_id='%s'\
				ORDER BY a.invoice_id,a.invoice_line_id,a.id"%(bill.id))
			bill_lines = cr.dictfetchall()
			# grouping bill_lines base on invoice_related_id and partner_id
			curr_partner_inv = {}
			for line in bill_lines:
				if not line.get('partner_id',False):
					continue
				
				key1 = line.get('partner_id',False)
				if key1 not in curr_partner_inv:
					curr_partner_inv.update({key1:None})
				curr_partner_inv[key1] = curr_partner_inv[key1] is None and line.get('invoice_id',False) or curr_partner_inv[key1]
			
			bill_lines_grouped1 = {} # to add for a new invoice
			bill_lines_grouped2 = {} # to add for a new invoice
			for line in bill_lines:
				# if not (line.get('invoice_id',False) or line.get('invoice_line_id',False)) and curr_partner_inv.get(line.get('partner_id',False),False):
				if curr_partner_inv.get(line.get('partner_id',False),False):
					key2 = curr_partner_inv.get(line.get('partner_id',False),False)
					if key2 not in bill_lines_grouped1:
						bill_lines_grouped1.update({key2:[]})
					bill_lines_grouped1[key2].append(line)
				else:
					key3 = (line.get('partner_id',False),False)
					if key3 not in bill_lines_grouped2:
						bill_lines_grouped2.update({key3:[]})
					bill_lines_grouped2[key3].append(line)
			
			# to update current invoice
			to_update_inv_ids = []
			for key_inv_id in bill_lines_grouped1.keys():
				context.update({'date_inv':bill.date_effective or bill.date_entry or False})
				to_update_inv_ids.append(key_inv_id)
				bill_lines = abpl_obj.browse(cr, uid, [x['id'] for x in bill_lines_grouped1[key_inv_id]])
				for line in bill_lines:
					invoice_line_vals = self._prepare_invoice_line(cr, uid, line, key_inv_id, context=context)
					if line.invoice_line_id:
						inv_line_id=line.invoice_line_id.id
						ail_obj.write(cr, uid, inv_line_id, {'invoice_id':key_inv_id})
					else:
						inv_line_id = ail_obj.create(cr, uid, invoice_line_vals, context=context)
						abpl_obj.write(cr, uid, line.id, {'invoice_line_id':inv_line_id})

					if not (line.comm_id or False) and (line.comm_provision_id or False):
						aic_obj.write(cr, uid, line.comm_provision_id.id, {'invoice_prov_id':key_inv_id,'invoice_prov_line_id':inv_line_id})
				abpl_obj.write(cr, uid, [x['id'] for x in bill_lines_grouped1[key_inv_id]], {'invoice_id':key_inv_id})
			if to_update_inv_ids:
				ai_obj.action_cancel_draft(cr, uid, to_update_inv_ids)
				ai_obj.button_reset_taxes(cr, uid, to_update_inv_ids, context=context)
				for inv in to_update_inv_ids:
					wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_open', cr)

			# to create new invoice
			to_add_inv_ids = []
			for key in bill_lines_grouped2.keys():
				context.update({'date_inv':bill.date_effective or bill.date_entry or False})
				invoice_vals = self._prepare_invoice(cr, uid, bill,key[0],'in_invoice',bill.journal_id.id, context=context)
				inv_id = ai_obj.create(cr, uid, invoice_vals, context=context)
				to_add_inv_ids.append(inv_id)
				bill_lines = abpl_obj.browse(cr, uid, [x['id'] for x in bill_lines_grouped2[key]])
				for line in bill_lines:
					invoice_line_vals = self._prepare_invoice_line(cr, uid, line, inv_id, context=context)
					inv_line_id = ail_obj.create(cr, uid, invoice_line_vals, context=context)
					abpl_obj.write(cr, uid, line.id, {'invoice_line_id':inv_line_id})

					if not (line.comm_id or False) and (line.comm_provision_id or False):
						aic_obj.write(cr, uid, line.comm_provision_id.id, {'invoice_prov_id':inv_id,'invoice_prov_line_id':inv_line_id})
				abpl_obj.write(cr, uid, [x['id'] for x in bill_lines_grouped2[key]], {'invoice_id':inv_id})
			if to_add_inv_ids:
				ai_obj.button_reset_taxes(cr, uid, to_add_inv_ids, context=context)
				for inv in to_add_inv_ids:
					wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_open', cr)
		self.write(cr, uid, ids, {'state':'approved'})
		return True

	def action_cancel_approve(self, cr, uid, ids, context=None):
		if context is None: 
			context={}
		wf_service = netsvc.LocalService("workflow")
		ai_obj = self.pool.get('account.invoice')
		for bill in self.browse(cr, uid, ids, context=context):
			for inv in bill.invoice_ids:
				wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
		self.write(cr, uid, ids, {'state':'confirmed'})
		return True

	def action_cancel(self, cr, uid, ids, context=None):
		if context is None: 
			context={}
		wf_service = netsvc.LocalService("workflow")
		ai_obj = self.pool.get('account.invoice')
		for bill in self.browse(cr, uid, ids, context=context):
			for inv in bill.invoice_ids:
				wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
		self.write(cr, uid, ids, {'state':'cancelled'})
		return True

	def action_set_to_draft(self, cr, uid, ids, context=None):
		if context is None: 
			context={}
		self.write(cr, uid, ids, {'state':'draft'})
		return True	

	# def action_create_payment(self, cr, uid, ids, context=None):
	# 	if context is None# 		context={}
		
	# 	for bill in self.browse(cr, uid, ids, context=context):
	# 	return True

	def _prepare_invoice(self, cr, uid, bill, partner_id, inv_type, journal_id, context=None):
		""" Builds the dict containing the values for the invoice
			@param picking: picking object
			@param partner: object of the partner to invoice
			@param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
			@param journal_id: ID of the accounting journal
			@return: dict that will be used to create the invoice object
		"""
		if isinstance(partner_id, int):
			partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
		invoice_vals = {
			'bill_id' : bill.id,
			# 'name': bill.name,
			'origin': (bill.name or ''),
			'reference' : (bill.name or ''),
			'type': inv_type,
			'account_id': bill.account_id.id,
			'partner_id': partner.id,
			# 'comment': comment,
			# 'payment_term': payment_term,
			# 'fiscal_position': partner.property_account_position.id,
			'date_invoice': context.get('date_inv', False),
			'company_id': bill.company_id.id,
			'user_id': uid,
			'charge_type':'sale',
			'currency_tax_id':bill.company_id.currency_id.id,
		}
		cur_id = bill.currency_id.id
		if cur_id:
			invoice_vals['currency_id'] = cur_id
		if journal_id:
			invoice_vals['journal_id'] = journal_id
		return invoice_vals

	def _prepare_invoice_line(self, cr, uid, bill_line, invoice_id, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param: bill_line: account_bill_passing_line object
			@param: invoice_id: ID of the related invoice
			@return: dict that will be used to create the invoice line
		"""
		
		return {
			'name': bill_line.desciption or '-',
			'origin': '',
			'invoice_id': invoice_id,
			'account_id': bill_line.account_id.id,
			'price_unit': bill_line.amount,
			'quantity': 1.0,
			'invoice_related_id':bill_line.invoice_related_id.id,
			'invoice_line_tax_id':[(6, 0, [x.id for x in bill_line.bill_line_tax_id])],
		}
	

class account_bill_passing_line(osv.Model):
	_name = "account.bill.passing.line"
	_description = "Bill Passing Advice Line"

	def _get_amount_tax(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.amount
			taxes = tax_obj.compute_all(cr, uid, line.bill_line_tax_id, price, 1.0, product=False, partner=line.partner_id)
			res[line.id] = taxes['total_included'] - taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	_columns = {
		'bill_id' : fields.many2one('account.bill.passing','Reference'),
		'comm_id' : fields.many2one('account.invoice.commission','Commission'),
		'comm_provision_id' : fields.many2one('account.invoice.commission','Commission'),
		'invoice_id' : fields.many2one('account.invoice','Invoice'),
		'invoice_line_id' : fields.many2one('account.invoice.line','Invoice Line'),
		'type_of_charge': fields.many2one('charge.type', 'Type'),
		'invoice_related_id' : fields.many2one('account.invoice','Charge for Invoice'),
		"desciption" : fields.char('Description', size=320),
		"bill_date" : fields.date('Bill Date'),
		"partner_id" : fields.many2one('res.partner','Partner'),
		'account_id' : fields.many2one('account.account', 'Account'),
		"amount" : fields.float('Amount', required=True, digits_compute=dp.get_precision('Account')),
		'bill_line_tax_id': fields.many2many('account.tax', 'account_bill_pass_line_tax_rel', 'bill_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
		'tax_amount':fields.function(_get_amount_tax, type='float', method=True, string='Tax Amount', digits_compute=dp.get_precision('Account'),store={
				'account.bill.passing.line':(lambda self,cr,uid,ids,context={}:ids,['bill_line_tax_id','amount'],10),
			}),
	}
