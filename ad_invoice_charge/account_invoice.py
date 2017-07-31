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

import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice(osv.osv):
    """ inherited account.invoice """
    _inherit = 'account.invoice'
    
    _columns = {
        'charge_type': fields.selection([
            ('sale','Sale'),
            ('purchase','Purchase'),
            ('bank_charge','Bank Charges'),
            ('other','Others'),
            ],'Charge Type', readonly=False, select=True, change_default=True, track_visibility='always'),
    }

class account_invoice_line(osv.osv):
    """ inherited account.invoice.line """
    _inherit = 'account.invoice.line'
    
    _columns = {
        'invoice_related_id' : fields.many2one('account.invoice','Related Invoice'),
        'picking_related_id' : fields.many2one('stock.picking','Related Picking'),
        # 'shipping_id' : fields.many2one('container.booking','Shippment'),
        'type_of_charge': fields.many2one('charge.type', 'Charge For'),
        'report_charge_type' : fields.selection([('freight','Freight'),('fob','FOB Cost'),('emkl','EMKL'),('emkl','Other EMKL'),('ocost','Other Cost')],"Freight Cost Type"),
        # 'state' : fields.related('invoice_id','state'),
    }

    _defaults = {
        'report_charge_type':lambda *a:'freight',
    }

    def onchange_charge(self, cr, uid, ids, type_of_charge):
        result={}
        charge = self.pool.get('charge.type').browse(cr,uid,type_of_charge)
        if charge.account_id:
            result= {'value':{'account_id':charge.account_id and charge.account_id.id or False}}
            return result
        else:
            return result

class charge_type(osv.osv):
    _name = "charge.type"
    _description = 'Type of Charge'
    _order = "id, name"
    _columns = {
        'code' : fields.char('Code', size=10, select=True),
        'name': fields.char('Type of Charge', size=64, select=True),
        'account_id' : fields.many2one('account.account','Account',domain="[('type','not in',['view','closed'])]"),
        'type' : fields.selection([('delivery','Delivery Charges'),('invoicing','Invoicing/Payment Charges'),('other','Other Charges')], "Type"),
        'trans_type' : fields.selection([('sale','Sales Charges'),('purchase','Purchase Charges')], "Transaction Type"),
        'sale_type' : fields.selection([('local','Local'),('export','Export')], "Sale Type"),
        'purchase_type' : fields.selection([('local','Local'),('import','Import')], "Purchase Type"),
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Type of Charge must be unique!'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name','code'], context)
        res = []
        for record in reads:
            code = record['code']
            if code:
                name = '[' + code + '] ' + record['name']
            else:
                name = record['name']
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        ids = []
        if name:
            ids = self.search(cr, uid, ['|',('name', '=', name),('code', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, ['|',('name', operator, name),('code', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: