import re
import time
import xlwt
from report import report_sxw
from report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class commision_detail_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(commision_detail_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})
	def _get_result(self, data):
		res = []
		start_date=data['form']['start_date']
		end_date=data['form']['end_date']
		sale_type=data['form']['sale_type']
		query = """select * from commission_detail('"""+start_date+"""'::date,'"""+end_date+"""'::date,'"""+sale_type+"""'::text)"""
		self.cr.execute(query)
		result = self.cr.dictfetchall()
		return result
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		cr = self.cr
		uid = self.uid
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

class commision_detail_xls(report_xls):
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
		result = parser._get_result(data)
		# group by production unit
		result_grouped1={}
		for res in result:
			key1=res['production_unit']
			if key1 not in result_grouped1:
				result_grouped1.update({key1:[]})	
			result_grouped1[key1].append(res)
		
		for key2 in result_grouped1.keys():
			ws = wb.add_sheet(key2,cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1 
			ws.preview_magn = 65
			ws.normal_magn = 65
			ws.print_scaling=65
			
			title_style = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
			title_style1 = xlwt.easyxf('font: height 210, name Calibri, colour_index black; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
			hdr_style_border_top = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin;')
			hdr_style_border_top_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin, bottom thin;')
			hdr_style_border_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: bottom thin;')
			normal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap off, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
			normal_right_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0;(#,##0)')
			normal_right_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
			normal_right_style15 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.000;(#,##0.000)')
			normal_right_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')
			subtotal_label_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; borders: bottom dotted;')
			subtotal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0;(#,##0)')
			subtotal_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.00;(#,##0.00)')
			subtotal_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.0000;(#,##0.0000)')

			ws.write_merge(0,0,0,15, "PT.BITRATEX INDUSTRIES", title_style)
			ws.write_merge(1,1,0,15, "DETAIL OF COMMISSION COST - "+key2, title_style)
			ws.write_merge(2,2,0,15, "FROM "+datetime.strptime(data['form']['start_date'],"%Y-%m-%d").strftime("%d/%m/%Y")+" TO "+datetime.strptime(data['form']['end_date'],"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)
			
			ws.write_merge(4,4,0,1, "Invoice", hdr_style_border_top)
			ws.write(5,0, "No.", hdr_style_border_bottom)
			ws.write(5,1, "Date", hdr_style_border_bottom)
			ws.write_merge(4,5,2,2, "LC\nBatch No", hdr_style_border_top_bottom)
			ws.write_merge(4,4,3,4, "Surat Jalan", hdr_style_border_top)
			ws.write(5,3, "No", hdr_style_border_bottom)
			ws.write(5,4, "Date", hdr_style_border_bottom)
			ws.write_merge(4,5,5,5, "Contract\nNo", hdr_style_border_top_bottom)
			ws.write_merge(4,5,6,6, "Customer", hdr_style_border_top_bottom)
			ws.write_merge(4,5,7,7, "Product", hdr_style_border_top_bottom)
			ws.write_merge(4,5,8,8, "Amount\n(US$)", hdr_style_border_top_bottom)
			ws.write_merge(4,4,9,11, "Commision", hdr_style_border_top)
			ws.write(5,9, "Agent", hdr_style_border_bottom)
			ws.write(5,10, "%", hdr_style_border_bottom)
			ws.write(5,11, "(US$)",hdr_style_border_bottom)
			ws.write_merge(4,5,12,12, "Total Freight\n(US$)", hdr_style_border_top_bottom)
			# ws.write_merge(4,5,13,13, "Insurance\n(US$)", hdr_style_border_top_bottom)
			ws.write_merge(4,5,13,13, "Amount\nFOB(US$)",hdr_style_border_top_bottom)
			ws.write_merge(4,5,14,14, "Commision\nFOB(US$)",hdr_style_border_top_bottom)
			ws.write_merge(4,5,15,15, " ",hdr_style_border_top_bottom)
			rowcount=6

			max_width_col = {0:12,1:8,2:12,3:12,4:8,5:14,6:20,7:20,8:10,9:20,10:5,11:10,12:10,13:10,14:10,15:4}
			total_inv = 0.0
			total_comm_amt = 0.0
			total_freight = 0.0
			total_insurance = 0.0
			total_fob = 0.0
			total_comm_amt_fob = 0.0
			# group by agent
			result_grouped2 = {}
			for line in sorted(result_grouped1[key2],key=lambda l:(l['inv_date'],l['inv_no'])):
				ws.write(rowcount,0,line['inv_no'],normal_style)
				ws.write(rowcount,1,line['inv_date'] and parser.formatLang(line['inv_date'],date=True),normal_style)
				ws.write(rowcount,2,line['lc_batch'],normal_style)
				ws.write(rowcount,3,line['sj_no'],normal_style)
				ws.write(rowcount,4,line['sj_date'] and parser.formatLang(line['sj_date'],date=True) or '',normal_style)
				ws.write(rowcount,5,line['contract'],normal_style)
				ws.write(rowcount,6,(line['party'] and len(line['party'])>max_width_col[6] and line['party'][:20] or line['party']),normal_style)
				ws.write(rowcount,7,(line['prod_name'] and len(line['prod_name'])>max_width_col[7] and line['prod_name'][:20] or line['prod_name']),normal_style)
				ws.write(rowcount,8,line['price_subtotal'],normal_right_style1)
				ws.write(rowcount,9,(line['agent_name'] and len(line['agent_name'])>max_width_col[9] and line['agent_name'][:20] or line['agent_name']),normal_style)
				ws.write(rowcount,10,line['comm_percent'],normal_right_style15)
				ws.write(rowcount,11,line['comm_amt'],normal_right_style1)
				ws.write(rowcount,12,line['freight'],normal_right_style1)
				# ws.write(rowcount,13,line['insurance'],normal_right_style1)
				ws.write(rowcount,13,line['fob'],normal_right_style1)
				ws.write(rowcount,14,line['comm_amt_fob'],normal_right_style1)
				ws.write(rowcount,15,line['incoterm'],normal_style)
				
				total_inv+=(line['price_subtotal'] or 0.0)
				total_comm_amt+=(line['comm_amt'] or 0.0)
				total_freight+=(line['freight'] or 0.0)
				total_insurance+=(line['insurance'] or 0.0)
				total_fob+=(line['fob'] or 0.0)
				total_comm_amt_fob+=(line['comm_amt_fob'] or 0.0)
				rowcount+=1

				key3 = line['agent_name']
				if key3 not in result_grouped2:
					result_grouped2.update({key3:
						{'comm':0.0,'comm_fob':0.0}
						})
				result_grouped2.update({
					key3:{
					'comm':result_grouped2[key3]['comm']+(line['comm_amt'] or 0.0),
					'comm_fob':result_grouped2[key3]['comm_fob']+(line['comm_amt_fob'] or 0.0)
					}
				})

			ws.write_merge(rowcount,rowcount,0,7, "Total", subtotal_label_style)
			ws.write(rowcount,8,total_inv,subtotal_style1)
			if total_inv and len(str(total_inv))>max_width_col[8]:
				max_width_col[8]=len(str(total_inv))
			ws.write_merge(rowcount,rowcount,9,10, "", subtotal_style)
			ws.write(rowcount,11,total_comm_amt,subtotal_style1)
			if total_comm_amt and len(str(total_comm_amt))>max_width_col[11]:
				max_width_col[11]=len(str(total_comm_amt))
			ws.write(rowcount,12,total_freight,subtotal_style1)
			if total_freight and len(str(total_freight))>max_width_col[12]:
				max_width_col[12]=len(str(total_freight))
			# ws.write(rowcount,13,total_insurance,subtotal_style1)
			ws.write(rowcount,13,total_fob,subtotal_style1)
			if total_fob and len(str(total_fob))>max_width_col[13]:
				max_width_col[13]=len(str(total_fob))
			ws.write(rowcount,14,total_comm_amt_fob,subtotal_style1)
			if total_comm_amt_fob and len(str(total_comm_amt_fob))>max_width_col[14]:
				max_width_col[14]=len(str(total_comm_amt_fob))
			ws.write(rowcount,15,"",subtotal_style)
			rowcount+=1

			for c in range(0,16):
				ws.col(c).width = 256*int(max_width_col[c]*1.4)

			rowcount+=2
			ws.write(rowcount,0,"Prepared By : ")
			ws.write(rowcount,3,"Checked By : ")
			ws.write(rowcount,6,"Approved By : ")

			rowcount+=2
			ws.write_merge(rowcount,rowcount+1,9,10,"",hdr_style_border_bottom)
			ws.write_merge(rowcount,rowcount+1,11,11,"Commision\n",hdr_style_border_bottom)
			ws.write_merge(rowcount,rowcount+1,12,12,"Commision\nFOB",hdr_style_border_bottom)
			rowcount+=2
			total_comm_amt2 = 0.0
			total_comm_amt_fob2 = 0.0
			for key4 in sorted(result_grouped2.keys()):
				if key4 in ('',False):
					continue
				ws.write_merge(rowcount,rowcount,9,10,key4,normal_style)
				ws.write(rowcount,11,result_grouped2[key4]['comm'],normal_right_style1)
				ws.write(rowcount,12,result_grouped2[key4]['comm_fob'],normal_right_style1)
				total_comm_amt2+=result_grouped2[key4]['comm']
				total_comm_amt_fob2+=result_grouped2[key4]['comm_fob']
				rowcount+=1
			ws.write_merge(rowcount,rowcount,9,10, "Total", subtotal_style)
			ws.write(rowcount,11,total_comm_amt2,subtotal_style1)
			ws.write(rowcount,12,total_comm_amt_fob2,subtotal_style1)
			rowcount+=1
		pass

commision_detail_xls('report.commision.detail.report','commision.detail.wizard','addons/ad_sales_report/report/pending_sales_report.mako', parser=commision_detail_parser, header=False)