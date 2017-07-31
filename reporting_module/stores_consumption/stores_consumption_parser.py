import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class stores_consumption_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(stores_consumption_parser, self).__init__(cr, uid, name, context=context)
		company = self.pool.get('res.users').browse(self.cr, uid, uid,
																context=context).company_id
		self.localcontext.update({
			'time': time,
			'get_location':self._get_location,
			'get_analytic_account':self._get_analytic_account,
			'get_inventory_type': self._get_inventory_type,
			'get_result':self._get_result,
			'company' : company,
		})

	def _get_analytic_account(self,data):
		cr = self.cr
		uid = self.uid
		if not data['analytic_account_force']:
			analytic_account_ids = self.pool.get('account.analytic.account').search(cr,uid,[('id','<>',False)])
		else:
			analytic_account_ids = data['analytic_account_force']
		if analytic_account_ids:
			all_aa_ids = self.pool.get('account.analytic.account').search(cr,uid,[('id','in',sorted(list(set(analytic_account_ids))))],order="code asc")
			return self.pool.get('account.analytic.account').browse(cr,uid,all_aa_ids)
		return []

	def _get_location(self,data):
		cr = self.cr
		uid = self.uid
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('scrap_location','=',False),\
				('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
			# location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('scrap_location','=',False),\
				# ('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
		else:
			location_ids = data['location_force']
		if location_ids:
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="sequence asc, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []
	
	def _get_inventory_type(self,data):
		cr = self.cr
		uid = self.uid
		if data['goods_type']:
			goods_type_ids = data['goods_type']
			return self.pool.get('goods.type').browse(cr,uid,goods_type_ids)
		return []

	def _get_department_ids(self, data):
		cr = self.cr
		uid = self.uid
		if data['department_id']:
			query = "select id from hr_department where id="+str(data['department_id'])+" or parent_id="+str(data['department_id'])
			cr.execute(query)
			dept_ids = cr.dictfetchall()
			dept_ids = dept_ids and [x['id'] for x in dept_ids] or []
			return dept_ids
		return []

	def _get_result(self, data):
		res = []
		start_date=data['start_date']
		end_date=data['end_date']
		location_ids = [loc.id for loc in self._get_location(data)]
		sloc = ''
		# department_ids = data['department_id'] and self._get_department_ids(data) or False
		for location_id in location_ids:
			if sloc != '':
				sloc += ','
			sloc += str(location_id)
		analytic_account_ids = [aa.id for aa in self._get_analytic_account(data)]
		saa = ''
		for analytic_account_id in analytic_account_ids:
			if saa != '':
				saa += ','
			saa += str(analytic_account_id)

		query_issue = "\
			SELECT \
				coalesce(prc.code,coalesce(pfsc.code,'')) as reason_code, \
				coalesce(prc.name,coalesce(pfsc.name,'')) as reason_desc, \
				coalesce(aaa.code,'') as subaccount_code, \
				coalesce(aaa.name,'') as subaccount_desc, \
				sum(round((smm.price_unit_out*smm.qty)::numeric,2)) as consumtion_cost \
			FROM \
				stock_move sm \
				INNER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_product pp ON pp.id=sm.product_id \
				INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id \
				INNER JOIN stock_location sl ON sl.id=sm.location_dest_id \
				LEFT JOIN product_reason_code prc ON prc.id=sm.reason_code \
				LEFT JOIN account_analytic_account aaa ON aaa.id=sm.analytic_account_id \
				LEFT JOIN product_first_segment_code pfsc ON pfsc.id=pp.first_segment_code \
				LEFT JOIN stock_move_matching smm on smm.move_out_id=sm.id \
			WHERE sp.date_done::date between '%s' and '%s' \
				and sl.usage not in ('internal','supplier')\
				and pp.internal_type in ('Packing','Stores') \
				and sm.state='done'"
		if sloc:
			query_issue += " and sm.location_id in (%s)"
			if saa:
				query_issue += " and sm.analytic_account_id in (%s)"
				query_issue = query_issue%(start_date,end_date,sloc,saa)
			else:
				query_issue = query_issue%(start_date,end_date,sloc)
		else:
			if saa:
				query_issue += " and sm.analytic_account_id in (%s)"
				query_issue = query_issue%(start_date,end_date,saa)
			else:
				query_issue = query_issue%(start_date,end_date)
		query_issue += " GROUP BY coalesce(prc.code,coalesce(pfsc.code,'')), coalesce(prc.name,coalesce(pfsc.name,'')), coalesce(aaa.code,''), coalesce(aaa.name,'')"
		query_issue += " ORDER BY coalesce(prc.code,coalesce(pfsc.code,''))"

		query_department_return = "\
			SELECT \
				coalesce(prc.code,coalesce(pfsc.code,'')) as reason_code, \
				coalesce(prc.name,coalesce(pfsc.name,'')) as reason_desc, \
				coalesce(aaa.code,'') as subaccount_code, \
				coalesce(aaa.name,'') as subaccount_desc, \
				sum(round((sm.price_unit*-1*sm.product_qty)::numeric,2)) as consumtion_cost \
			FROM \
				stock_move sm \
				INNER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_product pp ON pp.id=sm.product_id \
				INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id \
				INNER JOIN stock_location sl ON sl.id=sm.location_id \
				LEFT JOIN product_reason_code prc ON prc.id=sm.reason_code \
				LEFT JOIN account_analytic_account aaa ON aaa.id=sm.analytic_account_id \
				LEFT JOIN product_first_segment_code pfsc ON pfsc.id=pp.first_segment_code \
			WHERE sp.date_done::date between '%s' and '%s' \
				and sl.usage not in ('internal','supplier')\
				and pp.internal_type in ('Packing','Stores') \
				and sm.state='done'"
		if sloc:
			query_department_return += " and sm.location_dest_id in (%s)"
			if saa:
				query_department_return += " and sm.analytic_account_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,sloc,saa)
			else:
				query_department_return = query_department_return%(start_date,end_date,sloc)
		else:
			if saa:
				query_department_return += " and sm.analytic_account_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,saa)
			else:
				query_department_return = query_department_return%(start_date,end_date)
		query_department_return += " GROUP BY coalesce(prc.code,coalesce(pfsc.code,'')), coalesce(prc.name,coalesce(pfsc.name,'')), coalesce(aaa.code,''), coalesce(aaa.name,'')"
		query_department_return += " ORDER BY coalesce(prc.code,coalesce(pfsc.code,''))"
		query = "\
			SELECT reason_code, reason_desc, subaccount_code, subaccount_desc, sum(consumtion_cost) as consumtion_cost FROM (( \
			"+query_issue+")\
			UNION ALL \
			("+query_department_return+")) dummy\
			GROUP BY reason_code, reason_desc, subaccount_code, subaccount_desc"
		print "::::::::::::::::::::::::",query
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _uom_to_base(self,data,qty,uom_source,dest_uom_name):
		cr = self.cr
		uid = self.uid
		uom_base = dest_uom_name
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result


	def _price_per_base(self,data,price,uom_source,dest_uom_name):
		cr = self.cr
		uid = self.uid
		uom_base = dest_uom_name
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
			return "%s - %s"%(da.strftime("%d/%m/%Y"),db.strftime("%d/%m/%Y"))
		else:
			return "Wholetime"

class stores_consumption_report_xls(report_xls):
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
		ws = wb.add_sheet('Stores Consumption',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 

		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		title_style_left				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz center; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style_left				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		
		label = xlwt.easyxf('font : name calibri, colour_index black; align: vert centre, horiz center;' "borders:top dashed, bottom thin")
		body_detail2 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;')
		body_detail = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz left;')

		ws.write_merge(0,0,0,7, "PT.BITRATEX INDUSTRIES", title_style)
		ws.write_merge(1,1,0,7, "STORES CONSUMPTION REPORT", title_style)
		ws.write_merge(2,2,0,7, "Period: ("+parser._get_date_range(data)+") As of : "+time.strftime('%d/%m/%Y'), title_style)
		
		ws.write_merge(3,4,0,0, " ", th_both_style)
		ws.write_merge(3,3,1,2, "Analytic Account", th_top_style)
		ws.write(4,1, "Code", th_bottom_style)
		ws.write(4,2, "Description", th_bottom_style)
		ws.write_merge(3,3,3,4, "Reason Code", th_top_style)
		ws.write(4,3, "Code", th_bottom_style)
		ws.write(4,4, "Description", th_bottom_style)
		ws.write_merge(3,4,5,5, "Sanction\nUSD", th_both_style)
		ws.write_merge(3,4,6,6, "Consumption\nUSD", th_both_style)
		ws.write_merge(3,4,7,7, "Balance\nUSD", th_both_style)

		rowcount=5
		max_width_col ={
			0:3,1:6,2:10,3:5,4:12,5:8,6:8,7:8
		}
		result=parser._get_result(data)
		result_grouped = {}
		for res in result:
			key=(res['subaccount_code'] or '-',res['subaccount_desc'] or 'Undefined Analytic Account')
			if key not in result_grouped:
				result_grouped.update({key:[]})
			result_grouped[key].append(res)
		total = {5:0,6:0,7:0}
		for key in sorted(result_grouped.keys(),key=lambda x:x[1]):
			ws.write_merge(rowcount,rowcount,0,7, key[1] or '', normal_bold_style_b)
			rowcount+=1
			subtotal = {5:0, 6:0, 7:0}
			for line in sorted(result_grouped[key], key = lambda x:(x['reason_code'])):
				ws.write(rowcount,1, line['subaccount_code'],normal_style)
				ws.write(rowcount,2, line['subaccount_desc'],normal_style)
				if max_width_col[2]<len(line['subaccount_desc'] or ''):
					max_width_col[2]=len(line['subaccount_desc'])
				ws.write(rowcount,3, line['reason_code'],normal_style)
				ws.write(rowcount,4, line['reason_desc'],normal_style)
				if max_width_col[4]<len(line['reason_desc'] or ''):
					max_width_col[4]=len(line['reason_desc'])
				ws.write(rowcount,5, '' , normal_style_float)
				ws.write(rowcount,6, line['consumtion_cost'] and parser.formatLang(line['consumtion_cost'] or 0.0) or 0.0, normal_style_float)
				ws.write(rowcount,7, '' , normal_style_float)
				subtotal[6]+=line['consumtion_cost']
				rowcount+=1

			ws.write(rowcount,0, '', subtotal_style)
			ws.write_merge(rowcount,rowcount,1,4, 'Subtotal', subtotal_style)
			for c in range(5,8):
				ws.write(rowcount,c, subtotal[c] and subtotal[c] or '', subtotal_style2)
				total[c]+=subtotal[c]
			rowcount+=1
		ws.write_merge(rowcount,rowcount,0,4,' Grand Total', total_style)
		for c in range(5,8):
			ws.write(rowcount,c, total[c] and total[c] or '', total_style2)
			if total[c] and max_width_col[c]<len(str(total[c])):
				max_width_col[c]=len(str(total[c]))
		rowcount+=1

		for x in range(0,8):
			ws.col(x).width = 256*int(max_width_col[x]*1.4)
		pass

stores_consumption_report_xls('report.stores.consumption.report','stores.comsunption.wizard','addons/reporting_module/stores_consumption/stores_consumption_report.mako', parser=stores_consumption_parser, header=False)