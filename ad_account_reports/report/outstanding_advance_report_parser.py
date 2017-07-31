import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt

class outstanding_advance_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(outstanding_advance_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
		})

	def _get_results(self, data):
		cr = self.cr
		uid = self.uid

		# initialize pooler obj
		curr_obj = self.pool.get('res.currency')
		am_obj = self.pool.get('account.move')
		aml_obj = self.pool.get('account.move.line')
		rp_obj = self.pool.get('res.partner')
		ip_obj = self.pool.get('ir.property')

		# init var
		results = []
		as_on_date = data['form']['as_on_date']
		account_ids = data['form']['account_ids']
		# journal_ids = data['form']['journal_ids']
		
		domain = [('account_id','in',account_ids),('state','=','valid'),('date','<=',as_on_date),('move_id','!=',False)]
		# if journal_ids:
		# 	domain.append(('journal_id','in',journal_ids))

		# all account_move_line of related advance account
		aml_ids = aml_obj.search(cr, uid, domain)
		for aml in aml_obj.browse(cr, uid, aml_ids):
			balance = aml.debit-aml.credit
			balance_amt_curr = aml.currency_id and aml.amount_currency or 0.0
			sign = balance < 0 and -1 or 1
			state = aml.reconcile_id and 'Closed' or 'Open'
			for settlement in (aml.reconcile_id and aml.reconcile_id.line_id or (aml.reconcile_partial_id and aml.reconcile_partial_id.line_partial_ids or [])):
				if settlement.id!=aml.id and settlement.date<=as_on_date:
					if aml.currency_id and aml.currency_id.id!=aml.company_id.currency_id.id:
						if settlement.currency_id and settlement.currency_id.id!=aml.currency_id.id:
							balance_amt_curr+=curr_obj.compute(cr, uid, settlement.currency_id.id, aml.currency_id.id, settlement.amount_currency, context={'date':settlement.date})
						elif settlement.currency_id and settlement.currency_id==aml.currency_id:
							balance_amt_curr+=settlement.amount_currency
						elif not settlement.currency_id:
							balance_amt_curr+=curr_obj.compute(cr, uid, aml.company_id.currency_id.id, aml.currency_id.id, (settlement.debit-settlement.credit), context={'date':settlement.date})
					balance+=(settlement.debit-settlement.credit)
			if round(balance,2)==0.0:
				continue

			results.append({
					'partner_id' : aml.partner_id and aml.partner_id.id or False,
					'partner_name' : aml.partner_id and (aml.partner_id.partner_alias or aml.partner_id.name) or False,
					'partner_code' : aml.partner_id and aml.partner_id.partner_code or False,
					'original_amount' : aml.currency_id and aml.amount_currency or (aml.debit-aml.credit),
					'balance' : balance,
					'balance_amt_curr' : balance_amt_curr,
					'currency_name' : aml.currency_id and aml.currency_id.name or aml.company_id.currency_id.name,
					'date' : aml.date,
					'batch_number' : aml.move_id.name,
					'period_name' : aml.period_id and aml.period_id.name or (aml.move_id.period_id and aml.move_id.period_id.name or ''),
					'description' : aml.name,
					'state' : state,
					'account_code' : aml.account_id.code2,
					'to_check' : aml.reconcile_id and aml.reconcile_id or (aml.reconcile_partial_id and aml.reconcile_partial_id or (aml.id)),
				})

		# we will check if there is acount_move_line that has the same account_move_reconcile id
		temp_dict = {}
		for l in results:
			key = l['to_check']
			if key not in temp_dict:
				temp_dict.update({key:[]})
			temp_dict[key].append(l)
		if temp_dict:
			results = []
			for k in temp_dict.keys():
				results.append(sorted(temp_dict[k], key=lambda k:k['date'])[0])
		return results

	def _get_result_grouped(self, lines):
		result_grouped = {}
		for line in lines:
			key1 = line['account_code']
			if key1 not in result_grouped:
				result_grouped.update({key1:{}})
			key2=(line['partner_id'],line['partner_code'])
			if key2 not in result_grouped[key1]:
				result_grouped[key1].update({key2:[]})
			result_grouped[key1][key2].append(line)
		return result_grouped
		
