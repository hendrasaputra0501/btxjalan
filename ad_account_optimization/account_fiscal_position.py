# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields

class account_fiscal_position_tax_global(osv.osv):
    _inherit = 'account.fiscal.position.tax'
    _name = 'account.fiscal.position.tax.global'

    _columns = {
        'operator': fields.selection([('gt','Greated Than'),('lt','Lesser Than')], 'Operator', required=True),
        'amount': fields.float('Amount', required=True),
    }

    _defaults = {
        'operator': lambda *a: 'gt',
    }
account_fiscal_position_tax_global()

class account_fiscal_position_i(osv.osv):
    _inherit = 'account.fiscal.position'

    _columns = {
        'global_tax_ids': fields.one2many('account.fiscal.position.tax.global', 'position_id', 'Tax Mapping'),
    }

    # def map_global_tax(self, cr, uid, amount, fposition_id, taxes, context=None):
    #     if context is None:
    #         context = {}
    #     if not taxes:
    #         return []
    #     if not fposition_id:
    #         return map(lambda x: x.id, taxes)
    #     result = []
    #     for t in taxes:
    #         ok = False
    #         for tax in fposition_id.global_tax_ids:
    #             if tax.operator == 'gt' and not (amount > tax.amount):
    #                 continue
    #             if tax.operator == 'lt' and not (amount < tax.amount):
    #                 continue
    #             if tax.tax_src_id.id == t.id:
    #                 if tax.tax_dest_id:
    #                     result.append(tax.tax_dest_id.id)
    #                 ok=True
    #         if not ok:
    #             result.append(t.id)
    #     return result

account_fiscal_position_i()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
