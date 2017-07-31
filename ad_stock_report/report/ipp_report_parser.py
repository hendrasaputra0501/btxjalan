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

class ipp_report_parse(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(ipp_report_parse, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_issue':self._get_issue,

		})

	def _get_period(self,period_id):
		if period_id:
			return self.pool.get('account.period').browse(self.cr,self.uid,period_id)
		return '-'

	def _get_issue(self,data):
		cr = self.cr
		uid = self.uid
		po_line_pool =self.pool.get('purchase.order.line')
		curr_pool =self.pool.get('res.currency')
		internal_locs = self.pool.get('stock.location').search(cr,uid,[('usage','=','internal')])
		consume_locs = self.pool.get('stock.location').search(cr,uid,[('usage','=','production')])
		product_ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=','Stores')])
		subaccount_ids = data['sub_account_ids']
		if data['filter']=='period':
			period =self.pool.get('account.period').browse(cr,uid,data['period_id'])
			date_start = period.date_start
			date_end = period.date_stop
		else:
			date_start = data['date_start']
			date_end = data['date_end']
		if subaccount_ids:
			issue_ids = self.pool.get('stock.move').search(cr,uid,[('location_id','in',internal_locs), \
			('location_dest_id','in',consume_locs),('date','>=',date_start),('date','<=',date_end),('state','=','done'),('product_id','in',product_ids),('analytic_account_id','in',subaccount_ids)])
		else:
			issue_ids = self.pool.get('stock.move').search(cr,uid,[('location_id','in',internal_locs), \
			('location_dest_id','in',consume_locs),('date','>=',date_start),('date','<=',date_end),('state','=','done'),('product_id','in',product_ids)])
		result_issues = []
		
		# def recursive_track(mv,list_match_out):
		# 	for matchout in mv.matching_ids_out:
		# 		if matchout.move_in_id.matching_ids_out:
		# 			return recursive_track(matchout.move_in_id,list_match_out)
		# 		else:
		# 			list_match_out.append(matchout)
		# 			return (matchout.move_in_id,list_match_out)

		def recursive_track(mv,list_match_out):
			for matchout in mv.matching_ids_out:
				if matchout.move_in_id.matching_ids_out:
					list_match_out.extend(recursive_track(matchout.move_in_id,[])) 
				else:
					list_match_out.append(matchout)
			
			return list_match_out

		for issue in self.pool.get('stock.move').browse(cr,uid,issue_ids):
			sources=[]
			matching = []
			#check recursively for last matching
			matching = recursive_track(issue,sources)
			result_issues.append([issue,matching])
		result = []
		for res_issue in result_issues:
			for mm in res_issue[1]:
				is_mm_mrr = mm.move_in_id.location_id.usage=='supplier' and True or False
				mm_po_line_pu_net,mm_po_line_pu =0.0,0.0
				mm_po_line_cur = 'USD'
				if is_mm_mrr and mm.move_in_id.purchase_line_id:
					mm_po_line_pu = mm.move_in_id.purchase_line_id and mm.move_in_id.purchase_line_id.price_unit
					
					mm_po_line_pu_net = po_line_pool.get_line_price_after_disc(cr,uid,mm.move_in_id.purchase_line_id,context={})
					mm_po_line_cur = mm.move_in_id.purchase_line_id.order_id.pricelist_id.currency_id.name
					po_curr_id = mm.move_in_id.purchase_line_id.order_id.pricelist_id.currency_id.id
					po_company_curr_id = mm.move_in_id.purchase_line_id.order_id.company_id.currency_id.id
					po = mm.move_in_id.purchase_line_id.order_id
					po_line_pu_usd = curr_pool.compute(cr,uid,po_curr_id,po_company_curr_id,mm_po_line_pu_net,context={'date':po.date_order})
					# total_po_amount = sum([(l.price_unit*l.product_qty) for l in po.order_line if l.product_id])
					total_po_amount = po.amount_untaxed
					total_po_amount_usd = curr_pool.compute(cr,uid,po_curr_id,po_company_curr_id,total_po_amount,context={'date':po.date_order})
					total_po_qty = sum([l.product_qty for l in po.order_line if l.product_id])
				result.append({
					'issue_nbr'		: res_issue[0].picking_id.name,
					'issue_date'	: res_issue[0].picking_id.date_done_2,
					'issue_qty'		: mm.qty,
					'issue_pu'		: mm.move_in_id.price_unit,
					'issue_sub_acc'	: res_issue[0].analytic_account_id and res_issue[0].analytic_account_id.code or '-',
					'mrr_nbr'		: is_mm_mrr and mm.move_in_id.picking_id and mm.move_in_id.picking_id.name or 'OPS / ADJ',
					'mrr_date'		: is_mm_mrr and mm.move_in_id.picking_id.date_done_2 or mm.move_in_id.date[:10],
					'mrr_qty'		: mm.qty,
					'mrr_pu'		: mm.move_in_id.price_unit,
					'mrr_pu_curr'	: is_mm_mrr and mm_po_line_pu_net or mm.move_in_id.price_unit,
					'mrr_cur'		: is_mm_mrr and mm_po_line_cur or 'USD',
					'po_nbr'		: is_mm_mrr and po.name or 'OPS / ADJ',
					'po_date'		: is_mm_mrr and po.date_order or '',
					'po_partner_cd'	: is_mm_mrr and po.partner_id.partner_code or '',
					'po_partner_nm'	: is_mm_mrr and po.partner_id.name or '',
					'segment_1'		: res_issue[0].product_id.first_segment_code and res_issue[0].product_id.first_segment_code.code or '',
					'segment_2'		: res_issue[0].product_id.second_segment_code and res_issue[0].product_id.second_segment_code.name or '',
					'product_cd'	: res_issue[0].product_id.default_code or res_issue[0].product_id.old_code or '',
					'product_nm'	: res_issue[0].product_id.name or '',
					'location_id'	: res_issue[0].location_id.alias or res_issue[0].location_id.name or '',
					'po_qty'		: is_mm_mrr and mm.move_in_id.purchase_line_id.product_qty or 0.0,
					'po_pu'			: is_mm_mrr and po_line_pu_usd or mm.move_in_id.price_unit,
					'po_pu_curr_net'	: is_mm_mrr and mm_po_line_pu_net,
					'po_pu_curr'	: is_mm_mrr and mm_po_line_pu,
					'po_curr'		: is_mm_mrr and mm_po_line_cur,
					'total_po_qty'	: total_po_qty,
					'total_po_amount'	: total_po_amount,
					'total_po_amount_usd'	: total_po_amount_usd,
					})
		import operator
		result2=[]
		result2 = sorted(result,key=operator.itemgetter('issue_date','issue_nbr','mrr_date','mrr_nbr','po_date','po_nbr'))
		return result2
	
	

