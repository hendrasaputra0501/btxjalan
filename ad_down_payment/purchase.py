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
class landed_cost(osv.osv):
    _name = 'landed.cost'
    _columns = {
            'name' : fields.char('Landed Cost Name', size=32),
            'po_id': fields.many2one('purchase.order', 'Purchase Order Id'),
            'account_id': fields.many2one('account.account', 'Account'),
            'amount': fields.float('Price'),
                }
    
    _defaults = {
            'name' : "/"
                 }
    
landed_cost()

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def action_invoice_create(self, cr, uid, ids, *args):
        print "==============================================================================&&&***"
        print "Buat Invoice :::"
        res = False

        journal_obj = self.pool.get('account.journal')
        for o in self.browse(cr, uid, ids):
            il = []
            todo = []
            for ol in o.order_line:
                todo.append(ol.id)
                if ol.product_id:
                    a = ol.product_id.product_tmpl_id.property_account_expense.id
                    if not a:
                        a = ol.product_id.categ_id.property_account_expense_categ.id
                    if not a:
                        raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (ol.product_id.name, ol.product_id.id,))
                else:
                    a = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category').id
                fpos = o.fiscal_position or False
                a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
                il.append(self.inv_line_create(cr, uid, a, ol))
            
            ################Landed Cost################## 
            
            for cost in o.landed_cost_line:
                print "Landed Cost :xxx", cost.name
                
                landed_cost_line = (0, False, {
                     'name':cost.name or False,
                     'account_id':cost.account_id.id or False,
                     'price_unit':cost.amount or False,
                     })
                il.append(landed_cost_line)
            print "Tes INis"
            #################Down Payment#################
            for dp in o.downpayment_line:
                dp_amount = 0.0
                dp_amount = dp_amount + dp.amount
                print "Amount DP ;_*****---------------->>", dp_amount
                
            ##############################################

            a = o.partner_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', o.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error !'),
                    _('There is no purchase journal defined for this company: "%s" (id:%d)') % (o.company_id.name, o.company_id.id))
            inv = {
                'name': o.partner_ref or o.name,
                'reference': o.partner_ref or o.name,
                'account_id': a,
                'type': 'in_invoice',
                'partner_id': o.partner_id.id,
                'currency_id': o.pricelist_id.currency_id.id,
                'address_invoice_id': o.partner_address_id.id,
                'address_contact_id': o.partner_address_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'origin': o.name,
                'invoice_line': il,
                'fiscal_position': o.fiscal_position.id or o.partner_id.property_account_position.id,
                'payment_term': o.partner_id.property_payment_term and o.partner_id.property_payment_term.id or False,
                'company_id': o.company_id.id,
            }
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv, {'type':'in_invoice'})
            self.pool.get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'in_invoice'}, set_total=True)
            self.pool.get('purchase.order.line').write(cr, uid, todo, {'invoiced':True})
            self.write(cr, uid, [o.id], {'invoice_ids': [(4, inv_id)]})
            res = inv_id
            
#            #########Tambahan Untuk DP########
#            print "INV_ID:::", inv_id
#            print "pur_id :::", o.id
#            account_voc_id_search = self.pool.get('account.voucher').search(cr, uid,[('purchase_id','=',o.id)])
#            account_voc_id_browse = self.pool.get('account.voucher').browse(cr, uid,account_voc_id_search)
#            
#            
#            
#            for a in account_voc_id_browse:
#                print "=================>>>", a
#                if a:
##                   account_inv_id_search = self.pool.get('account.invoice').search(cr, uid,[('purchase_id','=',o.id),('state','!=','cancel')])
##                   account_inv_id_browse = self.pool.get('account.invoice').browse(cr, uid,account_inv_id_search)
##                    
##                    for inv_id in account_inv_id_browse:
##                        inv_id.id
#                    
#                    
#                    account_voc_id_search = self.pool.get('account.voucher').write(cr, uid,[a.id],{'invoice_id':inv_id})
#            
#            print "IDS ::", o.id
#            
#            ################
            
        return res

    
    _columns = {
            'account_voc_line': fields.one2many('account.voucher', 'purchase_id' ,"Account Voc", readonly=True),
            'dp': fields.boolean('DP'),
            'landed_cost_line': fields.one2many('landed.cost','po_id','Landed Cost Line'),
            'landed_cost_check': fields.selection([('free', 'Free'),('landed_cost', 'Landed Cost')], 'Charges'),
            
            ###########################################
            'downpayment_line'  : fields.one2many('downpayment.line', 'purchase_id' ,"Downpayment Lines", readonly=True),
            'downpayment_id'    : fields.many2one('downpayment','Downpayment'),
            ###########################################
                }
    
    _defaults = {
            'dp': False,
            'landed_cost_check': 'free',
                }
    
