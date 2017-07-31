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


class PendingPurchaseOrderRegister(report_sxw.rml_parse):
	def __init__(self,cr,uid,name,context=None):
		super(PendingPurchaseOrderRegister,self).__init__(cr,uid,name,context=context)
		self.localcontext.update({
			'time' : time,
			'get_result':self._get_result,
			'get_itemrequest': self._get_itemrequest,
			'get_itemreceived': self._get_itemreceived,
			'get_itemrejected': self._get_itemrejected,
			'get_itemcanceled': self._get_itemcanceled,
			'get_advanced': self._get_advanced,
			'get_price_subtotal_usd': self._get_price_subtotal_usd,
			'convert_to_company_currency': self._convert_to_company_currency,
			})

	def _get_object(self,data):
		date_start =data['form']['date_start']
		date_stop =data['form']['date_stop']
		self.cr.execute("SELECT * FROM get_purchase_line('"+date_start+"','"+date_stop+"')dummy")
		result=self.cr.fetchall()
		line_ids=[x[0] for x in result]
		return self.pool.get('purchase.order.line').browse(self.cr, self.uid, line_ids)


	def _convert_to_company_currency(self, from_curr, amount, date):
		curr_obj = self.pool.get('res.currency')
		cr = self.cr
		uid = self.uid
		company_curr = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
		res = curr_obj.compute(cr, uid, from_curr, company_curr, amount, round=False, context={'date':date!='False' and date or time.strftime('%Y-%m-%d')})
		return res

	def _get_advanced(self,id_po):
		cr=self.cr
		uid=self.uid
		context=None
		# print id_po,"mmmmmmmmmmmmmmmmmmmmmmmmmm"
		adv_amount=0.00
		date_pay=''
		advance_obj=self.pool.get('purchase.order').browse(cr,uid,id_po,context=context)
		# print id_po,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		if advance_obj.advance_ids:
			# print id_po,"gggggggggggggggggggggg"
			# adv_amount=0.00
			# print advance_obj.date_payment,"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
			for line in advance_obj.advance_ids:
				adv_amount+=line.total_amount
				date_pay=line.date_payment
		return adv_amount,date_pay


	def _get_itemcanceled(self,id_po,id_product,date_start,date_stop):
		cr=self.cr
		uid=self.uid
		context=None
		qty_tot=0.00
		incoming_obj=self.pool.get('stock.picking')
		incoming_cancel_ids=incoming_obj.search(cr,uid,[('purchase_id','=',id_po),('state','=','cancel'),('type','=','in'),('date_done','<=',date_stop)])
		if incoming_cancel_ids:
			for picking_line in incoming_cancel_ids:
				incoming_cancel_detail_obj=self.pool.get('stock.move')
				incoming_cancel_detail_ids=incoming_cancel_detail_obj.search(cr,uid,[('picking_id','=',picking_line),('product_id','=',id_product)])
				for move_line in incoming_cancel_detail_ids:
					qty_canceled=self.pool.get('stock.move').browse(cr,uid,move_line,context=context).product_qty
					qty_tot+=qty_canceled
		return qty_tot


	def _get_itemrejected(self,id_po,id_product,date_start,date_stop):
		cr=self.cr
		uid=self.uid
		context=None
		qty_tot=0.00
		incoming_obj=self.pool.get('stock.picking')
		incoming_reject_ids=incoming_obj.search(cr,uid,[('purchase_id','=',id_po),('state','in',('done','approved')),('type','=','out'),('date_done','<=',date_stop)])
		if incoming_reject_ids:
			for picking_line in incoming_reject_ids:
				incoming_reject_detail_obj=self.pool.get('stock.move')
				incoming_reject_detail_ids=incoming_reject_detail_obj.search(cr,uid,[('picking_id','=',picking_line),('product_id','=',id_product)])
				for move_line in incoming_reject_detail_ids:
					qty_rejected=self.pool.get('stock.move').browse(cr,uid,move_line,context=context).product_qty
					qty_tot+=qty_rejected
		return qty_tot

	def _get_itemreceived(self,id_po,id_product,date_start,date_stop):
		cr=self.cr
		uid=self.uid
		context=None
		qty_tot=0.00
		incoming_obj=self.pool.get('stock.picking')
		# incoming_ids=incoming_obj.search(cr,uid,[('purchase_id','=',id_po),('state','in',('done','approved')),('type','=','in'),('date_done','>=',date_start),('date_done','<=',date_stop)])
		incoming_ids=incoming_obj.search(cr,uid,[('purchase_id','=',id_po),('state','in',('done','approved')),('type','=','in'),('date_done','<=',date_stop)])
		if incoming_ids:
			for picking_line in incoming_ids:
				# print picking_line,"mamamamamamamamamama"
				incoming_detail_obj=self.pool.get('stock.move')
				incoming_detail_ids=incoming_detail_obj.search(cr,uid,[('picking_id','=',picking_line),('product_id','=',id_product)])
				for move_line in incoming_detail_ids:
					qty_received=self.pool.get('stock.move').browse(cr,uid,move_line,context=context).product_qty
					qty_tot+=qty_received
		return qty_tot

	def _get_price_subtotal_usd(self,id_pol,id_po,id_product):
		cr=self.cr
		uid=self.uid
		context=None
		price_subtotal_usd=0.00
		purchase_line_obj=self.pool.get('purchase.order.line')
		purchase_line_ids=purchase_line_obj.search(cr,uid,[('id','=',id_pol),('order_id','=',id_po),('product_id','=',id_product)])
		# purchase_req_obj=purchase_req_line.browse(cr,uid,reqid_line,context=context)[0]
		if purchase_line_ids:
			for line in purchase_line_ids:
				currency_id=purchase_line_obj.browse(cr,uid,line,context=context).order_id.pricelist_id.currency_id.id
				# currency_id=purchase_line_obj.search(cr,uid,[('order_id','=',id_po),('product_id','=',id_product)]).order_id.pricelist_id.currency_id.id
				# print currency_id,"xxxxxxxxxxxxxxxxxxxxxxxxxx"
				subtotal=purchase_line_obj.browse(cr,uid,line,context=context).price_subtotal
				# print subtotal,"lalalalalalalalala"
				date_order=purchase_line_obj.browse(cr,uid,line,context=context).order_id.date_order
				# print date_order,"ajajajajajajajajajajaja"
			price_subtotal_usd=self._convert_to_company_currency(currency_id,subtotal,date_order)
		# print price_subtotal_usd,"dadadadadadadadadadadadadada"
		return price_subtotal_usd
		

	def _get_itemrequest(self,id_po):
		cr=self.cr
		uid=self.uid
		context=None
		matreq_name=""
		purchase_order_reqid=self.pool.get('purchase.order').browse(cr,uid,id_po,context=context).requisition_id
		purchase_req_line=self.pool.get('purchase.requisition.line')
		# print purchase_order_reqid.id,"cccccccccccccccccccccccccccccccccccccccccc"

		if purchase_order_reqid:
			reqid_line=purchase_req_line.search(cr,uid,[('requisition_id','=',purchase_order_reqid.id)])
			# print reqid_line,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
			# matreq_name=[]
			purchase_req_obj=purchase_req_line.browse(cr,uid,reqid_line,context=context)[0]
			# print purchase_req_obj.id,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
			if purchase_req_obj.material_req_line_id.id:
				matreq_lineid=purchase_req_obj.material_req_line_id.id
				# print matreq_lineid,"qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
				material_line_obj=self.pool.get('material.request.line')
				material_line_id=material_line_obj.search(cr,uid,[('id','=',matreq_lineid)])
				if material_line_id:
					matreq_line=material_line_obj.browse(cr,uid,material_line_id,context=context)
					for line in matreq_line:
						matreq_id=line.requisition_id.id
						# print matreq_id,"qhqhqhqhqqhhqhqhqhqhqhqhqhqhqhqhqhqhqhq"
						matreq_obj=self.pool.get('material.request')
						matreq_name=matreq_obj.browse(cr,uid,matreq_id,context=context).name
						# print matreq_name,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
		return matreq_name


	def _get_result(self,data):
		# date_start =data['form']['date_start']
		date_start =data['form']['date_start']
		date_stop =data['form']['date_stop']
		output_type =data['form']['output_type']
		purchase_type =data['form']['purchase_type']
		goods_type=data['form']['goods_type']
		if purchase_type =='all':
			purchase_type ="('local','import')"
		else:
			purchase_type = "('%s')" %purchase_type
		if goods_type =='all':
			goods_type ="('packing','raw','stores')"
		else:
			goods_type = "('%s')" %goods_type
		# print purchase_type,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

		query="select \
					po.id as id_po,\
					pol.id as id_pol,\
					po.name as po_number,\
					po.date_order as date_order,\
					po.goods_type as goods_type,\
					rp.partner_code as partner_code,\
					rp.name as vendor,\
					pp.name_template as description,\
					pp.default_code as code_product,\
					pp.id as id_product,\
					pu.name as uom,\
					pol.product_qty, \
					rc.name as currency,\
					pol.price_unit as price\
					\
				from purchase_order_line pol \
					inner join purchase_order po on pol.order_id=po.id \
					left outer join res_partner rp on po.partner_id=rp.id \
					left outer join product_product pp on pol.product_id=pp.id \
					left outer join product_uom pu on pol.product_uom=pu.id \
					left outer join product_pricelist ppl on po.pricelist_id=ppl.id\
					left outer join res_currency rc on ppl.currency_id=rc.id\
					\
				where po.state in('done','approved') and po.goods_type in %s and po.purchase_type in %s \
				and to_char(po.date_order,'YYYY-MM-DD') >= substring('%s',1,10) and to_char(po.date_order,'YYYY-MM-DD') <= substring('%s',1,10) \
				and ((pol.knock_off is null or pol.knock_off='f') and (to_char(pol.date_knock_off,'YYYY-MM-DD')<=substring('%s',1,10)or to_char(pol.date_knock_off,'YYYY-MM-DD') is null))\
				and pol.other_cost_type is null and po.knock_off_picking='f'\
			"
		query = query%(goods_type,purchase_type,date_start,date_stop,date_stop)

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		#res2 = sorted(res, key=lambda k: k[11])
		res1=sorted(res,key=lambda m:m['date_order'])
		res2=sorted(res1,key=lambda l:l['description'])
		res3=sorted(res2, key=lambda k:k['vendor'])
		return res3

