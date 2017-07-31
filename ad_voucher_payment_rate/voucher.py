from openerp.osv import fields,osv
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

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

class account_voucher(osv.Model):
	_inherit = "account.voucher"

	def _paid_amount_in_company_currency(self, cr, uid, ids, name, args, context=None):
		if context is None:
			context = {}
		res = {}
		ctx = context.copy()
		for v in self.browse(cr, uid, ids, context=context):
			ctx.update({'date': v.date})
			#make a new call to browse in order to have the right date in the context, to get the right currency rate
			voucher = self.browse(cr, uid, v.id, context=ctx)
			# ctx.update({
			#   'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,
			#   'voucher_special_currency_rate': voucher.currency_id.rate * voucher.payment_rate,})
			res[voucher.id] =  self.pool.get('res.currency').compute(cr, uid, voucher.currency_id.id, voucher.company_id.currency_id.id, voucher.amount, context=ctx)
		return res

	def _get_create_uid(self, cr, uid, ids, name, args, context=None):
		if context is None:
			context = {}
		res = {}
		ctx = context.copy()
		for v in self.browse(cr, uid, ids, context=context):
			cr.execute("select create_uid from account_voucher where id='%s'"%v.id)
			cr_id = cr.fetchone()[0]
			res[v.id] = cr_id
		return res

	_columns = {
		"create_by" : fields.function(_get_create_uid, type='many2one', obj='res.users', string='Create By', store=True),
		"force_multi_currency":fields.boolean("Use Multi Currency",help="Check this box if you want to apply specific currency rate in payment",readonly=True, states={'draft': [('readonly', False)]}),
		'paid_amount_in_company_currency': fields.function(_paid_amount_in_company_currency, string='Paid Amount in Company Currency', type='float', readonly=True),
		#"expected_rate": fields.float('Expected Exchange Rate', digits=(12,6), required=True, readonly=True, states={'draft': [('readonly', False)]},),
		'payment_rate': fields.float('Exchange Rate', digits=(12,20), required=True, readonly=True, states={'draft': [('readonly', False)]},
			help='The specific rate that will be used, in this voucher, between the selected currency (in \'Payment Rate Currency\' field)  and the voucher currency.'),

		# filter columns
		# 'move_line_id' : fields.many2one('account.move.line','Filter Journal Item'),
		'filter_account_id' : fields.many2one('account.account','Filter Account',domain=[('type','in',('payable','receivable'))], readonly=True, states={'draft': [('readonly', False)]}),
		'filter_date_from' : fields.date('From Date', readonly=True, states={'draft': [('readonly', False)]}),
		'filter_date_to' : fields.date('To Date', readonly=True, states={'draft': [('readonly', False)]}),
		'filter_due_date_until' : fields.date('Due Date Less Or Equal Then', readonly=True, states={'draft': [('readonly', False)]}),
		'filter_reference_contain' : fields.char('Reference Contain', help="Use this filter for filtering the receivable or payable that will appear in Payment Information lines\nUse ':' to put more than one reference.", placeholder="BLI-115/;TT431;ADV/201..;", readonly=True, states={'draft': [('readonly', False)]}),
		'filter_move_line_ids': fields.many2many('account.move.line', 'voucher_rel_move_line', 'move_id', 'voucher_id', 'Move Lines', readonly=True, states={'draft': [('readonly', False)]}),
		'alocate_automatically' : fields.boolean('Allocate directly?', readonly=True, states={'draft': [('readonly', False)]}),
	}

	_defaults = {
		"is_multi_currency":False,
		"force_multi_currency":False,
	}

	def onchange_filter(self, cr, uid, ids, currency_id, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, filter_move_line_ids, filter_account_id, filter_date_from, filter_date_to, filter_reference_contain, alocate_automatically, filter_due_date_until, context=None):
		if context is None:
			context = {}
		if not currency_id or  not journal_id:
			return False
		vals = {'value':{} }
		currency_id = currency_id
		vals['value'].update({'currency_id': currency_id, 'payment_rate_currency_id': currency_id})
		#in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
		#without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
		#t0his common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
		if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
			vals['value']['amount'] = 0
			amount = 0
		if filter_move_line_ids[0][2]:
			context.update({'filter_move_line_ids':filter_move_line_ids[0][2]})
		if filter_account_id:
			context.update({'filter_account_id':filter_account_id})
		if filter_reference_contain:
			context.update({'filter_reference_contain':filter_reference_contain})
		if filter_date_to:
			context.update({'filter_date_to':filter_date_to})
		if filter_date_from:
			context.update({'filter_date_from':filter_date_from})
		if alocate_automatically and alocate_automatically==True:
			context.update({'alocate_automatically':True})
		if filter_due_date_until:
			context.update({'filter_due_date_until':filter_due_date_until})

		if partner_id:
			res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
			for key in res.keys():
				vals[key].update(res[key])
		return vals

	def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
		"""
		Returns a dict that contains new values and context

		@param partner_id: latest value from user input for field partner_id
		@param args: other arguments
		@param context: context arguments, like lang, time zone

		@return: Returns a dict which contains new values, and context
		"""
		def _remove_noise_in_o2m():
			"""if the line is partially reconciled, then we must pay attention to display it only once and
				in the good o2m.
				This function returns True if the line is considered as noise and should not be displayed
			"""
			if line.reconcile_partial_id:
				if currency_id == line.currency_id.id:
					if line.amount_residual_currency <= 0:
						return True
				else:
					if line.amount_residual <= 0:
						return True
			return False

		if context is None:
			context = {}
		context_multi_currency = context.copy()
		
		currency_pool = self.pool.get('res.currency')
		move_line_pool = self.pool.get('account.move.line')
		partner_pool = self.pool.get('res.partner')
		journal_pool = self.pool.get('account.journal')
		line_pool = self.pool.get('account.voucher.line')

		#set default values
		default = {
			'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
		}

		#drop existing lines
		line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
		if line_ids:
			line_pool.unlink(cr, uid, line_ids)

		if not partner_id or not journal_id:
			return default

		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		partner = partner_pool.browse(cr, uid, partner_id, context=context)
		currency_id = currency_id or journal.company_id.currency_id.id

		total_credit = 0.0
		total_debit = 0.0
		account_type = None
		if context.get('account_id'):
			account_type = self.pool['account.account'].browse(cr, uid, context['account_id'], context=context).type
		if ttype == 'payment':
			if not account_type:
				account_type = 'payable'
			total_debit = price or 0.0
		else:
			total_credit = price or 0.0
			if not account_type:
				account_type = 'receivable'

		if context.get('st_move_line_id', False):
			c_move_line_ids = []
			if context.get('move_line_ids', []):
				c_move_line_ids = context.get('move_line_ids', [])
				del context['move_line_ids']
			c_move_line_ids.append(context.get('st_move_line_id', False))
			context.update({'move_line_ids':c_move_line_ids})
			
			st_move_line = move_line_pool.browse(cr, uid, context.get('st_move_line_id', False))
			invoice_id = st_move_line.invoice and st_move_line.invoice.id or False
			if invoice_id:
				context.update({'invoice_id':invoice_id})
		if context.get('filter_move_line_ids',[]):
			c_move_line_ids = []
			if context.get('move_line_ids', []):
				c_move_line_ids = context.get('move_line_ids', [])
				del context['move_line_ids']
			c_move_line_ids+=context.get('filter_move_line_ids', [])
			context.update({'move_line_ids':c_move_line_ids})

		if not context.get('move_line_ids', False):
			domain_def = []
			if context.get('filter_reference_contain',False):
				fref_list = [x.strip() for x in context.get('filter_reference_contain',False).split(";") if x.strip()]
				n_fref_list = len(fref_list)
				if n_fref_list>1:
					domain_def.append("&")
					for findx in range(0,n_fref_list):
						if findx<(n_fref_list-1):
							domain_def.append("|")
						domain_def.append(('ref','like',fref_list[findx]))
				else:
					domain_def.append(('ref','like',fref_list[0].strip()))
			
			if context.get('filter_date_from',False):
				domain_def.append(('date','>=',context.get('filter_date_from',False)))
			if context.get('filter_date_to',False):
				domain_def.append(('date','<=',context.get('filter_date_to',False)))
			if context.get('filter_account_id',False):
				domain_def.append(('account_id','like',context.get('filter_account_id',False)))
			if context.get('filter_due_date_until',False):
				domain_def.append("|")
				domain_def.append(('date_maturity','<=',context.get('filter_due_date_until',False)))
				domain_def.append(('date_maturity','=',False))
			# default domain from OpenERP account_vouher basic basic
			domain_def.append(('state','=','valid'))
			domain_def.append(('account_id.type', '=', account_type))
			domain_def.append(('reconcile_id', '=', False))
			domain_def.append(('partner_id', '=', partner_id))
			ids = move_line_pool.search(cr, uid, domain_def, context=context)
		else:
			ids = context['move_line_ids']
		invoice_id = context.get('invoice_id', False)
		company_currency = journal.company_id.currency_id.id
		move_lines_found = []

		#order the lines by most old first
		ids.reverse()
		account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

		#compute the total debit/credit and look for a matching open amount or invoice
		for line in account_move_lines:
			if _remove_noise_in_o2m():
				continue

			if invoice_id:
				if line.invoice.id == invoice_id:
					#if the invoice linked to the voucher line is equal to the invoice_id in context
					#then we assign the amount on that line, whatever the other voucher lines
					move_lines_found.append(line.id)
			elif currency_id == company_currency:
				#otherwise treatments is the same but with other field names
				if line.amount_residual == price:
					#if the amount residual is equal the amount voucher, we assign it to that voucher
					#line, whatever the other voucher lines
					move_lines_found.append(line.id)
					break
				#otherwise we will split the voucher amount on each line (by most old first)
				total_credit += line.credit or 0.0
				total_debit += line.debit or 0.0
			elif currency_id == line.currency_id.id:
				if line.amount_residual_currency == price:
					move_lines_found.append(line.id)
					break
				total_credit += line.credit and line.amount_currency or 0.0
				total_debit += line.debit and line.amount_currency or 0.0

		remaining_amount = price
		#voucher line creation
		for line in account_move_lines:
			if _remove_noise_in_o2m():
				continue

			if line.currency_id and currency_id == line.currency_id.id:
				amount_original = abs(line.amount_currency)
				amount_unreconciled = abs(line.amount_residual_currency)
			elif line.currency_id and currency_id != line.currency_id.id and currency_id != company_currency:
				amount_original = currency_pool.compute(cr, uid, line.currency_id.id, currency_id, abs(line.amount_currency), context=context_multi_currency)
				amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id, currency_id, abs(line.amount_residual_currency), context=context_multi_currency)
			else:
				#always use the amount booked in the company currency as the basis of the conversion into the voucher currency
				amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
				amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
			line_currency_id = line.currency_id and line.currency_id.id or company_currency
			rs = {
				'name':line.move_id.name,
				'type': line.credit and 'dr' or 'cr',
				'move_line_id':line.id,
				'account_id':line.account_id.id,
				'amount_original': amount_original,
				'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
				'date_original':line.date,
				'date_due':line.date_maturity,
				'amount_unreconciled': amount_unreconciled,
				'currency_id': line_currency_id,
			}
			#we set the account_analytic_id here
			rs.update({'account_analytic_id':line.analytic_account_id and line.analytic_account_id.id or False})

			remaining_amount -= rs['amount']
			#in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
			#on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
			if not move_lines_found:
				if currency_id == line_currency_id:
					if line.credit:
						amount = min(amount_unreconciled, abs(total_debit))
						rs['amount'] = amount
						total_debit -= amount
					else:
						amount = min(amount_unreconciled, abs(total_credit))
						rs['amount'] = amount
						total_credit -= amount

			# if user dont want the amount alocate automatically
			if not context.get('line_type',False) and context.get('alocate_automatically',False)==False:
				rs['amount'] = 0.0

			if rs['amount_unreconciled'] == rs['amount']:
				rs['reconcile'] = True

			if rs['type'] == 'cr':
				default['value']['line_cr_ids'].append(rs)
			else:
				default['value']['line_dr_ids'].append(rs)

			if len(default['value']['line_cr_ids']) > 0:
				default['value']['pre_line'] = 1
			elif len(default['value']['line_dr_ids']) > 0:
				default['value']['pre_line'] = 1
			default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
		if context.get('force_multi_currency',False):
			default['value']['is_multi_currency']=True

		return default

	def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
		context = context or {}
		if not line_dr_ids and not line_cr_ids:
			return {'value':{'writeoff_amount': 0.0}}
		line_osv = self.pool.get("account.voucher.line")
		line_dr_ids = resolve_o2m_operations(cr, uid, line_osv, line_dr_ids, ['amount'], context)
		line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, line_cr_ids, ['amount'], context)
		#compute the field is_multi_currency that is used to hide/display options linked to secondary currency on the voucher
		is_multi_currency = False
		#loop on the voucher lines to see if one of these has a secondary currency. If yes, we need to see the options
		voucher_lines = line_dr_ids+line_cr_ids
		move_line_ids = [v.get('move_line_id',False) for v in voucher_lines if v.get('move_line_id',False)]
		move_lines = self.pool.get('account.move.line').browse(cr, uid, move_line_ids, context=context)
		for line_id in move_lines:
			if line_id  and line_id.currency_id:
				is_multi_currency = True
				break
		if context.get('force_multi_currency',False)!=False:
			is_multi_currency=True
		return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount, type), 'is_multi_currency': is_multi_currency}}


	def onchange_force_multi_currency(self,cr,uid,ids,partner_id, journal_id, amount, currency_id, ttype, date,force_multi_currency,context=None):
		if not context:context={}
		context.update({'force_multi_currency':force_multi_currency})
		onchange=self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
		return {'context':{'force_multi_currency':force_multi_currency},'value':onchange.get('value',{})}

	# def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
	# 	context = context or {}
	# 	print "context===========",context
	# 	if not line_dr_ids and not line_cr_ids:
	# 		return {'value':{'writeoff_amount': 0.0}}
	# 	line_osv = self.pool.get("account.voucher.line")
	# 	line_dr_ids = resolve_o2m_operations(cr, uid, line_osv, line_dr_ids, ['amount'], context)
	# 	line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, line_cr_ids, ['amount'], context)
	# 	#compute the field is_multi_currency that is used to hide/display options linked to secondary currency on the voucher
	# 	is_multi_currency = False
	# 	#loop on the voucher lines to see if one of these has a secondary currency. If yes, we need to see the options
	# 	for voucher_line in line_dr_ids+line_cr_ids:
	# 		line_id = voucher_line.get('id') and self.pool.get('account.voucher.line').browse(cr, uid, voucher_line['id'], context=context).move_line_id.id or voucher_line.get('move_line_id')
	# 		#print "thisisisisis",voucher_line.get('force_multi_currency')
	# 		if line_id and self.pool.get('account.move.line').browse(cr, uid, line_id, context=context).currency_id:
	# 			is_multi_currency = True
	# 			break
	# 	# if not is_multi_currency and context.get('force_multi_currency',False):
	# 	# 	#print "=============",is_multi_currency,"=============", context.get('force_multi_currency',False)
	# 	# 	is_multi_currency=True
	# 	return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount, type), 'is_multi_currency': is_multi_currency}}

