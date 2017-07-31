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

from tools import DEFAULT_SERVER_DATETIME_FORMAT
import addons.decimal_precision as dp

from openerp.osv import fields, osv
from openerp import netsvc

class mass_mo(osv.osv_memory):
    _name = "mo.batch"
    _description = "Manufacturing Orders"
    _columns = {
        'date_create': fields.datetime('Create Date', help='', required=True),
        'user_id': fields.many2one('res.users', 'Responsible', required=True),
        'mo_batch_line': fields.one2many('mo.batch.line', 'mo_batch_id', 'Products'),
    }
    _defaults = {
        'date_create': lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        'user_id': lambda self, cr, uid, c: uid,
    }

    def create_batch_mo(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order batch
        @return: New created Production Orders batch
        """
        wf_service = netsvc.LocalService("workflow")
        production_obj = self.pool.get('mrp.production')
        mo_batch_line_obj = self.pool.get('mo.batch.line')
        mo_batch = self.browse(cr, uid, ids, context=context)[0]
        for mo_line in mo_batch.mo_batch_line:
            vals = mo_batch_line_obj._prepare_mo_batch_line(cr, uid, mo_line, context)
            produce_id = production_obj.create(cr, uid, vals, context=context)
            bom_result = production_obj.action_compute(cr, uid,
                    [produce_id])
            wf_service.trg_validate(uid, 'mrp.production', produce_id, 'button_confirm', cr)
        return True

class mass_mo_line(osv.osv_memory):
    _name = "mo.batch.line"
    _description = "Manufacturing Orders Line"
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('internal_type','=','Finish'),('bom_ids','!=',False),('bom_ids.bom_id','=',False)]),
        'product_qty': fields.float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'product_uos_qty': fields.float('Product UoS Quantity'),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'bom_id': fields.many2one('mrp.bom', 'Blend (BoM)', required=True, domain=[('bom_id','=',False)], help="Bill of Materials allow you to define the list of required raw materials to make a finished product."),
        'date_planned': fields.datetime('Scheduled Date', required=True, select=1),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'mo_batch_id': fields.many2one('mo.batch', 'MO'),
    }
    _defaults = {
        'date_planned': lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        'product_qty':  lambda *a: 1.0,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.production', context=c),
    }
    
    def product_id_change(self, cr, uid, ids, product_id, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        if not product_id:
            return {'value': {
                'product_uom': False,
                'bom_id': False,
            }}
        bom_obj = self.pool.get('mrp.bom')
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        product_uom_id = product.uom_id and product.uom_id.id or False
        bom_id = bom_obj._bom_find(cr, uid, product.id, product_uom_id, [])
        result = {
            'product_uom': product_uom_id,
            'bom_id': bom_id,
        }
        return {'value': result}

    def _prepare_mo_batch_line(self, cr, uid, line, context=None):
        vals = {
            'origin': 'Create from batch',
            'product_id': line.product_id.id,
            'product_qty': line.product_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': line.product_uos and line.product_uos_qty or False,
            'product_uos': line.product_uos and line.product_uos.id or False,
            'bom_id': line.bom_id and line.bom_id.id or False,
            'date_planned': line.date_planned,
            'user_id': line.mo_batch_id.user_id.id,
            'company_id': line.company_id.id,
        }
        return vals
