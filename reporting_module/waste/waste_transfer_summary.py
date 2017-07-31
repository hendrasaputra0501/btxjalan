from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from tools.translate import _
import cStringIO
import netsvc
import tools
import decimal_precision as dp
import logging
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP


class waste_transfer_summary_parser(report_sxw.rml_parse):
	def __init__(self,cr,uid,name,context=None):
		super(waste_transfer_summary_parser,self).__init__(cr,uid,name,context=context)
		self.localcontext.update({
			'time' : time,
			'get_result' : self._get_result,
			'get_location' : self._get_location,
			})

	def _get_location(self,data):
		cr = self.cr
		uid = self.uid
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXX", "ADA" if data['location_exception'] else "TIDAK ADA"
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('scrap_location','=',False)])
				# ('usage',"not in",['view','customer','supplier','inventory','procurement','production'])])
			#print "-----------sssssssssssssssssss----------",location_ids
		else:
			location_ids = data['location_force']
		if location_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(location_ids)))
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="sequence asc, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []


	def _get_result(self,data):
		date_start =data['form']['date_start']
		date_stop  =data['form']['date_stop']
		output_type =data['form']['output_type']
		goods_type =data['form']['goods_type']
		goods_type = "('%s')" %goods_type
		location_ids = [loc.id for loc in self._get_location(data)]
		sloc = ''
		for location_id in location_ids:
			if sloc != '':
				sloc += ','
			sloc += str(location_id)
		query="select\
				pp.default_code,\
				left(pp.default_code,3) as fg_group,\
				pp.name_template, \
				sl.name as source_location,\
				sum(sm.product_qty) as product_qty, \
				sum(sm.product_uop_qty) as product_uop_qty,\
				pu.name as uom\
				from stock_move sm inner join stock_picking sp \
				on sm.picking_id=sp.id \
				left join product_product pp on sm.product_id=pp.id \
				left join stock_location sl on sm.location_id=sl.id \
				left join stock_location slo on sm.location_dest_id=slo.id \
				left join product_uom pu on sm.product_uom=pu.id\
				where sp.state='done' \
				and sp.type in('internal') and sp.internal_shipment_type in ('fg_receipt','fgo_receipt')\
				and to_char(sm.date,'YYYY-MM-DD') >= substring('%s',1,10)\
				and to_char(sm.date,'YYYY-MM-DD') <= substring('%s',1,10)\
				and  sp.goods_type in %s \
				and sm.location_id in (%s)\
				group by pp.default_code,left(pp.default_code,3),pp.name_template,sl.name,pu.name \
				"
		query=query%(date_start,date_stop,goods_type,sloc)
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		print goods_type,"hahahaha"
		# print res,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		return res

report_sxw.report_sxw('report.waste.transfer.sum.report','waste.transfer.summary.wizard','addons/reporting_module/waste/waste_transfer_summary.mako',parser=waste_transfer_summary_parser)
