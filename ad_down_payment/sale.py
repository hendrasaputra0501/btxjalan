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
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

#
# Model definition
#
class sale_order(osv.osv):
    _inherit = "sale.order"
    
    _columns = {
            'account_voc_line': fields.one2many('account.voucher', 'sale_id' ,"Account Voc", readonly=True),
            
            'dp': fields.boolean('DP'),
                }
    
    _defaults = {
            'dp': False,
                }
    
sale_order()

class downpayment_sale_notification(osv.osv_memory):
    _name = "downpayment.sale.notification"
    _description = "Sales Advance Payment Invoice"
    _columns = {
       
                }
downpayment_sale_notification()

class sale_advance_payment_inv(osv.osv_memory):
    _name = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"
    _columns = {
        #'account_id':fields.many2one('account.account', 'Account', required=True, ),
        'amount': fields.float('Down Payment Amount', digits_compute=dp.get_precision('Account'), required=True),
        'name': fields.char('Down Payment Description', size=64, required=True),
        'journal_id':fields.many2one('account.journal', 'Receipt Method', required=True),
    }
    
    def create_payment_sale(self, cr, uid, ids, context=None):
        
        """
             To create invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs if we want more than one
             @param context: A standard dictionary

             @return:

        """
        list_inv = []
        lines = []
        obj_sale = self.pool.get('sale.order')
        obj_voc_lines = self.pool.get('account.voucher.line')
        voc_obj = self.pool.get('account.voucher')
        if context is None:
            context = {}
        
        for sale_adv_obj in self.browse(cr, uid, ids, context=context):
            
            for sale in obj_sale.browse(cr, uid, context.get('active_ids', []), context=context):
                
                obj_sale.write(cr, uid, context.get('active_ids', []), {'dp': True})
                
                
            vals_line = {
                            "name": sale_adv_obj.name,
                            "account_id": sale.partner_id.property_account_receivable.id,
                            "amount": sale_adv_obj.amount,
                            "partner_id": sale.partner_id.id,
                            
                            }
            lines.append((0,0,vals_line))
            
            vals = {
                    "account_id": sale_adv_obj.journal_id.default_debit_account_id.id,
                    "partner_id": sale.partner_id.id,
                    "amount": sale_adv_obj.amount,
                    "line_cr_ids": lines,
                    "type": "receipt",
                    "name_dp": sale_adv_obj.name,
                    "partner_id_dp": sale.partner_id.id,
                    "amount_dp": sale_adv_obj.amount,
                    "date_dp" : time.strftime('%Y-%m-%d'),
                    "dp": True,
                    "sale_id" : sale.id,
                    "journal_id" : sale_adv_obj.journal_id.id,
                    }


            voc_obj.create(cr, uid, vals)
            
                
   
        return {
            'name': 'Downpayment Notification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'downpayment.sale.notification',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }


sale_advance_payment_inv()