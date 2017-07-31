import time
from report import report_sxw
from report.render import render
from osv import osv
import pooler
from ad_amount2text_idr import amount_to_text_id
import datetime

class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_webkit_html, self).__init__(cr, uid, name, context=context)
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'nourut': self.no_urut,
            'blank_line':self.blank_line,
            'total_amount':self.total_amount,
            'get_rate_convertion':self._get_rate_convertion,
            'get_move_lines' : self._get_move_lines,
        })
    
    def convert(self, amount, cur):
        amt_id = amount_to_text_id.amount_to_text(amount, 'id', cur)
        return amt_id
    
    def total_amount(self, ext_lines):
        total = 0.0
        for ext in ext_lines:
            if ext.credit:
                total+=ext.credit
        return total#{'quantity':total}
    
    def no_urut(self, list, value):
        return list.index(value) + 1
        
    def blank_line(self, nlines):
        
#row = len(nlines)
        row = nlines
        res = ""
        if row < 8:
            for i in range(8 - row):
                res = res + ('A<br/>')
                #res = res + ('<tr> <td>&nbsp;</td> <td>&nbsp;</td> <td>&nbsp;</td> <td colspan="2">&nbsp;</td></tr>')
        return res

    def _get_rate_convertion(self, move_line):
        cr = self.cr
        uid = self.uid
        curr_obj = self.pool.get('res.currency')
        company_currency = move_line.move_id.company_id.currency_id
        company_tax_currency = move_line.move_id.company_id.tax_base_currency
        current_currency = move_line.currency_id and move_line.currency_id or False
        context = {}
        
        context.update({'date':move_line.date})
        rate = 1
        amt_trans = 1 * (move_line.debit or move_line.credit)
        currency_trans = company_currency and company_currency.name or ''
        if move_line.move_id and (move_line.move_id.journal_id.type=='sale' or move_line.move_id.journal_id.type=='purchase'):
            if move_line.invoice and current_currency and current_currency == company_tax_currency and current_currency<>company_currency:
                currency_trans = move_line.invoice.currency_id.name
                if move_line.invoice.currency_id==company_tax_currency:
                    if move_line.invoice.use_kmk_ar_ap and move_line.invoice.currency_tax_id.id==company_tax_currency.id:
                        tax_date = (move_line and move_line.invoice and move_line.invoice.tax_date !='False' and move_line.invoice.tax_date) or move_line.invoice.date_invoice
                        tax_date = self.formatLang(tax_date, date=True)

                        tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',company_currency.id),('name','<=',datetime.datetime.strptime(tax_date,'%d/%m/%Y').strftime('%Y-%m-%d')  )])
                        if tax_rate_ids:
                            rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
                    else:
                        rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.invoice.currency_id, context=context)
                    amt_trans = move_line.amount_currency
                else:
                    rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.invoice.currency_id, context=context)
                    amt_trans = move_line.amount_currency
                    # amt_trans = curr_obj.round(cr, uid, current_currency, amt_trans * rate)
            elif move_line.invoice and current_currency and current_currency<>company_currency:
                currency_trans = move_line.invoice.currency_id.name
                rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                amt_trans = move_line.amount_currency
                # amt_trans = curr_obj.round(cr, uid, current_currency, amt_trans * rate)
            elif current_currency:
                currency_trans = current_currency.name
                rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                amt_trans = move_line.amount_currency

        elif move_line.move_id and (move_line.move_id.journal_id.type=='bank' or move_line.move_id.journal_id.type=='cash'):
            currency_trans = move_line.journal_id.currency and move_line.journal_id.currency.name or (current_currency and current_currency.name or currency_trans)
            if move_line.move_id and move_line.journal_id and move_line.journal_id.currency and current_currency and move_line.journal_id.currency==current_currency:
                # kondisi 1 : untuk move_line gainloss ar/ap
                if move_line.reconcile_id and not move_line.amount_currency:
                    rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                    amt_trans = 0.0
                # kondisi 2 : untuk move_line transaksi casual bank/cash 
                else:
                    rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                    amt_trans = move_line.amount_currency
            elif move_line.move_id and move_line.journal_id and move_line.journal_id.currency and current_currency and move_line.journal_id.currency!=current_currency:
                rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                amt_trans = move_line.amount_currency
                currency_trans = current_currency.name
            elif move_line.move_id and move_line.journal_id and move_line.journal_id.currency and not current_currency:
                rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.journal_id.currency, context=context)
                amt_trans = 0.0
            elif not move_line.journal_id.currency and current_currency:
                rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
                amt_trans = move_line.amount_currency
        elif current_currency:
            currency_trans = current_currency.name
            rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
            amt_trans = move_line.amount_currency
        return rate, amt_trans, currency_trans

    # def _get_rate_convertion(self, move_line):
    #     cr = self.cr
    #     uid = self.uid
    #     curr_obj = self.pool.get('res.currency')
    #     company_currency = move_line.move_id.company_id.currency_id
    #     company_tax_currency = move_line.move_id.company_id.tax_base_currency
    #     current_currency = move_line.currency_id and move_line.currency_id or False
    #     context = {}
        
    #     context.update({'date':move_line.date})
    #     rate = 1
    #     amt_trans = 1 * (move_line.debit or move_line.credit)
    #     currency_trans = company_currency and company_currency.name or ''
    #     if move_line.move_id and (move_line.move_id.journal_id.type=='sale' or move_line.move_id.journal_id.type=='purchase'):
    #         if move_line.invoice and current_currency and current_currency == company_tax_currency and current_currency<>company_currency:
    #             currency_trans = move_line.invoice.currency_id.name
    #             if move_line.invoice.currency_id==company_tax_currency:
    #                 if move_line.invoice.use_kmk_ar_ap:
    #                     tax_date = (move_line and move_line.invoice and move_line.invoice.tax_date !='False' and move_line.invoice.tax_date) or move_line.invoice.date_invoice
    #                     tax_date = self.formatLang(tax_date, date=True)

    #                     tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',company_currency.id),('name','<=',datetime.datetime.strptime(tax_date,'%d/%m/%Y').strftime('%Y-%m-%d')  )])
    #                     if tax_rate_ids:
    #                         rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
    #                 else:
    #                     rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.invoice.currency_id, context=context)
    #                 amt_trans = abs(move_line.amount_currency)
    #             else:
    #                 rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.invoice.currency_id, context=context)
    #                 amt_trans = curr_obj.round(cr, uid, current_currency, amt_trans * rate)
    #         elif move_line.invoice and current_currency and current_currency<>company_currency:
    #             currency_trans = move_line.invoice.currency_id.name
    #             rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
    #             amt_trans = curr_obj.round(cr, uid, current_currency, amt_trans * rate)
    #         elif current_currency:
    #             currency_trans = current_currency.name
    #             rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
    #             amt_trans = abs(move_line.amount_currency)

    #     elif move_line.move_id and (move_line.move_id.journal_id.type=='bank' or move_line.move_id.journal_id.type=='cash'):
    #         currency_trans = move_line.move_id.journal_id.currency and move_line.move_id.journal_id.currency.name or currency_trans
    #         if move_line.move_id and move_line.move_id.journal_id.currency and current_currency and move_line.move_id.journal_id.currency==current_currency:
    #             # kondisi 1 : untuk move_line gainloss ar/ap
    #             if move_line.reconcile_id and not move_line.amount_currency:
    #                 rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
    #                 amt_trans = 0.0
    #             # kondisi 2 : untuk move_line transaksi casual bank/cash 
    #             else:
    #                 rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
    #                 amt_trans = abs(move_line.amount_currency)
    #         elif move_line.move_id and move_line.move_id.journal_id.currency and not current_currency:
    #             rate = curr_obj._get_conversion_rate(cr, uid, company_currency, move_line.move_id.journal_id.currency, context=context)
    #             amt_trans = 0.0
    #     elif current_currency:
    #         currency_trans = current_currency.name
    #         rate = curr_obj._get_conversion_rate(cr, uid, company_currency, current_currency, context=context)
    #         amt_trans = abs(move_line.amount_currency)
    #     return rate, amt_trans, currency_trans

    def move_line_characteristic_hashcode(self, move_line):
        return "%s-%s-%s-%s-%s"%(
            move_line.debit>0 and "dr" or "cr",
            move_line.account_id and move_line.account_id.id or "False",
            move_line.tax_code_id and move_line.tax_code_id.id or "False",
            move_line.partner_id and move_line.partner_id.id or "False",
            move_line.currency_id and move_line.currency_id.id or "False")

    def _get_move_lines(self, move_lines):
        res = []
        move_line_group = {}
        for line in sorted(move_lines, key=lambda x:x.id):
            rate,amt_curr,curr = self._get_rate_convertion(line)
            type_line = (line.debit>0 or line.amount_currency > 0) and 'dr' or 'cr'
            # group for tax only for transaction from tax_lines on ext_transaksi
            if line.tax_code_id and line.faktur_pajak_source and line.faktur_pajak_source._name=='ext.transaksi.line':
                key = self.move_line_characteristic_hashcode(line)
                if key not in move_line_group:
                    move_line_group[key]={
                        'line_id' : line.id,
                        'account_code' : line.account_id.code or line.account_id.code2 or False,
                        'account_name' : line.account_id.name or '',
                        'referense': '',
                        'date_maturity' : line.date!='False' and line.date or '',
                        'description' : (line.name or '') + (line.partner_id and (' from '+ line.partner_id.name) or ''),
                        'trans_currency' : curr,
                        'trans_amt' : amt_curr,
                        'rate_currency' : rate,
                        'debit' : line.debit or 0.0,
                        'credit' : line.credit or 0.0,
                        'type_line' : type_line,
                    }
                else:
                    move_line_group[key]['line_id']=move_line_group[key]['line_id']>line.id and line.id or move_line_group[key]['line_id']
                    move_line_group[key]['trans_amt']+=amt_curr
                    move_line_group[key]['debit']+=line.debit or 0.0
                    move_line_group[key]['credit']+=line.credit or 0.0

            # grouping for expense, if there is a bugs, MODIF HERE
            elif line.account_id.type!='receivable' and line.account_id.type!='payable' and line.account_id.user_type.code!='bank' \
                and line.account_id.user_type.code!='cash' and not line.tax_code_id and not line.reconcile_id and not line.invoice and line.analytic_account_id:
                key = "expense-"+str(line.debit>0 and 'dr' or 'cr')+"-"+str(line.account_id.id)+'-'+str(line.analytic_account_id and line.analytic_account_id.id or 'False')
                if key not in move_line_group:
                    move_line_group[key]={
                        'line_id' : line.id,
                        'account_code' : line.account_id.code or line.account_id.code2 or False,
                        'account_name' : line.account_id.name or '',
                        'referense': '',
                        'date_maturity' : line.date!='False' and line.date or '',
                        'description' : line.move_id.narration or line.move_id.name,
                        'trans_currency' : curr,
                        'trans_amt' : amt_curr,
                        'rate_currency' : rate,
                        'debit' : line.debit or 0.0,
                        'credit' : line.credit or 0.0,
                        'type_line' : type_line,
                    }
                else:
                    # move_line_group[key]['description']+=';'+line.name or ''
                    move_line_group[key]['line_id']=move_line_group[key]['line_id']>line.id and line.id or move_line_group[key]['line_id']
                    move_line_group[key]['trans_amt']+=amt_curr
                    move_line_group[key]['debit']+=line.debit or 0.0
                    move_line_group[key]['credit']+=line.credit or 0.0

            # Not For Grouping
            else:
                key = "nontax-"+str(line.debit>0 and "dr" or "cr")+"-"+str(line.id)
                move_line_group[key]={
                    'line_id' : line.id,
                    'account_code' : line.account_id.code or '' + '/' + line.account_id.code2 or '',
                    'account_name' : line.account_id.name or '',
                    'referense': line.other_ref and line.other_ref or line.ref or '',
                    'date_maturity' : line.date!='False' and line.date or '',
                    'description' : '',
                    'trans_currency' : curr,
                    'trans_amt' : amt_curr,
                    'rate_currency' : rate,
                    'debit' : line.debit or 0.0,
                    'credit' : line.credit or 0.0,
                    'type_line' : type_line,
                }
                # if line.account_id.type=='receivable' or line.account_id.type=='payable' or line.account_id.user_type.code=='bank' or line.account_id.user_type.code=='cash':
                move_line_group[key]['line_id']=move_line_group[key]['line_id']>line.id and line.id or move_line_group[key]['line_id']
                if line.account_id.type=='receivable' or line.account_id.type=='payable':
                    move_line_group[key]['description']=line.partner_id and line.partner_id.name or line.name or ''
                else:
                    move_line_group[key]['description']=line.name or ''
        for x in move_line_group.keys():
            res.append(move_line_group[x])

        return sorted(res, key = lambda x:x['line_id'])
        
from netsvc import Service
try:
    del Service._services['report.webkit.extra.transaksi']
    del Service._services['report.webkit.account.move']
except:
    pass

report_sxw.report_sxw('report.webkit.extra.transaksi',
                       'ext.transaksi', 
                       'addons/ad_ext_transaksi/report/report_webkit_html.mako',
                       parser=report_webkit_html,header=False)
report_sxw.report_sxw('report.webkit.account.move',
                       'account.move', 
                       'addons/ad_ext_transaksi/report/account_move_html.mako',
                       parser=report_webkit_html,header=False)
