# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from report import report_sxw
from account.report.account_partner_balance import partner_balance

class partner_balance_i(partner_balance):

    def set_context(self, objects, data, ids, report_type=None):
        r = super(partner_balance_i, self).set_context(objects, data, ids, report_type=report_type)
        if not data.get('reconciled',True):
            self.query += ' AND l.reconcile_id IS NULL '
        return r

report_sxw.report_sxw('report.account.partner.balance.opti',
                      'res.partner',
                      'addons/ad_account_optimization/report/account_partner_balance.rml',
                      parser=partner_balance_i,
                      header='internal')
