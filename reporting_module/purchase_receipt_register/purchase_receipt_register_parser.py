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

class PurchaseReceiptRegister (report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(PurchaseReceiptRegister, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_objects' : self._get_object,       
			"get_difference": self._get_difference,
			"get_result":self._get_result,
			"get_price_usd":self._get_price_usd,
			"get_price_unit":self._get_price_unit,
			"get_price_subtotal_po":self._get_price_subtotal_po,
			"convert_to_company_currency":self._convert_to_company_currency,
		})

	def _get_price_usd(self, cury_po,company_curyid,date_order,price_unit):
		curr_obj = self.pool.get("res.currency")
		usd_amt = 0.0
		
		cury_idco = company_curyid
		cury_id_po=cury_po
		ctx={'date':date_order!='False' and date_order or time.strftime('%Y-%m-%d')}
		usd_amt = curr_obj.compute(self.cr, self.uid, cury_id_po, cury_idco, (price_unit or 0.0), context=ctx)
		
		return usd_amt

	def _get_object(self,data):
		# obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
		date_start = data['form']['start_date']
		date_end = data['form']['end_date']

		self.cr.execute("SELECT sm.id, rp.name FROM stock_move sm \
			LEFT JOIN stock_picking sp ON sp.id=sm.picking_id \
			LEFT JOIN res_partner rp ON sp.partner_id=rp.id \
			WHERE  \
			sp.state='done' and sp.type='in' and sp.purchase_id is not NULL \
			and ((to_char(sm.date,'YYYY-MM-DD')>='"+date_start+"' and to_char(sm.date,'YYYY-MM-DD')<='"+date_end+"') \
			or (to_char(sp.date_done,'YYYY-MM-DD')>='"+date_start+"' and to_char(sp.date_done,'YYYY-MM-DD')<='"+date_end+"'))\
			order by rp.name,sm.date")
		queries = self.cr.fetchall()
		move_ids = [x[0] for x in queries]
		partner_ids = list(set([x[1] for x in queries]))
		result = {}
		for partner in partner_ids:
			result.update({partner:[]})
		if move_ids:
			obj_data=self.pool.get('stock.move').browse(self.cr,self.uid,move_ids)
			for obj in obj_data:
				if obj.picking_id and obj.picking_id.partner_id:
					res = result.get(obj.picking_id.partner_id.name,[])
					res.append(obj)
					result.update({obj.picking_id.partner_id.name:res})
			return result
		return {}

	def _get_result(self, data):
		date_start = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['start_date']
		date_end = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['end_date']
		purchase_type = data['form']['purchase_type']
		goods_type = data['form']['goods_type']
		foc = data['form']['foc']
		mrr_without_invoice = data['form']['mrr_pending_ap_voucher']
		if foc:
			foc=" AND b.purchase_id is NULL AND b.invoice_id is NULL AND a.invoice_line_id is NULL"
		else:
			foc=" AND (c.purchase_type in %s or b.purchase_type in %s)"
		if mrr_without_invoice:
			add_query = " AND (b.invoice_state<>'none' and (b.invoice_id is NULL or j.move_id is NULL)) "
		else:
			add_query = ""
		if purchase_type =='all':
			purchase_type ="('local','import')"
		else:
			purchase_type = "('%s')" %purchase_type
		force_picking_conditions = ""
		if data['form']['force_picking_ids']:
			force_picking_conditions = " AND b.id IN ("+','.join([str(x) for x in data['form']['force_picking_ids']])+")"
		query = "\
			SELECT \
				coalesce(discount.discount_amt, 0)/100 as discount,\
				a.id as sm_id, \
				b.id as mrr_id, \
				b.name as mrr_no, \
				to_char(b.date_done,'DD/MM/YY') as mrr_date, \
				to_char(b.date_done,'YYYY-MM-DD') as mrr_date2, \
				c.name as po_no, \
				to_char(c.date_order,'DD/MM/YY') as po_date, \
				coalesce(d.id,dd.id) as party_id, \
				coalesce(d.partner_code,dd.partner_code) as party_code, \
				coalesce(d.name,dd.name) as party_name, \
				e.name as transport, \
				b.supplier_delicery_slip as sj_no, \
				to_char(b.date_delivery_slip,'DD/MM/YY') as sj_date, \
				f.default_code as prod_code, \
				i.name as prod_name, \
				(case b.type when 'in' then a.product_uop_qty else -1*a.product_uop_qty end) as qty2, \
				m.name as uom_name, \
				n.name as lot_number, \
				coalesce(a.net_weight,0) as nw, \
				a.moisturity as mois, (case b.type when 'in' then a.product_qty else -1*a.product_qty end) as qty1, \
				h.name as curr_name, a.price_unit as cost, \
				coalesce(o.price_unit,a.price_unit) as po_price_unit,\
				round(((case b.type when 'in' then a.product_qty else -1*a.product_qty end)*a.price_unit),2) as eq_usd,\
				j.reference as inv_ref, \
				coalesce(k.price_unit,0) as inv_cost, \
				j.number as inv_number, \
				b.contract_purchase_number as contract, \
				to_char(j.date_due,'DD/MM/YY') as dd_payment, \
				l.name as loc_name, \
				coalesce(l.alias,l.name) as loc_alias, \
				string_agg(p.mr_name,',') as ir_number, \
				coalesce(o.part_number,'') as part_number,\
				h.id as curry_idpo,\
				q.currency_id as company_curyid,\
				c.date_order as date_order, \
				case when l.usage='internal' then \
					'in'\
					else 'out' end as ptype \
			FROM \
				stock_move a\
				INNER JOIN stock_picking b ON b.id=a.picking_id \
				LEFT JOIN purchase_order c ON c.id=b.purchase_id \
				LEFT JOIN res_partner d ON d.id=b.partner_id \
				LEFT JOIN res_partner dd ON dd.id=c.partner_id \
				LEFT JOIN stock_transporter e ON e.id=b.trucking_company \
				LEFT JOIN product_product f ON f.id=a.product_id \
				LEFT JOIN product_pricelist g ON g.id=c.pricelist_id \
				LEFT JOIN res_currency h ON h.id=g.currency_id \
				LEFT JOIN product_template i ON i.id=f.product_tmpl_id \
				LEFT JOIN account_invoice j ON j.id=b.invoice_id \
				LEFT JOIN account_invoice_line k ON k.id=a.invoice_line_id \
				LEFT JOIN stock_location l ON l.id=a.location_dest_id \
				LEFT JOIN product_uom m ON m.id=a.product_uom\
				LEFT JOIN stock_tracking n ON n.id=a.tracking_id\
				LEFT JOIN purchase_order_line o ON o.id=a.purchase_line_id and o.order_id=c.id \
				LEFT JOIN res_company q on q.id=b.company_id\
				LEFT JOIN (\
					SELECT DISTINCT \
						mr.name as mr_name, mrl.product_id, po.id as order_id \
					FROM \
						material_request_line mrl \
						INNER JOIN material_request mr ON mr.id=mrl.requisition_id \
						INNER JOIN purchase_requisition pr ON pr.id=mrl.pr_id\
						INNER JOIN purchase_order po ON po.requisition_id=pr.id\
					) p ON p.order_id=c.id AND p.product_id=o.product_id\
				LEFT JOIN (\
				select discount_amt,po_line_id from price_discount_po_line_rel prdis left join price_discount pd on prdis.disc_id=pd.id)discount on o.id=discount.po_line_id\
				LEFT JOIN account_move am on am.id=j.move_id\
			WHERE \
				a.state='done' AND b.type in ('in','out') \
				AND (c.goods_type='%s' or b.goods_type='%s') \
				AND (b.date_done::date>='%s' and b.date_done::date<='%s')\
				"+force_picking_conditions+" \
				"+foc+" \
				"+add_query+" \
			GROUP BY a.id, round(((case b.type when 'in' then a.product_qty else -1*a.product_qty end)*a.price_unit),2), a.price_unit, a.product_qty, b.id, b.name, to_char(b.date_done,'DD/MM/YY'),to_char(b.date_done,'YYYY-MM-DD'), \
			c.name,to_char(c.date_order,'DD/MM/YY'),coalesce(d.id,dd.id),coalesce(d.partner_code,dd.partner_code),coalesce(d.name,dd.name),e.name,b.supplier_delicery_slip,to_char(b.date_delivery_slip,'DD/MM/YY'),\
			f.default_code,i.name,a.product_uop_qty,m.name,n.name,coalesce(a.net_weight,0),a.moisturity,h.name,po_price_unit,j.reference,coalesce(k.price_unit,0),\
			j.number,b.contract_purchase_number,to_char(j.date_due,'DD/MM/YY'),l.name,coalesce(l.alias,l.name), coalesce(o.part_number,''),discount.discount_amt,h.id,\
			q.currency_id,c.date_order,l.usage \
			ORDER BY b.id\
			"
		print "::::::::::::::::", query
		if data['form']['foc']:
			query = query%(goods_type,goods_type,date_start,date_end)
		else:
			query = query%(goods_type,goods_type,date_start,date_end,purchase_type,purchase_type)

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _get_price_unit(self, move_id):
		cr = self.cr
		uid = self.uid
		move = self.pool.get('stock.move').browse(cr, uid, move_id)
		if move.purchase_line_id:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in move.purchase_line_id.discount_ids],move.purchase_line_id.price_unit,move.purchase_line_id.product_qty)
			price_after = disc.get('price_after',move.purchase_line_id.price_unit)
		else:
			price_after = move.price_unit
		return price_after

	def _get_price_subtotal_po(self, move_id):
		tax_obj = self.pool.get('account.tax')
		cr = self.cr
		uid = self.uid
		move = self.pool.get('stock.move').browse(cr, uid, move_id)
		if move.purchase_line_id:
			purchase_line = move.purchase_line_id
			price_subtotal = tax_obj.compute_all(cr, uid, purchase_line.taxes_id, self._get_price_unit(move_id), move.product_qty, product=move.product_id, partner=purchase_line.order_id.partner_id)['total']
		else:
			price_subtotal = move.price_unit*move.product_qty
		return price_subtotal

	def _convert_to_company_currency(self, from_curr, amount, date):
		curr_obj = self.pool.get('res.currency')
		cr = self.cr
		uid = self.uid
		company_curr = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
		res = curr_obj.compute(cr, uid, from_curr, company_curr, amount, round=False, context={'date':date!='False' and date or time.strftime('%Y-%m-%d')})
		return res

	def _get_difference(self,date_start,date_end):
		if date_start and date_end:
			try:
				date_start=datetime.strptime(date_start,'%Y-%m-%d')
			except:
				date_start=datetime.strptime(date_start,'%Y-%m-%d %H:%M:%S')
			try:
				date_end=datetime.strptime(date_end,'%Y-%m-%d')
			except:
				date_end=datetime.strptime(date_end,'%Y-%m-%d %H:%M:%S')
			date_difference=date_end-date_start
			return date_difference.days>0 and date_difference.days or ''
		return ""
