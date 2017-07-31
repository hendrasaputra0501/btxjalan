from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
import time
from dateutil.relativedelta import relativedelta

class account_bank_loan_type(osv.Model):
	_name = "account.bank.loan.type"
	_columns = {
		"name" : fields.char('Type',size=128, required=True),
		"account_id" : fields.many2one('account.account','Account'),
		"int_rate_line" : fields.one2many('account.bank.loan.interest.rate','loan_type_id','Interest Rate'),
	}
account_bank_loan_type()

class account_bank_loan(osv.osv):
	def _amount_residual(self, cr, uid, ids, name, args, context=None):
		"""Function of the field residual. It computes the residual amount (balance) for each invoice"""
		if context is None:
			context = {}
		ctx = context.copy()
		result = {}
		currency_obj = self.pool.get('res.currency')
		for loan in self.browse(cr, uid, ids, context=context):
			nb_inv_in_partial_rec = max_invoice_id = 0
			result[loan.id] = 0.0
			if loan.move_id:
				for aml in loan.move_id.line_id:
					# if aml.account_id.type in ('receivable','payable'):
					if aml.account_id.id==loan.account_payable.id:
						if aml.currency_id and aml.currency_id.id == (loan.journal_id.currency.id or loan.journal_id.company_id.currency_id.id):
							result[loan.id] += aml.amount_residual_currency
						else:
							ctx['date'] = aml.date
							result[loan.id] += currency_obj.compute(cr, uid, aml.company_id.currency_id.id, (loan.journal_id.currency.id or loan.journal_id.company_id.currency_id.id), aml.amount_residual, context=ctx)

			#prevent the residual amount on the invoice to be less than 0
			result[loan.id] = max(result[loan.id], 0.0)
		return result

	def _get_move_line_id(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.move_id:
				for move_line in loan.move_id.line_id:
					if move_line.account_id.id==loan.account_payable.id:
						res[loan.id]=move_line.id		
		return res

	def _get_journal(self, cr, uid, context=None):
		if context is None:
			context = {}
		
		cur_obj = self.pool.get('res.currency')
		journal_obj = self.pool.get('account.journal')
		res = journal_obj.search(cr, uid, [('type','in',['bank','cash'])])

		return res and res[0] or False

	def _get_create_uid(self, cr, uid, ids, name, args, context=None):
		if context is None:
			context = {}
		res = {}
		ctx = context.copy()
		for v in self.browse(cr, uid, ids, context=context):
			cr.execute("select create_uid from account_bank_loan where id='%s'"%v.id)
			cr_id = cr.fetchone()[0]
			res[v.id] = cr_id
		return res

	_name = 'account.bank.loan'
	_columns = {
		'name' : fields.char('Name',size=50,required=True, readonly=True),
		'ref' : fields.char('Payment Ref',size=50, readonly=True, states={'draft':[('readonly',False)]}),
		'memo' : fields.char('Memo',size=240, readonly=True, states={'draft':[('readonly',False)]}),
		'loan_type' : fields.selection([('nego','Invoice Negotiation'),('tr','Transfer Receipt'),('others','Others')],'Loan Type',required=True,readonly=True,states={'draft':[('readonly',False)]}),
		'loan_type_id' : fields.many2one('account.bank.loan.type','Loan Classification'),
		'invoice_related_id' : fields.many2one('account.invoice','Related Invoice',readonly=True, states={'draft':[('readonly',False)]}),
		'partner_id' : fields.many2one('res.partner','Partner',readonly=True, states={'draft':[('readonly',False)]}),
		'journal_id' : fields.many2one('account.journal','Journal',readonly=True,required=True, states={'draft':[('readonly',False)]}),
		'date_request' : fields.date('Date of Request',readonly=True, states={'draft':[('readonly',False)]}),
		'effective_date' : fields.date('Effective Date',readonly=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'liability_move_line_id' : fields.function(_get_move_line_id,type='many2one',obj='account.move.line',string='Liability Entry Item',store=True),
		# 'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		# 'currency_id' : fields.many2one('res.currency','Currency',required=True, readonly=True,states={'draft':[('readonly',False)]}),
		'account_id': fields.many2one('account.account', 'Debit Account',required=True,readonly=True,states={'draft':[('readonly',False)]}),
		# 'residual_amount' : fields.float("Residual Amount", digits_compute= dp.get_precision('amount'),readonly=True),
		'residual_amount' : fields.function(_amount_residual, string='Residual Amount', digits_compute= dp.get_precision('Account')),
		'company_id' : fields.many2one('res.company','Company',readonly=True),
		'total_amount' : fields.float("Amount",required=True, digits_compute= dp.get_precision('Account'),readonly=True,states={'draft':[('readonly',False)]}),
		'account_payable': fields.many2one('account.account', 'Account Payable',required=True,readonly=True,states={'draft':[('readonly',False)]}),
		'note' : fields.text('Term',readonly=True,states={'draft':[('readonly',False)]}),
		'repayment_line' :  fields.one2many('account.bank.loan.repayment','loan_id','Repayment'),
		'int_rate_line' :  fields.one2many('account.bank.loan.interest.rate','loan_id','Interest Rate'),
		'int_line' :  fields.one2many('account.bank.loan.interest','loan_id','Interest'),
		'state' : fields.selection([
			('draft','Draft'),
			('confirm','Confirm'),
			('open','Open'),
			('paid','Paid'),
			('cancel','Cancelled')], 'State'),
		'use_scheduler' : fields.boolean('Use Scheduler',readonly=True,states={'draft':[('readonly',False)]}),
		'voucher_id' : fields.many2one('account.voucher','Reconcile Using Voucher', readonly=True,states={'open':[('readonly',False)]}),
		#this is Loan with Periodical Payment, 
		'config_type' : fields.selection([('manual','Manual'),('auto','Automatically')],'Configuration Type',required=True,readonly=True,states={'draft':[('readonly',False)]}),
		'payment_control' : fields.selection([('30','Every 30 days'),('monthly','Monthly')],'Pay Installment per',readonly=True, states={'draft':[('readonly',False)]},help="Pay Installment per Every 30 days, for example : \n Installment start on 1/1/2014. Next payment on 1/31/2014, 3/2/2014, 4/1/2014, etc.\n Pay Installment per Monthly, for example : \n First Installment on 1/1/2014. Next payment installment on 2/1/2014,3/1,2014,etc."),
		'date_start' : fields.date('Date Start',readonly=True, states={'draft':[('readonly',False)]}),
		'method_number' : fields.integer('Number of Installment Period', required=False,readonly=True,states={'draft':[('readonly',False)]}),
		# 'method_period' : fields.integer('Number of Months in a Period', required=True,readonly=True,states={'draft':[('readonly',False)]}),
		'intr_calc_method' : fields.selection([('custom','Custom'),('flat','Flat'),('efektif','Effective'),('anuitas','Annuities')],'Computation Method',readonly=True,states={'draft':[('readonly',False)]},help="- Flat : \n Interest per month : PV * i * N"),
		'interest_for' : fields.selection([('term1','30/360'),('term2','n days/360')],'Interest for',readonly=True,states={'draft':[('readonly',False)]},help="Interest Rate for 30/360 or Interest rate for n days/365."),
		'interest_perc' : fields.float('Interest Percentage', required=False,readonly=True,states={'draft':[('readonly',False)]}),
		'installment_line' :  fields.one2many('account.bank.loan.installment','loan_id','Installment',required=True,readonly=False),
		"create_by" : fields.function(_get_create_uid, type='many2one', obj='res.users', string='Create By', store=True),
	}

	_defaults = {
		'use_scheduler' : False,
		'loan_type':lambda *a:'nego',
		'state': lambda *a:'draft',
		'config_type' : lambda *a:'manual',
		'name' : '/',
		'date_request' : lambda *a:time.strftime('%Y-%m-%d'),
		'interest_for' : lambda *a:'term2', 
		'journal_id' : _get_journal,
		'company_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id or False,
		# 'currency_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
	}

	_order = 'id desc'

	def create(self,cr,uid,vals,context=None):
		
		if vals.get('journal_id',False) and vals.get('name','/')=='/':
			seq_obj = self.pool.get('ir.sequence')
			journal_id = self.pool.get('account.journal').browse(cr, uid, vals.get('journal_id',False),context=context)
			if journal_id.sequence_id:
				if not journal_id.sequence_id.active:
					raise osv.except_osv(_('Configuration Error !'),
						_('Please activate the sequence of selected journal !'))
				c = {}
				if vals.get('effective_date',False):
					c = {'date':datetime.strptime(vals['effective_date'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
				elif vals.get('date_request',False):
					c = {'date':datetime.strptime(vals['date_request'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
				name = seq_obj.next_by_id(cr, uid, journal_id.sequence_id.id, context=c)
				vals['name'] = name
			else:
				raise osv.except_osv(_('Error!'),
					_('Please define a sequence on the journal.'))
		
		return super(account_bank_loan,self).create(cr,uid,vals,context=context)

	def _get_company_currency(self, cr, uid, loan_id, context=None):
		return self.browse(cr,uid,loan_id,context).journal_id.company_id.currency_id.id

	def _get_current_currency(self, cr, uid, loan_id, context=None):
		loan = self.browse(cr,uid,loan_id,context)
		return loan.journal_id.currency.id or self._get_company_currency(cr,uid,loan.id,context)

	def button_test_paid(self, cr, uid, ids, context=None):
		if not context:
			context={}
		wf_service = netsvc.LocalService("workflow")
		loan = self.browse(cr,uid,ids,context)[0]
		voucher = loan.voucher_id and loan.voucher_id
		if voucher:
			cek_move = False
			for line in voucher.line_dr_ids + voucher.line_cr_ids:
				if line.move_line_id.id == loan.liability_move_line_id.id:
					cek_move = True
			if cek_move:
				wf_service.trg_validate(uid, 'account.bank.loan', loan.id, 'test_paid', cr)
			else:
				raise osv.except_osv(_('Error!'),
					_('The voucher doesnt have any relation with this Loan'))

		return True

	def account_move_get(self, cr, uid, loan_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		loan = self.browse(cr,uid,loan_id,context)
		effective_date = loan.effective_date!='False' and loan.effective_date or time.strftime('%Y-%m-%d')
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': loan.name or '',
			'ref': loan.ref or loan.name,
			'journal_id': loan.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
		}

		return move

	def onchange_total_amount(self,cr,uid,ids,amt,context=None):
		return {'value':{'residual_amount':amt}}

	def onchange_invoice(self,cr,uid,ids,invoice_id, journal_id,context=None):
		inv_obj = self.pool.get('account.invoice')
		journal_obj = self.pool.get('account.journal')
		inv = inv_obj.browse(cr, uid, invoice_id)
		journal = journal_obj.browse(cr, uid, journal_id)
		amount = 0.0
		if inv and journal:
			amount=self.pool.get('res.currency').compute(cr, uid, inv.currency_id.id, journal.currency.id or journal.company_id.currency_id.id, inv.amount_total, context=context)
		return {'value':{'total_amount':amount}}

	def onchange_journal(self,cr,uid,ids, journal_id,context=None):
		inv_obj = self.pool.get('account.invoice')
		journal_obj = self.pool.get('account.journal')
		journal = journal_obj.browse(cr, uid, journal_id)
		account_id = journal.default_debit_account_id and journal.default_debit_account_id.id or False
		return {'value':{'account_id':account_id}}

	def payable_move_line_get(self, cr, uid, loan_id, move_id, company_currency, current_currency, amount, context=None):
		loan = self.browse(cr,uid,loan_id,context)
		
		debit = credit = 0.0
		credit = amount

		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1
		effective_date = loan.effective_date!='False' and loan.effective_date or time.strftime('%Y-%m-%d')
		period=self.pool.get('account.period').find(cr,uid,dt=effective_date)
		account_id=loan.account_payable and loan.account_payable.id or False
		
		if not account_id:
			raise osv.except_osv(_('Configuration Error !'),
				_('Please set the account payable for this document'))

		move_line = {
			'name': loan.memo or '/',
			'ref' : loan.ref or loan.name or '',
			'debit': debit,
			'credit': credit,
			'account_id': account_id or False,
			'move_id': move_id,
			'journal_id': loan.journal_id.id,
			'period_id': period and period[0] or False,
			'partner_id': loan.partner_id.id,
			'currency_id': company_currency <> current_currency and  current_currency or False,
			'amount_currency': company_currency <> current_currency and sign * loan.total_amount or 0.0,
			'date': effective_date,
		}
		return move_line

	def destination_move_line_get(self, cr, uid, loan_id, move_id, company_currency, current_currency, amount, context=None):
		loan = self.browse(cr,uid,loan_id,context)
		
		debit = credit = 0.0
		debit = amount

		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1
		effective_date = loan.effective_date!='False' and loan.effective_date or time.strftime('%Y-%m-%d')
		period=self.pool.get('account.period').find(cr,uid,dt=effective_date)
		account_id=False
		
		if loan.account_id : 
			account_id = loan.account_id.id

		if not account_id and loan.journal_id.default_debit_account_id : 
			account_id = loan.journal_id.default_debit_account_id.id
		
		if not account_id:
			raise osv.except_osv(_('Configuration Error !'),
				_('Please set account debit or set the default debit account in this corresponding journal'))

		move_line = {
			'name': loan.memo or '/',
			'ref' : loan.ref or loan.name or '',
			'debit': debit,
			'credit': credit,
			'account_id': account_id or False,
			'move_id': move_id,
			'journal_id': loan.journal_id.id,
			'period_id': period and period[0] or False,
			'partner_id': loan.partner_id.id,
			'currency_id': company_currency <> current_currency and  current_currency or False,
			'amount_currency': company_currency <> current_currency and sign * loan.total_amount or 0.0,
			'date': effective_date,
		}
		return move_line

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.move_id:
				continue

			date = loan.effective_date!='False' and loan.effective_date or time.strftime('%Y-%m-%d')
			context.update({'date':date})
			company_currency = self._get_company_currency(cr, uid, loan.id, context)
			current_currency = self._get_current_currency(cr, uid, loan.id, context)

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, loan.id, context=context), context=context)
			name = move_pool.browse(cr, uid, move_id, context=context).name
			amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, loan.total_amount, context=context)
			
			move_line_pool.create(cr,uid,self.payable_move_line_get(cr, uid, loan.id, move_id, company_currency, current_currency, amount, context),context)
			move_line_pool.create(cr,uid,self.destination_move_line_get(cr, uid, loan.id, move_id, company_currency, current_currency, amount, context),context)

			if loan.config_type=='auto':
				for installment in loan.installment_line:
					installment_line_pool.write(cr, uid, installment.id, {'state':'open'})
			self.write(cr,uid,loan.id ,{'state':'open','move_id':move_id})
			if loan.move_id:
				move_pool.post(cr, uid, [move_id], context={})
		return True	

	def action_cancel_loan(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.repayment_line:
				for repayment in loan.repayment_line:
					if repayment.state=='paid':
						raise osv.except_osv(_('Cancel Error !'),
							_('Please Unreconcile All Repayment/Installment payment first'))

			move_pool.button_cancel(cr, uid, [loan.move_id.id])
			move_pool.unlink(cr, uid, [loan.move_id.id])
			
			self.write(cr,uid,loan.id ,{'state':'cancel','move_id':False})
		return True

	def action_paid(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		self.write(cr, uid, ids, {'state':'paid'}, context=context)
		return True

	def recompute_real_amount(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		repayment_pool = self.pool.get('account.bank.loan.repayment')
		# for loan in self.browse(cr, uid, ids, context=context):
		# 	repayment_paid_ids = []
		# 	total_paid = 0.0
		# 	for repayment in loan.repayment_line:
		# 		if repayment.state=='paid':
		# 			total_paid+=repayment.real_amount
		# 			repayment_paid_ids.append(repayment.id)
		# 	outstanding = loan.total_amount - total_paid

		# 	repayment_confrimed_ids = repayment_pool.search(cr, uid, [('loan_id','=',loan.id),('state','=','confirmed'),('id','not in',repayment_paid_ids)], order='id asc')
			
		# 	# variable temporary untuk menampung selisih revision_amount dgn real_amount
		# 	temp_amt = 0.0
		# 	for repayment in repayment_pool.browse(cr, uid, repayment_confrimed_ids, context=context):
		# 		revision_amount = repayment.revision_amount
		# 		if temp_amt:

		# 		if revision_amount:
		# 			# revision_amount += temp_amt
		# 			temp_amt = repayment.real_amount - revision_amount
		# 			if revision_amount > 0:
		# 				repayment_pool.write(cr, uid, repayment.id, {
		# 					'real_amount' : revision_amount,
		# 					'lastest_revision':revision_amount,
		# 					'revision_amount':0.0
		# 					})
		# 			else:
		# 				repayment_pool.write(cr, uid, repayment.id, {
		# 					'real_amount' : 0.0,
		# 					'lastest_revision':0.0,
		# 					'revision_amount':0.0
		# 					})

		# 		elif temp_amt and not revision_amount:
		# 			repayment_pool.write(cr, uid, repayment.id, {
		# 				'real_amount' : revision_amount,
		# 				'lastest_revision':revision_amount,
		# 				'revision_amount':0.0
		# 				})

		return True

	def recompute_interest(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		for loan in self.browse(cr, uid, ids, context=context):
			# calculating and creating the installment
			pv=loan.total_amount
			i=float(loan.interest_perc/100)
			residual_amount=pv
			seq=0
			for line in loan.installment_line:
				date_from=datetime.strptime(line.date_from,"%Y-%m-%d")
				date_to=datetime.strptime(line.date_to,"%Y-%m-%d")
				selisih=(date_to-date_from).days
				if loan.interest_for=='term1':
					n=30/360.00
				elif loan.interest_for=='term2':
					n=float(selisih)/360.00

				interest_per_periode=residual_amount*i*n
				residual_amount-=line.installment_amount

				installment_line_pool.write(cr, uid, line.id ,{
						'remain_amount':residual_amount,
						'interest_cost':interest_per_periode,
					})

		return True

	def action_confirm(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.move_id:
				continue

			if loan.config_type=='auto':

				# calculating and creating the installment
				start_date=datetime.strptime(loan.date_start,"%Y-%m-%d")
				pv=loan.total_amount
				i=float(loan.interest_perc/100)
				date_from=start_date
				residual_amount=pv
				seq=0
				for method_number in range(0,loan.method_number):
					seq=method_number+1
					if loan.payment_control=='30':
						date_to=date_from+relativedelta(days=+30)
					elif loan.payment_control=='monthly':
						date_to=date_from+relativedelta(months=+1)
					if loan.interest_for=='term1':
						n=30.00/360.00
					elif loan.interest_for=='term2':
						n=float((date_to-date_from).days)/360.00
					if loan.intr_calc_method=='flat' or loan.intr_calc_method=='custom':
						interest_per_month=pv*i*n
						installment_amount=pv/loan.method_number
						residual_amount-=installment_amount
						installment_line_pool.create(cr, uid, {
								'config_type':'auto',
								'name':'Installment '+str(seq),
								'date_from':date_from.strftime('%Y-%m-%d'),
								'date_to':date_to.strftime('%Y-%m-%d'),
								'installment_amount':installment_amount,
								'remain_amount':residual_amount,
								'interest_cost':interest_per_month,
								'state':'draft',
								'loan_id':loan.id,
							})
					elif loan.intr_calc_method=='efektif':
						interest_per_month=residual_amount*i*n
						installment_amount=pv/loan.method_number
						residual_amount-=installment_amount
						installment_line_pool.create(cr, uid, {
								'config_type':'auto',
								'name':'Installment '+str(seq),
								'date_from':date_from.strftime('%Y-%m-%d'),
								'date_to':date_to.strftime('%Y-%m-%d'),
								'installment_amount':installment_amount,
								'remain_amount':residual_amount,
								'interest_cost':interest_per_month,
								'state':'draft',
								'loan_id':loan.id,
							})
					elif loan.intr_calc_method=='anuitas':
						interest_per_month=residual_amount*i*n
						PMV=(pv*i*n)/(1-(1+i*n)**-loan.method_number)
						installment_amount=PMV-interest_per_month
						residual_amount-=installment_amount
						installment_line_pool.create(cr, uid, {
								'config_type':'auto',
								'name':'Installment '+str(seq),
								'date_from':date_from.strftime('%Y-%m-%d'),
								'date_to':date_to.strftime('%Y-%m-%d'),
								'installment_amount':installment_amount,
								'remain_amount':residual_amount,
								'interest_cost':interest_per_month,
								'state':'draft',
								'loan_id':loan.id,
							})
					date_from=date_to
			self.write(cr,uid,loan.id ,{'state':'confirm'})
		return True	

	def action_set_to_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		wf_service = netsvc.LocalService("workflow")
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.move_id:
				continue

			for line in loan.installment_line:
				installment_line_pool.unlink(cr,uid,line.id)

			wf_service.trg_delete(uid, 'account.bank.loan', loan.id, cr)
			wf_service.trg_create(uid, 'account.bank.loan', loan.id, cr)
			self.write(cr,uid,loan.id ,{'state':'draft'})
		return True

	def test_paid(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		installment_line_pool = self.pool.get('account.bank.loan.installment')
		loan = self.browse(cr, uid, ids, context=context)[0]
		ok1 = True
		cr.execute('select reconcile_id from account_move_line where id=%s', (loan.liability_move_line_id.id,))
		ok1 = ok1 and bool(cr.fetchone()[0])

		ok2 = loan.liability_move_line_id and loan.liability_move_line_id.amount_residual < 0 and True or False
		return ok1 or ok2 

class account_bank_loan_installment(osv.osv):
	def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			subtotal = line.installment_amount + line.interest_cost
			res[line.id] = subtotal
		return res

	_name = 'account.bank.loan.installment'
	_columns = {
		'name' : fields.char('Sequence',size=20),
		'loan_id':fields.many2one('account.bank.loan','Bank Loan'),
		'liability_move_line_id' : fields.related('loan_id','liability_move_line_id',type='many2one',relation='account.move.line',string='Liability Entry Item'),
		'config_type' : fields.selection([('manual','Manual'),('auto','Automatically')],'Configuration Type'),
		'date_from' : fields.date('Date from',readonly=False, required=True),
		'date_to' : fields.date('Date to',readonly=False,required=True),
		'installment_amount' : fields.float("Installment Amount",required=True, digits_compute= dp.get_precision('Account')),
		'residual_amount' : fields.float("Residual Amount", digits_compute= dp.get_precision('Account'),readonly=False),
		'remain_amount' : fields.float("Remaining Balance", digits_compute= dp.get_precision('Account')),
		'date_payment' : fields.date('Date Payment',readonly=True, states={'payment':[('readonly',False)]}),
		'journal_id' : fields.many2one('account.journal','Payment Method',readonly=True, states={'payment':[('readonly',False)]}),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'interest_cost' : fields.float("Interest Amount",required=False, digits_compute= dp.get_precision('Account'),readonly=False),
		'interest_perc' : fields.float('Interest Rate % '),
		'account_interest': fields.many2one('account.account', 'Account Interest',required=False,readonly=True,states={'payment':[('readonly',False)]}),
		# 'adm_cost' : fields.float("Payment Adm",required=False, digits_compute= dp.get_precision('amount'),readonly=True, states={'payment':[('readonly',False)]}),
		'adm_cost_ids' : fields.one2many("account.bank.loan.installment.expense","installment_id", "Payment Adm",required=False, readonly=True, states={'payment':[('readonly',False)]}),		
		'total_amount' : fields.function(_amount_line, string='Total Amount', digits_compute= dp.get_precision('Account')),
		# 'interest_id': fields.many2one('account.interest','Payment'),
		'state' : fields.selection([
			('draft','Draft'),
			('open','Computed'),
			('open2','Open'),
			('payment','Register Payment'),
			('paid','Paid'),
			('cancel','Cancelled')], 'State'),
	}

	_defaults = {
		'residual_amount' : lambda self, cr, uid, context: context.get('residual_amount',0.0),
		'config_type' : lambda self, cr, uid, context: context.get('config_type','manual'),
		'state':lambda *a:'draft',
	}

	_order = 'date_from asc'

	def create(self,cr,uid,vals,context=None):
		loan_id = vals['loan_id']
		installment_ids = self.search(cr, uid, [('loan_id','=',loan_id)])
		loan=self.pool.get('account.bank.loan').browse(cr, uid, loan_id)
		if loan.state=='draft':
			raise osv.except_osv(_('Creation Error !'),
				_('Please confirm the Loan first before creating the new Installment! \
				\n Please Delete your new Payment/Installment data before continue'))
		else:
			if not installment_ids:
				return super(account_bank_loan_installment,self).create(cr,uid,vals,context=context)
			else:
				installment = self.browse(cr, uid, installment_ids)
				check = False
				for line in installment:
					if line.state!='paid':
						check = True

				if check == True:
					raise osv.except_osv(_('Creation Error !'),
						_('Please pay previous Payment before creating the new one!\
						\n Please Delete your new Payment data before continue'))
				else:
					return super(account_bank_loan_installment,self).create(cr,uid,vals,context=context)

	def unlink(self,cr,uid,ids,context=None):
		installment = self.browse(cr, uid, ids)
		if installment.move_id or installment.move_id.state=='Post':
			raise osv.except_osv(_('Deletion Error !'),
				_('You cannot delete this Document, because there is document Jurnal Entries no '+ installment.move_id.name +'that related to this Document. \n \
				Please cancel its Journal Entries first before deleting this Installment/Payment! '))
		else:
			return super(account_bank_loan_installment,self).unlink(cr,uid,ids,context=context)

	def account_move_get(self, cr, uid, installment_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		installment = self.browse(cr,uid,installment_id,context)
		
		effective_date = installment.date_payment!='False' and installment.date_payment or time.strftime('%Y-%m-%d')
		if installment.journal_id.sequence_id:
			if not installment.journal_id.sequence_id.active:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please activate the sequence of selected journal !'))
			c = {'date':datetime.strptime(effective_date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			name = seq_obj.next_by_id(cr, uid, installment.journal_id.sequence_id.id, context=c)
		else:
			raise osv.except_osv(_('Error!'),
				_('Please define a sequence on the journal.'))
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': name,
			'journal_id': installment.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
		}

		return move

	def action_pay(self, cr, uid, ids, context=None):
		if not context:
			context={}
		installment=self.browse(cr, uid, ids[0], context)
		loan=self.pool.get('account.bank.loan').browse(cr, uid, installment.loan_id.id, context)
		if loan.state!='open':
			raise osv.except_osv(_('Update Error !'),
				_('You cannot Confirm this Payment/Installment before Its Loan number '+loan.name+' is in Open state. \n \
				Please Validate the Loan first before Confirm this Payment/Installment!'))
		else:
			self.write(cr,uid,ids ,{'state':'payment'})
		return True	

	def action_set_draft(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids ,{'state':'draft'})
		return True

	def action_unreconcile(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		move_lines = []
		for installment in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			installment.refresh()
			amr=[]
			for line in installment.move_ids:
				line.refresh()
				if line.reconcile_id:
					move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
					move_lines.remove(line.id)
					#reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
					amr.append(line.reconcile_id.id)

			reconcile_pool.unlink(cr, uid, amr)
			if len(move_lines) >= 2:
				move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
			if installment.move_id:
				move_pool.button_cancel(cr, uid, [installment.move_id.id])
				move_pool.unlink(cr, uid, [installment.move_id.id])
		res = {
			'state':'cancel',
			'move_id':False,
		}
		self.write(cr, uid, ids, res)
		return True

	def action_post_payment(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_pool = self.pool.get('account.bank.loan')
		for installment in self.browse(cr, uid, ids, context=context):
			if installment.move_id:
				continue
			rec_list_ids=[]
			loan=loan_pool.browse(cr, uid, installment.loan_id.id, context)

			rec_list_ids.append(loan.liability_move_line_id.id)
			date = installment.date_payment!='False' and installment.date_payment or time.strftime('%Y-%m-%d')
			context.update({'date':date})

			company_currency = loan_pool._get_company_currency(cr, uid, loan.id, context)
			current_currency = loan_pool._get_current_currency(cr, uid, loan.id, context)

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, installment.id, context=context), context=context)
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			effective_date = installment.date_payment!='False' and installment.date_payment or time.strftime('%Y-%m-%d')
			period=self.pool.get('account.period').find(cr,uid,dt=effective_date)
			
			installment_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, installment.installment_amount, context=context)
			interest_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, installment.interest_cost, context=context)
			bank_account_id=installment.journal_id.default_credit_account_id and installment.journal_id.default_credit_account_id.id
			if not bank_account_id:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the account of selected Journal !'))

			#amount installment line
			debit = credit = 0.0
			debit = installment_amount
			sign = debit - credit < 0 and -1 or 1

			move_id_liab=move_line_pool.create(cr,uid,{
				'name': loan.name or ''+'/'+installment.name or '/',
				'debit': debit,
				'credit': credit,
				'account_id': loan.account_payable.id or False,
				'move_id': move_id,
				'journal_id': installment.journal_id.id,
				'period_id': period and period[0] or False,
				'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * installment.installment_amount or 0.0,
				'date': effective_date,
			},context)

			rec_list_ids.append(int(move_id_liab))
			#amount interest line
			debit = credit = 0.0
			if interest_amount > 0.0:
				debit = interest_amount
			else:
				credit = -interest_amount
			sign = debit - credit < 0 and -1 or 1
			move_line_pool.create(cr,uid,{
				'name': loan.name or ''+'/'+installment.name or '/',
				'debit': debit,
				'credit': credit,
				'account_id': installment.account_interest.id or False,
				'move_id': move_id,
				'journal_id': installment.journal_id.id,
				'period_id': period and period[0] or False,
				# 'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * installment.interest_cost or 0.0,
				'date': effective_date,
			},context)

			total_cost=0.0
			if installment.adm_cost_ids:
				for cost in installment.adm_cost_ids:
					cost_amount = self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, cost.expense_amount, context=context)
					debit = credit = 0.0
					debit = cost_amount
					if debit < 0.0:
						credit = debit
						debit = 0.0

					sign = debit - credit < 0 and -1 or 1

					move_line_pool.create(cr,uid,{
						'name': loan.name or ''+'/'+installment.name or ''+'/'+cost.name or '',
						'debit': debit,
						'credit': credit,
						'account_id': cost.account_id.id or False,
						'move_id': move_id,
						'journal_id': installment.journal_id.id,
						'period_id': period and period[0] or False,
						# 'partner_id': loan.partner_id.id,
						'currency_id': company_currency <> current_currency and  current_currency or False,
						'amount_currency': company_currency <> current_currency and sign * cost_amount or 0.0,
						'date': effective_date,
					},context)
					total_cost += cost_amount		

			#amount bank
			debit = credit = 0.0
			credit = installment_amount + interest_amount + total_cost
			sign = debit - credit < 0 and -1 or 1
			move_line_pool.create(cr,uid,{
				'name': loan.name or ''+'/'+installment.name or '/',
				'debit': debit,
				'credit': credit,
				'account_id': bank_account_id or False,
				'move_id': move_id,
				'journal_id': installment.journal_id.id,
				'period_id': period and period[0] or False,
				# 'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * (installment.installment_amount+installment.interest_cost) or 0.0,
				'date': effective_date,
			},context)
			
			self.write(cr,uid,installment.id ,{'state':'paid','move_id':move_id})

			loan_pool.write(cr, uid, loan.id, {'residual_amount':installment.remain_amount} )
			
			if loan.account_payable.type == 'receivable' or loan.account_payable.type == 'payable' or loan.account_payable.reconcile:
				reconcile = False
				if len(rec_list_ids) >= 2:
					reconcile = move_line_pool.reconcile_partial(cr, uid, rec_list_ids, writeoff_acc_id=False, writeoff_period_id=(period and period[0] or False), writeoff_journal_id=installment.journal_id.id)

			if loan.move_id:
				move_pool.post(cr, uid, [move_id], context={})
		return True	

	def compute_interest(self, cr, uid, ids, context=None):
		if not context:
			context={}
		installment=self.browse(cr, uid, ids[0], context)
		loan=self.pool.get('account.bank.loan').browse(cr, uid, installment.loan_id.id, context)
		if loan.state not in ['confirm','open']:
		# if loan.state!='open':
			raise osv.except_osv(_('Creation Error !'),
				_('Please confirm the Loan first before creating the new Installment! \
				\n Please Delete your new Payment/Installment data before continue'))
		else:
			if installment.config_type=='manual':
				date_from=datetime.strptime(installment.date_from,"%Y-%m-%d")
				date_to=datetime.strptime(installment.date_to,"%Y-%m-%d")
				selisih=(date_to-date_from).days
				
				if loan.interest_for=='term1':
					n=30/360.00
				elif loan.interest_for=='term2':
					n=float(selisih)/360.00
				irate=installment.interest_perc/100
				
				interest_per_periode=installment.residual_amount*irate*n

				remain_amount=installment.residual_amount-installment.installment_amount

				self.write(cr, uid, installment.id ,{
					'remain_amount':remain_amount,
					'interest_cost':interest_per_periode,
					'state':'open',
				})
				# self.pool.get('account.bank.loan').write(cr, uid, loan.id, {'residual_amount':remain_amount})
		return True

class account_bank_loan_installment_expense(osv.osv):
	_name = "account.bank.loan.installment.expense"

	_columns = {
		"installment_id" : fields.many2one("account.bank.loan.installment","Installment/Repayment", delete="cascade"),
		"name" : fields.char('Description', size=400),
		"account_id" : fields.many2one("account.account","Expense Account"),
		"expense_amount" : fields.float("Amount", digits_compute= dp.get_precision('Account')),
	}

class account_bank_loan_repayment(osv.osv):
	def _get_next_repayment(self, cr, uid, ids, field_name, arg, context=None):
		if not context:context={}
		res = []
		for rep in self.pool.get('account.bank.loan.repayment').browse(cr,uid,ids,context=context):
			if rep.next_id:
				res.append(rep.next_id.id)
		return res

	_name = 'account.bank.loan.repayment'
	_columns = {
		# 'prev_id' : fields.many2one('account.bank.loan.repayment','Prev Repayment'),
		# 'next_id' : fields.many2one('account.bank.loan.repayment','Next Repayment'),
		'loan_id':fields.many2one('account.bank.loan','Bank Loan'),
		'use_scheduler' : fields.related('loan_id','use_scheduler', type='boolean', relation='account.bank.loan', string='Use Scheduler', readonly=True),
		'name' : fields.char('Sequence',size=20),
		'payment_memo' : fields.char('Memo',size=200),
		'liability_move_line_id' : fields.related('loan_id','liability_move_line_id',type='many2one',relation='account.move.line',string='Liability Entry Item'),
		'schedule_payment' : fields.date('Schedule Payment'),
		'payment_date' : fields.date('Payment Date'),
		'planning_amount' : fields.float("Planning Payment Amount", digits_compute= dp.get_precision('Account')),
		'revision_amount' : fields.float("Revision Payment Amount", digits_compute= dp.get_precision('Account')),
		'lastest_revision' : fields.float("Lastest Revision Amount", digits_compute= dp.get_precision('Account'), readonly=True),
		'real_amount' : fields.float(" Repayment Amount", digits_compute= dp.get_precision('Account')),
		'journal_id' : fields.many2one('account.journal','Payment Method'),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'drawdown_repayment_id' : fields.many2one('account.bank.loan.drawdown.repayment','Reference Drawdown Payment'),
		'state' : fields.selection([
			('draft','Draft'),
			('confirmed','Confirmed'),
			('paid','Paid'),('paid2','Drawdown Paid'),
			('cancel','Cancelled')], 'State'),
	}

	_defaults = {
		# 'residual_amount' : lambda self, cr, uid, context: context.get('residual_amount',0.0),
		# 'config_type' : lambda self, cr, uid, context: context.get('config_type','manual'),
		'state':lambda *a:'draft',
	}

	_order = 'schedule_payment asc'

	def action_confirm(self, cr, uid, ids, context=None):
		if not context:
			context={}
		repayment=self.browse(cr, uid, ids[0], context)
		loan=self.pool.get('account.bank.loan').browse(cr, uid, repayment.loan_id.id, context)
		if loan.state!='open':
			raise osv.except_osv(_('Update Error !'),
				_('You cannot Confirm this Payment/Installment before Its Loan number '+loan.name+' is in Open state. \n \
				Please Validate the Loan first before Confirm this Payment/Installment!'))
		else:
			update_val = {
				'journal_id' : loan.journal_id.id or False,
				'real_amount' : repayment.planning_amount or 0.0,
				'state':'confirmed',
				'payment_date' : repayment.schedule_payment,
			}
			self.write(cr,uid,ids ,update_val)
		return True

	def action_set_to_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		for repayment in self.browse(cr, uid, ids, context=context):
			self.write(cr,uid,repayment.id ,{'state':'draft'})
		return True

	def account_move_get(self, cr, uid, repayment_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		repayment = self.browse(cr,uid,repayment_id,context)
		
		effective_date = context.get('date',time.strftime('%Y-%m-%d'))
		if repayment.journal_id.sequence_id:
			if not repayment.journal_id.sequence_id.active:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please activate the sequence of selected journal !'))
			c = {'date':datetime.strptime(effective_date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			name = seq_obj.next_by_id(cr, uid, repayment.journal_id.sequence_id.id, context=c)
		else:
			raise osv.except_osv(_('Error!'),
				_('Please define a sequence on the journal.'))
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': name,
			'journal_id': repayment.journal_id.id,
			'date': effective_date,
			'ref':repayment.loan_id and repayment.loan_id.ref or repayment.loan_id.name or '',
			'period_id': period and period[0] or False,
		}

		return move

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_pool = self.pool.get('account.bank.loan')
		wf_service = netsvc.LocalService("workflow")
		for repayment in self.browse(cr, uid, ids, context=context):
			if repayment.move_id:
				continue
			rec_list_ids=[]
			loan=loan_pool.browse(cr, uid, repayment.loan_id.id, context)

			rec_list_ids.append(loan.liability_move_line_id.id)
			date = repayment.payment_date!='False' and repayment.payment_date or (repayment.schedule_payment!='False' and repayment.schedule_payment) or time.strftime('%Y-%m-%d')
			context.update({'date':date})

			company_currency = loan_pool._get_company_currency(cr, uid, loan.id, context)
			current_currency = loan_pool._get_current_currency(cr, uid, loan.id, context)

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, repayment.id, context=context), context=context)
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			period=self.pool.get('account.period').find(cr,uid,dt=date)
			
			repayment_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, repayment.real_amount, context=context)
			bank_account_id=repayment.journal_id.default_credit_account_id and repayment.journal_id.default_credit_account_id.id or False
			if not bank_account_id:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the account of selected Journal !'))

			#amount installment line
			debit = credit = 0.0
			debit = repayment_amount
			sign = debit - credit < 0 and -1 or 1
			# 'name': repayment.payment_memo or ((loan.name or '')+'/'+repayment.name or '/'),
			move_id_liab=move_line_pool.create(cr,uid,{
				'name': repayment.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': loan.account_payable.id or False,
				'move_id': move_id,
				'journal_id': repayment.journal_id.id,
				'period_id': period and period[0] or False,
				'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * repayment.real_amount or 0.0,
				'date': date,
			},context)

			rec_list_ids.append(int(move_id_liab))

			#amount bank
			debit = credit = 0.0
			credit = repayment_amount #+ interest_amount + total_cost
			sign = debit - credit < 0 and -1 or 1
			move_line_pool.create(cr,uid,{
				'name': repayment.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': bank_account_id or False,
				'move_id': move_id,
				'journal_id': repayment.journal_id.id,
				'period_id': period and period[0] or False,
				# 'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * (repayment.real_amount) or 0.0,
				'date': date,
			},context)
			
			self.write(cr,uid,repayment.id ,{'state':'paid','move_id':move_id})
			
			if loan.account_payable.type == 'receivable' or loan.account_payable.reconcile:
				reconcile = False
				if len(rec_list_ids) >= 2:
					reconcile = move_line_pool.reconcile_partial(cr, uid, rec_list_ids, writeoff_acc_id=False, writeoff_period_id=(period and period[0] or False), writeoff_journal_id=repayment.journal_id.id)

			if repayment.move_id:
				move_pool.post(cr, uid, [move_id], context={})
			wf_service.trg_validate(uid, 'account.bank.loan', loan.id, 'test_paid', cr)
		return True	

	def action_unreconcile(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		move_lines = []
		for repayment in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			repayment.refresh()
			imr=[]
			for line in repayment.move_ids:
				if line.reconcile_id:
					move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
					move_lines.remove(line.id)
					#reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
					imr.append(line.reconcile_id.id)

			reconcile_pool.unlink(cr, uid, imr)
			if len(move_lines) >= 2:
				move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
			if repayment.move_id:
				move_pool.button_cancel(cr, uid, [repayment.move_id.id])
				move_pool.unlink(cr, uid, [repayment.move_id.id])
		res = {
			'state':'cancel',
			'move_id':False,
		}
		self.write(cr, uid, ids, res)
		return True

class account_bank_loan_interest_rate(osv.osv):
	_name = "account.bank.loan.interest.rate"

	_columns = {
		"loan_id" : fields.many2one("account.bank.loan","Interest Rate", delete="cascade"),
		"loan_type_id" : fields.many2one('account.bank.loan.type','Loan Classification', delete="cascade"),
		"rate" : fields.float("Rate", digits=(2,4)),
		"date_from" : fields.date("Valid From"),
		"date_to" : fields.date("Valid To"),
	}

class account_bank_loan_interest(osv.osv):
	def _get_amount_total(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for interest in self.browse(cr, uid, ids, context=context):
			paid_amount=0.0
			for line in interest.writeoff_lines:
				paid_amount += line.amount
			res[interest.id] = interest.interest_amount + paid_amount
		
		return res

	_name = "account.bank.loan.interest"

	_columns = {
		"loan_id" : fields.many2one("account.bank.loan","Bank Loan", delete="cascade"),
		"drawdown_interest_id" : fields.many2one('account.bank.loan.drawdown.interest','Reference Drawdown Interest'),
		"drawdown_interest_prov_id" : fields.many2one('account.bank.loan.drawdown.interest','Reference Drawdown Interest'),
		'payment_memo' : fields.char('Memo',size=200),
		"compute_type" : fields.selection([
			('multi','Using Multi Interest Rate'),
			('single','Using Single Interest Rate')], 'Computation Method'),
		"use_loan_type_rate" : fields.boolean('Use rate from master in Loan Classification?'),
		"rate" : fields.float("Rate", digits=(2,4)),
		"date_from" : fields.date("Interest From"),
		"date_to" : fields.date("Interest To"),
		'interest_amount' : fields.float("Interest Amount", digits=(2,4)),
		'account_interest': fields.many2one('account.account', 'Account Interest',required=False,readonly=True,states={'computed':[('readonly',False)]}),
		'interest_line' : fields.one2many("account.bank.loan.interest.line","interest_id","Interest Amount", digits_compute= dp.get_precision('Account')),
		'journal_id' : fields.many2one('account.journal','Payment Method'),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_provision_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'move_prov_ids': fields.related('move_provision_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'liability_move_prov_id': fields.many2one('account.move.line', 'Liability Provision Move', readonly=True),
		'payment_date' : fields.date('Payment Date'),
		'payment_prov_date' : fields.date('Payment Date'),
		"writeoff_lines" : fields.one2many("account.voucher.writeoff",'interest_id',"Other Charge"),
		"total_paid_amount" : fields.function(_get_amount_total, type='float', string='Paid Amount', digits=(2,4)),
		'is_provision' : fields.boolean('Provision',readonly=True,states={'computed':[('readonly',False)]}),
		'payment_prov_journal_id' : fields.many2one('account.journal','Payment Method'),
		'prov_account_id' : fields.many2one('account.account', 'Provision Account',readonly=True,states={'computed':[('readonly',False)]}),
		'type_of_charge': fields.many2one('charge.type', 'Type'),
		'state' : fields.selection([
			('draft','Draft'),
			('computed','Computed'),
			('provision','Provisioned'),
			('paid','Paid'),('paid2','Drawdown Paid'),
			('cancel','Cancelled')], 'State'),
	}

	_defaults = {
		'state' : lambda *a : 'draft',
		'compute_type' : 'multi',
	}

	_order = "loan_id asc, id asc"

	def compute_interest(self, cr, uid, ids, context=None):
		if not context:
			context={}
		interest=self.browse(cr, uid, ids[0], context)
		repayment_obj = self.pool.get('account.bank.loan.repayment')
		interest_rate_obj = self.pool.get('account.bank.loan.interest.rate')
		# rate from master interest
		acc_interest_obj = self.pool.get('account.interest')
		acc_interest_rate_obj = self.pool.get('account.interest.rate')

		loan=self.pool.get('account.bank.loan').browse(cr, uid, interest.loan_id.id, context)
		if loan.state not in ['open','paid']:
			raise osv.except_osv(_('Update Error !'),
				_('You cannot Confirm this Payment/Installment before Its Loan number '+loan.name+' is in Open state. \n \
				Please Validate the Loan first before Confirm this Payment/Installment!'))
		else:
			# calculate last outstanding
			date_from = interest.date_from
			date_to = interest.date_to
			total_paid = 0.0
			prev_repay_ids = []
			for repayment in sorted(loan.repayment_line, key=lambda x:x.payment_date):
				if repayment.payment_date <= date_from: 
					prev_repay_ids.append(repayment.id)
					total_paid += repayment.state in ('paid','paid2') and repayment.real_amount or 0.0
			last_outstanding = loan.total_amount - total_paid
			
			# date_from on model account.bank.loan.interest.rate is last rate updated
			rate_ids = []
			if interest.compute_type == 'multi':
				if interest.use_loan_type_rate:
					first_rate_ids = interest_rate_obj.search(cr, uid, [('loan_type_id','=',loan.loan_type_id.id),('date_from','<=',date_from)])
				else:
					first_rate_ids = interest_rate_obj.search(cr, uid, [('loan_id','=',loan.id),('date_from','<=',date_from)])

				if not first_rate_ids:
					raise osv.except_osv(_('Configuration Error !'),
					_('You cannot Compute while there are no available rate inputed on Interest Rate Master. \n \
					Please Input Interest Rate on the master Interest or change the Interest Payment type into Single Interest Rate only!'))
				
				# this is only take the first valid rate to use for computing the interest
				# in order to save the start date that will be use inside the start date of the first interest amount 
				first_rate = interest_rate_obj.browse(cr, uid, first_rate_ids, context=context)[len(first_rate_ids)-1]
				first_rate_date = first_rate.date_from
				if first_rate_date < date_from:
					first_rate_date = date_from
				into_rate_date = date_to
				first_rate_rate = first_rate.rate
				
				if interest.use_loan_type_rate:
					rate_ids = interest_rate_obj.search(cr, uid, [('loan_type_id','=',loan.loan_type_id.id),('date_from','>',date_from),('date_from','<=',date_to)])
					# rate_ids = interest_rate_obj.search(cr, uid, [('loan_type_id','=',loan.loan_type_id.id),('date_from','>=',date_from),('date_from','<=',date_to)])
				else:
					rate_ids = interest_rate_obj.search(cr, uid, [('loan_id','=',loan.id),('date_from','>',date_from),('date_from','<=',date_to)])
					# rate_ids = interest_rate_obj.search(cr, uid, [('loan_id','=',loan.id),('date_from','>=',date_from),('date_from','<=',date_to)])
			else:
				first_rate_date = date_from
				into_rate_date = date_to
				first_rate_rate = interest.rate
			interest_line = []
			total_interest_amount = 0.0
			# reset interest line
			for int_line in interest.interest_line:
				interest_line.append((2,int_line.id))
			print "::::::::::::::::::::::::::::start", first_rate_date, into_rate_date, first_rate_rate
			if rate_ids:
				for rate in interest_rate_obj.browse(cr, uid, rate_ids, context=context):
					into_rate_date = (datetime.strptime(rate.date_from,'%Y-%m-%d') + relativedelta(days=-1)).strftime('%Y-%m-%d')
					print "::::::::::::::::::::::::::::loop rate", first_rate_date, into_rate_date, first_rate_rate
					# into_rate_date = rate.date_from
					# repayment_ids = repayment_obj.search(cr, uid, [('loan_id','=',loan.id),('payment_date','>=',first_rate_date),('payment_date','<=',into_rate_date),('state','in',['confirmed','paid','paid2'])])
					repayment_ids = repayment_obj.search(cr, uid, [('loan_id','=',loan.id),('payment_date','>=',first_rate_date),('payment_date','<=',into_rate_date),('state','in',['confirmed','paid','paid2']),('id','not in',prev_repay_ids)])
					if repayment_ids:
						for repayment in repayment_obj.browse(cr, uid, repayment_ids, context=context):
							# selisih = (datetime.strptime(repayment.payment_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days
							selisih = (datetime.strptime(repayment.payment_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days + 1
							last_outstanding -= repayment.real_amount
							print "::::::::::::::::::::::::::::loop rep", repayment.payment_date, first_rate_date, selisih, first_rate_rate, last_outstanding
							if selisih > 0:
								interest_amount = last_outstanding * selisih/360 * first_rate_rate/100
								# interest_amount = last_outstanding * selisih/360 * rate.rate/100

								interest_line.append((0,0,{
										"interest_id" : interest.id,
										"rate" : first_rate_rate,
										# "rate" : rate.rate,
										"date_from" : first_rate_date,
										# "date_to" : (datetime.strptime(repayment.payment_date,'%Y-%m-%d') + relativedelta(days=-1)).strftime('%Y-%m-%d'),
										"date_to" : repayment.payment_date,
										"n_days" : selisih,
										"outstanding" : last_outstanding,
										"amount" : interest_amount,
									}))
								total_interest_amount+=interest_amount

								# first_rate_date = repayment.payment_date
								first_rate_date = (datetime.strptime(repayment.payment_date,'%Y-%m-%d') + relativedelta(days=+1)).strftime('%Y-%m-%d')
								# last_outstanding -= repayment.real_amount
								prev_repay_ids.append(repayment.id)
					selisih = (datetime.strptime(into_rate_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days	+ 1
					print "::::::::::::::::::::::::::::loop rate", first_rate_date, into_rate_date,selisih, first_rate_rate, last_outstanding
					# selisih = (datetime.strptime(into_rate_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days
					if selisih > 0:
						interest_amount = last_outstanding * selisih/360 * first_rate_rate/100
						# interest_amount = last_outstanding * selisih/360 * rate.rate/100
						interest_line.append((0,0,{
								"interest_id" : interest.id,
								"rate" : first_rate_rate,
								# "rate" : rate.rate,
								"date_from" : first_rate_date,
								"date_to" : into_rate_date,
								"n_days" : selisih,
								"outstanding" : last_outstanding,
								"amount" : interest_amount,
							}))
						total_interest_amount+=interest_amount
					first_rate_date = rate.date_from
						# first_rate_date = (datetime.strptime(into_rate_date,'%Y-%m-%d') + relativedelta(days=+1)).strftime('%Y-%m-%d')
					first_rate_rate = rate.rate

				# if the rate masters already done computing the interest, then we need to compute for the 
				# remaining date that need to be put for total interest amount
				into_rate_date = date_to
				# repayment_ids = repayment_obj.search(cr, uid, [('loan_id','=',loan.id),('payment_date','>=',first_rate_date),('payment_date','<=',into_rate_date),('state','in',['confirmed','paid','paid2'])])
				repayment_ids = repayment_obj.search(cr, uid, [('loan_id','=',loan.id),('payment_date','>=',first_rate_date),('payment_date','<=',into_rate_date),('state','in',['confirmed','paid','paid2']),('id','not in',prev_repay_ids)])
				print "::::::::::::::::::::::::::::finishing", first_rate_date, into_rate_date, first_rate_rate
				if repayment_ids:
					for repayment in repayment_obj.browse(cr, uid, repayment_ids, context=context):
						selisih = (datetime.strptime(repayment.payment_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days
						# selisih = (datetime.strptime(repayment.payment_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days + 1
						print "::::::::::::::::::::::::::::finishing loop rep", repayment.payment_date, first_rate_date, selisih, first_rate_rate, last_outstanding
						if selisih > 0:
							interest_amount = last_outstanding * selisih/360 * first_rate_rate/100

							interest_line.append((0,0,{
									"interest_id" : interest.id,
									"rate" : first_rate_rate,
									"date_from" : first_rate_date,
									"date_to" : (datetime.strptime(repayment.payment_date,'%Y-%m-%d') + relativedelta(days=-1)).strftime('%Y-%m-%d'),
									# "date_to" : repayment.payment_date,
									"n_days" : selisih,
									"outstanding" : last_outstanding,
									"amount" : interest_amount,
								}))
							total_interest_amount+=interest_amount

							first_rate_date = repayment.payment_date
							# first_rate_date = (datetime.strptime(repayment.payment_date,'%Y-%m-%d') + relativedelta(days=+1)).strftime('%Y-%m-%d')
						last_outstanding -= repayment.real_amount
						# last_outstanding -= repayment.real_amount
				selisih = (datetime.strptime(into_rate_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days	+ 1
				print "::::::::::::::::::::::::::::end", first_rate_date, into_rate_date, selisih, first_rate_rate, last_outstanding
				if selisih > 0:
					interest_amount = last_outstanding * selisih/360 * first_rate_rate/100
					interest_line.append((0,0,{
							"interest_id" : interest.id,
							"rate" : first_rate_rate,
							"date_from" : first_rate_date,
							"date_to" : into_rate_date,
							"n_days" : selisih,
							"outstanding" : last_outstanding,
							"amount" : interest_amount,
						}))
					total_interest_amount+=interest_amount
			else:
				repayment_ids = repayment_obj.search(cr, uid, [('loan_id','=',loan.id),('payment_date','>',first_rate_date),('payment_date','<=',into_rate_date),('state','in',['confirmed','paid','paid2'])])
				if repayment_ids:
					# outstanding amount will be used as the base amount to calculate the interest
					# we need to compute the current outstanding and the payment that happened between the date period of interest payment 
					for repayment in repayment_obj.browse(cr, uid, repayment_ids, context=context):
						selisih = (datetime.strptime(repayment.payment_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days
						if selisih > 0:
							interest_amount = last_outstanding * selisih/360 * first_rate_rate/100

							interest_line.append((0,0,{
								"interest_id" : interest.id,
								"rate" : first_rate_rate,
								"date_from" : first_rate_date,
								"date_to" : (datetime.strptime(repayment.payment_date,'%Y-%m-%d') + relativedelta(days=-1)).strftime('%Y-%m-%d'),
								"n_days" : selisih,
								"outstanding" : last_outstanding,
								"amount" : interest_amount,
							}))
							total_interest_amount += interest_amount
							first_rate_date = repayment.payment_date
							last_outstanding -= repayment.real_amount
				
				# to calculate either if there isnt any repayment yet or there is remaining outstanding 
				selisih = (datetime.strptime(into_rate_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days + 1
				# selisih = (datetime.strptime(into_rate_date,'%Y-%m-%d')-datetime.strptime(first_rate_date,'%Y-%m-%d')).days
				if selisih > 0:
					interest_amount = last_outstanding * selisih/360 * first_rate_rate/100
					interest_line.append((0,0,{
						"interest_id" : interest.id,
						"rate" : first_rate_rate,
						"date_from" : first_rate_date,
						"date_to" : into_rate_date,
						"n_days" : selisih,
						"outstanding" : last_outstanding,
						"amount" : interest_amount,
					}))
					total_interest_amount+=interest_amount

			update_val = {
				'journal_id' : loan.journal_id.id or False,
				'interest_line' : interest_line,
				'interest_amount' : total_interest_amount,
				'state':'computed'
			}
			self.write(cr,uid,ids ,update_val)
		return True

	def action_set_to_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		for interest in self.browse(cr, uid, ids, context=context):
			self.write(cr,uid,interest.id ,{'state':'draft'})
		return True

	def account_move_get(self, cr, uid, interest_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		interest = self.browse(cr,uid,interest_id,context)
		
		effective_date = context.get('date',time.strftime('%Y-%m-%d'))
		if interest.journal_id.sequence_id:
			if not interest.journal_id.sequence_id.active:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please activate the sequence of selected journal !'))
			c = {'date':datetime.strptime(effective_date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			name = seq_obj.next_by_id(cr, uid, interest.journal_id.sequence_id.id, context=c)
		else:
			raise osv.except_osv(_('Error!'),
				_('Please define a sequence on the journal.'))
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': name,
			'ref':interest.loan_id.ref or interest.loan_id.name or '',
			'journal_id': context.get('payment_prov_journal_id',False) and interest.payment_prov_journal_id.id or interest.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
		}

		return move

	def other_charge_move_line(self, cr, uid, interest_id, line_total, move_id, name, company_currency, current_currency, context=None):
		'''
		Set a dict to be use to create the writeoff move line.

		:param interest_id: Id of interest what we are creating account_move.
		:param line_total: Amount remaining to be allocated on lines.
		:param move_id: Id of account move where this line will be added.
		:param name: Description of account move line.
		:param company_currency: id of currency of the company to which the interest belong
		:param current_currency: id of currency of the interest
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		currency_obj = self.pool.get('res.currency')
		
		interest = self.browse(cr, uid, interest_id)
		current_currency_obj = interest.loan_id.journal_id.currency or interest.loan_id.journal_id.company_id.currency_id
		
		if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
			wfline={}
			analytic_line = {}
			movex_line = {}
			sign = -1
			for line in interest.writeoff_lines:
				amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context={'date':interest.payment_date})
				mvl = {
				'name': line.name or name,
				'account_id': line.account_id and line.account_id.id or False,
				'move_id': move_id,
				'partner_id': False,
				'date': interest.payment_date,
				'debit': amount > 0 and amount or 0.0,
				'credit': amount < 0 and amount or 0.0,
				'amount_currency': company_currency <> current_currency and (sign * -1 * line.amount) or 0.0,
				'currency_id': company_currency <> current_currency and current_currency or False,
				#'analytic_account_id': line.analytic_id and line.analytic_id.id or False,
				}


				if line.account_id.id in wfline:
					amount_exist = wfline[line.account_id.id]['debit']>0.0 and wfline[line.account_id.id]['debit'] or -1*wfline[line.account_id.id]['credit']
					currency_exist = wfline[line.account_id.id]['amount_currency']
					amount +=amount_exist
					line_curr =company_currency <> current_currency and (line.amount) or 0.0

					amount_currency = line_curr - currency_exist
					mvl.update({
						'debit':amount>0 and amount or 0.0,
						'credit':amount<0 and amount or 0.0,
						'amount_currency' : company_currency <> current_currency and (sign * -1 * amount_currency) or 0.0
						})
				# print "::::::::::::::::::::::move other > ", mvl['debit'], mvl['credit'], mvl['amount_currency']
				wfline.update({line.account_id.id:mvl})
			for wx in wfline.keys():
				move_line_id = self.pool.get('account.move.line').create(cr,uid,wfline[wx],context)
				movex_line.update({wfline[wx]['account_id']:move_line_id})
			for obj_line in interest.writeoff_lines:
				amt = currency_obj.compute(cr, uid, current_currency, company_currency, obj_line.amount,context={'date':interest.payment_date}) 
				if obj_line.analytic_id and obj_line.analytic_id.id:
					anline={
							"invoice_related_id" : obj_line.invoice_related_id,
							"name"			: obj_line.name,
							"date"			: interest.payment_date,
							"account_id"	: obj_line.analytic_id.id,
							"amount"		: amt,
							"general_acccount":obj_line.account_id.id,
							"move_id"		: movex_line[obj_line.account_id.id],
							"journal_id"	: obj_line.analytic_journal_id.id or obj_line.journal_id.analytic_journal_id.id,
							"ref"			: obj_line.name,
						   }
					xid=self.pool.get('account.move.line.distribution').create(cr,uid,anline,context)
			return True

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_pool = self.pool.get('account.bank.loan')
		for interest in self.browse(cr, uid, ids, context=context):
			if interest.move_id:
				continue
			if interest.is_provision and interest.move_provision_id:
				continue
			loan=loan_pool.browse(cr, uid, interest.loan_id.id, context)

			date = interest.payment_date!='False' and interest.payment_date or time.strftime('%Y-%m-%d')
			date = interest.payment_prov_date!='False' and interest.is_provision and interest.payment_prov_date or date
			context.update({'date':date})

			company_currency = loan_pool._get_company_currency(cr, uid, loan.id, context)
			current_currency = loan_pool._get_current_currency(cr, uid, loan.id, context)

			if interest.is_provision:
				context.update({'payment_prov_journal_id':True})
			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, interest.id, context=context), context=context)
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			period=self.pool.get('account.period').find(cr,uid,dt=date)
			
			interest_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, interest.interest_amount, context=context)
			bank_account_id=interest.journal_id.default_credit_account_id and interest.journal_id.default_credit_account_id.id or False
			if not bank_account_id and not interest.is_provision:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the account of selected Journal !'))

			#amount installment line
			debit = credit = 0.0
			debit = interest_amount
			sign = debit - credit < 0 and -1 or 1

			move_line_pool.create(cr,uid,{
				'name': interest.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': interest.account_interest and interest.account_interest.id or False,
				'move_id': move_id,
				'journal_id': interest.is_provision and interest.payment_prov_journal_id.id or interest.journal_id.id,
				'period_id': period and period[0] or False,
				'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * interest.interest_amount or 0.0,
				'date': date,
			},context)
			# other charge amounnt
			line_total = interest.total_paid_amount - interest_amount
			if interest.writeoff_lines:
				self.other_charge_move_line(cr, uid, interest.id, line_total, move_id, name, company_currency, current_currency)

			#amount bank
			debit = credit = 0.0
			credit =  interest.total_paid_amount #+  + total_cost
			sign = debit - credit < 0 and -1 or 1
			move_id_liab=move_line_pool.create(cr,uid,{
				'name': interest.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': interest.is_provision and interest.prov_account_id.id or bank_account_id or False,
				'move_id': move_id,
				'journal_id': interest.is_provision and interest.payment_prov_journal_id.id or interest.journal_id.id,
				'period_id': period and period[0] or False,
				# 'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * (interest.real_amount) or 0.0,
				'date': date,
			},context)
			
			to_update = {}
			if interest.is_provision:
				to_update.update({'move_provision_id':move_id,
					'liability_move_prov_id':move_id_liab,
					'state':'provision',
					})
			else:
				to_update.update({'move_id':move_id,
					'state':'paid',
					})


			self.write(cr,uid,interest.id, to_update)

			# loan_pool.write(cr, uid, loan.id, {'residual_amount':installment.remain_amount} )
			

			if loan.move_id and loan.move_id.journal_id.entry_posted:
				move_pool.post(cr, uid, [move_id], context={})
		return True

	def action_provision_settlement(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_pool = self.pool.get('account.bank.loan')
		for interest in self.browse(cr, uid, ids, context=context):
			if interest.move_id:
				continue
			loan=loan_pool.browse(cr, uid, interest.loan_id.id, context)

			date = interest.payment_date!='False' and interest.payment_date or time.strftime('%Y-%m-%d')
			context.update({'date':date})

			company_currency = loan_pool._get_company_currency(cr, uid, loan.id, context)
			current_currency = loan_pool._get_current_currency(cr, uid, loan.id, context)

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, interest.id, context=context), context=context)
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			period=self.pool.get('account.period').find(cr,uid,dt=date)
			
			interest_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, interest.interest_amount, context=context)
			bank_account_id=interest.journal_id.default_credit_account_id and interest.journal_id.default_credit_account_id.id or False
			if not bank_account_id:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the account of selected Journal !'))

			#amount installment line
			debit = credit = 0.0
			debit = interest_amount
			sign = debit - credit < 0 and -1 or 1

			move_id_liab=move_line_pool.create(cr,uid,{
				'name': interest.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': interest.prov_account_id and interest.prov_account_id.id or False,
				'move_id': move_id,
				'journal_id': interest.journal_id.id,
				'period_id': period and period[0] or False,
				'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * interest.interest_amount or 0.0,
				'date': date,
			},context)

			if interest.liability_move_prov_id:
				balance_prov = interest.liability_move_prov_id.debit - interest.liability_move_prov_id.credit
				diff = (debit-credit) + balance_prov
				if diff!=0.0:
					exchange_gain_loss=move_line_pool.create(cr,uid,{
							'name': 'Difference %s'%(interest.payment_memo or loan.name or ''),
							'debit': diff>0.0 and 0.0 or diff,
							'credit': diff<0.0 and 0.0 or abs(diff),
							'account_id': interest.prov_account_id and interest.prov_account_id.id or False,
							'move_id': move_id,
							'journal_id': interest.journal_id.id,
							'period_id': period and period[0] or False,
							'partner_id': loan.partner_id.id,
							'currency_id': company_currency <> current_currency and  current_currency or False,
							'amount_currency': 0.0,
							'date': date,
						},context)

					exchange_gain_loss_counterpart=move_line_pool.create(cr,uid,{
							'name': 'Difference %s'%(interest.payment_memo or loan.name or ''),
							'debit': diff<0.0 and 0.0 or abs(diff),
							'credit': diff>0.0 and 0.0 or diff,
							'account_id': interest.prov_account_id and interest.prov_account_id.id or False,
							'move_id': move_id,
							'journal_id': interest.journal_id.id,
							'period_id': period and period[0] or False,
							'partner_id': loan.partner_id.id,
							'currency_id': company_currency <> current_currency and  current_currency or False,
							'amount_currency': 0.0,
							'date': date,
						},context)


			# other charge amounnt
			line_total = interest.total_paid_amount - interest_amount
			if interest.writeoff_lines:
				self.other_charge_move_line(cr, uid, interest.id, line_total, move_id, name, company_currency, current_currency)

			#amount bank
			debit = credit = 0.0
			credit =  interest.total_paid_amount #+  + total_cost
			sign = debit - credit < 0 and -1 or 1
			move_line_pool.create(cr,uid,{
				'name': interest.payment_memo or loan.name or '',
				'debit': debit,
				'credit': credit,
				'account_id': bank_account_id or False,
				'move_id': move_id,
				'journal_id': interest.journal_id.id,
				'period_id': period and period[0] or False,
				# 'partner_id': loan.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and sign * (interest.real_amount) or 0.0,
				'date': date,
			},context)
			
			self.write(cr,uid,interest.id ,{'state':'paid','move_id':move_id})

			if loan.move_id and loan.move_id.journal_id.entry_posted:
				move_pool.post(cr, uid, [move_id], context={})
		return True

	def action_unreconcile_provision(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for interest in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			interest.refresh()
			
			if interest.move_provision_id:
				move_pool.button_cancel(cr, uid, [interest.move_provision_id.id])
				move_pool.unlink(cr, uid, [interest.move_provision_id.id])
			res = {
				'state':'cancel',
				'move_provision_id':False,
				'move_id':False,
			}
			self.write(cr, uid, interest.id, res)
		return True

	def action_unreconcile(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for interest in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			interest.refresh()
			
			if interest.move_id:
				move_pool.button_cancel(cr, uid, [interest.move_id.id])
				move_pool.unlink(cr, uid, [interest.move_id.id])
			res = {
				'state':interest.is_provision and 'provision' or 'cancel',
				'move_id':False,
			}
			self.write(cr, uid, interest.id, res)
		return True

class account_bank_loan_interest_line(osv.osv):
	_name = "account.bank.loan.interest.line"

	_columns = {
		"interest_id" : fields.many2one("account.bank.loan.interest","Interest Rate", delete="cascade"),
		"rate" : fields.float("Rate", digits=(2,4)),
		"date_from" : fields.date("Valid From"),
		"date_to" : fields.date("Valid To"),
		"n_days" : fields.integer('n Days'),
		"outstanding" : fields.float('Outstanding Amount'),
		"amount" : fields.float('Amount', digits=(2,4)),
	}
