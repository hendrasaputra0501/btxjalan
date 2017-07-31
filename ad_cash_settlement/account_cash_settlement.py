import time
from lxml import etree

from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare,DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from openerp.report import report_sxw

class account_cash_settlement(osv.osv):
    def _check_paid(self, cr, uid, ids, name, args, context=None):
        res = {}
        for settlement in self.browse(cr, uid, ids, context=context):
            res[settlement.id] = any([((line.account_id.type, 'in', ('receivable', 'payable')) and line.reconcile_id) for line in settlement.move_ids])
        return res

    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False

    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')

        res = journal_pool.search(cr, uid, [('type', '=', 'general')], limit=1)
        return res and res[0] or False

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

    def _get_income_exchange_account_id(self, cr, uid, context=None):
        if context is None: context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        return company.income_currency_exchange_account_id and company.income_currency_exchange_account_id.id or False

    def _get_expense_exchange_account_id(self, cr, uid, context=None):
        if context is None: context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        return company.expense_currency_exchange_account_id and company.expense_currency_exchange_account_id.id or False

    def _compute_settlement_amount(self, cr, uid, line_dr_ids, line_cr_ids, amount):
        debit = credit = 0.0
        sign = 1
        for l in line_dr_ids:
            debit += l['amount']
        for l in line_cr_ids:
            credit += l['amount']
        return amount - sign * (credit - debit)

    def _compute_writeoff_amount(self, cr, uid, line_dr_ids, line_cr_ids, settlement_line_dr_ids, settlement_line_cr_ids, amount, context=None):
        context = context or {}
        debit = credit = 0.0
        sign = 1
        for l in line_dr_ids+settlement_line_dr_ids:
            debit += l['amount']
        for l in line_cr_ids+settlement_line_cr_ids:
            credit += l['amount']
        return amount - sign * (credit - debit)

    def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, settlement_line_dr_ids, settlement_line_cr_ids, amount, settlement_currency, context=None):
        context = context or {}
        if not line_dr_ids and not line_cr_ids:
            return {'value':{'writeoff_amount': 0.0}}
        line_osv1 = self.pool.get("account.cash.settlement.advance")
        line_dr_ids = resolve_o2m_operations(cr, uid, line_osv1, line_dr_ids, ['amount'], context)
        line_cr_ids = resolve_o2m_operations(cr, uid, line_osv1, line_cr_ids, ['amount'], context)
        line_osv2 = self.pool.get("account.cash.settlement.line")
        settlement_line_dr_ids = resolve_o2m_operations(cr, uid, line_osv2, settlement_line_dr_ids, ['amount'], context)
        settlement_line_cr_ids = resolve_o2m_operations(cr, uid, line_osv2, settlement_line_cr_ids, ['amount'], context)
        return {'value': {'settlement_amount': self._compute_settlement_amount(cr, uid, line_dr_ids, line_cr_ids, amount), 'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, settlement_line_dr_ids, settlement_line_cr_ids, amount)}}

    def _get_journal_currency(self, cr, uid, ids, name, args, context=None):
        res = {}
        for settlement in self.browse(cr, uid, ids, context=context):
            res[settlement.id] = settlement.journal_id.currency and settlement.journal_id.currency.id or settlement.company_id.currency_id.id
        return res

    def _get_settlement_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        debit = credit = 0.0
        for settlement in self.browse(cr, uid, ids, context=context):
            sign = 1
            for l in settlement.line_dr_ids:
                debit += l.amount
            for l in settlement.line_cr_ids:
                credit += l.amount
            currency = settlement.currency_id or settlement.company_id.currency_id
            res[settlement.id] =  currency_obj.round(cr, uid, currency, settlement.amount - sign * (credit - debit))
        return res

    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        debit = credit = 0.0
        for settlement in self.browse(cr, uid, ids, context=context):
            sign = 1
            for l in settlement.line_dr_ids+settlement.settlement_line_dr_ids:
                debit += l.amount
            for l in settlement.line_cr_ids+settlement.settlement_line_cr_ids:
                credit += l.amount
            currency = settlement.currency_id or settlement.company_id.currency_id
            res[settlement.id] =  currency_obj.round(cr, uid, currency, settlement.amount - sign * (credit - debit))
        return res


    _name = 'account.cash.settlement'
    _description = 'Accounting Cash Settlement'
    _order = "date desc, id desc"
    # _rec_name = 'number'
    
    _columns = {
        'name':fields.char('Memo', size=256, readonly=True, states={'draft':[('readonly',False)]}),
        'date':fields.date('Date', readonly=True, select=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'account_id':fields.many2one('account.account', 'Account', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'line_ids':fields.one2many('account.cash.settlement.advance','settlement_id','Advance Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'line_cr_ids':fields.one2many('account.cash.settlement.advance','settlement_id','Settlement Credits',
            domain=[('type','=','cr')], context={'default_type':'cr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'line_dr_ids':fields.one2many('account.cash.settlement.advance','settlement_id','Settlement Debits',
            domain=[('type','=','dr')], context={'default_type':'dr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'settlement_line_ids':fields.one2many('account.cash.settlement.line','settlement_id','Settlement Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'settlement_line_cr_ids':fields.one2many('account.cash.settlement.line','settlement_id','Counter-part Settlement Credits',
            domain=[('type','=','cr')], context={'default_type':'cr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'settlement_line_dr_ids':fields.one2many('account.cash.settlement.line','settlement_id','Counter-part Settlement Debits',
            domain=[('type','=','dr')], context={'default_type':'dr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'narration':fields.text('Notes', readonly=True, states={'draft':[('readonly',False)]}),
        # 'currency_id': fields.function(_get_journal_currency, type='many2one', relation='res.currency', string='Currency', readonly=True, required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, required=True, states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'income_currency_exchange_account_id': fields.many2one('account.account',string="Gain Exchange Rate Account",domain="[('type', '=', 'other')]",readonly=True, states={'draft':[('readonly',False)]}),
        'expense_currency_exchange_account_id': fields.many2one('account.account',string="Loss Exchange Rate Account",domain="[('type', '=', 'other')]",readonly=True, states={'draft':[('readonly',False)]}),
        'state':fields.selection(
            [('draft','Draft'),
             ('cancel','Cancelled'),
             ('posted','Posted')
            ], 'Status', readonly=True, size=32, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Cash Settlement. \
                        \n* The \'Posted\' status is used when user create settlement,a settlement number is generated and settlement entries are created in account \
                        \n* The \'Cancelled\' status is used when user cancel settlement.'),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft':[('readonly',False)]}, help="Transaction reference number."),
        'number': fields.char('Number', size=32, readonly=True,),
        'move_id':fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft':[('readonly',False)]}),
        'paid': fields.function(_check_paid, string='Paid', type='boolean', help="The Settlement has been totally paid."),
        'pre_line':fields.boolean('Previous Payments ?', required=False),
        'payment_option':fields.selection([
                                           ('without_writeoff', 'Keep Open'),
                                           ('with_writeoff', 'Reconcile Payment Balance'),
                                           ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)"),
        'writeoff_acc_id': fields.many2one('account.account', 'Counterpart Account', readonly=True, states={'draft': [('readonly', False)]}),
        'comment': fields.char('Counterpart Comment', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'analytic_id': fields.many2one('account.analytic.account','Write-Off Analytic Account', readonly=True, states={'draft': [('readonly', False)]}),
        'writeoff_amount': fields.function(_get_writeoff_amount, string='Write-Off Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the settlement and the sum of allocation on the settlement lines."),
        'settlement_amount': fields.function(_get_settlement_amount, string='Settlement Amount', type='float', readonly=True, help="Computed as the total sum of allocation amount on the settlement lines."),
    }
    _defaults = {
        'period_id': _get_period,
        'partner_id': _get_partner,
        'journal_id':_get_journal,
        'currency_id': _get_currency,
        'reference': _get_reference,
        'narration':_get_narration,
        'amount': _get_amount,
        'income_currency_exchange_account_id':_get_income_exchange_account_id,
        'expense_currency_exchange_account_id':_get_expense_exchange_account_id,
        'state': 'draft',
        'name': '',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.settlement',context=c),
        'payment_option': 'without_writeoff',
        'comment': _('Write-Off'),
    }

    def onchange_amount(self, cr, uid, ids, settlement_line_dr_ids, settlement_line_cr_ids, amount, partner_id, journal_id, currency_id, date, company_id, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'date': date})
        #read the settlement rate with the right date in the context
        currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        res = self.recompute_settlement_lines(cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, amount, currency_id, date, context=ctx)
        return res
    
    def basic_onchange_partner(self, cr, uid, ids, partner_id, journal_id, context=None):
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        res = {'value': {'account_id': False}}
        if not partner_id or not journal_id:
            return res

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        res['value']['account_id'] = account_id
        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, amount, currency_id, date, context=None):
        if not journal_id:
            return {}
        if context is None:
            context = {}
        #TODO: comment me and use me directly in the sales/purchases views
        res = self.basic_onchange_partner(cr, uid, ids, partner_id, journal_id, context=context)
        ctx = context.copy()
        # not passing the payment_rate currency and the payment_rate in the context but it's ok because they are reset in recompute_payment_rate
        ctx.update({'date': date})
        vals = self.recompute_settlement_lines(cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, amount, currency_id, date, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])
        #TODO: can probably be removed now
        #TODO: onchange_partner_id() should not returns [pre_line, line_dr_ids, payment_rate...] for type sale, and not 
        # [pre_line, line_cr_ids, payment_rate...] for type purchase.
        # We should definitively split account.settlement object in two and make distinct on_change functions. In the 
        # meanwhile, bellow lines must be there because the fields aren't present in the view, what crashes if the 
        # onchange returns a value for them
        return res

    def recompute_settlement_lines(self, cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, price, currency_id, date, context=None):
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
            move_line_pool = self.pool.get('account.move.line')
            amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, line.id, context=context)
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
        line_pool = self.pool.get('account.cash.settlement.advance')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('settlement_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'other'
        
        ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('account_id.reconcile','=',True), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        company_currency = journal.company_id.currency_id.id
        
        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
            
        line_osv = self.pool.get("account.cash.settlement.line")
        settlement_line_dr_ids = resolve_o2m_operations(cr, uid, line_osv, settlement_line_dr_ids, ['amount'], context)
        settlement_line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, settlement_line_cr_ids, ['amount'], context)

        #settlement line creation
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, line.id, context=context)
            
            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the settlement currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.name or line.move_id.name,
                'type': line.debit and 'cr' or 'dr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_currency_original':line.currency_id and line.amount_currency or (line.debit-line.credit),
                'currency_original':line.currency_id and line.currency_id.id or line.company_id.currency_id.id,
                'amount_original': amount_original,
                'amount': 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }

            if rs['type'] == 'dr':
                default['value']['line_dr_ids'].append(rs)
            else:
                default['value']['line_cr_ids'].append(rs)

            if len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['settlement_amount'] = self._compute_settlement_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price)
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], settlement_line_dr_ids, settlement_line_cr_ids, price)
        return default

    def onchange_date(self, cr, uid, ids, date, currency_id, amount, company_id, context=None):
        """
        @param date: latest value from user input for field date
        @param args: other arguments
        @param context: context arguments, like lang, time zone
        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context ={}
        res = {'value': {}}
        #set the period of the settlement
        period_pool = self.pool.get('account.period')
        currency_obj = self.pool.get('res.currency')
        ctx = context.copy()
        ctx.update({'company_id': company_id, 'account_period_prefer_normal': True})
        settlement_currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        pids = period_pool.find(cr, uid, date, context=ctx)
        if pids:
            res['value'].update({'period_id':pids[0]})
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, partner_id, date, settlement_line_dr_ids, settlement_line_cr_ids, amount, company_id, context=None):
        if context is None:
            context = {}
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        
        vals = {'value':{} }
        currency_id = False
        if journal.currency:
            currency_id = journal.currency.id
        else:
            currency_id = journal.company_id.currency_id.id
        vals['value'].update({'currency_id': currency_id})
        if partner_id:
            res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, amount, currency_id, date, context)
            for key in res.keys():
                vals[key].update(res[key])
        return vals

    def onchange_currency(self, cr, uid, ids, currency_id, journal_id, line_ids, partner_id, date, settlement_line_dr_ids, settlement_line_cr_ids, amount, company_id, context=None):
        if context is None:
            context = {}
        if not currency_id or  not journal_id:
            return False
        vals = {'value':{} }
        currency_id = currency_id
        if partner_id:
            res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, settlement_line_dr_ids, settlement_line_cr_ids, amount, currency_id, date, context)
            for key in res.keys():
                vals[key].update(res[key])
        return vals

    def button_validate_settlement(self, cr, uid, ids, context=None):
        context = context or {}
        wf_service = netsvc.LocalService("workflow")
        for vid in ids:
            wf_service.trg_validate(uid, 'account.cash.settlement', vid, 'validate_settlement', cr)
        return {'type': 'ir.actions.act_window_close'}

    def validate_settlement(self, cr, uid, ids, context=None):
        self.action_move_line_create(cr, uid, ids, context=context)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for settlement_id in ids:
            wf_service.trg_create(uid, 'account.cash.settlement', settlement_id, cr)
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def cancel_settlement(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for settlement in self.browse(cr, uid, ids, context=context):
            # refresh to make sure you don't unlink an already removed move
            settlement.refresh()
            for line in settlement.move_ids:
                # refresh to make sure you don't unreconcile an already unreconciled entry
                line.refresh()
                if line.reconcile_id:
                    move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
                    move_lines.remove(line.id)
                    reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
                    if len(move_lines) >= 2:
                        move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
            if settlement.move_id:
                move_pool.button_cancel(cr, uid, [settlement.move_id.id])
                move_pool.unlink(cr, uid, [settlement.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete Settlement(s) which are already opened or paid.'))
        return super(account_cash_settlement, self).unlink(cr, uid, ids, context=context)

    def _sel_context(self, cr, uid, settlement_id, context=None):
        """
        Select the context to use accordingly if it needs to be multicurrency or not.

        :param settlement_id: Id of the actual settlement
        :return: The returned context will be the same as given in parameter if the settlement currency is the same
                 than the company currency, otherwise it's a copy of the parameter with an extra key 'date' containing
                 the date of the settlement.
        :rtype: dict
        """
        company_currency = self._get_company_currency(cr, uid, settlement_id, context)
        current_currency = self._get_current_currency(cr, uid, settlement_id, context)
        if current_currency <> company_currency:
            context_multi_currency = context.copy()
            settlement = self.pool.get('account.cash.settlement').browse(cr, uid, settlement_id, context)
            context_multi_currency.update({'date': settlement.date})
            return context_multi_currency
        return context

    def account_move_get(self, cr, uid, settlement_id, context=None):
        '''
        This method prepare the creation of the account move related to the given settlement.

        :param settlement_id: Id of settlement for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        settlement = self.pool.get('account.cash.settlement').browse(cr,uid,settlement_id,context)
        if settlement.number:
            name = settlement.number
        elif settlement.journal_id.sequence_id:
            if not settlement.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': settlement.period_id.fiscalyear_id.id, 'date':datetime.strptime(settlement.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
            name = seq_obj.next_by_id(cr, uid, settlement.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        
        ref = settlement.reference

        move = {
            'name': name,
            'journal_id': settlement.journal_id.id,
            'narration': settlement.narration,
            'date': settlement.date,
            'ref': ref,
            'period_id': settlement.period_id.id,
        }
        return move

    def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
        '''
        Prepare the two lines in company currency due to currency rate difference.

        :param line: browse record of the settlement.line for which we want to create currency rate difference accounting
            entries
        :param move_id: Account move wher the move lines will be.
        :param amount_residual: Amount to be posted.
        :param company_currency: id of currency of the company to which the settlement belong
        :param current_currency: id of currency of the settlement
        :return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
        :rtype: tuple of dict
        '''
        if amount_residual > 0:
            account_id = line.settlement_id.expense_currency_exchange_account_id and line.settlement_id.expense_currency_exchange_account_id or line.settlement_id.company_id.expense_currency_exchange_account_id
            if not account_id:
                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
        else:
            account_id = line.settlement_id.income_currency_exchange_account_id and line.settlement_id.income_currency_exchange_account_id or line.settlement_id.company_id.income_currency_exchange_account_id 
            if not account_id:
                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
        # Even if the amount_currency is never filled, we need to pass the foreign currency because otherwise
        # the receivable/payable account may have a secondary currency, which render this field mandatory
        if line.account_id.currency_id:
            account_currency_id = line.account_id.currency_id.id
        else:
            account_currency_id = company_currency <> current_currency and current_currency or False
        move_line = {
            'journal_id': line.settlement_id.journal_id.id,
            'period_id': line.settlement_id.period_id.id,
            'name': _('change')+': '+(line.name or '/'),
            'account_id': line.account_id.id,
            'move_id': move_id,
            'partner_id': line.settlement_id.partner_id.id,
            'currency_id': account_currency_id,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': amount_residual > 0 and amount_residual or 0.0,
            'debit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.settlement_id.date,
        }
        move_line_counterpart = {
            'journal_id': line.settlement_id.journal_id.id,
            'period_id': line.settlement_id.period_id.id,
            'name': _('change')+': '+(line.name or '/'),
            'account_id': account_id.id,
            'move_id': move_id,
            'amount_currency': 0.0,
            'partner_id': line.settlement_id.partner_id.id,
            'currency_id': account_currency_id,
            'quantity': 1,
            'debit': amount_residual > 0 and amount_residual or 0.0,
            'credit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.settlement_id.date,
        }
        return (move_line, move_line_counterpart)

    def _convert_amount(self, cr, uid, amount, settlement_id, context=None):
        '''
        This function convert the amount given in company currency. It takes either the rate in the settlement (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.

        :param amount: float. The amount to convert
        :param settlement: id of the settlement on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the settlement date
            field in order to select the good rate to use.
        :return: the amount in the currency of the settlement's company
        :rtype: float
        '''
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        settlement = self.browse(cr, uid, settlement_id, context=context)
        return currency_obj.compute(cr, uid, settlement.currency_id.id, settlement.company_id.currency_id.id, amount, context=context)

    def settlement_move_line_create(self, cr, uid, settlement_id, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per settlement line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param settlement_id: settlement id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all settlement lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the settlement belong
        :param current_currency: id of currency of the settlement
        :return: Tuple build as (remaining amount not allocated on settlement lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tot_line = 0.0
        rec_lst_ids = []

        date = self.read(cr, uid, settlement_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        settlement = self.pool.get('account.cash.settlement').browse(cr, uid, settlement_id, context=ctx)
        settlement_currency = settlement.currency_id or settlement.company_id.currency_id
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in settlement.line_ids:
            #create one move line per settlement line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the settlement line into the currency of the settlement's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the settlement if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.amount, settlement.id, context=ctx)
            amount_residual_currency, amount_residual = move_line_obj.get_amount_residual(cr, uid, line.move_line_id and line.move_line_id.id, context=context)
            # if the amount encoded in settlement is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong settlement line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': settlement.journal_id.id,
                'period_id': settlement.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': settlement.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': settlement.date
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

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the settlement and the settlement line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the settlement, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            settlement_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [settlement_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, settlement.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in settlement currency
                move_line_foreign_currency = {
                    'journal_id': line.settlement_id.journal_id.id,
                    'period_id': line.settlement_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.settlement_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.settlement_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        
        for line in settlement.settlement_line_ids:
            # create one counterpart move line of move line per settlement line
            if not line.amount:
                continue

            amount = self._convert_amount(cr, uid, line.amount, settlement.id, context=ctx)
            move_line = {
                'journal_id': settlement.journal_id.id,
                'period_id': settlement.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': settlement.partner_id.id,
                'currency_id': company_currency <> settlement_currency.id and settlement_currency.id or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': settlement.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'
            sign = line.type=='dr' and 1 or -1
            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            move_line['amount_currency'] = company_currency <> settlement_currency.id and sign*line.amount or 0.0
            settlement_line = move_line_obj.create(cr, uid, move_line)

        # if settlement.writeoff_amount and settlement.writeoff_amount != 0.0:
        amount = self._convert_amount(cr, uid, settlement.writeoff_amount or 0.0, settlement.id, context=ctx)
        tot_line -= amount
        if not (abs(round(tot_line,2)) == 0.0):
            diff_account_id = False
            if settlement.payment_option == 'with_writeoff' and settlement.writeoff_acc_id:
                diff_account_id = settlement.writeoff_acc_id.id
            elif settlement.income_currency_exchange_account_id and settlement.expense_currency_exchange_account_id:
                diff_account_id = tot_line<0.0 and settlement.expense_currency_exchange_account_id.id or settlement.income_currency_exchange_account_id.id
            elif settlement.partner_id and settlement.partner_id.account_balance_id:
                diff_account_id = settlement.partner_id.account_balance_id.id
            else:
                diff_account_id = settlement.account_id.id
            move_line_rounding = {
                    'journal_id': settlement.journal_id.id,
                    'period_id': settlement.period_id.id,
                    'name': _('Rounding difference'),
                    'account_id': diff_account_id,
                    'move_id': move_id,
                    'partner_id': line.settlement_id.partner_id.id,
                    'quantity': 1,
                    'credit': tot_line>0.0 and tot_line or 0.0,
                    'debit': tot_line<0.0 and -1*tot_line or 0.0,
                    'date': line.settlement_id.date,
                    'amount_currency':0.0,
                }
            new_id = move_line_obj.create(cr, uid, move_line_rounding, context=context)
        tot_line = amount

        return (tot_line, rec_lst_ids)

    def writeoff_move_line_get(self, cr, uid, settlement_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param settlement_id: Id of settlement what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the settlement belong
        :param current_currency: id of currency of the settlement
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        settlement = self.pool.get('account.cash.settlement').browse(cr,uid,settlement_id,context)
        current_currency_obj = settlement.currency_id or settlement.journal_id.company_id.currency_id
        
        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account_id = False
            write_off_name = ''
            if settlement.payment_option == 'with_writeoff':
                account_id = settlement.writeoff_acc_id.id
                write_off_name = settlement.comment
            elif settlement.partner_id and settlement.partner_id.account_balance_id:
                account_id = settlement.partner_id.account_balance_id.id
            else:
                # fallback on account of settlement
                account_id = settlement.account_id.id
            sign = 1
            
            move_line = {
                'name': write_off_name or name,
                'account_id': account_id,
                'move_id': move_id,
                'partner_id': settlement.partner_id.id,
                'date': settlement.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and (sign * -1 * settlement.writeoff_amount) or 0.0,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': settlement.analytic_id and settlement.analytic_id.id or False,
            }
        return move_line

    def _get_company_currency(self, cr, uid, settlement_id, context=None):
        '''
        Get the currency of the actual company.

        :param settlement_id: Id of the settlement what i want to obtain company currency.
        :return: currency id of the company of the settlement
        :rtype: int
        '''
        return self.pool.get('account.cash.settlement').browse(cr,uid,settlement_id,context).journal_id.company_id.currency_id.id

    def _get_current_currency(self, cr, uid, settlement_id, context=None):
        '''
        Get the currency of the settlement.

        :param settlement_id: Id of the settlement what i want to obtain current currency.
        :return: currency id of the settlement
        :rtype: int
        '''
        settlement = self.pool.get('account.cash.settlement').browse(cr,uid,settlement_id,context)
        return settlement.currency_id.id or self._get_company_currency(cr,uid,settlement.id,context)

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the settlements given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        cash_advance_settle_pool = self.pool.get('account.cash.settlement.advance')
        settle_line_pool = self.pool.get('account.cash.settlement.line')
        for settlement in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=settlement.journal_id.company_id.id)
            if settlement.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, settlement.id, context)
            current_currency = self._get_current_currency(cr, uid, settlement.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, settlement.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': settlement.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, settlement.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            
            rec_list_ids = []
            # Create one move line per settlement line and its counterpart move line where amount is not 0.0
            line_total, rec_list_ids = self.settlement_move_line_create(cr, uid, settlement.id, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, settlement.id, line_total, move_id, name, company_currency, current_currency, local_context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)
            # We post the settlement.
            self.write(cr, uid, [settlement.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            # and we delete all Credit Lines and Debit Lines that are not allocated
            for line in settlement.line_ids:
                if line.amount==0.0:
                    cash_advance_settle_pool.unlink(cr, uid, line.id)
            for line in settlement.settlement_line_ids:
                if line.amount==0.0:
                    settle_line_pool.unlink(cr, uid, line.id)
            
            if settlement.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=settlement.writeoff_acc_id.id, writeoff_period_id=settlement.period_id.id, writeoff_journal_id=settlement.journal_id.id)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'state': 'draft',
            'number': False,
            'move_id': False,
            'line_cr_ids': False,
            'line_dr_ids': False,
            'settlement_line_cr_ids': False,
            'settlement_line_dr_ids': False,
            'reference': False
        })
        if 'date' not in default:
            default['date'] = time.strftime('%Y-%m-%d')
        return super(account_cash_settlement, self).copy(cr, uid, id, default, context)


class account_cash_settlement_line(osv.osv):
    _name = 'account.cash.settlement.line'
    _description = 'settlement Lines'
    _order = "id"

    _columns = {
        'settlement_id':fields.many2one('account.cash.settlement', 'Cash Settlement', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'account_id':fields.many2one('account.account','Account', required=True),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Dr/Cr'),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
        'company_id': fields.related('settlement_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
    }
    _defaults = {
        'name': '',
    }

account_cash_settlement_line()

class account_cash_settlement_advance(osv.osv):
    _name = 'account.cash.settlement.advance'
    _description = 'Advance Settlement Lines'
    _order = "move_line_id"
    # If the payment is in the same currency than the invoice, we keep the same amount
    # Otherwise, we compute from invoice currency to payment currency
    # checked
    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        move_line_pool = self.pool.get('account.move.line')
        for line in self.browse(cr, uid, ids, context=context):
            res = {}
            ctx = context.copy()
            ctx.update({'date': line.settlement_id.date})
            company_currency = line.settlement_id.journal_id.company_id.currency_id.id
            settlement_currency = line.settlement_id.currency_id and line.settlement_id.currency_id.id or company_currency
            move_line = line.move_line_id or False
            amount_residual_currency, amount_residual = 0.0, 0.0
            if move_line:
                amount_residual_currency, amount_residual = move_line_pool.get_amount_residual(cr, uid, move_line.id, context=context)

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
            elif move_line.currency_id and settlement_currency==move_line.currency_id.id:
                res['amount_original'] = abs(move_line.amount_currency)
                res['amount_unreconciled'] = abs(amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the settlement currency
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, settlement_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, settlement_currency, abs(amount_residual), context=ctx)

            rs_data[line.id] = res
        return rs_data

    # checked
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
                    result[line.id]['amount_currency_original'] = line.move_line_id.currency_id and line.move_line_id.amount_currency or (line.move_line_id.debit-line.move_line_id.credit)
                    result[line.id]['currency_original'] = line.move_line_id.currency_id and line.move_line_id.currency_id.id or line.move_line_id.company_id.currency_id.id
        return result

    # checked
    def _currency_id(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a settlement line. It's either the currency of the
        associated move line (if any) or the currency of the settlement or the company currency.
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            move_line = line.move_line_id
            if move_line:
                res[line.id] = move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id
            else:
                res[line.id] = line.settlement_id.currency_id and line.settlement_id.currency_id.id or line.settlement_id.company_id.currency_id.id
        return res

    _columns = {
        'settlement_id':fields.many2one('account.cash.settlement', 'Cash Settlement', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'account_id':fields.many2one('account.account','Account', required=True),
        'partner_id':fields.related('settlement_id', 'partner_id', type='many2one', relation='res.partner', string='Partner'),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'reconcile': fields.boolean('Full Reconcile'),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Dr/Cr'),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
        'amount_currency_original' : fields.function(_get_original_amount, multi='cash_settlement_line', type='float', string='Original Amount Currency'),
        'currency_original' : fields.function(_get_original_amount, multi='cash_settlement_line', type='many2one', obj='res.currency', string='Original Currency'),
        'date_original': fields.related('move_line_id','date', type='date', relation='account.move.line', string='Date', readonly=1),
        'date_due': fields.related('move_line_id','date_maturity', type='date', relation='account.move.line', string='Due Date', readonly=1),
        'amount_original': fields.function(_compute_balance, multi='dc', type='float', string='Original Amount', store=True, digits_compute=dp.get_precision('Account')),
        'amount_unreconciled': fields.function(_compute_balance, multi='dc', type='float', string='Open Balance', store=True, digits_compute=dp.get_precision('Account')),
        'company_id': fields.related('settlement_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
        'currency_id': fields.function(_currency_id, string='Currency', type='many2one', relation='res.currency', readonly=True),
    }
    _defaults = {
        'name': '',
    }

    # checked
    def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
        vals = {'amount': 0.0}
        if reconcile:
            vals = { 'amount': amount_unreconciled}
        return {'value': vals}

    # checked
    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
        vals = {}
        if amount:
            vals['reconcile'] = (amount == amount_unreconciled)
        return {'value': vals}

    # checked
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
            res.update({
                'account_id': move_line.account_id.id,
                'type': ttype,
                'currency_id': move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id,
            })
        return {
            'value':res,
        }

    # checked
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
        values = super(account_cash_settlement_advance, self).default_get(cr, user, fields_list, context=context)
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
            if partner.account_balance_id:
                account_id = partner.account_balance_id.id
        values.update({
            'account_id':account_id,
            'type':ttype
        })
        return values
account_cash_settlement_advance()

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


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
