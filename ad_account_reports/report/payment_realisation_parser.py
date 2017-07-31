import re
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
 
class payment_realisation_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(payment_realisation_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})
		
	def _get_result(self, data):
		cr = self.cr
		uid = self.uid
		voucher_pool_obj = self.pool.get('account.voucher')
		vline_pool_obj = self.pool.get('account.voucher.line')
		invoice_pool_obj = self.pool.get('account.invoice')
		mline_pool_obj = self.pool.get('account.move.line')
		curr_pool_obj = self.pool.get('res.currency')

		from_date = data['form']['from_date']
		to_date = data['form']['to_date']
		period_id = data['form']['period_id']
		sale_type = data['form']['sale_type']
		currency_id = data['form']['currency_id']
		# journal_ids = data['form']['journal_ids']
		# account_ids = data['form']['account_ids']

		query = "\
				SELECT\
					a.id as voucher_id,\
					b.id as line_id,\
					b.move_line_id as invoice_move_id\
				FROM\
					account_voucher a\
					INNER JOIN account_voucher_line b ON b.voucher_id=a.id\
					INNER JOIN account_move_line c ON b.move_line_id=c.id\
					INNER JOIN account_invoice d ON d.move_id=c.move_id\
				WHERE\
					b.move_line_id is not NULL\
					AND a.type='receipt' \
					AND d.sale_type='"+sale_type+"' \
					AND d.currency_id="+str(currency_id[0])+" "
		if data['form']['filter'] == 'filter_date':
			query += " AND a.date between '"+from_date+"' and '"+to_date+"'"
		elif data['form']['filter'] == 'filter_period':
			query += " AND a.period_id="+str(period_id[0])

		# if journal_ids:
		# 	query += " AND c.journal_id IN ("+','.join([str(x) for x in journal_ids])+") "
		# if account_ids:
		# 	query += " AND c.account_id IN ("+','.join([str(x) for x in account_ids])+") "
		self.cr.execute(query)
		res = self.cr.dictfetchall()

		result_grouped = {}
		for line in vline_pool_obj.browse(cr, uid, [x['line_id'] for x in res]):
			if not line.move_line_id or not line.move_line_id.invoice or not line.voucher_id:
				continue

			key1 = line.voucher_id.partner_id
			if key1 not in result_grouped:
				result_grouped.update({key1:[]})

			due_date = line.move_line_id.date_maturity!='False' and line.move_line_id.date_maturity or line.move_line_id.date
			# amount_paid = self._get_amount_company_currency(line.voucher_id.currency_id.id, line.amount, line.voucher_id.date)
			if line.move_line_id.invoice.currency_id.id!=line.voucher_id.currency_id.id:
				amount_paid = self._get_amount_converted(line.voucher_id.currency_id.id, line.move_line_id.invoice.currency_id.id, line.amount, line.voucher_id.date)
			else:
				amount_paid = line.amount

			chg_amt = 0.0
			exchange_account_ids = []
			if line.voucher_id.company_id.income_receivable_currency_exchange_account_id:
				exchange_account_ids.append(line.voucher_id.company_id.income_receivable_currency_exchange_account_id.id)
			if line.voucher_id.company_id.expense_receivable_currency_exchange_account_id:
				exchange_account_ids.append(line.voucher_id.company_id.expense_receivable_currency_exchange_account_id.id)

			total_payment_amount = sum([(x.type=='cr' and x.amount or -1*x.amount) for x in line.voucher_id.line_ids])
			total_alocation = sum([(x.type=='cr' and x.amount or 0.0) for x in line.voucher_id.line_ids])
			writeoff_amount = total_payment_amount-line.voucher_id.amount
			if writeoff_amount!=0.0:
				if line.voucher_id.extra_writeoff:
					for wline in line.voucher_id.writeoff_lines:
						if wline.invoice_related_id and wline.invoice_related_id.id==line.move_line_id.invoice.id and wline.account_id.id not in exchange_account_ids:
							if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
								chg_amt += wline.amount
							else:
								chg_amt += self._get_amount_converted(from_curr.id, wline.invoice_related_id.currency_id.id, wline.amount, line.voucher_id.date)
				else:
					if line.voucher_id.writeoff_acc_id and line.voucher_id.writeoff_acc_id.id not in exchange_account_ids:
						ratio_rcvd = line.amount/total_alocation
						if line.move_line_id.invoice.currency_id.id==line.voucher_id.currency_id.id:
							chg_amt += ratio_rcvd*writeoff_amount
						else:
							chg_amt += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
					# chg_amt += self._get_amount_company_currency(from_curr.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
			result_grouped[key1].append({
					'inv_number' : line.move_line_id.invoice.internal_number or line.move_line_id.invoice.number or '',
					'inv_date' : datetime.strptime(line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%b'),
					'n_realisation_days' : (datetime.strptime(line.voucher_id.date,'%Y-%m-%d')-datetime.strptime(line.move_line_id.date,'%Y-%m-%d')).days,
					'n_inv_days' : (datetime.strptime(due_date,'%Y-%m-%d')-datetime.strptime(line.move_line_id.date,'%Y-%m-%d')).days,
					'amount_paid' : amount_paid,
					'chg_amt' : chg_amt,
					'date_payment' : datetime.strptime(line.voucher_id.date, '%Y-%m-%d').strftime('%d/%b'),
				})
		return result_grouped
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_amount_converted(self, from_curr, to_curr, amount, date):
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, to_curr, amount, context={'date':date})

