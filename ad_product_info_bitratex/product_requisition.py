# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class product_requisition(osv.Model):
	_name = "product.requisition"
	_columns = {
		"name" : fields.char('Number', size=128, required=True),
		"requisition_lines" : fields.one2many('product.requisition.line','requisition_id'),
		
		"partner_id" : fields.many2one('res.partner','Supplier'),
		"date_entry" : fields.date('Date Entry', required=True),
		"source_dept_id" : fields.many2one('hr.department','Source Department', required=True),
		"dest_dept_id" : fields.many2one('hr.department','Destination Department', required=True),
		"request_by" : fields.many2one('res.users', 'Requested By', required=True),
		"state" : fields.selection(
			[('draft', 'Draft'),
			('submitted', 'Submitted'),
			('approved', 'Approved'),],
			'Status', readonly=True, select=True),
	}
	_defaults = {
		"state" : lambda *a:'draft',
		"name" : lambda self, cr, uid, context: self.pool.get('ir.sequence').get(cr, uid, 'product_requisition'),
	}

	def action_submit(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'submitted'})

	def action_approve(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'approved'})

class product_requisition_line(osv.Model):
	_name = "product.requisition.line"
	_columns = {
		"requisition_id" : fields.many2one('product.requisition','Reference'),
		"name" : fields.char('Product Name', size=128, required=True),
		"catalogue" : fields.char("Catalogue Number",size=20,required=False),
		"part_number" : fields.char("Part Number",size=20,required=False),
		"product_uom" : fields.many2one('product.uom','Unit of Measure', required=True),
		"suggested_code" : fields.char('Suggested Code', size=128, required=False),
		"product_id" : fields.many2one('product.product','Product'),
		"default_code" : fields.related('product_id','default_code', string="Real Code", type="char"),
		"state" : fields.related('requisition_id','state',
			type='selection',selection=[('draft', 'Draft'),
			('submitted', 'Submitted'),
			('approved', 'Approved'),],
			string='Status', readonly=True, select=True),
	}