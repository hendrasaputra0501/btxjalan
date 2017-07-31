# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011 Thamini S.à.R.L (<http://www.thamini.com>)
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
import re
from report import report_sxw
from account.report.account_partner_ledger import third_party_ledger
#from common_report_header import common_report_header

class third_party_ledger_i(third_party_ledger):

    def set_context(self, objects, data, ids, report_type=None):
        obj_move = self.pool.get('account.move.line')
        obj_partner = self.pool.get('res.partner')
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=data['form'].get('used_context', {}))
        ctx2 = data['form'].get('used_context',{}).copy()
        self.initial_balance = data['form'].get('initial_balance', True)
        if self.initial_balance:
            ctx2.update({'initial_bal': True})
        self.init_query = obj_move._query_get(self.cr, self.uid, obj='l', context=ctx2)
        self.reconcil = True
        if data['form']['filter'] == 'unreconciled':
            self.reconcil = False
        self.result_selection = data['form'].get('result_selection', 'customer')
        self.amount_currency = data['form'].get('amount_currency', False)
        self.target_move = data['form'].get('target_move', 'all')
        PARTNER_REQUEST = ''
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        if (data['model'] == 'res.partner'):
            ## Si on imprime depuis les partenaires
            if ids:
                PARTNER_REQUEST =  "AND line.partner_id IN %s",(tuple(ids),)
        if self.result_selection == 'supplier':
            self.ACCOUNT_TYPE = ['payable']
        elif self.result_selection == 'customer':
            self.ACCOUNT_TYPE = ['receivable']
        else:
            self.ACCOUNT_TYPE = ['payable','receivable']

        self.cr.execute(
            "SELECT a.id " \
            "FROM account_account a " \
            "LEFT JOIN account_account_type t " \
                "ON (a.type=t.code) " \
                'WHERE a.type IN %s' \
                "AND a.active", (tuple(self.ACCOUNT_TYPE), ))
        self.account_ids = [a for (a,) in self.cr.fetchall()]
        partner_to_use = []
        self.cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.partner_id IS NOT NULL " \
                    "AND l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "AND am.state IN %s"
#                    "AND " + self.query +" " \
                    "AND l.account_id IN %s " \
                    " " + PARTNER_REQUEST + " " \
                    "AND account.active ",
                (tuple(move_state), tuple(self.account_ids),))

        res = self.cr.dictfetchall()
        for res_line in res:
            partner_to_use.append(res_line['partner_id'])
        new_ids = partner_to_use
        self.partner_ids = new_ids
        objects = obj_partner.browse(self.cr, self.uid, new_ids)
        return super(third_party_ledger_i, self).set_context(objects, data, new_ids, report_type)

report_sxw.report_sxw('report.third.party.ledger.optim', 'res.partner',
        'addons/ad_account_optimization/report/account_partner_ledger.rml', parser=third_party_ledger_i,
        header='internal')
report_sxw.report_sxw('report.third.party.ledger.optim.other', 'res.partner',
        'addons/ad_account_optimization/report/account_partner_ledger_other.rml', parser=third_party_ledger_i,
        header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