class payment_realisation_xls(report_xls):
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
		ws = wb.add_sheet('Payment Realisation',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		company = "PT.BITRATEX INDUSTRIES"
		doc_name = ""
		if data['form']['filter'] == 'filter_date':
			from_date = datetime.strptime(data['form']['from_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			to_date = datetime.strptime(data['form']['to_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			doc_name = "Payment Realisation between "+str(from_date)+" and "+str(to_date)
		elif data['form']['filter'] == 'filter_period':
			period = data['form']['period_id'][1]
			doc_name = "Payment Realisation of Period "+period
		
		ws.write_merge(0,0,0,12, company, title_style)
		ws.write_merge(1,1,0,12, doc_name, title_style)
		
		ws.write(2,0, "Doc#", th_both_style)
		ws.write(2,1, "Inv No", th_both_style)
		ws.write(2,2, "Date", th_both_style)
		ws.write(2,3, "Paid", th_both_style)
		ws.write(2,4, "T.dys", th_both_style)
		ws.write(2,5, "CrDys", th_both_style)
		ws.write(2,6, "ODys", th_both_style)
		ws.write(2,7, "Amount", th_both_style)
		ws.write(2,8, "Interest", th_both_style)
		ws.write(2,9, "Cash", th_both_style)
		ws.write(2,10, "Others", th_both_style)
		ws.write(2,11, "Bnk Chgs", th_both_style)
		ws.write(2,12, "Net Amount", th_both_style)
		rowcount=3
		ws.horz_split_pos = rowcount
		
		total = {
			1:0.0,
			2:0.0,
			3:0.0,
			4:0.0,
			5:0.0,
			6:0.0,
		}
		max_width_col = {0:4,1:12,2:8,3:8,4:5,5:5,6:5,7:12,8:12,9:12,10:12,11:12,12:12}
		results = parser._get_result(data)
		list_summary = []
		for key in sorted(results.keys(),key=lambda k: k.name):
			ws.write_merge(rowcount,rowcount,0,12, key.name or '',normal_bold_style)
			rowcount+=1
			nos = 0
			subtotal = {
				1:0.0,
				2:0.0,
				3:0.0,
				4:0.0,
				5:0.0,
				6:0.0,
				7:0.0,
				8:0.0,
				9:0.0,
			}
			summary = {
				'partner_name' : key.name,
			}
			for payment in sorted(results[key],key = lambda x : x['date_payment']):
				nos += 1
				ws.write(rowcount, 0, nos, normal_style_float_round)
				ws.write(rowcount, 1, payment['inv_number'],normal_style)
				ws.write(rowcount, 2, payment['inv_date'],normal_style)
				ws.write(rowcount, 3, payment['date_payment'],normal_style)
				ws.write(rowcount, 4, payment['n_realisation_days'],normal_style_float_round)
				ws.write(rowcount, 5, payment['n_inv_days'],normal_style_float_round)
				od_days = payment['n_realisation_days']-payment['n_inv_days']
				ws.write(rowcount, 6, od_days<=0 and 0 or od_days,normal_style_float_round)
				ws.write(rowcount, 7, payment['amount_paid'],normal_style_float)
				ws.write(rowcount, 8, 0.0,normal_style_float)
				ws.write(rowcount, 9, 0.0,normal_style_float)
				ws.write(rowcount, 10, 0.0,normal_style_float)
				ws.write(rowcount, 11, payment['chg_amt'],normal_style_float)
				net_amount = payment['amount_paid']-payment['chg_amt']
				ws.write(rowcount, 12, net_amount,normal_style_float)
				subtotal[1]+=payment['amount_paid']
				# subtotal[2]+=results2[0]['nego_amount']
				# subtotal[3]+=results2[0]['balance']
				# subtotal[4]+=results2[0]['balance']
				subtotal[5]+=payment['chg_amt']
				subtotal[6]+=net_amount
				subtotal[7]+=payment['n_realisation_days']
				subtotal[8]+=payment['n_inv_days']
				subtotal[9]+=od_days
				rowcount+=1
			ws.write_merge(rowcount,rowcount,2,3, "Customer Total",normal_style)
			ws.write(rowcount, 7, subtotal[1],normal_style_float)
			ws.write(rowcount, 8, subtotal[2],normal_style_float)
			ws.write(rowcount, 9, subtotal[3],normal_style_float)
			ws.write(rowcount, 10, subtotal[4],normal_style_float)
			ws.write(rowcount, 11, subtotal[5],normal_style_float)
			ws.write(rowcount, 12, subtotal[6],normal_style_float)
			rowcount+=1

			summary['count'] = nos
			summary['n_realisation_days'] = subtotal[7]/nos
			summary['n_inv_days'] = subtotal[8]/nos
			summary['n_od_days'] = subtotal[9]/nos
			summary['amount_paid'] = subtotal[1]
			summary['amount_interest'] = subtotal[2]
			summary['amount_cash'] = subtotal[3]
			summary['amount_others'] = subtotal[4]
			summary['chg_amt'] = subtotal[5]
			summary['net_amount'] = subtotal[6]
			list_summary.append(summary)
			ws.write_merge(rowcount,rowcount,2,3, "Customer Average")
			ws.write(rowcount, 4, subtotal[7]/nos,normal_style_float_round)
			ws.write(rowcount, 5, subtotal[8]/nos,normal_style_float_round)
			ws.write(rowcount, 6, subtotal[9]/nos,normal_style_float_round)
			ws.write(rowcount, 7, subtotal[1]/nos,normal_style_float)
			ws.write(rowcount, 8, subtotal[2]/nos,normal_style_float)
			ws.write(rowcount, 9, subtotal[3]/nos,normal_style_float)
			ws.write(rowcount, 10, subtotal[4]/nos,normal_style_float)
			ws.write(rowcount, 11, subtotal[5]/nos,normal_style_float)
			ws.write(rowcount, 12, subtotal[6]/nos,normal_style_float)
			rowcount+=1

			total[1]+=subtotal[1]
			# total[2]+=subtotal[2]
			# total[3]+=subtotal[3]
			# total[4]+=subtotal[4]
			# total[5]+=subtotal[5]
			total[6]+=subtotal[6]

		# ws.write(rowcount, 7, total[1])
		# ws.write(rowcount, 8, total[2])
		# ws.write(rowcount, 9, total[3])
		# ws.write(rowcount, 10, total[4])
		# ws.write(rowcount, 11, total[5])
		# ws.write(rowcount, 12, total[6])
		for c in max_width_col.keys():
			ws.col(c).width = 256*int(max_width_col[c]*1.4)

		ws1 = wb.add_sheet('Payment Realisation Summary',cell_overwrite_ok=True)
		ws1.panes_frozen = True
		ws1.remove_splits = True
		ws1.portrait = 0 # Landscape
		ws1.fit_width_to_pages = 1
		company = "PT.BITRATEX INDUSTRIES"
		doc_name = ""
		if data['form']['filter'] == 'filter_date':
			from_date = datetime.strptime(data['form']['from_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			to_date = datetime.strptime(data['form']['to_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			doc_name = "Payment Realisation between "+str(from_date)+" and "+str(to_date)
		elif data['form']['filter'] == 'filter_period':
			period = data['form']['period_id'][1]
			doc_name = "Payment Realisation of Period "+period
		
		ws1.write_merge(0,0,0,10, company, title_style)
		ws1.write_merge(1,1,0,10, doc_name, title_style)
		
		ws1.write(2,0, "Cnt", th_both_style)
		ws1.write(2,1, "Customer", th_both_style)
		ws1.write(2,2, "T.dys", th_both_style)
		ws1.write(2,3, "CrDys", th_both_style)
		ws1.write(2,4, "ODys", th_both_style)
		ws1.write(2,5, "Amount", th_both_style)
		ws1.write(2,6, "Interest", th_both_style)
		ws1.write(2,7, "Cash", th_both_style)
		ws1.write(2,8, "Others", th_both_style)
		ws1.write(2,9, "Bnk Chgs", th_both_style)
		ws1.write(2,10, "Net Amount", th_both_style)
		rowcount=3
		ws1.horz_split_pos = rowcount
		
		total = {
			1:0.0,
			2:0.0,
			3:0.0,
			4:0.0,
			5:0.0,
			6:0.0,
			7:0.0,
			8:0.0,
			9:0.0,
		}
		max_width_col = {0:4,1:10,2:5,3:5,4:5,5:12,6:12,7:12,8:12,9:12,10:12}
		for summary in list_summary:
			ws1.write(rowcount, 0, summary['count'], normal_style_float_round)
			ws1.write(rowcount, 1, summary['partner_name'],normal_style)
			if len(summary['partner_name'])>max_width_col[1]:
				max_width_col[1]=len(summary['partner_name'])
			ws1.write(rowcount, 2, summary['n_realisation_days'],normal_style_float_round)
			ws1.write(rowcount, 3, summary['n_inv_days'],normal_style_float_round)
			ws1.write(rowcount, 4, summary['n_od_days'],normal_style_float_round)
			ws1.write(rowcount, 5, summary['amount_paid'],normal_style_float)
			ws1.write(rowcount, 6, summary['amount_interest'],normal_style_float)
			ws1.write(rowcount, 7, summary['amount_cash'],normal_style_float)
			ws1.write(rowcount, 8, summary['amount_others'],normal_style_float)
			ws1.write(rowcount, 9, summary['chg_amt'],normal_style_float)
			ws1.write(rowcount, 10, summary['net_amount'],normal_style_float)
			rowcount+=1
			total[1]+=summary['amount_paid']
			# total[2]+=summary['amount_interest']
			# total[3]+=summary['amount_cash']
			# total[4]+=summary['amount_others']
			total[5]+=summary['chg_amt']
			total[6]+=summary['net_amount']
			total[7]+=summary['n_realisation_days']
			total[8]+=summary['n_inv_days']
			total[9]+=summary['n_od_days']
		nos = len(list_summary)
		ws1.write_merge(rowcount,rowcount,0,1, "Grand Total", subtotal_style)
		ws1.write(rowcount, 2, total[7]/nos,subtotal_style2)
		ws1.write(rowcount, 3, total[8]/nos,subtotal_style2)
		ws1.write(rowcount, 4, total[9]/nos,subtotal_style2)
		ws1.write(rowcount, 5, total[1],subtotal_style2)
		ws1.write(rowcount, 6, total[2],subtotal_style2)
		ws1.write(rowcount, 7, total[3],subtotal_style2)
		ws1.write(rowcount, 8, total[4],subtotal_style2)
		ws1.write(rowcount, 9, total[5],subtotal_style2)
		ws1.write(rowcount, 10, total[6],subtotal_style2)
		rowcount+=1
		for c in max_width_col.keys():
			ws1.col(c).width = 256*int(max_width_col[c]*1.4)
		pass

payment_realisation_xls('report.payment.realisation.analysis','payment.realisation.analysis.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=payment_realisation_parser, header=False)