class account_voucher_line(osv.Model):
	def _get_original_amount(self, cr, uid, ids, name, args, context=None):
		if context is None:
			context = {}
		currency_pool = self.pool.get('res.currency')
		move_line_pool = self.pool.get('account.move.line')
		result={}
		for line in self.browse(cr, uid, ids, context=context):
			result.update({
				line.id:{
					'amount_currency_original':0.0,
					'currency_original':False
				}
			})
			if line.move_line_id:
				sign = line.type=='dr' and -1 or 1
				# if line.move_line_id.currency_id:
				result[line.id]['amount_currency_original'] = sign*(line.move_line_id.currency_id and line.move_line_id.amount_currency or (line.move_line_id.debit-line.move_line_id.credit))
				result[line.id]['currency_original'] = line.move_line_id.currency_id and line.move_line_id.currency_id.id or line.move_line_id.company_id.currency_id.id
		return result

	def _compute_balance(self, cr, uid, ids, name, args, context=None):
		currency_pool = self.pool.get('res.currency')
		rs_data = {}
		for line in self.browse(cr, uid, ids, context=context):
			ctx = context.copy()
			ctx.update({'date': line.voucher_id.date})
			voucher_rate = self.pool.get('res.currency').read(cr, uid, line.voucher_id.currency_id.id, ['rate'], context=ctx)['rate']
			ctx.update({
				'voucher_special_currency': line.voucher_id.payment_rate_currency_id and line.voucher_id.payment_rate_currency_id.id or False,
				'voucher_special_currency_rate': line.voucher_id.payment_rate * voucher_rate})
			res = {}
			company_currency = line.voucher_id.journal_id.company_id.currency_id.id
			voucher_currency = line.voucher_id.currency_id and line.voucher_id.currency_id.id or company_currency
			move_line = line.move_line_id or False

			if not move_line:
				res['amount_original'] = 0.0
				res['amount_unreconciled'] = 0.0
			elif move_line.currency_id and voucher_currency==move_line.currency_id.id:
				res['amount_original'] = abs(move_line.amount_currency)
				res['amount_unreconciled'] = abs(move_line.amount_residual_currency)
			elif move_line.currency_id and voucher_currency!=move_line.currency_id.id and voucher_currency!=company_currency:
				res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, abs(move_line.amount_currency), context=ctx)
				res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
			else:
				#always use the amount booked in the company currency as the basis of the conversion into the voucher currency
				res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
				res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)

			rs_data[line.id] = res
		return rs_data

	_inherit = "account.voucher.line"

	_columns = {
		"force_multi_currency":fields.boolean("Use Multi Currency",help="Check this box if you want to apply specific currency rate in payment",digits_compute=dp.get_precision('Account')),
		'amount_currency_original' : fields.function(_get_original_amount, multi='voucher_line', type='float', string='Original Amount Currency',digits_compute=dp.get_precision('Account')),
		'currency_original' : fields.function(_get_original_amount, multi='voucher_line', type='many2one', obj='res.currency', string='Original Currency'),
		'amount_original': fields.function(_compute_balance, multi='dc', type='float', string='Original Amount', store=True, digits_compute=dp.get_precision('Account')),
		'amount_unreconciled': fields.function(_compute_balance, multi='dc', type='float', string='Open Balance', store=True, digits_compute=dp.get_precision('Account')),
	}

	_defaults = {
		"force_multi_currency":lambda self,cr,uid,context: context.get('force_multi_currency',False),
	}
