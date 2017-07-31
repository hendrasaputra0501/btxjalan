import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
from negotiation_report_parser import negotiation_report_parser

class nego_report_xls(report_xls):
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
		ws = wb.add_sheet('Date Wise',cell_overwrite_ok=True)
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
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz center; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		
		ws.write_merge(0,0,0,13, "PT. Bitratex Industries", title_style)
		ws.write_merge(1,1,0,13, "EXPORT NEGOTIATION STATEMENT REPORT - DATE WISE", title_style)
		ws.write_merge(2,2,0,13, "Negotation date from " + parser.formatLang(data['form']['start_date'],date=True) + " to " + parser.formatLang(data['form']['end_date'],date=True), title_style)

		ws.write_merge(3,4,0,0, "No.", th_bottom_style)
		ws.write_merge(3,3,1,2, "Invoice", th_bottom_style)
		ws.write(4,1, "No.", th_bottom_style)
		ws.write(4,2, "Date", th_bottom_style)
		ws.write_merge(3,4,3,3, "LC\nBat.Nbr", th_bottom_style)
		ws.write_merge(3,4,4,4, "Customer", th_bottom_style)
		ws.write_merge(3,4,5,5, "Giro No.", th_bottom_style)
		ws.write_merge(3,4,6,6, "Payment\nBank", th_bottom_style)
		ws.write_merge(3,4,7,7, "Negotiation\nBank", th_bottom_style)
		ws.write_merge(3,4,8,8, "Cury\nId", th_bottom_style)
		ws.write_merge(3,3,9,10, "Dispatch", th_bottom_style)
		ws.write(4,9, "Transaction", th_bottom_style)
		ws.write(4,10, "USD", th_bottom_style)
		ws.write_merge(3,3,11,12, "Received", th_bottom_style)
		ws.write(4,11, "Transaction", th_bottom_style)
		ws.write(4,12, "USD", th_bottom_style)
		# ws.write_merge(3,3,13,15, "Charges", th_bottom_style)
		# ws.write(4,13, "Negotation", th_bottom_style)
		# ws.write(4,14, "Discount", th_bottom_style)
		# ws.write(4,15, "Others", th_bottom_style)
		ws.write_merge(3,4,13,13, "Net Negotation\n(USD)", th_bottom_style)
		
		rowcount=5
		max_width_col={0:3,1:10,2:8,3:9,4:8,5:8,6:11,7:11,8:6,9:12,10:10,11:12,12:10,13:12}
		total={1:0,2:0,3:0,4:0,5:0}
		
		results = parser._get_nego_datas(data)
		n = 0
		summary_nego_bank = {}
		for key in sorted(results.keys(), key=lambda k:k):
			ws.write_merge(rowcount,rowcount,0,16, "Negotiated On : "+parser.formatLang(key, date=True), normal_bold_style)
			rowcount+=1
			subtotal={1:0,2:0,3:0,4:0,5:0}
			nos = 0
			for nego in sorted(results[key],key = lambda x : x['inv_date']):
				nos += 1
				ws.write(rowcount, 0, nos, normal_style_float_round)
				ws.write(rowcount, 1, nego['inv_number'], normal_style)
				ws.write(rowcount, 2, nego['inv_date'], normal_style)
				ws.write(rowcount, 3, nego['lc_batch'], normal_style)
				ws.write(rowcount, 4, nego['customer'], normal_style)
				if nego['customer'] and len(str(nego['customer']))>max_width_col[4]:
					max_width_col[4]=len(str(nego['customer']))
				ws.write(rowcount, 5, nego['giro_number'], normal_style)
				ws.write(rowcount, 6, nego['payment_bank'], normal_style)
				ws.write(rowcount, 7, nego['nego_bank'], normal_style)
				if nego['nego_bank'] and len(str(nego['nego_bank']))>max_width_col[7]:
					max_width_col[7]=len(str(nego['nego_bank']))
				keysumm = nego['nego_bank']
				if keysumm not in summary_nego_bank.keys():
					summary_nego_bank.update({keysumm:{1:0,2:0,3:0,4:0,5:0}})

				ws.write(rowcount, 8, nego['cury'], normal_style)
				ws.write(rowcount, 9, nego['dispatch_amt'], normal_style_float)
				ws.write(rowcount, 10, nego['dispatch_amt_company_curr'], normal_style_float)
				ws.write(rowcount, 11, nego['received_amt'], normal_style_float)
				ws.write(rowcount, 12, nego['received_amt_company_curr'], normal_style_float)
				# ws.write(rowcount, 13, 0.0, normal_style_float)
				# ws.write(rowcount, 14, 0.0, normal_style_float)
				# ws.write(rowcount, 15, 0.0, normal_style_float)
				net_amount=nego['received_amt']
				ws.write(rowcount, 13, net_amount, normal_style_float)
				
				subtotal[1]+=nego['dispatch_amt']
				# summary_nego_bank[keysumm]+=nego['dispatch_amt']

				subtotal[2]+=nego['dispatch_amt_company_curr']
				summary_nego_bank[keysumm][2]+=nego['dispatch_amt_company_curr']

				subtotal[3]+=nego['received_amt']
				# summary_nego_bank[keysumm][3]+=nego['received_amt']

				subtotal[4]+=nego['received_amt_company_curr']
				summary_nego_bank[keysumm][4]+=nego['received_amt_company_curr']
				# subtotal[5]+=payment['n_realisation_days']
				# subtotal[6]+=payment['n_realisation_days']
				# subtotal[7]+=payment['n_realisation_days']
				subtotal[5]+=net_amount
				summary_nego_bank[keysumm][5]+=net_amount
				rowcount+=1
			
			ws.write_merge(rowcount,rowcount,0,8, "Subtotal : ",subtotal_title_style)
			for c in subtotal.keys():
				total[c]+=subtotal[c]
				ws.write(rowcount, c+8, subtotal[c], subtotal_style2)
			rowcount+=1

		ws.write_merge(rowcount,rowcount,0,8, "Total", subtotal_title_style)
		for c in total.keys():
			ws.write(rowcount, c+8, total[c], subtotal_style2)
			if total[c] and len(str(total[c]))>max_width_col[c+8]:
				max_width_col[c+8]=len(str(total[c]))
		rowcount+=2

		ws.write_merge(rowcount,rowcount+1,7,8, "Negotiation\nBank",th_bottom_style)
		ws.write_merge(rowcount,rowcount+1,9,9, "Dispatch\nAmount",th_bottom_style)
		ws.write_merge(rowcount,rowcount+1,10,10, "Received\nAmount",th_bottom_style)
		# ws.write_merge(rowcount,rowcount,11,13, "Charges", th_bottom_style)
		# ws.write(rowcount+1,11, "Negotation", th_bottom_style)
		# ws.write(rowcount+1,12, "Discount", th_bottom_style)
		# ws.write(rowcount+1,13, "Others", th_bottom_style)
		ws.write_merge(rowcount,rowcount+1,11,11, "Net\nNegotiation",th_bottom_style)
		rowcount+=2

		totalsumm={1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0}
		for keysumm in summary_nego_bank.keys():
			ws.write_merge(rowcount,rowcount,7,8, keysumm, normal_bold_style)
			ws.write(rowcount,9, summary_nego_bank[keysumm][2], normal_style_float_bold)
			ws.write(rowcount,10, summary_nego_bank[keysumm][4], normal_style_float_bold)
			# ws.write(rowcount,11, summary_nego_bank[keysumm][5], normal_style_float_bold)
			# ws.write(rowcount,12, summary_nego_bank[keysumm][6], normal_style_float_bold)
			# ws.write(rowcount,13, summary_nego_bank[keysumm][7], normal_style_float_bold)
			ws.write(rowcount,11, summary_nego_bank[keysumm][5], normal_style_float_bold)
			for c in summary_nego_bank[keysumm].keys():
				totalsumm[c]+=summary_nego_bank[keysumm][c]
			rowcount+=1

		ws.write_merge(rowcount,rowcount,7,8, "Total", subtotal_style)
		ws.write(rowcount,9, totalsumm[2], subtotal_style2)
		ws.write(rowcount,10, totalsumm[4], subtotal_style2)
		# ws.write(rowcount,11, totalsumm[5], subtotal_style2)
		# ws.write(rowcount,12, totalsumm[6], subtotal_style2)
		# ws.write(rowcount,13, totalsumm[7], subtotal_style2)
		ws.write(rowcount,11, totalsumm[5], subtotal_style2)

		for c in max_width_col.keys():
			ws.col(c).width = 256*int(max_width_col[c]*1.4)
		
		pass

nego_report_xls('report.nego.report','negotiation.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=negotiation_report_parser, header=False)