from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):
	_inherit = "account.invoice"

	def _get_invoice_from_line(self, cr, uid, ids, context=None):
		move = {}
		for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
			if line.reconcile_partial_id:
				for line2 in line.reconcile_partial_id.line_partial_ids:
					move[line2.move_id.id] = True
			if line.reconcile_id:
				for line2 in line.reconcile_id.line_id:
					move[line2.move_id.id] = True
		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
		return invoice_ids

	def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
		move = {}
		for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
			for line in r.line_partial_ids:
				move[line.move_id.id] = True
			for line in r.line_id:
				move[line.move_id.id] = True

		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
		return invoice_ids

	def _get_date_payment_invoice(self, cr, uid, ids, name, args, context=None):
		res = {}
		for invoice in self.browse(cr, uid, ids, context=context):
			res[invoice.id] = False
			paid = True
			if invoice.move_id:
				for aml in invoice.move_id.line_id:
					if aml.account_id.type in ('receivable','payable'):
						if aml.reconcile_id:
							paid = paid and True
						else:
							paid = paid and False
			if not paid:
				continue
			if invoice.payment_ids:
				for payment in invoice.payment_ids:
					if not res[invoice.id] or res[invoice.id]<payment.date:
						res[invoice.id] = payment.date
		return res

	def _get_amount_peb_fob(self, cr, uid, ids, name, args, context=None):
		res = {}
		for invoice in self.browse(cr, uid, ids, context=context):
			res[invoice.id] = invoice.amount_total - invoice.peb_freight - invoice.peb_insurance
		return res

	def _check_peb_number(self, cr, uid, ids, context=None):
		""" Checks if peb_number has not created yet or not.
		@return: True or False
		"""

		for inv in self.browse(cr, uid, ids, context=context):
			if inv.peb_number:
				year = datetime.strptime(inv.date_invoice,'%Y-%m-%d').strftime('%Y')
				query = "SELECT id FROM account_invoice WHERE peb_number='"+inv.peb_number+"' and extract(year from date_invoice)='"+year+"';"
				cr.execute(query)
				result = cr. dictfetchall()
				res = [x['id'] for x in result if x['id']!=inv.id]
				if res:
					return False
		return True

	_columns = {
		'default_expense_account_id': fields.many2one('account.account', 'Default Expense Account' , readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}, ),
		'default_tax_ids': fields.many2many('account.tax', 'account_invoice_tax_rel', 'account_invoice_id', 'tax_id', 'Default Taxes', domain=[('parent_id','=',False)], readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'account_id': fields.many2one('account.account', 'Account', required=True, readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}, help="The partner account used for this invoice."),
		'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'date_effective' : fields.date('Effective Date', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		# 'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=False),
		'state': fields.selection([
			('draft','Draft'),
			('proforma','Pro-forma'),
			('proforma2','Invoice Released'),
			('open','AR/AP Outstanding'),
			('paid','Paid'),
			('cancel','Cancelled'),
			],'Status', select=True, readonly=True, track_visibility='onchange',
			help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
			\n* The \'Confirm By MRKT\' when invoice already confirm by Marketing Dept,and then an invoice number is generated. \
			\n* The \'Open\' status is used when user create invoice.Its in open status till user does not pay invoice. \
			\n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
			\n* The \'Cancelled\' status is used when user cancel invoice.'),
		'bl_date' : fields.date('BL Date', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'bl_number' : fields.char('BL Number',size=200),
		'bl_received_date' : fields.date('BL Received Date'),
		'co_date' : fields.date('Certificate of Origin Date'),
		'co_number' : fields.char('Certificate of Origin Number',size=200),
		'co_received_date' : fields.date('Certificate of Origin Received Date'),
		'peb_date' : fields.date('PEB Date'),
		'peb_number' : fields.char('PEB Number',size=200),
		'peb_insurance' : fields.float('Insurance'),
		'peb_freight' : fields.float('Freight'),
		'peb_fob' : fields.function(_get_amount_peb_fob,type='float',digits_compute= dp.get_precision('Product Unit of Measure'),string='FOB Amount'),
		'pe_number' : fields.char('PE Number',size=200),
		'vessel_name' : fields.char('Vessel Name',size=400),
		'bank_submission' : fields.many2one('res.bank', 'Bank Submission',help=''),
		'bank_submission_date' : fields.date('Bank Submission Date'),
		# 'bank_negotiation_no' : fields.char('Bank Negotitation No.',size=200),
		# 'bank_negotiation_date' : fields.date('Bank Negotitation Date'),
		'creation_date' : fields.date('Entry Date', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'payment_date' : fields.function(_get_date_payment_invoice,type='date',string='Payment Date',
			store={
				'account.invoice' : (lambda self, cr,uid,ids,c: ids, ['payment_ids'], 10),
				'account.move.line': (_get_invoice_from_line, None, 50),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
			}),
		'due_date_from_bl_date' : fields.related('payment_term','due_date_from_bl_date',type='boolean',string='Due Date From BL Date'),
		

		'shipper' : fields.many2one('res.partner','Shipper'),
		's_address_text' : fields.text('Shipper Address Details'),
		'show_shipper_address' : fields.boolean('Use Customs Address Desc?'),

		'address_text' : fields.text('Buyer Address Details'),
		'c_address_text' : fields.text('Consignee Address Details'),
		'n_address_text' : fields.text('Notify Address Details'),
		
		'a_address_text' : fields.text('Applicant Address Details'),
		'buyer' : fields.many2one('res.partner','Buyer',domain=[('customer', '=', True)]),
		'show_buyer_address' : fields.boolean('Use Customs Address Desc?'),
		
		'consignee' : fields.many2one('res.partner','Consignee',domain=[('customer', '=', True)]),
		'show_consignee_address' : fields.boolean('Use Customs Address Desc?'),
		'notify' : fields.many2one('res.partner','Notify',domain=[('customer', '=', True)]),
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'applicant' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)]),
		'show_applicant_address' : fields.boolean('Use Customs Address Desc?'),
		'label_print' : fields.text('Label Print'),
		"model_id":fields.many2one('ir.model','Model'),
		'additional_remarks' : fields.text('Additional Remarks'),
		'print_inv_grouping':fields.text("Invoice Line Group by"),
		'courier_number':fields.char('Courier No',size=200),
	}

	_defaults = {
		'model_id': lambda self,cr,uid,context:self.pool.get('ir.model').search(cr,uid,[('model','=',self._name)])[0],
		'label_print':'{}',
		'creation_date':time.strftime('%Y-%m-%d'),
	}

	_constraints = [
		(_check_peb_number,
			'PEB Number must be unique. Please check your PEB Number in existing document.',
			['peb_number'])]

	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoices = self.read(cr, uid, ids, ['state','internal_number','number'], context=context)
		unlink_ids = []

		for t in invoices:
			if t['state'] not in ('draft', 'cancel'):
				raise openerp.exceptions.Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
			elif t['internal_number'] and t['number']:
				raise openerp.exceptions.Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
			else:
				unlink_ids.append(t['id'])

		osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
		return True

	def onchange_peb_number(self, cr, uid, ids, peb_number):
		if peb_number:
			if len(peb_number) > 6:
				return {'value':{'peb_number':False},'warning':{'title':'Wrong PEB Number','message':'You are inputing '+str(len(peb_number))+' digits of PEB Number, while PEB Number should be only 6 digits.'}}
			check = True
			for x in peb_number:
				try:
					tes = isinstance(int(x),int)
				except:
					check = False
			if check:
				return {'value':{'peb_number':peb_number}}
			else:
				return {'value':{'peb_number':False},'warning':{'title':'Wrong PEB Number','message':'Dont input character format. Please input integer/number format on PEB Number'}}


	def button_set_expense_account(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ctx = context.copy()
		
		inv = self.browse(cr, uid, ids, context=ctx)[0]
		if not inv.default_expense_account_id:
			raise osv.except_osv(_('Update Error!'), _('Please define Default Expense Account on this invoice if you want to use this method'))

		account_id = inv.default_expense_account_id.id
		for line in inv.invoice_line:
			self.pool.get('account.invoice.line').write(cr, uid, line.id, {'account_id':account_id}, context=ctx)

		return True

	def button_set_taxes_on_line(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ctx = context.copy()
		
		inv = self.browse(cr, uid, ids, context=ctx)[0]
		if not inv.default_tax_ids:
			raise osv.except_osv(_('Update Error!'), _('Please define Default Expense Account on this invoice if you want to use this method'))
		
		tax_ids = [x.id for x in inv.default_tax_ids]
		for line in inv.invoice_line:
			self.pool.get('account.invoice.line').write(cr, uid, line.id, {'invoice_line_tax_id':[(6,0,tax_ids)]}, context=ctx)

		self.button_reset_taxes(cr, uid, [inv.id] , context)

		return True

	def action_internal_number(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		faktur_pool = self.pool.get('nomor.faktur.pajak')

		for obj_inv in self.browse(cr, uid, ids, context=context):
			# if obj_inv.nomor_faktur_id and obj_inv.nomor_faktur_id.status=='1':
			# 	raise osv.except_osv(_('Faktur Pajak Invalid!'), _('This Faktur Pajak number is already used on another invoice'))

			if not obj_inv.internal_number or obj_inv.internal_number=='':
				internal_number = ''
				company_id = obj_inv.company_id
				company_code = ''
				sale_type = ''
				goods_type = ''
				if company_id:
					company_code=company_id.prefix_sequence_code
				
				if obj_inv.sale_ids:
					sale=obj_inv.sale_ids[0]
					goods_type = sale.goods_type
					if goods_type not in ('finish','finish_others','raw','asset','stores','packing','service'):
						goods_type = 'others'
					date = datetime.strptime(obj_inv.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
					internal_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.'+sale.sale_type+'.'+goods_type, context={'date':date}) or '/')
					
				self.write(cr, uid, ids, {'internal_number': internal_number})
			# if obj_inv.nomor_faktur_id:
			# 	faktur_pool.write(cr, uid, obj_inv.nomor_faktur_id.id, {'status':'1'})
		return True	

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		types = {
				'out_invoice': _('Invoice'),
				'in_invoice': _('Supplier Invoice'),
				'out_refund': _('Refund'),
				'in_refund': _('Supplier Refund'),
				}
		return [(r['id'], '%s' % (r['internal_number'] or types[r['type']])) for r in self.read(cr, uid, ids, ['type', 'number', 'internal_number', 'name'], context, load='_classic_write')]

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if context is None:
			context = {}
		ids = []
		if name:
			ids = self.search(cr, user, [('internal_number','=',name)] + args, limit=limit, context=context)
		if not ids:
			ids = self.search(cr, user, [('internal_number',operator,name)] + args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

	# def action_cancel(self, cr, uid, ids, context=None):
	# 	if context is None:
	# 		context={}
	# 	faktur_pool = self.pool.get('nomor.faktur.pajak')
	# 	res = super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
	# 	invoices = self.read(cr, uid, ids, ['nomor_faktur_id'])
	# 	fp_ids=[]
	# 	for i in invoices:
	# 		if i['nomor_faktur_id']:
	# 			fp_ids.append(i['nomor_faktur_id'][0])

	# 	if fp_ids:
	# 		faktur_pool.write(cr, uid, fp_ids, {'status':'0'})
		
	# 	return res

	def onchange_date(self, cr, uid, ids, date_invoice, date_effective, context=None):
		period_obj = self.pool.get('account.period')
		res = {}
		date = date_effective!=False and date_effective or date_invoice or False
		if date:
			period_ids = period_obj.find(cr, uid, date, context=context)
			if period_ids:
				period_id = period_ids and period_ids[0] or False
				res.update({'period_id':period_id})
		return {'value':res}

	def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice):
		res = {}
		ctx={}
		if isinstance(ids, (int, long)):
			ids = [ids]
		if not date_invoice:
			date_invoice = time.strftime('%Y-%m-%d')
		
		try:
			inv = self.browse(cr, uid, ids[0])
		except:
			inv = self.browse(cr,uid,ids)
		if not payment_term_id:
			#To make sure the invoice due date should contain due date which is entered by user when there is no payment term defined
			return {'value':{'date_due': inv.date_due and inv.date_due or date_invoice}}
		if inv and inv.due_date_from_bl_date:
			ctx.update({'due_date_from_bl_date':inv.due_date_from_bl_date,'bl_date':inv.bl_date})	
		pterm_list = self.pool.get('account.payment.term').compute(cr, uid, payment_term_id, value=1, date_ref=date_invoice, context=ctx)
		if pterm_list:
			pterm_list = [line[0] for line in pterm_list]
			pterm_list.sort()
			res = {'value':{'date_due': pterm_list[-1]}}
		else:
			 raise osv.except_osv(_('Insufficient Data!'), _('The payment term of supplier does not have a payment term line.'))
		return res

	def group_lines(self, cr, uid, iml, line, inv):
		"""Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
		if inv.journal_id.group_invoice_lines:
			line2 = {}
			for x, y, l in line:
				tmp = self.inv_line_characteristic_hashcode(inv, l)

				if tmp in line2:
					am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
					amt_currency = line2[tmp]['amount_currency'] + l['amount_currency']
					line2[tmp]['debit'] = (am > 0) and am or 0.0
					line2[tmp]['credit'] = (am < 0) and -am or 0.0
					line2[tmp]['amount_currency'] = amt_currency
					line2[tmp]['tax_amount'] += l['tax_amount']
					line2[tmp]['analytic_lines'] += l['analytic_lines']
				else:
					line2[tmp] = l
			line = []
			for key, val in line2.items():
				line.append((0,0,val))
		return line

	def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
		# print ":;;;;;;;;;;;;;;;;;;; compute_invoice_totals Yang dijalankan di module ad_account_invoice"
		if context is None:
			context={}
		total = 0
		total_currency = 0
		cur_obj = self.pool.get('res.currency')
		tax_currency = inv.currency_tax_id and inv.currency_tax_id.id or company_currency
		tax_base_currency = inv.company_id and inv.company_id.tax_base_currency and inv.company_id.tax_base_currency.id or tax_currency
		
		# penanda menggunakan agar rate kmk disetiap account receiveble dan atau account tax
		is_kmk_tax = inv.company_id and inv.company_id.tax_base_currency and (inv.company_id.tax_base_currency.id == inv.currency_tax_id.id)

		context_rate = context.copy()

		context_rate.update({'date':inv.tax_date or (inv.date_effective and inv.date_effective or inv.date_invoice) or time.strftime('%Y-%m-%d'),'trans_currency':inv.currency_id and inv.currency_id.id or False})
		for i in invoice_move_lines:
			if inv.currency_id.id != company_currency:
				context.update({'date': inv.date_effective or inv.date_invoice or time.strftime('%Y-%m-%d')})
				i['currency_id'] = inv.currency_id.id
				i['amount_currency'] = i['price']

				if i['type'] == 'tax':
					if is_kmk_tax:
						context_rate.update({'reverse':False})
						# i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['amount_currency'] = round(round(i['tax_amount']/i['base_amount'],2)*cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['base'], context=context_rate),0)
						if inv.currency_id.id!=inv.company_id.tax_base_currency.id:
							context_rate.update({'reverse':True})
							i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id ,company_currency, i['price'],round=True, context=context)
						else:
							i['amount_currency'] = i['price']
							i['currency_id'] = inv.currency_id.id
							context_rate.update({'reverse':True})
							i['price'] = cur_obj.computerate(cr, uid, inv.currency_id.id ,company_currency, i['amount_currency'],round=True, context=context_rate)
						i['currency_id'] = tax_currency
						i['tax_amount'] = i['price'] 
					else:
						i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
								company_currency, i['price'],
								context=context)
						# i['currency_id'] = inv.currency_id and inv.currency_id.id or False
				else:	
					# if not inv.use_kmk_ar_ap:
					# 	i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
					# 			company_currency, i['price'],
					# 			context=context)
					# else:
					# 	context_rate.update({'reverse':False})
					# 	i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
					# 	context_rate.update({'reverse':True})
					# 	i['price'] = cur_obj.computerate(cr, uid, tax_base_currency, company_currency, i['amount_currency'], context=context_rate)
					# 	i['tax_amount'] = i['price']
					if is_kmk_tax and inv.use_kmk_ar_ap:
						context_rate.update({'reverse':False})
						i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						context_rate.update({'reverse':True})
						i['price'] = cur_obj.computerate(cr, uid, tax_base_currency, company_currency, i['amount_currency'],round=True, context=context_rate)
						i['tax_amount'] = i['price']
					else:
						i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
							company_currency, i['price'],round=True,
							context=context)
						# print "#################################",i['price']
			else:
				i['amount_currency'] = False
				i['ref'] = ref
				if i['type'] == 'tax':
					if is_kmk_tax:
						# i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['amount_currency'] = round(round(i['tax_amount']/i['base_amount'],2)*cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['base'], context=context_rate),0)
						i['currency_id'] = tax_base_currency
				elif i['type'] != 'tax' and inv.use_kmk_ar_ap:
				# 	if inv.currency_tax_id.id != company_currency  and inv.use_kmk_ar_ap:
				# 		i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
				# 		i['currency_id']=t1ax_base_currency or False
				# 	elif inv.currency_tax_id.id == company_currency and inv.use_kmk_ar_ap:
				# 		i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
				# 		i['currency_id']=tax_base_currency or False
					if is_kmk_tax:
						i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['currency_id']=tax_base_currency or False


			if inv.type in ('out_invoice','in_refund'):
				total += i['price']
				total_currency += i['amount_currency'] or i['price']
				i['price'] = - i['price']
			else:
				total -= i['price']
				total_currency -= i['amount_currency'] or i['price']
		# print "total===============",total
		return total, total_currency, invoice_move_lines

	def compute_diff_stock_real_time(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
		if context is None:
			context={}
		
		cur_obj = self.pool.get('res.currency')
		move_obj = self.pool.get('stock.move')
		product_obj = self.pool.get('product.product')
		line_obj = self.pool.get('account.invoice.line')
		
		is_kmk_tax = inv.company_id and inv.company_id.tax_base_currency and (inv.company_id.tax_base_currency.id == inv.currency_tax_id.id)

		context_rate = context.copy()
		context_rate.update({'date':inv.tax_date or (inv.date_effective and inv.date_effective or inv.date_invoice) or time.strftime('%Y-%m-%d'),'trans_currency':inv.currency_id and inv.currency_id.id or False})
			
		ppv_exist = line_obj.search(cr, uid, [('id','in',[x['invl_id'] for x in invoice_move_lines if x.get('invl_id',False)]),('is_ppv_entry','=',True)])
		if ppv_exist:
			return invoice_move_lines
		res = []
		for i in invoice_move_lines:
			
			if i['type']=='tax' or not i['product_id']:
				continue
			total_amt_stock = 0.0
			total_amt_inv = 0.0
			product = product_obj.browse(cr, uid, i['product_id'])
			account_stock_input_id = product.property_stock_account_input and product.property_stock_account_input.id or (product.categ_id.property_stock_account_input_categ and product.categ_id.property_stock_account_input_categ.id or False)
			if account_stock_input_id and i['account_id']==account_stock_input_id and product.valuation=='real_time':
				move_line_ids = move_obj.search(cr, uid, [('invoice_line_id','=',i['invl_id'])])
				for move in move_obj.browse(cr, uid, move_line_ids):
					total_amt_stock  += cur_obj.round(cr, uid, inv.company_id.currency_id,(move.product_qty * move.price_unit))
				total_amt_inv += i['price']
			diff = round((total_amt_inv - total_amt_stock),2)
			if abs(diff) > 0.0:
				if diff > 0.0:
					account_id = inv.type=='out_invoice' and inv.company_id.expense_receivable_currency_exchange_account_id or inv.company_id.expense_payable_currency_exchange_account_id
					if not account_id:
						raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
				else:
					account_id = inv.type=='out_invoice' and inv.company_id.income_receivable_currency_exchange_account_id or inv.company_id.income_payable_currency_exchange_account_id
					if not account_id:
						raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
				res.append({
					'type':'src',
					'name':'Unrealized Rounding',
					'price_unit': -diff,
					'quantity': 1,
					'price': -diff,
					'account_id': account_stock_input_id,
					'tax_code_id': False,
					'tax_amount': False,
					'account_analytic_id': False,
					'amount_currency': 0.0,
					'currency_id' : False,
					'ref' : ref,
				})

				res.append({
					'type':'src',
					'name':'Unrealized Rounding Gain/Loss',
					'price_unit': diff,
					'quantity': 1,
					'price': diff,
					'account_id': account_id.id,
					'tax_code_id': False,
					'tax_amount': False,
					'account_analytic_id': False,
					'amount_currency': 0.0,
					'currency_id' : False,
					'ref' : ref,
				})
		return invoice_move_lines + res

	def action_move_create(self, cr, uid, ids, context=None):
		"""Creates invoice related analytics and financial move lines"""
		# print "================ad_account_invoice=============="
		ait_obj = self.pool.get('account.invoice.tax')
		cur_obj = self.pool.get('res.currency')
		period_obj = self.pool.get('account.period')
		payment_term_obj = self.pool.get('account.payment.term')
		journal_obj = self.pool.get('account.journal')
		move_obj = self.pool.get('account.move')
		if context is None:
			context = {}
		for inv in self.browse(cr, uid, ids, context=context):
			if not inv.journal_id.sequence_id:
				raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line:
				raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
			if inv.move_id:
				continue

			ctx = context.copy()
			ctx.update({'lang': inv.partner_id.lang})
			if not inv.date_invoice:
				if not inv.date_effective:
					self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
				else:
					self.write(cr, uid, [inv.id], {'date_invoice': inv.date_effective}, context=ctx)
			
			if not inv.date_effective:
				if not inv.date_invoice:
					self.write(cr, uid, [inv.id], {'date_effective': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
				else:
					self.write(cr, uid, [inv.id], {'date_effective': inv.date_invoice}, context=ctx)

			company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
			# create the analytical lines
			# one move line per invoice line
			iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
			# for x in iml:
			# 	print "::::::::::::::::::::::", x['type'], x['name'], x['price'], x.get('amount_currency',False)
			# check if taxes are all computed
			compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
			if inv.currency_tax_id and inv.currency_tax_id.id==inv.company_id.tax_base_currency.id and inv.currency_id.id==inv.company_id.tax_base_currency.id:
				for taxe in compute_taxes.values():
					taxe['base'] = round(taxe['base'])
					taxe['amount'] = round(taxe['amount'])
					taxe['base_amount'] = round(taxe['base_amount'])
					taxe['tax_amount'] = round(taxe['tax_amount'])
			self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
			# I disabled the check_total feature
			group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
			group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
			if group_check_total and uid in [x.id for x in group_check_total.users]:
				if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
					raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

			if inv.payment_term:
				total_fixed = total_percent = 0
				for line in inv.payment_term.line_ids:
					if line.value == 'fixed':
						total_fixed += line.value_amount
					if line.value == 'procent':
						total_percent += line.value_amount
				total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
				if (total_fixed + total_percent) > 100:
					raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

			# one move line per tax line
			iml += ait_obj.move_line_get(cr, uid, inv.id)
			# for x in iml:
			# 	print ";;;;;;;;;;;;;;;;;;;;;;;;", x['type'], x['name'], x['price'], x.get('amount_currency',False)

			entry_type = ''
			if inv.type in ('in_invoice', 'in_refund'):
				# ref = inv.reference
				ref = ''
				entry_type = 'journal_pur_voucher'
				if inv.type == 'in_refund':
					entry_type = 'cont_voucher'
			else:
				ref = self._convert_ref(cr, uid, inv.number)
				entry_type = 'journal_sale_vou'
				if inv.type == 'out_refund':
					entry_type = 'cont_voucher'
			diff_currency_p = inv.currency_id.id <> company_currency
			
			# create one move line for the total and possibly adjust the other lines amount
			total = 0
			total_currency = 0
			# print "=========1=========",iml
			total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
			# print "=========2=========",iml,total,total_currency
			iml = self.compute_diff_stock_real_time(cr, uid, inv, company_currency, ref, iml, context=ctx)
			acc_id = inv.account_id.id

			# for x in iml:
			# 	print "++++++++++++++++++++++++++", x['type'], x['name'], x['price'], x['amount_currency']
			
			name = inv['name'] or inv['supplier_invoice_number'] or '/'
			totlines = False
			if inv.payment_term:
				if inv.due_date_from_bl_date:
					ctx.update({'due_date_from_bl_date':inv.due_date_from_bl_date,'bl_date':inv.bl_date})

				totlines = payment_term_obj.compute(cr,
						uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
			if totlines:
				res_amount_currency = total_currency
				i = 0
				ctx.update({'date': inv.date_effective and inv.date_effective or inv.date_invoice})
				for t in totlines:
					if inv.currency_id.id != company_currency:
						amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
					else:
						amount_currency = False

					# last line add the diff
					res_amount_currency -= amount_currency or 0
					i += 1
					if i == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': acc_id,
						'date_maturity': t[0],
						'amount_currency': diff_currency_p \
								and amount_currency or False,
						'currency_id': diff_currency_p \
								and inv.currency_id.id or False,
						'ref': ref,
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': acc_id,
					'date_maturity': inv.date_due or False,
					'amount_currency': diff_currency_p \
							and total_currency or False,
					'currency_id': diff_currency_p \
							and inv.currency_id.id or False,
					'ref': ref
			})
			
			date = inv.date_effective and inv.date_effective or inv.date_invoice or time.strftime('%Y-%m-%d')

			part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)
			# for x in iml:
			# 	print "---------------------------------", x['type'], x['name'], x['price'], x['amount_currency']
			# print "___________________________________________",iml
			line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)
			# for x in line:
			# 	print "))))))))))))))))))))))))))))))))))))", x[2]['name'], x[2]['debit'], x[2]['credit'], x[2]['amount_currency']
			line = self.group_lines(cr, uid, iml, line, inv)

			journal_id = inv.journal_id.id
			journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
			if journal.centralisation:
				raise osv.except_osv(_('User Error!'),
						_('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

			line = self.finalize_invoice_move_lines(cr, uid, inv, line)
			
			all_taxes = self.pool.get('account.tax').search(cr,uid,[])
			codes = [t.tax_code_id and t.tax_code_id.id  for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)] + [t.ref_tax_code_id and t.ref_tax_code_id.id  for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)]
			codes = list(set(codes))
					
			line_temp = []
			for mvl_temp in line:
				
				if 'tax_code_id' in mvl_temp[2] and mvl_temp[2]['tax_code_id'] in codes:
					dummy_data = mvl_temp[2].copy()
					dummy_data.update({
						'faktur_pajak_source'	:'account.invoice,%s'%inv.id,
#						'faktur_pajak_no'		: inv.nomor_faktur_id and inv.nomor_faktur_id.name or ''
						})
					line_temp.append((0,0,dummy_data))
				else:
					line_temp.append(mvl_temp)
			line = line_temp
			
			move = {
				# 'ref': inv.reference and inv.reference or inv.name,
				'line_id': line,
				'journal_id': journal_id,
				'date': date,
				'narration': inv.comment,
				'company_id': inv.company_id.id,
			}
			# print "-------------------line----------------------",line
			period_id = inv.period_id and inv.period_id.id or False
			ctx.update(company_id=inv.company_id.id,
					   account_period_prefer_normal=True)
			if not period_id:
				period_ids = period_obj.find(cr, uid, inv.date_effective and inv.date_effective or inv.date_invoice, context=ctx)
				period_id = period_ids and period_ids[0] or False
			if period_id:
				move['period_id'] = period_id
				for i in line:
					i[2]['period_id'] = period_id

			ctx.update(invoice=inv)
			move_id = move_obj.create(cr, uid, move, context=ctx)
			new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
			# make the invoice point to that move
		
			self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			# link to account_move post
			move_obj.post(cr, uid, [move_id], context=ctx)
		self._log_event(cr, uid, ids)
		return True

	def line_get_convert(self, cr, uid, x, part, date, context=None):
		res = super(account_invoice,self).line_get_convert(cr, uid, x, part, date, context=context)
		if x['price']:
			res['amount_currency'] = x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False))
		else:
			res['amount_currency'] = x['amount_currency']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False))
		return res

	def get_lc(self, picking_ids, product_ids):
		res1 = [] # for lc_product_line_id
		res2 = [] # for lc_id
		for picking in picking_ids:
			for move in picking.move_lines:
				if move.lc_product_line_id and move.lc_product_line_id not in res1 and move.product_id.id in product_ids:
					res1.append(move.lc_product_line_id)
					if move.lc_product_line_id.lc_id not in res2:
						res2.append(move.lc_product_line_id.lc_id)
			for lc in picking.lc_ids:
				if lc not in res2:
					res2.append(lc)
		return res1, res2

	def update_description(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		for inv in self.browse(cr, uid, ids, context=context):
			shipper_id = False
			use_shipper = False
			shipper_desc = ""
			consignee_id = False
			use_consignee = False
			consignee_desc = ""
			applicant_id = False
			use_applicant = False
			applicant_desc = ""
			buyer_id = False
			use_buyer = False
			buyer_desc = ""
			notify_id = False
			use_notify = False
			notify_desc = ""
			source_port_id = False
			source_port_desc = ""
			dest_port_id = False
			dest_port_desc = ""
			picking_ids = inv.picking_ids
			sale_ids = []
			if picking_ids:
				product_ids = [x.product_id.id for x in inv.invoice_line if x.product_id]
				lc_product_lines, lc_objs = self.get_lc(picking_ids,product_ids)
				# first, take desc from lc_product_lines
				# move_line_ids = [y.id for x in picking_ids for y in x.move_lines]
				if lc_product_lines:
					lc_product_lines_desc = {}
					for line in lc_product_lines:
						if line.consignee_pl and not consignee_id:
							consignee_id = line.consignee_pl.id
						if line.show_consignee_address_pl and not use_consignee:
							use_consignee = line.show_consignee_address_pl
						if line.c_address_text_pl and not consignee_desc:
							consignee_desc = line.c_address_text_pl
						
						if line.notify_pl and not notify_id:
							notify_id = line.notify_pl.id
						if line.show_notify_address_pl and not use_notify:
							use_notify = line.show_notify_address_pl
						if line.n_address_text_pl and not notify_desc:
							notify_desc = line.n_address_text_pl

						if line.lc_dest and not dest_port_id:
							dest_port_id = line.lc_dest.id
						if line.lc_dest_desc and not dest_port_desc:
							dest_port_desc = line.lc_dest_desc
						
						if line.product_id.id not in lc_product_lines_desc:
							lc_product_lines_desc.update({line.product_id.id:line.name})
					
					for prod in inv.invoice_line:
						if prod.move_line_ids and prod.move_line_ids[0].lc_product_line_id:
							self.pool.get('account.invoice.line').write(cr, uid, prod.id, {'name':prod.move_line_ids[0].lc_product_line_id.name})
						elif prod.product_id.id in lc_product_lines_desc:
							self.pool.get('account.invoice.line').write(cr, uid, prod.id, {'name':lc_product_lines_desc[prod.product_id.id]})

				if lc_objs:
					for lc in lc_objs:
						# if lc.shipper and not shipper_id:
						# 	shipper_id = lc.shipper.id
						if lc.show_shipper_address and not use_shipper:
							use_shipper = lc.show_shipper_address
						if lc.s_address_text and not shipper_desc:
							shipper_desc = lc.s_address_text
						
						if lc.applicant_pl and not applicant_id:
							applicant_id = lc.applicant_pl.id
						if lc.show_applicant_address_pl and not use_applicant:
							use_applicant = lc.show_applicant_address_pl
						if lc.a_address_text_pl and not applicant_desc:
							applicant_desc = lc.a_address_text_pl
						
						if lc.consignee_pl and not consignee_id:
							consignee_id = lc.consignee_pl.id
						if lc.show_consignee_address_pl and not use_consignee:
							use_consignee = lc.show_consignee_address_pl
						if lc.c_address_text_pl and not consignee_desc:
							consignee_desc = lc.c_address_text_pl
						
						if lc.notify_pl and not notify_id:
							notify_id = lc.notify_pl.id
						if lc.show_notify_address_pl and not use_notify:
							use_notify = lc.show_notify_address_pl
						if lc.n_address_text_pl and not notify_desc:
							notify_desc = lc.n_address_text_pl
			update_val={}
			# if shipper_id:
			# update_val.update({'shipper':shipper_id})
			# if use_shipper:
			update_val.update({'show_shipper_address':use_shipper})
			# if shipper_desc:
			update_val.update({'s_address_text':shipper_desc})
			# if applicant_id:
			update_val.update({'applicant':applicant_id})
			# if use_applicant:
			update_val.update({'show_applicant_address':use_applicant})
			# if applicant_desc:
			update_val.update({'a_address_text':applicant_desc})
			# if consignee_id:
			update_val.update({'consignee':consignee_id})
			# if use_consignee:
			update_val.update({'show_consignee_address':use_consignee})
			# if consignee_desc:
			update_val.update({'c_address_text':consignee_desc})
			# if notify_id:
			update_val.update({'notify':notify_id})
			# if use_notify:
			update_val.update({'show_notify_address':use_notify})
			# if notify_desc:
			update_val.update({'n_address_text':notify_desc})
			# if dest_port_desc:
			update_val.update({'port_to_desc':dest_port_desc})
			# if dest_port_id:
			update_val.update({'port_to':dest_port_id})
			# print ">>>>>>>>>>>>>>>>>>>>>", update_val
			if update_val:
				self.write(cr, uid, inv.id, update_val)
		return True

	def print_invoice_for_released(self, cr, uid, ids, context=None):
		if context is None:
			context={}
		datas = {
			'model': 'account.invoice',
			'ids': ids,
			'form': self.read(cr, uid, ids[0], context=context),
		}
		# if context.get('header',False):
		# 	datas.update({'header':context.get('header',False)})
		return {'type': 'ir.actions.report.xml', 'report_name': 'invoice.for.released', 'datas': datas}
account_invoice()

class account_invoice_line(osv.osv):
	""" inherited account.invoice.line """
	_inherit = 'account.invoice.line'
	
	_columns = {
		'name': fields.text('Description', required=True, readonly=False),
		'invoice_id': fields.many2one('account.invoice', 'Invoice Reference', ondelete='cascade', select=True, readonly=True),
		'uos_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True, readonly=True, states={'draft':[('readonly',False)]}),
		'product_id': fields.many2one('product.product', 'Product', ondelete='set null', select=True, readonly=True, states={'draft':[('readonly',False)]}),
		'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The income or expense account related to the selected product.", readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'), readonly=True, states={'draft':[('readonly',False)]}),
		'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_line_tax', 'invoice_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)], readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
		'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),

		'company_id': fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
		'partner_id': fields.related('invoice_id','partner_id',type='many2one',relation='res.partner',string='Partner',store=True, readonly=True),
		
		'currency_id' : fields.related('invoice_id','currency_id',type='many2one',relation='res.currency',string='Currency'),
		'state': fields.related('invoice_id', 'state', type='selection', string='Status', selection=[
			('draft','Draft'),
			('proforma','Pro-forma'),
			('proforma2','Confirm by MRKT'),
			('open','Open'),
			('paid','Paid'),
			('cancel','Cancelled'),
			]),
		'payment_date' : fields.related('invoice_id', 'payment_date', type='date', string='Payment Date'),
		'is_ppv_entry' : fields.boolean('Is for PPV entry'),
	}

	_defaults = {
		'state' : lambda *a:'draft',
	}

	def unlink(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_lines = self.read(cr, uid, ids, ['state'], context=context)
		unlink_ids = []

		for t in invoice_lines:
			if t['state'] not in ('draft', 'cancel'):
				raise osv.except_osv(_('User Error!'),
					_('You cannot delete an invoice line which is the parent invoice not draft or cancelled. You should refund it instead.'))
			else:
				unlink_ids.append(t['id'])
		
		super(account_invoice_line,self).unlink(cr, uid, unlink_ids)
		return True
