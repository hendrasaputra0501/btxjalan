import time
from datetime import datetime
from operator import itemgetter
from openerp.report import report_sxw

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT

class bank_transaction(osv.osv):
	_name = "bank.transaction"
	_description = "Bank Transaction"

	def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
		if not ids: return {}
		currency_obj = self.pool.get('res.currency')
		res = {}
		total = 0.0
		for bank_trans in self.browse(cr, uid, ids, context=context):
			context.update({'date':bank_trans.date})
			for l in bank_trans.line_ids:
				total += (l.amount / l.force_rate)
			
			currency = bank_trans.currency_id or bank_trans.company_id.currency_id
			res[bank_trans.id] =  currency_obj.round(cr, uid, currency, bank_trans.amount - total)
		return res

	def _get_alocated_amount(self, cr, uid, ids, name, args, context=None):
		if not ids: return {}
		currency_obj = self.pool.get('res.currency')
		res = {}
		for bank_trans in self.browse(cr, uid, ids, context=context):
			total = bank_trans.amount
			for l in bank_trans.line_ids:
				total -= l.source_amount
			
			res[bank_trans.id] =  total
		return res
	
	_columns = {
		'name' : fields.char('Transaction', 64,required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'number': fields.char('Number', size=32, readonly=True,),
		'ref' : fields.char('Ref',64,readonly=True, states={'draft':[('readonly',False)]}),
		'note' : fields.text('Notes'),
		'date_created': fields.date('Creation date', select=True,readonly=True, states={'draft':[('readonly',False)]}),
		'company_id' : fields.many2one('res.company', string ='Company', required =True),
		
		'partner_id' : fields.many2one('res.partner','Partner',readonly=True, states={'draft':[('readonly',False)]}),
		'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}, help="Journal Cash/Bank Payment"),
		'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'date' : fields.date('Date Effective',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], help="Keep empty to use the period of the validation(invoice) date.", readonly=True, states={'draft':[('readonly',False)]}),
		'amount':fields.float('Amount Total', digits_compute=dp.get_precision('Account'),required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'state':fields.selection([('draft','Draft'), ('confirm','Confirm'),('posted','Posted')], 'State', readonly=True,
						  help='When bank transaction is created the state will be \'Draft\'.\n* When all the payments are done it will be in \'Posted\' state.'),
		
		'line_ids':fields.one2many('bank.transaction.line','bank_trans_id','Bank Transaction Lines',readonly=True, states={'draft':[('readonly',False)]}),
		'move_id':fields.many2one('account.move', 'Journal Entry',readonly=True, states={'draft':[('readonly',False)]}),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True),
		'writeoff_amount': fields.function(_get_writeoff_amount, string='Difference Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
		'alocated_amount': fields.function(_get_alocated_amount, string='Diff. Alocated Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
		'gainloss_acc_id' : fields.many2one('account.account','Gain/Loss Account', states={'draft':[('readonly',False)]}),
	}
	
	_defaults = {
		'state':lambda *a:'draft',
		'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'bank.transaction', context=c),
		}

	def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
		result = {
			'value':{},
		}
		journal_pool = self.pool.get('account.journal')
		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		result['value'].update({'currency_id':journal.currency and journal.currency.id or journal.company_id.currency_id.id or False})
		return result

	def onchange_amount(self, cr, uid, ids, line_ids, amount, context=None):
		if context is None:
			context = {}
		if not line_ids:
			return {'value':{'alocated_amount': amount}}
		line_osv = self.pool.get("bank.transaction.line")
		line_ids = resolve_o2m_operations(cr, uid, line_osv, line_ids, ['source_amount'], context)
		alocated_amount = 0.0
		for l in line_ids:
			alocated_amount+=l['source_amount']
		return {'value':{'alocated_amount':amount-alocated_amount},'context':context.update({'alocated_amount':amount-alocated_amount})}


	def onchange_line_ids(self, cr, uid, ids, line_ids, amount, context=None):
		if context is None:
			context = {}
		if not line_ids:
			return {'value':{'alocated_amount': 0.0}}
		line_osv = self.pool.get("bank.transaction.line")
		line_ids = resolve_o2m_operations(cr, uid, line_osv, line_ids, ['source_amount'], context)
		alocated_amount = 0.0
		for l in line_ids:
			alocated_amount+=l['source_amount']
		return {'value':{'alocated_amount':amount-alocated_amount},'context':context.update({'alocated_amount':amount-alocated_amount})}

	def cancel_approval(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state':'draft'}, context=None)
		return True
	
	def confirm_treasury(self, cr, uid, ids, context=None):
		period_obj = self.pool.get('account.period')
		for bank_trans in self.browse(cr,uid,ids,context=context):
			period_id = bank_trans.period_id and bank_trans.period_id.id or False
			if not period_id:
				period_ids = period_obj.find(cr, uid, bank_trans.date, context=context)
				period_id = period_ids and period_ids[0] or False
			self.write(cr, uid, ids, {'period_id': period_id, 'state':'confirm'}, context=None)
		return True

	def confirm_bank_trans(self, cr, uid, ids, context=None):
		if not context:
			context={}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		seq_obj = self.pool.get('ir.sequence')
		period_obj = self.pool.get('account.period')
		currency_obj = self.pool.get('res.currency')

		for bank_trans in self.browse(cr,uid,ids,context=context):
			company_currency=bank_trans.company_id.currency_id.id
			current_currency=bank_trans.journal_id.currency and bank_trans.journal_id.currency.id or bank_trans.company_id.currency_id.id
			period_id = bank_trans.period_id and bank_trans.period_id.id or False
			if not period_id:
				period_ids = period_obj.find(cr, uid, bank_trans.date, context=context)
				period_id = period_ids and period_ids[0] or False
			
			# name : for account_move_line
			if bank_trans.number:
				name = bank_trans.number
			elif bank_trans.journal_id.sequence_id:
				date2 = datetime.strptime(bank_trans.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT) 
				name = seq_obj.get_id(cr, uid, bank_trans.journal_id.sequence_id.id, context={'date':date2})
			else:
				raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))

			# ref : for reference on Journal Item on Credit Move Line
			if not bank_trans.ref:
				ref = name.replace('/','')
			else:
				ref = bank_trans.ref

			move = {
				'name': name,
				'journal_id': bank_trans.journal_id.id,
				'narration': bank_trans.name,
				'date': bank_trans.date,
				'ref': ref,
				'period_id': period_id,
				}
			
			move_id = move_pool.create(cr, uid, move)
			
			amt=bank_trans.amount
			if company_currency <> current_currency:
				context.update({'date':bank_trans.date})
				amt_curr=amt
				amt=currency_obj.compute(cr, uid, current_currency, company_currency, amt, context=context)

			move_line_credit = {
				'name': bank_trans.name or '/',
				'debit': 0,
				'other_ref': ref,
				'credit': amt,
				'account_id': bank_trans.journal_id.default_credit_account_id.id,
				'move_id': move_id,
				'journal_id': bank_trans.journal_id.id,
				'period_id': period_id,
				'partner_id': bank_trans.partner_id.id,
				'currency_id': company_currency <> current_currency and current_currency or False,
				'amount_currency': company_currency <> current_currency and -amt_curr or 0.0,
				'date': bank_trans.date,
			}
			
			move_line_pool.create(cr, uid, move_line_credit)

			total_line = amt
			for line in bank_trans.line_ids:
				
				amt_line = line.amount
				if company_currency <> line.currency_id.id:
					context.update({'date':line.bank_trans_id.date})
					debit = currency_obj.compute(cr, uid, line.currency_id.id, company_currency, amt_line, context=context)
					amount_cur = amt_line
				else:
					debit = amt_line

				move_line_debit = {
					'name': line.name or '/',
					'other_ref' : line.reference or '',
					'debit': debit,
					'credit': 0,
					'account_id': line.account_id.id,
					'move_id': move_id,
					'journal_id': line.journal_id.id,
					'period_id': period_id,
					'partner_id': bank_trans.partner_id and bank_trans.partner_id.id or False,
					'currency_id': line.currency_id.id <> company_currency and line.currency_id.id or False,
					'amount_currency': line.currency_id.id <> company_currency and amount_cur or 0.0,
					'date': bank_trans.date,
					}
				
				total_line -= debit
				
				move_line_pool.create(cr, uid, move_line_debit)
			
			if not currency_obj.is_zero(cr, uid, bank_trans.company_id.currency_id, total_line):
				# create move_line gainloss
				debit = credit = 0.0
				if total_line < 0:
					credit = abs(total_line)
				else:
					debit = total_line

				# silakan diganti dengan account gainloss default jika ada
				curr_id = False
				desc = "Gain/Loss"
				if total_line < 0:
					gl_account_id = bank_trans.gainloss_acc_id and bank_trans.gainloss_acc_id or bank_trans.company_id.income_currency_exchange_account_id
					desc = "Realized Gain"
					if current_currency<>company_currency:
						curr_id = current_currency
					if not gl_account_id:
						raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
				else:
					gl_account_id = bank_trans.gainloss_acc_id and bank_trans.gainloss_acc_id or bank_trans.company_id.expense_currency_exchange_account_id
					desc = "Realized Loss"
					if line.currency_id.id<>company_currency:
						curr_id = line.currency_id.id
					if not gl_account_id:
						raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
				
				# gl_account_id = bank_trans.journal_id.default_credit_account_id.id 

				move_line_gainloss = {
					'name': desc,
					'debit': debit,
					'credit': credit,
					'account_id': gl_account_id.id,
					'move_id': move_id,
					'journal_id': bank_trans.journal_id.id,
					'period_id': period_id,
					'partner_id': bank_trans.partner_id and bank_trans.partner_id.id or False,
					'currency_id': curr_id,
					'amount_currency': 0.0,
					'date': bank_trans.date,
					}
						
				move_line_pool.create(cr, uid, move_line_gainloss)
			
			move_pool.write(cr,uid,[move_id],{'state':'posted'})
			
			date_created = bank_trans.date_created or time.strftime('%Y-%m-%d')
			self.write(cr, uid, [bank_trans.id], {
				'move_id': move_id,
				'state': 'posted',
				'number': name,
				'date_created': date_created,
				'period_id': period_id,
			})
			
			move_pool.post(cr, uid, [move_id], context={})
		return True
	
	def cancel_bank_trans(self, cr, uid, ids, context=None):
		move_pool = self.pool.get('account.move')
		bank_trans=self.browse(cr,uid,ids,context=context)[0]
		move_id=bank_trans.move_id.id
		move_pool.write(cr,uid,[move_id],{'state':'draft'})
		move_pool.unlink(cr,uid,[move_id])
		
		return self.write(cr, uid, ids, {'state':'draft'}, context=context)

class bank_transaction_line(osv.osv):
	_name = "bank.transaction.line"
	_description = "Bank Transaction Line"

	def _get_currency_help_label(self, cr, uid, line_currency_id, bank_rate, bank_currency_id, context=None):
		rml_parser = report_sxw.rml_parse(cr, uid, 'currency_help_label', context=context)
		currency_pool = self.pool.get('res.currency')
		line_currency_str = bank_rate_str = ''

		if line_currency_id:
			line_currency_str = rml_parser.formatLang(1.00, currency_obj=currency_pool.browse(cr, uid, line_currency_id, context=context))
		if bank_currency_id:
			bank_rate_str  = rml_parser.formatLang(bank_rate, currency_obj=currency_pool.browse(cr, uid, bank_currency_id, context=context))
		currency_help_label = _('At the operation date, the exchange rate was\n%s = %s') % (line_currency_str, bank_rate_str)
		return currency_help_label
	
	def _fnct_currency_help_label(self, cr, uid, ids, name, args, context=None):
		res = {}
		for line in self.browse(cr, uid, ids, context=context):
			res[line.id] = self._get_currency_help_label(cr, uid, line.currency_id.id, line.force_rate, line.bank_trans_id.currency_id.id, context=context)
		return res

	_columns = {
		'bank_trans_id':fields.many2one('bank.transaction','Bank Transaction', readonly=True),
		'reference':fields.char('Reference',size=128),
		'name':fields.char('Description',size=528),
		'journal_id':fields.many2one('account.journal',"Journal Destination", help="Journal Cash/Bank Receipt"),
		'account_id': fields.related('journal_id', 'default_debit_account_id', type='many2one', relation='account.account', string='Account', store=True),
		'currency_id':fields.many2one('res.currency','Currency'),
		'source_amount':fields.float('Source Amount',digits_compute=dp.get_precision('Account'),required=True),
		'source_currency_id':fields.related('bank_trans_id','currency_id',type='many2one',relation='res.currency',string='Source Currency',digits_compute=dp.get_precision('Account'),readonly=True),
		'amount':fields.float('Amount',digits_compute=dp.get_precision('Account'),required=True),
		'force_rate':fields.float('Bank Rate', digits=(16,15), help="", required=True),
		'currency_help_label': fields.function(_fnct_currency_help_label, type='text', string="Helping Sentence", help="This sentence helps you to know how to specify the payment rate by giving you the direct effect it has"), 
		# 'expense': fields.boolean('With Expense?', help="Check this if transaction with expense"),
		# 'expense_journal_id':fields.many2one('account.journal','Expense Journal'),
		# 'expense_account_credit':fields.many2one('account.account','Expense on Credit'),
		# 'expense_account_debit':fields.many2one('account.account','Expense on Debit'),
		# 'expense_amount':fields.float('Expense Amount', digits_compute=dp.get_precision('Account')),
		# 'expense_rate':fields.function(_get_expense_rate, method=True, type="float", string='Expense Rate', store=True),
	}
	_defaults = {
		'source_amount' : lambda self,cr,uid,context:context.get('alocated_amount',0.0),
	}

	def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
		result = {
			'value':{},
		}
		journal_pool = self.pool.get('account.journal')
		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		result['value'].update({'currency_id':journal.currency and journal.currency.id or journal.company_id.currency_id.id or False})
		return result

	def onchange_currency_id(self, cr, uid, ids, amount, line_currency_id, bank_currency_id, context=None):
		if context is None:
			context = {}
		currency_obj = self.pool.get('res.currency')
		currency = currency_obj.browse(cr, uid, [line_currency_id,bank_currency_id],context=context)
		date = context.get('date',time.strftime('%Y-%m-%d'))
		print "................context, date", context, date
		rate = currency_obj._get_conversion_rate(cr, uid, currency[1], currency[0], context={'date':date})
		res =  {
				'value': 
						{
						'force_rate': rate,
						'amount' : amount * rate,
						'currency_help_label': self._get_currency_help_label(cr, uid, line_currency_id, rate, bank_currency_id, context=context)
						}
				}
		return res

	def onchange_force_rate(self, cr, uid, ids, amount, line_currency_id, bank_rate, bank_currency_id, context=None):
		if context is None:
			context = {}
		res =  {
				'value': 
						{
						'amount': amount * bank_rate,
						'currency_help_label': self._get_currency_help_label(cr, uid, line_currency_id, bank_rate, bank_currency_id, context=context)
						}
				}
		return res

class account_journal(osv.osv):
	_inherit = "account.journal"
	_description = "Journal"
	_columns = {
		'payment': fields.boolean('Payment', help="Journal Cash/Bank Out Finance"),
		'receipt': fields.boolean('Receipt', help="Journal Cash/Bank In Finance"),
	}

account_journal()

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