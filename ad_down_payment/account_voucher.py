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
from lxml import etree

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class account_voucher(osv.osv):
    
    _inherit = 'account.voucher'
    
    _columns = {
            'purchase_id' :fields.many2one('purchase.order', "Purchase ID"),
            'sale_id' :fields.many2one('sale.order', "Purchase ID"),
            'dp':fields.boolean('Down Payment'),
            'name_dp':fields.char('Memo', size=256, readonly=True),
            'amount_dp':fields.float('Total',readonly=True),
            'date_dp':fields.date('Date', readonly=True,),
            'partner_id_dp':fields.many2one('res.partner', 'Supplier', readonly=True,),
            'invoice_id': fields.many2one('account.invoice', "Account Voc", readonly=True),
                }
    

    
account_voucher()

###############################################
class account_voucher_line(osv.osv):
    _inherit = 'account.voucher.line'
    
    def onchange_anti(self, cr, uid, ids, amount_dp):
        print "111----"
        
        
        #raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal and make sure it is activated !'))
#        return {
#            'value' : {'amount_dp' : ''}
#        }
    
    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.voucher_id.date})
            res = {}
            company_currency = line.voucher_id.journal_id.company_id.currency_id.id
            voucher_currency = line.voucher_id.currency_id.id
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
                res['dp_amount_unreconciled'] = 0.0

            elif move_line.currency_id:
                res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, voucher_currency, move_line.amount_currency, context=ctx)
            elif move_line and move_line.credit > 0:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit, context=ctx)
            else:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.debit, context=ctx)

            if move_line:
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
#            ####################################################
#            if move_line:
#                res['dp_amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, voucher_currency, abs(move_line.amount_residual_currency), context=ctx)
#            
#            ####################################################
            rs_data[line.id] = res
        return rs_data
    
    def write(self, cr, user, ids, vals, context=None):
        '''
            Add invoice and description in payment modification line
        '''
        if type(ids) == type([]):
            move = self.browse(cr, user,ids[0]).move_line_id
        else:
            move = self.browse(cr, user,ids).move_line_id
        if move:
            vals['invoice_id'] = move.invoice and move.invoice.id
            #vals['invoice_number'] = move.invoice and move.invoice.invoice_no
            #vals['name'] = move.invoice and move.invoice.number

        return super(account_voucher_line, self).write(cr, user, ids, vals, context)

    def create(self, cr, user, vals, context=None):
        '''
            Add invoice and description in payment modification line
        '''
        if vals.has_key('move_line_id') and vals['move_line_id']:
            move = self.pool.get('account.move.line').browse(cr, user,vals['move_line_id'])
            vals['invoice_id'] = move.invoice and move.invoice.id
            #vals['invoice_number'] = move.invoice and move.invoice.invoice_no
            #vals['name'] = move.invoice and move.invoice.number
        return super(account_voucher_line, self).create(cr, user, vals, context)
    
    _columns = {
            'invoice_id'            : fields.many2one('account.invoice','Invoice'),
            #'amount_dp_relation': fields.related('invoice_id', 'amount_dp', type='float', string='Downpayment', store=True, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
            'currency_id'           : fields.related('invoice_id', 'currency_id', relation='res.currency',type='many2one', string='Currency',store=True, readonly=True),
            'amount_dp'             : fields.float('Downpayment'),
            'downpayment_id'        : fields.many2one('downpayment', 'Downpayment'),
            'amount_dp_original'    : fields.float('Downpayment Original'),
            #'dp_amount_unreconciled': fields.function(_compute_balance, method=True, multi='dc', type='float', string='DP Unreconcile', store=True),
            #'number': fields.related('amount_dp', 'amount_dp', type='char', readonly=True, size=64, relation='account.voucher.line', store=True, string='Number'),
                }
account_voucher_line()