import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
from openerp.osv import osv
 
class apvendor_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(apvendor_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_domain(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		period_from=data['form'].get('period_from',False) and data['form']['period_from'][0] or False
		period_to=data['form'].get('period_to',False) and data['form']['period_to'][0] or False
		
		cr = self.cr
		uid = self.uid
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		fiscalperiod_obj = self.pool.get('account.period')
		query = ""
		domain = []
		if data['form'].get('account_ids',False) and data['form']['account_ids']:
			domain.append(('account_id','in',data['form']['account_ids']))
		else:
			raise osv.except_osv(_('No Id Found'), _('Please repeat your work')) 
		
		if data['form'].get('journal_ids',False) and data['form']['journal_ids']:
			domain.append(('journal_id','in',data['form']['journal_ids']))
		domain.append(('journal_id.type','!=','situation'))

		if data['form'].get('partner_ids',False) and data['form']['partner_ids']:
			domain.append(('partner_id','in',data['form']['partner_ids']))
		else:
			domain.append(('partner_id','!=',False))

		if data['form']['filter'] == 'filter_date':
			domain.append(('date','>=',from_date))
			domain.append(('date','<=',to_date))
		elif data['form']['filter'] == 'filter_period':
			period_ids = []
			period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, period_from, period_to)
			domain.append(('period_id','in',period_ids))

		return domain

	def _get_query(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		period_from=data['form'].get('period_from',False) and data['form']['period_from'][0] or False
		period_to=data['form'].get('period_to',False) and data['form']['period_to'][0] or False
		initial_bal=context.get('initial_bal',False)
		fiscalyear_id = data['form'].get('fiscalyear_id',False) and data['form']['fiscalyear_id'][0] or False
		cr = self.cr
		uid = self.uid
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		fiscalperiod_obj = self.pool.get('account.period')

		opening_period_id = fiscalperiod_obj.search(cr, uid, [('fiscalyear_id','=',fiscalyear_id),('special','=',True)])
		opening_period = fiscalperiod_obj.browse(cr, uid, opening_period_id[0])

		query = ""
		if data['form'].get('account_ids',[]) and data['form']['account_ids']:
			query += " AND l.account_id IN ("+','.join([str(x) for x in data['form']['account_ids']])+") "
		if data['form'].get('journal_ids',[]) and data['form']['journal_ids']:
			query += " AND l.journal_id in ("+','.join([str(x) for x in data['form']['journal_ids']])+") "

		if data['form'].get('partner_ids',[]) and data['form']['partner_ids']:
			query += " AND l.partner_id is NOT NULL AND l.partner_id in ("+','.join([str(x) for x in data['form']['partner_ids']])+") "
		else:
			query += " AND l.partner_id is NOT NULL "

		if data['form']['filter'] == 'filter_date':
			if initial_bal:
				if opening_period.date_start == from_date:
					query += " AND l.period_id = "+str(opening_period.id)+" "
				elif opening_period.date_start < from_date:
					query += " AND l.date >= '"+opening_period.date_start+"' AND l.date<'"+from_date+"' "
			else:
				query += " AND l.date between '"+from_date+"' and '"+to_date+"'"
		elif data['form']['filter'] == 'filter_period':
			period_ids = []
			if initial_bal:
				period_company_id = fiscalperiod_obj.browse(cr, uid, period_from, context=context).company_id.id
				first_period = fiscalperiod_obj.search(cr, uid, [('company_id', '=', period_company_id),('fiscalyear_id','=',fiscalyear_id)], order='date_start', limit=1)[0]
				print ":::::::::::::::::::::::::::::;", first_period, period_from
				period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, first_period, period_from)
				if period_from in period_ids:
					period_ids.remove(period_from)
			else:
				period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, period_from, period_to)
			
			query += " AND l.period_id IN ("+','.join([str(x) for x in period_ids or []])+") "

		return query

	def _get_initbalance_per_vendor(self, data):
		query_init = "SELECT \
					d.id as partner_id,\
					d.partner_code as partner_code,\
					d.name as partner_name,\
					sum(coalesce(l.debit,0.0)) as debit,\
					sum(coalesce(l.credit,0.0)) as credit,\
					sum(coalesce(l.debit,0.0)-coalesce(l.credit,0.0)) as progress,\
					sum(case coalesce(l.currency_id,0) when 0 then 0.0 else coalesce(l.amount_currency,0.0) end) as amount_currency\
				FROM \
					account_move_line l\
					INNER JOIN account_move b ON b.id=l.move_id\
					INNER JOIN account_account c ON c.id=l.account_id\
					LEFT JOIN res_partner d ON d.id=l.partner_id\
					LEFT JOIN res_currency e ON e.id=l.currency_id\
					INNER JOIN account_period f ON f.id=l.period_id\
					INNER JOIN account_journal g ON g.id=l.journal_id\
					LEFT JOIN account_analytic_account h ON h.id=l.analytic_account_id\
				WHERE\
					l.state='valid' "
		query_init += self._get_query(data, context={'initial_bal':True})
		query_init += "GROUP BY d.id,d.partner_code,d.name"
		self.cr.execute(query_init)
		return self.cr.dictfetchall()

	def _get_result(self, data):
		cr = self.cr
		uid = self.uid

		# initialize pooler obj
		am_obj = self.pool.get('account.move')
		aml_obj = self.pool.get('account.move.line')
		ai_obj = self.pool.get('account.invoice')
		rp_obj = self.pool.get('res.partner')
		ip_obj = self.pool.get('ir.property')

		journal_ids = data['form']['journal_ids']
		account_ids = data['form']['account_ids']
		# adv_account_id = data['form'].get('adv_account_id',False) and data['form']['adv_account_id'][0] or False
		# show_outstanding_advance = data['form']['show_outstanding_advance']
		
		# customer_ids = self.pool.get('res.partner').search(cr, uid, [('customer','=',True)])
		# ap transaction
		domain = [('state','=','valid')]
		for d in self._get_domain(data):
			domain.append(d)
		aml_ids = aml_obj.search(cr, uid, domain)
		
		
		# init_ids = self._get_initbalance_per_vendor(data)

		if not aml_ids:
			return {}
		
		# ============== MAPPING FOR RETURN VALUE =================
		res_grouped = {}
		for aml in aml_obj.browse(cr, uid, aml_ids):
			key = (aml.partner_id.id, aml.partner_id.name, aml.partner_id.partner_code)
			
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append({
					'batch_number' : aml.move_id and aml.move_id.name or '',
					'ref_number' : aml.ref  or '',
					'date1' : dt.strptime(aml.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'date_maturity' : aml.date_maturity!=False and dt.strptime(aml.date_maturity, '%Y-%m-%d').strftime('%d/%m/%Y') or '',
					'payment_term' : aml.invoice and aml.invoice.payment_term and aml.invoice.payment_term.name or False,
					'inv_number' : aml.invoice and (aml.invoice.reference and aml.invoice.reference or aml.invoice.supplier_invoice_number or '') or '',
					'period' : aml.period_id and aml.period_id.name or '',
					'doc_amount' : aml.debit>0 and -1*aml.debit or aml.credit,
					'curr_doc_amount' : aml.currency_id and (aml.amount_currency and -1*aml.amount_currency or 0) or 0.0,
					# 'curr_doc_amount' : aml.currency_id and (aml.amount_currency and -1*aml.amount_currency or 0) or (not aml.currency_id and aml.debit>0 and -1*aml.debit or aml.credit),
					'currency' : aml.currency_id and aml.currency_id.name or (aml.company_id and aml.company_id.currency_id and aml.company_id.currency_id.name or ''),	
				})

		return res_grouped
			
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

	def get_start_period(self, data):
		if data.get('form', False) and data['form'].get('period_from', False):
			return self.pool.get('account.period').browse(self.cr,self.uid,data['form']['period_from'][0]).name
		return ''

	def get_end_period(self, data):
		if data.get('form', False) and data['form'].get('period_to', False):
			return self.pool.get('account.period').browse(self.cr, self.uid, data['form']['period_to'][0]).name
		return ''

	def _display_filter(self, parser, data):
		if data['form']['filter'] == 'filter_date':
			filter_string = '%s -> %s' % (parser.formatLang(data['form']['from_date'], date=True),
										  parser.formatLang(data['form']['to_date'], date=True))
		elif data['form']['filter'] == 'filter_period':
			filter_string = '%s -> %s' % (parser.get_start_period(data),parser.get_end_period(data))

		return 'Filter By: %s' % (filter_string)

class apvendor_report_xls(report_xls):
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
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
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
		ws.write_merge(1,1,0,12, "AP VENDOR", title_style)
		ws.write_merge(2,2,0,12, parser._display_filter(parser,data), title_style)

		ws.write(3,0, "", th_bottom_style)
		ws.write(3,1, "Batch Number", th_bottom_style)
		ws.write(3,2, "Reference", th_bottom_style)
		ws.write(3,3, "Date", th_bottom_style)
		ws.write(3,4, "Due Date", th_bottom_style)
		ws.write(3,5, "Payment Term", th_bottom_style)
		ws.write(3,6, "Invoice Number", th_bottom_style)
		ws.write(3,7, "Period", th_bottom_style)
		ws.write(3,8, "Doc Amt", th_bottom_style)
		ws.write(3,9, "Balance", th_bottom_style)
		ws.write(3,10, "CuryID", th_bottom_style)
		ws.write(3,11, "Cury Doc Amt", th_bottom_style)
		ws.write(3,12, "Cury Balance", th_bottom_style)
		
		max_width_col = {0:5,1:12,2:10,3:10,4:10,5:12,6:14,7:11,8:12,9:12,10:6,11:12,12:12}
		rowcount=4
		
		total_bal, total_cury_bal = 0.0, 0.0
		results = parser._get_result(data)

		init_memorizer = parser._get_initbalance_per_vendor(data)
		vendor_hide = {}
		for x in init_memorizer:
			k = (x['partner_id'],x['partner_name'],x['partner_code'] and x['partner_code'] or False)
			if k not in vendor_hide:
				vendor_hide.update({k:True})
			if round(abs(x['progress']),2)>0 or round(abs(x['amount_currency']),2)>0:
				vendor_hide[k] = False

		for ky, val in results.items():
			if ky not in vendor_hide:
				vendor_hide.update({ky:True})
			if val and len(val)>0:
				vendor_hide[ky] = vendor_hide[ky] and False

		for keyvendor in sorted(vendor_hide.keys() or [], key=lambda k:k[1]):
			if vendor_hide.get(keyvendor,True):
				continue
			op = [x for x in init_memorizer if x['partner_id']==keyvendor[0]]
			bal = 0.0
			cury_bal = 0.0
			if op:
				op = op[0]
				bal = -1*op['progress']
				cury_bal = -1*op['amount_currency']
			ws.write(rowcount,0,keyvendor[2],normal_bold_style)
			ws.write_merge(rowcount,rowcount,1,6,keyvendor[1],normal_bold_style)
			ws.write(rowcount,7,"Op. Balance",normal_style)
			ws.write(rowcount,8,bal,normal_style_float)
			ws.write(rowcount,11,cury_bal,normal_style_float)
			rowcount+=1
			
			key = keyvendor
			if key in results.keys():
				for line in sorted(results[key],key=lambda l:l['date1']):
					bal+=line['doc_amount']
					cury_bal+=line['curr_doc_amount']
					ws.write(rowcount,1,line['batch_number'],normal_style)
					if len(line['batch_number'] and str(line['batch_number']) or '')>max_width_col[1]:
						max_width_col[1] = len(str(line['batch_number']))
					ws.write(rowcount,2,line['ref_number'],normal_style)
					if len(line['ref_number'] and str(line['ref_number']) or '')>max_width_col[2]:
						max_width_col[2] = len(str(line['ref_number']))
					ws.write(rowcount,3,line['date1'],normal_style)
					ws.write(rowcount,4,line['date_maturity'],normal_style)
					ws.write(rowcount,5,line['payment_term'] or '',normal_style)
					ws.write(rowcount,6,line['inv_number'],normal_style)
					if len(line['inv_number'] and str(line['inv_number']) or '')>max_width_col[6]:
						max_width_col[6] = len(str(line['inv_number']))
					ws.write(rowcount,7,line['period'],normal_style)
					ws.write(rowcount,8,line['doc_amount'],normal_style_float)
					ws.write(rowcount,9,bal,normal_style_float)
					ws.write(rowcount,10,line['currency'],normal_style)
					ws.write(rowcount,11,line['curr_doc_amount'],normal_style_float)
					ws.write(rowcount,12,cury_bal,normal_style_float)
					rowcount+=1
			ws.write_merge(rowcount,rowcount,1,7,"Vendor Totals : ",subtotal_title_style)
			ws.write(rowcount,8,bal,subtotal_style2)
			ws.write_merge(rowcount,rowcount,9,10," ",subtotal_title_style)
			ws.write(rowcount,11,cury_bal,subtotal_style2)
			total_bal+=bal
			total_cury_bal+=cury_bal
			rowcount+=1

		ws.write_merge(rowcount,rowcount,1,7,"Grand Totals : ",subtotal_title_style)
		ws.write(rowcount,8,total_bal,subtotal_style2)
		if len(total_bal and str(total_bal) or '')>max_width_col[8]:
			max_width_col[8] = len(str(total_bal))
		ws.write_merge(rowcount,rowcount,9,10," ",subtotal_title_style)
		ws.write(rowcount,11,total_cury_bal,subtotal_style2)
		if len(total_cury_bal and str(total_cury_bal) or '')>max_width_col[11]:
			max_width_col[11] = len(str(total_cury_bal))
		
		for k in max_width_col.keys():
			ws.col(k).width = 256*int(max_width_col[k]*1.4)		
		
		pass
apvendor_report_xls('report.apvendor.report','apvendor.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=apvendor_report_parser, header=False)