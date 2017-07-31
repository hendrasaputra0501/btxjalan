import re
import time
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime

 
class advance_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(advance_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result_detail':self._get_result_detail,
		})
	
	def _get_result_detail(self, data):
		res = []
		data=data['form']
		query = "SELECT \
				adv.name,to_char(adv.effective_date,'DD/MM/YY') as adv_date ,p.name as cust_name,p.partner_code, \
				(SELECT string_agg(so.name,'; ') FROM sale_order so \
					LEFT JOIN sale_order_advance_rel so_rel on so_rel.adv_id=so.id \
					WHERE so_rel.order_id=adv.id) as so_name, \
				(SELECT string_agg(inv.name,'; ') FROM account_invoice inv \
					WHERE inv.move_id=(SELECT mvl2.move_id FROM account_move_line mvl2 WHERE mvl2.reconcile_id=mvl.reconcile_id \
						or mvl2.reconcile_partial_id=mvl.reconcile_partial_id limit 1)) as inv_number, \
				(case coalesce(mvl3.currency_id,0) when 0 then mvl3.debit else mvl3.amount_currency end) as amount_usd, aa.name as bank \
			FROM account_advance_payment adv \
				LEFT JOIN res_partner p on adv.partner_id=p.id \
				LEFT JOIN account_move_line mvl on adv.move_id=mvl.move_id and adv.account_id=mvl.account_id \
				LEFT JOIN account_move_line mvl3 on adv.move_id=mvl3.move_id and adv.account_id!=mvl3.account_id \
				LEFT JOIN account_account aa on mvl3.account_id=aa.id \
			WHERE adv.date_payment<='%s' and adv.date_payment>='%s' and adv.sale_type='%s' and adv.currency_id=%s\
			"%(data['end_date'],data['start_date'],data['sale_type'],data['currency_id'][0])
		
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _get_result_outs(self, data):
		data=data['form']
		cr = self.cr
		uid = self.uid
		aml_obj = self.pool.get('account.move.line')
		as_on_date=data['as_on_date']
		query = "SELECT\
					adv.id as adv_id, aml.id as aml_id\
				FROM\
					account_advance_payment adv\
					INNER JOIN account_move_line aml ON aml.move_id=adv.move_id and aml.account_id=adv.account_id\
				WHERE adv.date_payment<='%s' and adv.type='in' and adv.state='posted' and adv.currency_id=%s and adv.sale_type='%s'\
				"%(as_on_date,data['currency_id'][0],data['sale_type'])
		
		self.cr.execute(query)
		qresults = self.cr.dictfetchall()
		list_outstanding_adv = {}
		for aml in aml_obj.browse(cr, uid, [x['aml_id'] for x in qresults]):
			balance = aml.debit-aml.credit
			balance_amt_curr = aml.currency_id and aml.amount_currency or 0.0
			sign = balance < 0 and -1 or 1
			for adj in (aml.reconcile_id and aml.reconcile_id.line_id or (aml.reconcile_partial_id and aml.reconcile_partial_id.line_partial_ids or [])):
				if adj.id!=aml.id and adj.date<=as_on_date:
					if aml.currency_id and aml.currency_id.id!=aml.company_id.currency_id.id:
						if adj.currency_id and adj.currency_id.id!=aml.currency_id.id:
							balance_amt_curr+=curr_obj.compute(cr, uid, adj.currency_id.id, aml.currency_id.id, adj.amount_currency, context={'date':adj.date})
						elif adj.currency_id and adj.currency_id==aml.currency_id:
							balance_amt_curr+=adj.amount_currency
						elif not adj.currency_id:
							balance_amt_curr+=curr_obj.compute(cr, uid, aml.company_id.currency_id.id, aml.currency_id.id, (adj.debit-adj.credit), context={'date':adj.date})
					balance+=(adj.debit-adj.credit)
			if round(balance,2)==0.0:
				continue

			adv = [x['adv_id'] for x in qresults if x['aml_id']==aml.id]
			if not adv:
				continue
			list_outstanding_adv.update({(adv and adv[0] or False):balance_amt_curr and sign*balance_amt_curr or sign*balance})
		if not list_outstanding_adv:
			return []
		query = "SELECT \
				adv.id as adv_id, adv.name, adv.effective_date as adv_date, p.name as cust_name, p.partner_code, \
				(SELECT string_agg(so.name,'; ') FROM sale_order so \
					LEFT JOIN sale_order_advance_rel so_rel on so_rel.adv_id=so.id \
					WHERE so_rel.order_id=adv.id) as so_name, \
				(SELECT string_agg(inv.name,'; ') FROM account_invoice inv \
					WHERE inv.move_id=(SELECT mvl2.move_id FROM account_move_line mvl2 WHERE mvl2.reconcile_id=mvl.reconcile_id \
						or mvl2.reconcile_partial_id=mvl.reconcile_partial_id limit 1)) as inv_number, \
				(case coalesce(mvl3.currency_id,0) when 0 then mvl3.debit else mvl3.amount_currency end) as amount_usd, (case coalesce(mvl.currency_id,0) when 0 then mvl.credit else -mvl.amount_currency end) as amount_adv_usd, aa.name as bank \
			FROM account_advance_payment adv \
				LEFT JOIN res_partner p on adv.partner_id=p.id \
				LEFT JOIN account_move_line mvl on adv.move_id=mvl.move_id and adv.account_id=mvl.account_id \
				LEFT JOIN account_move_line mvl3 on adv.move_id=mvl3.move_id and adv.account_id!=mvl3.account_id \
				LEFT JOIN account_account aa on mvl3.account_id=aa.id \
			WHERE adv.id in %s"%(str(tuple([x for x in list_outstanding_adv.keys()])))
		
		self.cr.execute(query)
		results = self.cr.dictfetchall()
		for line in results:
			line.update({'balance_amt' : list_outstanding_adv[line['adv_id']]})
		return results

	def _get_result_adjustment(self, data):
		data=data['form']
		cr = self.cr
		uid = self.uid
		aml_obj = self.pool.get('account.move.line')
		start_date=data['start_date']
		end_date=data['end_date']
		query = "SELECT\
					adv.id as adv_id, aml.id as aml_id\
				FROM\
					account_advance_payment adv\
					INNER JOIN account_move_line aml ON aml.move_id=adv.move_id and aml.account_id=adv.account_id\
				WHERE adv.date_payment<='%s' and adv.type='in' and adv.state='posted' and adv.currency_id=%s and adv.sale_type='%s'\
				"%(end_date,data['currency_id'][0],data['sale_type'])
		
		self.cr.execute(query)
		qresults = self.cr.dictfetchall()
		list_adjustment_adv = {}
		for aml in aml_obj.browse(cr, uid, [x['aml_id'] for x in qresults]):
			adj_amount = 0
			adj_amt_curr = 0.0
			# sign = (aml.debit-aml.credit) < 0 and -1 or 1
			sign = 1
			invoice_alocation = []
			
			adv = [x['adv_id'] for x in qresults if x['aml_id']==aml.id]
			if not adv:
				continue
			
			for adj in (aml.reconcile_id and aml.reconcile_id.line_id or (aml.reconcile_partial_id and aml.reconcile_partial_id.line_partial_ids or [])):
				if adj.id!=aml.id and adj.date>=start_date and adj.date<=end_date:
					if aml.currency_id and aml.currency_id.id!=aml.company_id.currency_id.id:
						if adj.currency_id and adj.currency_id.id!=aml.currency_id.id:
							adj_amt_curr+=curr_obj.compute(cr, uid, adj.currency_id.id, aml.currency_id.id, sign*adj.amount_currency, context={'date':adj.date})
						elif adj.currency_id and adj.currency_id==aml.currency_id:
							adj_amt_curr+=sign*adj.amount_currency
						elif not adj.currency_id:
							adj_amt_curr+=curr_obj.compute(cr, uid, aml.company_id.currency_id.id, aml.currency_id.id, sign*(adj.debit-adj.credit), context={'date':adj.date})
					adj_amount+=(adj.debit-adj.credit)
					q = "SELECT coalesce(ai.internal_number,ai.number) as invoice_number\
						FROM account_voucher av \
							INNER JOIN account_voucher_split_advances avsa ON avsa.voucher_id=av.id\
							INNER JOIN voucher_split_advance_line vsal ON vsal.split_id=avsa.id\
							INNER JOIN account_invoice ai ON ai.id=vsal.invoice_id\
						WHERE av.move_id="+str(adj.move_id.id)
					self.cr.execute(q)
					r = self.cr.dictfetchall()
					for v in r:
						if v['invoice_number'] not in invoice_alocation:
							invoice_alocation.append(v['invoice_number'])
			if round(adj_amount,2)==0.0:
				continue

			list_adjustment_adv.update({(adv and adv[0] or False):{
					'adj_amount':adj_amt_curr and adj_amt_curr or adj_amount,
					'invoices':invoice_alocation and ','.join([str(x) for x in invoice_alocation]) or '',
				}})
		if not list_adjustment_adv:
			return []
		query = "SELECT \
				adv.id as adv_id, adv.name, adv.effective_date as adv_date, p.name as cust_name, p.partner_code, \
				(SELECT string_agg(so.name,'; ') FROM sale_order so \
					LEFT JOIN sale_order_advance_rel so_rel on so_rel.adv_id=so.id \
					WHERE so_rel.order_id=adv.id) as so_name, \
				(case coalesce(mvl3.currency_id,0) when 0 then mvl3.debit else mvl3.amount_currency end) as amount_usd, (case coalesce(mvl.currency_id,0) when 0 then mvl.credit else -mvl.amount_currency end) as amount_adv_usd, aa.name as bank \
			FROM account_advance_payment adv \
				LEFT JOIN res_partner p on adv.partner_id=p.id \
				LEFT JOIN account_move_line mvl on adv.move_id=mvl.move_id and adv.account_id=mvl.account_id \
				LEFT JOIN account_move_line mvl3 on adv.move_id=mvl3.move_id and adv.account_id!=mvl3.account_id \
				LEFT JOIN account_account aa on mvl3.account_id=aa.id \
			WHERE adv.id in %s"%(str(tuple([x for x in list_adjustment_adv.keys()])))
		
		self.cr.execute(query)
		results = self.cr.dictfetchall()
		for line in results:
			line.update({'adj_amt' : list_adjustment_adv[line['adv_id']]['adj_amount']})
			line.update({'inv_number' : list_adjustment_adv[line['adv_id']]['invoices']})
		return results
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_date_range(self,data):
		date_start = data['start_date']
		date_stop = data['end_date']
		if date_start and not date_stop:
			da = datetime.strptime(date_start,"%Y-%m-%d")
			return "From : %s"%da.strftime("%d/%m/%Y")
		elif date_stop and not date_start:
			db = datetime.strptime(date_stop,"%Y-%m-%d")
			return "Until : %s"%db.strftime("%d/%m/%Y")
		elif date_stop and date_start:
			da = datetime.strptime(date_start,"%Y-%m-%d")
			db = datetime.strptime(date_stop,"%Y-%m-%d")
			return "Range : %s - %s"%(da.strftime("%d/%m/%Y"),db.strftime("%d/%m/%Y"))
		else:
			return "Wholetime"

