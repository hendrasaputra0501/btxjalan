from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta

class insurance_polis(osv.Model):
	def _amount_all(self, cr, uid, ids, name, args, context=None):
		res = {}
		tax_obj = self.pool.get('account.tax')
		for polis in self.browse(cr, uid, ids, context=context):
			res[polis.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0
			}
			for line in polis.product_ids:
				res[polis.id]['amount_untaxed'] += line.price_subtotal
			for line in polis.product_ids:
				taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, line.quantity, product=line.product_id, partner=line.invoice_id and line.invoice_id.partner_id and line.invoice_id.partner_id or False)
				res[polis.id]['amount_tax'] += taxes['total_included']-taxes['total']
			res[polis.id]['amount_total'] = res[polis.id]['amount_tax'] + res[polis.id]['amount_untaxed']
		return res

	_name = "insurance.polis"
	_description = "Insurance Polis"
	_columns = {
		"type" : fields.selection([('sale','Sale'),('purchase','Purchase')],'Type'),
		# 'name' : fields.char('Name',size=50,required=True, readonly=True, states={'draft':[('readonly',False)]}),
		# basic information
		"contract_number" : fields.char('Contract Number',size=50,required=False),
		"name" : fields.char('Policy No',size=50,required=True),
		"entry_date" : fields.date('Entry Date'),
		"company_id" : fields.many2one('res.company','Company',readonly=True),
		"insured" : fields.many2one('res.partner','Insured by',required=True),
		"insurer" : fields.many2one('res.partner','Insurer',required=True),
		"currency_id" : fields.many2one('res.currency', 'Currency', required=True, track_visibility='always'),
		"clause_ids" : fields.many2many('insurance.clause','polis_clause_rel','polis_id','clause_id', 'Conditions/Clauses'),
		
		"insured_amount" : fields.float('Insured Amount'),
		"compute_insured_amount" : fields.text('Insured Amount Compute'),
		"premi_rate" : fields.float('Premi Rate (%)', digits=(2,6)),
		"deductible_amount" : fields.float('Deductible Amount'),
		"compute_deductible_amount" : fields.text('Deductible Amount Compute'),
		"invoice_charge_id" : fields.many2one('account.invoice','Invoice Charge',help='This is invoice charge that create to pay the Premi/Deductible Amount'),
		"bpa_charge_id":fields.many2one("ext.transaksi","BPA Insurance"),
		"product_ids" : fields.one2many('insurance.polis.products','polis_id','Interest'),

		# shipment information
		"invoice_id" : fields.many2one('account.invoice','Invoice Number'),
		"invoice_ids" : fields.many2many('account.invoice','insurance_invioce_rel','insurance_id','invoice_id','Invoice(s)'),
		"picking_ids" : fields.many2many('stock.picking','insurance_picking_rel','insurance_id','picking_id','Picking(s)'),
		# "bl_number" : fields.related('invoice_id','bl_number',relation='account.invoice', type='char',readonly=True),
		"bl_number" : fields.char('BL Number',size=200),
		"lc_number" : fields.char('LC Number',size=200),
		"amount_untaxed": fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always', multi='all'),
		"amount_tax": fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax', multi='all'),
		"amount_total": fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total', multi='all'),
		"vessel" : fields.related('invoice_id','vessel_name',relation='account.invoice', type='char',readonly=True),
		# "date_sailing" : fields.related('invoice_id','bl_number',relation='account.invoice', type='char',readonly=True),
		# "voyage_from" : fields.related('invoice_id','bl_number',relation='account.invoice', type='char',readonly=True),
		# "voyage_to" : fields.related('invoice_id','bl_number',relation='account.invoice', type='char',readonly=True),
		# "transhipment" : fields.related('invoice_id','bl_number',relation='account.invoice', type='char',readonly=True),
		'supplier_invoice_number' : fields.char('Supplier Invoice Number', char=64),
		"shipper" : fields.text('Shipper'),
		"consignee" : fields.text('Consignee'),
		"notify" : fields.text('Notify'),
		'title_document_header_one' : fields.char('Title Label'),
		'title_document_header_two' : fields.char('Subtitle Label'),
		'claim_title'				: fields.char('Claim Label'),
		'claim_data'				: fields.char('Claim Text'),
		'surveyor'					: fields.many2one('res.partner', 'Surveyor'),
		'desc_surveyor'				: fields.text('Address'),
		'open_cover_no'				: fields.char('Open-Cover NO'),
		'value_at'					: fields.char('Value AT'),
		# vessel, connect vessel, voyage from, voyage to,transhipment 20150210
		'vessel_conveyance'	: fields.char('Vessel/Conveyance',size=120),
		'connect_vessel' : fields.char('Connect Vessel',size=60),
		'voyage_from' : fields.char('Voyage From',size=60),
		'transhipment' : fields.char('Transhipment',size=60),
		'voyage_to' : fields.char('Voyage To',size=60),
		'paid' : fields.boolean('Paid'),
		'address_text' : fields.text('Insured by Address Details'),
		'show_insuredby_address' : fields.boolean('Use Customs Address Desc?'),
		'show_premi_rate' : fields.boolean("Show Premi Rate"),
		'deductable_premi': fields.char('Deductable Premi'),
		'period_id' : fields.many2one('account.period','Period'),
		'additional_cost' : fields.one2many('insurance.other.cost','polis_id', 'Additional Cost'),
		'lc_date' :fields.date('LC Date'),
		'invoice_number' : fields.char('Invoice Number'),
		'invoice_date' : fields.date('Invoice Date'),
	}

	_defaults = {
		'company_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id or False,
		'currency_id': lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
		'insured' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.partner_id.id or False,
		'compute_insured_amount' : '''# total_cost : Total\n\ninsured_amount = total_cost + (total_cost*10/100)''',
		'compute_deductible_amount' : '''# premi_rate : Premi Rate\n# insured_amount : total Insured Amount\n# Deductible Amount / Premi\n\npremi = premi_rate / 100 * insured_amount''',
		'insured_amount' : 0.0,
		'deductible_amount' : 0.0,
		'premi_rate' : 0.0,
		'open_cover_no':'0103111000023',
		'type':lambda self,cr,uid,context: context.get('type','sale'),
		'show_premi_rate':True,
		'deductable_premi':lambda self,cr,uid,context: context.get('type','sale')=='sale' and  '''0.5% OF TSI, MAX USD 1,000 AOA''' or '',
		'consignee':lambda self,cr,uid,context: context.get('type','sale')=='purchase' and 'PT. BITRATEX INDUSTRIES \nJL. BRIGJEND S. SUDIARTO KM 11 \nSEMARANG, INDONESIA' or '',
		'notify':lambda self,cr,uid,context: context.get('type','sale')=='purchase' and 'PT. BITRATEX INDUSTRIES \nJL. BRIGJEND S. SUDIARTO KM 11 \nSEMARANG, INDONESIA' or '',
	}

	_order = "id asc"

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'The Police Number of the certificate must be unique!'),
	]

	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		default = default.copy()
		default.update({
		'name': '-',
		})
		return super(insurance_polis, self).copy(cr, uid, id, default, context)

	def default_get(self, cr, uid, fields, context):
		if context is None: context = {}
		res = super(insurance_polis, self).default_get(cr, uid, fields, context=context)
		
		if 'additional_cost' in fields:
			curr_idr_id = self.pool.get('res.currency').search(cr, uid, [('name','=','IDR')])
			line_ids=[{
					'sequence' : 1,
					'name' : 'Certificate Fee',
					'amount':10000.00,
					'show' : True,
					'currency_id':curr_idr_id and curr_idr_id[0] or self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id,},
					{
					'sequence' : 2,
					'name' : 'Stamp Duty',
					'amount':9000.00,
					'show' : True,
					'currency_id':curr_idr_id and curr_idr_id[0] or self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id,
					}]
			res.update(additional_cost=line_ids)
		
		return res

	# def create(self, cr, uid, vals, context=None):
	# 	if context is None:
	# 		context = {}
		
	# 	return super(insurance_polis, self).create(cr, uid, id, default, context)

	def onchange_picking(self, cr, uid, ids, picking_ids):
		res = {
			'invoice_ids' : False,
		}
		if picking_ids and picking_ids[0][2]:
			invoice_ids = []
			for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids[0][2]):
				if picking.invoice_id and picking.invoice_id.id not in invoice_ids:
					invoice_ids.append(picking.invoice_id.id)
			if invoice_ids:
				res['invoice_ids']=invoice_ids

		return {'value':res}

	def onchange_invoice(self, cr, uid, ids, instype, invoice_id, invoice_ids, currency_id, polis_date, context=None):
		res = {}
		if context is None:
			context = {}
		# if instype=='sale':
		inv_ids = invoice_id and [invoice_id] or []
		if inv_ids:
			inv = self.pool.get('account.invoice').browse(cr, uid, inv_ids, context=context)[0]
			res.update({'bl_number':inv.bl_number})
			res.update({'lc_number':inv.picking_ids and inv.picking_ids[0].lc_ids and inv.picking_ids[0].lc_ids[0].lc_number or ''})
		elif invoice_ids:
			product_val = {}
			curr_obj = self.pool.get('res.currency')
			if currency_id:
				for inv in self.pool.get('account.invoice').browse(cr, uid, invoice_ids[0][2], context=context):
					if not product_val:
						product_val = {
							'invoice_id' : False,
							'invoice_line_id' : False,
							'product_id' : False,
							'name' : "Detail Invoice Terlampir",
							'uom_id' : False,
							'quantity' : 1.0,
							'price_unit' : 0.0,
							'invoice_line_tax_id' : False,
						}
					
					context.update({'date':polis_date or time.strftime('%Y-%m-%d')})
					product_val['price_unit']+=curr_obj.compute(cr, uid, inv.currency_id.id, currency_id, inv.amount_untaxed, context=context)
			if product_val:
				res.update({'product_ids':[(0,0,product_val)]})
		return {'value':res}

	def generate_products(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		products = []
		
		polis = self.browse(cr, uid, ids)[0]
		if polis.invoice_id:
			for line in polis.invoice_id.invoice_line:
				products.append([0,0,{
					'polis_id' : polis.id,
					'invoice_id' : polis.invoice_id.id,
					'invoice_line_id' : line.id,
					'product_id' : line.product_id and line.product_id.id or False,
					'name' : line.name,
					'uom_id' : line.uos_id and line.uos_id.id or False,
					'quantity' : line.quantity or 0.0,
					'price_unit' : line.price_unit or 0.0,
					'invoice_line_tax_id' : line.invoice_line_tax_id and line.invoice_line_tax_id or False,
					}])

		if polis.invoice_ids:
			for inv in polis.invoice_ids:
				for line in polis.invoice_id.invoice_line:
					products.append([0,0,{
						'polis_id' : polis.id,
						'invoice_id' : polis.invoice_id.id,
						'invoice_line_id' : line.id,
						'product_id' : line.product_id and line.product_id.id or False,
						'name' : line.name,
						'uom_id' : line.uos_id and line.uos_id.id or False,
						'quantity' : line.quantity or 0.0,
						'price_unit' : line.price_unit or 0.0,
						'invoice_line_tax_id' : line.invoice_line_tax_id and line.invoice_line_tax_id or False,
						}]) 

		if products:
			self.write(cr, uid, polis.id, {'product_ids':products})

		return True

	def compute_insured_amount(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		polis = self.browse(cr, uid, ids)[0]
		localdict = {'total_cost':polis.amount_total}
		exec polis.compute_insured_amount in localdict
		amt = localdict['insured_amount']

		return self.write(cr, uid, polis.id, {'insured_amount':amt})

	def compute_deductible_amount(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		polis = self.browse(cr, uid, ids)[0]
		localdict = {'premi_rate':polis.premi_rate, 'insured_amount':polis.insured_amount}
		exec polis.compute_deductible_amount in localdict
		premi = localdict['premi']

		return self.write(cr, uid, polis.id, {'deductible_amount':premi})

	def _prepare_invoice(self, cr, uid, polis, partner, inv_type='in_invoice', context=None):
		""" Builds the dict containing the values for the invoice
			@param polis: polis object
			@param partner: object of the partner to invoice
			@param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
			@param journal_id: ID of the accounting journal
			@return: dict that will be used to create the invoice object
		"""
		if isinstance(partner, int):
			partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
		if inv_type in ('out_invoice', 'out_refund'):
			account_id = partner.property_account_receivable.id
			payment_term = partner.property_payment_term.id or False
		else:
			account_id = partner.property_account_payable.id
			payment_term = partner.property_supplier_payment_term.id or False
		# comment = self._get_comment_invoice(cr, uid, picking)
		invoice_vals = {
			# 'name': picking.name,
			# 'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
			'charge_type':'sale',
			'type': inv_type,
			'account_id': account_id,
			'partner_id': partner.id,
			# 'comment': comment,
			'payment_term': payment_term,
			# 'fiscal_position': partner.property_account_position.id,
			'date_invoice': time.strftime('%Y-%m-%d'),
			'company_id': polis.company_id.id,
			'user_id': uid,
		}
		cur_id = polis.currency_id and polis.currency_id.id or False
		if cur_id:
			invoice_vals['currency_id'] = cur_id
		# if journal_id:
		# 	invoice_vals['journal_id'] = journal_id
		return invoice_vals

	def invoice_charge_create(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		polis = self.browse(cr, uid, ids)[0]
		ai_pool = self.pool.get('account.invoice')
		aml_pool = self.pool.get('account.invoice.line')
		charge_type_pool = self.pool.get('charge.type')
		invoice_vals=self._prepare_invoice(cr, uid, polis, polis.insurer and polis.insurer.id or False, 'in_invoice', context=context)

		account_id=False
		type_of_charge=False
		charge_ids = charge_type_pool.search(cr, uid, [('name','=','Insurance')])
		if charge_ids:
			charge_id = charge_type_pool.browse(cr, uid, charge_ids[0], context=context)
			type_of_charge = charge_ids[0]
			account_id = charge_id.account_id and charge_id.account_id.id or False

		if not account_id or not type_of_charge:
			raise osv.except_osv(_('Error, no type charge!'),
				_('Please create one type charge with name Insurance and define the Expense Account too'))
		else:
			invoice_id = ai_pool.create(cr, uid, invoice_vals, context=context)
			aml_pool.create(cr, uid, 
			{
				'name': polis.invoice_id and 'Insurance for INV No.' + polis.invoice_id.internal_number or '',
				# 'origin': origin,
				'invoice_id': invoice_id,
				'invoice_related_id':polis.invoice_id and polis.invoice_id.id or False,
				'uos_id': False,
				'product_id': False,
				'type_of_charge' : type_of_charge,
				'account_id': account_id,
				'price_unit': polis.deductible_amount,
				'quantity': 1.0,
				'account_analytic_id': False,
			}, context=context)

			# run the trigger of insurance charge to compute total insurance cost 
			ai_pool.write(cr, uid, invoice_id, {'state':'draft'})
			self.write(cr, uid, polis.id, {'invoice_charge_id':invoice_id})

		return True

	def bpa_charge_create(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		polis = self.browse(cr, uid, ids)[0]
		bpa_obj = self.pool.get('ext.transaksi')
		bpa_line_obj = self.pool.get('ext.transaksi.line')
		charge_type_pool = self.pool.get('charge.type')
		for polis in self.browse(cr, uid, ids):
			account_id=False
			type_of_charge=False
			charge_ids = charge_type_pool.search(cr, uid, [('name','=','Insurance')])
			if charge_ids:
				charge_id = charge_type_pool.browse(cr, uid, charge_ids[0], context=context)
				type_of_charge = charge_ids[0]
				account_id = charge_id.account_id and charge_id.account_id.id or False

			if not account_id or not type_of_charge:
				raise osv.except_osv(_('Error, no type charge!'),
					_('Please create one type charge with name Insurance and define the Expense Account too'))
			else:
				bpa_id = bpa_obj.create(cr, uid, {
					'name' : 'Insurance Payment',
					'journal_id': False,
					'ref': '',
					'request_date': time.strftime('%Y-%m-%d'),
					# 'due_date': time.strftime('%Y-%m-%d')},
					'currency_id':polis.currency_id and polis.currency_id.id or False,
					}, context=context)
				bpa_line_obj.create(cr, uid, {
					'type_of_charge': type_of_charge,
					'account_id' : account_id,
					'invoice_related_id' : polis.invoice_id and polis.invoice_id.id or False,
					'name' : polis.name and 'Insurance Payment fo Polis No. '+polis.name or 'Insurance Payment',
					'ext_transaksi_id': bpa_id,
					'debit': polis.deductible_amount,
					'partner_id': polis.insurer and polis.insurer.id or False,
				}, context=context)

				# run the trigger of insurance charge to compute total insurance cost 
				bpa_obj.write(cr, uid, bpa_id, {'state':'draft'})
				self.write(cr, uid, polis.id, {'bpa_charge_id':bpa_id})

		return True

class insurance_polis_products(osv.Model):
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id or False, partner=line.invoice_id and line.invoice_id.partner_id and line.invoice_id.partner_id or False)
			res[line.id] = taxes['total']
			if line.invoice_id:
				cur = line.invoice_id and line.invoice_id.currency_id or line.polis_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	_name = "insurance.polis.products"
	_description = "Insurance Product"
	_columns = {
		"polis_id": fields.many2one('insurance.polis', 'Insurance Polis', ondelete='cascade', select=True),
		"invoice_id": fields.many2one('account.invoice', 'Invoice', select=True),
		"invoice_line_id": fields.many2one('account.invoice.line', 'Invoice Line', select=True),
		"name": fields.text('Description', required=True),
		"product_id": fields.many2one('product.product', 'Product', ondelete='set null', select=True),
		"uom_id": fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True),
		"price_unit": fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
		"price_subtotal": fields.function(_amount_line, string='Amount', type="float",
			digits_compute= dp.get_precision('Account')),
		"invoice_line_tax_id": fields.many2many('account.tax', 'polis_products_tax', 'polis_products_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
		"quantity": fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
	}
	_defaults = {
		'quantity': 1,
		'price_unit': 0.0,
	}
	_order = "id asc"

class insurance_clause(osv.Model):
	_name = "insurance.clause"
	_description = "Insurance Clause"
	_columns = {
		"name": fields.char('Name', size=200, required=True),
		"code": fields.char('Code', size=10, required=True),
		"description": fields.text('Description'),
	}

class insurance_other_cost(osv.Model):
	_name = "insurance.other.cost"
	_description = "Insurance Other Cost"
	_columns = {
		"polis_id": fields.many2one('insurance.polis', 'Insurance Polis', ondelete='cascade', select=True),
		"sequence": fields.integer('Sequence'),
		"name": fields.char('Name', size=200, required=True),
		"show": fields.boolean('Show in printed Paper'),
		"currency_id" : fields.many2one('res.currency', 'Currency', required=True),
		"amount" : fields.float('Amount', required=True),
	}
