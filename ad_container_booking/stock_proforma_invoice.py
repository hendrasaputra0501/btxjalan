from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class stock_proforma_invoice(osv.Model):
	def _get_type(self, cr, uid, context=None):
		if context is None:
			context = {}
		return context.get('type', 'out_invoice')

	def _get_journal(self, cr, uid, context=None):
		if context is None:
			context = {}
		type_inv = context.get('type', 'out_invoice')
		user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
		company_id = context.get('company_id', user.company_id.id)
		type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
		journal_obj = self.pool.get('account.journal')
		domain = [('company_id', '=', company_id)]
		if isinstance(type_inv, list):
			domain.append(('type', 'in', [type2journal.get(type) for type in type_inv if type2journal.get(type)]))
		else:
			domain.append(('type', '=', type2journal.get(type_inv, 'sale')))
		res = journal_obj.search(cr, uid, domain, limit=1)
		return res and res[0] or False

	def _get_currency(self, cr, uid, context=None):
		res = False
		journal_id = self._get_journal(cr, uid, context=context)
		if journal_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
			res = journal.currency and journal.currency.id or journal.company_id.currency_id.id
		return res

	def _get_invoice_line(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('stock.proforma.invoice.line').browse(cr, uid, ids, context=context):
			result[line.invoice_id.id] = True
		return result.keys()

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
				taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
				res[invoice.id]['amount_tax'] += taxes['total_included']-taxes['total']
			res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
		return res

	def _get_amount_peb_fob(self, cr, uid, ids, name, args, context=None):
		res = {}
		for invoice in self.browse(cr, uid, ids, context=context):
			res[invoice.id] = invoice.amount_total - invoice.peb_freight - invoice.peb_insurance
		return res

	_name = "stock.proforma.invoice"
	_columns = {
		'name': fields.char('Description', size=64, select=True),
		'origin': fields.char('Source Document', size=64, help="Reference of the document that produced this invoice."),
		'type': fields.selection([
			('out_invoice','Customer Invoice'),
			('in_invoice','Supplier Invoice'),
			('out_refund','Customer Refund'),
			('in_refund','Supplier Refund'),
			],'Type', readonly=True, select=True, change_default=True, track_visibility='always'),
		'internal_number': fields.char('Invoice Number', size=32, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
		'reference': fields.char('Invoice Reference', size=64, help="The partner reference of this invoice."),
		'comment': fields.text('Additional Information'),
		'additional_remarks' : fields.text('Additional Remarks'),
		
		'date_invoice': fields.date('Invoice Date', select=True, help="Keep empty to use the current date"),
		'date_due': fields.date('Due Date', select=True,
			help="If you use payment terms, the due date will be computed automatically at the generation "\
				"of accounting entries. The payment term may compute several due dates, for example 50% now and 50% in one month, but if you want to force a due date, make sure that the payment term is not set on the invoice. If you keep the payment term and the due date empty, it means direct payment."),
		
		'partner_id': fields.many2one('res.partner', 'Partner', change_default=True, required=True, track_visibility='always'),
		'payment_term': fields.many2one('account.payment.term', 'Payment Terms',
			help="If you use payment terms, the due date will be computed automatically at the generation "\
				"of accounting entries. If you keep the payment term and the due date empty, it means direct payment. "\
				"The payment term may compute several due dates, for example 50% now, 50% in one month."),

		'invoice_line': fields.one2many('stock.proforma.invoice.line', 'invoice_id', 'Invoice Lines'),
		'tax_line': fields.one2many('stock.proforma.invoice.tax', 'invoice_id', 'Tax Lines'),

		'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
			store={
				'stock.proforma.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
				# 'stock.proforma.invoice.tax': (_get_invoice_tax, None, 20),
				'stock.proforma.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
			},
			multi='all'),
		'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
			store={
				'stock.proforma.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
				# 'stock.proforma.invoice.tax': (_get_invoice_tax, None, 20),
				'stock.proforma.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
			},
			multi='all'),
		'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
			store={
				'stock.proforma.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
				# 'stock.proforma.invoice.tax': (_get_invoice_tax, None, 20),
				'stock.proforma.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
			},
			multi='all'),
		'currency_id': fields.many2one('res.currency', 'Currency', required=True, track_visibility='always'),
		'journal_id': fields.many2one('account.journal', 'Journal', required=True,
									  domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale_refund'], 'in_refund': ['purchase_refund'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]"),
		'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True),
		'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account',
			help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Supplier Refund, otherwise a Partner bank account number.'),
		'user_id': fields.many2one('res.users', 'Salesperson', track_visibility='onchange'),

		'goods_type' : fields.selection([('finish','Finish Goods'),('finish_others','Finish Goods(Others)'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type'),
		'sale_type' : fields.selection([('export','Export'),('local','Local')],"Sale Type"),
		'locale_sale_type' : fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type"),
		'incoterms' : fields.many2one('stock.incoterms','Incoterm Contract', readonly=False),
		# post shipment information
		'bl_date' : fields.date('BL Date'),
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

		#additional party information
		'shipper' : fields.many2one('res.partner','Shipper'),
		's_address_text' : fields.text('Shipper Address Details'),
		'show_shipper_address' : fields.boolean('Use Customs Address Desc?'),

		'buyer' : fields.many2one('res.partner','Buyer',domain=[('customer', '=', True)]),
		'show_buyer_address' : fields.boolean('Use Customs Address Desc?'),
		'address_text' : fields.text('Buyer Address Details'),
		
		'consignee' : fields.many2one('res.partner','Consignee',domain=[('customer', '=', True)]),
		'show_consignee_address' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text' : fields.text('Consignee Address Details'),
		
		'notify' : fields.many2one('res.partner','Notify',domain=[('customer', '=', True)]),
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text' : fields.text('Notify Address Details'),
		
		'applicant' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)]),
		'show_applicant_address' : fields.boolean('Use Customs Address Desc?'),
		'a_address_text' : fields.text('Applicant Address Details'),
		
		'label_print' : fields.text('Label Print'),
		# 'model_id':fields.many2one('ir.model','Model'),

		'picking_ids' : fields.one2many('stock.picking','draft_invoice_id','Related Picking(s)',readonly=True),
		'sale_ids': fields.many2many('sale.order', 'sale_order_stock_prof_invoice_rel', 'invoice_id', 'order_id', 'Sale Order', readonly=True, help="This is the list of sales order source document"),
	}
	_defaults = {
		'type': _get_type,
		'journal_id': _get_journal,
		'currency_id': _get_currency,
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.proforma.invoice', context=c),
		'internal_number': False,
		'user_id': lambda s, cr, u, c: u,
	}

