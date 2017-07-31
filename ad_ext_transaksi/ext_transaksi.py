import time
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools
import urllib3
from lxml import etree

class ext_transaksi(osv.osv):
    _name = "ext.transaksi"
    _description = "Extra Transaksi"

    def _get_move_line_id(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for ext_trans in self.browse(cr, uid, ids, context=context):
            if ext_trans.advance_move_id:
                for move_line in ext_trans.advance_move_id.line_id:
                    if move_line.account_id.type=='receivable' or move_line.account_id.type=='payable':
                        res[ext_trans.id]=move_line.id
        return res
    
    def _get_create_uid(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        ctx = context.copy()
        for v in self.browse(cr, uid, ids, context=context):
            cr.execute("select create_uid from ext_transaksi where id='%s'"%v.id)
            cr_id = cr.fetchone()[0]
            res[v.id] = cr_id
        return res

    def _get_balance(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        ctx = context.copy()
        for v in self.browse(cr, uid, ids, context=context):
            total_balance = 0.0
            for line in v.ext_line:
                total_balance += line.debit-line.credit
            res[v.id] = total_balance
        return res

    def _get_tax_balance(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        ctx = context.copy()
        for v in self.browse(cr, uid, ids, context=context):
            total_balance = 0.0
            for line in v.tax_ext_line:
                total_balance += line.debit-line.credit
            res[v.id] = total_balance
        return res

    def _get_gain_loss_account(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if uid:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            if user.company_id and user.company_id.expense_currency_exchange_account_id:
                return user.company_id.expense_currency_exchange_account_id.id
            else:
                return False
        else:
            return False

    _columns = {
        'name' : fields.char('Transaction', 64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'ext_line' : fields.one2many('ext.transaksi.line', 'ext_transaksi_id','Lines', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'tax_ext_line' : fields.one2many('ext.transaksi.line', 'tax_ext_transaksi_id','Tax Lines', required=False, readonly=False),
        'journal_id': fields.many2one('account.journal', 'Journal', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'ref': fields.char('Reference', size=64, readonly=True, states={'draft':[('readonly',False)]}),
        'number': fields.char('Number', size=32, readonly=True, states={'draft':[('readonly',False)]}),
        'request_date': fields.date('Request Date', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'due_date': fields.date('Due Date', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'date': fields.date('Posting Date', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'payment_date': fields.date('Payment Date', required=False, readonly=True),
        'move_id':fields.many2one('account.move', 'Account Entry',readonly=True, states={'draft':[('readonly',False)]}),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True, states={'draft':[('readonly',False)]}),
        'currency_id':fields.many2one('res.currency', 'Currency', readonly=True, states={'draft':[('readonly',False)]}),
        'force_period': fields.many2one('account.period','Force Period', required=False, readonly=True, states={'draft':[('readonly',False),('required',True)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
        'state':fields.selection([('draft','Draft'), ('posted','Posted')], 'State', readonly=True),
        'tax_state':fields.selection([('draft','Draft'), ('posted','Posted')], 'Tax State', readonly=True),
        'tax_move_id':fields.many2one('account.move', 'Account Entry',readonly=True, states={'draft':[('readonly',False)]}),
        'tax_move_ids': fields.related('tax_move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True, states={'draft':[('readonly',False)]}),
        'group_by_account' : fields.boolean('Group By Account',help='Group Ext Transaction Lines base for the same account and type of charge'),
        #'department_id': fields.many2one('hr.department','Department', readonly=True, states={'draft':[('readonly',False)]})
        #'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'advance_id' : fields.many2one('account.advance.payment','Advance',readonly=True, states={'draft':[('readonly',False)]}),
        'advance_move_id' : fields.related('advance_id','move_id',string='Advance Journal Entries',readonly=True, type='many2one', relation='account.move'),
        'advance_move_line_id' : fields.function(_get_move_line_id,type='many2one',obj='account.move.line',string='Advance Move Line'),
        'use_advance' : fields.boolean('Use Advance Payment',readonly=True, states={'draft':[('readonly',False)]}),
        'is_bpa' : fields.boolean('Is BPA?',readonly=True, states={'draft':[('readonly',False)]}),
        'paid_amount': fields.float('Paid Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}, required=True),
        'is_once' : fields.boolean('Posted Once'),
        'tax_paid_amount': fields.float('Tax Paid Amount', digits_compute=dp.get_precision('Account'), required=True),
        'type_transaction':fields.selection([('payment','Payment'), ('receipt','Receipt'),('others','Others')], 'Type Transaction', readonly=True),
        "create_by" : fields.function(_get_create_uid, type='many2one', obj='res.users', string='Create By', store=True),
        "total_balance" : fields.function(_get_balance, type='float', string='Total Balance'),
        "tax_total_balance" : fields.function(_get_tax_balance, type='float', string='Total Balance'),
        'rounding_account_id' : fields.many2one('account.account', 'Rounding Account', required=False, domain=[('type','!=','view')]),
        'default_debit_account_id' : fields.many2one('account.account', 'Default Debit Account', required=False, domain=[('type','!=','view')]),
        'default_credit_account_id' : fields.many2one('account.account', 'Default Credit Account', required=False, domain=[('type','!=','view')]),
        'qr_urls' :  fields.text("Efaktur URLs", readonly=False, states={'draft':[('readonly',False)]}),
        'faktur_pajak_lines' : fields.one2many('efaktur.head','related_ext_transaksi_id','Faktur Pajak Lines', readonly=False),
    }
    
    _defaults = {
        'rounding_account_id': _get_gain_loss_account,
        'paid_amount':0.0,
        'tax_paid_amount':0.0,
        'state' : 'draft',
        'tax_state' : 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'ext.transaksi', context=c),
        'type_transaction' :lambda self,cr,uid,context:context.get('type_transaction','payment'),
    }
    
    _order = "id desc"

    def auto_balance(self, cr, uid, id, move_id, context=None):

        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        sum_debit   = 0.0
        sum_credit  = 0.0
        move = move_pool.browse(cr, uid, move_id, context=None)
        for line in move.line_id:
            sum_debit   += line.debit
            sum_credit  += line.credit

        diff = sum_debit - sum_credit
        if abs(diff) < 0.99:
            ext_pay = self.browse(cr, uid, id)
            move_line = {
                'move_id':move_id,
                'name': 'Rounding Difference',
                'debit': diff < 0 and abs(diff) or 0.0,
                'credit': diff > 0 and abs(diff) or 0.0,
                'account_id': ext_pay.rounding_account_id and ext_pay.rounding_account_id.id or False,
                'other_ref' : ext_pay.ref or '',
                'journal_id': ext_pay.journal_id.id,
                'period_id': ext_pay.force_period.id,
                'date': ext_pay.date!='False' and ext_pay.date or time.strftime("%Y-%m-%d"),
                'currency_id' : ext_pay.currency_id and ext_pay.currency_id.id!=ext_pay.company_id.currency_id.id and ext_pay.currency_id.id or False,
                'amount_currency' : 0.0,
            }
            move_line_pool.create(cr, uid, move_line)

        return True

    def group_lines(self, cr, uid, line, group=None):
        if group:
            line2 = {}
            i = 0
            for l in line:
                # if l['type_of_charge']:
                    key="%s"%(l['account_id'])

                    if key in line2:
                        am = line2[key]['debit'] - line2[key]['credit'] + (l['debit'] - l['credit'])
                        amt_currency = line2[key]['amount_currency'] + l['amount_currency']
                        line2[key]['amount_currency'] = amt_currency
                        line2[key]['debit'] = (am > 0) and am or 0.0
                        line2[key]['credit'] = (am < 0) and -am or 0.0
                    else:
                        line2[key] = l
                # else:
                    # i+=1
                    # key="non-"+str(i)
                    # line2[key]=l

            line = []
            for key, val in line2.items():
                line.append(val)
        return line

    def group_ext_lines(self, cr, uid, line, group=None):
        line_result = []
        if group:
            line2 = {}
            i = 0
            for l in line:
                key="%s"%(l['account_id'])
                if key not in line2:
                    line2.update({key:{}})
                    line2[key].update({
                    'name' : l.name or '/',
                    'debit' : 0.0,
                    'credit' : 0.0,
                    'account_id' : l.account_id.id,
                    'other_ref' : l.reference or '',
                    'analytic_account_id' : l.analytic_account_id and l.analytic_account_id.id or False,
                    'partner_id' : l.partner_id and l.partner_id.id or False,
                    })
                line2[key]['debit'] += l.debit
                line2[key]['credit'] += l.credit
            
            for key, val in line2.items():
                line_result.append(val)
        return line_result

    def set_default_account(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        ext_line_pool = self.pool.get('ext.transaksi.line')
        
        ext_trans = self.browse(cr, uid, ids, context=context)[0]
        debit_line_ids = []
        credit_line_ids = []
        for line in ext_trans.ext_line:
            if line.debit:
                debit_line_ids.append(line.id)
            elif line.credit:
                credit_line_ids.append(line.id)

        if ext_trans.default_debit_account_id:
            ext_line_pool.write(cr, uid, debit_line_ids, {'account_id':ext_trans.default_debit_account_id.id})
        if ext_trans.default_credit_account_id:
            ext_line_pool.write(cr, uid, credit_line_ids, {'account_id':ext_trans.default_credit_account_id.id})
        return True

    def create_advance_line(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        ext_line_pool = self.pool.get('ext.transaksi.line')
        currency_obj = self.pool.get('res.currency')

        ext_trans = self.browse(cr, uid, ids, context=context)[0]
        cek_lines = False
        advance = ext_trans.advance_id or False
        for line in ext_trans.ext_line:
            if line.adv_move_line_id == ext_trans.advance_move_line_id:
                cek_lines = True
        if cek_lines:
            return True

        if advance and advance.state=='posted' and advance.move_id:
            advance_move_line_id = ext_trans.advance_move_line_id
            account_id = ext_trans.advance_move_line_id.account_id.id
            amt_adv = False
            current_curr = ext_trans.currency_id
            advance_curr = advance.journal_id.currency or advance.journal_id.company_id.currency_id
            company_curr = ext_trans.company_id.currency_id
            if advance_move_line_id and account_id:
                if advance_move_line_id.debit-advance_move_line_id.credit < 0:
                    sign = 1
                else:
                    sign = -1

                if advance_move_line_id.currency_id and advance_move_line_id.currency_id!=company_curr:
                    if advance_move_line_id.currency_id!=current_curr:
                        amt_adv = currency_obj.compute(cr, uid, advance_move_line_id.currency_id.id, current_curr.id, advance_move_line_id.amount_residual_currency, context={'date':ext_trans.date})
                    elif advance_move_line_id.currency_id==current_curr:
                        amt_adv = advance_move_line_id.amount_residual_currency
                else:
                    if current_curr!=company_curr:
                        amt_adv = currency_obj.compute(cr, uid, company_curr.id, current_curr.id, advance_move_line_id.amount_residual, context={'date':ext_trans.date})
                    else:
                        amt_adv = advance_move_line_id.amount_residual

                ext_line_id = ext_line_pool.create(cr, uid, {
                        'type_of_charge': False,
                        'account_id' : account_id,
                        'adv_move_line_id' : advance_move_line_id.id,
                        'name' : 'Advance Payment',
                        'ext_transaksi_id': ext_trans.id,
                        'debit': sign * amt_adv > 0 and amt_adv or 0.0,
                        'credit': sign * amt_adv < 0 and amt_adv or 0.0,
                        'partner_id': advance.partner_id and advance.partner_id.id or False,
                    }, context=context)

        return True
    
    def posted_action(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        account_obj = self.pool.get('account.account')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        seq_obj = self.pool.get('ir.sequence')
        currency_obj = self.pool.get('res.currency')
        for ext_pay in self.browse(cr, uid, ids, context=context):
            rec_list_ids = []
            date = ext_pay.date!='False' and ext_pay.date or time.strftime('%Y-%m-%d')
            if ext_pay.number:
                name = ext_pay.number
            elif ext_pay.journal_id.sequence_id:
                cd = {'date':datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
                name = seq_obj.get_id(cr, uid, ext_pay.journal_id.sequence_id.id, context=cd)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            

            move = {
                'name': name,
                'journal_id': ext_pay.journal_id.id,
                'narration': ext_pay.name,
                'date': date,
                'ref': ext_pay.ref or '',
                'period_id': ext_pay.force_period.id
                }

            
            move_id = move_pool.create(cr, uid, move)
            company_currency = ext_pay.company_id.currency_id.id
            current_currency = ext_pay.currency_id and ext_pay.currency_id.id or (ext_pay.journal_id.currency and ext_pay.journal_id.currency.id) or company_currency

            ml = []
            tml= []
            line, line1 = [],[]

            if not context.get('tax_line',False):
                # ext line group
                ext_line_grouped = self.group_ext_lines(cr, uid, ext_pay.ext_line, ext_pay.group_by_account)
                if ext_line_grouped:
                    for ext_line_g in ext_line_grouped:
                        debit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_line_g['debit'], context={'date': ext_pay.date})
                        credit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_line_g['credit'], context={'date': ext_pay.date})
                            
                        if debit > 0:
                            amount_currency = ext_line_g['debit']
                        else:
                            amount_currency = -ext_line_g['credit']
                        
                        move_line = {
                            'name': ext_line_g['name'] or '/',
                            'debit': debit,
                            'credit': credit,
                            'account_id': ext_line_g['account_id'],
                            'other_ref' : ext_line_g['other_ref'],
                            'journal_id': ext_pay.journal_id.id,
                            'period_id': ext_pay.force_period.id,
                            'analytic_account_id': ext_line_g['analytic_account_id'],
                            'partner_id': ext_line_g['partner_id'],
                            'currency_id': company_currency <> current_currency and current_currency or False,
                            'amount_currency': company_currency <> current_currency and amount_currency or 0.0,
                            'date': date,
                            }
                        
                        ml.append(move_line)
                else:
                    for ext_pay_line in ext_pay.ext_line:
                        acc = account_obj.browse(cr, uid, ext_pay_line.account_id.id, context=context)
                        debit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_pay_line.debit, context={'date': ext_pay.date})
                        credit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_pay_line.credit, context={'date': ext_pay.date})
                            
                        if debit > 0:
                            amount_currency = ext_pay_line.debit
                        else:
                            amount_currency = -ext_pay_line.credit
                        
                        move_line = {
                            'name': ext_pay_line.name or '/',
                            'debit': debit,
                            'credit': credit,
                            'account_id': ext_pay_line.account_id.id,
                            'other_ref' : ext_pay_line.reference or '',
                            # 'move_id': move_id,
                            'journal_id': ext_pay.journal_id.id,
                            'period_id': ext_pay.force_period.id,
                            'analytic_account_id': ext_pay_line.analytic_account_id and ext_pay_line.analytic_account_id.id or False,
                            'partner_id': ext_pay_line.partner_id and ext_pay_line.partner_id.id or False,
                            'currency_id': company_currency <> current_currency and current_currency or False,
                            'amount_currency': company_currency <> current_currency and amount_currency or 0.0,
                            'date': date,
                            }
                        
                        ml.append(move_line)
                        if ext_pay_line.adv_move_line_id:
                            rec_list_ids.append(ext_pay_line.adv_move_line_id.id)
                        # move_line_id = move_line_pool.create(cr, uid, move_line)
                        # move_lines_group[key]=move_line_id
                # move line group
                ml = self.group_lines(cr, uid, ml,ext_pay.group_by_account)
                line=map(lambda x:(0,0,x),ml)

            if context.get('tax_line',False) or context.get('post_once',False):
                for ext_tax_line in ext_pay.tax_ext_line:
                    tax_currency = ext_tax_line.currency_id and ext_tax_line.currency_id.id or False
                    debit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_tax_line.debit, context={'date': ext_pay.date})
                    credit = currency_obj.compute(cr, uid, current_currency, company_currency, ext_tax_line.credit, context={'date': ext_pay.date})
                    
                    if debit > 0:
                        amount_currency = tax_currency and (ext_tax_line.amount_currency or ext_tax_line.debit) or ext_tax_line.debit
                    else:
                        amount_currency = tax_currency and (ext_tax_line.amount_currency or ext_tax_line.credit) or ext_tax_line.credit

                    move_line = {
                        'name': ext_tax_line.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': ext_tax_line.account_id.id,
                        'other_ref' : ext_tax_line.reference or '',
                        # 'move_id': move_id,
                        'journal_id': ext_pay.journal_id.id,
                        'period_id': ext_pay.force_period.id,
                        'analytic_account_id': ext_tax_line.analytic_account_id and ext_tax_line.analytic_account_id.id or False,
                        'partner_id': ext_tax_line.partner_id and ext_tax_line.partner_id.id or False,
                        'currency_id': company_currency <> current_currency and current_currency or False,
                        'amount_currency': company_currency <> current_currency and amount_currency or 0.0,
                        'date': date,
                        'tax_amount': (debit-credit),
                        'faktur_pajak_source':'ext.transaksi.line,%s'%ext_tax_line.id,
                        'tax_code_id' : ext_tax_line.tax_code_id and ext_tax_line.tax_code_id.id or False,
                        # 'faktur_pajak_no': ext_tax_line.faktur_pajak and ext_tax_line.faktur_pajak or '',
                        }
                    
                    tml.append(move_line)
                    # move_line_pool.create(cr, uid, move_line)
                line1=map(lambda x:(0,0,x),tml)


            if ext_pay.type_transaction != 'others':
                # create bank/cash move line
                account_id = False
                if ext_pay.type_transaction == 'payment':
                    sign = -1
                    account_id = ext_pay.journal_id.default_credit_account_id and ext_pay.journal_id.default_credit_account_id.id or False
                elif ext_pay.type_transaction == 'receipt':
                    sign = 1
                    account_id = ext_pay.journal_id.default_debit_account_id and ext_pay.journal_id.default_debit_account_id.id or False

                if not account_id:
                    raise osv.except_osv(_('Configuration Error !'),
                        _('Please set the default debit/credit account of selected Journal !'))

                if context.get('post_once',False):
                    amount_paid = sign * (ext_pay.paid_amount+ext_pay.tax_paid_amount)
                elif context.get('tax_line',False):
                    amount_paid = sign * ext_pay.tax_paid_amount
                else:
                    amount_paid = sign * ext_pay.paid_amount

                if current_currency<>company_currency:
                    amt_currency = amount_paid
                    amount_paid = currency_obj.compute(cr, uid, current_currency, company_currency, amount_paid, context={'date': ext_pay.date})
                
                move_line = {
                    'name': ext_pay.name or '/',
                    'debit': amount_paid > 0 and amount_paid or 0.0,
                    'credit': amount_paid < 0 and abs(amount_paid) or 0.0,
                    'account_id': account_id,
                    'other_ref' : ext_pay.ref or '',
                    # 'move_id': move_id,
                    'journal_id': ext_pay.journal_id.id,
                    'period_id': ext_pay.force_period.id,
                    # 'analytic_account_id': ext_pay_line.analytic_account_id and ext_pay_line.analytic_account_id.id or False,
                    # 'partner_id': ext_pay_line.partner_id and ext_pay_line.partner_id.id or False,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'amount_currency': company_currency <> current_currency and amt_currency or 0.0,
                    'date': date,
                }
                line2=map(lambda x:(0,0,x),[move_line])
                move_pool.write(cr, uid, [move_id], {'line_id':line+line1+line2}, context={})
            else:
                move_pool.write(cr, uid, [move_id], {'line_id':line+line1}, context={})
                
            if ext_pay.advance_move_line_id:
                adv_ext_line = move_line_pool.search(cr, uid, [('move_id','=',move_id),('account_id','=',ext_pay.advance_move_line_id.account_id.id)])
                rec_list_ids.append(adv_ext_line and adv_ext_line[0])
                reconcile = False
                if len(rec_list_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_list_ids, writeoff_acc_id=False, writeoff_period_id=ext_pay.force_period.id, writeoff_journal_id=ext_pay.journal_id.id)

            
            self.auto_balance(cr, uid, ext_pay.id, move_id, context)
            
            # move_pool.post(cr, uid, [move_id], context={})
            update_ext_pay_val = {}
            if not context.get('tax_line',False):
                update_ext_pay_val.update({
                    'state': 'posted',
                    'move_id':move_id,
                    'date':date,
                })
            
            if context.get('tax_line',False) or context.get('post_once',False):
                update_ext_pay_val.update({
                    'tax_state': 'posted',
                    'tax_move_id':move_id,
                })

            if context.get('post_once',False):
                update_ext_pay_val.update({'is_once':True})

            update_ext_pay_val.update({'number':name})
            self.write(cr, uid, ids, update_ext_pay_val, context=context)

        return True
    
    def cancel_transaction(self, cr, uid, ids, context=None):
        if context is None:
            context={}

        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_pool_line = self.pool.get('account.move.line')
        analytic_line_pool = self.pool.get('account.analytic.line')
        
        for voucher in self.browse(cr, uid, ids, context=context):
            if not context.get('tax_line',False):
                recs = []
                imr = []
                if not voucher.move_id:
                    break
                for line in voucher.move_ids:
                    analytic_line_search = analytic_line_pool.search(cr, uid, [('move_id','=',line.id)])
                    move_pool_line.write(cr, uid, [line.id], {'analytic_account_id': ''})
                    if analytic_line_search:
                        analytic_line_browse = analytic_line_pool.browse(cr, uid, analytic_line_search)
                        for line_analytic in analytic_line_browse:
                            recs.append(line_analytic.id)
                    if line.reconcile_id:
                        imr.append(line.reconcile_id.id)

                reconcile_pool.unlink(cr, uid, imr)
                analytic_line_pool.unlink(cr, uid, recs)
                #move_pool_line.write(cr, uid, [voucher.move_id.id], {'account_analytic_id': ''})
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
            
            if context.get('tax_line',False):
                recs = []
                if not voucher.tax_move_id:
                    break
                for line in voucher.tax_move_ids:
                    analytic_line_search = analytic_line_pool.search(cr, uid, [('move_id','=',line.id)])
                    move_pool_line.write(cr, uid, [line.id], {'analytic_account_id': ''})
                    if analytic_line_search:
                        analytic_line_browse = analytic_line_pool.browse(cr, uid, analytic_line_search)
                        for line_analytic in analytic_line_browse:
                            recs.append(line_analytic.id)
                analytic_line_pool.unlink(cr, uid, recs)
                #move_pool_line.write(cr, uid, [voucher.move_id.id], {'account_analytic_id': ''})
                move_pool.button_cancel(cr, uid, [voucher.tax_move_id.id])
                move_pool.unlink(cr, uid, [voucher.tax_move_id.id])
        update_val = {}
        if not context.get('tax_line',False):
            update_val.update({
                'state':'draft',
                'move_id':False,
            })
        
        if context.get('tax_line',False) or context.get('post_once',False):
            update_val.update({
                'tax_state':'draft',
                'tax_move_id':False,
            })

        if context.get('post_once',False):
            update_val.update({
                'is_once':False,
            })
        
        self.write(cr, uid, ids, update_val)
        return True    

    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        if context is None:
            context={}
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        return {'value': {'currency_id': journal.currency and journal.currency.id or journal.company_id.currency_id.id or False}}

    def onchange_date(self, cr, uid, ids, date, context=None):
        period_obj = self.pool.get('account.period')
        res = {}
        if date:
            period_ids = period_obj.find(cr, uid, date, context=context)
            if period_ids:
                period_id = period_ids and period_ids[0] or False
                res.update({'force_period':period_id})
        return {'value':res}

    def get_tax_data(self, cr, uid, ids, context=None):
        if not context:context={}
        ulib3 = urllib3.PoolManager()
        efaktur_head_pool = self.pool.get('efaktur.head')
        for ext_pay in self.browse(cr, uid, ids, context=context):
            npwpcompany = ext_pay.company_id.npwp.replace(".","").replace("-","")
            urls=ext_pay.qr_urls
            
            urlspot=[]
            for url in urls.split("http://"):
                if url and url!='' and url not in ("\n","\t","\r"):
                    href="http://"+url
                    head_ids = efaktur_head_pool.search(cr, uid, [('url','=',href.strip())])
                    if not head_ids:
                        urlspot.append(href.strip())
                    if head_ids:
                        for efaktur in efaktur_head_pool.browse(cr, uid, head_ids):
                            if efaktur.related_ext_transaksi_id and efaktur.related_ext_transaksi_id.id!=ext_pay.id:
                                raise osv.except_osv(_('Error Validation'), _("Factur no. %s is already linked with extra payment no. %s"%(efaktur.nomorFaktur, efaktur.related_ext_transaksi_id.number)))
                            else:
                                efaktur_head_pool.write(cr, uid, efaktur.id, {'related_ext_transaksi_id':ext_pay.id})

            for link in list(set(urlspot)):
                # try:
                    res = ulib3.request('GET', link)
                    if res.status==200 and res.data:
                        tree = etree.fromstring(res.data)
                        efaktur_head={}
                        detailtrans = []
                        for subtree1 in tree:
                            if subtree1.tag!='detailTransaksi':
                                if subtree1.tag=="tanggalFaktur":
                                    dts=datetime.strptime(subtree1.text,"%d/%m/%Y").strftime('%Y-%m-%d')
                                    efaktur_head.update({subtree1.tag:dts})
                                else:
                                    efaktur_head.update({subtree1.tag:subtree1.text})
                            else:
                                dumpy = {}
                                for detail in subtree1.getchildren():
                                    dumpy.update({detail.tag:detail.text})
                                    if detail.tag=='ppnbm':
                                        detailtrans.append((0,0,dumpy))
                                        dumpy={}
                            
                        efaktur_head.update({
                            'related_ext_transaksi_id':ext_pay.id,
                            'company_id':ext_pay.company_id.id,
                            'url': link,
                            'type': npwpcompany == efaktur_head.get('npwpPenjual',False) and 'out' or 'in',
                            "efaktur_lines":detailtrans
                            })
                        self.pool.get('efaktur.head').create(cr, uid, efaktur_head, context=context)
                        # self.pool.get('efaktur.batch').write(cr,uid,batch.id,{'batch_lines':[]})
                # except:
                    # raise osv.except_osv(_('Error Connecting to Server'), _("The connection to http://svc.efaktur.pajak.go.id/ can not be established."))
        return True
ext_transaksi()

class ext_transaksi_line(osv.osv):
    _name = "ext.transaksi.line"
    _description = "Extra Transaksi"
    
    _columns = {
        # 'shipping_id' : fields.many2one('container.booking','Shippment'),
        'reference' : fields.char('Reference', 64),
        'adv_move_line_id' : fields.many2one('account.move.line','Advance Move Line'),
        'invoice_related_id' : fields.many2one('account.invoice','Related Invoice'),
        'picking_related_id' : fields.many2one('stock.picking','Related Picking'),
        'type_of_charge': fields.many2one('charge.type', 'Type'),
        'ext_transaksi_id': fields.many2one('ext.transaksi', 'Extra Payment ID',ondelete='cascade'),
        'name' : fields.char('Transaction', 64,required=False),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account')),
        'account_id' : fields.many2one('account.account', 'Account', required=False, domain=[('type','!=','view')]),
        'department_id': fields.many2one('hr.department','Department',),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'partner_id': fields.many2one('res.partner', string="Partner", help='The Ordering Partner'),
        'tax_ext_transaksi_id': fields.many2one('ext.transaksi', 'Tax Extra Payment ID'),
        'tax_date' : fields.date('Tax Date'),
        'faktur_pajak' : fields.char('No. Faktur Pajak', size=120),
        'tax_base' : fields.float('DPP'),
        'tax_code_id' : fields.many2one('account.tax.code','Tax Account'),
        'amount_currency': fields.float('Amount Currency', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
    }
    
    def onchange_debit(self, cr, uid, ids, debit, credit):
        result= {}
        if debit:
            result['value'] = {
                'debit': debit,
                'credit': 0,
            }
        else:
            result['value'] = {
                'debit': 0,
                'credit': 0,
            }
        return result
    
    def onchange_credit(self, cr, uid, ids, debit, credit):
        result= {}
        if credit:
            result['value'] = {
                'debit': 0,
                'credit': credit,
            }
        else:
            result['value'] = {
                'debit': 0,
                'credit': 0,
            }
        return result

    def onchange_charge(self, cr, uid, ids, type_of_charge):
        result={}
        charge = self.pool.get('charge.type').browse(cr,uid,type_of_charge)
        if charge.account_id:
            result= {'value':{'account_id':charge.account_id and charge.account_id.id or False}}
            return result
        else:
            return result
        
    
    def onchange_currency_tax(self, cr, uid, ids, amount, to_currency_id, from_currency_id, date=False, journal=False, context=None):
        if context is None:
            context = {}
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        currency_obj = self.pool.get('res.currency')
        result = {}
        if from_currency_id and to_currency_id:
            context.update({'date':date or time.strftime('%Y-%m-%d')})
            v = currency_obj.compute(cr, uid, from_currency_id, to_currency_id, amount, context=context)
            result['value'] = {
               'debit': v > 0 and v or 0.0,
            }
        return result
    
ext_transaksi_line()


class efaktur_head(osv.Model):
    _inherit = "efaktur.head"
    _columns = {
        "related_ext_transaksi_id"  : fields.many2one("ext.transaksi","Related Extra Payment"),
    }
