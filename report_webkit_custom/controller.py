# -*- coding: utf-8 -*-
import openerp.addons.web.http as openerpweb
from openerp.addons.web.controllers.main import Reports as Reports3
from openerp.addons.web.controllers.main import content_disposition
import ast
import base64
import csv
import glob
import itertools
import logging
import operator
import datetime
import hashlib
import os
import re
import simplejson
import time
import urllib
import urllib2
import urlparse
import xmlrpclib
import zlib
from xml.etree import ElementTree
from cStringIO import StringIO
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import babel.messages.pofile
import werkzeug.utils
import werkzeug.wrappers
try:
	import xlwt
except ImportError:
	xlwt = None

class Reports2(Reports3):
	@openerpweb.httprequest
	def index(self, req, action, token):
		action = simplejson.loads(action)

		report_srv = req.session.proxy("report")
		context = dict(req.context)
		context.update(action["context"])
		report_data = {}
		report_ids = context["active_ids"]
		if 'report_type' in action:
			report_data['report_type'] = action['report_type']
		if 'datas' in action:
			if 'ids' in action['datas']:
				report_ids = action['datas'].pop('ids')
			report_data.update(action['datas'])

		report_id = report_srv.report(
			req.session._db, req.session._uid, req.session._password,
			action["report_name"], report_ids,
			report_data, context)

		report_struct = None
		while True:
			report_struct = report_srv.report_get(
				req.session._db, req.session._uid, req.session._password, report_id)
			if report_struct["state"]:
				break

			time.sleep(self.POLLING_DELAY)

		report = base64.b64decode(report_struct['result'])
		if report_struct.get('code') == 'zlib':
			report = zlib.decompress(report)
		report_mimetype = self.TYPES_MAPPING.get(
			report_struct['format'], 'octet-stream')
		file_name = action.get('name', 'report')
		if 'name' not in action:
			reports = req.session.model('ir.actions.report.xml')
			res_id = reports.search([('report_name', '=', action['report_name']),],
									0, False, False, context)
			if len(res_id) > 0:
				file_name = reports.read(res_id[0], ['name'], context)['name']
			else:
				file_name = action['report_name']

		if action.get("override_name",False) not in (False,""):
			pooler_obj = req.session.model(context.get('active_model',False))
			field_to_fetch = action.get('override_name',False)
			found = re.findall('\[\'(.*?)\'\]',str(field_to_fetch))
			
			objects = pooler_obj.read(context.get('active_ids',False), found, context)

			overrides = action.get('override_name',False).split("+")
			to_eval = ""
			for override in overrides:
				if override.strip().startswith("("):
					to_eval+=override.strip()+" "
			file_name_temp = ""
			try:
				for obj in objects:
					file_name_temp+=str(eval(to_eval))+" "
			except:
				#raise Exception(_('Please check filename format in ir.actions.report override_name ! Or jus leave it blank.'))
				pass
			file_name = ""
			ch = False 
			for override in overrides:
				if not override.strip().startswith("("):
					file_name+=override.strip()+" "
				elif override.strip().startswith("(") and not ch:
					file_name+=file_name_temp
			file_name=file_name.strip()
		file_name = '%s.%s' % (file_name, report_struct['format'])
		return req.make_response(report,
			 headers=[
				 ('Content-Disposition', content_disposition(file_name, req)),
				 ('Content-Type', report_mimetype),
				 ('Content-Length', len(report))],
			 cookies={'fileToken': token})
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
