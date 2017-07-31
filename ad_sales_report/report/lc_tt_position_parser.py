import re
import time
import xlwt
from report import report_sxw
from report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class lc_tt_position_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(lc_tt_position_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_result(self, data):
		res = []
		query = "\
			SELECT\
				a.lc_number as lc_no, coalesce(l.name,a.name) as bat_no, \
				b.name as nego_bank, to_char(a.rcvd_smg,'DD/MM/YY') as rcvd_on, \
				to_char(a.lc_expiry_date,'DD/MM/YY') as exp, to_char(lpl.earliest_delivery_date,'DD/MM/YY') as esd, \
				to_char(lpl.est_delivery_date,'DD/MM/YY') as lsd, coalesce(c.price_unit,0) as price_unit, coalesce(lpl.product_uom_qty,0) as qty, \
				c.product_uom as uom, coalesce(a.tolerance_percentage,0) as tol, \
				c.sequence_line as sc_number, substring(e.name from 1 for 16) as cust_name, \
				(lpl.product_uom_qty+coalesce(f.product_qty,0.0)) as balance_qty, \
				c.cone_weight, g.alias as packing, c.other_description as remarks, \
				h.default_code, substring(k.name from 1 for 19) as prod_name,\
				h2.name as blend, h.count, h.sd_type, h.wax, \
				i.s_u as s_u, i.usance_day as usance_day, h.id as product_id, coalesce(c.production_location,j.property_stock_prod_id) as property_stock_prod_id, \
				n.name as prod_loc, coalesce((select count(a1.id) from letterofcredit a1 where a1.id = a.parent_id),0) as amd \
			FROM\
				letterofcredit_product_line lpl\
				INNER JOIN sale_order_line c on c.id=lpl.sale_line_id\
				INNER JOIN sale_order d on d.id=c.order_id\
				LEFT JOIN letterofcredit a on a.id=lpl.lc_id\
				LEFT JOIN res_bank b on b.id=a.negotiate_bank\
				LEFT JOIN res_partner e on e.id=a.partner_id\
				LEFT JOIN (select f1.lc_product_line_id, f1.product_id, \
								  sum(case f2.type \
									  when 'in' then f1.product_qty \
									  when 'out' then -f1.product_qty \
									  else 0 end) as product_qty \
						   from stock_move f1 \
						   inner join stock_picking f2 on f1.picking_id=f2.id\
						   where f1.state='done' and to_char(f2.date_done,'YYYY-MM-DD') <= '%s' \
						   group by f1.lc_product_line_id,f1.product_id) f \
					  on lpl.id = f.lc_product_line_id and lpl.product_id = f.product_id\
				LEFT JOIN packing_type g on g.id=c.packing_type\
				LEFT JOIN product_product h on h.id=c.product_id\
				LEFT JOIN mrp_blend_code h2 on h2.id=h.blend_code\
				LEFT JOIN (select \
					(case i1.type \
					when 'usance' then 'U'\
					else 'S' end) as s_u, \
					(case i1.type \
					when 'usance' then coalesce((select i1_1.days from account_payment_term_line i1_1 where i1_1.payment_id=i1.id limit 1),0)\
					else 0 end) as usance_day, i1.id \
					from account_payment_term i1) as i on i.id=a.lc_payment_term\
				LEFT JOIN (select cast(substring(j1.value_reference from 16 for (char_length(j1.value_reference)-15)) as integer) as property_stock_prod_id,cast(substring(j1.res_id from 18 for (char_length(j1.res_id)-16)) as integer) as prod_tmpl_id from ir_property j1 where j1.name='property_stock_production') j on j.prod_tmpl_id=h.product_tmpl_id \
				LEFT JOIN product_template k on k.id=h.product_tmpl_id\
				LEFT JOIN letterofcredit l on l.id=a.parent_id\
				LEFT JOIN stock_location m on m.id=j.property_stock_prod_id\
				LEFT JOIN stock_location n on n.id=m.location_id\
			WHERE a.lc_type='%s' and (a.hide='f' or a.hide is NULL) and d.sale_type='%s' and d.goods_type='%s' and a.state not in ('closed','canceled','nonactive') \
			and (lpl.knock_off is NULL or lpl.knock_off!='t' or lpl.date_knock_off>'%s') \
			and lpl.min_tolerance > 0.0 \
			ORDER BY n.name, property_stock_prod_id, h2.name,h.count,h.sd_type,h.wax,c.sequence_line asc\
			"%(data['form']['as_on'].encode("utf-8"),data['form']['lc_type'].encode("utf-8"),data['form']['sale_type'].encode("utf-8"),data['form']['goods_type'].encode("utf-8"),data['form']['as_on'].encode("utf-8"))
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _uom_to_base(self,data,qty,uom_source):
		cr = self.cr
		uid = self.uid
		if data['form']['sale_type'] == 'local':
			uom_base = 'KGS'
		elif data['form']['sale_type'] == 'export':
			uom_base = 'BALES'
		else:
			uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result


	def _price_per_base(self,data,price,uom_source):
		cr = self.cr
		uid = self.uid
		if data['form']['sale_type'] == 'local':
		  uom_base = 'KGS'
		elif data['form']['sale_type'] == 'export':
		  uom_base = 'BALES'
		else:
		  uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=base and base[0] or False)
		if qty_result>0:
		  price_result = price*1000.0/qty_result 
		else:
		  price_result = price 
		return price_result

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

class lc_tt_position_xls(report_xls):
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
		results = parser._get_result(data)
		# group disini
		result_grouped={}
		for res in results:
			key=res['prod_loc']
			if key not in result_grouped:
				result_grouped.update({key:{}})
			key1=res['property_stock_prod_id']
			if key1 not in result_grouped[key]:
				result_grouped[key].update({key1:{}})
			key2=res['blend']
			if key2 not in result_grouped[key][key1]:
				result_grouped[key][key1].update({key2:{}})
			key3=res['count']
			if key3 not in result_grouped[key][key1][key2]:
				result_grouped[key][key1][key2].update({key3:{}})
			key4=res['sd_type']
			if key4 not in result_grouped[key][key1][key2][key3]:
				result_grouped[key][key1][key2][key3].update({key4:{}})
			key5=res['wax']
			if key5 not in result_grouped[key][key1][key2][key3][key4]:
				result_grouped[key][key1][key2][key3][key4].update({key5:{}})
			key6=res['product_id']
			if key6 not in result_grouped[key][key1][key2][key3][key4][key5]:
				result_grouped[key][key1][key2][key3][key4][key5].update({key6:[]})
			
			result_grouped[key][key1][key2][key3][key4][key5][key6].append(res)

		for parent_loc in sorted(result_grouped.keys()):
			ws = wb.add_sheet((str(parent_loc)+" LC TT Position"))
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1 
			ws.preview_magn = 60
			ws.normal_magn = 60
			ws.print_scaling=60
			ws.page_preview = False
			ws.set_fit_width_to_pages(1)
			
			title_style = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
			title_style1 = xlwt.easyxf('font: height 210, name Calibri, colour_index black; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
			hdr_style_border_top = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin;')
			hdr_style_border_top_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin, bottom thin;')
			hdr_style_border_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: bottom thin;')
			normal_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz left;',num_format_str='#,##0;(#,##0)')
			normal_style1 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz left;',num_format_str='#,##0.00;(#,##0.00)')
			normal_style2 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
			normal_right_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0;(#,##0)')
			normal_right_style1 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
			normal_right_style2 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')

			# max_width_col_16 = len("DESCRIPTION")
			if data['form']['lc_type'].encode("utf-8")=='in':
				lc_type = 'LC'
			else:
				lc_type = 'TT'

			ws.write_merge(0,0,0,22,"PT. Bitratex Industries", title_style )
			ws.write_merge(1,1,0,22,lc_type+" POSITION STATEMENT (PRODUCT WISE) AS ON "+datetime.strftime(datetime.strptime(data['form']['as_on'],"%Y-%m-%d"),"%d/%m/%Y"), title_style )
			ws.write_merge(2,2,0,22,"", title_style )
			
			ws.write(4,0,"LC NO", hdr_style_border_top_bottom)
			ws.write(4,1,"Bat.No",hdr_style_border_top_bottom)
			ws.write(4,2,"NEGO BANK", hdr_style_border_top_bottom)
			ws.write(4,3, "S/U", hdr_style_border_top_bottom)
			ws.write(4,4,"DAYS", hdr_style_border_top_bottom)
			ws.write(4,5,"RCVD.ON",hdr_style_border_top_bottom)
			ws.write(4,6,"ESD",hdr_style_border_top_bottom)
			ws.write(4,7,"LSD", hdr_style_border_top_bottom)
			ws.write(4,8,"EXP", hdr_style_border_top_bottom)
			ws.write(4,9,"AMD",hdr_style_border_top_bottom)
			ws.write(4,10,"QUANTITY", hdr_style_border_top_bottom)
			ws.write(4,11,"QTY TOL", hdr_style_border_top_bottom)
			ws.write_merge(3,3,0,11,"LC. DETAILS",hdr_style_border_top_bottom)
			ws.write_merge(3,4,12,12,"AMOUNT", hdr_style_border_top_bottom)
			ws.write_merge(3,4,13,13,"AMT.\nTOL.", hdr_style_border_top_bottom)
			ws.write_merge(3,4,14,14,"S.C\nNO", hdr_style_border_top_bottom)
			ws.write_merge(3,4,15,15,"CUSTOMER", hdr_style_border_top_bottom)
			ws.write_merge(3,4,16,16,"PRODUCT\nDESCRIPTION", hdr_style_border_top_bottom)
			ws.write_merge(3,4,17,17,"TOL\n%", hdr_style_border_top_bottom)
			ws.write_merge(3,3,18,19," BALANCE", hdr_style_border_top_bottom)
			ws.write(4,18,"QTY", hdr_style_border_top_bottom)
			ws.write(4,19,"AMOUNT", hdr_style_border_top_bottom)
			ws.write_merge(3,4,20,20,"C/P", hdr_style_border_top_bottom)
			ws.write_merge(3,4,21,21, "C/W", hdr_style_border_top_bottom)
			ws.write_merge(3,4,22,22, "REMARKS", hdr_style_border_top_bottom)

			rowcount=5
			max_width_col_0=0
			max_width_col_1=0
			max_width_col_2 = len("NEGO BANK")
			max_width_col_3 = 3
			max_width_col_4 = 5
			max_width_col_9 = 4
			max_width_col_13 = len("AMT.TOL")
			max_width_col_14=0
			max_width_col_15=16
			max_width_col_16=20
			max_width_col_17 = 4
			max_width_col_20=3
			max_width_col_21=3
			max_width_col_22=0
			for loc_id in sorted(result_grouped[parent_loc].keys()):
				for blend in sorted(result_grouped[parent_loc][loc_id].keys()):
					for count in sorted(result_grouped[parent_loc][loc_id][blend].keys()):
						for sd in sorted(result_grouped[parent_loc][loc_id][blend][count].keys()):
							for wax in sorted(result_grouped[parent_loc][loc_id][blend][count][sd].keys()):
								for pl in sorted(result_grouped[parent_loc][loc_id][blend][count][sd][wax].keys()):	
									for line in result_grouped[parent_loc][loc_id][blend][count][sd][wax][pl]:
										price_unit = parser._price_per_base(data,line['price_unit'],line['uom'])
										qty = round(parser._uom_to_base(data,line['qty'],line['uom']),2)
										qty_tol = round(qty*(line['tol']/100),2)
										amt = round(price_unit*qty,2)
										amt_tol = round(amt * (line['tol']/100),2)
										balance_qty = round(parser._uom_to_base(data,line['balance_qty'],line['uom']),2)
										balance_amt = round(price_unit*balance_qty,2)

										if balance_qty < qty_tol or balance_qty < 1:
											continue
										
										ws.write(rowcount,0, line['lc_no'],normal_style)
										if len(line['lc_no'] and line['lc_no'] or '')>max_width_col_0:
											max_width_col_0 = len(line['lc_no'])
										ws.write(rowcount,1, line['bat_no'],normal_style)
										if len(line['bat_no'] and line['bat_no'] or '')>max_width_col_1:
											max_width_col_1 = len(line['bat_no'])
										ws.write(rowcount,2, line['nego_bank'],normal_style)
										if len(line['nego_bank'] and line['nego_bank'] or '')>max_width_col_2:
											max_width_col_2 = len(line['nego_bank'])
										ws.write(rowcount,3,line['s_u'], normal_style)
										ws.write(rowcount,4,line['usance_day'] and line['usance_day'] or '', normal_right_style)
										ws.write(rowcount,5, line['rcvd_on'],normal_style)
										ws.write(rowcount,6, line['esd'],normal_style)
										ws.write(rowcount,7, line['lsd'],normal_style)
										ws.write(rowcount,8, line['exp'],normal_style)
										ws.write(rowcount,9, line['amd'] and line['amd'] or '',normal_style)
										ws.write(rowcount,10,qty, normal_right_style1)
										ws.write(rowcount,11,qty_tol, normal_right_style1)
										ws.write(rowcount,12,amt, normal_right_style1)
										ws.write(rowcount,13,amt_tol, normal_right_style1)
										if len(str(amt_tol))>max_width_col_13:
											max_width_col_13 = len(str(amt_tol))
										ws.write(rowcount,14,line['sc_number'],normal_style)
										if len(line['sc_number'] and line['sc_number'] or '')>max_width_col_14:
											max_width_col_14 = len(line['sc_number'])
										ws.write(rowcount,15,line['cust_name'],normal_style)
										ws.write(rowcount,16,line['prod_name'],normal_style)
										ws.write(rowcount,17,line['tol'],normal_style)
										ws.write(rowcount,18,balance_qty,normal_right_style1)
										ws.write(rowcount,19,balance_amt,normal_right_style1)
										# if len(line['cust_name'] and line['cust_name'] or '')>max_width_col_15:
										# 	max_width_col_15 = len(line['cust_name'])
										ws.write(rowcount,20,line['packing'],normal_style)
										ws.write(rowcount,21,line['cone_weight'] and line['cone_weight'] or '',normal_right_style1)
										if len(str(line['cone_weight'] and line['cone_weight'] or ''))>max_width_col_21:
											max_width_col_21 = len(str(line['cone_weight'] and line['cone_weight'] or ''))
										ws.write(rowcount,22,line['remarks'],normal_style)
										if len(line['remarks'] and line['remarks'] or '')>max_width_col_22:
											max_width_col_22 = len(line['remarks'])
										rowcount+=1
			ws.col(0).width = 256 * int(max_width_col_0)
			ws.col(1).width = 256 * int(max_width_col_1)
			ws.col(2).width = 256 * int(max_width_col_2 * 1.2)
			ws.col(3).width = 256 * int(max_width_col_3 * 1.6)
			ws.col(4).width = 256 * int(max_width_col_4 * 1.2)
			ws.col(9).width = 256 * int(max_width_col_9 * 1.5)
			ws.col(13).width = 256 * int(max_width_col_13 * 1.2)
			ws.col(14).width = 256 * int(max_width_col_14)
			ws.col(15).width = 256 * int(max_width_col_15 * 1.2)
			ws.col(16).width = 256 * int(max_width_col_16 * 1.2)
			ws.col(17).width = 256 * int(max_width_col_17 * 1.2)
			ws.col(20).width = 256 * int(max_width_col_20 * 1.6)
			ws.col(21).width = 256 * int(max_width_col_21 * 1.2)
			ws.col(22).width = 256 * int(max_width_col_22)
		pass

lc_tt_position_xls('report.lc.tt.position.report', 'lc.tt.position.wizard', 'addons/ad_sales_report/report/pending_sales_report.mako', parser=lc_tt_position_parser, header=False)
