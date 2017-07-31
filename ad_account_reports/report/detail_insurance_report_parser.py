import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
 
class detail_insurance_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(detail_insurance_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_domain(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		domain = []
		domain.append(('date','>=',from_date))
		domain.append(('date','<=',to_date))
		
		return domain

	def _get_query(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		query = ""
		query += " AND to_char(coalesce(coalesce(c.estimation_date,b.estimation_deliv_date),a.entry_date),'YYYY-MM-DD') between '"+from_date+"' and '"+to_date+"'"
		return query

	def _get_result(self, data):
		query = "SELECT DISTINCT\
					a.name as no_policy,\
					to_char(coalesce(coalesce(c.estimation_date,b.estimation_deliv_date),a.entry_date),'YYYY-MM-DD') as etd_date,\
					a.voyage_from as voyage_from,\
					coalesce(d.internal_number, '') as inv_number,\
					a.voyage_to as voyage_to,\
					e.name as cury,\
					a.insured_amount as insured_amt,\
					a.premi_rate as rate,\
					a.deductible_amount as premi_amt,\
					coalesce(d.type,'') as inv_type, coalesce(ioc.other_cost,0.0) as other_cost\
				FROM \
					insurance_polis a\
					LEFT JOIN stock_picking b ON b.invoice_id=a.invoice_id\
					LEFT JOIN container_booking c ON c.id=b.container_book_id\
					LEFT JOIN account_invoice d ON d.id=a.invoice_id and d.id=b.invoice_id\
					LEFT JOIN res_currency e ON e.id=a.currency_id\
					LEFT JOIN (SELECT polis_id,sum(amount) as other_cost FROM insurance_other_cost GROUP BY polis_id) ioc ON ioc.polis_id=a.id\
				WHERE\
					to_char(coalesce(coalesce(c.estimation_date,b.estimation_deliv_date),a.entry_date),'YYYY-MM-DD') is not NULL "
		query += self._get_query(data)
		query += "ORDER BY etd_date,inv_number"
		self.cr.execute(query)
		return self.cr.dictfetchall()

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _display_filter(self, parser, data):
		filter_string = '%s - %s' % (parser.formatLang(data['form']['from_date'], date=True),
										  parser.formatLang(data['form']['to_date'], date=True))
		return ' %s' % (filter_string)

class detail_insurance_report_xls(report_xls):
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
		ws = wb.add_sheet('Aging Report',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_4			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.0000;-#,##0.0000')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap off, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		ws.write_merge(0,0,0,12, "PT. Bitratex Industries", title_style)
		ws.write_merge(1,1,0,12, "Detail Insurance for "+parser._display_filter(parser,data), title_style)

		ws.write_merge(2,3,0,0, "NO POLICY", th_bottom_style)
		ws.write_merge(2,3,1,1, "DATE", th_bottom_style)
		ws.write_merge(2,3,2,2, "FROM", th_bottom_style)
		ws.write_merge(2,3,3,3, "INVOICE", th_bottom_style)
		ws.write_merge(2,3,4,4, "PARTY", th_bottom_style)
		ws.write_merge(2,2,5,7, "AMOUNT INSURED", th_bottom_style)
		ws.write(3,5, "CURY", th_bottom_style)
		ws.write(3,6, "AMOUNT", th_bottom_style)
		ws.write(3,7, "FOR", th_bottom_style)
		ws.write_merge(2,2,8,10, "AMOUNT PREMI", th_bottom_style)
		ws.write(3,8, "RATE", th_bottom_style)
		ws.write(3,9, "CURY", th_bottom_style)
		ws.write(3,10, "AMOUNT", th_bottom_style)
		ws.write_merge(2,2,11,12, "OTHER COST", th_bottom_style)
		ws.write(3,11, "CURY", th_bottom_style)
		ws.write(3,12, "AMOUNT", th_bottom_style)
		
		max_width_col = {0:16,1:10,2:10,3:12,4:10,5:5,6:14,7:11,8:6,9:5,10:8,11:5,12:6}
		rowcount=4
		
		total_amount,total_oth_cost = 0.0, 0.0
		results = parser._get_result(data)
		for line in results:
			ws.write(rowcount,0,line['no_policy'],normal_style)
			if len(line['no_policy'] and str(line['no_policy']) or '')>max_width_col[0]:
				max_width_col[0] = len(str(line['no_policy']))
			ws.write(rowcount,1,line['etd_date'] and dt.strptime(line['etd_date'], '%Y-%m-%d').strftime('%d/%m/%Y') or '',normal_style)
			ws.write(rowcount,2,line['voyage_from'],normal_style)
			if len(line['voyage_from'] and str(line['voyage_from']) or '')>max_width_col[2]:
				max_width_col[2] = len(str(line['voyage_from']))
			ws.write(rowcount,3,line['inv_number'],normal_style)
			ws.write(rowcount,4,line['voyage_to'],normal_style)
			if len(line['voyage_to'] and str(line['voyage_to']) or '')>max_width_col[4]:
				max_width_col[4] = len(str(line['voyage_to']))
			ws.write(rowcount,5,line['cury'],normal_style)
			ws.write(rowcount,6,line['insured_amt'],normal_style_float)
			if len(line['insured_amt'] and str(line['insured_amt']) or '')>max_width_col[6]:
				max_width_col[6] = len(str(line['insured_amt']))
			ws.write(rowcount,7,"EXPORT/SEA",normal_style)
			ws.write(rowcount,8,line['rate'],normal_style_float_4)
			ws.write(rowcount,9,line['cury'],normal_style_float)
			ws.write(rowcount,10,line['premi_amt'],normal_style_float)
			ws.write(rowcount,11, "IDR" ,normal_style_float)
			ws.write(rowcount,12,line['other_cost'],normal_style_float)
			rowcount+=1
			total_amount+=line['premi_amt']
			total_oth_cost += line['other_cost']
		ws.write_merge(rowcount,rowcount,0,9," ",subtotal_title_style)
		ws.write(rowcount,10,total_amount,subtotal_style2)
		if len(total_amount and str(total_amount) or '')>max_width_col[10]:
			max_width_col[10] = len(str(total_amount))
		ws.write(rowcount,11," ",subtotal_title_style)
		ws.write(rowcount,12,total_oth_cost,subtotal_style2)
		if len(total_oth_cost and str(total_oth_cost) or '')>max_width_col[12]:
			max_width_col[12] = len(str(total_oth_cost))

		for k in max_width_col.keys():
			ws.col(k).width = 256*int(max_width_col[k]*1.4)		
		
		pass
detail_insurance_report_xls('report.detail.insurance.report','detail.insurance.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=detail_insurance_report_parser, header=False)