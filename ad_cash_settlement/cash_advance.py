#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Alam Dewata Utama, PT    
#   Copyright (C) 2010-2013 ADSOft (<http://www.adsoft.co.id>). 
#   All Rights Reserved
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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT


class cash_advance(osv.osv):

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
            return tax_id
        return False

    def _get_currency_base(self, cr, uid, context=None):
        
        currency_search = self.pool.get('res.currency').search(cr, uid, [('base', '=', True)])
        currency_browse = self.pool.get('res.currency').browse(cr, uid, currency_search)
        
        for cur_id in currency_browse:
            id_currency = cur_id.id
            
        #return id_currency
        
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
                result = mod_obj.get_object_reference(cr, uid, 'cash_advance', 'view_voucher_tree')
            elif view_type == 'form':
                if condition:
                    result = mod_obj.get_object_reference(cr, uid, 'cash_advance', 'view_advance_payment_form')
                else:
                    result = mod_obj.get_object_reference(cr, uid, 'cash_advance', 'view_vendor_payment_form')
            return result and result[1] or False

        if not view_id and context.get('invoice_type', False):
            view_id = get_res_id(view_type,context.get('invoice_type', False) in ('out_invoice', 'out_refund'))

        if not view_id and context.get('line_type', False):
            view_id = get_res_id(view_type,context.get('line_type', False) == 'customer')

        res = super(cash_advance, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='partner_id']")
        if context.get('type', 'sale') in ('purchase', 'payment'):
            for node in nodes:
                node.set('domain', "[('supplier', '=', True)]")
            res['arch'] = etree.tostring(doc)
        return res

    def _compute_writeoff_amount(self, cr, uid, line_dr_ids, line_cr_ids, amount):
        debit = credit = 0.0
        for l in line_dr_ids:
            debit += l['amount']
        for l in line_cr_ids:
            credit += l['amount']
        return abs(amount - abs(credit - debit))

    def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount):
        if not line_dr_ids and not line_cr_ids:
            return {'value':{}}
        line_dr_ids = [x[2] for x in line_dr_ids]
        line_cr_ids = [x[2] for x in line_cr_ids]
        return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount)}}

    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            for l in voucher.line_dr_ids:
                debit += l.amount
            for l in voucher.line_cr_ids:
                credit += l.amount
            res[voucher.id] =  abs(voucher.amount - abs(credit - debit))
        return res
    
    def get_partner_id(self, cr, uid, employee_id, context=None):
        employee_pool = self.pool.get('hr.employee')
        employee = employee_pool.browse(cr, uid, employee_id, context=context)
        partner_id = employee.address_home_id and employee.address_home_id.id or False
        return partner_id
    
    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        if not employee_id:
            return {}
        partner_pool = self.pool.get('res.partner')
        partner_id = self.get_partner_id(cr, uid, employee_id, context=context)
        if not partner_id:
            raise osv.except_osv(_('The Employee not to set as Partner!'), _('Please Set Employee Partner before, \n fill in Home Address on the Employees Form.'))
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_partner = False
        if partner:
            account_partner = partner.account_balance_id.id
        if not account_partner:
            raise osv.except_osv(_('Account Settlement Balance is not set!'), _('Please Set Account Settlement before, \n fill in Account Settlement on the Employees Form.'))
        return {'value':{'partner_id': partner_id, 'account_advance_id': account_partner}}

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        employee_id = vals.get('employee_id', False)
        if employee_id:
            self.onchange_employee(cr, uid, [], employee_id, context=context)
        return super(cash_advance, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        employee_id = vals.get('employee_id', self.browse(cr, uid, ids, context=context)[0].employee_id.id)
        self.onchange_employee(cr, uid, ids, employee_id, context=context)

        partner_id = self.get_partner_id(cr, uid, employee_id, context)
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        if partner:
            vals.update({
                'account_advance_id': partner.account_balance_id and partner.account_balance_id.id or False,
            })

        return super(cash_advance, self).write(cr, uid, ids, vals, context)

    def _compute_total_line(self, cr, uid, ids, name, args, context=None):
        rs_data={}
        res={}
        amount = 0.0
        for line in self.browse(cr, uid, ids, context=None)[0].line_dr_ids:
            amount += line.amount
            
        res['amount'] = amount
        rs_data[ids[0]] = res
        return rs_data

    _name = 'cash.advance'
    _description = 'Accounting Voucher'
    _inherit = ['mail.thread']
    _order = "date desc, id desc"
#    _rec_name = 'number'
    _track = {
        'state': {
            'ad_cash_settlement.mt_advance_state_change': lambda self, cr, uid, obj, ctx=None: True,
        },
    }
    
    _columns = {
        'type': fields.selection([
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ('payment', 'Payment'),
            ('receipt', 'Receipt')
            ], 'Default Type', readonly=True, states={'draft': [('readonly', False)]}),
        'name': fields.char('Memo', size=256, required=True ,readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Date', readonly=True, select=True, states={'draft': [('readonly', False)]}, help="Effective date for accounting entries"),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'account_id': fields.many2one('account.account', 'Account', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many('cash.advance.line', 'voucher_id', 'Voucher Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'line_cr_ids': fields.one2many('cash.advance.line', 'voucher_id', 'Credits',
            domain=[('type', '=', 'cr')], context={'default_type': 'cr'}, readonly=True, states={'draft': [('readonly', False)]}),
        'line_dr_ids': fields.one2many('cash.advance.line', 'voucher_id', 'Debits',
            domain=[('type', '=', 'dr')], context={'default_type': 'dr'}, readonly=True, states={'draft': [('readonly', False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'narration': fields.text('Notes', readonly=True, states={'draft': [('readonly', False)]}),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, states={'draft': [('readonly', False)]}),
#        'currency_id': fields.related('journal_id','currency', type='many2one', relation='res.currency', string='Currency', store=True, readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('approve', 'Approve'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
            ], 'State', readonly=True, size=32,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Voucher. \
                        \n* The \'Pro-forma\' when voucher is in Pro-forma state,voucher does not have an voucher number. \
                        \n* The \'Posted\' state is used when user create voucher,a voucher number is generated and voucher entries are created in account \
                        \n* The \'Cancelled\' state is used when user cancel voucher.'),
        ##############Change Type##############
        #'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'amount': fields.function(_compute_total_line, method=True, multi='dc', type='float', string='Total', store=True),
        ########################
        
        'tax_amount': fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft': [('readonly', False)]}, help="Transaction reference number."),
        'number': fields.char('Number', size=32, readonly=True,),
        'move_id':fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft': [('readonly', False)]}),
        'audit': fields.related('move_id','to_check', type='boolean', relation='account.move', string='Audit Complete ?'),
        'pay_now':fields.selection([
            ('pay_now', 'Pay Directly'),
            ('pay_later', 'Pay Later or Group Funds'),
            ], 'Payment', select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'tax_id': fields.many2one('account.tax', 'Tax', readonly=True, states={'draft': [('readonly', False)]}),
        'pre_line': fields.boolean('Previous Payments ?', required=False),
        'date_due': fields.date('Due Date', readonly=True, select=True, states={'draft': [('readonly', False)]}),
        'payment_option':fields.selection([
            ('without_writeoff', 'Keep Open'),
            ('with_writeoff', 'Reconcile with Write-Off'),
            ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'writeoff_acc_id': fields.many2one('account.account', 'Write-Off account', readonly=True, states={'draft': [('readonly', False)]}),
        'comment': fields.char('Write-Off Comment', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'analytic_id': fields.many2one('account.analytic.account','Write-Off Analytic Account', readonly=True, states={'draft': [('readonly', False)]}),
        'writeoff_amount': fields.function(_get_writeoff_amount, method=True, string='Write-Off Amount', type='float', readonly=True),
        'employee_id': fields.many2one("hr.employee", "Employee", required=True, readonly=True, states={"draft": [("readonly", False)], "approve": [("readonly", False)]}),
        'account_advance_id':fields.many2one('account.account', 'Advance Account', readonly=True),
        #'advance_currency': fields.many2one('res.currency', 'Currencies', required=True),
        
        #############################################
        'payment_adm': fields.selection([
            ('cash', 'Cash'),
            ('free_transfer', 'Non Payment Administration Transfer'),
            ('transfer', 'Transfer'),
            #('cheque','Cheque'),
            ],'Payment Method', readonly=True, select=True, states={'draft': [('readonly', False)]}),
        'adm_acc_id': fields.many2one('account.account', 'Account Adm', readonly=True, states={'draft': [('readonly', False)]}),
        'adm_comment': fields.char('Comment Adm', size=128, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'adm_amount': fields.float('Amount Adm', readonly=True, states={'draft': [('readonly', False)]}),
         'bank_id': fields.many2one("res.bank", "Bank", required=False, readonly=True, states={"draft": [("readonly", False)]}, select=2),
        'cheque_number': fields.char('Cheque No', size=128, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        "cheque_start_date": fields.date("Cheque Date", required=False, readonly=True, states={"draft": [("readonly", False)]}),
        "cheque_end_date": fields.date("Cheque Expire Date", required=False, readonly=True, states={"draft": [("readonly", False)]}),
        ##############################################
    
    }
    _defaults = {
        'period_id': _get_period,
        'partner_id': _get_partner,
        'journal_id':_get_journal,
        #INI yang Aslinya >>>>>>>>>>>
        'currency_id': _get_currency,
#         'currency_id': _get_currency_base,
        'reference': _get_reference,
        'narration':_get_narration,
        'amount': _get_amount,
        'type':_get_type,
        'state': 'draft',
        'pay_now': 'pay_later',
        'name': '',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'cash.advance', context=c),
        'tax_id': _get_tax,
        'payment_option': 'without_writeoff',
        'comment': _('Write-Off'),
        'payment_adm':"cash",
    }
    
    def compute_tax(self, cr, uid, ids, context=None):
        tax_pool = self.pool.get('account.tax')
        partner_pool = self.pool.get('res.partner')
        position_pool = self.pool.get('account.fiscal.position')
        voucher_line_pool = self.pool.get('cash.advance.line')
        voucher_pool = self.pool.get('cash.advance')
        if context is None: context = {}

        for voucher in voucher_pool.browse(cr, uid, ids, context=context):
            voucher_amount = 0.0
            for line in voucher.line_ids:
                voucher_amount += line.untax_amount or line.amount
                line.amount = line.untax_amount or line.amount
                voucher_line_pool.write(cr, uid, [line.id], {'amount': line.amount, 'untax_amount': line.untax_amount})

            if not voucher.tax_id:
                self.write(cr, uid, [voucher.id], {'amount': voucher_amount, 'tax_amount':0.0})
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
                    voucher_line_pool.write(cr, uid, [line.id], {'amount': line_total, 'untax_amount': untax_amount})

            self.write(cr, uid, [voucher.id], {'amount': total, 'tax_amount': total_tax})
        return True

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
            'amount': total or voucher_total,
            'tax_amount': total_tax
        })
        return {
            'value': res
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
                'date_due': due_date
            })
        return {'value': default}

    def onchange_journal_voucher(self, cr, uid, ids, line_ids=False, tax_id=False, price=0.0, partner_id=False, journal_id=False, ttype=False, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value': {},
        }

        if not partner_id or not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        tr_type = False
        if journal.type in ('sale', 'sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund', 'expense'):
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

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context = {}
        if not journal_id:
            return {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        line_pool = self.pool.get('cash.advance.line')
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        vals = self.onchange_journal(cr, uid, ids, journal_id, [], False, partner_id, context)
        vals = vals.get('value')
        currency_id = vals.get('currency_id', currency_id)
        default = {
            'value': {'line_ids': [], 'line_dr_ids': [], 'line_cr_ids': [], 'pre_line': False, 'currency_id': currency_id},
        }

        if not partner_id:
            return default

        if not partner_id and ids:
            line_ids = line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
            if line_ids:
                line_pool.unlink(cr, uid, line_ids)
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        if journal.type in ('sale', 'sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund', 'expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'

        if not context.get('move_line_ids', False):
            domain = [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)]
            if context.get('invoice_id', False):
                domain.append(('invoice', '=', context['invoice_id']))
            ids = move_line_pool.search(cr, uid, domain, context=context)
        else:
            ids = context['move_line_ids']
        ids.reverse()
        moves = move_line_pool.browse(cr, uid, ids, context=context)

        company_currency = journal.company_id.currency_id.id
        if company_currency != currency_id and ttype == 'payment':
            total_debit = currency_pool.compute(cr, uid, currency_id, company_currency, total_debit, context=context_multi_currency)
        elif company_currency != currency_id and ttype == 'receipt':
            total_credit = currency_pool.compute(cr, uid, currency_id, company_currency, total_credit, context=context_multi_currency)

        for line in moves:
            if line.credit and line.reconcile_partial_id and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and ttype == 'payment':
                continue
            total_credit += line.credit or 0.0
            total_debit += line.debit or 0.0
        for line in moves:
            if line.credit and line.reconcile_partial_id and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and ttype == 'payment':
                continue
            original_amount = line.credit or line.debit or 0.0
            amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, abs(line.amount_residual_currency), context=context_multi_currency)
            rs = {
                'name': line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id': line.id,
                'account_id': line.account_id.id,
                'amount_original': currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context=context_multi_currency),
                'date_original': line.date,
                'date_due': line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
            }

            if line.credit:
                amount = min(amount_unreconciled, currency_pool.compute(cr, uid, company_currency, currency_id, abs(total_debit), context=context_multi_currency))
                rs['amount'] = amount
                total_debit -= amount
            else:
                amount = min(amount_unreconciled, currency_pool.compute(cr, uid, company_currency, currency_id, abs(total_credit), context=context_multi_currency))
                rs['amount'] = amount
                total_credit -= amount

            default['value']['line_ids'].append(rs)
            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price)

        return default

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
            res['value'].update({'period_id': pids[0]})
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, context=None):
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
        vals['value'].update({'currency_id':currency_id})
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
            wf_service.trg_create(uid, 'cash.advance', voucher_id, cr)
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def cancel_voucher(self, cr, uid, ids, context=None):
        obj_settlement = self.pool.get('cash.settlement')
        
        settlement_search = obj_settlement.search(cr, uid, [('cash_advance_id', '=', ids)])
        settlement_browse = obj_settlement.browse(cr, uid, settlement_search)
        for a in settlement_browse:
            if a.state not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid action !'), _('Cannot cancel Cash Advance Request(s) which are Settlement already opened or paid !'))
            else:
                obj_settlement.unlink(cr, uid, settlement_search, context=context)
        
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')

        for voucher in self.browse(cr, uid, ids, context=context):
            recs = []
            for line in voucher.move_ids:
                if line.reconcile_id:
                    recs += [line.reconcile_id.id]
                if line.reconcile_partial_id:
                    recs += [line.reconcile_partial_id.id]

            reconcile_pool.unlink(cr, uid, recs)

            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state': 'cancel',
            'move_id': False,
        }
        self.write(cr, uid, ids, res)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete Voucher(s) which are already opened or paid !'))
        return super(cash_advance, self).unlink(cr, uid, ids, context=context)

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
            if journal.type in ('sale', 'sale_refund'):
                account_id = partner.property_account_receivable.id
            elif journal.type in ('purchase', 'purchase_refund','expense'):
                account_id = partner.property_account_payable.id
            else:
                account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            res['account_id'] = account_id
        return {'value': res}
    
    def check_amount(self, cr, uid, ids, context=None):
        self.onchange_employee(cr, uid, ids, self.browse(cr, uid, ids, context=context)[0].employee_id.id, context)
        a = self.browse(cr, uid, ids)
        for b in a:
            total_amount = b.amount
            
        cr.execute("SELECT SUM(amount) FROM cash_advance_line WHERE voucher_id in (%s)" %(tuple(ids)))
        sum_amount = cr.fetchone()[0]
        
        if total_amount != sum_amount:
            raise osv.except_osv(_('Error Amount !'), _('Please check your Total Amount !'))
    
    def action_move_line_create2(self, cr, uid, ids, context=None):
        
        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        if context is None:
            context = {}
        partner_pool = self.pool.get('res.partner')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        for inv in self.browse(cr, uid, ids, context=context):
            self.onchange_employee(cr, uid, ids, inv.employee_id.id, context=context)
    
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                date2 = datetime.strptime(inv.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id, context={'date':date2})
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
                
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
                
            #credit = 100
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            
            sign = debit - credit < 0 and -1 or 1
            
            #create the first line of the voucher
            move_line = {
                'name': inv.name or '/',
                'debit': debit,
                'credit': credit,
                #'account_id': inv.account_id.id,
                'account_id': inv.journal_id.default_credit_account_id.id,
                'move_id': move_id,
                'journal_id': inv.journal_id.id,
                'period_id': inv.period_id.id,
                'partner_id': inv.partner_id.id,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                'date': inv.date,
                'date_maturity': inv.date_due
            }
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            amount_total_debit = 0.0
            desc_merge = ''
            c = 1
            for line in inv.line_ids:
                if not line.amount:
                    continue
                
                #create one move line per voucher line where amount is not 0.0
                desc_merge += line.name and line.name + (c <> len(inv.line_ids) and ", " or "") or ""
                c += 1
                
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': desc_merge,
                    #'name': line.name and line.name or '/',
                    'account_id': inv.account_advance_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount
                
                amount_total_debit = amount_total_debit + move_line['debit']
                
#                if inv.tax_id and inv.type in ('sale', 'purchase'):
#                    move_line.update({
#                        'account_tax_id': inv.tax_id.id,
#                    })
#                if move_line.get('account_tax_id', False):
#                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
#                    if not (tax_data.base_code_id and tax_data.tax_code_id):
#                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
            move_line['account_id'] = inv.account_advance_id.id
            move_line['debit'] = amount_total_debit
            #DI Geser#
            voucher_line = move_line_pool.create(cr, uid, move_line)
            if line.move_line_id.id:
                rec_ids = [voucher_line, line.move_line_id.id]
                rec_list_ids.append(rec_ids)

            
        
            #----------------------tambah disini buat gbu-------------
            #print "pppppppppppppppp"
            diff_adm = inv.adm_amount
            if inv.payment_adm == 'transfer' or inv.payment_adm == 'cheque':
                debit_adm = currency_pool.compute(cr, uid, current_currency, company_currency, diff_adm, context=context_multi_currency)
                credit_adm = currency_pool.compute(cr, uid, current_currency, company_currency, diff_adm, context=context_multi_currency)
                sign_adm = debit_adm - credit_adm < 0 and -1 or 1
                if inv.payment_adm == 'transfer':
                    cost_name = inv.adm_comment
                else:
                    cost_name = 'Cheque Fee'
                    
                move_line_adm_c = {
                    'name': cost_name,
                    'account_id': inv.journal_id.default_credit_account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'debit': 0,# < 0 and -diff or 0.0,
                    'credit': credit_adm,#diff > 0 and diff or 0.0,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'amount_currency': company_currency <> current_currency and sign_adm * -diff_adm or 0.0,
                }
                account_id = inv.adm_acc_id.id
                move_line_adm_d = {
                    'name': cost_name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'debit': debit_adm,# < 0 and -diff or 0.0,
                    'credit': 0,#diff > 0 and diff or 0.0,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'amount_currency': company_currency <> current_currency and sign_adm * diff_adm or 0.0,
                }
                #print "xxxx3xxxx",move_line_adm_c
                #print "xxxx4xxxx",move_line_adm_d
                if diff_adm != 0:
                    move_line_pool.create(cr, uid, move_line_adm_c)
                    move_line_pool.create(cr, uid, move_line_adm_d)
            #------------------------------------------------------


            inv_currency_id = inv.currency_id or inv.journal_id.currency or inv.journal_id.company_id.currency_id
            if not currency_pool.is_zero(cr, uid, inv_currency_id, line_total):
                
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    account_id = inv.partner_id.property_account_receivable.id
                else:
                    account_id = inv.partner_id.property_account_payable.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                move_line_pool.create(cr, uid, move_line)
            self.write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        
        cash_advance = self.browse(cr, uid, ids)
        
        obj_cash_advance_line = self.pool.get('cash.advance.line')
        
        cash_advance_line_search = obj_cash_advance_line.search(cr, uid, [('voucher_id','=',ids)])
        cash_advance_line_browse = obj_cash_advance_line.browse(cr, uid, cash_advance_line_search)
        
        lines = []
        lines_history = []
        
        for advance_line in cash_advance_line_browse:
            vals_line={
                        "name": advance_line.name,
                        #"account_id": inv.account_advance_id.id,
                        #"account_id": advance_line.account_id.id,
                        #"account_id": line.account_id.id,
                        "amount": advance_line.amount,
                        #"quantity": line.quantity,
                        #"invoice_line_tax_id": [(6,0,[t.id for t in line.taxes])],
                        #"product_id": line.product_id.id,
            }
            lines.append((0,0,vals_line))
            
            vals_history_line={
                        "name_history": advance_line.name,
                        #"account_id": advance_line.account_id.id,
                        #"account_id": line.account_id.id,
                        "amount_history": advance_line.amount,
                        #"quantity": line.quantity,
                        #"invoice_line_tax_id": [(6,0,[t.id for t in line.taxes])],
                        #"product_id": line.product_id.id,
            }
            lines_history.append((0,0,vals_history_line))
        
        obj_cash_settlement = self.pool.get('cash.settlement')
        
        req_date = inv.date
        
        vals={
                "employee_id": inv.employee_id.id,
                "partner_id": inv.partner_id.id,
                #"journal_id": inv.journal_id.id,
                "type": 'purchase',
                "line_dr_ids": lines,
                "line_history_ids": lines_history,
                #"account_id": 191,
                "account_advance_id": inv.account_advance_id.id,
                "account_id": inv.account_advance_id.id,
                "name": inv.name,
                "amount":inv.amount,
                "reserved": inv.amount,
                "date_req": req_date,
                "cash_advance_ref": name,
                "cash_advance_id": inv.id,
                "currency_id" : inv.currency_id.id,
                #"amount":total,
                #"account_expense_id":account_journal_debit,
                #"origin": replen.name,
                #"state": "approved",
                #partner.property_account_payable.id
                #partner.id
        }
        
#         cash_settlement = obj_cash_settlement.create(cr, uid, vals)
        return True

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
        return super(cash_advance, self).copy(cr, uid, id, default, context)

cash_advance()

class cash_advance_line(osv.osv):
    _name = 'cash.advance.line'
    _description = 'Voucher Lines'
    _order = "move_line_id"

    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.voucher_id.date})
            res = {}
            company_currency = line.voucher_id.journal_id.company_id.currency_id.id
            voucher_currency = line.voucher_id.currency_id.id
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0

            elif move_line.currency_id:
                res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, move_line.amount_currency, context=ctx)
            elif move_line and move_line.credit > 0:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit, context=ctx)
            else:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.debit, context=ctx)

            if move_line:
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
            rs_data[line.id] = res
        return rs_data

    _columns = {
        'voucher_id':fields.many2one('cash.advance', 'Voucher', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'account_id':fields.many2one('account.account','Account', required=False),
        'partner_id':fields.related('voucher_id', 'partner_id', type='many2one', relation='res.partner', string='Partner'),
        'untax_amount':fields.float('Untax Amount'),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Cr/Dr'),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
        'date_original': fields.related('move_line_id','date', type='date', relation='account.move.line', string='Date', readonly=1),
        'date_due': fields.related('move_line_id','date_maturity', type='date', relation='account.move.line', string='Due Date', readonly=1),
        'amount_original': fields.function(_compute_balance, method=True, multi='dc', type='float', string='Original Amount', store=True),
        'amount_unreconciled': fields.function(_compute_balance, method=True, multi='dc', type='float', string='Open Balance', store=True),
        'company_id': fields.related('voucher_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
        
    }
    _defaults = {
        'name': ''
    }

    def onchange_move_line_id(self, cr, user, ids, move_line_id, context=None):
        """
        Returns a dict that contains new values and context

        @param move_line_id: latest value from user input for field move_line_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        res = {}
        move_line_pool = self.pool.get('account.move.line')
        if move_line_id:
            move_line = move_line_pool.browse(cr, user, move_line_id, context=context)
            if move_line.credit:
                ttype = 'dr'
            else:
                ttype = 'cr'
            account_id = move_line.account_id.id
            res.update({
                'account_id':account_id,
                'type': ttype
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
        values = super(cash_advance_line, self).default_get(cr, user, fields_list, context=context)
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
cash_advance_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: