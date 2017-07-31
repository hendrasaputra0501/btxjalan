import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from report_engine_xls import report_xls
import os


import cStringIO
from xlwt import Workbook, Formula
# import xlrd
from tools.translate import _


from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter
from datetime import datetime


class sca_print_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		print
		super(sca_print_parser, self).__init__(cr, uid, name, context=context)		
		self.localcontext.update({
			'time' : time,
			'get_object' : self.get_object,
			# 'group_lines' : self.group_lines,
		})
	
	def get_object(self,data):
		return self.pool.get('purchase.requisition').browse(self.cr,self.uid,data['ids'])

	def get_price_usd(self,pr_line_obj):
		if pr_line_obj:
			currency_pool = self.pool.get("res.currency")
			company_curr = pr_line_obj.last_order_id and pr_line_obj.last_order_id.company_id and pr_line_obj.last_order_id.company_id.currency_id.id
			po_curr= pr_line_obj.last_order_id and pr_line_obj.last_order_id.currency_id and pr_line_obj.last_order_id.currency_id.id or False
			print "============",po_curr
			usd_amt = 0.0
			if po_curr:
				usd_amt=currency_pool.compute(self.cr,self.uid,po_curr,company_curr, (pr_line_obj.last_price or 0.0),context={'date':pr_line_obj.last_order_id.date_order})
		return usd_amt


	def get_last_mrr_date(self,po_id):
		if po_id:
			mrr_ids = self.pool.get("stock.picking").search(self.cr,self.uid,[('purchase_id','=',po_id.id),('state','=','done')],order="date_done desc")
			if mrr_ids:
				try:
					mrr = self.pool.get("stock.picking").browse(self.cr,self.uid,mrr_ids[0])
				except:
					mrr = self.pool.get("stock.picking").browse(self.cr,self.uid,mrr_ids)
				return mrr.date_done
		return False

	# def get_purc_ids(self,purc_ids):
	# 	if purc_ids:
	# 		for purc_line in purc_ids:
	# 			rfq_number=purc_line.name2
	# 			term_condition=purc_line.template_special_condition

	def get_current_rfq(self,sca_ids,product_id):
		if sca_ids and product_id:
			currency_pool = self.pool.get("res.currency")
			dict_data = {}
			for sca in sca_ids:
				if sca.product_id and sca.product_id.id==product_id:
					order_id = sca.po_line_id.order_id or sca.po_line_id.old_order_id
					po_curr = order_id.currency_id.id
					company_curr = order_id.company_id.currency_id.id
					usd_amt = currency_pool.compute(self.cr,self.uid,po_curr,company_curr,sca.po_line_id.price_subtotal,context={'date':order_id.date_order})
					price_unit_usd = currency_pool.compute(self.cr,self.uid,po_curr,company_curr,sca.po_line_id.price_subtotal/sca.po_line_id.product_qty,context={'date':order_id.date_order})
					dict_data.update({
						sca.partner_id.name:{
							'rfq_number':sca.po_line_id and order_id and order_id.name2 or "",
							'rfq_date':sca.po_line_id and order_id and order_id.date_order or "", 
							'price_unit':sca.po_line_id and sca.po_line_id.price_subtotal/sca.po_line_id.product_qty or "", 
							'price_unit_usd':sca.po_line_id and order_id and order_id.currency_id and sca.po_line_id.price_unit and price_unit_usd or "", 
							'currency_id':sca.po_line_id and order_id and order_id.currency_id and order_id.currency_id.name or "",
							'amt':sca.po_line_id.price_subtotal or "",
							'usd_amt':sca.po_line_id and order_id and order_id.currency_id and sca.po_line_id.price_subtotal and usd_amt or "",
							'incoterm':sca.po_line_id and order_id and order_id.incoterm and order_id.incoterm.code or order_id.incoterm.name or "",							
							}
						})
				else:
					continue
			return dict_data

			"""{
				'SUPPLIER NAME A':{
								'rfq_number':RFQ NUMBER or "",
								'rfq_date':RFQ DATE or "", 
								'price_unit':SUBTOTAL or "", 
								'currency_id':CURRENCY or "",
								'usd_amt':USD AMT or "",
								'incoterm': INCOTERM
								},
				'SUPPLIER NAME B':{
								'rfq_number':RFQ NUMBER or "",
								'rfq_date':RFQ DATE or "", 
								'price_unit':SUBTOTAL or "", 
								'currency_id':CURRENCY or "",
								'usd_amt':USD AMT or "",
								'incoterm': INCOTERM
								}
			}"""
		return {}