class ipp_report_xls(report_xls):
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
		c = parser.localcontext['company']
		i=0

		ws = wb.add_sheet('IPP',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 1 # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 100
		ws.normal_magn = 100
		ws.print_scaling=100
		ws.page_preview = False
		ws.set_fit_width_to_pages(1)
		##Penempatan untuk template rows
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz centre; ')
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: top thin, bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		# Header of Ageing Summary Statement
		rowcount = 0
		ws.write_merge(rowcount,rowcount,0,23, "Issue - MRR - PO Detail",title_style)
		rowcount+=1
		if data['filter']=='period':
			ws.write_merge(rowcount,rowcount,0,23, "Period: %s "%parser._get_period(data['period_id']).name,title_style)
		else:
			ws.write_merge(rowcount,rowcount,0,23, "Date Range: %s - %s"%(data['date_start'],data['date_end']),title_style)
		rowcount+=2
		ws.write_merge(rowcount,rowcount,0,4, "ISSUE",title_style)
		ws.write_merge(rowcount,rowcount,5,10, "MRR",title_style)
		ws.write_merge(rowcount,rowcount,11,26, "PO",title_style)
		rowcount+=1

		ws.write(rowcount,0,'IssueNbr',title_style)
		ws.write(rowcount,1,'Date',title_style)
		ws.write(rowcount,2,'Qty',title_style)
		ws.write(rowcount,3,'TranAmt',title_style)
		ws.write(rowcount,4,'Sub Acct ',title_style)
		ws.write(rowcount,5,'MRRNbr',title_style)
		ws.write(rowcount,6,'Date',title_style)
		ws.write(rowcount,7,'Qty',title_style)
		ws.write(rowcount,8,'ExtCost',title_style)
		ws.write(rowcount,9,'Cury Id',title_style)
		ws.write(rowcount,10,'CuryExtCost',title_style)
		ws.write(rowcount,11,'PONbr',title_style)
		ws.write(rowcount,12,'Date',title_style)
		ws.write(rowcount,13,'Vend Id',title_style)
		ws.write(rowcount,14,'Vend Name',title_style)
		ws.write(rowcount,15,'First Segment ',title_style)
		ws.write(rowcount,16,'Second Segment',title_style)
		ws.write(rowcount,17,'Invt Id',title_style)
		ws.write(rowcount,18,'Invt Descr',title_style)
		ws.write(rowcount,19,'Site Id',title_style)
		ws.write(rowcount,20,'Qty',title_style)
		ws.write(rowcount,21,'CuryPriceUnit',title_style)
		ws.write(rowcount,22,'ExtCost (USD)',title_style)
		ws.write(rowcount,23,'Cury Id',title_style)
		ws.write(rowcount,24,'CuryExtCost',title_style)
		ws.write(rowcount,25,'TotalQtyPO',title_style)
		ws.write(rowcount,26,'CuryTotalPO',title_style)
		ws.write(rowcount,27,'TotalPO(USD)',title_style)

		ress = parser._get_issue(data)
		rowcount+=1
		for res in ress:
			ws.write(rowcount,0,res['issue_nbr'],normal_style)
			ws.write(rowcount,1,res['issue_date'],normal_style)
			ws.write(rowcount,2,res['issue_qty'],normal_style_float)
			ws.write(rowcount,3,res['issue_qty']*res['issue_pu'],normal_style_float)
			ws.write(rowcount,4,res['issue_sub_acc'],normal_style)
			ws.write(rowcount,5,res['mrr_nbr'],normal_style)
			ws.write(rowcount,6,res['mrr_date'],normal_style)
			ws.write(rowcount,7,res['mrr_qty'],normal_style_float)
			ws.write(rowcount,8,res['mrr_qty']*res['mrr_pu'],normal_style_float)
			ws.write(rowcount,9,res['mrr_cur'],normal_style)
			ws.write(rowcount,10,res['mrr_qty']*res['mrr_pu_curr'],normal_style_float)
			ws.write(rowcount,11,res['po_nbr'],normal_style)
			ws.write(rowcount,12,res['po_date'],normal_style)
			ws.write(rowcount,13,res['po_partner_cd'],normal_style)
			ws.write(rowcount,14,res['po_partner_nm'],normal_style)
			ws.write(rowcount,15,res['segment_1'],normal_style)
			ws.write(rowcount,16,res['segment_2'],normal_style)
			ws.write(rowcount,17,res['product_cd'],normal_style)
			ws.write(rowcount,18,res['product_nm'],normal_style)
			ws.write(rowcount,19,res['location_id'],normal_style)
			ws.write(rowcount,20,res['po_qty'],normal_style_float)
			ws.write(rowcount,21,res['po_pu_curr'],normal_style_float)
			ws.write(rowcount,22,res['po_qty']*res['po_pu'],normal_style_float)
			ws.write(rowcount,23,res['po_curr'],normal_style_float)
			ws.write(rowcount,24,res['po_qty']*res['po_pu_curr_net'],normal_style_float)
			ws.write(rowcount,25,res['total_po_qty'],normal_style_float)
			ws.write(rowcount,26,res['total_po_amount'],normal_style_float)
			ws.write(rowcount,27,res['total_po_amount_usd'],normal_style_float)
			rowcount+=1
		pass


ipp_report_xls('report.ipp.report.xls','ipp.wizard', 'addons/ad_stock_report/report/summary_stock_report.mako',
						parser=ipp_report_parse)