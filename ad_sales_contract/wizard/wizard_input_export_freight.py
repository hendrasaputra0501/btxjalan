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

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler
import time

class wizard_input_export_freight(osv.osv_memory):
	_name = "wizard.input.export.freight"
	_description = "Input Estimated Export Freight Rate"

	_columns = {
		# 'sale_ids' : fields.many2many('sale.order', 'sale_order_rel_wizard_input_freight', 'sale_id', 'wizard_id', 'Sales Orders', domain=[('sale_type','=','export'),('state','not in',['cancel','draft','sent'])]),
		'from_date' : fields.date('From Date', required=True),
		'to_date' : fields.date('To Date', required=True),
		'line_ids' : fields.one2many('wizard.input.export.freight.line', 'wizard_id', 'Sales Orders'),
	}

	_defaults = {
	}

	def onchange_fields(self, cr, uid, ids, from_date, to_date, context=None):
		sale_obj = self.pool.get('sale.order')
		
		res = []
		if not from_date or not to_date:
			return {'value':{'line_ids':[]}}
			
		sale_ids = sale_obj.search(cr, uid, [('freight_rate_value','<=',0),('date_order','>=',from_date),('date_order','<=',to_date),('state','not in',['cancel','draft','sent']),('sale_type','=','export')])
		if not sale_ids:
			return {'value':{'line_ids':[]}}

		for sale in sale_obj.browse(cr, uid, sale_ids):
			res.append({
				'sale_id' : sale.id,
				'freight_rate_value' : sale.freight_rate_value,
				})
		return {'value':{'line_ids':res}}

	def input_freight_rate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		wf_service = netsvc.LocalService("workflow")
		pool_obj = self.pool.get('sale.order')
		data = self.browse(cr, uid, ids[0], context=context)
		for line in data.line_ids:
			pool_obj.write(cr, uid, line.sale_id.id, {'freight_rate_value': line.freight_rate_value}, context=context)
		
		return {'type': 'ir.actions.act_window_close'}

wizard_input_export_freight()

class wizard_input_export_freight_line(osv.osv_memory):
	_name = "wizard.input.export.freight.line"
	_columns = {
		'wizard_id' : fields.many2one('wizard.input.export.freight','Wizard Reference'),
		'sale_id' : fields.many2one('sale.order','Sale Order', required=True),
		'freight_rate_value'	: fields.float("Freight Rate", required=False),
	}
wizard_input_export_freight_line()

class wizard_input_efisiensi_rate(osv.osv_memory):
	_name = "wizard.input.efisiensi.rate"
	_description = "Input Estimated Export Freight Rate"

	_columns = {
		# 'sale_ids' : fields.many2many('sale.order', 'sale_order_rel_wizard_input_efisiensi', 'sale_id', 'wizard_id', 'Sales Orders', domain=[('state','not in',['cancel','draft','sent'])]),
		'from_date' : fields.date('From Date', required=True),
		'to_date' : fields.date('To Date', required=True),
		'sale_type' : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		'goods_type' : fields.selection([
						('finish','Finish Goods'),
						('finish_others','Finish Goods(Others)'),
						('raw','Raw Material'),
						('service','Services'),
						('stores','Stores'),
						('waste','Waste'),
						('scrap','Scrap'),
						('packing','Packing Material'),
						('asset','Fixed Asset')],'Goods Type',required=True),
		'line_ids' : fields.one2many('wizard.input.efisiensi.rate.line', 'wizard_id', 'Sales Orders'),
	}

	_defaults = {
		'sale_type' : lambda *s: 'export',
		'goods_type' : lambda *g: 'finish',
	}

	def onchange_fields(self, cr, uid, ids, from_date, to_date, sale_type, goods_type, context=None):
		sale_obj = self.pool.get('sale.order')
		sale_line_obj = self.pool.get('sale.order.line')
		
		res = []
		if not from_date or not to_date or not sale_type or not goods_type:
			return {'value':{'line_ids':[]}}
		
		sale_ids = sale_obj.search(cr, uid, [('date_order','>=',from_date),('date_order','<=',to_date),('state','not in',['cancel','draft','sent']),('sale_type','=',sale_type),('goods_type','=',goods_type)])	
		if not sale_ids:
			return {'value':{'line_ids':[]}}
		
		sale_line_ids = sale_line_obj.search(cr, uid, [('efisiensi_rate','<=',0),('order_id','in',sale_ids or [])])
		if not sale_line_ids:
			return {'value':{'line_ids':[]}}

		for line in sale_line_obj.browse(cr, uid, sale_line_ids):
			res.append({
				'sale_line_id' : line.id,
				'efisiensi_rate' : line.efisiensi_rate,
				})
		return {'value':{'line_ids':res}}

	def input_efisiensi_rate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		wf_service = netsvc.LocalService("workflow")
		pool_obj = self.pool.get('sale.order.line')
		data = self.browse(cr, uid, ids[0], context=context)
		for line in data.line_ids:
			pool_obj.write(cr, uid, line.sale_line_id.id, {'efisiensi_rate': line.efisiensi_rate}, context=context)
		
		return {'type': 'ir.actions.act_window_close'}

wizard_input_efisiensi_rate()

class wizard_input_efisiensi_rate_line(osv.osv_memory):
	_name = "wizard.input.efisiensi.rate.line"
	_columns = {
		'wizard_id' : fields.many2one('wizard.input.efisiensi.rate','Wizard Reference'),
		'sale_line_id' : fields.many2one('sale.order.line','Order Number', required=True),
		'efisiensi_rate'	: fields.float("Efisiensi Rate", required=False),
	}
wizard_input_efisiensi_rate_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