class sca_analysis(report_xls):
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

		data.update({
			'ids':ids,
			"context":
			context
			})
		rml_parser.set_context(objs, data, ids, 'xls')
		n = cStringIO.StringIO()
		wb = xlwt.Workbook(encoding='utf-8')
		self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
		wb.save(n)
		
		n.seek(0)
		return (n.read(), 'xls')

	



	def generate_xls_report(self, parser, data, obj, wb):
		c = parser.localcontext['company']
		title_style = xlwt.easyxf('font: height 220, name Monospace, colour_index black; align: wrap on, vert centre, horiz left; ')
		title_style_bold = xlwt.easyxf('font: height 220, name Monospace, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
		title_style_bold_border = xlwt.easyxf('font: height 220, name Monospace, colour_index black, bold on; align: wrap on, vert centre, horiz center;borders: bottom thin,top thin; ')
		title_style_bold_border_all= xlwt.easyxf('font: height 220, name Monospace, colour_index black, bold on; align: wrap on, vert centre, horiz center;borders: bottom thin,top thin,left thin; ')
		title_style_bold_left = xlwt.easyxf('font: height 220, name Monospace, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_style_float_bold = xlwt.easyxf('font: height 180, name Monospace, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz left;')
		normal_style_vtop = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert top, horiz left;')
		normal_style_bold = xlwt.easyxf('font: height 180, name Monospace, colour_index black,bold on; align: wrap on, vert centre, horiz left;')
		normal_style_border_left = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz left;borders: left thin;')
		normal_style_border = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz centre;borders: bottom thin,top thin;')
		normal_style_border_bottom_left = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz left;borders: bottom thin,left thin;')
		normal_style_border_bottom = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz left;borders: bottom thin;')
		normal_style_float_border_bottom = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz right;borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_border_bottom_top = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz right;borders: bottom thin,top thin;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_border_bottom_center_left=xlwt.easyxf('font: height 180, name Monospacse, colour_index black; align: wrap on, vert centre, horiz center;borders: bottom thin,left thin;')
		normal_style_border_right=xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz right;borders:left thin;')
		normal_style_border_top = xlwt.easyxf('font: height 180, name Monospace, colour_index black; align: wrap on, vert centre, horiz centre;borders: top thin;')
		rowcount = 0
		print "xxxxxxxxxxxxxxxxx",c
		parser.lang = c.partner_id.lang
		objects = parser.get_object(data)
		for o in objects:
			ws = wb.add_sheet('SCA',cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1
			ws.preview_magn = 58.0
			ws.normal_magn = 58.0
			ws.print_scaling= 58.0
			ws.page_preview = False
			ws.set_fit_width_to_pages(1)
			ws.top_margin = 0.6
			ws.bottom_margin = 0.6
			ws.left_margin = 0.6
			ws.right_margin = 0.6
			ws.fit_num_pages = 1
			ws.write_merge(rowcount,rowcount,0,15, "Supplier Comparison Approval", title_style_bold)
			
			rowcount+=1
			ws.write(rowcount,0,"PR No.",normal_style_float_bold)
			ws.write_merge(rowcount,rowcount,1,2,o.name or "-",title_style)
			ws.write_merge(rowcount,rowcount,3,4,"PR Date :",normal_style_float_bold)
			ws.write_merge(rowcount,rowcount,5,6,parser.formatLang(o.date_end,date=True) or "-",title_style)
			ws.write_merge(rowcount,rowcount,7,8,"Responsible :",normal_style_float_bold)
			ws.write_merge(rowcount,rowcount,9,10,o.user_id.name or "-",title_style)
			ws.write_merge(rowcount,rowcount,12,13,"Assigned Buyer :",normal_style_float_bold)
			ws.write_merge(rowcount,rowcount,14,15,o.assigned_employee.name or "-",title_style)
			ws.write_merge(3,3,0,6,"LAST PO INFORMATION",title_style_bold)
			ws.write_merge(3,3,7,12,"CURRENT RFQS",title_style_bold_left)

			ws.write_merge(4,5,0,0,"PRODUK",title_style_bold_border)
			ws.write_merge(4,5,1,1,"LAST PO",title_style_bold_border)
			ws.write_merge(4,5,2,2,"VENDOR",title_style_bold_border)
			ws.write_merge(4,5,3,3,"DATE",title_style_bold_border)
			ws.write_merge(4,5,4,4,"PRICE",title_style_bold_border)
			ws.write_merge(4,5,5,5,"CCY",title_style_bold_border)
			ws.write_merge(4,5,6,6,"USD PRICE",title_style_bold_border)
			# ws.write_merge(4,5,7,7,"LEAD TIME (DAYS)",title_style_bold_border)
			# ws.write(4,8,"PRODUK",title_style_bold_border)
			# ws.write(4,9,"REQ. NO.",title_style_bold_border)
			# ws.write(4,10,"REQ. DATE",title_style_bold_border)
			# ws.write(4,11,"PRICE",title_style_bold_border)
			# ws.write(4,12,"CCY",title_style_bold_border)
			# ws.write(4,13,"USD PRICE",title_style_bold_border)
			# ws.write(4,14,"INCOTERM",title_style_bold_border)
			# ws.write(4,15,"NOTES",title_style_bold_border)

			start_check = 4
			
			# ws.col(0).width = len("ABCDEFGHIJKLMN")*400
			# ws.col(1).width = (ws.col(0).width)-1500
			# ws.col(2).width = (ws.col(0).width)*2
			# ws.col(3).width = (ws.col(0).width)-1500
			# ws.col(4).width = (ws.col(0).width)-1000
			# ws.col(5).width = 4000
			# ws.col(6).width = (ws.col(0).width)-1500
			# ws.col(7).width = (ws.col(0).width)-3000
			# ws.col(8).width = (ws.col(0).width)
			# ws.col(9).width = (ws.col(0).width)
			# ws.col(10).width = (ws.col(0).width)-1000
			# ws.col(11).width = 4000
			# ws.col(12).width = (ws.col(0).width)-1500
			# ws.col(13).width = (ws.col(0).width)-1500
			# ws.col(14).width = (ws.col(0).width)
			# ws.col(15).width = (ws.col(0).width)-1000

			width={
			0: len("Produk")*500,
			1: len("LAST PO")*500,
			2: len("VENDOR")*1000,
			3: len("date")*900,
			4: len("PRICE")*500,
			5: len("CCY")*500,
			6: len("USD PRICE")*300,
			# 7: len("LEAD TIME (DAYS)"),
			# 8: len("PRODUK/VENDOR"),
			# 9: len("REQ. NO."),
			# 10: len("REQ. DATE"),
			# 11: len("PRICE"),
			# 12: len("CCY"),
			# 13: len("USD PRICE"),
			# 14: len("INCOTERM"),
			# 15: len("NOTES"),
			}
			ws.col(0).width=width[0]
			ws.col(1).width=width[1]
			ws.col(2).width=width[2]
			ws.col(3).width=width[3]
			ws.col(4).width=width[4]
			ws.col(5).width=width[5]
			ws.col(6).width=width[6]
			write = False
			rowcount=4
			for line in o.line_ids:
				first_pos =rowcount
				dict_data=parser.get_current_rfq(o.sca_ids,line.product_id.id)
				colcount =7
				for partner in sorted(dict_data.keys()):
					ws.write_merge(rowcount,rowcount,colcount,colcount+1,partner,title_style_bold_border_all)
					ws.write(rowcount+1,colcount,dict_data[partner]['currency_id'],normal_style_border_bottom_center_left)
					ws.write(rowcount+1,colcount+1,"USD AMT",normal_style_border_bottom_center_left)
					colcount+=2
				rowcount+=2
				# last_ord_date=line and datetime.strptime(line.last_date_order,"%Y-%m-%d")#last PO date
				# lead_time='-'
				# try:
				# 	last_date_mrr = datetime.strptime(parser.get_last_mrr_date(line.last_order_id),"%Y-%m-%d %H:%M:%S") #last Mrr date
				# except:
				# 	last_date_mrr =  False
				# if last_date_mrr:
				# 	lead_time=last_date_mrr-last_ord_date
				# 	lead_time=lead_time.days
				# else:
				# 	lead_time="-"
				price_usd=parser.get_price_usd(line)
				w={}
				w[0]=line and line.product_id and line.product_id.name_template or '-'
				w[1]=line and line.last_order_id and line.last_order_id.name or '-'
				w[2]=line and line.last_partner_id and line.last_partner_id.name or '-'
				w[3]=line and line.last_date_order or '-'
				w[4]=line and line.last_price or '-'
				w[5]=line and line.last_order_id and line.last_order_id.currency_id and line.last_order_id.currency_id.name or '-'
				w[6]=price_usd
				# w[7]=lead_time
				ws.write(rowcount,0,w[0],normal_style)
				ws.write(rowcount,1,w[1],normal_style)
				ws.write(rowcount,2,w[2],normal_style)
				ws.write(rowcount,3,w[3],normal_style)
				ws.write(rowcount,4,w[4],normal_style)
				ws.write(rowcount,5,w[5],normal_style)
				ws.write(rowcount,6,w[6],normal_style)
				# ws.write(rowcount,7,w[7],normal_style)
				colcount =7
				for partner in sorted(dict_data.keys()):
					ws.write(rowcount,colcount,dict_data[partner]['price_unit'] or 0.0,normal_style_border_right)
					ws.write(rowcount,colcount+1,dict_data[partner]['price_unit_usd'] or 0.0,normal_style_border_right)
					colcount+=2
				rowcount+=1
			first_pos = rowcount
			colcount =7
			first_col=colcount
			# end_check = rowcount
			# ws.write(first_pos,0,"",normal_style)
			# first_pos+=1
			ws.write_merge(first_pos+1,first_pos+1,first_col-4,first_col-1,"Term & Condition OF RFQS",normal_style_bold)
			first_pos+=1
			height={}
			if o.purchase_ids:
				for purch_line in o.purchase_ids:
					rfq_number_inpo=purch_line.name2
					term_condition=purch_line.notes and purch_line.notes.strip() or ''
					# partner=purch_line.partner_id.partner_alias or purch_line.partner_id.name or ''
					ws.write_merge(first_pos,first_pos,first_col,first_col+1,rfq_number_inpo,normal_style_vtop)
					# ws.write(first_pos,1,partner,normal_style_vtop)
					ws.write_merge(first_pos+1,first_pos+1,first_col,first_col+1,term_condition,normal_style)
					height[first_pos+1]=term_condition.count('\n')
					first_col+=2
			# # for col in range(0,15):
			# # 	ws.col(col).width=width.get(col,1)*400
			for row in height:
				ws.row(row).height_mismatch = True
				ws.row(row).height=height[row]*500
			n_partner = len(o.purchase_ids)
			ws.write_merge(first_pos+2,first_pos+2,0,6+2*n_partner,"",normal_style_border_top)
			first_pos+=3
			ws.write(first_pos,0,"Remarks :",normal_style_bold)
			ws.write_merge(first_pos+1,first_pos+1,0,5,o.description or '',normal_style)
			first_pos+=4
		ws.write(first_pos,1,"Prepared By",normal_style_border_top)
		ws.write(first_pos,3,"MMD",normal_style_border_top)
		ws.write(first_pos,5,"AK Ladha",normal_style_border_top)
		ws.write(first_pos,7,"D Singh",normal_style_border_top)
		ws.write(first_pos,9,"PD",normal_style_border_top)

sca_analysis('report.sca.analysis.xls', 'purchase.requisition', 'addons/ad_material_requisition/report/sca_analysis.mako', parser=sca_print_parser) 