class outstanding_advance_report_xls(report_xls):
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
		
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed;')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:bottom dashed;')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		
		result_grouped = parser._get_result_grouped(parser._get_results(data))
		for account_code in sorted(result_grouped.keys()):
			ws = wb.add_sheet(str(account_code),cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1 
			
			ws.write_merge(0,0,0,9, "PT. Bitratex Industries", title_style)
			ws.write_merge(1,1,0,9, "DETAIL ADVANCE AS ON "+parser.formatLang(data['form']['as_on_date'],date=True), title_style)
			
			ws.write_merge(3,3,0,1, "Partner", th_both_style)
			ws.write(4,0, "Code", th_both_style)
			ws.write(4,1, "Name", th_both_style)
			ws.write_merge(3,4,2,2, "Period", th_both_style)
			ws.write_merge(3,4,3,3, "CA/JV No.", th_both_style)
			ws.write_merge(3,4,4,4, "Date", th_both_style)
			ws.write_merge(3,4,5,5, "Transaction\nDescription", th_both_style)
			ws.write_merge(3,4,6,6, "Currency", th_both_style)
			ws.write_merge(3,4,7,7, "Original\nCurrency", th_both_style)
			ws.write_merge(3,4,8,8, "USD\nAmount", th_both_style)
			ws.write_merge(3,4,9,9, "Status", th_both_style)
			
			rowcount=5
			max_width_col={0:5,1:8,2:7,3:8,4:8,5:10,6:5,7:12,8:12,9:5}
			total = {7:0.0,8:0.0}
			
			for key in sorted(result_grouped[account_code].keys(), key=lambda k:k[1]):
				subtotal = {7:0.0,8:0.0}
				for line in sorted(result_grouped[account_code][key], key=lambda l:l['date']):
					ws.write(rowcount,0, line['partner_code'], normal_style)
					ws.write(rowcount,1, line['partner_name'], normal_style)
					ws.write(rowcount,2, line['period_name'], normal_style)
					ws.write(rowcount,3, line['batch_number'], normal_style)
					ws.write(rowcount,4, parser.formatLang(line['date'], date=True), normal_style)
					ws.write(rowcount,5, line['description'], normal_style)
					ws.write(rowcount,6, line['currency_name'], normal_style)
					ws.write(rowcount,7, line['balance_amt_curr'], normal_style_float)
					ws.write(rowcount,8, line['balance'], normal_style_float)
					ws.write(rowcount,9, line['state'], normal_style)

					if len(line['partner_name'] and str(line['partner_name']) or '')>max_width_col[1]:
						max_width_col[1] = len(str(line['partner_name']))
					if len(line['batch_number'] and str(line['batch_number']) or '')>max_width_col[3]:
						max_width_col[3] = len(str(line['batch_number']))
					if len(line['description'] and str(line['description']) or '')>max_width_col[5]:
						max_width_col[5] = len(str(line['description']))
					
					subtotal[7]+=line['balance_amt_curr']
					subtotal[8]+=line['balance']
					rowcount=rowcount+1
				
				ws.write_merge(rowcount,rowcount,0,6, "Total "+str(key[1] or '')+" :", subtotal_style2)
				for c in range(7,9):
					ws.write(rowcount, c, subtotal[c], subtotal_style2)
					total[c]+=subtotal[c]
				rowcount+=1
			rowcount+=1
			ws.write_merge(rowcount,rowcount,0,6,  "Grand Total : ", total_style)
			for c in range(7,9):
				ws.write(rowcount, c, total[c], total_style2)

			for c in range(0,10):
				ws.col(c).width = 256*int(max_width_col[c]*1.4)
		pass
outstanding_advance_report_xls('report.outstanding.advance.report','outstanding.advance.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=outstanding_advance_report_parser, header=False)