from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from tools.translate import _
import cStringIO
import netsvc
import tools
import decimal_precision as dp
import logging
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from detail_freight_cost_parser import *
from collections import OrderedDict

class detail_freight_cost_xls(report_xls):
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
		# company = parser.get_company(c)
		currencies = parser.get_currencies(data)
		for curr in currencies:
			ws = wb.add_sheet('Detail Freight Cost - %s'%(curr.name),cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1
			ws.preview_magn = 65
			ws.normal_magn = 65
			ws.print_scaling=65
			ws.page_preview = False
			ws.set_fit_width_to_pages(1)
			date_range = parser._get_date_range(data)

			title_style  = xlwt.easyxf('font: height 280, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
			normal_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_date = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='DD-MM-YYYY')
			normal_style_float = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right ;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_float_bold = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center',num_format_str='#,##0.00;-#,##0.00')
			normal_bold_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			normal_bold_style_a = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right',num_format_str='#,##0.00;-#,##0.00')
			normal_bold_style_b = xlwt.easyxf('font: height 180, name Calibri, colour_index white, bold on;pattern: pattern solid, pattern_back_colour black; align: wrap on, vert centre, horiz left; ')
			th_top_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on;align: wrap on, vert centre, horiz center; border:top thick')
			th_both_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top thick, bottom thick',num_format_str='#,##0.00;-#,##0.00')
			th_both_style_right = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right; border:top thick, bottom thick',num_format_str='#,##0.00;-#,##0.00')
			th_bottom_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:bottom thick',num_format_str='#,##0.00;-#,##0.00')


			ws.write_merge(0,0,0,18, "PT. BITRATEX INDUSTRIES", title_style)
			ws.write_merge(1,1,0,18, "DETAIL OF OCEAN FREIGHT COST", title_style)
			ws.write_merge(2,2,0,18, "%s - %s"%(date_range[0],date_range[1]),title_style)

			ws.write_merge(4,4,0,1, "Invoice", th_both_style)
			# ws.write_merge(4,5,2,2, "LC Batch No", th_both_style)
			# ws.write_merge(4,4,3,5, "Surat Jalan", th_both_style)
			# ws.write_merge(4,5,6,6, "Customer", th_both_style)
			# ws.write_merge(4,5,7,7, "Destination", th_both_style)
			# ws.write_merge(4,5,8,8, "Container", th_both_style)
			# ws.write_merge(4,5,9,9, "Shipping Agent", th_both_style)
			# ws.write_merge(4,5,10,10, "Freight US$", th_both_style)
			# ws.write_merge(4,4,11,12, "EMKL", th_both_style)
			# ws.write_merge(4,4,13,14, "Other EMKL Cost", th_both_style)
			# ws.write_merge(4,4,15,16, "Other Cost", th_both_style)
			# ws.write_merge(4,5,17,17, "Total Freight", th_both_style)
			ws.write_merge(4,4,2,4, "Surat Jalan", th_both_style)
			ws.write_merge(4,5,5,5, "Customer", th_both_style)
			ws.write_merge(4,5,6,6, "Destination", th_both_style)
			ws.write_merge(4,5,7,7, "Container", th_both_style)
			ws.write_merge(4,5,8,8, "Shipping Agent", th_both_style)
			ws.write_merge(4,5,9,9, "Freight %s(%s)"%(curr.name,curr.symbol), th_both_style)
			ws.write_merge(4,4,10,11, "EMKL", th_both_style)
			ws.write_merge(4,4,12,13, "Other EMKL Cost", th_both_style)
			ws.write_merge(4,4,14,15, "Other Cost", th_both_style)
			ws.write_merge(4,5,16,16, "Total Freight", th_both_style)
			ws.write_merge(4,5,17,17, "Total FOB\nCost", th_both_style)
			ws.write_merge(4,5,18,18, "Total EMKL US$", th_both_style)
			ws.write_merge(4,5,19,19, "Total US$", th_both_style)

			ws.write(5,0, "No.", th_bottom_style)
			ws.write(5,1, "Date", th_bottom_style)
			ws.write(5,2, "No.", th_bottom_style)
			ws.write(5,3, "Date", th_bottom_style)
			ws.write(5,4, "B/L Date", th_bottom_style)
			
			ws.write(5,10, "Agent", th_bottom_style)
			ws.write(5,11, "(Rp)", th_bottom_style)
			ws.write(5,12, "US$", th_bottom_style)
			ws.write(5,13, "(Rp)", th_bottom_style)
			ws.write(5,14, "US$", th_bottom_style)
			ws.write(5,15, "(Rp)", th_bottom_style)
			ws.write(5,16, "US$", th_bottom_style)

			
			current_row = 6
			max_width_col = {}
			max_width_col[0] = 12
			max_width_col[1] = 10
			# max_width_col[2] = 18
			max_width_col[2] = 14
			max_width_col[3] = 10
			max_width_col[4] = 10
			#max_width_col[5] = len("Customer")
			max_width_col[5] = len("Customer")
			max_width_col[6] = len("Destination")
			max_width_col[7] = len("Container")
			max_width_col[8] = len("Shipping Agent")
			max_width_col[9] = 12
			max_width_col[10] = 12
			max_width_col[11] = 12
			max_width_col[12] = 10
			max_width_col[13] = 10
			max_width_col[14] = 10
			max_width_col[15] = 5
			max_width_col[16] = 5
			max_width_col[17] = 8
			max_width_col[18] = 8
			max_width_col[19] = 8

			cols = {}
			for x in range(0,20):
				if x not in (6,7):
					cols[x]=""
				else:
					cols[x]={0:"",1:""}
			freight_cost={}
			freight_cost_2={}
			emkl_cost = {}
			other_emkl_cost = {}
			other_cost = {}
			for pick in parser._get_result(data,curr.id):
				cols[0]=pick.invoice_id and pick.invoice_id.internal_number or ""
				cols[1]=pick.invoice_id and datetime.strptime(pick.invoice_id.date_invoice,'%Y-%m-%d').strftime('%d-%m-%Y') or ""
				# cols[2]=parser.aggregate_lc(pick.lc_ids)
				cols[2]=pick.name or ""
				cols[3]=datetime.strptime(pick.date_done,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') or ""
				cols[4]=pick.invoice_id and pick.invoice_id.bl_date and datetime.strptime(pick.invoice_id.bl_date,'%Y-%m-%d').strftime('%d-%m-%Y') or ""
				cols[5]=pick.invoice_id and pick.invoice_id.partner_id and  (pick.invoice_id.partner_id.partner_alias or pick.invoice_id.partner_id.name) or ""
				cols[6][0]=pick.forwading_charge and pick.forwading_charge.port_id and pick.forwading_charge.port_id.name or ""
				cols[6][1]=pick.forwading_charge and pick.forwading_charge.country_id and pick.forwading_charge.country_id.code or ""
				cols[7][0]=pick.container_number or ""
				cols[7][1]=pick.container_size and pick.container_size.type and pick.container_size.type.name or ""
				cols[8]=pick.forwading and pick.forwading.name or ""
				cols[9]=parser._get_freight_from_invoice(pick,curr.id) + parser._get_fob_from_invoice(pick,curr.id)
				cols[99]=parser._get_freight_from_invoice(pick,pick.company_id.currency_id.id)
				cols[10]=pick.trucking_company and pick.trucking_company.partner_id.name or ""
				cols[11]=pick.trucking_charge and pick.trucking_charge.cost or ""
				cols[12]=pick.lifton_bpa_id and parser._get_lifton_bpa(pick,pick.company_id.currency_id.id) or 0.0
				cols[13]=pick.lifton_bpa_id and parser._get_lifton_bpa(pick,pick.company_id.tax_base_currency.id) or 0.0
				cols[14]=pick.invoice_id and parser._get_other_cost_from_invoice(pick,pick.company_id.currency_id.id) or 0.0
				cols[15]=pick.invoice_id and parser._get_other_cost_from_invoice(pick,pick.company_id.tax_base_currency.id)
				# fs ="K"+str(current_row+1)+"+P"+str(current_row+1)
				cols[16]=cols[99]+cols[14]+parser._convert_rate(cols[15],pick.invoice_id.date_invoice,pick)
				cols[17]=parser._get_fob_from_invoice(pick,pick.company_id.currency_id.id)
				cols[18]=parser._convert_rate(cols[11] or 0.0,pick.invoice_id.date_invoice,pick) + cols[12] + parser._convert_rate(cols[13],pick.invoice_id.date_invoice,pick)
				cols[19]=cols[16]+cols[17]+cols[18]

				if cols[9] and cols[9]!="" and cols[8] not in freight_cost.keys():
					freight_cost.update({cols[8]:cols[9]})
					freight_cost_2.update({cols[8]:cols[99]})
				elif cols[9] and cols[9]!="" and cols[8] in freight_cost.keys():
					freight_cost.update({cols[8]:freight_cost[cols[8]]+cols[9]})
					freight_cost_2.update({cols[8]:freight_cost_2[cols[8]]+cols[99]})

				if cols[11] and cols[11]!="" and cols[10] not in emkl_cost.keys():
					emkl_cost.update({cols[10]:cols[11]})
				elif cols[11] and cols[11]!="" and cols[10] in emkl_cost.keys():
					emkl_cost.update({cols[10]:emkl_cost[cols[10]]+cols[11]})

				if ((cols[12] and cols[12]!="") or (cols[13] and cols[13]!="")) and cols[10] not in other_emkl_cost.keys():
					other_emkl_cost.update({cols[10]:[cols[12],cols[13]]})
				elif ((cols[12] and cols[12]!="") or (cols[13] and cols[13]!="")) and cols[10] in other_emkl_cost.keys():
					other_emkl_cost.update({
						cols[10]:[other_emkl_cost[cols[10]][0]+cols[12],other_emkl_cost[cols[10]][1]+cols[13]]
						})

				if ((cols[14] and cols[14]!="") or (cols[15] and cols[15]!="")) and cols[8] not in other_cost.keys():
					other_cost.update({cols[8]:[cols[14],cols[15]]})
				elif ((cols[14] and cols[14]!="") or (cols[15] and cols[15]!="")) and cols[8] in other_cost.keys():
					other_cost.update({
						cols[8]:[other_cost[cols[8]][0]+cols[14],other_cost[cols[8]][1]+cols[15]]
						})

				for y in range(0,19):
					if y not in (6,7):
						if len(str(cols[y]).strip())>max_width_col[y]:
							max_width_col[y]=int(len(str(cols[y]).strip()))
					else:
						if ( max_width_col[y] < (3 + len(str(cols[y][0]).strip()) + len(str(cols[y][1]).strip()) ) ):
							max_width_col[y]=int(3+len(str(cols[y][0]).strip())+len(str(cols[y][1]).strip()))

				ws.write(current_row,0, "%s"%(cols[0]), normal_style)
				ws.write(current_row,1, "%s"%(cols[1]), normal_style_date)
				ws.write(current_row,2, "%s"%(cols[2]), normal_style)
				ws.write(current_row,3, "%s"%(cols[3]), normal_style_date)
				
				ws.write(current_row,4, "%s"%(cols[4]), normal_style_date)
				ws.write(current_row,5, "%s"%(cols[5]), normal_style)
				ws.write(current_row,6, "%s - %s"%(cols[6][0],cols[6][1]), normal_style)
				ws.write(current_row,7, "%s - %s"%(cols[7][0],cols[7][1]), normal_style)
				ws.write(current_row,8, "%s"%(cols[8]), normal_style)
				ws.write(current_row,9, (cols[9]), normal_style_float)
				ws.write(current_row,10, "%s"%(cols[10]), normal_style)
				ws.write(current_row,11, (cols[11]), normal_style_float)
				ws.write(current_row,12, (cols[12]), normal_style_float)
				ws.write(current_row,13, (cols[13]), normal_style_float)
				ws.write(current_row,14, (cols[14]), normal_style_float)
				ws.write(current_row,15, (cols[15]), normal_style_float)
				ws.write(current_row,16, cols[16], normal_style_float)
				ws.write(current_row,17, cols[17], normal_style_float)
				ws.write(current_row,18, cols[18], normal_style_float)
				ws.write(current_row,19, cols[19], normal_style_float)
				current_row +=1
			ws.write(current_row,0, "Total", th_both_style_right)
			ws.write_merge(current_row,current_row,1,8, "", th_both_style_right)
			ws.write(current_row,9, xlwt.Formula("SUM($J$6:$J$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,10, "", th_both_style_right)
			ws.write(current_row,11, xlwt.Formula("SUM($L$6:$L$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,12, xlwt.Formula("SUM($M$6:$M$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,13, xlwt.Formula("SUM($N$6:$N$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,14, xlwt.Formula("SUM($O$6:$O$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,15, xlwt.Formula("SUM($P$6:$P$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,16, xlwt.Formula("SUM($Q$6:$Q$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,17, xlwt.Formula("SUM($R$6:$R$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,18, xlwt.Formula("SUM($S$6:$S$"+str(current_row)+")"), th_both_style_right)
			ws.write(current_row,19, xlwt.Formula("SUM($T$6:$T$"+str(current_row)+")"), th_both_style_right)
			current_row += 1
			
			current_row+=1
			ws.write_merge(current_row,current_row,0,2,"Prepared By: ",normal_style)
			ws.write_merge(current_row,current_row,4,6,"Checked By: ",normal_style)
			ws.write_merge(current_row,current_row,8,11,"Approved By: ",normal_style)
			current_row+=2

			ws.write_merge(current_row,current_row,0,3,"Freight Cost",normal_bold_style_a)
			ws.write_merge(current_row,current_row,5,6,"EMKL Cost",normal_bold_style_a)
			ws.write_merge(current_row,current_row,8,11,"Other EMKL Cost",normal_bold_style_a)
			ws.write_merge(current_row,current_row,13,16,"Other Cost",normal_bold_style_a)
			current_row+=1
			ws.write(current_row,10, "( US $ )", normal_bold_style)
			ws.write(current_row,11, "( Rp )", normal_bold_style)
			ws.write(current_row,15, "( US $ )", normal_bold_style)
			ws.write(current_row,16, "( Rp )", normal_bold_style)
			current_row+=1
			restart_row=current_row
			totalfr = 0.0
			totalfr2 = 0.0
			for fr in OrderedDict(sorted(freight_cost.items(), key=lambda t: t[0])).keys():	
				ws.write_merge(current_row,current_row,0,2,fr,normal_style)
				ws.write(current_row,3, freight_cost[fr], normal_style_float)
				totalfr+=freight_cost[fr]
				current_row+=1
			ws.write_merge(current_row,current_row,0,2,"Total",th_both_style_right)
			ws.write(current_row,3, totalfr, th_both_style_right)
			current_row+=2

			# if curr.id!=c.currency_id.id:
			# 	for fr2 in OrderedDict(sorted(freight_cost_2.items(), key=lambda t: t[0])).keys():	
			# 		ws.write_merge(current_row,current_row,0,2,fr,normal_style)
			# 		ws.write(current_row,3, freight_cost_2[fr2], normal_style_float)
			# 		totalfr2+=freight_cost_2[fr2]
			# 		current_row+=1
			# 	ws.write_merge(current_row,current_row,0,2,"Total",th_both_style_right)
			# 	ws.write(current_row,3, totalfr2, th_both_style_right)

			current_row=restart_row
			totalemkl=0.0
			for emk in OrderedDict(sorted(emkl_cost.items(), key=lambda t: t[0])).keys():
				ws.write_merge(current_row,current_row,5,5,emk,normal_style)
				ws.write(current_row,6, emkl_cost[emk], normal_style_float)
				totalemkl+=emkl_cost[emk]
				current_row+=1
			ws.write_merge(current_row,current_row,5,5,"Total",th_both_style_right)
			ws.write(current_row,6, totalemkl, th_both_style_right)
			
			current_row=restart_row
			totaloemkl0=0.0
			totaloemkl1=0.0
			for oemk in OrderedDict(sorted(other_emkl_cost.items(), key=lambda t: t[0])).keys():
				ws.write_merge(current_row,current_row,8,9,oemk,normal_style)
				ws.write(current_row,10, other_emkl_cost[oemk][0], normal_style_float)
				ws.write(current_row,11, other_emkl_cost[oemk][1], normal_style_float)
				totaloemkl0+=other_emkl_cost[oemk][0]
				totaloemkl1+=other_emkl_cost[oemk][1]
				current_row+=1
			ws.write_merge(current_row,current_row,8,9,"Total",th_both_style_right)
			ws.write(current_row,10, totaloemkl0, th_both_style_right)
			ws.write(current_row,11, totaloemkl1, th_both_style_right)

			current_row=restart_row
			totalocost0=0.0
			totalocost1=0.0
			for ocost in OrderedDict(sorted(other_cost.items(), key=lambda t: t[0])).keys():
				ws.write_merge(current_row,current_row,13,14,ocost,normal_style)
				ws.write(current_row,15, other_cost[ocost][0], normal_style_float)
				ws.write(current_row,16, other_cost[ocost][1], normal_style_float)
				totalocost0+=other_cost[ocost][0]
				totalocost1+=other_cost[ocost][1]
				current_row+=1
			ws.write_merge(current_row,current_row,13,14,"Total",th_both_style_right)
			ws.write(current_row,15, totalocost0, th_both_style_right)
			ws.write(current_row,16, totalocost1, th_both_style_right)
			for n in [11,15,16]:
				max_width_col[n]=14
			 	ws.col(n).width = int(256*max_width_col[n]*1.2)

			for z in [0,2,3,7,8,9,10]:
			 	ws.col(z).width = int(256*max_width_col[z]*1.1)

			for l in [1,4,12,13,14]:
			 	ws.col(l).width = int(250*max_width_col[l]*1.1)

			for k in [5]:
			 	ws.col(k).width = int(170*max_width_col[k]*1.1)

			for m in [6]:
			 	ws.col(m).width = int(230*max_width_col[m]*1.1)
		pass

#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
detail_freight_cost_xls('report.detail.freight.cost.report','detail.freight.cost', 'addons/reporting_module/detail_freight_cost/detail_freight_cost.mako',
						parser=DetailFreightCost)




