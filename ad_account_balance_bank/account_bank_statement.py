#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Alam Dewata Utama, PT    
#   Copyright (C) 2010-2014 ADSOft (<http://www.adsoft.co.id>). 
#   All Rights Reserved
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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class account_bank_statement_line(osv.osv):
    """ inherited account.bank.statement.line """
    _inherit = 'account.bank.statement.line'
    
    def _get_balance(self, cr, uid, ids, field_name, arg, context=None):
        account_obj = self.pool.get('account.account')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = account_obj.browse(cr, uid, line.account_id.id, context=context).balance
        return res

    def onchange_account_id(self, cr, uid, ids, account_id, context=None):
        account_obj = self.pool.get('account.account')
        context = context or {}
        res = {'value': {}}
        if account_id:
            res['value']['account_balance'] = account_obj.browse(cr, uid, account_id, context=context).balance
        print "res: %s" % res
        return res

    _columns = {
        'account_balance': fields.function(_get_balance, type='float', method=True, string='Balance', store=True, readonly=True, digits_compute=dp.get_precision('Account')),
    }

#     def default_get(self, cr, uid, fields_list, context=None):
#         """
#         Returns default values for fields
#         @param fields_list: list of fields, for which default values are required to be read
#         @param context: context arguments, like lang, time zone
# 
#         @return: Returns a dict that contains default values for fields
#         """
#         if context is None:
#             context = {}
#         account_id = context.get('account_id', False)
#         account_obj = self.pool.get('account.account')
#         values = super(account_bank_statement_line, self).default_get(cr, uid, fields_list, context=context)
#         if not account_id:
#             return values
#         account_balance = account_obj.browse(cr, uid, account_id, context=context).balance
#         values.update({
#             'account_balance':account_balance,
#         })
#         print "values: %s" %values
#         return values

account_bank_statement_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: