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

class PurchaseRegisterDaily (report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(PurchaseRegisterDaily, self).__init__(cr, uid, name, context=context)
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
		
		# company_curr = rfq.company_id and rfq.company_id.currency_id.id
		# cury_idco = curr_obj.browse(self.cr,self.uid, company_curyid)
		cury_idco = company_curyid
		# po_curr = rfq.pricelist_id and rfq.pricelist_id.currency_id and rfq.pricelist_id.currency_id.id
		# cury_id_po=curr_obj.browse(self.cr,self.uid,cury_po)
		cury_id_po=cury_po
		# ctx = {'date':sca_date!='False' and sca_date or time.strftime('%Y-%m-%d')}
		ctx={'date':date_order!='False' and date_order or time.strftime('%Y-%m-%d')}
		# usd_amt = currency_pool.compute(self.cr, self.uid, po_curr, company_curr, (price_unit or 0.0), context=ctx)
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
		if purchase_type =='all':
			purchase_type ="('local','import')"
		else:
			purchase_type = "('%s')" %purchase_type
		force_picking_conditions = ""
		if data['form']['force_purchase_ids']:
			force_picking_conditions = " AND po.id IN ("+','.join([str(x) for x in data['form']['force_purchase_ids']])+")"
		query = "\
			SELECT \
			po.name as po_number, \
			po.date_order as order_date, \
			po.purchase_type as purchase_type, \
			rp.partner_code as supplier_code, \
			rp.name as supplier_name, \
			po.amount_total as amount_total, \
			pp.default_code as product_code, \
			pt.name as product_name, \
			pol.product_qty as quantity, \
			pol.price_unit as unit_price, \
			coalesce(disc.diskon,'') as discount, \
			coalesce(tax.taxes,'') as taxes, \
			coalesce(sl.alias,coalesce(sl.name,'')) as site_id \
			FROM purchase_order po \
			INNER JOIN purchase_order_line pol ON pol.order_id=po.id \
			INNER JOIN res_partner rp ON rp.id=po.partner_id \
			INNER JOIN product_product pp ON pp.id=pol.product_id \
			INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id \
			LEFT JOIN (select rel.po_line_id, string_agg(pd.discount_amt::text||(case pd.type when 'percentage' then '%%' else '' end),'+') as diskon \
			           from price_discount_po_line_rel rel \
			           inner join price_discount pd ON pd.id=rel.disc_id \
			           group by rel.po_line_id) disc ON disc.po_line_id=pol.id \
			LEFT JOIN (select rel.ord_id, string_agg(at.name,',') as taxes \
			           from purchase_order_taxe rel \
			           inner join account_tax at ON at.id=rel.tax_id \
			           group by rel.ord_id) tax ON tax.ord_id=pol.id \
			INNER JOIN (SELECT mrl.id as mr_line_id, prl.id as pr_line_id, pr.id as pr_id, mrl.product_id as prod_id, mrl.location_id as site_id \
			            FROM material_request_line mrl \
			            INNER JOIN material_request mr ON mr.id=mrl.requisition_id \
			            INNER JOIN hr_department hd ON hd.id=mr.department \
			            INNER JOIN purchase_requisition_line prl ON prl.id=mrl.pr_line_id \
			            INNER JOIN purchase_requisition pr ON pr.id=prl.requisition_id) ind ON ind.prod_id=pol.product_id and ind.pr_id=po.requisition_id \
			LEFT JOIN stock_location sl ON sl.id=ind.site_id \
			WHERE po.state in ('approved','done') \
				AND po.goods_type='%s' \
				AND po.date_order between '%s' and '%s' \
				AND po.purchase_type in %s "+force_picking_conditions+" \
			ORDER BY po.date_order, po.name"

		query = query%(goods_type,date_start,date_end,purchase_type)

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
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in move.purchase_line_id.discount_ids],move.purchase_line_id.price_unit,move.purchase_line_id.product_qty)
			price_after = disc.get('price_after',move.purchase_line_id.price_unit)
			purchase_line = move.purchase_line_id
			# price_subtotal = tax_obj.compute_all(cr, uid, purchase_line.taxes_id, purchase_line.price_unit, move.product_qty, product=move.product_id, partner=purchase_line.order_id.partner_id)['total']
			price_subtotal = tax_obj.compute_all(cr, uid, purchase_line.taxes_id, price_after, move.product_qty, product=move.product_id, partner=purchase_line.order_id.partner_id)['total']
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
report_sxw.report_sxw('report.purchase.register.daily.report','purchase.register.daily.wizard', 'addons/reporting_module/purchase_register/purchase_register_daily.mako', parser=PurchaseRegisterDaily)




class purchase_register_wizard_xls(report_xls):
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
		ws = wb.add_sheet('Purchase Register',cell_overwrite_ok=True)
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

		date_start = data['form']['start_date']
		date_end = data['form']['end_date']
		rm_goods_type = data['form']['goods_type']=='raw'
		
		# if rm_goods_type:
		ws.write_merge(0,0,0,11, c.name, title_style)
		ws.write_merge(1,1,0,11, "PURCHASE REGISTER", title_style)
		if data['form']['filter_date']=='as_of':
			ws.write_merge(2,2,0,11, "As Of "+datetime.strptime(data['form']['as_of_date'],"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)
		else:
			ws.write_merge(2,2,0,11, "FROM "+datetime.strptime(date_start,"%Y-%m-%d").strftime("%d/%m/%Y")+" TO "+datetime.strptime(date_end,"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)

		ws.write_merge(4,4,0,1, "PO", th_top_style)
		ws.write(5,0, "NO.", th_bottom_style)
		ws.write(5,1, "DATE", th_bottom_style)
		ws.write_merge(4,4,2,3, "VENDOR", th_top_style)
		ws.write(5,2, "CODE", th_bottom_style)
		ws.write(5,3, "NAME", th_bottom_style)
		ws.write_merge(4,4,4,5, "INVENTORY", th_top_style)
		ws.write(5,4, "ID", th_bottom_style)
		ws.write(5,5, "DESCRIPT", th_bottom_style)
		ws.write_merge(4,5,6,6, "QTY", th_both_style)
		ws.write_merge(4,5,7,7, "SITE ID", th_both_style)
		ws.write_merge(4,5,8,8, "UNIT\nPRICE", th_both_style)
		ws.write_merge(4,5,9,9, "AMOUNT", th_both_style)
		ws.write_merge(4,5,10,10, "DISCOUNT", th_both_style)
		ws.write_merge(4,5,11,11, "TAX", th_both_style)
		
		result = parser._get_result(data)
		result_grouped={}
		for name in result :
			#key = rm_goods_type and data['form']['header_group_by']=='vendor_wise' and (name['supplier_name'],name['supplier_code']) or (data['form']['header_group_by']=='date_wise' and name['order_date'] or ("All","All"))
			key = data['form']['header_group_by']=='vendor_wise' and (name['supplier_name'],name['supplier_code']) or (data['form']['header_group_by']=='date_wise' and name['order_date'] or ("All","All"))
			if key not in result_grouped:
				result_grouped.update({key:[]})
			result_grouped[key].append(name)

		max_width_col_0 = len('NO')
		max_width_col_1 = len('DATE')
		max_width_col_2 = len('CODE')
		max_width_col_3 = len('NAME')
		max_width_col_4 = len('ID')
		max_width_col_5 = len('DESCRIPT')
		max_width_col_6 = len('QTY')
		max_width_col_7 = len('SITE ID')
		max_width_col_8 = len('UNIT PRICE')
		max_width_col_9 = len('AMOUNT')
		max_width_col_10 = len('DISCOUNT')
		max_width_col_11 = len('TAX')

		rowcount=6
		total1, total2 = 0.0,0.0
		for name in sorted(result_grouped.keys(),key = lambda x: (rm_goods_type and data['form']['header_group_by']=='vendor_wise' and x[1] or x)):
			st=0.0
			st1=0.0

			for o in sorted(result_grouped[name], key = lambda x : (x['order_date'],x['po_number'])):       
				ws.write(rowcount,0,o['po_number'],normal_style)
				if len(o['po_number'] or '')>max_width_col_0:
					max_width_col_0=len(o['po_number'])
				ws.write(rowcount,1,o['order_date'],normal_style)
				ws.write(rowcount,2,o['supplier_code'],normal_style)
				if len(o['supplier_code'] or '')>max_width_col_2:
					max_width_col_2=len(o['supplier_code'])
				ws.write(rowcount,3,o['supplier_name'],normal_style)
				if len(o['supplier_name'] or '')>max_width_col_3:
					max_width_col_3=len(o['supplier_name'])
				ws.write(rowcount,4,o['product_code'],normal_style)
				if len(o['product_code'] or '')>max_width_col_4:
					max_width_col_4=len(o['product_code'])
				ws.write(rowcount,5,o['product_name'],normal_style)
				if len(o['product_name'] or '')>max_width_col_5:
					max_width_col_5=len(o['product_name'])
				ws.write(rowcount,6,o['quantity'],normal_style_float)
				ws.write(rowcount,7,o['site_id'],normal_style)
				ws.write(rowcount,8,o['unit_price'],normal_style_float)
				ws.write(rowcount,9,o['amount_total'],normal_style_float)
				ws.write(rowcount,10,o['discount'],normal_style)
				ws.write(rowcount,11,o['taxes'],normal_style)

				st=st+o['quantity']
				st1=st1+o['amount_total']
				rowcount+=1
			#if rm_goods_type and data['form']['header_group_by']=='vendor_wise':
			if data['form']['header_group_by']=='vendor_wise':
				ws.write_merge(rowcount,rowcount,2,5, "Total Vendor "+name[0], subtotal_style)
				ws.write(rowcount,6,st,subtotal_style2)
				ws.write(rowcount,9,st1,subtotal_style2)
				rowcount+=1
			elif data['form']['header_group_by']=='date_wise':
				ws.write_merge(rowcount,rowcount,2,5, "Total Receipt ON "+parser.formatLang(name,date=True), subtotal_style)
				ws.write(rowcount,6,st,subtotal_style2)
				ws.write(rowcount,9,st1,subtotal_style2)
				rowcount+=1
			total1+=st
			total2+=st1

		ws.write_merge(rowcount,rowcount,0,5, "Grand Total", total_style)
		ws.write(rowcount,6,total1,total_style2)
		ws.write(rowcount,7," ",total_style)
		ws.write(rowcount,8," ",total_style)
		ws.write(rowcount,9,total2,total_style2)
		ws.write(rowcount,10," ",total_style)
		ws.write(rowcount,11," ",total_style)
		rowcount+=1


		ws.col(0).width = 256 * int(max_width_col_0*1.4)
		ws.col(1).width = 256 * int(max_width_col_1*1.4)
		ws.col(2).width = 256 * int(max_width_col_2*1.4)
		ws.col(3).width = 256 * int(max_width_col_3*1.4)
		ws.col(4).width = 256 * int(max_width_col_4*1.4)
		ws.col(5).width = 256 * int(max_width_col_5*1.4)
		ws.col(6).width = 256 * int(max_width_col_6*2.0)
		ws.col(7).width = 256 * int(max_width_col_7*1.4)
		ws.col(8).width = 256 * int(max_width_col_8*2.0)
		ws.col(9).width = 256 * int(max_width_col_9*2.5)
		ws.col(10).width = 256 * int(max_width_col_10*1.4)
		ws.col(11).width = 256 * int(max_width_col_11*5.0)		

		pass

#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
purchase_register_wizard_xls('report.xls.purchase.register.daily.report','purchase.register.daily.wizard', 'addons/reporting_module/purchase_register/purchase_register_daily.mako',
						parser=PurchaseRegisterDaily)




