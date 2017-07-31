import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt

class om_tally_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(om_tally_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
		})

	def _get_results(self, data):
		cr = self.cr
		uid = self.uid
		# {u'period_id': [28, u'01/2016'], u'journal_ids': [209, 5], u'ar_account_ids': [230, 231, 232], u'id': 2, u'adv_account_ids': [120]}
		period_id = data['form']['period_id'][0]
		# period_id_bef = (data['form']['period_id'][0]-1)
		ar_account = data['form']['ar_account_ids']
		adv_account = data['form']['adv_account_ids']
		adv_journal = data['form']['journal_ids']
		
		period = self.pool.get('account.period').browse(cr,uid,period_id)
		# period_bef = self.pool.get('account.period').browse(cr,uid,period_id_bef)
		
		datestart = period.date_start
		# datestart_bef = period_bef.date_start
		last_period_id = self.pool.get('account.period').search(cr,uid,[('date_stop','<',datestart),('special','=',False)],order="date_stop desc")
		# last_period_id_bef = self.pool.get('account.period').search(cr,uid,[('date_stop','<',datestart_bef),('special','=',False)],order="date_stop desc")
		last_period = self.pool.get('account.period').browse(cr,uid,last_period_id)[0]
		# last_period_bef = self.pool.get('account.period').browse(cr,uid,last_period_id_bef)[0]
		opening_dt = last_period.date_stop
		closing_dt = period.date_stop
		# opening_dt_bef = last_period_bef.date_stop
		cr.execute("""
			select * from get_om_tally("""+str(period_id)+""",array"""+str(ar_account)+""",array"""+
				str(adv_account)+""",array"""+str(adv_journal)+""",'"""+str(opening_dt)+"""','"""+str(closing_dt)+"""')  order by sale,curr,code,cust
			""")
		result = cr.fetchall()
		return result 

class om_tally_report_xls(report_xls):
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
		
		total_lbl_style					=xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;')
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		
		ws = wb.add_sheet("Tally -"+data['form']['period_id'][1].replace('/','-'),cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		ws.write_merge(0,0,0,11, "PT. Bitratex Industries", title_style)
		ws.write_merge(1,1,0,11, "OM TALLY - "+data['form']['period_id'][1], title_style)
		
		ws.write(3,0, "SALE", th_both_style)
		ws.write(3,1, "CODE", th_both_style)
		ws.write(3,2, "CUSTOMER", th_both_style)
		ws.write(3,3, "CURR", th_both_style)
		ws.write(3,4, "OPENING", th_both_style)
		ws.write(3,5, "CN", th_both_style)
		ws.write(3,6, "DN", th_both_style)
		ws.write(3,7, "INV DPP", th_both_style)
		ws.write(3,8, "INV TAX", th_both_style)
		ws.write(3,9, "PA", th_both_style)
		ws.write(3,10, "PP", th_both_style)
		ws.write(3,11, "TOTAL", th_both_style)
		
		curr = 4
		topen=0
		cn=0
		dn=0
		inv_dpp=0
		inv_tax=0
		pa=0
		pp=0
		total_alls=0
		result = parser._get_results(data)
		ws.set_panes_frozen(True)
		ws.set_horz_split_pos(curr) 
		ws.set_vert_split_pos(4) 
		for rows in result:
			ws.write(curr,0,rows[3],normal_style)
			ws.write(curr,1,rows[1],normal_style)
			ws.write(curr,2,rows[2],normal_style)
			ws.write(curr,3,rows[4],normal_style)
			ws.write(curr,4,rows[5],normal_style_float)
			ws.write(curr,5,rows[7],normal_style_float)
			ws.write(curr,6,rows[8],normal_style_float)
			ws.write(curr,7,rows[9],normal_style_float)
			ws.write(curr,8,rows[10],normal_style_float)
			ws.write(curr,9,rows[11],normal_style_float)
			ws.write(curr,10,rows[12],normal_style_float)
			ws.write(curr,11,rows[6],normal_style_float)
			# ws.write(curr,11,rows[5]+rows[7]+rows[8]+rows[9]-rows[6]-rows[10]-rows[11],normal_style_float)
			curr+=1

			topen+=rows[5]
			cn+=rows[7]
			dn+=rows[8]
			inv_dpp+=rows[9]
			inv_tax+=rows[10]
			pa+=rows[11]
			pp+=rows[12]
			# total=rows[5]+rows[7]+rows[8]+rows[9]-rows[6]-rows[10]-rows[11]
			total = rows[6]
			total_alls+=total
			ws.write(curr,3,"Total",total_lbl_style)
			ws.write(curr,4,topen,total_style)
			ws.write(curr,5,cn,total_style)
			ws.write(curr,6,dn,total_style)
			ws.write(curr,7,inv_dpp,total_style)
			ws.write(curr,8,inv_tax,total_style)
			ws.write(curr,9,pa,total_style)
			ws.write(curr,10,pp,total_style)
			ws.write(curr,11,total_alls,total_style)

		width = [1800,2000,17000,2400,4500,4500,4500,4500,4500,4500,4500,4500]
		for x in range(0,12):
			ws.col(x).width=width[x]
		pass
om_tally_report_xls('report.om.tally.report','om.tally.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=om_tally_report_parser, header=False)