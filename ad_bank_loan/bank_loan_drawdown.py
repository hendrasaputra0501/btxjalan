from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

############################ REPAYMENT LOAN ###############################
class account_bank_loan_drawdown_repayment(osv.Model):
	_name = "account.bank.loan.drawdown.repayment"
	_columns = {
		'name' : fields.char('Number',size=128, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'memo' : fields.char('Memo',size=128, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'ref' : fields.char('Payment Ref',size=128, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'entry_date' : fields.date('Entry Date', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'date' : fields.date('Payment Date', required=True, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'amount' : fields.float("Repayment Amount", digits_compute= dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		
		'journal_id' : fields.many2one('account.journal','Payment Method',required=True, readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'state' : fields.selection([
			('draft','Draft'),
			('confirmed','Confirmed'),
			('posted','Posted'),
			('cancel','Cancelled')], 'State'),
		'line_ids' : fields.one2many('account.bank.loan.drawdown.repayment.line','repayment_id','Repayment Lines', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'company_id' : fields.many2one('res.company', 'Company'),
	}

	_defaults = {
		'state' : lambda *s:'draft',
		'entry_date' : lambda *e:time.strftime('%Y-%m-%d'),
		'company_id' : lambda self, cr, uid, ids, context=None: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
	}

	def onchange_journal_id(self, cr, uid, ids, journal_id, date, line_ids, context=None):
		if context is None:
			context = {}
		res = {}
		journal_pool = self.pool.get('account.journal')
		currency_obj = self.pool.get('res.currency')
		drawdown_line_pool = self.pool.get('account.bank.loan.drawdown.repayment.line')
		loan_pool = self.pool.get('account.bank.loan')
		if not journal_id:
			return {'value':res}
		
		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		if not journal.default_credit_account_id or not journal.default_debit_account_id:
			raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal "%s".') % (journal.name))
		if line_ids:
			res.update({'line_ids':[]})
			company_currency = journal.company_id.currency_id.id
			curr_currency_id = journal.currency and journal.currency.id or company_currency
			
			ctx = context.copy()
			ctx.update({'date':date!=False and date or time.strftime('%Y-%m-%d')})

			line_ids = [x[1] for x in line_ids]
			loan_ids = [x.loan_id.id for x in drawdown_line_pool.browse(cr, uid, line_ids, context=context) if x.loan_id]
			for line_id in line_ids:
				drawdown_line_pool.unlink(cr, uid, line_id)

			for line in loan_pool.browse(cr, uid, loan_ids, context=context):
				if line.liability_move_line_id.currency_id and curr_currency_id == line.liability_move_line_id.currency_id.id:
					amount_original = abs(line.liability_move_line_id.amount_currency)
					amount_unreconciled = abs(line.liability_move_line_id.amount_residual_currency)
				else:
					amount_original = currency_obj.compute(cr, uid, company_currency, curr_currency_id, line.liability_move_line_id.credit or line.liability_move_line_id.debit or 0.0, context=ctx)
					amount_unreconciled = currency_obj.compute(cr, uid, company_currency, curr_currency_id, abs(line.liability_move_line_id.amount_residual), context=ctx)

				res['line_ids'].append({
					'loan_id': line.id or False,
					'liability_move_line_id': line.liability_move_line_id and line.liability_move_line_id.id or False,
					'amount_original': amount_original,
					'amount_unreconciled': amount_unreconciled,
					'date': line.liability_move_line_id.date,
					})
		
		return {'value':res}

	def account_move_get(self, cr, uid, repayment_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		repayment = self.browse(cr,uid,repayment_id,context)
		name = repayment.name or ''

		effective_date = context.get('date',(repayment.date!='False' and repayment.date or time.strftime('%Y-%m-%d')))
		if not name:
			if repayment.journal_id.sequence_id:
				if not repayment.journal_id.sequence_id.active:
					raise osv.except_osv(_('Configuration Error !'),
						_('Please activate the sequence of selected journal !'))
				c = {'date':datetime.strptime(effective_date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
				name = seq_obj.next_by_id(cr, uid, repayment.journal_id.sequence_id.id, context=c)
			else:
				raise osv.except_osv(_('Error!'),
					_('Please define a sequence on the journal.'))
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': name,
			'ref':repayment.ref or '',
			'journal_id': repayment.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
			'comment' : repayment.memo,
		}

		return move

	def first_move_line_get(self, cr, uid, repayment_id, move_id, company_currency, current_currency, context=None):
		'''
		Return a dict to be use to create the first account move line of given voucher.

		:param repayment_id: Id of repayment what we are creating account_move.
		:param move_id: Id of account move where this line will be added.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		repayment = self.browse(cr,uid,repayment_id,context)
		debit = credit = 0.0
		# TODO: is there any other alternative then the voucher type ??
		# ANSWER: We can have payment and receipt "In Advance".
		# TODO: Make this logic available.
		# -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
		amount = self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, repayment.amount, context=context)
		credit = amount
		debit = 0.0
		
		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1

		move = self.pool.get('account.move').browse(cr, uid, move_id)
		account_id = False
		if repayment.journal_id:
			if repayment.journal_id.default_credit_account_id:
				account_id = repayment.journal_id.default_credit_account_id.id
			else:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the default credit account of selected Journal !'))
		#set the first line of the voucher
		move_line = {
				'name': repayment.memo and repayment.memo or (repayment.name or '/'),
				'debit': debit,
				'credit': credit,
				'account_id': account_id,
				'move_id': move_id,
				'journal_id': repayment.journal_id.id,
				'period_id': move.period_id.id,
				# 'partner_id': voucher.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': company_currency <> current_currency and (sign * abs(repayment.amount) or 0.0),
				'date': repayment.date,
				'ref': repayment.ref or repayment.name or '/'
			}
		# print "############################# first_move_line_get",  move_line
		return move_line

	def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
		'''
		Prepare the two lines in company currency due to currency rate difference.

		:param line: browse record of the voucher.line for which we want to create currency rate difference accounting
			entries
		:param move_id: Account move wher the move lines will be.
		:param amount_residual: Amount to be posted.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
		:rtype: tuple of dict
		'''
		if amount_residual > 0:
			account_id = line.liability_move_line_id.company_id.expense_currency_exchange_account_id
			if not account_id:
				raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		else:
			account_id = line.liability_move_line_id.company_id.income_currency_exchange_account_id
			if not account_id:
				raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		# Even if the amount_currency is never filled, we need to pass the foreign currency because otherwise
		# the receivable/payable account may have a secondary currency, which render this field mandatory
		if line.liability_move_line_id.account_id.currency_id:
			account_currency_id = line.liability_move_line_id.account_id.currency_id.id
		else:
			account_currency_id = company_currency <> current_currency and current_currency or False
		move = self.pool.get('account.move').browse(cr, uid, move_id)
		move_line = {
			'journal_id': line.repayment_id.journal_id.id,
			'period_id': move.period_id.id,
			'name': _('change')+': '+(line.loan_id.name or '/'),
			'account_id': line.liability_move_line_id.account_id.id,
			'move_id': move_id,
			# 'partner_id': line.voucher_id.partner_id.id,
			'currency_id': account_currency_id,
			'amount_currency': 0.0,
			'quantity': 1,
			'credit': amount_residual > 0 and amount_residual or 0.0,
			'debit': amount_residual < 0 and -amount_residual or 0.0,
			'date': line.repayment_id.date,
		}
		move_line_counterpart = {
			'journal_id': line.repayment_id.journal_id.id,
			'period_id': move.period_id.id,
			'name': _('change')+': '+(line.loan_id.name or '/'),
			'account_id': account_id.id,
			'move_id': move_id,
			'amount_currency': 0.0,
			# 'partner_id': line.voucher_id.partner_id.id,
			'currency_id': account_currency_id,
			'quantity': 1,
			'debit': amount_residual > 0 and amount_residual or 0.0,
			'credit': amount_residual < 0 and -amount_residual or 0.0,
			'date': line.repayment_id.date,
		}
		return (move_line, move_line_counterpart)

	def repayment_move_line_create(self, cr, uid, repayment_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param repayment_id: Repayment id what we are working with
		:param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
		:param move_id: Account move wher those lines will be joined.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
		:rtype: tuple(float, list of int)
		'''
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		move_pool = self.pool.get('account.move')
		currency_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		tot_line = line_total
		rec_lst_ids = []

		date = self.read(cr, uid, repayment_id, ['date'], context=context)['date']
		ctx = context.copy()
		ctx.update({'date': date})
		repayment = self.browse(cr, uid, repayment_id, context=ctx)
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		
		move = self.pool.get('account.move').browse(cr, uid, move_id)
		for line in repayment.line_ids:
			#create one move line per voucher line where amount is not 0.0
			# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
			if not line.amount and not (line.liability_move_line_id and not float_compare(line.liability_move_line_id.debit, line.liability_move_line_id.credit, precision_digits=prec) and not float_compare(line.liability_move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
			# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			
			amount = self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, line.amount, context=ctx)
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
			# currency rate difference
			if line.amount == line.amount_unreconciled:
				if not line.liability_move_line_id:
					raise osv.except_osv(_('Wrong repayment line'),_("The loan you are willing to pay is not valid anymore."))
				# sign = line.type =='dr' and -1 or 1
				sign = amount>0 and 1 or -1
				currency_rate_difference = sign * (line.liability_move_line_id.amount_residual - amount)
			else:
				currency_rate_difference = 0.0
			move_line = {
				'journal_id': repayment.journal_id.id,
				'period_id': move.period_id.id,
				'name': line.repayment_id.memo or line.loan_id.name or '/',
				'other_ref' : line.liability_move_line_id.ref or '',
				'account_id': line.liability_move_line_id.account_id.id,
				'move_id': move_id,
				# 'partner_id': voucher.partner_id.id,
				'currency_id': company_currency <> current_currency and current_currency or False,
				# 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': repayment.date,
				# 'ref': line.account_id.type=='liquidity' and voucher.reference or line.name or '/'
			}
			
			if amount < 0:
				move_line['credit'] = abs(amount)
			else:
				move_line['debit'] = abs(amount)
			tot_line -= amount
			
			# compute the amount in foreign currency
			foreign_currency_diff = 0.0
			amount_currency = False
			if line.liability_move_line_id:
				# We want to set it on the account move line as soon as the original line had a foreign currency
				if line.liability_move_line_id.currency_id and line.liability_move_line_id.currency_id.id != company_currency:
					# we compute the amount in that foreign currency.
					if line.liability_move_line_id.currency_id.id == current_currency:
						# if the voucher and the voucher line share the same currency, there is no computation to do
						sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
						amount_currency = sign * (line.amount)
					else:
						# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
						# otherwise we use the rates of the system
						amount_currency = currency_obj.compute(cr, uid, company_currency, line.liability_move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
				if line.amount == line.amount_unreconciled:
					foreign_currency_diff = line.liability_move_line_id.amount_residual_currency - abs(amount_currency)

			move_line['amount_currency'] = amount_currency
			# print "################################ main credit",move_line['debit'],move_line['credit'],move_line['amount_currency']
			repayment_line = move_line_obj.create(cr, uid, move_line)
			rec_ids = [repayment_line, line.liability_move_line_id.id]

			if not currency_obj.is_zero(cr, uid, repayment.company_id.currency_id, currency_rate_difference):
				# Change difference entry in company currency

				exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				# print "################################ gain loss",exch_lines[0]['debit'],exch_lines[0]['credit'],exch_lines[0]['amount_currency']
				# print "################################ gain loss",exch_lines[1]['debit'],exch_lines[1]['credit'],exch_lines[1]['amount_currency']
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
				move_line_obj.create(cr, uid, exch_lines[1], context)
				rec_ids.append(new_id)
			
			if line.liability_move_line_id and line.liability_move_line_id.id:
				rec_lst_ids.append(rec_ids)

		# if voucher.writeoff_amount and voucher.writeoff_amount !=0.0:
		# 	amount = 0.0
		# 	if voucher.writeoff_amount and not voucher.extra_writeoff:
		# 		amount += self._convert_amount(cr, uid, voucher.writeoff_amount, voucher.id, context=ctx) #possibility : -0.0
		# 		tot_line -= amount
		# 	elif voucher.extra_writeoff and voucher.writeoff_lines:
		# 		for wline in voucher.writeoff_lines:
		# 			amount_per_line = self._convert_amount(cr, uid, wline.amount, voucher.id, context=ctx)  #possibility : -0.0
		# 			amount += amount_per_line
		# 			tot_line -= amount_per_line

		# 	diff_account_id = False
		# 	if voucher.payment_option == 'with_writeoff' and voucher.writeoff_acc_id:
		# 		diff_account_id = voucher.writeoff_acc_id.id
		# 	elif voucher.partner_id:
		# 		if voucher.type in ('sale', 'receipt'):
		# 			diff_account_id = voucher.partner_id.property_account_receivable.id
		# 		else:
		# 			diff_account_id = voucher.partner_id.property_account_payable.id
		# 	else:
		# 		# fallback on account of voucher
		# 		diff_account_id = voucher.account_id.id
		# 	move_line_rounding = {
		# 			'journal_id': voucher.journal_id.id,
		# 			'period_id': voucher.period_id.id,
		# 			'name': _('Rounding difference'),
		# 			'account_id': diff_account_id,
		# 			'move_id': move_id,
		# 			'partner_id': line.voucher_id.partner_id.id,
		# 			'quantity': 1,
		# 			'credit': tot_line>0.0 and tot_line or 0.0,
		# 			'debit': tot_line<0.0 and -1*tot_line or 0.0,
		# 			'date': line.voucher_id.date,
		# 			'amount_currency':0.0,
		# 		}
		# 	print "################################ selisih rounding",move_line_rounding['debit'],move_line_rounding['credit'],move_line_rounding['amount_currency']
		# 	new_id = move_line_obj.create(cr, uid, move_line_rounding, context=context)
		# 	tot_line=amount
		return (tot_line, rec_lst_ids)

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_repayment_line_pool = self.pool.get('account.bank.loan.repayment')
		loan_pool = self.pool.get('account.bank.loan')
		wf_service = netsvc.LocalService("workflow")
		
		for repayment in self.browse(cr, uid, ids, context=context):
			local_context = dict(context, force_company=repayment.journal_id.company_id.id)
			if repayment.move_id:
				continue
			company_currency = repayment.journal_id.company_id.currency_id.id
			current_currency = repayment.journal_id.currency and repayment.journal_id.currency.id or company_currency
			
			# But for the operations made by _convert_amount, we always need to give the date in the context
			ctx = context.copy()
			ctx.update({'date': repayment.date})
			
			# Create the account move record.
			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, repayment.id, context=ctx), context=context)
			# Get the name of the account_move just created
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			# Create the first line of the voucher
			local_context.update({'move_name':name})
			move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,repayment.id, move_id, company_currency, current_currency, local_context), local_context)
			move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
			line_total = move_line_brw.debit - move_line_brw.credit
			
			rec_list_ids = []
			
			# Create one move line per voucher line where amount is not 0.0
			line_total, rec_list_ids = self.repayment_move_line_create(cr, uid, repayment.id, line_total, move_id, company_currency, current_currency, context=context)
			
			# Create the writeoff line if needed
			# ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
			# if ml_writeoff and not voucher.extra_writeoff:
			# 	move_line_pool.create(cr, uid, ml_writeoff, local_context)
			# if voucher.extra_writeoff and voucher.writeoff_lines:
			# 	self.writeoff_move_line_get_extra(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
			
			# We post the voucher.
			self.write(cr, uid, [repayment.id], {
				'move_id': move_id,
				'state': 'posted',
				'name': name,
			})
			# and we delete all Credit Lines and Debit Lines that are not allocated
			for line in repayment.line_ids:
				if line.amount==0.0:
					self.unlink(cr, uid, line.id)
			
			self.write(cr, uid, repayment.id, {'line_ids':[]})

			# We Post the Journal Voucher created, if entry_posted is True
			if repayment.journal_id.entry_posted:
				xx=move_pool.post(cr, uid, [move_id], context={})

			# We automatically reconcile the account move lines.
			reconcile = False
			
			for rec_ids in rec_list_ids:
				if len(rec_ids) >= 2:
					reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=False, writeoff_period_id=move_line_brw.period_id.id, writeoff_journal_id=repayment.journal_id.id)

			for line in repayment.line_ids:
				loan_repayment_line_pool.create(cr, uid, {
						'loan_id':line.loan_id and line.loan_id.id or False,
						'name' : name,
						'schedule_payment' : repayment.date,
						'payment_date' : repayment.date,
						'planning_amount' : line.amount,
						'revision_amount' : 0.0,
						'lastest_revision' : 0.0,
						'real_amount' : line.amount,
						'journal_id' : repayment.journal_id.id,
						'move_id' : move_id,
						'state' : 'paid2',
						'drawdown_repayment_id' : repayment.id,
					})
				wf_service.trg_validate(uid, 'account.bank.loan', line.loan_id.id, 'test_paid', cr)
		return True

	def action_confirm(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		
		return self.write(cr, uid, ids, {'state':'confirmed'}, context=context)

	def action_cancel(self, cr, uid, ids, context=None):
		if context is None:
			context = {}

		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		loan_repayment_line_pool = self.pool.get('account.bank.loan.repayment')
		wf_service = netsvc.LocalService("workflow")
		move_lines = []
		for obj in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			obj.refresh()
			if obj.move_id and obj.move_ids:
				amr_objs = list(set([line.reconcile_id for line in obj.move_ids if line.reconcile_id]))
				rec_list_ids = []
				for line in obj.move_ids:
					line.refresh()
					if line.reconcile_id:
						rec_ids = []
						for amr in amr_objs:
							if amr.id == line.reconcile_id.id:
								rec_ids = [move_line.id for move_line in line.reconcile_id.line_id]
								rec_ids.remove(line.id)
							#reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
							# amr.append(line.reconcile_id.id)
						rec_list_ids.append(rec_ids)
				reconcile_pool.unlink(cr, uid, [amr.id for amr in amr_objs])
				for rec_ids in rec_list_ids:
					if len(rec_ids) >= 2:
						move_line_pool.reconcile_partial(cr, uid, rec_ids, 'auto',context=context)
				if obj.move_id:
					move_pool.button_cancel(cr, uid, [obj.move_id.id])
					move_pool.unlink(cr, uid, [obj.move_id.id])

			cr.execute("SELECT id,loan_id FROM account_bank_loan_repayment WHERE drawdown_repayment_id=%s"%str(obj.id))
			line_ids = [x[0] for x in cr.fetchall()]
			loan_repayment_line_pool.unlink(cr, uid, line_ids)
			for line in obj.line_ids:
				if line.loan_id and line.loan_id.state=='paid':
					wf_service.trg_validate(uid, 'account.bank.loan', line.loan_id.id, 'open_test', cr)
		return self.write(cr, uid, ids, {'state':'cancel','move_id':False}, context=context)

	def action_set_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		
		return self.write(cr, uid, ids, {'state':'draft'}, context=context)
			
account_bank_loan_drawdown_repayment()

class account_bank_loan_drawdown_repayment_line(osv.Model):
	_name = "account.bank.loan.drawdown.repayment.line"
	_columns = {
		'repayment_id' : fields.many2one('account.bank.loan.drawdown.repayment','Reference'),
		'date' : fields.related('repayment_id','date',type='date',string='Date Payment'),
		'loan_id':fields.many2one('account.bank.loan','Bank Loan', required=True),
		'liability_move_line_id' : fields.related('loan_id','liability_move_line_id',type='many2one',relation='account.move.line',string='Liability Entry Item'),
		'date' : fields.related('loan_id','effective_date',type='date',string='Date Original'),
		'amount_original' : fields.float('Amount Original', digits_compute=dp.get_precision('Account')),
		'amount_unreconciled' : fields.float('Amount Unreconciled', digits_compute=dp.get_precision('Account')),
		'full_reconcile' : fields.boolean("Full Reconcile"),
		'amount' : fields.float("Allocation", digits_compute= dp.get_precision('Account')),
	}

	def onchange_full_reconcile(self, cr, uid, ids, full_reconcile, amount_unreconciled, context=None):
		if context is None:
			context = {}

		res = {}
		if full_reconcile:
			res = {'amount':amount_unreconciled}
		else:
			res = {'amount':0.0}
		return {'value':res}
account_bank_loan_drawdown_repayment_line()



##################### PAYMENT INTEREST LOAN ##############################
class account_bank_loan_drawdown_interest(osv.Model):
	_name = "account.bank.loan.drawdown.interest"
	_columns = {
		'name' : fields.char('Number',size=128, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'memo' : fields.char('Memo',size=128, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'ref' : fields.char('Payment Ref',size=128, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'entry_date' : fields.date('Entry Date', readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'date' : fields.date('Payment Date', required=True, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'amount' : fields.float("Repayment Amount", digits_compute= dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		
		'journal_id' : fields.many2one('account.journal','Payment Method',required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'account_interest': fields.many2one('account.account', 'Account Interest', required=True, readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'move_id':fields.many2one('account.move', 'Account Entry',readonly=True),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'state' : fields.selection([
			('draft','Draft'),
			('computed','Interest Computed'),
			('posted','Posted'),
			('cancel','Cancelled')], 'State'),
		# 'line_ids' : fields.one2many('account.bank.loan.drawdown.interest.line','interest_id','Interest Lines', readonly=True, states={'draft':[('readonly',False)],'confirmed':[('readonly',False)]}),
		'compute_type' : fields.selection([
			('multi','Using Multi Interest Rate'),
			('single','Using Single Interest Rate')], 'Computation Method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'rate' : fields.float("Rate", digits=(2,4)),
		'date_from' : fields.date("Interest From", required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'date_to' : fields.date("Interest To", required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'line_ids' :  fields.one2many('account.bank.loan.interest','drawdown_interest_id','Interest', readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'line_prov_ids' :  fields.one2many('account.bank.loan.interest','drawdown_interest_prov_id','Interest', readonly=True, states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'company_id' : fields.many2one('res.company', 'Company'),
		'is_provision' : fields.boolean('Provision', readonly=True,states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
		'prov_account_id' : fields.many2one('account.account', 'Provision Account',readonly=True,states={'draft':[('readonly',False)],'computed':[('readonly',False)]}),
	}

	_defaults = {
		'state' : lambda *s:'draft',
		'entry_date' : lambda *e:time.strftime('%Y-%m-%d'),
		'company_id' : lambda self, cr, uid, ids, context=None: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
	}

	def onchange_journal_id(self, cr, uid, ids, journal_id, date, date_from, date_to, compute_type, line_ids, is_provision, context=None):
		if context is None:
			context = {}
		res = {}
		journal_pool = self.pool.get('account.journal')
		currency_obj = self.pool.get('res.currency')
		interest_line_pool = self.pool.get('account.bank.loan.interest')
		loan_pool = self.pool.get('account.bank.loan')
		if not journal_id:
			return {'value':res}
		
		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		if (not journal.default_credit_account_id or not journal.default_debit_account_id) and not is_provision:
			raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal "%s".') % (journal.name))
		if line_ids:
			res.update({'line_ids':[]})
			
			line_ids = [x[1] for x in line_ids]
			loan_ids = [x.loan_id.id for x in interest_line_pool.browse(cr, uid, line_ids, context=context) if x.loan_id]
			for line_id in line_ids:
				interest_line_pool.unlink(cr, uid, line_id)

			for line in loan_pool.browse(cr, uid, loan_ids, context=context):
				res['line_ids'].append({
					'loan_id': line.id or False,
					'date_from': date_from,
					'date_to': date_to,
					'compute_type': compute_type,
					'payment_date' : date,
					'state' : 'draft',
					})
		
		return {'value':res}

	def account_move_get(self, cr, uid, interest_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		interest = self.browse(cr, uid, interest_id, context=context)
		name = interest.name or ''

		effective_date = context.get('date',(interest.date!='False' and interest.date or time.strftime('%Y-%m-%d')))
		if not name:
			if interest.journal_id.sequence_id:
				if not interest.journal_id.sequence_id.active:
					raise osv.except_osv(_('Configuration Error !'),
						_('Please activate the sequence of selected journal !'))
				c = {'date':datetime.strptime(effective_date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
				name = seq_obj.next_by_id(cr, uid, interest.journal_id.sequence_id.id, context=c)
			else:
				raise osv.except_osv(_('Error!'),
					_('Please define a sequence on the journal.'))
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		move = {
			'name': name,
			'ref':interest.ref or '',
			'journal_id': interest.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
			'comment' : interest.memo,
		}

		return move

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		interest_line_pool = self.pool.get('account.bank.loan.interest')
		
		for interest in self.browse(cr, uid, ids, context=context):
			if interest.move_id:
				continue
			
			date = interest.date!='False' and interest.date or time.strftime('%Y-%m-%d')
			context.update({'date':date})

			company_currency = interest.company_id.currency_id.id
			current_currency = interest.journal_id.currency and interest.journal_id.currency.id or company_currency

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, interest.id, context=context), context=context)
			move = move_pool.browse(cr, uid, move_id, context=context)
			name = move.name
			period=move.period_id
			
			bank_account_id=interest.journal_id.default_credit_account_id and interest.journal_id.default_credit_account_id.id or False
			if not bank_account_id and not interest.is_provision:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please set the account of selected Journal !'))

			check_balance = 0.0
			#amount interest line
			dict_provision_line = {}
			for line in interest.line_ids:
				interest_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, line.total_paid_amount, context=context)
				debit = credit = 0.0
				debit = interest_amount
				sign = debit - credit < 0 and -1 or 1

				move_line_pool.create(cr,uid,{
					'name': interest.memo or line.drawdown_interest_id.memo or line.loan_id.name or ''+'/'+interest.name or '/',
					'debit': debit,
					'credit': credit,
					'account_id': interest.account_interest and interest.account_interest.id or False,
					'move_id': move_id,
					'journal_id': interest.journal_id.id,
					'period_id': period and period.id or False,
					'currency_id': company_currency <> current_currency and  current_currency or False,
					'amount_currency': company_currency <> current_currency and sign * line.total_paid_amount or 0.0,
					'date': date,
				},context=context)
				# other charge amounnt
				line_total = line.total_paid_amount - interest_amount
				check_balance += debit-credit
				# print "::::::::::::::::1", (debit-credit), check_balance
				# if interest.writeoff_lines:
				# 	self.other_charge_move_line(cr, uid, interest.id, line_total, move_id, name, company_currency, current_currency)
				if interest.is_provision:
					move_id_liab=move_line_pool.create(cr,uid,{
						'name': interest.memo or line.drawdown_interest_id.memo or line.loan_id.name or ''+'/'+interest.name or '/',
						'debit': credit,
						'credit': debit,
						'account_id': interest.prov_account_id.id or False,
						'move_id': move_id,
						'journal_id': interest.journal_id.id,
						'period_id': period and period.id or False,
						'currency_id': company_currency <> current_currency and  current_currency or False,
						'amount_currency': company_currency <> current_currency and (-1* sign * line.total_paid_amount) or 0.0,
						'date': date,
					},context=context)
					check_balance += credit-debit
					dict_provision_line.update({line.id:move_id_liab})
					# print "::::::::::::::::1", (credit-debit), check_balance
			
			#amount interest provision line
			if not interest.is_provision and interest.line_prov_ids:
				for line in interest.line_prov_ids:
					interest_amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, line.total_paid_amount, context=context)
					debit = credit = 0.0
					debit = interest_amount
					sign = debit - credit < 0 and -1 or 1

					move_id_liab=move_line_pool.create(cr,uid,{
						'name': interest.memo or line.drawdown_interest_id.memo or line.loan_id.name or ''+'/'+interest.name or '/',
						'debit': debit,
						'credit': credit,
						'account_id': line.prov_account_id and line.prov_account_id.id or False,
						'move_id': move_id,
						'journal_id': interest.journal_id.id,
						'period_id': period and period.id or False,
						'currency_id': company_currency <> current_currency and  current_currency or False,
						'amount_currency': company_currency <> current_currency and sign * line.total_paid_amount or 0.0,
						'date': date,
					},context=context)
					check_balance += debit-credit
					# print "::::::::::::::::2", (debit-credit), check_balance
					# other charge amounnt
					if line.liability_move_prov_id:
						balance_prov = line.liability_move_prov_id.debit - line.liability_move_prov_id.credit
						diff = (debit-credit) + balance_prov
						if diff!=0.0:
							exchange_gain_loss=move_line_pool.create(cr,uid,{
									'name': 'Difference %s'%(line.drawdown_interest_id.memo or line.loan_id.name or ''+'/'+interest.name or '/'),
									'debit': diff>0.0 and 0.0 or diff,
									'credit': diff<0.0 and 0.0 or abs(diff),
									'account_id': line.prov_account_id and line.prov_account_id.id or False,
									'move_id': move_id,
									'journal_id': interest.journal_id.id,
									'period_id': period and period[0] or False,
									'partner_id': loan.partner_id.id,
									'currency_id': company_currency <> current_currency and  current_currency or False,
									'amount_currency': 0.0,
									'date': date,
								},context)

							exchange_gain_loss_counterpart=move_line_pool.create(cr,uid,{
									'name': 'Difference %s'%(line.drawdown_interest_id.memo or line.loan_id.name or ''+'/'+interest.name or '/',),
									'debit': diff<0.0 and 0.0 or abs(diff),
									'credit': diff>0.0 and 0.0 or diff,
									'account_id': line.prov_account_id and line.prov_account_id.id or False,
									'move_id': move_id,
									'journal_id': interest.journal_id.id,
									'period_id': period and period[0] or False,
									'partner_id': loan.partner_id.id,
									'currency_id': company_currency <> current_currency and  current_currency or False,
									'amount_currency': 0.0,
									'date': date,
								},context)
						# check_balance += debit-credit
					line_total = line.total_paid_amount - interest_amount
					# if interest.writeoff_lines:
					# 	self.other_charge_move_line(cr, uid, interest.id, line_total, move_id, name, company_currency, current_currency)

			if not interest.is_provision:
				#amount bank
				debit = credit = 0.0
				credit =  interest.amount #+  + total_cost
				sign = debit - credit < 0 and -1 or 1
					
				move_line_pool.create(cr,uid,{
					'name': interest.memo or line.drawdown_interest_id.memo or name,
					'debit': debit,
					'credit': credit,
					'account_id': bank_account_id or False,
					'move_id': move_id,
					'journal_id': interest.journal_id.id,
					'period_id': period and period.id or False,
					# 'partner_id': loan.partner_id.id,
					'currency_id': company_currency <> current_currency and  current_currency or False,
					'amount_currency': company_currency <> current_currency and sign * (interest.amount) or 0.0,
					'date': date,
				},context)
				check_balance += (debit-credit)
				# print "::::::::::::::::3", (debit-credit), round(check_balance,2)
				
			if round(check_balance,2)!=0.0:
				raise osv.except_osv(_('Error!'), _('Please put the Correct Total Interest Amount'))
			
			self.write(cr, uid, interest.id ,{'state':'posted','move_id':move_id})
			if interest.move_id and interest.journal_id.entry_posted:
				move_pool.post(cr, uid, [move_id], context={})

			if interest.is_provision:
				for line in interest.line_ids:
					to_update = {
						'journal_id' : interest.journal_id.id,
						'move_provision_id':move_id, 
						'state':'provision',
						'is_provision' : True,
						'liability_move_prov_id' : dict_provision_line.get(line.id,False),
						'prov_account_id' : interest.prov_account_id.id,
					}
					interest_line_pool.write(cr, uid, line.id, to_update)		
			else:
				for line in interest.line_ids+interest.line_prov_ids:
					to_update = {
						'journal_id' : interest.journal_id.id,
						# 'payment_date' : 
						'move_id':move_id, 
						'state':'paid2'
					}
					if not line.is_provision:
						to_update.update({'account_interest' : interest.account_interest.id})
					interest_line_pool.write(cr, uid, line.id, to_update)		
		return True

	def action_compute(self, cr, uid, ids, context=None):
		if context is None:
			context = {}

		interest_line_obj = self.pool.get('account.bank.loan.interest')
		for obj in self.browse(cr, uid, ids, context=context):
			for line in obj.line_ids:
				context.update({'journal_id':obj.journal_id.id})
				interest_line_obj.compute_interest(cr, uid, [line.id], context=context)
		
		return self.write(cr, uid, ids, {'state':'computed'}, context=context)

	def action_cancel(self, cr, uid, ids, context=None):
		if context is None:
			context = {}

		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		interest_line_pool = self.pool.get('account.bank.loan.interest')
		for obj in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			obj.refresh()
			if obj.move_id:
				move_pool.button_cancel(cr, uid, [obj.move_id.id])
				move_pool.unlink(cr, uid, [obj.move_id.id])
			interest_line_pool.action_unreconcile(cr, uid, [line.id for line in obj.line_ids+obj.line_prov_ids])
		return self.write(cr, uid, ids, {'state':'cancel','move_id':False}, context=context)

	def action_set_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		interest_line_pool = self.pool.get('account.bank.loan.interest')
		
		for obj in self.browse(cr, uid, ids, context=context):
			interest_line_pool.action_set_to_draft(cr, uid, [line.id for line in obj.line_ids])
		
		return self.write(cr, uid, ids, {'state':'draft'}, context=context)
			
account_bank_loan_drawdown_interest()