from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging
import json, ast
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
import calendar

class sum_expshipment_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(sum_expshipment_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_title' : self._get_title,
			'get_view' : self._get_view,
			'xdate' : self._xdate,
			#'get_result_ageing' : self._get_result_ageing,
		})

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

	def _get_title(self,data,sheet):
		if data['form']['sale_type'] == 'export':
			stitle = 'EXPORT '
		elif data['form']['sale_type'] == 'local':
			stitle = 'LOCAL '
		else:
			stitle = ''
		stitle = stitle + 'SHIPMENT STATEMENT - '
	        # if sheet == 'customer':
	        #     stitle = stitle + 'CUSTOMER WISE'
	        # elif sheet == 'product':
	        #     stitle = stitle + 'PRODUCT WISE'
	        # elif sheet == 'date':
	        #     stitle = stitle + 'DATE WISE'
		return stitle


	def _get_view(self,data,context=None):
		# data['sale_type'],data['as_on']
		as_on_date = datetime.strptime(data["as_on"],"%Y-%m-%d"	)
		daily = as_on_date.strftime('%Y-%m-%d')
		last_date_month=calendar.monthrange(int(as_on_date.strftime('%Y')),int(as_on_date.strftime('%m')))
		start_mth = '%s-%s-%s'%(as_on_date.strftime('%Y'),as_on_date.strftime('%m'),'01')
		end_mth = '%s-%s-%s'%(as_on_date.strftime('%Y'),as_on_date.strftime('%m'),last_date_month[1])
		start_year = '%s-%s-%s'%(as_on_date.strftime('%Y'),'01','01')
		end_year = '%s-%s-%s'%(as_on_date.strftime('%Y'),'12','31')
		stype = data['sale_type']
		# daily date,start_mth date,end_mth date,start_year date,end_year date,stype text
		query="select * from shipment_summary('"+daily+"'::date,'"+start_mth+"'::date,'"+daily+"'::date,'"+start_year+"'::date,'"+daily+"'::date,'"+stype+"'::text)"
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