stock_proforma_invoice()

class stock_proforma_invoice_line(osv.Model):
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
			res[line.id] = taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	_name = "stock.proforma.invoice.line"
	_order = "invoice_id,sequence,id"
	_columns = {
		'name': fields.text('Description', required=True),
		'origin': fields.char('Source Document', size=256, help="Reference of the document that produced this invoice."),
		'sequence': fields.integer('Sequence', help="Gives the sequence of this line when displaying the invoice."),
		'invoice_id': fields.many2one('stock.proforma.invoice', 'Invoice Reference', ondelete='cascade', select=True),
		'uos_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null', select=True),
		'product_id': fields.many2one('product.product', 'Product', ondelete='set null', select=True),
		'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
		'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
			digits_compute= dp.get_precision('Account'), store=True),
		'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
		# 'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
		'invoice_line_tax_id': fields.many2many('account.tax', 'stock_proforma_invoice_line_tax', 'invoice_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
	}
	_defaults = {
		'quantity': 1,
		# 'discount': 0.0,
		'price_unit': 0,
		'sequence': 10,
	}
stock_proforma_invoice_line()

# class stock_proforma_invoice_tax(osv.Model):
# 	_name = "stock.proforma.invoice.tax"
# 	_columns = {
# 		'invoice_id': fields.many2one('stock.proforma.invoice', 'Invoice Line', ondelete='cascade', select=True),
# 		'name': fields.char('Tax Description', size=64, required=True),
# 		'account_id': fields.many2one('account.account', 'Tax Account', required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
# 		'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
# 		'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
# 		'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
# 		'manual': fields.boolean('Manual'),
# 		'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of invoice tax."),
# 		'base_code_id': fields.many2one('account.tax.code', 'Base Code', help="The account basis of the tax declaration."),
# 		'base_amount': fields.float('Base Code Amount', digits_compute=dp.get_precision('Account')),
# 		'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', help="The tax basis of the tax declaration."),
# 		'tax_amount': fields.float('Tax Code Amount', digits_compute=dp.get_precision('Account')),
# 		'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
# 		'factor_base': fields.function(_count_factor, string='Multipication factor for Base code', type='float', multi="all"),
# 		'factor_tax': fields.function(_count_factor, string='Multipication factor Tax code', type='float', multi="all")
# 	}
# 	_order = 'sequence'
# 	_defaults = {
# 		'manual': 1,
# 		'base_amount': 0.0,
# 		'tax_amount': 0.0,
# 	}
# stock_proforma_invoice_line()