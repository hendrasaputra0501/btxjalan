from osv import osv
from osv import fields
import time


class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    def _global_amount_compute(self, cr, uid, invoice, taxes, context=None):
        if invoice.fiscal_position and invoice.fiscal_position.global_tax_ids:
            new_tax_ids = self.pool.get('account.fiscal.position').map_global_tax(cr, uid, invoice.amount_untaxed, invoice.fiscal_position, taxes, context=context)
            new_taxes = self.pool.get('account.tax').browse(cr, uid, new_tax_ids, context=context)
            return new_taxes
        return taxes

    #===========================================================================
    # THIS METHOD RETURN THE WRONG AMOUNT IN TAX INCLUDE IN PRICE
    #===========================================================================

#    def compute(self, cr, uid, invoice_id, context=None):
#        if context is None:
#            context = {}
#        print context
#        tax_grouped = {}
#        tax_obj = self.pool.get('account.tax')
#        cur_obj = self.pool.get('res.currency')
#        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context)
#        cur = inv.currency_id
#        company_currency = inv.company_id.currency_id.id
#
#        for line in inv.invoice_line:
#            ## INHERIT -- START
#            invline_taxes = self._global_amount_compute(cr, uid, inv, line.invoice_line_tax_id, context=context)
#            ## INHERIT -- END
#
#            for tax in tax_obj.compute(cr, uid, invline_taxes, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
#                val={}
#                val['invoice_id'] = inv.id
#                val['name'] = tax['name']
#                val['amount'] = tax['amount']
#                val['manual'] = False
#                val['sequence'] = tax['sequence']
#                val['base'] = tax['price_unit'] * line['quantity']
#
#                if inv.type in ('out_invoice','in_invoice'):
#                    val['base_code_id'] = tax['base_code_id']
#                    val['tax_code_id'] = tax['tax_code_id']
#                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
#                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
#                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
#                else:
#                    val['base_code_id'] = tax['ref_base_code_id']
#                    val['tax_code_id'] = tax['ref_tax_code_id']
#                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
#                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
#                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
#
#                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
#                if not key in tax_grouped:
#                    tax_grouped[key] = val
#                else:
#                    tax_grouped[key]['amount'] += val['amount']
#                    tax_grouped[key]['base'] += val['base']
#                    tax_grouped[key]['base_amount'] += val['base_amount']
#                    tax_grouped[key]['tax_amount'] += val['tax_amount']
#
#        for t in tax_grouped.values():
#            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
#            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
#            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
#            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
#        return tax_grouped
#
    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                tax['price_unit'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['price_unit'] * line['quantity']

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
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
        # print "tax_grouped===================",tax_grouped
        return tax_grouped

account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