report_sxw.report_sxw('report.purchase.receipt.register.report','purchase.receipt.register.wizard', 'addons/reporting_module/purchase_receipt_register/purchase_receipt_register.mako', parser=PurchaseReceiptRegister)




class purchase_receipt_register_wizard_xls(report_xls):
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
		ws = wb.add_sheet('Purchase Receipt Register',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 60
		ws.normal_magn = 60
		ws.print_scaling=60

		title_style                     = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		th_top_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed')
		th_both_style                   = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style                 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom dashed')
		
		normal_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float              = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round        = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold         = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style               = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b             = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style            = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; borders: bottom thin;')
		subtotal_style                  = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre; borders: top thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2                 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: top thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap off, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		add_info = data['form']['with_invoice_information'] or data['form']['mrr_pending_ap_voucher']
		date_start = data['form']['start_date']
		date_end = data['form']['end_date']
		rm_goods_type = data['form']['goods_type']=='raw'
		if data['form']['foc']:
			foc_text=" ( FOC )"
		else:
			foc_text=""
		# if rm_goods_type:
		ws.write_merge(0,0,0, add_info and 28 or 20, c.name, title_style)
		ws.write_merge(1,1,0, add_info and 28 or 20, "PURCHASE RECEIPT RECORD"+foc_text , title_style)
		if data['form']['filter_date']=='as_of':
			ws.write_merge(2,2,0, add_info and 28 or 20, "As Of "+datetime.strptime(data['form']['as_of_date'],"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)
		else:
			ws.write_merge(2,2,0, add_info and 28 or 20, "FROM "+datetime.strptime(date_start,"%Y-%m-%d").strftime("%d/%m/%Y")+" TO "+datetime.strptime(date_end,"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)

		ws.write_merge(4,4,0,2, "RECEIPT", th_top_style)
		ws.write(5,0, "NO.", th_bottom_style)
		ws.write(5,1, "DATE", th_bottom_style)
		ws.write(5,2, "BATCH", th_bottom_style)
		ws.write_merge(4,4,3,4, "PO", th_top_style)
		ws.write(5,3, "NO.", th_bottom_style)
		ws.write(5,4, "DATE", th_bottom_style)
		ws.write_merge(4,5,5,5, "VENDOR\nNAME", th_both_style)
		ws.write_merge(4,4,6,8, "Surat Jalan", th_top_style)
		ws.write(5,6, "TRANSPORT", th_bottom_style)
		ws.write(5,7, "NO.", th_bottom_style)
		ws.write(5,8, "DATE", th_bottom_style)
		ws.write_merge(4,4,9,11, "INVENTORY", th_top_style)
		ws.write(5,9, "ID", th_bottom_style)
		ws.write(5,10, "DESCRIPT", th_bottom_style)
		ws.write(5,11, "UNIT", th_both_style)
		if not data['form']['foc']:
			ws.write_merge(4,4,12,19, "RECEIPT", th_top_style)
			ws.write(5,12, "BALES", th_bottom_style)
			ws.write(5,13, "NET WT Kg", th_bottom_style)
			ws.write(5,14, "%", th_bottom_style)
			ws.write(5,15, "COMP WT.Kg", th_bottom_style)
			ws.write(5,16, "USD", th_bottom_style)
			ws.write(5,17, "AMOUNT", th_bottom_style)
			ws.write(5,18, "UNIT COST", th_bottom_style)
			ws.write(5,19, "EQ.USD", th_bottom_style)
			ws.write_merge(4,5,20,20, "REMARK", th_both_style)
			if add_info:
				ws.write_merge(4,4,21,28, "INVOICE RECEIPT", th_top_style)
				ws.write(5,21, "INV. NO.", th_bottom_style)
				ws.write(5,22, "COST", th_bottom_style)
				ws.write(5,23, "PAYMENT", th_bottom_style)
				ws.write(5,24, "VOUCHER", th_bottom_style)
				ws.write(5,25, "CONTRACT", th_bottom_style)
				ws.write(5,26, "BANK", th_bottom_style)
				ws.write(5,27, "DD OF PAY", th_bottom_style)
				ws.write(5,28, "DIFF RATE", th_bottom_style)
		else :
			ws.write_merge(4,4,12,18, "RECEIPT", th_top_style)
			# ws.write(5,12, "BALES", th_bottom_style)
			ws.write(5,12, "NET WT Kg", th_bottom_style)
			ws.write(5,13, "%", th_bottom_style)
			ws.write(5,14, "COMP WT.Kg", th_bottom_style)
			ws.write(5,15, "USD", th_bottom_style)
			ws.write(5,16, "AMOUNT", th_bottom_style)
			ws.write(5,17, "UNIT COST", th_bottom_style)
			ws.write(5,18, "EQ.USD", th_bottom_style)
			ws.write_merge(4,5,19,19, "REMARK", th_both_style)
			if add_info:
				ws.write_merge(4,4,20,27, "INVOICE RECEIPT", th_top_style)
				ws.write(5,20, "INV. NO.", th_bottom_style)
				ws.write(5,21, "COST", th_bottom_style)
				ws.write(5,22, "PAYMENT", th_bottom_style)
				ws.write(5,23, "VOUCHER", th_bottom_style)
				ws.write(5,24, "CONTRACT", th_bottom_style)
				ws.write(5,25, "BANK", th_bottom_style)
				ws.write(5,26, "DD OF PAY", th_bottom_style)
				ws.write(5,27, "DIFF RATE", th_bottom_style)
		
		result = parser._get_result(data)

		result_grouped={}
		for name in result :
			key = rm_goods_type and data['form']['header_group_by']=='vendor_wise' and (name['party_name'],name['party_code']) or (data['form']['header_group_by']=='date_wise' and name['mrr_date2'] or ("All","All"))
			if key not in result_grouped:
				result_grouped.update({key:[]})
			result_grouped[key].append(name)

		max_width_col_0 = 0
		max_width_col_2 = len("Total Vendor")
		max_width_col_3 = 0
		max_width_col_5 = 0
		max_width_col_6 = 0
		max_width_col_7 = 0
		max_width_col_9 = 0
		max_width_col_10 = 0
		max_width_col_13 = len('NET WT Kg')

		max_width_col_15 = len('COMP WT.Kg')
		max_width_col_21 = len('INV. NO.')
		max_width_col_24 = len('VOUCHER')
		max_width_col_25 = len('CONTRACT')
		#foc
		max_width_col_20 = len('INV. NO.')
		max_width_col_23 = len('VOUCHER')
		max_width_col_24 = len('CONTRACT')
		rowcount=6
		total1, total2, total3, total4, total5 = 0.0,0.0,0.0,0.0,0.0
		for name in sorted(result_grouped.keys(),key = lambda x: (rm_goods_type and data['form']['header_group_by']=='vendor_wise' and x[1] or x)):
			st=0.0
			st1=0.0
			st2=0.0
			st3=0.0
			st4=0.0
			for o in sorted(result_grouped[name], key = lambda x : (x['mrr_date2'],x['mrr_no'])):      
				
				qty1 = o['qty1']
				qty2 = o['ptype']=='in' and o['qty2'] or -1*o['qty2']
				nw = o['ptype']=='in' and o['nw'] or -1*o['nw']
				po_price_subtotal = parser._get_price_subtotal_po(o['sm_id'])
				cost = o['cost']


				ws.write(rowcount,0,o['mrr_no'],normal_style)
				if len(o['mrr_no'] and o['mrr_no'] or '')>max_width_col_0:
					max_width_col_0=len(o['mrr_no'])
				ws.write(rowcount,1,o['mrr_date'],normal_style)
				ws.write(rowcount,2,'',normal_style)
				ws.write(rowcount,3,o['po_no'],normal_style)
				if len(o['po_no'] and o['po_no'] or '')>max_width_col_3:
					max_width_col_3=len(o['po_no'])
				ws.write(rowcount,4,o['po_date'],normal_style)
				ws.write(rowcount,5,o['party_name'],normal_style)
				if len(o['party_name'] and o['party_name'] or '')>max_width_col_5:
					max_width_col_5=len(o['party_name'])
				ws.write(rowcount,6,o['transport'],normal_style)
				if len(o['transport'] and o['transport'] or '')>max_width_col_6:
					max_width_col_6=len(o['transport'])
				ws.write(rowcount,7,o['sj_no'],normal_style)
				if len(o['sj_no'] and o['sj_no'] or '')>max_width_col_7:
					max_width_col_7=len(o['sj_no'])
				ws.write(rowcount,8,o['sj_date'],normal_style)
				ws.write(rowcount,9,o['prod_code'],normal_style)
				if len(o['prod_code'] and o['prod_code'] or '')>max_width_col_9:
					max_width_col_9=len(o['prod_code'])
				ws.write(rowcount,10,o['prod_name'],normal_style)
				if len(o['prod_name'] and o['prod_name'] or '')>max_width_col_10:
					max_width_col_10=len(o['prod_name'])
				ws.write(rowcount,11,'',normal_style)
				if not data['form']['foc']:
					ws.write(rowcount,12,qty2,normal_style_float)
					ws.write(rowcount,13,nw,normal_style_float)
					ws.write(rowcount,14,o['mois'],normal_style_float)
					ws.write(rowcount,15,qty1,normal_style_float)
					ws.write(rowcount,16,o['curr_name'],normal_style)
					ws.write(rowcount,17,po_price_subtotal,normal_style_float)
					ws.write(rowcount,18,cost,normal_style_float)
					# eq_usd = parser._convert_to_company_currency(o['curry_idpo'],po_price_subtotal,o['mrr_date2'])
					# eq_usd = round(cost * qty1,2)
					eq_usd = o['eq_usd']
					ws.write(rowcount,19,eq_usd,normal_style_float)
					ws.write(rowcount,20,'',normal_style)
					if add_info:
						ws.write(rowcount,21,o['inv_ref'],normal_style)
						if len(o['inv_ref'] and o['inv_ref'] or '')>max_width_col_21:
							max_width_col_21=len(o['inv_ref'])
						ws.write(rowcount,22,o['ptype']=='in' and o['inv_cost'] or -1*o['inv_cost'],normal_style)
						ws.write(rowcount,23,o['inv_cost']*qty1,normal_style)
						ws.write(rowcount,24,o['inv_number'],normal_style)
						if len(o['inv_number'] and o['inv_number'] or '')>max_width_col_24:
							max_width_col_24=len(o['inv_number'])
						ws.write(rowcount,25,o['contract'],normal_style)
						if len(o['contract'] and o['contract'] or '')>max_width_col_25:
							max_width_col_25=len(o['contract'])
						ws.write(rowcount,26,'',normal_style)
						ws.write(rowcount,27,o['dd_payment'],normal_style)
						ws.write(rowcount,28,(o['inv_cost'] and (o['ptype']=='in' and (o['inv_cost']-o['po_price_unit']) or o['ptype']=='out' and -1*(o['inv_cost']-o['po_price_unit'])) or 0.0),normal_style)
				else :
					ws.write(rowcount,12,nw,normal_style_float)
					ws.write(rowcount,13,o['mois'],normal_style_float)
					ws.write(rowcount,14,qty1,normal_style_float)
					ws.write(rowcount,15,o['curr_name'],normal_style)
					ws.write(rowcount,16,po_price_subtotal,normal_style_float)
					ws.write(rowcount,17,cost,normal_style_float)
					# eq_usd = parser._convert_to_company_currency(o['curry_idpo'],po_price_subtotal,o['mrr_date2'])
					# eq_usd = round(cost * qty1,2)
					eq_usd = o['eq_usd']
					ws.write(rowcount,18,eq_usd,normal_style_float)
					ws.write(rowcount,19,'',normal_style)
					if add_info:
						ws.write(rowcount,20,o['inv_ref'],normal_style)
						if len(o['inv_ref'] and o['inv_ref'] or '')>max_width_col_20:
							max_width_col_20=len(o['inv_ref'])
						ws.write(rowcount,21,o['ptype']=='in' and o['inv_cost'] or -1*o['inv_cost'],normal_style)
						ws.write(rowcount,22,o['inv_cost']*qty1,normal_style)
						ws.write(rowcount,23,o['inv_number'],normal_style)
						if len(o['inv_number'] and o['inv_number'] or '')>max_width_col_23:
							max_width_col_23=len(o['inv_number'])
						ws.write(rowcount,24,o['contract'],normal_style)
						if len(o['contract'] and o['contract'] or '')>max_width_col_24:
							max_width_col_24=len(o['contract'])
						ws.write(rowcount,25,'',normal_style)
						ws.write(rowcount,26,o['dd_payment'],normal_style)
						ws.write(rowcount,27,(o['inv_cost'] and (o['ptype']=='in' and (o['inv_cost']-o['po_price_unit']) or o['ptype']=='out' and -1*(o['inv_cost']-o['po_price_unit'])) or 0.0),normal_style)

				st=st+qty2
				st1=st1+nw
				st2=st2+qty1
				st3=st3+po_price_subtotal
				st4=st4+eq_usd
				rowcount+=1
			if rm_goods_type and data['form']['header_group_by']=='vendor_wise':
				ws.write(rowcount,2, "Total Vendor", subtotal_style)
				ws.write(rowcount,3, name[1], subtotal_style)
				if not data['form']['foc']:
					ws.write(rowcount,12,st,subtotal_style2)
					ws.write(rowcount,13,st1,subtotal_style2)
					ws.write(rowcount,14," ",subtotal_style)
					ws.write(rowcount,15,st2,subtotal_style2)
					ws.write(rowcount,16," ",subtotal_style)
					ws.write(rowcount,17," ",subtotal_style)
					ws.write(rowcount,18," ",subtotal_style)
					ws.write(rowcount,19,st4,subtotal_style2)
					ws.write(rowcount,20," ",subtotal_style)

					rowcount+=1
				else :
					# ws.write(rowcount,12,st,subtotal_style2)
					ws.write(rowcount,12,st1,subtotal_style2)
					ws.write(rowcount,13," ",subtotal_style)
					ws.write(rowcount,14,st2,subtotal_style2)
					ws.write(rowcount,15," ",subtotal_style)
					ws.write(rowcount,16," ",subtotal_style)
					ws.write(rowcount,17," ",subtotal_style)
					ws.write(rowcount,18,st4,subtotal_style2)
					ws.write(rowcount,19," ",subtotal_style)

					rowcount+=1
			elif data['form']['header_group_by']=='date_wise':
				ws.write_merge(rowcount,rowcount,2,11, "Total Receipt ON "+parser.formatLang(name,date=True), subtotal_style)
				if not data['form']['foc']:
					ws.write(rowcount,12,st,subtotal_style2)
					ws.write(rowcount,13,st1,subtotal_style2)
					ws.write(rowcount,14," ",subtotal_style)
					ws.write(rowcount,15,st2,subtotal_style2)
					ws.write(rowcount,16," ",subtotal_style)
					ws.write(rowcount,17,st3,subtotal_style2)
					ws.write(rowcount,18," ",subtotal_style)
					ws.write(rowcount,19,st4,subtotal_style2)
					ws.write(rowcount,20," ",subtotal_style)
					rowcount+=1
				else :
					# ws.write(rowcount,12,st,subtotal_style2)
					ws.write(rowcount,12,st1,subtotal_style2)
					ws.write(rowcount,13," ",subtotal_style)
					ws.write(rowcount,14,st2,subtotal_style2)
					ws.write(rowcount,15," ",subtotal_style)
					ws.write(rowcount,16,st3,subtotal_style2)
					ws.write(rowcount,17," ",subtotal_style)
					ws.write(rowcount,18,st4,subtotal_style2)
					ws.write(rowcount,19," ",subtotal_style)
					rowcount+=1

			total1+=st
			total2+=st1
			total3+=st2
			total4+=st3
			total5+=st4

		ws.write_merge(rowcount,rowcount,0,11, "Grand Total", total_style)
		if not data['form']['foc']:
			ws.write(rowcount,12,total1,total_style2)
			ws.write(rowcount,13,total2,total_style2)
			ws.write(rowcount,14," ",total_style)
			ws.write(rowcount,15,total3,total_style2)
			ws.write(rowcount,16," ",total_style)
			ws.write(rowcount,17,total4,total_style2)
			ws.write(rowcount,18," ",total_style)
			ws.write(rowcount,19,total5,total_style2)
			ws.write(rowcount,20," ",total_style)
			rowcount+=1
		else :
			# ws.write(rowcount,12,total1,total_style2)
			ws.write(rowcount,12,total2,total_style2)
			ws.write(rowcount,13," ",total_style)
			ws.write(rowcount,14,total3,total_style2)
			ws.write(rowcount,15," ",total_style)
			ws.write(rowcount,16,total4,total_style2)
			ws.write(rowcount,17," ",total_style)
			ws.write(rowcount,18,total5,total_style2)
			ws.write(rowcount,19," ",total_style)
			rowcount+=1

		ws.col(0).width = 256 * int(max_width_col_0*1.4)
		ws.col(2).width = 256 * int(max_width_col_2*1.4)
		ws.col(3).width = 256 * int(max_width_col_3*1.4)
		ws.col(5).width = 256 * int(max_width_col_5*1.4)
		ws.col(6).width = 256 * int(max_width_col_6*1.4)
		ws.col(7).width = 256 * int(max_width_col_7*1.4)
		ws.col(9).width = 256 * int(max_width_col_9*1.4)
		ws.col(10).width = 256 * int(max_width_col_10*1.4)
		ws.col(13).width = 256 * int(max_width_col_13*1.4)
		ws.col(15).width = 256 * int(max_width_col_15*1.4)
		ws.col(21).width = 256 * int(max_width_col_21*1.4)
		ws.col(24).width = 256 * int(max_width_col_24*1.4)
		ws.col(25).width = 256 * int(max_width_col_25*1.4)
		

		pass

#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
purchase_receipt_register_wizard_xls('report.xls.purchase.receipt.register.report','purchase.receipt.register.wizard', 'addons/reporting_module/purchase_receipt_register/purchase_receipt_register.mako',
						parser=PurchaseReceiptRegister)