purchase_order()

#class purchase_order_line(osv.osv):
#    
#    _inherit = "purchase.order.line"
#    _columns = {
#        'virtual': fields.boolean('Budget Virtual', readonly=True),
#    }
#    
#purchase_order_line()

class downpayment_notification(osv.osv_memory):
    _name = "downpayment.notification"
    _description = "Sales Advance Payment Invoice"
    _columns = {
       
                }
downpayment_notification()

class purchase_advance_payment_inv(osv.osv_memory):
    _name = "purchase.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"
    _columns = {
        #'account_id':fields.many2one('account.account', 'Account', required=True, ),
        'amount': fields.float('Down Payment Amount', digits_compute=dp.get_precision('Account'), required=True),
        'name': fields.char('Down Payment Description', size=64, required=True),
        'journal_id':fields.many2one('account.journal', 'Payment Method', required=True),
    }
    
    def create_payment(self, cr, uid, ids, context=None):
        obj_dp      = self.pool.get('downpayment')
        obj_dp_line = self.pool.get('downpayment.line')
        list_inv = []
        lines = []
        obj_purchase = self.pool.get('purchase.order')
        obj_voc_lines = self.pool.get('account.voucher.line')
        voc_obj = self.pool.get('account.voucher')
        
        if context is None:
            context = {}
            
        for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
            for purchase in obj_purchase.browse(cr, uid, context.get('active_ids', []), context=context):
                dp_account_id = purchase.company_id.downpayment_account_id.id
                if not dp_account_id:
                    raise osv.except_osv(_('Error !'), _('Please define a Downpayment Account !'))
                dp_cr = purchase.downpayment_id
        if not dp_cr:
            for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
                for purchase in obj_purchase.browse(cr, uid, context.get('active_ids', []), context=context):
                    print "Amount----------***>>", purchase_adv_obj.amount
                    dp_desc     = purchase_adv_obj.name
                    amount      = purchase_adv_obj.amount
                    journal_id  = purchase_adv_obj.journal_id.id
                    purchase_id = context.get('active_ids', [])[0]
                    currency_id = purchase.pricelist_id.currency_id.id
                    company_id  = purchase.company_id.id
                    print "purchase_id-------------->>", purchase_id
                #obj_purchase.write(cr, uid, context.get('active_ids', []), {'dp': True})
                
                vals_line = {
                        'name'          : dp_desc,
                        #'dp_id'         : fields.many2one('downpayment', 'ID'),
                        'amount'        : amount,
                        'account_id'    : dp_account_id,
                        'purchase_id'   : purchase_id,
                                
                                }
                lines.append((0,0,vals_line))
                
                vals = {
                    'name'          : '/',
                    'dp_line'       : lines,
                    'journal_id'    : journal_id,
                    'ref'           : dp_desc,
                    'date'          : time.strftime('%Y-%m-%d'),
                    'currency_id'   : currency_id,
                    'company_id'    : company_id,
                    #'used'          : fields.boolean('Used'),
                    'partner_id'    : purchase.partner_id.id,
                        }
                
                dp_id = obj_dp.create(cr, uid, vals)
                obj_purchase.write(cr, uid, context.get('active_ids', []), {'dp': True, 'downpayment_id': dp_id})
        
        elif dp_cr:
            for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
                for purchase in obj_purchase.browse(cr, uid, context.get('active_ids', []), context=context):
                    dp_desc     = purchase_adv_obj.name
                    amount      = purchase_adv_obj.amount
                    journal_id  = purchase_adv_obj.journal_id.id
                    purchase_id = context.get('active_ids', [])[0]
                    
                    vals_line = {
                        'name'          : dp_desc,
                        #'dp_id'         : fields.many2one('downpayment', 'ID'),
                        'amount'        : amount,
                        'account_id'    : dp_account_id,
                        'purchase_id'   : purchase_id,
                        'dp_id'         : dp_cr.id,
                                }
                    lines.append((0,0,vals_line))
                    obj_dp_line.create(cr, uid, vals_line)
        
        return {
            'name'      : 'Downpayment Notification',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'downpayment.notification',
            'type'      : 'ir.actions.act_window',
            'target'    : 'new',
            'context'   : context
            }
    
