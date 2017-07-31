import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc, SUPERUSER_ID
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools import float_compare
from openerp.tools.translate import _


class account_invioce_line(osv.osv):
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			# price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit, line.quantity, context={})
			price_after = disc.get('price_after',line.price_unit)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price_after, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
			res[line.id] = taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res
	
	_inherit = "account.invoice.line"
	_columns = {
		"discount_ids" : fields.many2many('price.discount','price_discount_inv_line_line_rel','invoice_line_id','disc_id',"Discounts"),
		'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
			digits_compute= dp.get_precision('Account'), store=True),
	}
account_invioce_line()

class account_invoice_tax(osv.osv):
	_inherit = "account.invoice.tax"

	def compute(self, cr, uid, invoice_id, context=None):
		tax_grouped = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
		cur = inv.currency_id
		company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
		for line in inv.invoice_line:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit,line.quantity,context={})
			price_after = disc.get('price_after',line.price_unit)
			for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price_after, line.quantity, line.product_id, inv.partner_id)['taxes']:
				val={}
				val['invoice_id'] = inv.id
				val['name'] = tax['name']
				val['amount'] = tax['amount']
				val['manual'] = False
				val['sequence'] = tax['sequence']
				val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity'])

				if inv.type in ('out_invoice','in_invoice'):
					val['base_code_id'] = tax['base_code_id']
					val['tax_code_id'] = tax['tax_code_id']
					val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
					val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
					val['account_id'] = tax['account_collected_id'] or line.account_id.id
					val['account_analytic_id'] = tax['account_analytic_collected_id']
				else:
					val['base_code_id'] = tax['ref_base_code_id']
					val['tax_code_id'] = tax['ref_tax_code_id']
					val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
					val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
					val['account_id'] = tax['account_paid_id'] or line.account_id.id
					val['account_analytic_id'] = tax['account_analytic_paid_id']

				key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
				if not key in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']
					tax_grouped[key]['base_amount'] += val['base_amount']
					tax_grouped[key]['tax_amount'] += val['tax_amount']

		for t in tax_grouped.values():
			t['base'] = cur_obj.round(cr, uid, cur, t['base'])
			t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
			t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
			t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
		return tax_grouped

		