class advance_report_xls(report_xls):
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
		ws = wb.add_sheet('Advance Report',cell_overwrite_ok=True)
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
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz center; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')

		ws.write_merge(0,0,0,8, "PT.BITRATEX INDUSTRIES", title_style)
		if data['form']['report_type']=='adv_report':
			ws.write_merge(1,1,0,8, "%s PREPAYMENT STATEMENT-UNIT 1 & 2"%(data['form']['sale_type'].upper()), title_style)
			ws.write_merge(2,2,0,8, parser._get_date_range(data['form']), title_style)
		elif data['form']['report_type']=='adv_outs':
			ws.write_merge(1,1,0,8, "%s PREPAYMENT OUTSTANDING"%(data['form']['sale_type'].upper()), title_style)
			ws.write_merge(2,2,0,8, "As ON : "+parser.formatLang(data['form']['as_on_date'],date=True), title_style)
		elif data['form']['report_type']=='adv_adj':
			ws.write_merge(1,1,0,8, "%s PREPAYMENT ADJUSTMENT"%(data['form']['sale_type'].upper()), title_style)
			ws.write_merge(2,2,0,8, parser._get_date_range(data['form']), title_style)
			
		ws.write_merge(4,4,0,1, "CREDIT NOTE", th_both_style)
		ws.write(5,0, "BATCH NO.", th_both_style)
		ws.write(5,1, "DATE", th_both_style)
		ws.write_merge(4,5,2,2, "SC\nNumber", th_both_style)
		ws.write_merge(4,4,3,4, "Customer", th_both_style)
		ws.write(5,3, "ID", th_both_style)
		ws.write(5,4, "NAME", th_both_style)
		ws.write_merge(4,5,5,5, "INVOICE\nNo", th_both_style)
		ws.write_merge(4,5,6,6, "AMOUNT\n"+data['form']['currency_id'][1], th_both_style)
		ws.write_merge(4,5,7,7, "BANK", th_both_style)
		ws.write_merge(4,5,8,8, "REASON", th_both_style)
		
		rowcount=6
		max_width_col={0:12,1:8,2:12,3:5,4:10,5:12,6:8,7:8,8:6}
		total = 0.0
		summary_per_bank = {}
		if data['form']['report_type']=='adv_report':
			for adv in parser._get_result_detail(data):
				# print "LLLLLLLLLLLLLLLLL", adv['amount_usd']
				ws.write(rowcount,0,adv['name'],normal_style)
				if len(adv['name'] and adv['name'] or '')>max_width_col[0]:
					max_width_col[0]= len(adv['name'])
				ws.write(rowcount,1,adv['adv_date'], normal_style)
				ws.write(rowcount,2,adv['so_name'],normal_style)	
				if len(adv['so_name'] and adv['so_name'] or '')>max_width_col[2]:
					max_width_col[2]= len(adv['so_name'])
				ws.write(rowcount,3,adv['partner_code'],normal_style)
				ws.write(rowcount,4,adv['cust_name'],normal_style)
				if len(adv['cust_name'] and adv['cust_name'] or '')>max_width_col[4]:
					max_width_col[4]= len(adv['cust_name'])
				ws.write(rowcount,5,adv['inv_number'],normal_style)
				ws.write(rowcount,6,(adv['amount_usd'] and adv['amount_usd'] or 0.0),normal_style_float)
				total += (adv['amount_usd'] and adv['amount_usd'] or 0.0)
				ws.write(rowcount,7,adv['bank'],normal_style)
				if len(adv['bank'] and adv['bank'] or '')>max_width_col[7]:
					max_width_col[7]= len(adv['bank'])
				ws.write(rowcount,8,'')

				if adv['bank'] not in summary_per_bank:
					summary_per_bank.update({adv['bank']:0.0})
				summary_per_bank[adv['bank']]+=(adv['amount_usd'] and adv['amount_usd'] or 0.0)

				rowcount+=1

			ws.write_merge(rowcount,rowcount,0,5, "Total Advance",total_style2)
			ws.write(rowcount, 6, total, total_style2)
			if len(str(total))>max_width_col[6]:
				max_width_col[6]= len(str(total))
			ws.write_merge(rowcount, rowcount, 7, 8, "", total_style2)
			rowcount+=2
		elif data['form']['report_type']=='adv_outs':
			for adv in parser._get_result_outs(data):
				ws.write(rowcount,0,adv['name'],normal_style)
				if len(adv['name'] and adv['name'] or '')>max_width_col[0]:
					max_width_col[0]= len(adv['name'])
				ws.write(rowcount,1,parser.formatLang(adv['adv_date'],date=True), normal_style)
				ws.write(rowcount,2,adv['so_name'],normal_style)	
				if len(adv['so_name'] and adv['so_name'] or '')>max_width_col[2]:
					max_width_col[2]= len(adv['so_name'])
				ws.write(rowcount,3,adv['partner_code'],normal_style)
				ws.write(rowcount,4,adv['cust_name'],normal_style)
				if len(adv['cust_name'] and adv['cust_name'] or '')>max_width_col[4]:
					max_width_col[4]= len(adv['cust_name'])
				ws.write(rowcount,5,adv['inv_number'],normal_style)
				ws.write(rowcount,6,((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['balance_amt'], normal_style_float)
				total += ((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['balance_amt']
				ws.write(rowcount,7,adv['bank'],normal_style)
				if len(adv['bank'] and adv['bank'] or '')>max_width_col[7]:
					max_width_col[7]= len(adv['bank'])
				ws.write(rowcount,8,'')

				if adv['bank'] not in summary_per_bank:
					summary_per_bank.update({adv['bank']:0.0})
				summary_per_bank[adv['bank']]+=((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['balance_amt']

				rowcount+=1
			ws.write_merge(rowcount,rowcount,0,5, "Total Advance",total_style2)
			ws.write(rowcount, 6, total, total_style2)
			if len(str(total))>max_width_col[6]:
				max_width_col[6]= len(str(total))
			ws.write_merge(rowcount, rowcount, 7, 8, "", total_style2)
			rowcount+=2
		elif data['form']['report_type']=='adv_adj':
			for adv in parser._get_result_adjustment(data):
				ws.write(rowcount,0,adv['name'],normal_style)
				if len(adv['name'] and adv['name'] or '')>max_width_col[0]:
					max_width_col[0]= len(adv['name'])
				ws.write(rowcount,1,parser.formatLang(adv['adv_date'],date=True), normal_style)
				ws.write(rowcount,2,adv['so_name'],normal_style)	
				if len(adv['so_name'] and adv['so_name'] or '')>max_width_col[2]:
					max_width_col[2]= len(adv['so_name'])
				ws.write(rowcount,3,adv['partner_code'],normal_style)
				ws.write(rowcount,4,adv['cust_name'],normal_style)
				if len(adv['cust_name'] and adv['cust_name'] or '')>max_width_col[4]:
					max_width_col[4]= len(adv['cust_name'])
				ws.write(rowcount,5,adv['inv_number'],normal_style)
				ws.write(rowcount,6,((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['adj_amt'], normal_style_float)
				total += ((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['adj_amt']
				ws.write(rowcount,7,adv['bank'],normal_style)
				if len(adv['bank'] and adv['bank'] or '')>max_width_col[7]:
					max_width_col[7]= len(adv['bank'])
				ws.write(rowcount,8,'')

				if adv['bank'] not in summary_per_bank:
					summary_per_bank.update({adv['bank']:0.0})
				summary_per_bank[adv['bank']]+=((adv['amount_usd'] and adv['amount_usd'] or 0.0)/adv['amount_adv_usd'])*adv['adj_amt']

				rowcount+=1
			ws.write_merge(rowcount,rowcount,0,5, "Total Advance",total_style2)
			ws.write(rowcount, 6, total, total_style2)
			if len(str(total))>max_width_col[6]:
				max_width_col[6]= len(str(total))
			ws.write_merge(rowcount, rowcount, 7, 8, "", total_style2)
			rowcount+=2
		# print ">>>>>>>>>>>>>>>>>>>>>>>>", datas
		

		ws.write_merge(rowcount,rowcount+1,4,5, "BANK", th_both_style)
		ws.write_merge(rowcount,rowcount+1,6,6, "AMOUNT\n"+data['form']['currency_id'][1], th_both_style)
		rowcount+=2
		total_summary = 0.0
		if summary_per_bank:
			for key in summary_per_bank.keys():
				ws.write_merge(rowcount, rowcount, 4, 5, key, normal_bold_style)
				ws.write(rowcount, 6, summary_per_bank[key], normal_style_float_bold)
				total_summary += summary_per_bank[key]
				rowcount+=1
		ws.write_merge(rowcount, rowcount, 4, 5, "Total", total_style2)
		ws.write(rowcount, 6, total_summary, total_style2)

		for x in range(0,9):
			ws.col(x).width = 256*int(max_width_col[x]*1.4)
		pass

advance_report_xls('report.advance.report','advance.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=advance_report_parser, header=False)
advance_report_xls('report.os.advance.report','advance.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=advance_report_parser, header=False)
advance_report_xls('report.adj.advance.report','advance.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=advance_report_parser, header=False)
