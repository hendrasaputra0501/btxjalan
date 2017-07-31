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
#from common_report_header import common_report_header
from report import report_sxw
from account.report.account_journal import journal_print

class journal_print_i(journal_print):

    def set_context(self, objects, data, ids, report_type=None):
        obj_move = self.pool.get('account.move.line')
        new_ids = ids
        self.query_get_clause = ''
        self.target_move = data['form'].get('target_move', 'all')
        if (data['model'] == 'ir.ui.menu'):
            self.period_ids = tuple(data['form']['periods'])
            self.journal_ids = tuple(data['form']['journal_ids'])
            new_ids = data['form'].get('active_ids', [])
            self.query_get_clause = 'AND '
            self.query_get_clause += obj_move._query_get(self.cr, self.uid, obj='l', context=data['form'].get('used_context', {}))
            self.sort_selection = data['form'].get('sort_selection', 'date')
            objects = self.pool.get('account.journal.period').browse(self.cr, self.uid, new_ids)
        elif new_ids:
            #in case of direct access from account.journal.period object, we need to set the journal_ids and periods_ids
            self.cr.execute('SELECT period_id, journal_id FROM account_journal_period WHERE id IN %s', (tuple(new_ids),))
            res = self.cr.fetchall()
            self.period_ids, self.journal_ids = zip(*res)
        return super(journal_print_i, self).set_context(objects, data, ids, report_type=report_type)

report_sxw.report_sxw('report.account.journal.period.print.optim', 'account.journal.period', 'addons/ad_account_optimization/report/account_journal.rml', parser=journal_print_i, header='internal')
report_sxw.report_sxw('report.account.journal.period.print.sale.purchase.optim', 'account.journal.period', 'addons/ad_account_optimization/report/account_journal_sale_purchase.rml', parser=journal_print_i, header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
