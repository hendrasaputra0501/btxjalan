# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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

import logging
import time

import openerp
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from datetime import datetime

_logger = logging.getLogger(__name__)

class ir_sequence(osv.Model):
	_inherit = "ir.sequence"

	def _interpolation_dict(self, context=None):
		if context is None:
			context = {}
		if context.get('date',False):
			date = datetime.strptime(context['date'],DEFAULT_SERVER_DATETIME_FORMAT)
			res = {
				'year': date.strftime('%Y'),
				'month': date.strftime('%m'),
				'day': date.strftime('%d'),
				'y': date.strftime('%y'),
				'doy': date.strftime('%j'),
				'woy': date.strftime('%W'),
				'weekday': date.strftime('%w'),
				'h24': date.strftime('%H'),
				'h12': date.strftime('%I'),
				'min': date.strftime('%M'),
				'sec': date.strftime('%S'),
			}
		else:
			t = time.localtime() # Actually, the server is always in UTC.
			res = {
				'year': time.strftime('%Y', t),
				'month': time.strftime('%m', t),
				'day': time.strftime('%d', t),
				'y': time.strftime('%y', t),
				'doy': time.strftime('%j', t),
				'woy': time.strftime('%W', t),
				'weekday': time.strftime('%w', t),
				'h24': time.strftime('%H', t),
				'h12': time.strftime('%I', t),
				'min': time.strftime('%M', t),
				'sec': time.strftime('%S', t),
			}
		return res
	
	def _next(self, cr, uid, seq_ids, context=None):
		if not seq_ids:
			return False
		if context is None:
			context = {}
		force_company = context.get('force_company')
		if not force_company:
			force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
		sequences = self.read(cr, uid, seq_ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
		preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
		seq = preferred_sequences[0] if preferred_sequences else sequences[0]
		if seq['implementation'] == 'standard':
			cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
			seq['number_next'] = cr.fetchone()
		else:
			cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
			cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
		d = self._interpolation_dict(context=context)
		try:
			interpolated_prefix = self._interpolate(seq['prefix'], d)
			interpolated_suffix = self._interpolate(seq['suffix'], d)
		except ValueError:
			raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
		return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix