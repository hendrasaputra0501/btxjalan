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

from openerp.osv import fields, osv
from openerp.osv.osv import object_proxy
from openerp.tools.translate import _
from openerp import pooler
import time
from openerp import tools
from openerp import SUPERUSER_ID
from ..audittrail import audittrail

class audittrail_custom_objects_proxy(audittrail.audittrail_objects_proxy):
	def prepare_audittrail_log_line(self, cr, uid, pool, model, resource_id, method, old_values, new_values, field_list=None):
		if field_list is None:
			field_list = []
		key = (model.id, resource_id)
		lines = {
			key: []
		}
		# loop on all the fields
		for field_name, field_definition in pool.get(model.model)._all_columns.items():
			if field_name in ('__last_update', 'id'):
				continue
			#if the field_list param is given, skip all the fields not in that list
			if field_list and field_name not in field_list:
				continue
			field_obj = field_definition.column
			if field_obj._type in ('one2many','many2many'):
				# checking if an audittrail rule apply in super admin mode
				if self.check_rules(cr, SUPERUSER_ID, field_obj._obj, method):
					# checking if the model associated to a *2m field exists, in super admin mode
					x2m_model_ids = pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', field_obj._obj)])
					x2m_model_id = x2m_model_ids and x2m_model_ids[0] or False
					assert x2m_model_id, _("'%s' Model does not exist..." %(field_obj._obj))
					x2m_model = pool.get('ir.model').browse(cr, SUPERUSER_ID, x2m_model_id)
					# the resource_ids that need to be checked are the sum of both old and previous values (because we
					# need to log also creation or deletion in those lists).
					x2m_old_values_ids = old_values.get(key, {'value': {}})['value'].get(field_name, [])
					x2m_new_values_ids = new_values.get(key, {'value': {}})['value'].get(field_name, [])
					# We use list(set(...)) to remove duplicates.
					res_ids = list(set(x2m_old_values_ids + x2m_new_values_ids))
					if model.model == x2m_model.model:
						# we need to remove current resource_id from the many2many to prevent an infinit loop
						if resource_id in res_ids:
							res_ids.remove(resource_id)
					for res_id in res_ids:
						lines.update(self.prepare_audittrail_log_line(cr, SUPERUSER_ID, pool, x2m_model, res_id, method, old_values, new_values, field_list))
			# if the value value is different than the old value: record the change
			if key not in old_values or key not in new_values or old_values[key]['value'].get(field_name) != new_values[key]['value'].get(field_name):
				data = {
					  'name': field_name,
					  'new_value': key in new_values and new_values[key]['value'].get(field_name),
					  'old_value': key in old_values and old_values[key]['value'].get(field_name),
					  'new_value_text': key in new_values and new_values[key]['text'].get(field_name),
					  'old_value_text': key in old_values and old_values[key]['text'].get(field_name)
				}
				lines[key].append(data)
			# On read log add current values for fields.
			if method == 'read':
				data={
					'name': field_name,
					'old_value': key in old_values and old_values[key]['value'].get(field_name),
					'old_value_text': key in old_values and old_values[key]['text'].get(field_name)
				}
				lines[key].append(data)
		return lines
audittrail_custom_objects_proxy()