# report_sxw.report_sxw('report.pending.shipment.register.report','pending.shipment.register.wizard', 'addons/ad_purchases_report/pending_shipment_register_report.mako', parser=PendingShipmentRegister)
report_sxw.report_sxw('report.pending.purchase.order.report','pending.purchase.order.wizard', 'addons/ad_purchases_report/pending_purchase_order_report.mako',parser=PendingPurchaseOrderRegister)

class pending_purchase_order_wizard_xls(report_xls):
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
		ws = wb.add_sheet('Pending Purchase Order',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 60
		ws.normal_magn = 60
		ws.print_scaling=60
		ws.page_preview = False
		ws.set_fit_width_to_pages(1)
		pending_purchase_data = parser._get_result(data)

		title_style  = xlwt.easyxf('font: height 280, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
		normal_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz center ;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_bold_border_top = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center;border:top thick;' ,num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_bold_border_bottom = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center;border:bottom thick;' ,num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b = xlwt.easyxf('font: height 200, name Calibri, colour_index white, bold on;pattern: pattern solid, pattern_back_colour black; align: wrap on, vert centre, horiz right; ')
		th_top_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
		th_both_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
		th_bottom_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')

		date_start = data['form']['date_start']
		date_stop = data['form']['date_stop']

		ws.write_merge(0,0,0,18, "PT. BITRATEX INDUSTRIES", title_style)
		ws.write_merge(1,1,0,18, "PENDING PURCHASE ORDER", title_style)
		ws.write_merge(2,2,0,18, "BETWEEN "+datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") + " and " +datetime.strptime(date_stop,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"), title_style)
		
		ws.write_merge(3,3,0,1, "PO", normal_style_float_bold_border_top)
		ws.write(4,0, "Nbr.", normal_style_float_bold_border_bottom)
		ws.write(4,1, "Date", normal_style_float_bold_border_bottom)

		ws.write_merge(3,3,2,3, "Vendor", normal_style_float_bold_border_top)
		ws.write(4,2, "Code", normal_style_float_bold_border_bottom)
		ws.write(4,3, "Name", normal_style_float_bold_border_bottom)

		ws.write_merge(3,3,4,5, "Inventory", normal_style_float_bold_border_top)
		ws.write(4,4, "Code Inv", normal_style_float_bold_border_bottom)
		ws.write(4,5, "Description", normal_style_float_bold_border_bottom)

		ws.write(3,6, "Item Req.", normal_style_float_bold_border_top)
		ws.write(4,6, "Nbr", normal_style_float_bold_border_bottom)
		
		ws.write(3,7, "Department", normal_style_float_bold_border_top)
		ws.write(4,7, "User", normal_style_float_bold_border_bottom)

		ws.write_merge(3,3,8,13, "Quantity", normal_style_float_bold_border_top)
		ws.write(4,8, "UOM", normal_style_float_bold_border_bottom)
		ws.write(4,9, "Order", normal_style_float_bold_border_bottom)
		ws.write(4,10, "Canceled", normal_style_float_bold_border_bottom)
		ws.write(4,11, "Received", normal_style_float_bold_border_bottom)
		ws.write(4,12, "Rejected", normal_style_float_bold_border_bottom)
		ws.write(4,13, "Remaining", normal_style_float_bold_border_bottom)

		ws.write(3,14, " ", normal_style_float_bold_border_top)
		ws.write(4,14, "Cury", normal_style_float_bold_border_bottom)

		ws.write_merge(3,3,15,16, "Remaining", normal_style_float_bold_border_top)
		ws.write(4,15, "Value", normal_style_float_bold_border_bottom)

		# ws.write(3,16, "Remaining", normal_style_float_bold_border_top)
		ws.write(4,16, "Value USD", normal_style_float_bold_border_bottom)

		ws.write_merge(3,3,17,18, "Advance", normal_style_float_bold_border_top)
		ws.write(4,17, "Value", normal_style_float_bold_border_bottom)
		ws.write(4,18, "Date", normal_style_float_bold_border_bottom)

		max_width_col_0 = len('Nbr.')
		max_width_col_1 = len('Date')
		max_width_col_2 =len('Code')
		max_width_col_3=len('Name')
		max_width_col_4=len('Code Inv')
		max_width_col_5=len('Description')
		max_width_col_6=len('Item Req.')
		max_width_col_7=len('Department')
		max_width_col_8=len('UOM')
		max_width_col_9=len('Order')
		max_width_col_10=len('Canceled')
		max_width_col_11=len('Received')
		max_width_col_12=len('Rejected')
		max_width_col_13=len('Remaining')
		max_width_col_14=len('Cury')
		max_width_col_15=len('Remaining')
		max_width_col_16=len('Remaining')
		max_width_col_17=len('Value')
		max_width_col_18=len('Date')

		rowcount=5
		for o in pending_purchase_data:
		# for o in parser._get_result(data):
			itemcanceled=parser._get_itemcanceled(o['id_po'],o['id_product'],data['form']['date_start'],data['form']['date_stop'])
			itemreceived=parser._get_itemreceived(o['id_po'],o['id_product'],data['form']['date_start'],data['form']['date_stop'])
			itemrejected=parser._get_itemrejected(o['id_po'],o['id_product'],data['form']['date_start'],data['form']['date_stop'])			
			itemremaining=(o['product_qty']-itemreceived)+itemrejected
			price_subtotal_usd=parser._get_price_subtotal_usd(o['id_pol'],o['id_po'],o['id_product'])
			if itemremaining>0:
				ws.write(rowcount,0,o['po_number'],normal_style)
				if len(o['po_number'] or '')>max_width_col_0:
					max_width_col_0=len(o['po_number'])
				ws.write(rowcount,1,o['date_order'],normal_style)
				if len(o['date_order'] or '')>max_width_col_1:
					max_width_col_1=len(o['date_order'])
				ws.write(rowcount,2,o['partner_code'],normal_style)
				if len(o['partner_code'] or '')>max_width_col_2:
					max_width_col_2=len(o['partner_code'])
				ws.write(rowcount,3,o['vendor'],normal_style)
				if len(o['vendor'] or '')>max_width_col_3:
					max_width_col_3=len(o['vendor'])
				ws.write(rowcount,4,o['code_product'],normal_style)
				if len(o['code_product'] or '')>max_width_col_4:
					max_width_col_4=len(o['code_product'])
				ws.write(rowcount,5,o['description'],normal_style)
				if len(o['description'] or '')>max_width_col_5:
					max_width_col_5=len(o['description'])
				itemrequestnbr=parser._get_itemrequest(o['id_po'])
				ws.write(rowcount,6,itemrequestnbr,normal_style)
				if len(itemrequestnbr or '')>max_width_col_6:
					max_width_col_6=len(itemrequestnbr)
				ws.write(rowcount,7,o['goods_type'],normal_style)
				if len(o['goods_type'] or '')>max_width_col_7:
					max_width_col_7=len(o['goods_type'])
				ws.write(rowcount,8,o['uom'],normal_style)
				if len(o['uom'] or '')>max_width_col_8:
					max_width_col_8=len(o['uom'])
				ws.write(rowcount,9,o['product_qty'],normal_style)
				
				ws.write(rowcount,10,itemcanceled,normal_style)

				ws.write(rowcount,11,itemreceived,normal_style)

				ws.write(rowcount,12,itemrejected,normal_style)

				ws.write(rowcount,13,itemremaining,normal_style)

				ws.write(rowcount,14,o['currency'],normal_style)
				if len(o['currency'] or '')>max_width_col_14:
					max_width_col_14=len(o['currency'])

				ws.write(rowcount,15,o['price']*itemremaining,normal_style)

				advance_value,advance_date=parser._get_advanced(o['id_po'])
				ws.write(rowcount,16,(price_subtotal_usd/o['product_qty'])*itemremaining,normal_style)
				ws.write(rowcount,17,advance_value,normal_style)
				ws.write(rowcount,18,advance_date,normal_style)
				# for line in o['lines']:
				# ws.write_merge(rowcount,rowcount,0,17, "", normal_style_float_bold_border_top)
				# ws.write(rowcount,19,o['price'],normal_style)
				# ws.write(rowcount,20,price_subtotal_usd,normal_style)
				rowcount+=1
		ws.write_merge(rowcount,rowcount,0,17, "", normal_style_float_bold_border_top)

		ws.col(0).width = 256 * int(max_width_col_0*1.1)
		ws.col(1).width = 256 * int(max_width_col_1*1.3)
		ws.col(2).width = 256 * int(max_width_col_2*2)
		ws.col(3).width =256 * int(max_width_col_3*1.4)
		ws.col(4).width=256 * int(max_width_col_4*1.5)
		ws.col(5).width=256 * int(max_width_col_5*1)
		ws.col(6).width=256 * int(max_width_col_6*1.6)
		ws.col(7).width=256 * int(max_width_col_7*1.5)
		ws.col(8).width=256 * int(max_width_col_8*1)
		ws.col(9).width=256 * int(max_width_col_9*2)
		ws.col(10).width=256 * int(max_width_col_10*1.5)
		ws.col(11).width=256 * int(max_width_col_11*1.5)
		ws.col(12).width=256 * int(max_width_col_12*1.5)
		ws.col(13).width=256 * int(max_width_col_13*1.5)
		ws.col(14).width=256 * int(max_width_col_14*1.5)
		ws.col(15).width=256 * int(max_width_col_15*2.4)
		ws.col(16).width=256 * int(max_width_col_16*1.5)
		ws.col(17).width=256 * int(max_width_col_17*1.5)

pending_purchase_order_wizard_xls('report.xls.pending.purchase.order.report','pending.purchase.order.wizard', 'addons/ad_purchases_report/pending_purchase_register.mako',parser=PendingPurchaseOrderRegister)