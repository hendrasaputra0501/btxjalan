# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from lxml import etree

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _
from openerp.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from openerp.report import report_sxw


class cash_settlement(osv.osv):

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('type', False)

    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        if context.get('invoice_id', False):
            company_id = self.pool.get('account.invoice').browse(cr, uid, context['invoice_id'], context=context).company_id.id
            context.update({'company_id': company_id})
        periods = self.pool.get('account.period').find(cr, uid, context=context)
        return periods and periods[0] or False

    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        invoice_pool = self.pool.get('account.invoice')
        if context.get('invoice_id', False):
            currency_id = invoice_pool.browse(cr, uid, context['invoice_id'], context=context).currency_id.id
            journal_id = journal_pool.search(cr, uid, [('currency', '=', currency_id)], limit=1)
            return journal_id and journal_id[0] or False
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')

        ttype = context.get('type', 'bank')
        if ttype in ('payment', 'receipt'):
            ttype = 'bank'
        res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
        return res and res[0] or False

    def _get_tax(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if not journal_id:
            ttype = context.get('type', 'bank')
            res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            if tax_id and ttype in ('sale', 'purchase'):
                return False
            return tax_id
        return False
    
    def _get_currency_base(self, cr, uid, context=None):
        
        currency_search = self.pool.get('res.currency').search(cr, uid, [('base','=',True)])
        currency_browse = self.pool.get('res.currency').browse(cr, uid, currency_search)
        id_currency = False
        for cur_id in currency_browse:
            id_currency = cur_id.id
        return id_currency

    def _get_currency(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            if journal.currency:
                return journal.currency.id
        return self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id

    def _get_partner(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('partner_id', False)

    def _get_reference(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('reference', False)

    def _get_narration(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('narration', False)

    def _get_amount(self, cr, uid, context=None):
        if context is None:
            context= {}
        return context.get('amount', 0.0)

#    def name_get(self, cr, uid, ids, context=None):
#        if not ids:
#            return []
#        if context is None: context = {}
#        return [(r['id'], (str("%.2f" % r['amount']) or '')) for r in self.read(cr, uid, ids, ['amount'], context, load='_classic_write')]

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        mod_obj = self.pool.get('ir.model.data')
        if context is None: context = {}

        def get_res_id(view_type, condition):
            result = False
            if view_type == 'tree':
                result = mod_obj.get_object_reference(cr, uid, 'cash_settlement', 'view_voucher_tree')
            elif view_type == 'form':
                if condition:
                    result = mod_obj.get_object_reference(cr, uid, 'cash_settlement', 'view_vendor_receipt_form')
                else:
                    result = mod_obj.get_object_reference(cr, uid, 'cash_settlement', 'view_vendor_payment_form')
            return result and result[1] or False

        if not view_id and context.get('invoice_type', False):
            view_id = get_res_id(view_type,context.get('invoice_type', False) in ('out_invoice', 'out_refund'))

        if not view_id and context.get('line_type', False):
            view_id = get_res_id(view_type,context.get('line_type', False) == 'customer')

        res = super(cash_settlement, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='partner_id']")
        if context.get('type', 'sale') in ('purchase', 'payment'):
            for node in nodes:
                node.set('domain', "[('supplier', '=', True)]")
            res['arch'] = etree.tostring(doc)
        return res

    def _compute_writeoff_amount(self, cr, uid, line_dr_ids, line_cr_ids, amount, type):
        debit = credit = 0.0
        sign = type == 'payment' and 1 or -1
        for l in line_dr_ids:
            debit += l['amount']
        for l in line_cr_ids:
            credit += l['amount']
        return amount - sign * (credit - debit)

#     def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount):
#         if not line_dr_ids and not line_cr_ids:
#             return {'value':{}}
#         line_dr_ids = [x[2] for x in line_dr_ids]
#         line_cr_ids = [x[2] for x in line_cr_ids]
#         return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount)}}

    def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
        context = context or {}
        if not line_dr_ids and not line_cr_ids:
            return {'value':{'writeoff_amount': 0.0, 'reserved': 0.0}}  #add value for reserved
        line_osv = self.pool.get("cash.settlement.line")
        line_dr_ids = resolve_o2m_operations(cr, uid, line_osv, line_dr_ids, ['amount'], context)
        line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, line_cr_ids, ['amount'], context)
        #compute the field is_multi_currency that is used to hide/display options linked to secondary currency on the voucher
        is_multi_currency = False
        #loop on the voucher lines to see if one of these has a secondary currency. If yes, we need to see the options
        reserved = 0.0
        settlement_amount = 0.0
        for voucher_line in line_dr_ids+line_cr_ids:
            line_id = voucher_line.get('id') and line_osv.browse(cr, uid, voucher_line['id'], context=context).move_line_id.id or voucher_line.get('move_line_id')
            amount_unreconciled = voucher_line.get('amount_unreconciled', voucher_line.get('id') and line_osv.browse(cr, uid, voucher_line['id'], context=context).amount_original or 0.0)
            amount2 = voucher_line.get('amount', 0.0)
            if line_id and self.pool.get('account.move.line').browse(cr, uid, line_id, context=context).currency_id:
                is_multi_currency = True
                break
            settlement_amount += amount2
            reserved += amount_unreconciled
        if settlement_amount:
            amount = settlement_amount
        return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount, type), 'is_multi_currency': is_multi_currency, 'reserved': amount, 'settlement_amount': settlement_amount}}

    def _get_reserved(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            for l in voucher.line_dr_ids:
                debit += l.amount
            for l in voucher.line_cr_ids:
                credit += l.amount
            res[voucher.id] =  abs(credit - debit)
        return res
        
    def _get_settlement_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            for l in voucher.line_dr_ids:
                debit += l.amount_unreconciled
            for l in voucher.line_cr_ids:
                credit += l.amount_unreconciled
            res[voucher.id] =  abs(credit - debit)
        return res
        
    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            for l in voucher.line_dr_ids:
                debit += l.amount
            for l in voucher.line_cr_ids:
                credit += l.amount
            res[voucher.id] =  abs(voucher.reserved - abs(credit - debit))
        return res
    
    def _paid_amount_in_company_currency(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        ctx = context.copy()
        for v in self.browse(cr, uid, ids, context=context):
            ctx.update({'date': v.date})
            #make a new call to browse in order to have the right date in the context, to get the right currency rate
            voucher = self.browse(cr, uid, v.id, context=ctx)
            ctx.update({
              'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,
              'voucher_special_currency_rate': voucher.currency_id.rate * voucher.payment_rate,})
            res[voucher.id] =  self.pool.get('res.currency').compute(cr, uid, voucher.currency_id.id, voucher.company_id.currency_id.id, voucher.amount, context=ctx)
        return res

    def _get_currency_help_label(self, cr, uid, currency_id, payment_rate, payment_rate_currency_id, context=None):
        """
        This function builds a string to help the users to understand the behavior of the payment rate fields they can specify on the voucher. 
        This string is only used to improve the usability in the voucher form view and has no other effect.

        :param currency_id: the voucher currency
        :type currency_id: integer
        :param payment_rate: the value of the payment_rate field of the voucher
        :type payment_rate: float
        :param payment_rate_currency_id: the value of the payment_rate_currency_id field of the voucher
        :type payment_rate_currency_id: integer
        :return: translated string giving a tip on what's the effect of the current payment rate specified
        :rtype: str
        """
        rml_parser = report_sxw.rml_parse(cr, uid, 'currency_help_label', context=context)
        currency_pool = self.pool.get('res.currency')
        currency_str = payment_rate_str = ''
        if currency_id:
            currency_str = rml_parser.formatLang(1, currency_obj=currency_pool.browse(cr, uid, currency_id, context=context))
        if payment_rate_currency_id:
            payment_rate_str  = rml_parser.formatLang(payment_rate, currency_obj=currency_pool.browse(cr, uid, payment_rate_currency_id, context=context))
        currency_help_label = _('At the operation date, the exchange rate was\n%s = %s') % (currency_str, payment_rate_str)
        return currency_help_label

    def _fnct_currency_help_label(self, cr, uid, ids, name, args, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            res[voucher.id] = self._get_currency_help_label(cr, uid, voucher.currency_id.id, voucher.payment_rate, voucher.payment_rate_currency_id.id, context=context)
        return res

    def onchange_rate(self, cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=None):
        res =  {'value': {'paid_amount_in_company_currency': amount, 'currency_help_label': self._get_currency_help_label(cr, uid, currency_id, rate, payment_rate_currency_id, context=context)}}
        if rate and amount and currency_id:
            company_currency = self.pool.get('res.company').browse(cr, uid, company_id, context=context).currency_id
            #context should contain the date, the payment currency and the payment rate specified on the voucher
            amount_in_company_currency = self.pool.get('res.currency').compute(cr, uid, currency_id, company_currency.id, amount, context=context)
            res['value']['paid_amount_in_company_currency'] = amount_in_company_currency
        return res

    def get_partner_id(self, cr, uid, employee_id, context=None):
        employee_pool = self.pool.get('hr.employee')
        if not employee_id:
            return False
        employee = employee_pool.browse(cr, uid, employee_id, context=context)
        partner_id = employee.address_home_id and employee.address_home_id.id or False
        return partner_id
    
#     def onchange_employee(self, cr, uid, ids, employee_id):
#         
#         try:
#         
#             employee_search = self.pool.get('hr.employee').search(cr, uid, [('id', '=', employee_id)])
#         
#             for onchange in self.pool.get('hr.employee').browse(cr, uid, employee_search):
#                 
#                 employee_partner = onchange.address_home_id.partner_id.id
#                 account_partner = onchange.address_home_id.partner_id.property_account_payable.id
#                 
#             return {'value':{'partner_id': employee_partner, 'account_id': account_partner}}
#         
#         except: 
#                
#             result = {}
#             
#             warning = {
#                     "title": ("The Employee not to set as Partner !"),
#                     "message": ("Please Set Employee Partner before ")
#                 }
#             
#             
#             return {'warning': warning, 'value':{'partner_id': result, 'account_id':result}}

    def onchange_employee_id(self, cr, uid, ids, employee_id, journal_id, amount, currency_id, ttype, date, context=None):
        if context is None:
            context = {}
        warning = {}
        result = {}
        warning_msgs = ''
        partner_id = self.get_partner_id(cr, uid, employee_id, context=context)

        if not partner_id and employee_id:
            warn_msg = _('Please Set Employee Partner before, \n fill in Home Address on the Employees Form.')
            warning_msgs += _("No Partner ! : \n") + warn_msg +"\n\n"

        if warning_msgs:
            warning = {
                       'title': _('The Employee not to set as Partner!'),
                       'message' : warning_msgs
                    }
            result['employee_id'] = False
            result['partner_id'] = False
            result['account_id'] = False
            result['line_dr_ids'] = False
            return {'value': result, 'warning': warning}
        
        result = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id=journal_id, amount=amount, currency_id=currency_id, ttype=ttype, date=date, context=context)
        return {'value': result['value'], 'warning': warning}

    def _compute_total_line(self, cr, uid, ids, name, args, context=None):
        rs_data = {}
        amount = 0.0
        for line in self.browse(cr, uid, ids, context=None)[0].line_dr_ids:
            res= {}
            amount += line.amount
            
        res['amount'] = amount
        rs_data[line.voucher_id.id] = res
        return rs_data

    _name = 'cash.settlement'
    _description = 'Accounting Voucher'
    _inherit = ['mail.thread']
    _order = "date desc, id desc"
#    _rec_name = 'number'
    _track = {
        'state': {
            'ad_cash_settlement.mt_settlement_state_change': lambda self, cr, uid, obj, ctx=None: True,
        },
    }
    
    _columns = {
        'type':fields.selection([
            ('sale','Sale'),
            ('purchase','Purchase'),
            ('payment','Payment'),
            ('receipt','Receipt'),
        ],'Default Type', readonly=True, states={'draft':[('readonly',False)]}),
        'name':fields.char('Memo', size=256, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'date':fields.date('Settlement Payment', required=False ,readonly=True, states={'approve_lv2':[('readonly',False),('required',True)]}, select=True, help="Effective date for accounting entries"),
        'receive_settle_date':fields.date('Settlement Receive', required=False ,readonly=True, states={'draft':[('readonly',False),('required',True)]}, select=True, help="Date when Cost Control receive Settlement "),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'account_id':fields.many2one('account.account', 'Account', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'line_ids':fields.one2many('cash.settlement.line','voucher_id','Voucher Lines', readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'line_cr_ids':fields.one2many('cash.settlement.line','voucher_id','Credits',
            domain=[('type','=','cr')], context={'default_type':'cr'}, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'line_dr_ids':fields.one2many('cash.settlement.line','voucher_id','Debits',
            domain=[('type','=','dr')], context={'default_type':'dr'}, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'narration':fields.text('Notes', readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'currency_id':fields.many2one('res.currency', 'Currency', readonly=False,required=True),
#        'currency_id': fields.related('journal_id','currency', type='many2one', relation='res.currency', string='Currency', store=True, readonly=True, states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, ),
        'state':fields.selection(
            [('draft','Open'),
             ('proforma','Pro-forma'),
             ('approve_lv2','Approve'),
             ('posted','Posted'),
             ('cancel','Cancelled')
            ], 'State', readonly=True, size=32,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Voucher. \
                        \n* The \'Pro-forma\' when voucher is in Pro-forma state,voucher does not have an voucher number. \
                        \n* The \'Posted\' state is used when user create voucher,a voucher number is generated and voucher entries are created in account \
                        \n* The \'Cancelled\' state is used when user cancel voucher.'),
#         'amount': fields.function(_compute_total_line, method=True, multi='dc', type='float', string='Total', store=True),
        'amount': fields.function(_get_reserved, method=True, string="Total", type='float', readonly=True),
        
        'tax_amount':fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}, help="Transaction reference number."),
        'number': fields.char('Number', size=32, readonly=True,),
        'move_id':fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'audit': fields.related('move_id','to_check', type='boolean', relation='account.move', string='Audit Complete ?'),
        'pay_now':fields.selection([
            ('pay_now','Pay Directly'),
            ('pay_later','Pay Later or Group Funds'),
        ],'Payment', select=True, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'tax_id':fields.many2one('account.tax', 'Tax', readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'pre_line':fields.boolean('Previous Payments ?', required=False),
        'date_due': fields.date('Due Date', readonly=True, select=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'payment_option':fields.selection([
                                           ('without_writeoff', 'Keep Open'),
                                           ('with_writeoff', 'Reconcile with Write-Off'),
                                           ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)], 'approve_lv2':[('readonly',False)]}),
        'writeoff_acc_id': fields.many2one('account.account', 'Write-Off account', readonly=True, states={'draft': [('readonly', False)], 'approve_lv2':[('readonly',False)]}),
        'comment': fields.char('Write-Off Comment', size=64, required=True, readonly=True, states={'draft': [('readonly', False)], 'approve_lv2':[('readonly',False)]}),
        'analytic_id': fields.many2one('account.analytic.account','Write-Off Analytic Account', readonly=True, states={'draft': [('readonly', False)], 'approve_lv2':[('readonly',False)]}),
        'writeoff_amount': fields.function(_get_writeoff_amount, method=True, string='Write-Off Amount', type='float', readonly=True),
        'payment_rate_currency_id': fields.many2one('res.currency', 'Payment Rate Currency', required=True, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
        'payment_rate': fields.float('Exchange Rate', digits=(12,6), required=True, readonly=True, states={'draft': [('readonly', False)], 'approve_lv2':[('readonly',False)]},
            help='The specific rate that will be used, in this voucher, between the selected currency (in \'Payment Rate Currency\' field)  and the voucher currency.'),
        'paid_amount_in_company_currency': fields.function(_paid_amount_in_company_currency, string='Paid Amount in Company Currency', type='float', readonly=True),
        'is_multi_currency': fields.boolean('Multi Currency Voucher', help='Fields with internal purpose only that depicts if the voucher is a multi currency one or not'),
        'currency_help_label': fields.function(_fnct_currency_help_label, type='text', string="Helping Sentence", help="This sentence helps you to know how to specify the payment rate by giving you the direct effect it has"), 
        'employee_id': fields.many2one("hr.employee", "Employee", required=True, readonly=True, states={'draft':[('readonly',False)], 'approve_lv2':[('readonly',False)]}),
#         'reserved' : fields.float("Reserved Amount", readonly=True),
        'reserved' : fields.function(_get_reserved, string="Reserved Amount", type='float', digits_compute=dp.get_precision('Account'), readonly=True),
        'account_advance_id':fields.many2one('account.account','Account', readonly=True,),
        'line_history_ids':fields.one2many('cash.advance.history','voucher_id','Voucher Lines', readonly=True,),
        'cash_advance_id': fields.many2one('cash.advance', 'Cash Advance ID', readonly=False),
        'cash_advance_ref': fields.char('Advance Ref.Number', size=32, readonly=True),
        'date_req': fields.date("Cash Advance Request Date", readonly=True),
        'settlement_check': fields.boolean('Settlement Check',help="Check after Corrected"),
        
#         "settlement_amount": fields.float('Settlement Amount', required=False, readonly=True, states={"approve_lv2":[("readonly", False),("required", True)]}),
        "settlement_amount": fields.function(_get_settlement_amount, method=True, string='Settlement Amount', type='float', readonly=True),
#         'settlement_journal_id':fields.many2one('account.journal', 'Settlement Method', required=False, readonly=True, states={'approve_lv2':[('readonly',False),('required',True)]}),
        
    }
    _defaults = {
        'period_id': _get_period,
        'partner_id': _get_partner,
        'journal_id':_get_journal,
        'currency_id': _get_currency,
        'reference': _get_reference,
        'narration':_get_narration,
        'amount': _get_amount,
        'type':_get_type,
        'state': 'draft',
        'pay_now': 'pay_later',
        'name': '',
        #'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'cash.settlement',context=c),
        'tax_id': _get_tax,
        'payment_option': 'without_writeoff',
        'comment': _('Write-Off'),
        'settlement_check': False,
        'receive_settle_date': fields.date.context_today,
    }
    
    def compute_tax(self, cr, uid, ids, context=None):
        tax_pool = self.pool.get('account.tax')
        partner_pool = self.pool.get('res.partner')
        position_pool = self.pool.get('account.fiscal.position')
        voucher_line_pool = self.pool.get('cash.settlement.line')
        voucher_pool = self.pool.get('cash.settlement')
        if context is None: context = {}

        for voucher in voucher_pool.browse(cr, uid, ids, context=context):
            voucher_amount = 0.0
            for line in voucher.line_ids:
                voucher_amount += line.untax_amount or line.amount
                line.amount = line.untax_amount or line.amount
                voucher_line_pool.write(cr, uid, [line.id], {'amount':line.amount, 'untax_amount':line.untax_amount})

            if not voucher.tax_id:
                self.write(cr, uid, [voucher.id], {'amount':voucher_amount, 'tax_amount':0.0})
                continue

            tax = [tax_pool.browse(cr, uid, voucher.tax_id.id, context=context)]
            partner = partner_pool.browse(cr, uid, voucher.partner_id.id, context=context) or False
            taxes = position_pool.map_tax(cr, uid, partner and partner.property_account_position or False, tax)
            tax = tax_pool.browse(cr, uid, taxes, context=context)

            total = voucher_amount
            total_tax = 0.0

            if not tax[0].price_include:
                for tax_line in tax_pool.compute_all(cr, uid, tax, voucher_amount, 1).get('taxes', []):
                    total_tax += tax_line.get('amount', 0.0)
                total += total_tax
            else:
                for line in voucher.line_ids:
                    line_total = 0.0
                    line_tax = 0.0

                    for tax_line in tax_pool.compute_all(cr, uid, tax, line.untax_amount or line.amount, 1).get('taxes', []):
                        line_tax += tax_line.get('amount', 0.0)
                        line_total += tax_line.get('price_unit')
                    total_tax += line_tax
                    untax_amount = line.untax_amount or line.amount
                    voucher_line_pool.write(cr, uid, [line.id], {'amount':line_total, 'untax_amount':untax_amount})

            self.write(cr, uid, [voucher.id], {'amount':total, 'tax_amount':total_tax})
        return True

    def onchange_date_2(self, cr, uid, ids, date, context=None):
        if date!='False':
            period =self.pool.get('account.period').find(cr,uid,dt=date)
            print "->>>>>>>>", period
            if period:
                return {'value':{'period_id':period[0]}}
        return {'value':{}}

    def onchange_price(self, cr, uid, ids, line_ids, tax_id, partner_id=False, context=None):
        tax_pool = self.pool.get('account.tax')
        partner_pool = self.pool.get('res.partner')
        position_pool = self.pool.get('account.fiscal.position')
        res = {
            'tax_amount': False,
            'amount': False,
        }
        voucher_total = 0.0
        voucher_line_ids = []

        total = 0.0
        total_tax = 0.0
        for line in line_ids:
            line_amount = 0.0
            line_amount = line[2] and line[2].get('amount',0.0) or 0.0
            voucher_line_ids += [line[1]]
            voucher_total += line_amount

        total = voucher_total
        total_tax = 0.0
        if tax_id:
            tax = [tax_pool.browse(cr, uid, tax_id, context=context)]
            if partner_id:
                partner = partner_pool.browse(cr, uid, partner_id, context=context) or False
                taxes = position_pool.map_tax(cr, uid, partner and partner.property_account_position or False, tax)
                tax = tax_pool.browse(cr, uid, taxes, context=context)

            if not tax[0].price_include:
                for tax_line in tax_pool.compute_all(cr, uid, tax, voucher_total, 1).get('taxes', []):
                    total_tax += tax_line.get('amount')
                total += total_tax

        res.update({
            'amount':total or voucher_total,
            'tax_amount':total_tax
        })
        return {
            'value':res
        }

    def onchange_term_id(self, cr, uid, ids, term_id, amount):
        term_pool = self.pool.get('account.payment.term')
        terms = False
        due_date = False
        default = {'date_due':False}
        if term_id and amount:
            terms = term_pool.compute(cr, uid, term_id, amount)
        if terms:
            due_date = terms[-1][0]
            default.update({
                'date_due':due_date
            })
        return {'value':default}

    def onchange_journal_voucher(self, cr, uid, ids, line_ids=False, tax_id=False, price=0.0, partner_id=False, journal_id=False, ttype=False, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }

        if not partner_id or not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
            tr_type = 'purchase'
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'

        default['value']['account_id'] = account_id
        default['value']['type'] = ttype or tr_type

        vals = self.onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, context)
        default['value'].update(vals.get('value'))

        return default

    def recompute_payment_rate(self, cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=None):
        if context is None:
            context = {}
        #on change of the journal, we need to set also the default value for payment_rate and payment_rate_currency_id
        currency_obj = self.pool.get('res.currency')
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        company_id = journal.company_id.id
        payment_rate = 1.0
        currency_id = currency_id or journal.company_id.currency_id.id
        payment_rate_currency_id = currency_id
        ctx = context.copy()
        ctx.update({'date': date})
        o2m_to_loop = False
#         if ttype == 'receipt':
        if ttype == 'sale':
            o2m_to_loop = 'line_cr_ids'
#         elif ttype == 'payment':
        elif ttype == 'purchase':
            o2m_to_loop = 'line_dr_ids'
        if o2m_to_loop and 'value' in vals and o2m_to_loop in vals['value']:
            for voucher_line in vals['value'][o2m_to_loop]:
                if voucher_line['currency_id'] != currency_id:
                    # we take as default value for the payment_rate_currency_id, the currency of the first invoice that
                    # is not in the voucher currency
                    payment_rate_currency_id = voucher_line['currency_id']
                    tmp = currency_obj.browse(cr, uid, payment_rate_currency_id, context=ctx).rate
                    payment_rate = tmp / currency_obj.browse(cr, uid, currency_id, context=ctx).rate
                    break
        vals['value'].update({
            'payment_rate': payment_rate,
            'currency_id': currency_id,
            'payment_rate_currency_id': payment_rate_currency_id
        })
        #read the voucher rate with the right date in the context
        voucher_rate = self.pool.get('res.currency').read(cr, uid, currency_id, ['rate'], context=ctx)['rate']
        ctx.update({
            'voucher_special_currency_rate': payment_rate * voucher_rate,
            'voucher_special_currency': payment_rate_currency_id})
        res = self.onchange_rate(cr, uid, ids, payment_rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in res.keys():
            vals[key].update(res[key])
        return vals

    def basic_onchange_partner(self, cr, uid, ids, partner_id, journal_id, ttype, context=None):
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        res = {'value': {'partner_id': False, 'account_id': False}}  #add value for partner_id
        if not partner_id or not journal_id:
            return res

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
#         if journal.type in ('sale','sale_refund'):
#             account_id = partner.property_account_receivable.id
#         elif journal.type in ('purchase', 'purchase_refund','expense'):
#             account_id = partner.property_account_payable.id
        if partner.account_balance_id:
            account_id = partner.account_balance_id.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        res['value']['partner_id'] = partner_id  #add value for partner_id
        res['value']['account_id'] = account_id
        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        if not journal_id:
            return {}
        if context is None:
            context = {}
        #TODO: comment me and use me directly in the sales/purchases views
        res = self.basic_onchange_partner(cr, uid, ids, partner_id, journal_id, ttype, context=context)
        if ttype not in ['sale', 'purchase']:
            return res
        ctx = context.copy()
        # not passing the payment_rate currency and the payment_rate in the context but it's ok because they are reset in recompute_payment_rate
        ctx.update({'date': date})
        vals = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
        vals2 = self.recompute_payment_rate(cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=context)
        for key in vals.keys():
            res[key].update(vals[key])
        for key in vals2.keys():
            res[key].update(vals2[key])
        #TODO: can probably be removed now
        #TODO: onchange_partner_id() should not returns [pre_line, line_dr_ids, payment_rate...] for type sale, and not 
        # [pre_line, line_cr_ids, payment_rate...] for type purchase.
        # We should definitively split account.voucher object in two and make distinct on_change functions. In the 
        # meanwhile, bellow lines must be there because the fields aren't present in the view, what crashes if the 
        # onchange returns a value for them
        if ttype == 'sale':
            # del(res['value']['line_dr_ids'])
            # del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        elif ttype == 'purchase':
            # del(res['value']['line_cr_ids'])
            # del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        return res

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
                    if amount_residual_currency <= 0:
                        return True
                else:
                    if amount_residual <= 0:
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
#         account_type = 'receivable'
#         if ttype == 'payment':
        account_type = 'other'
        if ttype == 'purchase':
            # account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
#             account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id),('account_id.reconcile','=',True)], context=context)
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
            amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, line.id, context=context)
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:
            amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, line.id, context=context)

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.name,
                'type': line.credit and 'cr' or 'dr',
                'move_line_id':line.id,
                'amount_currency_original':line.currency_id and line.amount_currency or 0.0,
                'currency_original':line.currency_id and line.currency_id.id or False,
#                 'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(price), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            price -= rs['amount']
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

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'purchase' and len(default['value']['line_cr_ids']) > 0:
                print "::::::::::::::::::::::::::::::::: disini 1"
                default['value']['pre_line'] = True
            elif ttype == 'sale' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = True
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>>", default
        return default

    def onchange_payment_rate_currency(self, cr, uid, ids, currency_id, payment_rate, payment_rate_currency_id, date, amount, company_id, context=None):
        if context is None:
            context = {}
        res = {'value': {}}
        if currency_id:
            #set the default payment rate of the voucher and compute the paid amount in company currency
            ctx = context.copy()
            ctx.update({'date': date})
            #read the voucher rate with the right date in the context
            voucher_rate = self.pool.get('res.currency').read(cr, uid, currency_id, ['rate'], context=ctx)['rate']
            ctx.update({
                'voucher_special_currency_rate': payment_rate * voucher_rate, 
                'voucher_special_currency': payment_rate_currency_id})
            vals = self.onchange_rate(cr, uid, ids, payment_rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
            for key in vals.keys():
                res[key].update(vals[key])
        return res

    def onchange_date(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        @param date: latest value from user input for field date
        @param args: other arguments
        @param context: context arguments, like lang, time zone
        @return: Returns a dict which contains new values, and context
        """
        if context is None: context = {}
        period_pool = self.pool.get('account.period')
        res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        if context.get('invoice_id', False):
            company_id = self.pool.get('account.invoice').browse(cr, uid, context['invoice_id'], context=context).company_id.id
            context.update({'company_id': company_id})
        pids = period_pool.find(cr, uid, date, context=context)
        if pids:
            if not 'value' in res:
                res['value'] = {}
            res['value'].update({'period_id':pids[0]})
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, context=None):
        if context is None:
            context = {}
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        tax_id = False
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id

        vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
        vals['value'].update({'tax_id':tax_id})
        currency_id = journal.company_id.currency_id.id
        if journal.currency:
            currency_id = journal.currency.id
        #vals['value'].update({'currency_id':currency_id})

#         vals = {'value':{} }
#         if ttype in ('sale', 'purchase'):
#             vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
#             vals['value'].update({'tax_id':tax_id,'amount': amount})
#         currency_id = False
#         if journal.currency:
#             currency_id = journal.currency.id
#         else:
#             currency_id = journal.company_id.currency_id.id
#         vals['value'].update({'currency_id': currency_id})
#         #in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
#         #without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
#         #this common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
#         if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
#             vals['value']['amount'] = 0
#             amount = 0
#         res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
#         for key in res.keys():
#             vals[key].update(res[key])

        return vals

    def proforma_voucher(self, cr, uid, ids, context=None):
        self.action_move_line_create(cr, uid, ids, context=context)
        return True
    
    def proforma_voucher2(self, cr, uid, ids, context=None):
        self.action_move_line_create2(cr, uid, ids, context=context)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for voucher_id in ids:
            wf_service.trg_create(uid, 'cash.settlement', voucher_id, cr)
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def cancel_voucher(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        move_lines = []
        for voucher in self.browse(cr, uid, ids, context=context):
            # refresh to make sure you don't unlink an already removed move
            voucher.refresh()
            vmr=[]
            for line in voucher.move_ids:
                if line.reconcile_id:
                    move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
                    move_lines.remove(line.id)
                    vmr.append(line.reconcile_id.id)

            reconcile_pool.unlink(cr, uid, vmr)
            if len(move_lines) >= 2:
                move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete Voucher(s) which are already opened or paid !'))
        return super(cash_settlement, self).unlink(cr, uid, ids, context=context)

    # TODO: may be we can remove this method if not used anyware
    def onchange_payment(self, cr, uid, ids, pay_now, journal_id, partner_id, ttype='sale'):
        res = {}
        if not partner_id:
            return res
        res = {'account_id':False}
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        if pay_now == 'pay_later':
            partner = partner_pool.browse(cr, uid, partner_id)
            journal = journal_pool.browse(cr, uid, journal_id)
            if journal.type in ('sale','sale_refund'):
                account_id = partner.property_account_receivable.id
            elif journal.type in ('purchase', 'purchase_refund','expense'):
                account_id = partner.property_account_payable.id
            else:
                account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            res['account_id'] = account_id
        return {'value':res}
    
    def account_expense_check(self, cr, uid, ids):
        
        reserved_amount = self.browse(cr, uid,ids)
        for a in reserved_amount:
            reserved_amount = a.reserved
            amount = a.amount
        
        settlement_amount = abs(reserved_amount-amount)
        
        self.pool.get('cash.settlement').write(cr, uid, ids,{'settlement_amount':settlement_amount})
        
        cash_search = self.pool.get('cash.settlement.line').search(cr, uid, [('voucher_id','=',ids)])
        cash_browse = self.pool.get('cash.settlement.line').browse(cr, uid, cash_search)
        for cash_id in cash_browse:
            
            if not cash_id.account_id.id:
                raise osv.except_osv(_('Error !'), _('Please define a Expenses Account !'))
        
    def check_amount(self, cr, uid, ids, context=None):
        a = self.browse(cr, uid, ids)
        for b in a:
            total_amount = b.reserved
        cr.execute("SELECT SUM(coalesce(amount,0.0)) FROM cash_settlement_line WHERE voucher_id in (%s)"% (tuple(ids)))
        sum_amount = float(cr.fetchone()[0])
        if eval(str(total_amount)) != eval(str(sum_amount)):
            raise osv.except_osv(_('Error Amount !'), _('Please check your Total Amount !'))
    
    def _sel_context(self, cr, uid, voucher_id, context=None):
        """
        Select the context to use accordingly if it needs to be multicurrency or not.

        :param voucher_id: Id of the actual voucher
        :return: The returned context will be the same as given in parameter if the voucher currency is the same
                 than the company currency, otherwise it's a copy of the parameter with an extra key 'date' containing
                 the date of the voucher.
        :rtype: dict
        """
        company_currency = self._get_company_currency(cr, uid, voucher_id, context)
        current_currency = self._get_current_currency(cr, uid, voucher_id, context)
        if current_currency <> company_currency:
            context_multi_currency = context.copy()
            voucher = self.pool.get('cash.settlement').browse(cr, uid, voucher_id, context)
            context_multi_currency.update({'date': voucher.date})
            return context_multi_currency
        return context

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher = self.pool.get('cash.settlement').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher.type in ('purchase', 'payment'):
            credit = voucher.paid_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = voucher.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
                'name': voucher.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * voucher.amount or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due
            }
        return move_line

    def account_move_get(self, cr, uid, voucher_id, context=None):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        voucher = self.pool.get('cash.settlement').browse(cr,uid,voucher_id,context)
        if voucher.number:
            name = voucher.number
        elif voucher.journal_id.sequence_id:
            if not voucher.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id, 'date' : datetime.strptime(voucher.date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
            name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not voucher.reference:
            ref = name.replace('/','')
        else:
            ref = voucher.reference

        move = {
            'name': name,
            'journal_id': voucher.journal_id.id,
            'narration': voucher.narration,
            'date': voucher.date,
            'ref': ref,
            'period_id': voucher.period_id.id,
        }
        return move

    def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
        '''
        Prepare the two lines in company currency due to currency rate difference.

        :param line: browse record of the voucher.line for which we want to create currency rate difference accounting
            entries
        :param move_id: Account move wher the move lines will be.
        :param amount_residual: Amount to be posted.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
        :rtype: tuple of dict
        '''
        if amount_residual > 0:
            account_id = line.voucher_id.company_id.expense_currency_exchange_account_id
            if not account_id:
                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
        else:
            account_id = line.voucher_id.company_id.income_currency_exchange_account_id
            if not account_id:
                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
        # Even if the amount_currency is never filled, we need to pass the foreign currency because otherwise
        # the receivable/payable account may have a secondary currency, which render this field mandatory
        if line.account_id.currency_id:
            account_currency_id = line.account_id.currency_id.id
        else:
            account_currency_id = company_currency <> current_currency and current_currency or False
        move_line = {
            'journal_id': line.voucher_id.journal_id.id,
            'period_id': line.voucher_id.period_id.id,
            'name': _('change')+': '+(line.move_line_id.name or '/'),
            'account_id': line.voucher_id.account_id.id,
            'move_id': move_id,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': account_currency_id,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': amount_residual > 0 and amount_residual or 0.0,
            'debit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.voucher_id.date,
        }
        move_line_counterpart = {
            'journal_id': line.voucher_id.journal_id.id,
            'period_id': line.voucher_id.period_id.id,
            'name': _('change')+': '+(line.move_line_id.name or '/'),
            'account_id': account_id.id,
            'move_id': move_id,
            'amount_currency': 0.0,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': account_currency_id,
            'quantity': 1,
            'debit': amount_residual > 0 and amount_residual or 0.0,
            'credit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.voucher_id.date,
        }
        return (move_line, move_line_counterpart)

    def _convert_amount(self, cr, uid, amount, voucher_id, context=None):
        '''
        This function convert the amount given in company currency. It takes either the rate in the voucher (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.

        :param amount: float. The amount to convert
        :param voucher: id of the voucher on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
            field in order to select the good rate to use.
        :return: the amount in the currency of the voucher's company
        :rtype: float
        '''
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        voucher = self.browse(cr, uid, voucher_id, context=context)
        return currency_obj.compute(cr, uid, voucher.currency_id.id, voucher.company_id.currency_id.id, amount, context=context)

    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []
        move_lines_exp = []

        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('cash.settlement').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            amount_residual_currency, amount_residual = move_line_obj.get_amount_residual(cr, uid, line.move_line_id and line.move_line_id.id, context=context)
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The advance you are willing to settle is not valid anymore."))
                sign = voucher.type in ('payment', 'purchase') and 1 or -1
                currency_rate_difference = sign * (amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    sign = voucher.type in ('payment', 'purchase') and -1 or 1
                    foreign_currency_diff = sign * amount_residual_currency + amount_currency

            move_line['amount_currency'] = amount_currency
            move_lines_exp.append(move_line)
            # voucher_line_exp = move_line_obj.create(cr, uid, move_line)

            move_line_adv = move_line.copy()
            move_line_adv['debit'] = move_line.get('credit',0.0)
            move_line_adv['credit'] = move_line['debit']
            move_line_adv['amount_currency'] = amount_currency and -1*amount_currency or 0.0
            move_line_adv['account_id'] = line.move_line_id.account_id.id
            move_line_adv['name'] = line.move_line_id.name or '/'
            voucher_line_adv = move_line_obj.create(cr, uid, move_line_adv)

            rec_ids = [voucher_line_adv, line.move_line_id.id]
            
            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        group=True
        grouped_move_lines_exp = self.group_lines(cr, uid, move_lines_exp, group)
        for line in grouped_move_lines_exp:
            move_line_obj.create(cr, uid, line, context)
        return (tot_line, rec_lst_ids)

    def group_lines(self, cr, uid, line, group=None):
        if group:
            line2 = {}
            i = 0
            for l in line:
                key="%s-%s"%(l['account_id'],l['currency_id'])

                if key in line2:
                    am = line2[key]['debit'] - line2[key]['credit'] + (l['debit'] - l['credit'])
                    amt_currency = line2[key]['amount_currency'] + l['amount_currency']
                    line2[key]['amount_currency'] = amt_currency
                    line2[key]['debit'] = (am > 0) and am or 0.0
                    line2[key]['credit'] = (am < 0) and -am or 0.0
                else:
                    line2[key] = l
            line = []
            for key, val in line2.items():
                line.append(val)
        return line

    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher = self.pool.get('cash.settlement').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
#             account_id = False
            account_id = voucher.partner_id.account_balance_id.id
            write_off_name = ''
            if voucher.payment_option == 'with_writeoff':
                account_id = voucher.writeoff_acc_id.id
                write_off_name = voucher.comment
#             elif voucher.type in ('sale', 'receipt'):
#                 account_id = voucher.partner_id.property_account_receivable.id
#             else:
#                 account_id = voucher.partner_id.property_account_payable.id
            sign = voucher.type == 'payment' and -1 or 1
            move_line = {
                'name': write_off_name or name,
                'account_id': account_id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'date': voucher.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or False,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
            }

        return move_line

    def _get_company_currency(self, cr, uid, voucher_id, context=None):
        '''
        Get the currency of the actual company.

        :param voucher_id: Id of the voucher what i want to obtain company currency.
        :return: currency id of the company of the voucher
        :rtype: int
        '''
        return self.pool.get('cash.settlement').browse(cr,uid,voucher_id,context).journal_id.company_id.currency_id.id

    def _get_current_currency(self, cr, uid, voucher_id, context=None):
        '''
        Get the currency of the voucher.

        :param voucher_id: Id of the voucher what i want to obtain current currency.
        :return: currency id of the voucher
        :rtype: int
        '''
        voucher = self.pool.get('cash.settlement').browse(cr,uid,voucher_id,context)
        return voucher.currency_id.id or self._get_company_currency(cr,uid,voucher.id,context)

    def action_move_line_create2(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            rec_list_ids = []
            
            # move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)            
            # move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            # line_total = move_line_brw.debit - move_line_brw.credit
            # if voucher.type == 'sale':
            #     line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # elif voucher.type == 'purchase':
            #     line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            first_move_line = self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context)
            line_total = first_move_line['debit'] - first_move_line['credit']
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
            
            # Create the writeoff line if needed
            # ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            # if ml_writeoff:
                # move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
        
#     def action_move_line_create2(self, cr, uid, ids, context=None):
# 
#         def _get_payment_term_lines(term_id, amount):
#             term_pool = self.pool.get('account.payment.term')
#             if term_id and amount:
#                 terms = term_pool.compute(cr, uid, term_id, amount)
#                 return terms
#             return False
#         if context is None:
#             context = {}
#         move_pool = self.pool.get('account.move')
#         move_line_pool = self.pool.get('account.move.line')
#         currency_pool = self.pool.get('res.currency')
#         tax_obj = self.pool.get('account.tax')
#         seq_obj = self.pool.get('ir.sequence')
#         for inv in self.browse(cr, uid, ids, context=context):
# 
#             if inv.move_id:
#                 continue
#             context_multi_currency = context.copy()
#             context_multi_currency.update({'date': inv.date})
# 
#             if inv.number:
#                 name = inv.number
#             elif inv.journal_id.sequence_id:
#                 name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
#             else:
#                 raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
#             if not inv.reference:
#                 ref = name.replace('/','')
#             else:
#                 ref = inv.reference
#  
#             move = {
#                 'name': name,
#                 'journal_id': inv.journal_id.id,
#                 'narration': inv.narration,
#                 'date': inv.date,
#                 'ref': ref,
#                 'period_id': inv.period_id and inv.period_id.id or False
#             }
#             move_id = move_pool.create(cr, uid, move)
# 
#             #create the first line manually
#             company_currency = inv.journal_id.company_id.currency_id.id
#             current_currency = inv.currency_id.id
#             debit = 0.0
#             credit = 0.0
#             # TODO: is there any other alternative then the voucher type ??
#             # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
#             if inv.type in ('purchase', 'payment'):
#                 context_multi_currency.update({'date': inv.date_req})
#                 credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
#                 
#             elif inv.type in ('sale', 'receipt'):
#                 debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
#                 
#             #credit = inv.reserved
#             
#             credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.reserved, context=context_multi_currency)
#             
#             if debit < 0:
#                 credit = -debit
#                 debit = 0.0
#             if credit < 0:
#                 debit = -credit
#                 credit = 0.0
#             
#             sign = debit - credit < 0 and -1 or 1
#            
#             #create the first line of the voucher
#             
#             cur_date = time.strftime('%Y-%m-%d')
#             
#             move_line = {
#                 'name': inv.name or '/',
#                 'debit': debit,
#                 'credit': credit,
#                 #'account_id': inv.account_id.id,
#                 'account_id': inv.account_advance_id.id,
#                 'move_id': move_id,
#                 'journal_id': inv.journal_id.id,
#                 'period_id': inv.period_id.id,
#                 'partner_id': inv.partner_id.id,
#                 'currency_id': company_currency <> current_currency and  current_currency or False,
#                 'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
#                 'date': inv.date,
#                 'date_maturity': inv.date_due
#             }
#             move_line_pool.create(cr, uid, move_line)
#             
#             print "inv.reserved :", inv.reserved
#             print "settlement_amount :", inv.settlement_amount
#             #balance_diff = inv.settlement_amount
#             
#             if inv.reserved < inv.amount:
#                 print "keluar Uang"
#                 xdebit = 0.0
#                 xcredit = inv.settlement_amount
#                 xcredit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.settlement_amount, context=context_multi_currency)
#                 balance_diff = -1 * inv.settlement_amount
#                 xaccount_id = inv.settlement_journal_id.default_credit_account_id.id
#                 
#             elif inv.reserved > inv.amount:
#                 print "Masuk Uang"
#                 xdebit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.settlement_amount, context=context_multi_currency)
#                 #xdebit = inv.settlement_amount
#                 xcredit = 0.0
#                 balance_diff = inv.settlement_amount
#                 xaccount_id = inv.settlement_journal_id.default_debit_account_id.id
#                 print "xaccount_id :", inv.settlement_journal_id.default_debit_account_id.id
#                 
#             else:
#                 print "Pas"
#                 xdebit = 0.0
#                 xcredit = 0.0
#                 balance_diff = inv.settlement_amount
#                 xaccount_id = inv.account_id.id
#                 print "xaccount_id :", xaccount_id
#                 
#                 
#             print "balance_diff :----------------------->>", balance_diff
#             move_line2 = {
#                 'name': inv.name or '/',
#                 'debit': xdebit,
#                 'credit': xcredit,
#                 #'account_id': inv.account_id.id,
#                 'account_id': xaccount_id,
#                 'move_id': move_id,
#                 'journal_id': inv.journal_id.id,
#                 'period_id': inv.period_id.id,
#                 'partner_id': inv.partner_id.id,
#                 'currency_id': company_currency <> current_currency and  current_currency or False,
#                 'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
#                 'date': inv.date,
#                 'date_maturity': inv.date_due
#             }
#             
#             move_line_pool.create(cr, uid, move_line2)
#             
#             rec_list_ids = []
#             line_total = debit - credit
#             if inv.type == 'sale':
#                 
#                 line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
#             elif inv.type == 'purchase':
#                 
#                 context_multi_currency.update({'date': inv.date})
#                 line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
# 
#             for line in inv.line_ids:
#                 #create one move line per voucher line where amount is not 0.0
#                 if not line.amount:
#                     continue
#                 #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
#                 if line.amount == line.amount_unreconciled:
#                    
#                     amount = line.move_line_id.amount_residual #residual amount in company currency
#                 else:
#                     
#                     amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
#                 move_line = {
#                     'journal_id': inv.journal_id.id,
#                     'period_id': inv.period_id.id,
#                     'name': line.name and line.name or '/',
#                     'account_id': line.account_id.id,
#                     'move_id': move_id,
#                     'partner_id': inv.partner_id.id,
#                     'currency_id': company_currency <> current_currency and current_currency or False,
#                     'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                     'quantity': 1,
#                     'credit': 0.0,
#                     'debit': 0.0,
#                     'date': inv.date
#                     
#                 }
#                 
#                 if amount < 0:
#                     amount = -amount
#                     if line.type == 'dr':
#                         line.type = 'cr'
#                     else:
#                         line.type = 'dr'
# 
#                 if (line.type=='dr'):
#                     line_total += amount
#                     move_line['debit'] = amount
#                 else:
#                     line_total -= amount
#                     move_line['credit'] = amount
#                     
#                 if inv.tax_id and inv.type in ('sale', 'purchase'):
#                     move_line.update({
#                         'account_tax_id': inv.tax_id.id,
#                     })
#                 if move_line.get('account_tax_id', False):
#                     tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
#                     if not (tax_data.base_code_id and tax_data.tax_code_id):
#                         raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
#                 sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
#                 move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
#                 voucher_line = move_line_pool.create(cr, uid, move_line)
#                 if line.move_line_id.id:
#                     rec_ids = [voucher_line, line.move_line_id.id]
#                     rec_list_ids.append(rec_ids)
# 
#             if inv.reserved == inv.amount and inv.settlement_amount != 0.0: 
#                 print 'inv.amount', inv.amount, inv.reserved, inv.settlement_amount, (inv.reserved == inv.amount and inv.settlement_amount != 0.0)
#                 # raise osv.except_osv(_('Writeoff Warning !'), _('Your Writeoff More than Rp.100,- !'))
#                 
# 
#             inv_currency_id = inv.currency_id or inv.journal_id.currency or inv.journal_id.company_id.currency_id
#             if not currency_pool.is_zero(cr, uid, inv_currency_id, line_total):
#                 diff = line_total + balance_diff
#                 print "Diff :", diff
#                 absolut_diff = abs(diff)
#                 print "absolut_diff :", absolut_diff
#                 
#                 print "inv.reservedxxxx :", inv.reserved
#                 print "inv.amountxxxx ::", inv.amount
#                 
#                 if absolut_diff > 100:
#                     #raise osv.except_osv(_('Writeoff Warning !'), _('%s   Your Writeoff More than Rp.100,- !'%(absolut_diff)))
#                     raise osv.except_osv(_('Writeoff Warning !'), _('Your Writeoff More than Rp.100,- !'))
#                 
#                 account_id = False
#                 if inv.payment_option == 'with_writeoff':
#                     account_id = inv.writeoff_acc_id.id
#                 elif inv.type in ('sale', 'receipt'):
#                     account_id = inv.account_advance_id.id
#                 else:
#                     account_id = inv.account_advance_id.id
#                     #account_balance_id = inv.partner_id.account_balance_id.id
#                     rounding_account_id = inv.company_id.rounding_account_id.id
#                 move_line = {
#                     'name': name,
#                     'account_id': rounding_account_id or account_id,
#                     
#                     #'account_id': account_id,
#                     'move_id': move_id,
#                     'partner_id': inv.partner_id.id,
#                     'date': inv.date,
#                     'credit': diff > 0 and diff or 0.0,
#                     'debit': diff < 0 and -diff or 0.0,
#                     #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
#                     #'currency_id': company_currency <> current_currency and current_currency or False,
#                 }
#                 
#                 if move_line['credit'] > 0 or move_line['debit'] > 0:
#                     print "tttt", move_line['credit']
#                     print "cccc", move_line['debit']
#                     move_line_pool.create(cr, uid, move_line)
#             self.write(cr, uid, [inv.id], {
#                 'move_id': move_id,
#                 'state': 'posted',
#                 'number': name,
#             })
#             move_pool.post(cr, uid, [move_id], context={})
#             for rec_ids in rec_list_ids:
#                 if len(rec_ids) >= 2:
#                     move_line_pool.reconcile_partial(cr, uid, rec_ids)
#         return True
    
    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'state': 'draft',
            'number': False,
            'move_id': False,
            'line_cr_ids': False,
            'line_dr_ids': False,
            'reference': False
        })
        if 'date' not in default:
            default['date'] = time.strftime('%Y-%m-%d')
        return super(cash_settlement, self).copy(cr, uid, id, default, context)

cash_settlement()

class cash_settlement_line(osv.osv):
    _name = 'cash.settlement.line'
    _description = 'Voucher Lines'
    _order = "move_line_id"

    def _compute_balance(self, cr, uid, ids, name, args, context=None):
#         currency_pool = self.pool.get('res.currency')
#         rs_data = {}
#         for line in self.browse(cr, uid, ids, context=context):
#             ctx = context.copy()
#             ctx.update({'date': line.voucher_id.date})
#             res = {}
#             company_currency = line.voucher_id.journal_id.company_id.currency_id.id
#             voucher_currency = line.voucher_id.currency_id.id
#             move_line = line.move_line_id or False
# 
#             if not move_line:
#                 res['amount_original'] = 0.0
#                 res['amount_unreconciled'] = 0.0
# 
#             elif move_line.currency_id:
#                 res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, move_line.amount_currency, context=ctx)
#             elif move_line and move_line.credit > 0:
#                 res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit, context=ctx)
#             else:
#                 res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.debit, context=ctx)
# 
#             if move_line:
#                 res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
#             rs_data[line.id] = res
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
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
            if move_line:
                amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, move_line.id, context=context)

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
            elif move_line.currency_id and voucher_currency==move_line.currency_id.id:
                res['amount_original'] = abs(move_line.amount_currency)
                res['amount_unreconciled'] = abs(amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(amount_residual), context=ctx)

            rs_data[line.id] = res
        return rs_data

    def _reconcile(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a voucher line. It's either the currency of the
        associated move line (if any) or the currency of the voucher or the company currency.
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = (line.amount == line.amount_unreconciled)
        return res

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
                if line.move_line_id.currency_id:
                    result[line.id]['amount_currency_original'] = line.move_line_id.amount_currency or 0.0
                    result[line.id]['currency_original'] = line.move_line_id.currency_id.id or False
        return result

    def _currency_id(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a voucher line. It's either the currency of the
        associated move line (if any) or the currency of the voucher or the company currency.
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            move_line = line.move_line_id
            if move_line:
                res[line.id] = move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id
            else:
                res[line.id] = line.voucher_id.currency_id and line.voucher_id.currency_id.id or line.voucher_id.company_id.currency_id.id
        return res

    _columns = {
        'voucher_id':fields.many2one('cash.settlement', 'Voucher', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'account_id':fields.many2one('account.account','Account', required=True),
        'partner_id':fields.related('voucher_id', 'partner_id', type='many2one', relation='res.partner', string='Partner'),
        'untax_amount':fields.float('Untax Amount'),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'reconcile': fields.boolean('Full Reconcile'),
        # 'reconcile': fields.function(_reconcile, string='Full Reconcile', type='boolean', store=True, readonly=True),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Cr/Dr'),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
        'amount_currency_original' : fields.function(_get_original_amount, multi='cash_settlement_line', type='float', string='Original Amount Currency'),
        'currency_original' : fields.function(_get_original_amount, multi='cash_settlement_line', type='many2one', obj='res.currency', string='Original Currency'),
        'date_original': fields.related('move_line_id','date', type='date', relation='account.move.line', string='Date', readonly=1),
        'date_due': fields.related('move_line_id','date_maturity', type='date', relation='account.move.line', string='Due Date', readonly=1),
        'amount_original': fields.function(_compute_balance, method=True, multi='dc', type='float', string='Original Amount', store=True),
        'amount_unreconciled': fields.function(_compute_balance, method=True, multi='dc', type='float', string='Open Balance', store=True),
        'company_id': fields.related('voucher_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
        'currency_id': fields.function(_currency_id, string='Currency', type='many2one', relation='res.currency', readonly=True),
    }
    _defaults = {
        'name': ''
    }

    def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
        vals = {'amount': amount}
        if reconcile:
            vals = { 'amount': amount_unreconciled}
        return {'value': vals}

    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
        vals = {}
        if amount:
            vals['reconcile'] = (amount == amount_unreconciled)
        return {'value': vals}

    def onchange_move_line_id(self, cr, user, ids, move_line_id, journal_id, context=None):
        """
        Returns a dict that contains new values and context

        @param move_line_id: latest value from user input for field move_line_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context = {}
        context_multi_currency = context.copy()
        
        res = {}
        move_line_pool = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        currency_pool = self.pool.get('res.currency')
        if not journal_id:
            return {'value':res}
        journal = journal_pool.browse(cr, user, journal_id, context=context)
        currency_id = journal.currency and journal.currency.id or journal.company_id.currency_id.id
        company_currency = journal.company_id.currency_id.id
        if move_line_id:
            move_line = move_line_pool.browse(cr, user, move_line_id, context=context)
            if move_line.credit:
                ttype = 'cr'
            else:
                ttype = 'dr'
            if move_line.currency_id and currency_id == move_line.currency_id.id:
                amount_original = abs(move_line.amount_currency)
            else:
                amount_original = currency_pool.compute(cr, user, company_currency, currency_id, move_line.credit or move_line.debit or 0.0, context=context_multi_currency)
            res.update({
#                 'account_id': move_line.account_id.id,
                'amount_original': amount_original,
                'type': ttype,
                'currency_id': move_line.currency_id and move_line.currency_id.id or company_currency
            })
        return {
            'value':res,
        }

    def default_get(self, cr, user, fields_list, context=None):
        """
        Returns default values for fields
        @param fields_list: list of fields, for which default values are required to be read
        @param context: context arguments, like lang, time zone

        @return: Returns a dict that contains default values for fields
        """
        if context is None:
            context = {}
        journal_id = context.get('journal_id', False)
        partner_id = context.get('partner_id', False)
        journal_pool = self.pool.get('account.journal')
        partner_pool = self.pool.get('res.partner')
        values = super(cash_settlement_line, self).default_get(cr, user, fields_list, context=context)
        if (not journal_id) or ('account_id' not in fields_list):
            return values
        journal = journal_pool.browse(cr, user, journal_id, context=context)
        account_id = False
        ttype = 'cr'
        if journal.type in ('sale', 'sale_refund'):
            account_id = journal.default_credit_account_id and journal.default_credit_account_id.id or False
            ttype = 'cr'
        elif journal.type in ('purchase', 'expense', 'purchase_refund'):
            account_id = journal.default_debit_account_id and journal.default_debit_account_id.id or False
            ttype = 'dr'
        elif partner_id:
            partner = partner_pool.browse(cr, user, partner_id, context=context)
            if context.get('type') == 'payment':
                ttype = 'dr'
                account_id = partner.property_account_payable.id
            elif context.get('type') == 'receipt':
                account_id = partner.property_account_receivable.id

        values.update({
            'account_id':account_id,
            'type':ttype
        })
        return values
cash_settlement_line()

class cash_advance_history(osv.osv):
    _name = 'cash.advance.history'
    
    _columns = {
                'voucher_id':fields.integer("id"),
                'name_history':fields.char('Description', size=256, readonly=True),
                'amount_history':fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True),
                }
    
cash_advance_history()

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