class sum_expshipment_parser_xls(report_xls):
	no_ind = 0
	def get_no_index(self):
		self.set_no_index()
		return self.no_ind
	def set_no_index(self):
		self.no_ind += 1
		return True
	def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
		if not context:
			context = {}
		context = context.copy()
		rml_parser = self.parser(cr, uid, self.name2, context=context)
		objs = []
		rml_parser.set_context(objs, data, ids, 'xls')
		n = cStringIO.StringIO()
		wb = xlwt.Workbook(encoding='utf-8')
		self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
		wb.save(n)
		n.seek(0)
		return (n.read(), 'xls')
		  
	def generate_xls_report(self, parser, data, obj, wb):
		wr=wb.add_sheet(('Summary Export Shipment Report'))
		delivery_moves = parser._get_view(data)

		
		hdr_style= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; borders: top thin, bottom thin;')
		hdr_style_right= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: top thin, bottom thin;')
		header_style1 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz center;' "borders: top thin, bottom thin")
		locgroup_style = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz left;')
		normal_style= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		style2 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz right;')
		subtotal_style1 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz center;' "borders: top dashed")
		subtotal_style2 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' "borders: top thin,bottom thin; pattern: pattern solid, fore_color gray25;")
		title_style = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center;')
		title_style1 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin;')
		title_style2 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: bottom thin;')
		title_style2_right = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz right; pattern: pattern solid, fore_color gray25; borders: bottom thin;')
		title_style3 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		# normal_bold_style_b = xlwt.easyxf('font: name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		
		wr.write_merge(0,0,0,10, "SUMMARY REPORT OF EXPORT SHIPMENT AS ON "+parser._xdate(data['as_on']), title_style)

		#wr.write_merge(2,2,6,8, "FROM:"+parser._xdate(data['date_from']), title_style)
		#wr.write_merge(2,2,9,11, "TO:"+parser._xdate(data['date_to']), title_style)
		wr.write(2,0, "",title_style3)
		wr.write_merge(2,2,1,3, "TODAY",title_style3)
		wr.write_merge(2,2,4,6, "CUMMULATIVE MONTH",title_style3)
		wr.write_merge(2,2,7,9, datetime.strptime(data['as_on'],"%Y-%m-%d").strftime("%Y"),title_style3)
		wr.write(3,0, "PRODUCT", title_style2)
		wr.write(3,1, "QTY BALE", title_style2)
		wr.write(3,2, "(1 X 40')", title_style2)
		wr.write(3,3, "US$", title_style2)
		wr.write(3,4, "QTY BALE", title_style2)
		wr.write(3,5, "(1 X 40')", title_style2)
		wr.write(3,6, "US$", title_style2)
		wr.write(3,7, "QTY BALE", title_style2)
		wr.write(3,8, "(1 X 40')", title_style2)
		wr.write(3,9, "US$", title_style2)
		
		
		

		# wr = wb.add_sheet(('Shipment Statement')) 
		wr.col(0).width = len("ABCDEFG")*500
		wr.col(1).width = (wr.col(0).width)
		wr.col(2).width = (wr.col(0).width)
		wr.col(3).width = (wr.col(0).width)
		wr.col(4).width = (wr.col(0).width)
		wr.col(5).width = (wr.col(0).width)
		wr.col(6).width = (wr.col(0).width)
		wr.col(7).width = (wr.col(0).width)
		wr.col(8).width = (wr.col(0).width)
		wr.col(9).width = (wr.col(0).width)


		res_grouped = {}
		current_location = False
		rowcount=5
		gt = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
		for res in delivery_moves:
			if current_location != res['loc_name']:
				if current_location:
					wr.write(rowcount,0, "SUBTOTAL ",subtotal_style2)
					wr.write(rowcount,1,xlwt.Formula("SUM($B$"+str(first_row)+":$B$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,2,xlwt.Formula("SUM($C$"+str(first_row)+":$C$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,3,xlwt.Formula("SUM($D$"+str(first_row)+":$D$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,4,xlwt.Formula("SUM($E$"+str(first_row)+":$E$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,5,xlwt.Formula("SUM($F$"+str(first_row)+":$F$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,6,xlwt.Formula("SUM($G$"+str(first_row)+":$G$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,7,xlwt.Formula("SUM($H$"+str(first_row)+":$H$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,8,xlwt.Formula("SUM($I$"+str(first_row)+":$I$"+str(rowcount)+")"),subtotal_style2)
					wr.write(rowcount,9,xlwt.Formula("SUM($J$"+str(first_row)+":$J$"+str(rowcount)+")"),subtotal_style2)
					rowcount+=2
					
				wr.write_merge(rowcount,rowcount,0,1,res['loc_name'],hdr_style_right)
				wr.write_merge(rowcount,rowcount,2,9, "",hdr_style_right)
				rowcount+=1
				first_row=rowcount
			
			current_location=res['loc_name']
			wr.write(rowcount,0, res['blend'],normal_style)
			wr.write(rowcount,1,res['qty_bale_daily'],normal_style_float)
			wr.write(rowcount,2,res['cont_daily'],normal_style_float)
			wr.write(rowcount,3,res['subtotal_daily'],normal_style_float)
			wr.write(rowcount,4,res['qty_bale_monthly'],normal_style_float)
			wr.write(rowcount,5,res['cont_monthly'],normal_style_float)
			wr.write(rowcount,6,res['subtotal_monthly'],normal_style_float)
			wr.write(rowcount,7,res['qty_bale_annual'],normal_style_float)
			wr.write(rowcount,8,res['cont_annual'],normal_style_float)
			wr.write(rowcount,9,res['subtotal_annual'],normal_style_float)
			rowcount+=1
			gt[0]+=res['qty_bale_daily'] or 0.0
			gt[1]+=res['cont_daily'] or 0.0
			gt[2]+=res['subtotal_daily'] or 0.0
			gt[3]+=res['qty_bale_monthly'] or 0.0
			gt[4]+=res['cont_monthly'] or 0.0
			gt[5]+=res['subtotal_monthly'] or 0.0
			gt[6]+=res['qty_bale_annual'] or 0.0
			gt[7]+=res['cont_annual'] or 0.0
			gt[8]+=res['subtotal_annual'] or 0.0
		
		wr.write(rowcount,0,"GRAND TOTAL",subtotal_style2)
		for x in range(0,9):
			wr.write(rowcount,x+1,gt[x],subtotal_style2)
		pass


report_sxw.report_sxw('report.sum.expshipment.pdf','sum.expshipment.wizard', 'addons/ad_stock_report/report/summary_export_shipment_report.mako',
						parser=sum_expshipment_parser)
sum_expshipment_parser_xls('report.sum.expshipment.xls','sum.expshipment.wizard', 'addons/ad_stock_report/report/summary_export_shipment_report.mako',
						parser=sum_expshipment_parser)
