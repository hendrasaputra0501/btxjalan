# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from datetime import datetime
from dateutil.relativedelta import relativedelta
from lxml import etree

from osv import osv
from osv import fields

class account_aged_trial_balance_i(osv.osv_memory):
    _inherit = 'account.aged.trial.balance'
    _columns = {
        'type': fields.selection([('pdf','PDF'),], 'Type', required=False),
# TODO: create XLS report for this 'aged trial balance'
#        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=True),
    }
    _defaults = {
        'type': lambda *a: 'pdf',
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        res = {}
        if context is None:
            context = {}

        wizard = self.browse(cr, uid, ids[0], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['period_length', 'direction_selection'])[0])

        period_length = data['form']['period_length']
        if period_length<=0:
            raise osv.except_osv(_('UserError'), _('You must enter a period length that cannot be 0 or below !'))
        if not data['form']['date_from']:
            raise osv.except_osv(_('UserError'), _('Enter a Start date !'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")

        if data['form']['direction_selection'] == 'past':
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length)
                res[str(i)] = {
                    'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop - relativedelta(days=1)
        else:
            for i in range(5):
                stop = start + relativedelta(days=period_length)
                res[str(5-(i+1))] = {
                    'name': (i!=4 and str((i) * period_length)+'-' + str((i+1) * period_length) or ('+'+str(4 * period_length))),
                    'start': start.strftime('%Y-%m-%d'),
                    'stop': (i!=4 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop + relativedelta(days=1)
        data['form'].update(res)

        final_report = {
            'pdf': 'aged.trial.balance.optim',
            'xls': 'aged_trial_balance.xls',
        }[wizard.type]

        return {
            'type': 'ir.actions.report.xml',
            'report_name': final_report,
            'datas': data
        }

account_aged_trial_balance_i()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
