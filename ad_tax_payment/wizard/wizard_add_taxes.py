import time
import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools

class account_move_line_tax_wizard(osv.osv_memory):
	_name = "account.move.line.tax.wizard"
	_columns = {
		"name"				: fields.char("Description"),
		"move_line_id"		: fields.many2one("account.move.line","Move Line",required=True),
		"partner_id"		: fields.many2one("res.partner","Partner"),
		"invoice_id"		: fields.many2one("account.invoice","Invoice"),
		"amount"			: fields.float("Amount",required=True,digits_compute=dp.get_precision('Account')),
		"currency_id"		: fields.many2one("res.currency","Currency"),
		"amount_currency"	: fields.float("Amount Currency", digits_compute=dp.get_precision('Account')),
		"effective_date"	: fields.date("Effective Date",required=False),
		"wizard_add_tax_id"	: fields.many2one("wizard.add.taxes","Tax Wizard"),
	}

class wizard_add_taxes(osv.osv_memory):
	_name = "wizard.add.taxes"
	_columns = {
		'tax_move_line_ids': fields.one2many('account.move.line.tax.wizard','wizard_add_tax_id','Outstanding Tax'),
	}

	def generate_tax(self, cr, uid, ids, context=None):
		if context is None: context = {}
		try:
			gen = self.browse(cr,uid,ids)[0]
		except:
			gen = self.browse(cr,uid,ids)
		ttype = context.get('type',False)
		for line in gen.tax_move_line_ids:
			val = {
				"move_line_id"		: line.move_line_id and line.move_line_id.id or False,
				"payment_id_dr"		: ttype == 'tax_lines_dr' and context.get('active_id',False),
				"payment_id_cr"		: ttype == 'tax_lines_cr' and context.get('active_id',False),
				"payment_id_dr_kb"	: ttype == 'tax_lines_dr_kb' and context.get('active_id',False),
				"payment_id_cr_kb"	: ttype == 'tax_lines_cr_kb' and context.get('active_id',False),
				"payment_id_dr_unr"	: ttype == 'tax_lines_dr_unr' and context.get('active_id',False),
				"payment_id_cr_unr"	: ttype == 'tax_lines_cr_unr' and context.get('active_id',False),
				"invoice_id"		: line.invoice_id and line.invoice_id.id or False,
				"amount"			: line.amount or 0.0,
				"currency_id"		: line.currency_id and line.currency_id.id or False,
				"amount_currency"	: line.amount_currency or 0.0,
				"effective_date"	: line.effective_date or False,
			}
			self.pool.get('account.tax.payment.line').create(cr,uid,val,context=context)
		return True

	def default_get(self, cr, uid, fields_list, context=None):
		"""
		Returns default values for fields
		@param fields_list: list of fields, for which default values are required to be read
		@param context: context arguments, like lang, time zone

		@return: Returns a dict that contains default values for fields
		"""
		if context is None:
			context = {}
		date_start = datetime.date.today().strftime('%Y-01-01')
		date_end = datetime.date.today().strftime('%Y-%m-%d')

		values = super(wizard_add_taxes, self).default_get(cr, uid, fields_list, context=context)
		tax_ids = []
		if (context.get('active_id',False)):
			tax_payment = self.pool.get('account.tax.payment').browse(cr,uid,context.get('active_id',False))
			company_id = tax_payment.company_id and tax_payment.company_id.id or False
			tax_ids = [t.id for t in tax_payment.tax_type]
			date_end = tax_payment.date_end
		else:
			user = self.pool.get('res.users').browse(cr,uid,uid,context)
			company_id = user.company_id and user.company_id.id or False
			tax_ids=self.pool.get('account.tax').search(cr,uid,[('company_id','=',company_id)],context=context)
		tax_account_ids=[]
		tax_not_returned=[]
		tax_code_account_ids = []
		tax_code_unreturned = []
		for tax in self.pool.get('account.tax').browse(cr,uid,tax_ids,context):
			if not tax.inside_berikat and not tax.reported_unreturned:
				if tax.account_collected_id and tax.account_collected_id.id:
					tax_account_ids.append(tax.account_collected_id.id)
				if tax.account_paid_id and tax.account_paid_id.id:
					tax_account_ids.append(tax.account_paid_id and tax.account_paid_id.id)
				if tax.tax_code_id and tax.tax_code_id.id:
					tax_code_account_ids.append(tax.tax_code_id.id)
				if tax.ref_tax_code_id and tax.ref_tax_code_id.id:
					tax_code_account_ids.append(tax.ref_tax_code_id.id)
			else:
				if tax.account_collected_id and tax.account_collected_id.id:
					tax_not_returned.append(tax.account_collected_id and tax.account_collected_id.id)
				if tax.account_paid_id and tax.account_paid_id.id:
					tax_not_returned.append(tax.account_paid_id and tax.account_paid_id.id)
				if tax.tax_code_id and tax.tax_code_id.id:
					tax_code_unreturned.append(tax.tax_code_id and tax.tax_code_id.id)
				if tax.ref_tax_code_id and tax.ref_tax_code_id.id:
					tax_code_unreturned.append(tax.ref_tax_code_id and tax.ref_tax_code_id.id)
				#print "tax_not_returned==============",tax_not_returned
		tax_account_ids = list(set(tax_account_ids))
		tax_not_returned = list(set(tax_not_returned))
		tax_code_account_ids = list(set(tax_code_account_ids))
		tax_code_unreturned = list(set(tax_code_unreturned))
		company = self.pool.get('res.company').browse(cr,uid,company_id,context)
		if tax_account_ids or tax_not_returned:
			move_id = self.pool.get('account.move').search(cr,uid,[('state','=','posted'),('date',">=",date_start),('date',"<=",date_end)])
			existing_payment_line_ids = self.pool.get('account.tax.payment.line').search(cr,uid,[],context=context)
			existing_payment_lines = [epm.move_line_id.id for epm in self.pool.get('account.tax.payment.line').browse(cr,uid,existing_payment_line_ids)]
			existing_statement_ids = self.pool.get('account.tax.payment').search(cr,uid,[],context=context)
			existing_statements_move = [esm.move_id.id for esm in self.pool.get('account.tax.payment').browse(cr,uid,existing_statement_ids)]
			existing_statement_move_lines = self.pool.get('account.move.line').search(cr,uid,[('move_id','in',existing_statements_move)])
			existing_payment_lines += existing_statement_move_lines


		tax_lines_value=[]


		if context.get('type',False) == 'tax_lines_cr':
			move_lines = self.pool.get('account.move.line').search(cr,uid,[('id','not in',existing_payment_lines),\
				('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_account_ids),('account_id','in',tax_account_ids),\
				('state','=','valid'),('move_id','in',move_id),('debit','=',0.0),('credit',">=",0.0)])
			for line in self.pool.get('account.move.line').browse(cr,uid,move_lines,context=context):
				moves = line.move_id
				invoice_id=False
				for move_line in line.move_id.line_id:
					if move_line.invoice and move_line.invoice.id:
						invoice_id=move_line.invoice.id
				tax_lines={
					"name"				: line.name or line.ref or '/',
					"move_line_id"		: line.id,
					"invoice_id"		: invoice_id,
					"amount"			: line.debit or line.credit or 0.0,
					"currency_id"		: line.currency_id and line.currency_id.id or False,
					"amount_currency"	: line.amount_currency or 0.0,
					"effective_date"	: line.date or False,
					"partner_id"		: line.partner_id and line.partner_id.id or False,
					}
				tax_lines_value.append(tax_lines)
		elif context.get('type',False) == 'tax_lines_dr':
			move_lines = self.pool.get('account.move.line').search(cr,uid,[('id','not in',existing_payment_lines),\
				('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_account_ids),('account_id','in',tax_account_ids),\
				('state','=','valid'),('move_id','in',move_id),('debit','>=',0.0),('credit',"=",0.0)])

			for line in self.pool.get('account.move.line').browse(cr,uid,move_lines,context=context):
				moves = line.move_id
				invoice_id=False
				for move_line in line.move_id.line_id:
					if move_line.invoice and move_line.invoice.id:
						invoice_id=move_line.invoice.id
				tax_lines={
					"name"				: line.name or line.ref or '/',
					"move_line_id"		: line.id,
					"invoice_id"		: invoice_id,
					"amount"			: line.debit or line.credit or 0.0,
					"currency_id"		: line.currency_id and line.currency_id.id or False,
					"amount_currency"	: line.amount_currency or 0.0,
					"effective_date"	: line.date or False,
					"partner_id"		: line.partner_id and line.partner_id.id or False,
					}
				tax_lines_value.append(tax_lines)
		elif context.get('type',False) == 'tax_lines_cr_unr':
			move_lines_unreturned = self.pool.get('account.move.line').search(cr,uid,[('id','not in',existing_payment_lines),\
				('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_unreturned),('account_id','in',tax_not_returned),\
				('state','=','valid'),('move_id','in',move_id),('debit','=',0.0),('credit',">=",0.0)])
			for line in self.pool.get('account.move.line').browse(cr,uid,move_lines_unreturned,context=context):
				moves = line.move_id
				invoice_id=False
				for move_line in line.move_id.line_id:
					if move_line.invoice and move_line.invoice.id:
						invoice_id=move_line.invoice.id
				tax_lines={
					"name"				: line.name or line.ref or '/',
					"move_line_id"		: line.id,
					"invoice_id"		: invoice_id,
					"amount"			: line.debit or line.credit or 0.0,
					"currency_id"		: line.currency_id and line.currency_id.id or False,
					"amount_currency"	: line.amount_currency or 0.0,
					"effective_date"	: line.date or False,
					"partner_id"		: line.partner_id and line.partner_id.id or False,
					}
				tax_lines_value.append(tax_lines)
		elif context.get('type',False) == 'tax_lines_dr_unr':
			#move_lines = self.pool.get('account.move.line').search(cr,uid,[('account_id','not in',tax_not_returned),('id','not in',existing_payment_lines),('credit',"=",0.0),('debit',">=",0.0),('date',">=",date_start),('date',"<=",date_end),("account_id",'in',tax_account_ids),('move_id.state','=','posted'),('state','=','valid')],context=context)
			#move_lines_unreturned = self.pool.get('account.move.line').search(cr,uid,[('account_id','in',tax_not_returned),('id','not in',existing_payment_lines),('credit',"=",0.0),('debit',">=",0.0),('date',">=",date_start),('date',"<=",date_end),("account_id",'in',tax_account_ids),('move_id.state','=','posted'),('state','=','valid')],context=context)
			move_lines_unreturned = self.pool.get('account.move.line').search(cr,uid,[('id','not in',existing_payment_lines),\
				('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_unreturned),('account_id','in',tax_not_returned),\
				('state','=','valid'),('move_id','in',move_id),('debit','>=',0.0),('credit',"=",0.0)])

			for line in self.pool.get('account.move.line').browse(cr,uid,move_lines_unreturned,context=context):
				moves = line.move_id
				invoice_id=False
				for move_line in line.move_id.line_id:
					if move_line.invoice and move_line.invoice.id:
						invoice_id=move_line.invoice.id
				tax_lines={
					"name"				: line.name or line.ref or '/',
					"move_line_id"		: line.id,
					"invoice_id"		: invoice_id,
					"amount"			: line.debit or line.credit or 0.0,
					"currency_id"		: line.currency_id and line.currency_id.id or False,
					"amount_currency"	: line.amount_currency or 0.0,
					"effective_date"	: line.date or False,
					"partner_id"		: line.partner_id and line.partner_id.id or False,
					}
				tax_lines_value.append(tax_lines)
		values.update({'tax_move_line_ids':tax_lines_value})	
		
		return values
	