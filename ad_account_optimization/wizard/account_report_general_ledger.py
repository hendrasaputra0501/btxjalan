# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields

class account_report_general_ledger_opti(osv.osv_memory):
    _inherit = 'account.report.general.ledger'
    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True),
        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=False),
        #'currency_rate': fields.boolean('With Currency Rate ?', help="Converted All balance with Current rate Currency(default= IDR")
    }
    _defaults = {
        'type': lambda *a: 'pdf',
        'amount_currency': lambda *a: False,
        'landscape': lambda *a: True,
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['type', 'landscape',  'initial_balance', 'amount_currency', 'sortby'])[0])
        #print data
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})
        if wizard.type == 'xls':
            final_report = 'account.general.ledger_landscape.xls'
        elif wizard.type == 'pdf':
            final_report = 'account.general.ledger.ls'
        return { 'type': 'ir.actions.report.xml', 'report_name': final_report, 'datas': data}

account_report_general_ledger_opti()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
