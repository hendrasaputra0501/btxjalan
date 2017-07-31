# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields

class account_partner_balance_i(osv.osv_memory):
    _inherit = 'account.partner.balance'
    _columns = {
        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=False),
        'reconciled': fields.boolean('Include Reconciled Entries'),
    }
    _defaults = {
        'type': lambda *a: 'pdf',
        'reconciled': lambda *a: True,
    }

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(account_partner_balance_i, self).pre_print_report(cr, uid, ids, data, context=context)
        data.update(self.read(cr, uid, ids, ['reconciled'])[0])
        return data

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['display_partner'])[0])
        final_report = {
            'pdf': 'account.partner.balance.opti',
            'xls': 'account.partner.balance.xls',
        }[wizard.type]
        return {'type': 'ir.actions.report.xml', 'report_name': final_report, 'datas': data}

account_partner_balance_i()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
