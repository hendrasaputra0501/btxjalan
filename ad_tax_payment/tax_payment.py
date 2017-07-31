from openerp.osv import fields,osv
import datetime
import decimal_precision as dp
from tools.translate import _
from openerp import netsvc


class account_tax_payment(osv.osv):
	_name="account.tax.payment"
	_columns ={
		"name"				: fields.char("Number",size=64,required=True),
		"partner_id"		: fields.many2one("res.partner",'Tax Return Partner',domain="[('government_tax_partner','=',True)]"),
		"payment_method"	: fields.many2one("account.journal","Payment Method",required=True,domain="[('type','in',('cash','bank'))]"),
		"journal_id"		: fields.many2one("account.journal","Journal Name",required=True),
		"date_start"		: fields.date("Start Date",required=True),
		"date_end"			: fields.date("End Date",required=True),
		"period_id"			: fields.many2one("account.period","Period",required=True),
		"submit_date"		: fields.date("Date",required=True),
		"effective_date"	: fields.related('move_id','date',type="date",string="Effective Date"),
		'tax_type'			: fields.many2many('account.tax','account_tax_payment_rel','payment_id','tax_id',string='Tax Type', required=False, readonly=True, states={'draft':[('readonly',False)]}),
		"company_id"		: fields.many2one("res.company",required=True),
		"move_id"			: fields.many2one('account.move',"Journal Entry"),
		'move_ids'			: fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True, states={'draft':[('readonly',False)]}),
		"amount_total"		: fields.float("Amount Total",required=True,digits_compute=dp.get_precision('Account')),
		"tax_lines_dr" 		: fields.one2many("account.tax.payment.line","payment_id_dr","Taxes(Dr)"),
		"tax_lines_cr" 		: fields.one2many("account.tax.payment.line","payment_id_cr","Taxes(Cr)"),
		"tax_lines_dr_kb"	: fields.one2many("account.tax.payment.line","payment_id_dr_kb","Taxes(Dr) Kawasan Berikat"),
		"tax_lines_cr_kb"	: fields.one2many("account.tax.payment.line","payment_id_cr_kb","Taxes(Cr) Kawasan Berikat"),
		"tax_lines_dr_unr"	: fields.one2many("account.tax.payment.line","payment_id_dr_unr","Taxes(Dr) Unreturned"),
		"tax_lines_cr_unr"	: fields.one2many("account.tax.payment.line","payment_id_cr_unr","Taxes(Cr) Unreturned"),
		"voucher_id"		: fields.many2one("account.voucher","Voucher"),
		"voucher_move_id"	: fields.related("voucher_id",'move_id',type="many2one",relation="account.move",string="Voucher Journal",readonly=True,),
		'voucher_move_ids'	: fields.related('voucher_move_id','line_id', type='one2many', relation='account.move.line', string='Voucher Journal Items',readonly=True,),
		'state'				: fields.selection([
								('cancel','Cancelled'),
								('draft','Draft'),
								('tax_stated','Ready to be paid'),
								('voucher',"Voucher Created"),
								('done','Paid'),
		],'State', readonly=True,),
	}

	def _get_partner_return(self,cr,uid,context=None):
		if not context:context={}
		partner_id = self.pool.get('res.partner').search(cr,uid,[('government_tax_partner','=',True)],context=context)
		if partner_id:
			try:
				return partner_id[0]
			except:
				return partner_id
		return False


	_defaults={
		"state"			: lambda *a:"draft",
		"partner_id"	: _get_partner_return,
		"submit_date"	: lambda *a:datetime.date.today().strftime("%Y-%m-%d"),
		"date_start"	: lambda *a:datetime.date.today().strftime("%Y-%m-01"),
		"company_id"	: lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id,
		'name'			: lambda *a:'/'
	}

	def onchange_date(self,cr,uid,ids,date_start,date_end,company_id,tax_type,tax_lines_dr,tax_lines_cr,context=None):
		value={}
		if date_start and date_end:
			if datetime.datetime.strptime(date_start,"%Y-%m-%d") >= datetime.datetime.strptime(date_end,"%Y-%m-%d"):
				raise osv.except_osv(_('Invalid action !'), _("End Date should be greater than Start Date!"))
			else:
				if company_id:
					company_id=company_id or False
				else:
					user = self.pool.get('res.users').browse(cr,uid,uid,context)
					company_id = user.company_id and user.company_id.id or False
				if tax_type:
					tax_ids = tax_type[0][2]
				else:
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
				tax_account_ids = list(set(tax_account_ids))
				tax_not_returned = list(set(tax_not_returned))
				tax_code_account_ids = list(set(tax_code_account_ids))
				tax_code_unreturned = list(set(tax_code_unreturned))
				company = self.pool.get('res.company').browse(cr,uid,company_id,context)
				if tax_account_ids or tax_not_returned:
					move_id = self.pool.get('account.move').search(cr,uid,[('state','=','posted'),('date',">=",date_start),('date',"<=",date_end)])
					existing_payment_line_ids = self.pool.get('account.tax.payment.line').search(cr,uid,[],context)
					existing_payment_lines = [epm.move_line_id.id for epm in self.pool.get('account.tax.payment.line').browse(cr,uid,existing_payment_line_ids)]
					existing_statement_ids = self.pool.get('account.tax.payment').search(cr,uid,[],context)
					existing_statements_move = [esm.move_id.id for esm in self.pool.get('account.tax.payment').browse(cr,uid,existing_statement_ids)]
					existing_statement_move_lines = self.pool.get('account.move.line').search(cr,uid,[('move_id','in',existing_statements_move)])
					existing_payment_lines += existing_statement_move_lines

					tax_lines_dr=[]
					tax_lines_cr=[]
					tax_lines_dr_unr = []
					tax_lines_cr_unr = []


					move_lines = self.pool.get('account.move.line').search(cr,uid,[\
						('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_account_ids),('account_id','in',tax_account_ids),\
						('state','=','valid'),('move_id','in',move_id)])
					move_lines_unreturned = self.pool.get('account.move.line').search(cr,uid,[\
						('date','>=',date_start),('date','<=',date_end),('tax_code_id','in',tax_code_unreturned),('account_id','in',tax_not_returned),\
						('state','=','valid'),('move_id','in',move_id)])
					# print "tax_not_returned==============",move_lines,move_lines_unreturned
					for line in self.pool.get('account.move.line').browse(cr,uid,move_lines,context):
						moves = line.move_id
						invoice_id=False
						for move_line in line.move_id.line_id:
							if move_line.invoice and move_line.invoice.id:
								invoice_id=move_line.invoice.id
						tax_lines={
							"move_line_id"		: line.id,
							"invoice_id"		: invoice_id,
							"amount"			: line.debit or line.credit or 0.0,
							"currency_id"		: line.currency_id and line.currency_id.id or False,
							"amount_currency"	: line.amount_currency or 0.0,
							"effective_date"	: line.date or False,
						}

						if line.debit and line.debit>0:
							tax_lines_dr.append(tax_lines)
						else:
							tax_lines_cr.append(tax_lines)
					for line in self.pool.get('account.move.line').browse(cr,uid,move_lines_unreturned,context):
						moves = line.move_id
						invoice_id=False
						for move_line in line.move_id.line_id:
							if move_line.invoice and move_line.invoice.id:
								invoice_id=move_line.invoice.id
						tax_lines={
							"move_line_id"		: line.id,
							"invoice_id"		: invoice_id,
							"amount"			: line.debit or line.credit or 0.0,
							"currency_id"		: line.currency_id and line.currency_id.id or False,
							"amount_currency"	: line.amount_currency or 0.0,
							"effective_date"	: line.date or False,
						}
						if line.debit and line.debit>0:
							tax_lines_dr_unr.append(tax_lines)
						else:
							tax_lines_cr_unr.append(tax_lines)
					value.update({
						'tax_lines_dr':tax_lines_dr,
						'tax_lines_cr':tax_lines_cr,
						'tax_lines_dr_unr':tax_lines_dr_unr,
						'tax_lines_cr_unr':tax_lines_cr_unr
						})	
					# print "-----------------------",value
		return {'value':value,}

	def action_create_voucher(self,cr,uid,ids,context=None):
		if not context:context={}
		for statement in self.browse(cr,uid,ids,context=context):
			account_id = (statement.amount_total>0.0 and statement.payment_method and statement.payment_method.default_credit_account_id and statement.payment_method.default_credit_account_id.id) or \
						(statement.amount_total<0.0 and statement.payment_method and statement.payment_method.default_debit_account_id and statement.payment_method.default_debit_account_id.id) or \
						(statement.payment_method and statement.payment_method.default_credit_account_id and statement.payment_method.default_credit_account_id.id)
			type_voucher = statement.amount_total>=0.0 and 'payment' or 'receipt'
			amount =(statement.amount_total>0.0 and statement.amount_total) or (statement.amount_total*-1)
			voucher_vals = {
				'type':type_voucher,
				'name': "/",
				'partner_id': statement.partner_id and statement.partner_id.id,
				'journal_id': statement.payment_method and statement.payment_method.id,
				'account_id': account_id,
				'company_id': statement.company_id and statement.company_id.id or False,
				'currency_id': statement.company_id and statement.company_id.currency_id and statement.company_id.currency_id.id,
				'date': datetime.date.today().strftime('%Y-%m-%d'),
				'amount': amount,
				'period_id': statement.period_id and statement.period_id.id or False,
				"line_cr_ids":[],
				"line_dr_ids":[],
				}

			iml_ids = self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', statement.move_id.id), ('reconcile_id', '=', False),])
			if iml_ids:
				#context['invoice_id'] = invoice.id
				onchange_result=self.pool.get('account.voucher').onchange_partner_id(cr, uid, [],partner_id=statement.partner_id.id,
					journal_id=statement.payment_method and statement.payment_method.id or False, 
					amount=amount,currency_id=statement.company_id.currency_id.id,ttype=type_voucher,
					date=datetime.date.today().strftime('%Y-%m-%d'),
					context=context)['value']
				line_crs=[]
				for line_cr in onchange_result['line_cr_ids']:
					line_crs.append((0, 0, line_cr))
				onchange_result.update({'line_cr_ids':line_crs})
				line_drs=[]
				for line_dr in onchange_result['line_dr_ids']:
					line_drs.append((0, 0, line_dr))
				onchange_result.update({'line_dr_ids':line_drs})	
				# new_dr_line = []
				# if onchange_result and onchange_result['line_dr_ids']:
				# 	for dr_line in onchange_result['line_dr_ids']:
				# 		dr_line.update({})
				voucher_vals.update(onchange_result)
				print "voucher_vals=================",voucher_vals
				voucher_id = self.pool.get('account.voucher').create(cr, uid, voucher_vals, context=context)
			statement.write({'voucher_id':voucher_id,'state':'voucher'})		
		return True

	def action_validate(self,cr,uid,ids,context=None):
		if not context:context={}
		move_pool=self.pool.get('account.move')
		for statement in self.browse(cr,uid,ids,context):
			journal =statement.journal_id
			total_dr = 0.0
			total_cr = 0.0
			amount_currency = 0.0
			line = []
			name = self.pool.get('ir.sequence').next_by_code(cr, uid, journal.sequence_id.code, context=None)
			print "name=======",name
			move = {
				'name': name or "/",
				#'ref': name or "/",
				'line_id': line,
				'journal_id': statement.journal_id and statement.journal_id.id or False,
				'date': statement.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
				#'narration': name,
				#'company_id': statement.company_id and statement.company_id.id,
				"period_id":statement.period_id and statement.period_id.id or False,
				#"partner_id":statement.partner_id and statement.partner_id.id or False,
				#'amount': 0.0, 
				#'to_check':False, 
				#'balance': 0.0, 
				#'state':'draft',
				}
			for crx in statement.tax_lines_cr:
				total_cr += crx.move_line_id.credit or 0.0
				amount_currency += crx.move_line_id.amount_currency or 0.0
				#print "crx.move_line_id.account_id and crx.move_line_id.account_id",crx.move_line_id.account_id and crx.move_line_id.account_id.name
				cr_line = {

					'name': crx.move_line_id.name or "/",
					'debit': crx.move_line_id.credit,
					'credit': 0.0,
					'account_id': crx.move_line_id.account_id and crx.move_line_id.account_id.id or False,
					#'partner_id': crx.move_line_id.partner_id and crx.move_line_id.partner_id.id or False,
					#'tax_code_id': crx.move_line_id and crx.move_line_id.tax_code_id and crx.move_line_id.tax_code_id.id or False,
					#'tax_amount': crx.move_line_id and crx.move_line_id.tax_amount or False,
					'ref':crx.move_line_id.name or '/',
					'date': statement.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
					'currency_id':crx.move_line_id.currency_id and crx.move_line_id.currency_id.id or False,
					'amount_currency': (crx.move_line_id.amount_currency and (crx.move_line_id.amount_currency * -1)) or 0.0,
					'company_id': statement.company_id and statement.company_id.id or False,
					"period_id":statement.period_id and statement.period_id.id or False,
					}

				line.append((0,0,cr_line))

			for dr in statement.tax_lines_dr:
				total_dr += dr.move_line_id.debit or 0.0
				amount_currency += dr.move_line_id.amount_currency or 0.0
				dr_line = {
					'name': dr.move_line_id.name,
					'debit': 0.0,
					'credit': dr.move_line_id.debit,
					'account_id': dr.move_line_id.account_id and dr.move_line_id.account_id.id or False,
					#'partner_id': dr.move_line_id.partner_id and dr.move_line_id.partner_id.id or False,
					#'tax_code_id': dr.move_line_id and dr.move_line_id.tax_code_id and dr.move_line_id.tax_code_id.id or False,
					#'tax_amount': dr.move_line_id and dr.move_line_id.tax_amount or False,
					'ref':dr.move_line_id.name or '',
					'date': statement.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
					'currency_id':dr.move_line_id.currency_id and dr.move_line_id.currency_id.id or False,
					'amount_currency':(dr.move_line_id.amount_currency and (dr.move_line_id.amount_currency * -1)) or 0.0,
					'company_id': statement.company_id and statement.company_id.id or False,
					"period_id":statement.period_id and statement.period_id.id or False,
					}
				line.append((0,0,dr_line))
			total = total_dr - total_cr
			idr_currency = self.pool.get('res.currency').search(cr,uid,[('name','=','IDR')])
			#print "=================",idr_currency
			#idr_currency = 13
			if isinstance(idr_currency,(tuple,list)):
				idr_currency = idr_currency[0]
			ap_line = {
					'name': name,
					'debit': total>0.0 and total or 0.0,
					'credit': total<0.0 and (-1 * total) or 0.0,
					'account_id': (total>0.0 and journal.default_debit_account_id and journal.default_debit_account_id.id) or (total<0.0 and journal.default_credit_account_id and journal.default_credit_account_id.id) or journal.default_credit_account_id.id,
					'partner_id': statement.partner_id and statement.partner_id.id or False,
					'ref':name or '',
					'date': statement.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
					'currency_id':idr_currency,
					'amount_currency':amount_currency or 0.0,
					'company_id': statement.company_id and statement.company_id.id,
					"period_id":statement.period_id and statement.period_id.id or False,
					}
			line.append((0,0,ap_line))
			move.update({'line_id':line})
			print "move----------------",move
			move_id = move_pool.create(cr,uid,move,context=context)
			move_pool.post(cr,uid,[move_id])
			statement.write({'move_id':move_id,'name':name,'state':'tax_stated','amount_total':-1*total})
		return True

	def action_validate_voucher(self,cr,uid,ids,context=None):
		if not context:context={}
		wf_service = netsvc.LocalService("workflow")
		statements = []
		for statement in self.browse(cr,uid,ids,context):
			if statement.voucher_id:
				wf_service.trg_validate(uid, 'account.voucher', statement.voucher_id.id, 'proforma_voucher', cr)
				statements.append(statement.id)
			else:
				continue
		return self.write(cr,uid,statements,{'state':'done'})

	def action_cancel(self,cr,uid,ids,context=None):
		if not context:context={}
		statement = self.browse(cr,uid,ids,context)[0]
		if statement.state == 'done':
			if statement.voucher_id:
				self.pool.get('account.voucher').cancel_voucher(cr,uid,[statement.voucher_id.id],context)
				self.pool.get('account.voucher').action_cancel_draft(cr,uid,[statement.voucher_id.id],context)
				statement.write({'state':'voucher'})
		if statement.state == 'voucher':
			if statement.voucher_id and statement.voucher_id.id:
				self.pool.get('account.voucher').unlink(cr,uid,[statement.voucher_id.id])
			statement.write({'voucher_move_id':False,'state':'tax_stated'})
		if statement.move_id and statement.move_id.id and statement.state == 'tax_stated':
			self.pool.get('account.move').button_cancel(cr,uid,[statement.move_id.id])
			self.pool.get('account.move').unlink(cr,uid,[statement.move_id.id])
			statement.write({'move_id':False,'state':'cancel','amount_total':0.0,'name':'/'})
		return True

	def action_draft(self,cr,uid,ids,context=None):
		if not context:
			context={}
		return self.write(cr,uid,ids,{'state':'draft'})

class account_tax_payment_line(osv.osv):
	_name="account.tax.payment.line"
	_columns={
		"move_line_id"		: fields.many2one("account.move.line","Move Line"),
		"payment_id_dr"		: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment'),
		"payment_id_cr"		: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment'),
		"payment_id_dr_kb"	: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment KB'),
		"payment_id_cr_kb"	: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment KB'),
		"payment_id_dr_unr"	: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment Unreturned'),
		"payment_id_cr_unr"	: fields.many2one("account.tax.payment",ondelete="cascade",string='Payment Unreturned'),
		"invoice_id"		: fields.many2one("account.invoice","Invoice"),
		"amount"			: fields.float("Amount",required=True,digits_compute=dp.get_precision('Account')),
		"currency_id"		: fields.many2one("res.currency","Currency"),
		"amount_currency"	: fields.float("Amount Currency", digits_compute=dp.get_precision('Account')),
		"effective_date"	: fields.date("Effective Date",required=False),
	}

	_defaults = {
		"invoice_id":False,
		"amount":0.0,
		"effective_date":False,
	}