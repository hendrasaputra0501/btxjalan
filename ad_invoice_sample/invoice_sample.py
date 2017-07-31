from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class invoice_sample(osv.osv):
	def _amount_all(self, cr, uid, ids, name, args, context=None):
		res = {}
		tax_obj = self.pool.get('account.tax')
		for invoice in self.browse(cr, uid, ids, context=context):
			res[invoice.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0
			}
			for line in invoice.invoice_line:
				res[invoice.id]['amount_untaxed'] += line.price_subtotal
			for line in invoice.invoice_line:
				taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, line.quantity, product=line.product_id, partner=line.invoice_id.consignee_partner_id)
				res[invoice.id]['amount_tax'] += taxes['total_included']-taxes['total']
			res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
		return res

	# def _get_sequence(self, cr, uid, ids, name, args, context=None):
	# 	res = {}
	# 	sale_obj = self.pool.get('sale.order')
	# 	for invoice in self.browse(cr, uid, ids, context=context):
	# 		seq = False
	# 		if invoice.sale_id:
	# 			curr_pi = invoice.sale_id.proforma_ids
	# 			curr_seq_pi = [x.sequence for x in curr_pi]
	# 			len_curr_seq = max(curr_seq_pi)
	# 			if not invoice.sequence:
	# 				seq = len_curr_seq+1
			
	# 		if not invoice.sequence:
	# 			res[invoice.id]=seq
	# 		else:
	# 			res[invoice.id]=invoice.sequence
	# 	return res

	_name = "invoice.sample"
	_description = 'Invoice Sample'
	_order = "id desc"
	_columns = {
		# 'sequence' : fields.function(_get_sequence, type="integer", string='Sequence Number', store=True),
		'name': fields.char('Invoice Name', size=64, select=True, readonly=True),
		# 'sale_id' : fields.many2one('sale.order','Sales Contract'),
		# 'origin': fields.char('Source Document', size=64, help="Reference of the document that produced this proforma invoice."),
		'note': fields.text('Internal Information'),
		'type': fields.selection([
			('out_invoice','Customer Invoice'),
			('in_invoice','Supplier Invoice'),
			],'Type', readonly=True, select=True, change_default=True, track_visibility='always'),
		# 'state': fields.selection([
		#	 ('draft','Draft'),
		#	 ('proforma','Pro-forma'),
		#	 ('cancel','Cancelled'),
		#	 ],'Status', select=True, readonly=True, track_visibility='onchange',
		#	 help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
		#	 \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
		#	 \n* The \'Cancelled\' status is used when user cancel invoice.'),
		'sent': fields.boolean('Sent', readonly=True, help="It indicates that the proforma invoice has been sent."),
		'date_invoice': fields.date('Invoice Date', readonly=False, select=True, help="Keep empty to use the current date"),
		# 'date_due': fields.date('Due Date', readonly=True, states={'draft':[('readonly',False)]}, select=True,
		#	 help="If you use payment terms, the due date will be computed automatically at the generation "\
		#		 "of accounting entries. The payment term may compute several due dates, for example 50% now and 50% in one month, but if you want to force a due date, make sure that the payment term is not set on the invoice. If you keep the payment term and the due date empty, it means direct payment."),
		# 'partner_id': fields.many2one('res.partner', 'Buyer', change_default=True, readonly=False, required=True, track_visibility='always'),
		# 'p_address_text' : fields.text('Buyer Address Custom'),
		# 'p_use_custom_address' : fields.boolean('Use Custom Buyer Address?'),
		'consignee_partner_id': fields.many2one('res.partner', 'Consignee', change_default=True, readonly=False, required=True, track_visibility='always'),
		'c_address_text' : fields.text('Consignee Address Custom'),
		'c_use_custom_address' : fields.boolean('Use Custom Consignee Address?'),
		# 'notify_partner_id': fields.many2one('res.partner', 'Notify', change_default=True, readonly=False, required=False, track_visibility='always'),
		# 'n_address_text' : fields.text('Notify Address Custom'),
		# 'n_use_custom_address' : fields.boolean('Use Custom Notify Address?'),
		'shipper_id': fields.many2one('res.partner', 'Shipper', change_default=True, readonly=False, required=True, track_visibility='always'),
		's_address_text' : fields.text('Shipper Address Custom'),
		's_use_custom_address' : fields.boolean('Use Custom Shipper Address?'),
		'payment_term': fields.many2one('account.payment.term', 'Payment Terms',readonly=False,
			help="If you use payment terms, the due date will be computed automatically at the generation "\
				"of accounting entries. If you keep the payment term and the due date empty, it means direct payment. "\
				"The payment term may compute several due dates, for example 50% now, 50% in one month."),
		# 'tax_line': fields.one2many('proforma.invoice.tax', 'invoice_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]}),
		'invoice_line': fields.one2many('invoice.sample.line', 'invoice_id', 'Invoice Lines', readonly=False),
		'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always', multi='all'),
		'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax', multi='all'),
		'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total', multi='all'),
		'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=False, track_visibility='always'),
		'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=False),
		'remit_to' : fields.many2one('res.bank', 'Remit To',
			help=''),
		'credit_to' : fields.many2one('res.bank', 'Credit To',
			help=''),
		'company_bank_account' : fields.many2one('res.partner.bank', 'Bank Account',
			help='Bitratex Bank Account'),
		'user_id': fields.many2one('res.users', 'Salesperson', readonly=False, track_visibility='onchange'),
		'picking_ids' : fields.many2one('stock.picking', 'Related DO', readonly=False),
		'trucking_company':fields.many2one("stock.transporter","Transporter Trucking"),
	}


	# def _invoice_line_for(self, cr, uid, order_line):
	# 	invoice_line = {
	# 		'name': order_line.name,
	# 		# 'origin': fields.char('Source Document', size=256, help="Reference of the document that produced this proforma invoice."),
	# 		# 'sequence': fields.integer('Sequence', help="Gives the sequence of this line when displaying the invoice."),
	# 		'uom_id': order_line.product_uom.id,
	# 		'product_id': order_line.product_id.id,
	# 		'price_unit': order_line.price_unit,
	# 		'invoice_line_tax_id': [(6,0,[x.id for x in order_line.tax_id])],
	# 		'quantity': order_line.product_uom_qty,
	# 	}
	# 	if order_line.order_id.sale_type=='export':
	# 		invoice_line['name']=order_line.export_desc
	# 	return invoice_line

	# def default_get(self, cr, uid, fields, context):
	# 	if context is None: context = {}
	# 	res = super(invoice_sample, self).default_get(cr, uid, fields, context=context)
	# 	sale_id = context.get('sale_id', False)

	# 	# active_model = context.get('active_model')
	# 	# assert active_model in ('sale.order'), 'Bad context propagation'

	# 	if sale_id:
	# 		sale=self.pool.get('sale.order').browse(cr, uid, sale_id)

	# 		if 'sale_id' in fields:
	# 			res.update(sale_id=sale.id)
	# 		if 'partner_id' in fields:
	# 			res.update(partner_id=sale.partner_id.id)
	# 		if 'consignee_partner_id' in fields:
	# 			res.update(consignee_partner_id=sale.consignee and sale.consignee.id or sale.partner_invoice_id and sale.partner_invoice_id.id or sale.partner_id.id)
	# 		if 'notify_partner_id' in fields:
	# 			res.update(notify_partner_id=sale.notify and sale.notify.id or False)
	# 		if 'payment_term' in fields:
	# 			res.update(payment_term=False)
	# 		if 'currency_id' in fields:
	# 			res.update(payment_term=sale.currency_id and sale.currency_id.id or False)
	# 		if 'company_id' in fields:
	# 			res.update(payment_term=sale.currency_id and sale.currency_id.id or False)
	# 		if 'date_invoice' in fields:
	# 			res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
	# 		# if 'opening_bank' in fields:
	# 		# 	res.update(payment_term=sale.opening_bank and sale.opening_bank.id or False)
	# 		# if 'intermed_bank' in fields:
	# 		# 	res.update(payment_term=sale.intermed_bank and sale.intermed_bank.id or False)
	# 		# if 'negotiate_bank' in fields:
	# 		# 	res.update(payment_term=sale.negotiate_bank and sale.negotiate_bank.id or False)
	# 		if 'invoice_line' in fields:
	# 			line_ids = [self._invoice_line_for(cr, uid, order_line) for order_line in sale.order_line if order_line.state not in ('done')]
	# 			res.update(invoice_line=line_ids)
		
	# 	return res


	_defaults = {
		'type' : 'out_invoice',
		'date_invoice':lambda *a:time.strftime('%Y-%m-%d'),
		'currency_id': lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
		'shipper_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr,uid,uid,c).company_id.partner_id.id or False,
		'user_id': lambda s, cr, u, c: u,
		'sent': False,
	}

	def create(self, cr, uid, vals, context=None):
		res=super(invoice_sample, self).create(cr, uid, vals, context=context)
		pi_id = self.browse(cr, uid, res)
		if pi_id:
			company_code = ''

			if pi_id.company_id:
				company_code=pi_id.company_id.name[3]
			# print pi_id.company_id.name,"vavavavavavavvvvvvvvvvvvvvvvvvvvvvvvvvv"
			# print company_code,"brrarrararararararararaaaaaaaaaaaa"
			# prrr
			if pi_id.picking_ids:
			# 	if pi_id.picking_ids.sale_type=='export':
			# 		# self.write(cr, uid, res ,{'name': (company_code+'E '+(self.pool.get('ir.sequence').get(cr, uid, 'proforma.invoice.export') or '/'))})
			# 		self.write(cr, uid, res ,{'name': (company_code+'SA-EXP'+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.sample.export') or '/'))})
			# 	elif pi_id.picking_ids.sale_type=='local':
			# 		# self.write(cr, uid, res ,{'name': (company_code+'L '+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.sample.local') or '/'))})
			# 		self.write(cr, uid, res ,{'name': (company_code+'SA-LOC'+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.sample.local') or '/'))})
			# else:
				self.write(cr, uid, res ,{'name': (company_code+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.sample.sequence') or '/'))})		
		return res

	def get_address(self, partner_obj):
		if partner_obj:
			partner_address = ''
			partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
			partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
			partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
			partner_address += partner_obj.city and partner_obj.city +' ' or ''
			partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
			partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''

			return  partner_address
		else:
			return False

	def onchange_check(self, cr, uid, ids, partner_id, context=None):
		if context is None:
			context = {}
		if not partner_id:
			return {'value':{}}

		result = {}
		partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
		if context.get('shipper',False) and partner:
			result.update({'s_address_text':self.get_address(partner)})
		if context.get('consignee',False) and partner:
			result.update({'c_address_text':self.get_address(partner)})
		# if context.get('partner',False) and partner:
		# 	result.update({'p_address_text':self.get_address(partner)})
		# if context.get('notify',False) and partner:
		# 	result.update({'n_address_text':self.get_address(partner)})

		return {'value':result}

invoice_sample()

class invoice_sample_line(osv.osv):
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.consignee_partner_id)
			res[line.id] = taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	_name = "invoice.sample.line"
	_description = "Invoice Sample Line"
	_order = "invoice_id,sequence,id"
	_columns = {
		'name': fields.text('Description', required=True),
		'origin': fields.char('Source Document', size=256, help="Reference of the document that produced this proforma invoice."),
		'sequence': fields.integer('Sequence', help="Gives the sequence of this line when displaying the invoice."),
		'invoice_id': fields.many2one('invoice.sample', 'Invoice Sample', ondelete='cascade', select=True),
		'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True),
		'product_id': fields.many2one('product.product', 'Product', ondelete='set null', select=True),
		'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
		'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
			digits_compute= dp.get_precision('Account')),
		'invoice_line_tax_id': fields.many2many('account.tax', 'invoice_sample_line_tax', 'invoice_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
		'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
		'company_id': fields.related('invoice_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
		# 'partner_id': fields.related('invoice_id','partner_id',type='many2one',relation='res.partner',string='Partner',store=True),
		'move_id' : fields.many2one('stock.move', 'Stock Move', ondelete='cascade', select=True),
	}

	_defaults = {
		'quantity': 1,
		'price_unit': 0.0,
		'sequence': 10,
	}
