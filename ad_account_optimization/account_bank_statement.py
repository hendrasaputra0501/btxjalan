# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
from osv import osv

class account_bank_statement_line_i(osv.osv):
    _inherit = 'account.bank.statement.line'
    _order = 'sequence ASC'

    def _get_default_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        cdate = context.get('date', '')
        if cdate:
            return cdate
        return time.strftime('%Y-%m-%d')

    _defaults = {
        'date': _get_default_date,
    }

account_bank_statement_line_i()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
