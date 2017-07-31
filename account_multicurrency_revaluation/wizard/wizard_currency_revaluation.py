# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher, Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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

from datetime import date

from openerp.osv import fields, orm, osv
from tools.translate import _


class WizardCurrencyrevaluation(orm.TransientModel):
    _name = 'wizard.currency.revaluation'

    _columns = {
        'revaluation_date': fields.date(
            'Revaluation Date',
            required=True),
        'rate_date': fields.date(
            'Rate Date',
            required=True),
        'journal_id': fields.many2one(
            'account.journal',
            'Journal',
            domain="[('type','=','general')]",
            help="You can set the default "
                 "journal in company settings.",
            required=True),
        'currency_type': fields.many2one(
            'res.currency.rate.type',
            'Currency Type',
            help="If no currency_type is selected,"
            " only rates with no type will be browsed.",
            required=False),
        'label': fields.char(
            'Entry description',
            size=100,
            help="This label will be inserted in entries description."
            " You can use %(account)s, %(currency)s"
                 " and %(rate)s keywords.",
            required=True),
    }

    def _get_default_revaluation_date(self, cr, uid, context):
        """
        Get last date of previous fiscalyear
        """
        context = context or {}

        fiscalyear_obj = self.pool.get('account.fiscalyear')
        user_obj = self.pool.get('res.users')
        cp = user_obj.browse(cr, uid, uid, context=context).company_id
        # find previous fiscalyear
        current_date = date.today().strftime('%Y-%m-%d')
        previous_fiscalyear_ids = fiscalyear_obj.search(
            cr, uid,
            [('date_stop', '<', current_date),
             ('company_id', '=', cp.id)],
            limit=1,
            order='date_start DESC',
            context=context)
        if not previous_fiscalyear_ids:
            return current_date
        last_fiscalyear = fiscalyear_obj.browse(
            cr, uid, previous_fiscalyear_ids[0], context=context)
        return last_fiscalyear.date_stop

    def _get_default_journal_id(self, cr, uid, context):
        """
        Get default journal if one is defined in company settings
        """
        user_obj = self.pool.get('res.users')
        cp = user_obj.browse(cr, uid, uid, context=context).company_id

        journal = cp.default_currency_reval_journal_id
        return journal and journal.id or False

    _defaults = {
        'label': "%(currency)s %(account)s "
        "%(rate)s currency revaluation",
        'revaluation_date': _get_default_revaluation_date,
        'journal_id': _get_default_journal_id,
    }

    def on_change_revaluation_date(self, cr, uid, id, revaluation_date):
        if not revaluation_date:
            return {}
        warning = {}
        user_obj = self.pool.get('res.users')
        move_obj = self.pool.get('account.move')
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear_ids = fiscalyear_obj.search(
            cr, uid,
            [('date_start', '<=', revaluation_date),
             ('date_stop', '>=', revaluation_date),
             ('company_id', '=', company_id)],
            limit=1
        )
        if fiscalyear_ids:
            fiscalyear = fiscalyear_obj.browse(
                cr, uid, fiscalyear_ids[0])

            previous_fiscalyear_ids = fiscalyear_obj.search(
                cr, uid,
                [('date_stop', '<', fiscalyear.date_start),
                 ('company_id', '=', company_id)],
                limit=1)
            if previous_fiscalyear_ids:
                special_period_ids = [p.id for p in fiscalyear.period_ids
                                      if p.special]
                opening_move_ids = []
                if special_period_ids:
                    opening_move_ids = move_obj.search(
                        cr, uid, [('period_id', '=', special_period_ids[0])])
                if not opening_move_ids or not special_period_ids:
                    warning = {
                        'title': _('Warning!'),
                        'message': _('No opening entries in opening period '
                                     'for this fiscal year')
                    }

        res = {'value': {}, 'warning': warning}
        return res

    def _compute_unrealized_currency_gl(self, cr, uid,
                                        currency_id,
                                        balances,
                                        form,
                                        context=None):
        """
        Update data dict with the unrealized currency gain and loss
        plus add 'currency_rate' which is the value used for rate in
        computation

        @param int currency_id: currency to revaluate
        @param dict balances: contains foreign balance and balance

        @return: updated data for foreign balance plus rate value used
        """
        context = context or {}

        currency_obj = self.pool.get('res.currency')
        type_id = form.currency_type and form.currency_type.id or False

        # Compute unrealized gain loss
        ctx_rate = context.copy()
        ctx_rate['date'] = form.rate_date
        ctx_rate['currency_rate_type_id'] = type_id
        cp_currency_id = form.journal_id.company_id.currency_id.id

        currency = currency_obj.browse(cr, uid, currency_id, context=ctx_rate)

        foreign_balance = adjusted_balance = balances.get(
            'foreign_balance', 0.0)
        balance = balances.get('balance', 0.0)
        unrealized_gain_loss = 0.0
        if foreign_balance:
            ctx_rate['revaluation'] = True
            adjusted_balance = currency_obj.compute(
                cr, uid, currency_id, cp_currency_id, foreign_balance,
                currency_rate_type_to=type_id,
                context=ctx_rate)
            unrealized_gain_loss = adjusted_balance - balance
            # revaluated_balance =  balance + unrealized_gain_loss
        else:
            if balance:
                if currency_id != cp_currency_id:
                    unrealized_gain_loss = 0.0 - balance
                else:
                    unrealized_gain_loss = 0.0
            else:
                unrealized_gain_loss = 0.0
        return {'unrealized_gain_loss': unrealized_gain_loss,
                'currency_rate': currency.rate,
                'revaluated_balance': adjusted_balance}

    def _format_label(self, cr, uid, text, account_id, currency_id,
                      rate, context=None):
        """
        Return a text with replaced keywords by values

        @param str text: label template, can use
            %(account)s, %(currency)s, %(rate)s
        @param int account_id: id of the account to display in label
        @param int currency_id: id of the currency to display
        @param float rate: rate to display
        """
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        account = account_obj.browse(cr, uid,
                                     account_id,
                                     context=context)
        currency = currency_obj.browse(cr, uid, currency_id, context=context)
        data = {'account': account.code or False,
                'currency': currency.name or False,
                'rate': rate or False}
        return text % data

    def _write_adjust_balance(self, cr, uid, account_id, currency_id,
                              partner_id, amount, label, form, sums,
                              context=None):
        """
        Generate entries to adjust balance in the revaluation accounts

        @param account_id: ID of account to be reevaluated
        @param amount: Amount to be written to adjust the balance
        @param label: Label to be written on each entry
        @param form: Wizard browse record containing data

        @return: ids of created move_lines
        """
        context = context or {}

        def create_move():
            reversable = form.journal_id.company_id.reversable_revaluations
            base_move = {'name': label,
                         'journal_id': form.journal_id.id,
                         'period_id': period.id,
                         'date': form.revaluation_date,
                         'to_be_reversed': reversable}
            return move_obj.create(cr, uid, base_move, context=context)

        def create_move_line(move_id, line_data, sums):
            base_line = {'name': label,
                         'partner_id': partner_id,
                         'currency_id': currency_id,
                         'amount_currency': 0.0,
                         'date': form.revaluation_date,
                         }
            base_line.update(line_data)
            # we can assume that keys should be equals columns name + gl_
            # but it was not decide when the code was designed. So commented
            # code may sucks:
            # for k, v in sums.items():
            #    line_data['gl_' + k] = v
            base_line['gl_foreign_balance'] = sums.get('foreign_balance', 0.0)
            base_line['gl_balance'] = sums.get('balance', 0.0)
            base_line['gl_revaluated_balance'] = sums.get(
                'revaluated_balance', 0.0)
            base_line['gl_currency_rate'] = sums.get('currency_rate', 0.0)
            return move_line_obj.create(cr, uid, base_line, context=context)
        if partner_id is None:
            partner_id = False
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        user_obj = self.pool.get('res.users')
        company = form.journal_id.company_id or user_obj.browse(
            cr, uid, uid).company_id
        period_ids = period_obj.search(
            cr, uid,
            [('date_start', '<=', form.revaluation_date),
             ('date_stop', '>=', form.revaluation_date),
             ('company_id', '=', company.id),
             ('special', '=', False)],
            limit=1,
            context=context)
        if not period_ids:
            raise osv.except_osv(_('Error!'),
                                 _('There is no period for company %s on %s'
                                   % (company.name, form.revaluation_date)))
        period = period_obj.browse(cr, uid, period_ids[0], context=context)
        created_ids = []
        # over revaluation
        if amount >= 0.01:
            if company.revaluation_gain_account_id:
                move_id = create_move()
                # Create a move line to Debit account to be revaluated
                line_data = {'debit': amount,
                             'move_id': move_id,
                             'account_id': account_id,
                             }
                created_ids.append(create_move_line(move_id, line_data, sums))
                # Create a move line to Credit revaluation gain account
                analytic_acc_id = (company.revaluation_analytic_account_id.id
                                   if company.revaluation_analytic_account_id
                                   else False)
                line_data = {
                    'credit': amount,
                    'account_id': company.revaluation_gain_account_id.id,
                    'move_id': move_id,
                    'analytic_account_id': analytic_acc_id,
                }
                created_ids.append(create_move_line(move_id, line_data, sums))
            if company.provision_bs_gain_account_id and \
               company.provision_pl_gain_account_id:
                move_id = create_move()
                analytic_acc_id = (
                    company.provision_pl_analytic_account_id and
                    company.provision_pl_analytic_account_id.id or
                    False)
                # Create a move line to Debit provision BS gain
                line_data = {
                    'debit': amount,
                    'move_id': move_id,
                    'account_id': company.provision_bs_gain_account_id.id, }
                created_ids.append(create_move_line(move_id, line_data, sums))
                # Create a move line to Credit provision P&L gain
                line_data = {
                    'credit': amount,
                    'analytic_account_id': analytic_acc_id,
                    'account_id': company.provision_pl_gain_account_id.id,
                    'move_id': move_id, }
                created_ids.append(create_move_line(move_id, line_data, sums))

        # under revaluation
        elif amount <= -0.01:
            amount = -amount
            if company.revaluation_loss_account_id:
                move_id = create_move()
                # Create a move line to Debit revaluation loss account
                analytic_acc_id = (company.revaluation_analytic_account_id.id
                                   if company.revaluation_analytic_account_id
                                   else False)
                line_data = {
                    'debit': amount,
                    'move_id': move_id,
                    'account_id': company.revaluation_loss_account_id.id,
                    'analytic_account_id': analytic_acc_id,
                }

                created_ids.append(create_move_line(move_id, line_data, sums))
                # Create a move line to Credit account to be revaluated
                line_data = {
                    'credit': amount,
                    'move_id': move_id,
                    'account_id': account_id,
                }
                created_ids.append(create_move_line(move_id, line_data, sums))

            if company.provision_bs_loss_account_id and \
               company.provision_pl_loss_account_id:
                move_id = create_move()
                analytic_acc_id = (
                    company.provision_pl_analytic_account_id and
                    company.provision_pl_analytic_account_id.id or
                    False)
                # Create a move line to Debit Provision P&L
                line_data = {
                    'debit': amount,
                    'analytic_account_id': analytic_acc_id,
                    'move_id': move_id,
                    'account_id': company.provision_pl_loss_account_id.id, }
                created_ids.append(create_move_line(move_id, line_data, sums))
                # Create a move line to Credit Provision BS
                line_data = {
                    'credit': amount,
                    'move_id': move_id,
                    'account_id': company.provision_bs_loss_account_id.id, }
                created_ids.append(create_move_line(move_id, line_data, sums))
        return created_ids

    def _prepare_adjust_dict_move(self, cr, uid, account_id, currency_id,
                              partner_id, amount, label, form, move_line, line_sums,
                              context=None):
        """
        Generate entries to adjust balance in the revaluation accounts

        @param account_id: ID of account to be reevaluated
        @param amount: Amount to be written to adjust the balance
        @param label: Label to be written on each entry
        @param form: Wizard browse record containing data

        @return: ids of created move_lines
        """
        context = context or {}

        def prepare_move_line(line_data, move_line, line_sums):
            base_line = {'name': label,
                         'partner_id': partner_id,
                         'currency_id': currency_id,
                         'amount_currency': 0.0,
                         'date': form.revaluation_date,
                         }
            base_line.update(line_data)
            # we can assume that keys should be equals columns name + gl_
            # but it was not decide when the code was designed. So commented
            # code may sucks:
            # for k, v in sums.items():
            #    line_data['gl_' + k] = v
            base_line['gl_foreign_balance'] = move_line.amount_residual_currency
            base_line['gl_balance'] = move_line.amount_residual
            base_line['gl_revaluated_balance'] = line_sums.get(
                'revaluated_balance', 0.0)
            base_line['gl_currency_rate'] = line_sums.get('currency_rate', 0.0)
            return base_line
        if partner_id is None:
            partner_id = False
        period_obj = self.pool.get('account.period')
        user_obj = self.pool.get('res.users')
        company = form.journal_id.company_id or user_obj.browse(
            cr, uid, uid).company_id
        period_ids = period_obj.search(
            cr, uid,
            [('date_start', '<=', form.revaluation_date),
             ('date_stop', '>=', form.revaluation_date),
             ('company_id', '=', company.id),
             ('special', '=', False)],
            limit=1,
            context=context)
        if not period_ids:
            raise osv.except_osv(_('Error!'),
                                 _('There is no period for company %s on %s'
                                   % (company.name, form.revaluation_date)))
        period = period_obj.browse(cr, uid, period_ids[0], context=context)
        new_move_dict = {}
        # over revaluation
        if amount >= 0.01:
            line_data = {
                'debit': amount,
                'account_id': account_id,
            }
            new_move_dict = prepare_move_line(line_data, move_line, line_sums)
        # under revaluation
        elif amount <= -0.01:
            amount = -amount
            line_data = {
                'credit': amount,
                'account_id': account_id,
            }
            new_move_dict = prepare_move_line(line_data, move_line, line_sums)
        return new_move_dict

    def _create_adjust_entries(self, cr, uid, label, form, dict_adjustment, list_dict_moves, context=None):
        """
        Generate entries to adjust balance in the revaluation accounts

        @param account_id: ID of account to be reevaluated
        @param amount: Amount to be written to adjust the balance
        @param label: Label to be written on each entry
        @param form: Wizard browse record containing data

        @return: ids of created move_lines
        """
        context = context or {}

        def create_move():
            reversable = form.journal_id.company_id.reversable_revaluations
            base_move = {'name': label,
                         'journal_id': form.journal_id.id,
                         'period_id': period.id,
                         'date': form.revaluation_date,
                         'to_be_reversed': reversable}
            return move_obj.create(cr, uid, base_move, context=context)

        def create_move_line(move_id, line_data, dict_adjustment):
            base_line = {'name': dict_adjustment['name'],
                         'partner_id': dict_adjustment['partner_id'],
                         'currency_id': dict_adjustment['currency_id'],
                         'amount_currency': dict_adjustment['amount_currency'] or 0.0,
                         'date': dict_adjustment['date'],
                         }
            base_line.update(line_data)
            # we can assume that keys should be equals columns name + gl_
            # but it was not decide when the code was designed. So commented
            # code may sucks:
            # for k, v in sums.items():
            #    line_data['gl_' + k] = v
            base_line['gl_foreign_balance'] = dict_adjustment['gl_foreign_balance']
            base_line['gl_balance'] = dict_adjustment['gl_balance']
            base_line['gl_revaluated_balance'] = dict_adjustment['gl_revaluated_balance']
            base_line['gl_currency_rate'] = dict_adjustment['gl_currency_rate']
            return move_line_obj.create(cr, uid, base_line, context=context)
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        user_obj = self.pool.get('res.users')
        rec_ids = []
        company = form.journal_id.company_id or user_obj.browse(
            cr, uid, uid).company_id
        period_ids = period_obj.search(
            cr, uid,
            [('date_start', '<=', form.revaluation_date),
             ('date_stop', '>=', form.revaluation_date),
             ('company_id', '=', company.id),
             ('special', '=', False)],
            limit=1,
            context=context)
        if not period_ids:
            raise osv.except_osv(_('Error!'),
                                 _('There is no period for company %s on %s'
                                   % (company.name, form.revaluation_date)))
        period = period_obj.browse(cr, uid, period_ids[0], context=context)
        created_ids = []

        ##### CREATE GAIN/LOSS MOVE
        # over revaluation
        move_id = create_move()
        if dict_adjustment['amount'] >= 0.01:
            if company.revaluation_gain_account_id:
                # Create a move line to Credit revaluation gain account
                analytic_acc_id = (company.revaluation_analytic_account_id.id
                                   if company.revaluation_analytic_account_id
                                   else False)
                line_data = {
                    'credit': dict_adjustment['amount'],
                    'account_id': company.revaluation_gain_account_id.id,
                    'move_id': move_id,
                    'analytic_account_id': analytic_acc_id,
                }
                created_ids.append(create_move_line(move_id, line_data, dict_adjustment))
        # under revaluation
        elif dict_adjustment['amount'] <= -0.01:
            amount = -dict_adjustment['amount']
            if company.revaluation_loss_account_id:
                # Create a move line to Credit revaluation gain account
                analytic_acc_id = (company.revaluation_analytic_account_id.id
                                   if company.revaluation_analytic_account_id
                                   else False)
                line_data = {
                    'debit': amount,
                    'account_id': company.revaluation_loss_account_id.id,
                    'move_id': move_id,
                    'analytic_account_id': analytic_acc_id,
                }
                created_ids.append(create_move_line(move_id, line_data, dict_adjustment))
        ##### CREATE ADJUSTMENT MOVE
        rec_list_ids = []
        for x in list_dict_moves:
            line_id, dict_move = x.keys()[0], x.values()[0]
            rec_ids = [line_id]
            line_data = {
                'debit': dict_move.get('debit',0.0),
                'credit': dict_move.get('credit',0.0),
                'account_id': dict_move.get('account_id',False),
                'move_id': move_id,
                'analytic_account_id': False,
            }
            new_id = create_move_line(move_id, line_data, dict_move)
            rec_ids.append(new_id)
            created_ids.append(new_id)
            rec_list_ids.append(rec_ids)
        
        # reconcile entries
        for rec_ids in rec_list_ids:
            if len(rec_ids)>=2:
                reconcile = move_line_obj.reconcile_partial(cr, uid, rec_ids)
                print "===========reconcile completed", rec_ids
        return created_ids

    def revaluate_currency(self, cr, uid, ids, context=None):
        """
        Compute unrealized currency gain and loss and add entries to
        adjust balances

        @return: dict to open an Entries view filtered on generated move lines
        """

        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False


        if context is None:
            context = {}
        user_obj = self.pool.get('res.users')
        account_obj = self.pool.get('account.account')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        currency_obj = self.pool.get('res.currency')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        form = self.browse(cr, uid, ids[0], context=context)
        company = form.journal_id.company_id or user_obj.browse(
            cr, uid, uid).company_id
        if (not company.revaluation_loss_account_id and
            not company.revaluation_gain_account_id and
            not (company.provision_bs_loss_account_id and
                 company.provision_pl_loss_account_id) and
            not (company.provision_bs_gain_account_id and
                 company.provision_pl_gain_account_id)):
            raise osv.except_osv(
                _("Error!"),
                _("No revaluation or provision account are defined"
                  " for your company.\n"
                  "You must specify at least one provision account or"
                  " a couple of provision account."))
        created_ids = []
        # Search for accounts Balance Sheet to be eevaluated
        # on those criterions
        # - deferral method of account type is not None
        account_ids = account_obj.search(
            cr, uid,
            [('user_type.close_method', '!=', 'none'),
             ('currency_revaluation', '=', True)])
        if not account_ids:
            raise osv.except_osv(
                _('Settings Error!'),
                _("No account to be revaluated found. "
                  "Please check 'Allow Currency Revaluation' "
                  "for at least one account in account form."))
        fiscalyear_ids = fiscalyear_obj.search(
            cr, uid,
            [('date_start', '<=', form.revaluation_date),
             ('date_stop', '>=', form.revaluation_date),
             ('company_id', '=', company.id)],
            limit=1,
            context=context)
        if not fiscalyear_ids:
            raise osv.except_osv(
                _('Error!'),
                _('No fiscalyear found for company %s on %s.' %
                  (companym.name, form.revaluation_date)))
        fiscalyear = fiscalyear_obj.browse(
            cr, uid, fiscalyear_ids[0], context=context)
        special_period_ids = [p.id for p in fiscalyear.period_ids
                              if p.special]
        if not special_period_ids:
            raise osv.except_osv(
                _('Error!'),
                _('No special period found for the fiscalyear %s' %
                  fiscalyear.code))
        opening_move_ids = []
        if special_period_ids:
            opening_move_ids = move_obj.search(
                cr, uid, [('period_id', '=', special_period_ids[0])])
            if not opening_move_ids:
                # if the first move is on this fiscalyear, this is the first
                # financial year
                first_move_id = move_obj.search(
                    cr, uid, [('company_id', '=', company.id)],
                    order='date', limit=1)
                if not first_move_id:
                    raise osv.except_osv(_('Error!'),
                                         _('No fiscal entries found'))
                first_move = move_obj.browse(
                    cr, uid, first_move_id[0], context=context)
                if fiscalyear != first_move.period_id.fiscalyear_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('No opening entries in opening period for this '
                          'fiscal year %s' % fiscalyear.code))
        period_ids = [p.id for p in fiscalyear.period_ids]
        if not period_ids:
            raise osv.except_osv(_('Error!'),
                                 _('No period found for the fiscalyear %s' %
                                   fiscalyear.code))
        bankandcash_account_ids = account_obj.search(cr, uid, [('id','in',account_ids),('user_type.code','in',['bank','cash'])])
        account_ids = [x for x in account_ids if x not in bankandcash_account_ids]
        unreconcile_account_ids = account_obj.search(cr, uid, [('id','in',account_ids),('reconcile','=',True)])
        account_ids = [x for x in account_ids if x not in unreconcile_account_ids]
        if bankandcash_account_ids:
            # Get balance sums
            account_sums = account_obj.compute_revaluations_bankandcash(
                cr, uid,
                bankandcash_account_ids,
                period_ids,
                form.revaluation_date,
                context=context)
            for account_id, account_tree in account_sums.iteritems():
                for currency_id, sums in account_tree.iteritems():
                    if not sums['balance']:
                        continue
                    # Update sums with compute amount currency balance
                    diff_balances = self._compute_unrealized_currency_gl(
                        cr, uid, currency_id,
                        sums, form, context=context)
                    account_sums[account_id][currency_id].\
                        update(diff_balances)
            # Create entries only after all computation have been done
            for account_id, account_tree in account_sums.iteritems():
                for currency_id, sums in account_tree.iteritems():
                    adj_balance = sums.get('unrealized_gain_loss', 0.0)
                    if not adj_balance:
                        continue

                    rate = sums.get('currency_rate', 0.0)
                    label = self._format_label(
                        cr, uid, form.label, account_id, currency_id, rate)

                    # Write an entry to adjust balance
                    new_ids = self._write_adjust_balance(
                        cr, uid,
                        account_id,
                        currency_id,
                        False,
                        adj_balance,
                        label,
                        form,
                        sums,
                        context=context)
                    created_ids.extend(new_ids)

        if unreconcile_account_ids:
            # Get balance sums
            for account_id in unreconcile_account_ids:
                move_line_ids = move_line_obj.search(cr, uid, [('state','=','valid'),('reconcile_id', '=', False),('account_id', '=', account_id),('currency_id','!=',False),('date','<=',form.revaluation_date)])
                dict_gain_loss, dict_moves = {}, {}
                for line in move_line_obj.browse(cr, uid, move_line_ids):
                    if _remove_noise_in_o2m():
                        continue
                    # Compute unrealized gain loss
                    ctx_rate = context.copy()
                    ctx_rate['date'] = form.rate_date
                    ctx_rate['currency_rate_type_id'] = form.currency_type and form.currency_type.id or False
                    cp_currency_id = form.journal_id.company_id.currency_id.id
                    line_currency = currency_obj.browse(cr, uid, line.currency_id.id, context=ctx_rate)

                    foreign_balance = line.amount_residual_currency
                    balance = line.amount_residual
                    unrealized_gain_loss = 0.0
                    ctx_rate['revaluation'] = True
                    adjusted_balance = currency_obj.compute(
                        cr, uid, line.currency_id.id, cp_currency_id, foreign_balance,
                        currency_rate_type_to=(form.currency_type and form.currency_type.id or False),
                        context=ctx_rate)
                    unrealized_gain_loss = adjusted_balance - balance
                    adj_balance = currency_obj.round(cr, uid, line.currency_id, unrealized_gain_loss)
                    if not adj_balance:
                        continue
                    # prepare dict moves
                    label = self._format_label(
                            cr, uid, form.label, line.account_id.id, line.currency_id.id, rate)
                    line_sums = {
                        'revaluated_balance' : adjusted_balance,
                        'unrealized_gain_loss' : unrealized_gain_loss,
                        'currency_rate' : line_currency.rate,
                    }
                    partner_id = line.partner_id and line.partner_id.id or False
                    if (line.currency_id.id, partner_id) not in dict_gain_loss:
                        dict_gain_loss.update({(line.currency_id.id, partner_id):{
                                'name':label,
                                'amount':0.0,
                                'partner_id': partner_id,
                                'currency_id': line.currency_id.id,
                                'amount_currency': 0.0,
                                'date': form.revaluation_date,
                                'gl_balance' : 0.0,
                                'gl_currency_rate' : line_currency.rate,
                                'gl_foreign_balance' : 0.0,
                                'gl_revaluated_balance' : 0.0,
                            }})
                        dict_moves.update({(line.currency_id.id, partner_id):[]})
                    dict_gain_loss[(line.currency_id.id, partner_id)]['amount']+=adj_balance
                    dict_gain_loss[(line.currency_id.id, partner_id)]['gl_foreign_balance']+=line.amount_residual_currency
                    dict_gain_loss[(line.currency_id.id, partner_id)]['gl_balance']+=line.amount_residual
                    dict_gain_loss[(line.currency_id.id, partner_id)]['gl_revaluated_balance']+=adj_balance

                    dict_moves[(line.currency_id.id, partner_id)].append({line.id:self._prepare_adjust_dict_move(cr, uid, line.account_id.id, \
                                    line.currency_id.id,  partner_id, adj_balance, \
                                    label, form, line, line_sums, context=None)})
                for keyy in dict_gain_loss.keys():
                    created_ids.extend(self._create_adjust_entries(cr, uid, label, form, dict_gain_loss[keyy], \
                        dict_moves[keyy]))
        if account_ids:
            # Get balance sums
            account_sums = account_obj.compute_revaluations(
                cr, uid,
                account_ids,
                period_ids,
                form.revaluation_date,
                context=context)
            for account_id, account_tree in account_sums.iteritems():
                for currency_id, currency_tree in account_tree.iteritems():
                    for partner_id, sums in currency_tree.iteritems():
                        if not sums['balance']:
                            continue
                        # Update sums with compute amount currency balance
                        diff_balances = self._compute_unrealized_currency_gl(
                            cr, uid, currency_id,
                            sums, form, context=context)
                        account_sums[account_id][currency_id][partner_id].\
                            update(diff_balances)
            # Create entries only after all computation have been done
            for account_id, account_tree in account_sums.iteritems():
                for currency_id, currency_tree in account_tree.iteritems():
                    for partner_id, sums in currency_tree.iteritems():
                        adj_balance = sums.get('unrealized_gain_loss', 0.0)
                        if not adj_balance:
                            continue

                        rate = sums.get('currency_rate', 0.0)
                        label = self._format_label(
                            cr, uid, form.label, account_id, currency_id, rate)

                        # Write an entry to adjust balance
                        new_ids = self._write_adjust_balance(
                            cr, uid,
                            account_id,
                            currency_id,
                            partner_id,
                            adj_balance,
                            label,
                            form,
                            sums,
                            context=context)
                        created_ids.extend(new_ids)

        # print "FALSE", account_sum
        if created_ids:
            return {'domain': "[('id', 'in', %s)]" % created_ids,
                    'name': _("Created revaluation lines"),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'auto_search': True,
                    'res_model': 'account.move.line',
                    'view_id': False,
                    'search_view_id': False,
                    'type': 'ir.actions.act_window'}
        else:
            raise osv.except_osv(_("Warning"),
                                 _("No accounting entry have been posted."))
