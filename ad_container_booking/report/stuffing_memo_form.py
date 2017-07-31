import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from datetime import datetime
from dateutil import tz
import pytz
from openerp import SUPERUSER_ID

class stuffing_memo_parser(report_sxw.rml_parse):

	curr_unit_var = ''

	def __init__(self, cr, uid, name, context):
		super(stuffing_memo_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time':time,
			'xdate':self._xdate,
			'xdatepday':self._xdatepday,
			'get_unit_group':self._get_unit_group,
			'get_uom_base':self._get_uom_base,
			'uom_to_base':self._uom_to_base,
			'get_sale_type':self._get_sale_type,
			'xdatepmonth':self._xdatepmonth,
			'get_print_user_time':self._get_print_user_time,
			'set_curr_unit':self._set_curr_unit,
			'get_curr_unit':self._get_curr_unit,
			'xdate3month':self._xdate3month
		})

	def _set_curr_unit(self,curr_unit):
		stuffing_memo_parser.curr_unit_var = curr_unit
		return 0

	def _get_curr_unit(self):
		curr_unit = stuffing_memo_parser.curr_unit_var
		return curr_unit

	def _get_print_user_time(self,context=None):	
		cr = self.cr
		uid = self.uid
		curr_user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
		tlocal = time.localtime()
		slocal = str(tlocal.tm_year) + '-' + str(tlocal.tm_mon) + '-' + str(tlocal.tm_mday) + ' ' + str(tlocal.tm_hour) + ':' + str(tlocal.tm_min) 
		print_user_time = 'Printed By ' + curr_user.partner_id.name + ' On ' + datetime.strptime(slocal,'%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M')
		return print_user_time

	def _xdate(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
		except:
			y = x1
		return y

	def _xdatepday(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%A, %d/%m/%Y')
		except:
			y = x
		return y

	def _xdatepmonth(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%B %d, %Y')
		except:
			y = x
		return y

	def _xdate3month(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%b/%Y')
		except:
			y = x
		return y

	def _get_unit_group(self,stuff_memo_obj):
		res=[]
		stuff_memo_group={}
		key=stuff_memo_obj.manufacturer.name or ''
		stuff_memo_group[key]=['']
		stuff_memo_group[key][0]=key

		for line in stuff_memo_obj.goods_lines:
			key=line.manufacturer.name or ''
			if (key != ''):
				if (key not in stuff_memo_group):
					stuff_memo_group[key]=['']
					stuff_memo_group[key][0]=key

		for x in stuff_memo_group.keys():
			res.append(stuff_memo_group[x])
		return res

	def _get_sale_type(self,stuff_memo_obj):
		res = ''
		for line in stuff_memo_obj.goods_lines:
			res = line.sale_id and line.sale_id.sale_type or ''
			if (res != ''):
				break
		return res

	def _get_uom_base(self,sale_type):
		if sale_type == 'export':
			uom_base = 'KGS'
		elif sale_type == 'local':
			uom_base = 'KGS'
		else:
			uom_base = 'KGS'
		return uom_base

	def _uom_to_base(self,sale_type,qty,uom_source):
		cr = self.cr
		uid = self.uid
		if sale_type == 'export':
			uom_base = 'KGS'
		elif sale_type == 'local':
			uom_base = 'KGS'
		else:
			uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		if uom_source and base:
			qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source and uom_source.id or False, qty, to_uom_id=base[0])
		else:
			qty_result = qty
		return qty_result

report_sxw.report_sxw('report.stuffing.memo.form', 'stuffing.memo', 'ad_container_booking/report/stuffing_memo_form.mako', parser=stuffing_memo_parser,header=False) 