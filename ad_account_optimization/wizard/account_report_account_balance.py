# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields

class account_balance_report(osv.osv_memory):
    _inherit = 'account.balance.report'
    _columns = {
        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=False),
        #'currency_rate': fields.boolean('With Currency Rate ?', help="Converted All balance with Current rate Currency(default= IDR"),
        #'rate_opt': fields.float('Rate', digits=(16,4), help="Fill this blank with Rate Currency(default= IDR")
    }

    _defaults = {
        'type': lambda *a: 'pdf',
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['type'])[0])
        if wizard.type == 'xls':
            final_report = 'account.account.balance.xls'
        elif wizard.type == 'pdf':
            final_report = 'account.trial.balance.pt'
        return {'type': 'ir.actions.report.xml', 'report_name': final_report, 'datas': data}

account_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
