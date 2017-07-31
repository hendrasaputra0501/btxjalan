from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
import netsvc
from datetime import datetime
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class advance_payment(osv.osv):
	def _get_currency_help_label(self, cr, uid, currency_id, rate, advance_rate_currency_id, context=None):
		rml_parser = report_sxw.rml_parse(cr, uid, 'currency_help_label', context=context)
		currency_pool = self.pool.get('res.currency')
		from_rate_str = to_rate_str = ''

		if currency_id:
			from_rate_str = rml_parser.formatLang(1.00, currency_obj=currency_pool.browse(cr, uid, currency_id, context=context))
		if advance_rate_currency_id:
			to_rate_str  = rml_parser.formatLang(rate, currency_obj=currency_pool.browse(cr, uid, advance_rate_currency_id, context=context), digits=16)
		currency_help_label = _('At the operation date, the exchange rate was\n%s = %s') % (from_rate_str, to_rate_str)
		return currency_help_label

	def _fnct_currency_help_label(self, cr, uid, ids, name, args, context=None):
		res = {}
		for adv in self.browse(cr, uid, ids, context=context):
			res[adv.id] = self._get_currency_help_label(cr, uid, adv.currency_id.id, adv.advance_rate, adv.advance_rate_currency_id.id, context=context)
		return res

	def _compute_amount(self, cr, uid, ids, name, args, context=None):
		total=0.0
		res={}
		advance=self.browse(cr,uid,ids, context=context)[0]
		for line in advance.line_ids:
			total+=line.amount
		res[advance.id]=total
		return res

	_name = "account.advance.payment"
	_columns = {
		'name' : fields.char('Payment Ref',size=50,required=True, readonly=True),
		'partner_id' : fields.many2one('res.partner','Customer',required=True,readonly=True, states={'draft':[('readonly',False)]}),
		'notify_id' : fields.many2one('res.partner','Notify',readonly=True, states={'draft':[('readonly',False)]}),
		'notify' : fields.char('Notify',size=200,  readonly=True, states={'draft':[('readonly',False)]}),
		'memo' : fields.char('Memo',size=200,  readonly=True, states={'draft':[('readonly',False)]}),
		'journal_id' : fields.many2one('account.journal','Journal',required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'account_id' : fields.many2one('account.account','Account Advance',required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'analytic_account_id' : fields.many2one('account.analytic.account','Account Analytic',required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'currency_id' : fields.many2one('res.currency','Currency',required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'date_payment' : fields.date('Date of Payment',readonly=True, states={'draft':[('readonly',False)]}),
		'effective_date' : fields.date('Effective Date',readonly=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
		'line_ids' : fields.one2many('account.advance.payment.line','advance_id','Payment Line',readonly=True, states={'draft':[('readonly',False)]}),
		'move_id':fields.many2one('account.move', 'Account Entry'),
		'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
		'company_id' : fields.many2one('res.company','Company'),
		'total_amount' : fields.function(_compute_amount, type='float', string='Amount Total', store=True, digits_compute=dp.get_precision('total_amount')),
		'sale_type' : fields.selection([
			('export','Export'),
			('local','Local')], 'Sale Type'),
		'type' : fields.selection([
			('in','Customer'),
			('out','Supplier')], 'Type'),
		'state' : fields.selection([
			('draft','Draft'),
			('posted','Posted'),
			('cancel','Cancelled')], 'State'),
		'advance_rate_currency_id' : fields.many2one('res.currency','Exchange Rate Currency', readonly=True, states={'draft':[('readonly',False)]},),
		'advance_rate' : fields.float('Exchange Rate', digits=(2,16), readonly=True, states={'draft':[('readonly',False)]}),
		'use_special_rate' : fields.boolean('Use Special Rate', readonly=True, states={'draft':[('readonly',False)]}),
		'currency_help_label': fields.function(_fnct_currency_help_label, type='text', string="Helping Sentence", help="This sentence helps you to know how to specify the payment rate by giving you the direct effect it has"), 
	}
	_defaults = {
		'state' : 'draft',
		'name' : '/',
		# 'use_special_rate' : lambda *u : False,
		'advance_rate_currency_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
		'type' :lambda self,cr,uid,context:context.get('type','in'),
		'date_payment' : lambda *a:time.strftime('%Y-%m-%d'), 
		'company_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id or False,
		'currency_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
	}

	_order = "id desc"

	def create(self,cr,uid,vals,context=None):
		if vals.get('name','/')=='/':
			c = {}
			if vals.get('effective_date',False):
				c = {'date':datetime.strptime(vals['effective_date'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			elif vals.get('date_payment',False):
				c = {'date':datetime.strptime(vals['date_payment'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			
			if context.get('type',False)=='in':
				vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.advance.payment.in', context=c) or '/'
			else:
				vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.advance.payment.out', context=c) or '/'
		return super(advance_payment,self).create(cr,uid,vals,context=context)

	def onchange_set_account(self,cr,uid,ids,journal_id,partner_id,type_payment,context=None):
		if context is None:
			context = {}
		account_id = False

		if journal_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
			if type_payment == 'in':
				account_id = journal.default_credit_account_id and journal.default_credit_account_id.id or False
			else:
				account_id = journal.default_debit_account_id and journal.default_debit_account_id.id or False

		if partner_id:
			partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
			if type_payment == 'in':
				account_id = partner.advance_in_account_id and partner.advance_in_account_id.id or False
			else:
				account_id = partner.advance_out_account_id and partner.advance_out_account_id.id or False

		return {'value':{'account_id':account_id}}

	def onchange_notify(self,cr,uid,ids,partner_id,context=None):
		if context is None:
			context = {}
		notify = ''
		if partner_id:
			partner_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
			notify = partner_id.name or ''

		return {'value':{'notify':notify, 'memo':notify}}

	def onchange_currency(self, cr, uid, ids, currency_id, advance_rate_currency_id, date, context=None):
		if context is None:
			context = {}

		res = {'advance_rate':0.0, 'currency_help_label':''}
		currency_obj = self.pool.get('res.currency')
		if currency_id and advance_rate_currency_id: 
			curr = currency_obj.browse(cr, uid, [currency_id,advance_rate_currency_id])
			context.update({'date':date})
			rate = currency_obj._get_conversion_rate(cr, uid, curr[0], curr[1], context=context)
			res['advance_rate'] = rate
			res['currency_help_label']= self._get_currency_help_label(cr, uid, currency_id, rate, advance_rate_currency_id, context=context)

		return {'value':res}

	def onchange_advance_rate(self, cr, uid, ids, currency_id, rate, advance_rate_currency_id, context=None):
		if context is None:
			context = {}

		res = {'currency_help_label':''}
		currency_obj = self.pool.get('res.currency')
		if currency_id and advance_rate_currency_id: 
			curr = currency_obj.browse(cr, uid, [currency_id,advance_rate_currency_id])
			res['currency_help_label']= self._get_currency_help_label(cr, uid, currency_id, rate, advance_rate_currency_id, context=context)

		return {'value':res}

	def _get_company_currency(self, cr, uid, advance_id, context=None):
		return self.browse(cr,uid,advance_id,context).journal_id.company_id.currency_id.id

	def _get_current_currency(self, cr, uid, advance_id, context=None):
		advance = self.browse(cr,uid,advance_id,context)
		return advance.currency_id and advance.currency_id.id or advance.journal_id.currency.id or self._get_company_currency(cr,uid,advance.id,context)

	def account_move_get(self, cr, uid, advance_id, context=None):
		if not context:
			context={}
		seq_obj = self.pool.get('ir.sequence')
		advance = self.pool.get('account.advance.payment').browse(cr,uid,advance_id,context)
		effective_date = advance.effective_date!='False' and advance.effective_date or (advance.date_payment!='False' and advance.date_payment) or time.strftime('%Y-%m-%d')
		
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)
		ref = ''
		for line in advance.line_ids:
			ref += line.name or ''
		move = {
			'name': advance.name,
			'ref' : ref and ref or advance.name,
			'journal_id': advance.journal_id.id,
			'date': effective_date,
			'period_id': period and period[0] or False,
		}

		return move

	def first_move_line_get(self, cr, uid, advance_id, move_id, company_currency, current_currency, paid_amount, context=None):
		advance = self.pool.get('account.advance.payment').browse(cr,uid,advance_id,context)
		
		debit = credit = 0.0
		if advance.type=='in':
			credit = paid_amount
		elif advance.type=='out':
			debit = paid_amount
		if debit < 0: credit = -debit; debit = 0.0
		if credit < 0: debit = -credit; credit = 0.0
		sign = debit - credit < 0 and -1 or 1
		effective_date = advance.effective_date!='False' and advance.effective_date or (advance.date_payment!='False' and advance.date_payment) or time.strftime('%Y-%m-%d')

		period=self.pool.get('account.period').find(cr,uid,dt=effective_date)
		account_id = advance.account_id and advance.account_id.id or False
		# if advance.type=='in':
		# 	account_id=advance.partner_id.advance_in_account_id.id or False
		# 	if not account_id:
		# 		account_id = advance.journal_id.default_credit_account_id and advance.journal_id.default_credit_account_id.id
		# else:
		# 	account_id=advance.partner_id.advance_out_account_id.id or False,
		# 	if not account_id:
		# 		account_id = advance.journal_id.default_debit_account_id and advance.journal_id.default_debit_account_id.id
		if not account_id:
			raise osv.except_osv(_('Configuration Error !'),
				_('Please set the advance account of selected partner or selected Journal !'))

		move_line = {
			'name': advance.name or '/',
			'debit': debit,
			'credit': credit,
			'account_id': account_id or False,
			'analytic_account_id' : advance.analytic_account_id and advance.analytic_account_id.id or False,
			'move_id': move_id,
			'journal_id': advance.journal_id.id,
			'period_id': period and period[0] or False,
			'partner_id': advance.partner_id.id,
			'currency_id': company_currency <> current_currency and  current_currency or False,
			'amount_currency': company_currency <> current_currency and sign * advance.total_amount or 0.0,
			'date': effective_date,
		}
		return move_line

	def advance_move_line_create(self, cr, uid, advance_id, move_id, company_currency, current_currency, context=None):
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		currency_obj = self.pool.get('res.currency')
		rec_lst_ids = []

		advance = self.pool.get('account.advance.payment').browse(cr, uid, advance_id, context=context)
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		effective_date = advance.effective_date!='False' and advance.effective_date or (advance.date_payment!='False' and advance.date_payment) or time.strftime('%Y-%m-%d')
		period =self.pool.get('account.period').find(cr,uid,dt=effective_date)

		for line in advance.line_ids:
			debit = credit = 0.0
			if advance.use_special_rate:
				amount = self.pool.get('res.currency').compute(cr, uid, advance.advance_rate_currency_id and advance.advance_rate_currency_id.id or current_currency, company_currency, line.amount*advance.advance_rate, context=context)
			else:
				amount = self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, line.amount, context=context)
			if advance.type=='out':
				credit=amount
			else:
				debit=amount

			move_line = {
				'journal_id': advance.journal_id.id,
				'period_id': period and period[0] or False,
				'name': line.memo_line or advance.name or '/',
				'other_ref' : line.other_ref or '',
				'account_id': line.account_id and line.account_id.id or False ,
				'move_id': move_id,
				'partner_id': advance.partner_id.id,
				'currency_id': company_currency <> current_currency and  current_currency or False,
				# 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'credit': credit,
				'debit': debit,
				'date': effective_date,
			}
			sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
			move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0 
			advance_line = move_line_obj.create(cr, uid, move_line)
			# move_line_obj.write(cr, uid, advance_line, {'ref' : line.name or '/',})
			
		return True

	def action_validate(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for advance in self.browse(cr, uid, ids, context=context):
			if advance.move_id:
				continue

			context.update({'date':advance.effective_date or advance.date_payment})
			company_currency = self._get_company_currency(cr, uid, advance.id, context)
			current_currency = self._get_current_currency(cr, uid, advance.id, context)

			move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, advance.id, context=context), context=context)

			name = move_pool.browse(cr, uid, move_id, context=context).name

			# amount=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, advance.total_amount, context=context)
			amount=0.0
			for line in advance.line_ids:
				if advance.use_special_rate:
					amount+=self.pool.get('res.currency').compute(cr, uid, advance.advance_rate_currency_id and advance.advance_rate_currency_id.id or current_currency, company_currency, line.amount*advance.advance_rate, context=context)
				else:
					amount+=self.pool.get('res.currency').compute(cr, uid, current_currency, company_currency, line.amount, context=context)
			move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,advance.id, move_id, company_currency, current_currency, amount, context=context), context=context)
			
			move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
			
			self.advance_move_line_create(cr, uid, advance.id, move_id, company_currency, current_currency, context)

			self.write(cr,uid,advance.id ,{'state':'posted','move_id':move_id})
			if advance.move_id:
				move_pool.post(cr, uid, [move_id], context={})
		return True

	def action_cancel(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for advance in self.browse(cr, uid, ids, context=context):
			if not advance.move_id:
				continue

			for line in advance.move_ids:
				if line.reconcile_id:
					raise osv.except_osv(_('Cancel Error!'),
						_('Please unreconcile its receipt/payment first !'))
			

			move_pool.button_cancel(cr, uid, [advance.move_id.id])
			move_pool.unlink(cr, uid, [advance.move_id.id])

			res = {
				'state':'cancel',
				'move_id':False,
			}
			self.write(cr, uid, ids, res)
		return True

	def action_set_draft(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		for advance in self.browse(cr, uid, ids, context=context):
			res = {
				'state':'draft',
			}
			self.write(cr, uid, ids, res)
		return True

	def copy(self, cr, uid, id, default=None, context=None):
		if default is None:
			default = {}
		default.update({
			'state': 'draft',
			'name': '/',
			'move_id': False,
		})
		if 'date_payment' not in default:
			default['date_payment'] = time.strftime('%Y-%m-%d')
		return super(advance_payment, self).copy(cr, uid, id, default, context)

advance_payment()

class advance_payment_line(osv.osv):
	_name = "account.advance.payment.line"
	_columns = {
		'name' : fields.char('Reference',size=50,required=False),
		'memo_line' : fields.char('Memo',size=200),
		'other_ref' : fields.char('Other Ref',size=200),
		'advance_id' : fields.many2one('account.advance.payment','Advance'),
		'account_id' : fields.many2one('account.account',"Bank Account",required=True),
		'amount' : fields.float("Amount",required=True, digits_compute= dp.get_precision('amount')),
		# 'currency_id' : fields.many2one('res.currency','Currency'), 
		# 'amount_currency' : fields.float("Amount", digits_compute= dp.get_precision('amount_currency')),
	}

	_defaults = {
		'amount' : False,
		'memo_line' : '/',
	}
advance_payment_line()