#    def create_payment2(self, cr, uid, ids, context=None):
#        """
#             To create invoices.
#
#             @param self: The object pointer.
#             @param cr: A database cursor
#             @param uid: ID of the user currently logged in
#             @param ids: the ID or list of IDs if we want more than one
#             @param context: A standard dictionary
#
#             @return:
#
#        """
#        list_inv = []
#        lines = []
#        obj_purchase = self.pool.get('purchase.order')
#        obj_voc_lines = self.pool.get('account.voucher.line')
#        voc_obj = self.pool.get('account.voucher')
#        if context is None:
#            context = {}
#            
#        for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
#            for purchase in obj_purchase.browse(cr, uid, context.get('active_ids', []), context=context):
#                
#                obj_purchase.write(cr, uid, context.get('active_ids', []), {'dp': True})
#                
#            vals_line = {
#                            "name": purchase_adv_obj.name,
#                            "account_id": purchase.partner_id.property_account_payable.id,
#                            "amount": purchase_adv_obj.amount,
#                            "partner_id": purchase.partner_id.id,
#                            
#                            }
#            lines.append((0,0,vals_line))
#            
#            vals = {
#                    "account_id": purchase_adv_obj.journal_id.default_credit_account_id.id,
#                    "partner_id": purchase.partner_id.id,
#                    "amount": purchase_adv_obj.amount,
#                    "line_dr_ids": lines,
#                    "type": "payment",
#                    "name_dp": purchase_adv_obj.name,
#                    "partner_id_dp": purchase.partner_id.id,
#                    "amount_dp": purchase_adv_obj.amount,
#                    "date_dp" : time.strftime('%Y-%m-%d'),
#                    "dp": True,
#                    "purchase_id" : purchase.id,
#                    "journal_id" : purchase_adv_obj.journal_id.id,
#                    }
#            
#            voc_obj.create(cr, uid, vals)
#            
##            #########Tambahan Untuk DP########
##            
##            account_voc_id_search = self.pool.get('account.voucher').search(cr, uid,[('purchase_id','=',purchase.id)])
##            account_voc_id_browse = self.pool.get('account.voucher').browse(cr, uid,account_voc_id_search)
##            
##            for a in account_voc_id_browse:
##                print "=================>>>", a
##                if a:
##                    account_inv_id_search = self.pool.get('account.invoice').search(cr, uid,[('purchase_id','=',purchase.id),('state','!=','cancel')])
##                    account_inv_id_browse = self.pool.get('account.invoice').browse(cr, uid,account_inv_id_search)
##                    
##                    for inv_id in account_inv_id_browse:
##                        inv_id.id
##                    
##                    
##                    account_voc_id_search = self.pool.get('account.voucher').write(cr, uid,[a.id],{'invoice_id':inv_id.id})
##            
##            print "IDS ::", purchase.id
##            
##            ################
#           
#        return {
#            'name': 'Downpayment Notification',
#            'view_type': 'form',
#            'view_mode': 'form',
#            'res_model': 'downpayment.notification',
#            'type': 'ir.actions.act_window',
#            'target': 'new',
#            'context': context
#        }


purchase_advance_payment_inv()