from openerp.osv import fields,osv
from tools.translate import _
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
class voucher_payment_type(osv.Model):
	_name = "voucher.payment.type"
	_columns = {
		"name" :fields.char("Name",required=True,size=128),
		'description':fields.text("Description",required=False),
	}

class account_voucher(osv.Model):
	_inherit = "account.voucher"
	_columns = {
		'invoice_related_id' : fields.many2one('account.invoice','Related Invoice',readonly=True, states={'draft': [('readonly', False)]}),
		"writeoff_lines"	: fields.one2many("account.voucher.writeoff",'voucher_id',"Writeoff Lines",readonly=True, states={'draft': [('readonly', False)]}),
		"extra_writeoff"	: fields.boolean("Use Extra Writeoff",readonly=True, states={'draft': [('readonly', False)]}),
		'date_create'		: fields.date("Creation Date",required=False,readonly=True, states={'draft': [('readonly', False)]}),
		'payment_type'		: fields.many2one('voucher.payment.type',"Payment Type",required=False,readonly=True, states={'draft': [('readonly', False)]}),
		'total_writeoff'	: fields.float('Total Write-Off Amount', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
		'use_new_sequence'	: fields.boolean('Use a new number?',readonly=True, states={'draft': [('readonly', False)]}),
	}

	def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
		context = context or {}
		
		res = super(account_voucher,self).onchange_line_ids(cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=context)
		if not res['value']['writeoff_amount']:
			res['value'].update({'writeoff_lines':[],'extra_writeoff':False})

		return res

	def onchange_writeoff_lines(self, cr, uid, ids, writeoff_lines, line_dr_ids, line_cr_ids, amount, type, context=None):
		context = context or {}
		if not line_dr_ids and not line_cr_ids:
			return {'value':{'writeoff_amount': 0.0}}
		line_osv = self.pool.get("account.voucher.line")
		writeoff_line_osv = self.pool.get("account.voucher.writeoff")
		
		line_dr_ids = resolve_o2m_operations(cr, uid, line_osv, line_dr_ids, ['amount'], context)
		line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, line_cr_ids, ['amount'], context)
		writeoff_lines = resolve_o2m_operations(cr, uid, writeoff_line_osv, writeoff_lines, ['amount','name','account_id','analytic_id','analytic_journal_id','type','invoice_related_id'], context)
		total_writeoff = 0.0
		
		for writeoff_line in writeoff_lines:
			total_writeoff += writeoff_line.get('amount',0.0)

		if total_writeoff:
			amount-=total_writeoff

		return {'value': {'total_writeoff': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount, type)}}

	def writeoff_move_line_get_extra(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		'''
		Set a dict to be use to create the writeoff move line.

		:param voucher_id: Id of voucher what we are creating account_move.
		:param line_total: Amount remaining to be allocated on lines.
		:param move_id: Id of account move where this line will be added.
		:param name: Description of account move line.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		currency_obj = self.pool.get('res.currency')
		# move_line = {}

		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

		if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
			wfline={}
			analytic_line = {}
			movex_line = {}
			sign = voucher.type == 'payment' and 1 or -1
			# sign = 1
			for line in voucher.writeoff_lines:
				amount = currency_obj.compute(cr,uid,voucher.currency_id.id,voucher.journal_id.company_id.currency_id.id,sign*line.amount,context={'date':voucher.date})
				mvl = {
				'name': line.name or name,
				'account_id': line.account_id and line.account_id.id or False,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'date': voucher.date,
				'amount_currency': company_currency <> current_currency and (sign * line.amount) or 0.0,
				'currency_id': company_currency <> current_currency and current_currency or False,
				#'analytic_account_id': line.analytic_id and line.analytic_id.id or False,
				}

				mvl['debit'] = amount > 0 and amount or 0.0
				mvl['credit'] = amount < 0 and -amount or 0.0
				
				if line.account_id.id in wfline:
					
					amount_exist = wfline[line.account_id.id]['credit']>0.0 and wfline[line.account_id.id]['credit'] or wfline[line.account_id.id]['debit']
					currency_exist = wfline[line.account_id.id]['amount_currency']
					amount +=amount_exist
					line_curr =company_currency <> current_currency and (line.amount) or 0.0

					amount_currency = line_curr - currency_exist
					# print "==================amountxxxxxxxxxxxxxxxxx",line_curr,currency_exist,amount_currency
					mvl.update({
						'amount_currency' : company_currency <> current_currency and (sign * amount_currency) or 0.0
						})
					mvl['debit'] = amount > 0 and amount or 0.0
					mvl['credit'] = amount < 0 and -amount or 0.0
				print "################################ writeoff",mvl['debit'],mvl['credit'],mvl['amount_currency']
				wfline.update({line.account_id.id:mvl})
			for wx in wfline.keys():
				move_id = self.pool.get('account.move.line').create(cr,uid,wfline[wx],context)
				movex_line.update({wfline[wx]['account_id']:move_id})
			for obj_line in voucher.writeoff_lines:
				amt = currency_obj.compute(cr,uid,voucher.currency_id.id,voucher.journal_id.company_id.currency_id.id,obj_line.amount,context={'date':voucher.date}) 
				# print
				if obj_line.analytic_id and obj_line.analytic_id.id:
					anline={
							"invoice_related_id" : obj_line.invoice_related_id,
							"name"			: obj_line.name,
							"date"			: voucher.date,
							"account_id"	: obj_line.analytic_id.id,
							"amount"		: amt,
							"general_acccount":obj_line.account_id.id,
							"move_id"		: movex_line[obj_line.account_id.id],
							"journal_id"	: obj_line.analytic_journal_id.id or obj_line.journal_id.analytic_journal_id.id,
							"ref"			: obj_line.name,
						   }
					xid=self.pool.get('account.move.line.distribution').create(cr,uid,anline,context)
		return True

	def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
		'''
		Return a dict to be use to create the first account move line of given voucher.

		:param voucher_id: Id of voucher what we are creating account_move.
		:param move_id: Id of account move where this line will be added.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		debit = credit = 0.0
		# TODO: is there any other alternative then the voucher type ??
		# ANSWER: We can have payment and receipt "In Advance".
		# TODO: Make this logic available.
		# -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
		if voucher.type in ('purchase', 'payment'):
			credit = voucher.paid_amount_in_company_currency
		elif voucher.type in ('sale', 'receipt'):
			debit = voucher.paid_amount_in_company_currency
		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1
		#set the first line of the voucher
		move_line = {
				'name': voucher.name or '/',
				'debit': debit,
				'credit': credit,
				'account_id': voucher.account_id.id,
				'move_id': move_id,
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'partner_id': voucher.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				'amount_currency': (sign * abs(voucher.amount) # amount < 0 for refunds
					if company_currency != current_currency else 0.0),
				'date': voucher.date,
				'date_maturity': voucher.date_due,
				'ref': voucher.account_id.type=='liquidity' and voucher.reference or voucher.name or '/'
			}
		# print "=========first==============",voucher.account_id.type=='liquidity' and voucher.reference or voucher.name or '/'
		print "############################# first_move_line_get", move_line['debit'], move_line['credit'], move_line['amount_currency']
		return move_line

	def fix_move_line_reference(self,cr,uid,ids,context=None):
		if not context:context={}
		for voucher in self.browse(cr,uid,ids,context):
			if voucher.move_id and voucher.move_ids:
				for line in voucher.move_ids:
					if line.account_id.type in ('liquidity',):
						line.write({'ref':voucher.reference,'other_ref':voucher.reference,'name':line.partner_id.name})
					if line.account_id.type == 'receivable':
						line.write({'ref':line.name,'other_ref':line.name,'name':line.partner_id.name})
					if line.account_id.type in ('receivable','payable'):
						line.write({'ref':line.name,'other_ref':line.name,'name':line.partner_id.name})
		return True

	def account_move_get(self, cr, uid, voucher_id, context=None):
		'''
		This method prepare the creation of the account move related to the given voucher.

		:param voucher_id: Id of voucher for which we are creating account_move.
		:return: mapping between fieldname and value of account move to create
		:rtype: dict
		'''
		seq_obj = self.pool.get('ir.sequence')
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)

		if not voucher.use_new_sequence and voucher.number:
			name = voucher.number
		elif voucher.journal_id.sequence_id:
		# if voucher.journal_id.sequence_id:
			if not voucher.journal_id.sequence_id.active:
				raise osv.except_osv(_('Configuration Error !'),
					_('Please activate the sequence of selected journal !'))
			c = dict(context)
			c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id,'date':datetime.strptime(voucher.date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
			name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
		else:
			raise osv.except_osv(_('Error!'),
						_('Please define a sequence on the journal.'))
		if not voucher.reference:
			ref = name.replace('/','')
		else:
			ref = voucher.reference

		move = {
			'name': name,
			'journal_id': voucher.journal_id.id,
			'narration': voucher.narration,
			'date': voucher.date,
			'ref': ref,
			'period_id': voucher.period_id.id,
		}
		return move

	def _convert_amount(self, cr, uid, amount, voucher_id, context=None):
		'''
		This function convert the amount given in company currency. It takes either the rate in the voucher (if the
		payment_rate_currency_id is relevant) either the rate encoded in the system.

		:param amount: float. The amount to convert
		:param voucher: id of the voucher on which we want the conversion
		:param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
			field in order to select the good rate to use.
		:return: the amount in the currency of the voucher's company
		:rtype: float
		'''
		if context is None:
			context = {}
		currency_obj = self.pool.get('res.currency')
		voucher = self.browse(cr, uid, voucher_id, context=context)
		return currency_obj.compute(cr, uid, voucher.currency_id.id, voucher.company_id.currency_id.id, amount, context=context)

	def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param voucher_id: Voucher id what we are working with
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

		date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
		ctx = context.copy()
		ctx.update({'date': date})
		voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
		voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
		# ctx.update({
		# 	'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
		# 	'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		for line in voucher.line_ids:
			#create one move line per voucher line where amount is not 0.0
			# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
			if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
			# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			
			amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
			
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
			# currency rate difference
			if line.amount == line.amount_unreconciled:
				if not line.move_line_id:
					raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
				sign = line.type =='dr' and -1 or 1
				currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
			else:
				currency_rate_difference = 0.0
			move_line = {
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'name': line.name or '/',
				'account_id': line.account_id.id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
				'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': voucher.date,
				'ref': line.account_id.type=='liquidity' and voucher.reference or line.name or '/'
			}
			
			if amount < 0:
				amount = -amount
				if line.type == 'dr':
					line.type = 'cr'
				else:
					line.type = 'dr'

			if (line.type=='dr'):
				tot_line += amount
				move_line['debit'] = amount
			else:
				tot_line -= amount
				move_line['credit'] = amount

			if voucher.tax_id and voucher.type in ('sale', 'purchase'):
				move_line.update({
					'account_tax_id': voucher.tax_id.id,
				})

			if move_line.get('account_tax_id', False):
				tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
				if not (tax_data.base_code_id and tax_data.tax_code_id):
					raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

			# compute the amount in foreign currency
			foreign_currency_diff = 0.0
			amount_currency = False
			if line.move_line_id:
				# We want to set it on the account move line as soon as the original line had a foreign currency
				if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
					# we compute the amount in that foreign currency.
					if line.move_line_id.currency_id.id == current_currency:
						# if the voucher and the voucher line share the same currency, there is no computation to do
						sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
						amount_currency = sign * (line.amount)
					else:
						# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
						# otherwise we use the rates of the system
						amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
				if line.amount == line.amount_unreconciled:
					foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)
			move_line['amount_currency'] = amount_currency
			print "################################ main credit",move_line['debit'],move_line['credit'],move_line['amount_currency']
			
			voucher_line = move_line_obj.create(cr, uid, move_line)
			rec_ids = [voucher_line, line.move_line_id.id]

			if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
				# Change difference entry in company currency

				exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				print "################################ gain loss",exch_lines[0]['debit'],exch_lines[0]['credit'],exch_lines[0]['amount_currency']
				print "################################ gain loss",exch_lines[1]['debit'],exch_lines[1]['credit'],exch_lines[1]['amount_currency']
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
				move_line_obj.create(cr, uid, exch_lines[1], context)
				rec_ids.append(new_id)
			
			#create journal item to reconcile its receivable/payable for the amount currency balance 
			if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
				# Change difference entry in voucher currency
				if line.move_line_id.amount_currency > 0:
					foreign_currency_diff = -foreign_currency_diff
				else:
					foreign_currency_diff = foreign_currency_diff

				
				move_line_foreign_currency = {
					'journal_id': line.voucher_id.journal_id.id,
					'period_id': line.voucher_id.period_id.id,
					'name': _('change')+': '+(line.name or '/'),
					'account_id': line.account_id.id,
					'move_id': move_id,
					'partner_id': line.voucher_id.partner_id.id,
					'currency_id': line.move_line_id.currency_id.id,
					'amount_currency': foreign_currency_diff,
					'quantity': 1,
					'credit': 0.0,
					'debit': 0.0,
					'date': line.voucher_id.date,
				}
				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
				rec_ids.append(new_id)
			
			if line.move_line_id and line.move_line_id.id:
				rec_lst_ids.append(rec_ids)

		if voucher.writeoff_amount and voucher.writeoff_amount !=0.0:
			amount = 0.0
			if voucher.writeoff_amount and not voucher.extra_writeoff:
				amount += self._convert_amount(cr, uid, voucher.writeoff_amount, voucher.id, context=ctx) #possibility : -0.0
				if voucher.type in ('sale', 'receipt'):
					tot_line -= amount
				else:
					tot_line += amount
			elif voucher.extra_writeoff and voucher.writeoff_lines:
				for wline in voucher.writeoff_lines:
					amount_per_line = self._convert_amount(cr, uid, wline.amount, voucher.id, context=ctx)  #possibility : -0.0
					amount += amount_per_line
					if voucher.type in ('sale', 'receipt'):
						tot_line -= amount_per_line
					else:
						tot_line += amount_per_line

			diff_account_id = False
			if voucher.payment_option == 'with_writeoff' and voucher.writeoff_acc_id:
				diff_account_id = voucher.writeoff_acc_id.id
			elif voucher.partner_id:
				if voucher.type in ('sale', 'receipt'):
					diff_account_id = voucher.partner_id.property_account_receivable.id
				else:
					diff_account_id = voucher.partner_id.property_account_payable.id
			else:
				# fallback on account of voucher
				diff_account_id = voucher.account_id.id
			move_line_rounding = {
					'journal_id': voucher.journal_id.id,
					'period_id': voucher.period_id.id,
					'name': _('Rounding difference'),
					'account_id': diff_account_id,
					'move_id': move_id,
					'partner_id': line.voucher_id.partner_id.id,
					'quantity': 1,
					'credit': tot_line>0.0 and tot_line or 0.0,
					'debit': tot_line<0.0 and -1*tot_line or 0.0,
					'date': line.voucher_id.date,
					'amount_currency':0.0,
				}
			print "################################ selisih rounding",move_line_rounding['debit'],move_line_rounding['credit'],move_line_rounding['amount_currency']
			if abs(round(tot_line,2)) != 0.0 and abs(round(tot_line,2)) < 0.99:
				new_id = move_line_obj.create(cr, uid, move_line_rounding, context=context)
			if voucher.type in ('sale', 'receipt'):
				tot_line=amount
			else:
				tot_line=-1*amount
		return (tot_line, rec_lst_ids)

	def action_move_line_create(self, cr, uid, ids, context=None):
		'''
		Confirm the vouchers given in ids and create the journal entries for each of them
		'''

		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		voucher_line_pool = self.pool.get('account.voucher.line')
		for voucher in self.browse(cr, uid, ids, context=context):
			local_context = dict(context, force_company=voucher.journal_id.company_id.id)
			if voucher.move_id:
				continue
			company_currency = self._get_company_currency(cr, uid, voucher.id, context)
			current_currency = self._get_current_currency(cr, uid, voucher.id, context)
			# we select the context to use accordingly if it's a multicurrency case or not
			context = self._sel_context(cr, uid, voucher.id, context)
			# But for the operations made by _convert_amount, we always need to give the date in the context
			ctx = context.copy()
			ctx.update({'date': voucher.date})
			# Create the account move record.
			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
			# Get the name of the account_move just created
			name = move_pool.browse(cr, uid, move_id, context=context).name
			
			# Create the first line of the voucher
			# local_context.update({'move_name':name})
			move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
			move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
			line_total = move_line_brw.debit - move_line_brw.credit
			
			rec_list_ids = []
			if voucher.type == 'sale':
				line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
			elif voucher.type == 'purchase':
				line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
			# Create one move line per voucher line where amount is not 0.0
			line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
			# Create the writeoff line if needed
			ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
			if ml_writeoff and not voucher.extra_writeoff:
				move_line_pool.create(cr, uid, ml_writeoff, local_context)
			if voucher.extra_writeoff and voucher.writeoff_lines:
				self.writeoff_move_line_get_extra(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
			
			# We post the voucher.
			self.write(cr, uid, [voucher.id], {
				'move_id': move_id,
				'state': 'posted',
				'number': name,
			})
			# and we delete all Credit Lines and Debit Lines that are not allocated
			for line in voucher.line_cr_ids+voucher.line_dr_ids:
				if line.amount==0.0:
					voucher_line_pool.unlink(cr, uid, line.id)
			self.write(cr, uid, voucher.id, {'line_ids':[]})

			# We Post the Journal Voucher created, if entry_posted is True
			if voucher.journal_id.entry_posted:
				xx=move_pool.post(cr, uid, [move_id], context={})
				
			# We automatically reconcile the account move lines.
			reconcile = False
			
			for rec_ids in rec_list_ids:
				if len(rec_ids) >= 2:
					reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
		self.fix_move_line_reference(cr,uid,ids,context=None)
		return True

class account_voucher_writeoff(osv.Model):
	_name = "account.voucher.writeoff"
	_columns = {
		"name" 					: fields.char("Description",required=True,size=128),
		"voucher_id"			: fields.many2one("account.voucher","Voucher",required=False,ondelete="cascade"),
		"currency_id"			: fields.related("voucher_id","currency_id",type='many2one',relation='res.currency',readonly=True, string="Currency"),
		"account_id"			: fields.many2one("account.account","Counter Part Account",required=True),
		"analytic_id"			: fields.many2one("account.analytic.account","Analytic Account"),
		"analytic_journal_id"	: fields.many2one("account.analytic.journal","Analytic Journal"),
		"amount"				: fields.float("Writeoff Amount",required=True),
		"type"					: fields.many2one("charge.type","Writeoff Type"),
		'invoice_related_id' : fields.many2one('account.invoice','Related Invoice'),
	}

	def onchange_charge(self, cr, uid, ids, type_of_charge):
		result={}
		charge = self.pool.get('charge.type').browse(cr,uid,type_of_charge)
		if charge.account_id:
			result= {'value':{'account_id':charge.account_id and charge.account_id.id or False}}
			return result
		else:
			return result
account_voucher_writeoff()

def resolve_o2m_operations(cr, uid, target_osv, operations, fields, context):
	results = []
	for operation in operations:
		result = None
		if not isinstance(operation, (list, tuple)):
			result = target_osv.read(cr, uid, operation, fields, context=context)
		elif operation[0] == 0:
			# may be necessary to check if all the fields are here and get the default values?
			result = operation[2]
		elif operation[0] == 1:
			result = target_osv.read(cr, uid, operation[1], fields, context=context)
			if not result: result = {}
			result.update(operation[2])
		elif operation[0] == 4:
			result = target_osv.read(cr, uid, operation[1], fields, context=context)
		if result != None:
			results.append(result)
	return results