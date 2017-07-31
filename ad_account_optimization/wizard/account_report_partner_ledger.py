# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields

class account_partner_ledger_opti(osv.osv_memory):
    _inherit = 'account.partner.ledger'
    _columns = {
        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=False),
    }
    _defaults = {
        'type': lambda *a: 'pdf',
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['initial_balance', 'reconcil', 'page_split', 'amount_currency'])[0])

        final_report = ''
        if wizard.type == 'pdf':
            if data['form']['page_split']:
                final_report = 'third.party.ledger.optim'
            else:
                final_report = 'third.party.ledger.optim.other'
        elif wizard.type == 'xls':
            final_report = 'account.third_party_ledger.xls'
        else:
            return {}


        return {
            'type': 'ir.actions.report.xml',
            'report_name': final_report,
            'datas': data,
        }

account_partner_ledger_opti()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
