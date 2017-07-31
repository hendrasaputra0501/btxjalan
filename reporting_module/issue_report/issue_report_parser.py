import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class issue_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context={}
		super(issue_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_location':self._get_location,
			'get_analytic_account':self._get_analytic_account,
			'get_inventory_type': self._get_inventory_type,
			'get_result':self._get_result,
		})

	def _get_analytic_account(self,data):
		cr = self.cr
		uid = self.uid
		if not data['analytic_account_force']:
			# analytic_account_ids = self.pool.get('account.analytic.account').search(cr,uid,[('id','<>',False)])
			analytic_account_ids = []
		else:
			analytic_account_ids = data['analytic_account_force']
		if analytic_account_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(analytic_account_ids)))
			all_aa_ids = self.pool.get('account.analytic.account').search(cr,uid,[('id','in',sorted(list(set(analytic_account_ids))))],order="code asc")
			return self.pool.get('account.analytic.account').browse(cr,uid,all_aa_ids)
		return []

	def _get_location(self,data):
		cr = self.cr
		uid = self.uid
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXX", "ADA" if data['location_exception'] else "TIDAK ADA"
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('scrap_location','=',False),\
				('usage',"not in",['view','customer','supplier','inventory','procurement','production'])])
			#print "-----------sssssssssssssssssss----------",location_ids
		else:
			location_ids = data['location_force']
		if location_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(location_ids)))
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="sequence asc, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []

	def _get_department(self,data):
		cr=self.cr
		uid=self.uid
		if not data['department_force']:
			department_ids=[]
		else:
			department_ids= data['department_force']
		if department_ids:
			all_deparment_ids=self.pool.get('hr.department').search(cr,uid,[('id','in',sorted(list(set(department_ids))))],order="name asc")
			return self.pool.get('hr.department').browse(cr,uid,all_deparment_ids)
		return []

	def _get_product(self,data):
		cr=self.cr
		uid=self.uid
		if not data['product_force']:
			product_ids=[]
		else:
			product_ids=data['product_force']
		if product_ids:
			all_product_ids=self.pool.get('product.product').search(cr,uid,[('id','in',sorted(list(set(product_ids))))],order="name asc")
			print all_product_ids,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
			return self.pool.get('product.product').browse(cr,uid,all_product_ids)
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

	def _get_result(self, data,inventory_type):
		res = []
		start_date=data['start_date']
		end_date=data['end_date']
		location_ids = [loc.id for loc in self._get_location(data)]
		sloc = ''
		department_ids = data['department_id'] and self._get_department_ids(data) or False
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
		force_dept_ids= [dep.id for dep in self._get_department(data)]
		sdep=''
		for hr_department_id in force_dept_ids:
			if sdep !='':
				sdep+=','
			sdep +=str(hr_department_id)
		force_product_ids=[prod.id for prod in self._get_product(data)]
		sprod=''
		for product_id in force_product_ids:
			if sprod !='':
				sprod+=','
			sprod +=str(product_id)


		# sale_type=data['form']['sale_type'].encode("utf-8")
		#query = "\
		#	SELECT b.name as issue_number, to_char(b.date_done,'DD/MM/YY') as issue_date, b.origin as batch, \
		#	c.default_code as inv_id, d.name as inv_desc, e.name as inv_uom, e.id as inv_uom_id, a.product_qty as qty, a.product_uop_qty as qty2, \
		#	coalesce((select sm.price_unit from stock_move sm where a.prodlot_id=sm.prodlot_id and sm.price_unit is not NULL limit 1),0) as price_unit,\
		#	f.name as site_id, g.name as lot\
		#	FROM stock_move a \
		#	INNER JOIN stock_picking b ON b.id=a.picking_id \
		#	LEFT JOIN product_product c ON c.id=a.product_id \
		#	LEFT JOIN product_template d ON d.id=c.product_tmpl_id \
		#	INNER JOIN product_uom e ON e.id=a.product_uom \
		#	LEFT JOIN stock_location f ON f.id=a.location_id \
		#	LEFT JOIN stock_tracking g ON g.id=a.tracking_id \
		#	WHERE b.type='internal' and internal_shipment_type='rm_issue' \
		#	and b.date_done>='%s' and b.date_done<='%s'"%(start_date,end_date)
		query_issue = "\
			SELECT \
				b.name as issue_number, b.date_done::date as issue_date, b.origin as batch, \
				c.default_code as inv_id, d.name as inv_desc, \
				e.name as inv_uom, e.id as inv_uom_id, a.product_qty as qty, a.product_uop_qty as qty2, \
				coalesce(a.price_unit, 0) as price_unit, \
				(case c.internal_type when 'Packing' then coalesce(h.alias,h.name) else coalesce(f.alias,f.name) end) as site_id, g.name as lot, \
				coalesce(i.code,'') as reason_code, coalesce(i.name,'') as reason_desc, \
				coalesce(j.code,'') as subaccount, \
				coalesce(k.code,'') as first_seg_product_code, \
				coalesce(mt.name,'') as material_type_code, \
				coalesce(mt.description,'') as material_type_name, \
				sum(round((smm.qty*smm.price_unit_out)::numeric,2)) as amount, \
				hd.name as department \
			FROM \
				stock_move a \
				INNER JOIN stock_picking b ON b.id=a.picking_id \
				LEFT JOIN product_product c ON c.id=a.product_id \
				LEFT JOIN product_template d ON d.id=c.product_tmpl_id \
				INNER JOIN product_uom e ON e.id=a.product_uom \
				LEFT JOIN stock_location f ON f.id=a.location_id \
				LEFT JOIN stock_tracking g ON g.id=a.tracking_id \
				LEFT JOIN stock_location h ON h.id=a.location_dest_id \
				LEFT JOIN product_reason_code i ON i.id=a.reason_code \
				LEFT JOIN account_analytic_account j ON j.id=a.analytic_account_id \
				LEFT JOIN product_first_segment_code k ON k.id=c.first_segment_code \
				LEFT JOIN material_request mr ON mr.id=b.material_req_id \
				LEFT JOIN product_material_type mt ON mt.id=a.material_type \
				LEFT JOIN stock_move_matching smm on smm.move_out_id=a.id \
				LEFT JOIN hr_department hd on hd.id=mr.department\
			WHERE b.date_done::date between '%s' and '%s' \
				and h.usage not in ('internal','supplier')\
				and c.internal_type = '%s' \
				and a.state='done'"
		if sloc:
			query_issue += " and a.location_id in (%s)"
			# if saa:
			# 	query_issue += " and a.analytic_account_id in (%s)"
			# 	query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc,saa)
			# else:
			# 	query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc)
			if saa:
				query_issue += " and a.analytic_account_id in (%s)"
				query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc,saa)
			elif sdep:
				query_issue += " and mr.department in (%s)"
				query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc,sdep)
			elif sprod:
				query_issue += " and a.product_id in (%s)"
				query_issue=query_issue%(start_date,end_date,inventory_type.code,sloc,sprod)
				# print sprod,"nananananananananan"
			else:
				query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc)

		else:
			if saa:
				query_issue += " and a.analytic_account_id in (%s)"
				query_issue = query_issue%(start_date,end_date,inventory_type.code,saa)
			elif sdep:
				query_issue += " and mr.department in (%s)"
				query_issue = query_issue%(start_date,end_date,inventory_type.code,sloc,sdep)
			elif sprod:
				query_issue += " and a.product_id in (%s)"
				query_issue=query_issue%(start_date,end_date,inventory_type.code,sloc,sprod)
				# print sprod,"kakakakakakakakakakakakakak"
			else:
				query_issue = query_issue%(start_date,end_date,inventory_type.code)

		if department_ids:
			query_issue += " and (mr.department in ("+','.join([str(x) for x in department_ids])+") or mr.department is NULL) "

		query_issue += "GROUP BY a.id,b.name,b.date_done,b.origin,c.default_code,d.name,e.name ,e.id,c.internal_type,\
h.alias,h.name,f.alias,f.name,g.name,i.code,i.name,j.code,k.code,mt.name,mt.description,hd.name ORDER BY reason_code,issue_date, issue_number "
		
		query_department_return = "\
			SELECT \
				b.name as issue_number, b.date_done::date as issue_date, b.origin as batch, \
				c.default_code as inv_id, d.name as inv_desc, \
				e.name as inv_uom, e.id as inv_uom_id, (-1*coalesce(a.product_qty,0.0)) as qty, (-1*coalesce(a.product_uop_qty,0.0)) as qty2, \
				coalesce(a.price_unit, 0) as price_unit, \
				(case c.internal_type when 'Packing' then coalesce(h.alias,h.name) else coalesce(f.alias,f.name) end) as site_id, g.name as lot, \
				coalesce(i.code,'') as reason_code, coalesce(i.name,'') as reason_desc, \
				coalesce(j.code,'') as subaccount, \
				coalesce(k.code,'') as first_seg_product_code, \
				coalesce(mt.name,'') as material_type_code, \
				coalesce(mt.description,'') as material_type_name, \
				sum(round(((-1*a.product_qty)*a.price_unit)::numeric,2)) as amount, \
				hd.name as department \
			FROM \
				stock_move a \
				INNER JOIN stock_picking b ON b.id=a.picking_id \
				LEFT JOIN product_product c ON c.id=a.product_id \
				LEFT JOIN product_template d ON d.id=c.product_tmpl_id \
				INNER JOIN product_uom e ON e.id=a.product_uom \
				LEFT JOIN stock_location f ON f.id=a.location_dest_id \
				LEFT JOIN stock_tracking g ON g.id=a.tracking_id \
				LEFT JOIN stock_location h ON h.id=a.location_id \
				LEFT JOIN product_reason_code i ON i.id=a.reason_code \
				LEFT JOIN account_analytic_account j ON j.id=a.analytic_account_id \
				LEFT JOIN product_first_segment_code k ON k.id=c.first_segment_code \
				LEFT JOIN material_request mr ON mr.id=b.material_req_id \
				LEFT JOIN product_material_type mt ON mt.id=a.material_type \
				LEFT JOIN hr_department hd on hd.id=mr.department\
			WHERE b.date_done::date between '%s' and '%s' \
				and h.usage not in ('internal','supplier')\
				and c.internal_type = '%s' \
				and a.state='done'"
		if sloc:
			query_department_return += " and a.location_dest_id in (%s)"
			if saa:
				query_department_return += " and a.analytic_account_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code,sloc,saa)
			elif sprod:
				query_department_return += " and a.product_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code,sloc,sprod)
			else:
				# query_department_return += " and a.location_dest_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code,sloc)
		else:
			if saa:
				query_department_return += " and a.analytic_account_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code,saa)
			elif sprod:
				query_department_return += " and a.product_id in (%s)"
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code,sloc,sprod)
			else :
				query_department_return = query_department_return%(start_date,end_date,inventory_type.code)

		# if department_ids:
		# 	query_department_return += " and (mr.department in ("+','.join([str(x) for x in department_ids])+") or mr.department is NULL) "

		query_department_return += "GROUP BY a.id,b.name,b.date_done,b.origin,c.default_code,d.name,e.name ,e.id,c.internal_type,\
h.alias,h.name,f.alias,f.name,g.name,i.code,i.name,j.code,k.code,mt.name,mt.description,hd.name ORDER BY reason_code,issue_date, issue_number "
		
		query = "\
			SELECT * FROM (( \
			"+query_issue+")\
			UNION ALL \
			("+query_department_return+")) dummy\
			ORDER BY issue_date, issue_number"
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		# print query
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
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

class issue_report_xls(report_xls):
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
		for inventory_type in parser._get_inventory_type(data): 
			ws = wb.add_sheet('Class - %s'%inventory_type.name,cell_overwrite_ok=True)
			#ws = wb.add_sheet('Issue Report',cell_overwrite_ok=True)
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
			subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
			subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
			total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
			total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
			total_style_left				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
			total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
			
			label = xlwt.easyxf('font : name calibri, colour_index black; align: vert centre, horiz center;' "borders:top dashed, bottom thin")
			body_detail2 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;')
			body_detail = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz left;')

			ws.write_merge(0,0,0,0, "Whse.Loc", title_style_left)
			ws.write_merge(1,1,0,0, "Class Id", title_style_left)
			ws.write_merge(2,2,0,0, "Issue Type", title_style_left)
			#ws.write_merge(0,0,1,2, ": MMD-RM", title9)
			#ws.write_merge(1,1,1,2, ": RM", title9)
			#ws.write_merge(2,2,1,2, ": RAW MATERIAL", title9)
			ws.write_merge(1,1,1,2, ": %s"%inventory_type.name, title_style)

			ws.write_merge(0,0,3,14, "PT.BITRATEX INDUSTRIES", title_style)
			ws.write_merge(1,1,3,14, "ISSUE REPORT"+(data['header_group_by']=='site_wise' and '-SITE WISE' or (data['header_group_by']=='analytic_account_wise' and '-ANALYTIC ACCOUNT WISE' or (data['header_group_by']=='code_wise' and '-Code Wise' or ''))), title_style)
			ws.write_merge(2,2,3,14, "Period: ("+parser._get_date_range(data)+") As of : "+time.strftime('%d/%m/%Y'), title_style)
			
			ws.write_merge(3,3,0,2, "ISSUE", th_top_style)
			ws.write(4,0, "No.", th_bottom_style)
			ws.write(4,1, "Date", th_bottom_style)
			ws.write(4,2, "Batch", th_bottom_style)
			ws.write_merge(3,3,3,5, "Inventory", th_top_style)
			ws.write(4,3, "Id", th_bottom_style)
			ws.write(4,4, "Description", th_bottom_style)
			ws.write(4,5, "UOM", th_bottom_style)
			ws.write_merge(3,4,6,6, "SITE\nID", th_both_style)
			ws.write_merge(3,4,7,7, "Quantity", th_both_style)
			ws.write_merge(3,4,8,8, inventory_type.code=='Raw Material' and "Bales" or "2nd Qty", th_both_style)
			ws.write_merge(3,3,9,10, "USD", th_top_style)
			ws.write(4,9, "Unit Cost", th_bottom_style)
			ws.write(4,10, "Ext.Cost", th_bottom_style)
			ws.write_merge(3,3,11,12, "CC", th_top_style)
			ws.write(4,11, "Account", th_bottom_style)
			ws.write(4,12, "Subaccount",th_bottom_style)
			ws.write_merge(3,3,13,14, "REASON", th_top_style)
			ws.write(4,13, "Code",th_bottom_style)
			ws.write(4,14, "Description",th_bottom_style)
			
			rowcount=5
			max_width_col ={
				0:10,1:8,2:8,3:12,4:20,5:5,6:5,7:8,8:8,9:8,10:8,11:7,12:7,13:5,14:10
			}
			result=parser._get_result(data,inventory_type)
			result_grouped = {}
			for res in result:
				key=inventory_type.code=="Raw Material" and not data['header_group_by'] and res['lot'] \
					or (data['header_group_by'] and data['header_group_by']=='site_wise' and res['site_id'] \
						or (data['header_group_by']=='analytic_account_wise' and res['subaccount'] or '') \
							or (data['header_group_by']=='code_wise' and res['first_seg_product_code'] or '')
								or (data['header_group_by']=='material_type' and "%s - %s"%(res['material_type_code'],res['material_type_name']) or '')
								or (data['header_group_by']=='department_wise' and res['department'] or ''))
				# print key,"dadadadadadadadadaadadadadada"
				if key not in result_grouped:
					result_grouped.update({key:[]})
				result_grouped[key].append(res)
			total_7, total_8, total_10 = 0, 0, 0
			
			for key in sorted(result_grouped.keys()):
				if inventory_type.code=="Raw Material" and not data['header_group_by']:
					ws.write(rowcount,0, 'LotNbr')
					ws.write_merge(rowcount,rowcount,1,14, ':  '+(key and str(key) or 'Undefined Lot'), normal_bold_style_b)
					rowcount+=1
				elif data['header_group_by']=='site_wise' or data['header_group_by']=='analytic_account_wise' or data['header_group_by']=='code_wise' or data['header_group_by']=='material_type' or data['header_group_by']=='department_wise':
					ws.write_merge(rowcount,rowcount,0,14, ((data['header_group_by']=='site_wise' and 'Site ID : ') or (data['header_group_by']=='analytic_account_wise' and 'Analytic Account : ') or (data['header_group_by']=='code_wise' and 'Product Code : ') or (data['header_group_by']=='material_type' and 'Detail Group : ') or (data['header_group_by']=='department_wise' and 'Department : ') or '')+(key and  str(key) or 'Undefined'), normal_bold_style_b)
					# ws.write(rowcount,1, ':  '+(key and str(key) or 'Undefined Site ID'))
					rowcount+=1

				subtotal_7, subtotal_8, subtotal_10 = 0, 0, 0
				if data['header_group_by']=='analytic_account_wise':
					linesss = sorted(result_grouped[key], key = lambda x:(x['issue_date'],x['site_id'],x['issue_number'],x['reason_code']))
				else:
					linesss = sorted(result_grouped[key], key = lambda x:(x['issue_date'],x['issue_number'],x['reason_code']))

				for line in linesss:
					ws.write(rowcount,0,line['issue_number'], normal_style)
					if len(line['issue_number'] and line['issue_number'] or '')>max_width_col[0]:
						max_width_col[0] = len(line['issue_number'])
					
					ws.write(rowcount,1,parser.formatLang(line['issue_date'],date=True), normal_style)
					if len(line['issue_date'] and line['issue_date'] or '')>max_width_col[1]:
						max_width_col[1] = len(line['issue_date'])
					
					ws.write(rowcount,2,line['batch'] , normal_style)
					if len(line['batch'] and line['batch'] or '')>max_width_col[2]:
						max_width_col[2] = len(line['batch'])
					
					ws.write(rowcount,3,line['inv_id'], normal_style)
					if len(line['inv_id'] and line['inv_id'] or '')>max_width_col[3]:
						max_width_col[3]= len(line['inv_id'])
					
					ws.write(rowcount,4,line['inv_desc'], normal_style)
					
					if inventory_type.code == 'Raw Material': 
						sinv_uom = 'KGS'
					else:
						sinv_uom = line['inv_uom']
					ws.write(rowcount,5,sinv_uom,normal_style)
					
					ws.write(rowcount,6,line['site_id'], normal_style)
					if len(line['site_id'] and line['site_id'] or '')>max_width_col[6]:
						max_width_col[6]=len(line['site_id'])
					if inventory_type.code == 'Raw Material': 
						qty = parser._uom_to_base(data,line['qty'],line['inv_uom_id'],'KGS')
					else:
						qty = line['qty']
					ws.write(rowcount,7,qty, normal_style_float)
					subtotal_7 += qty
					ws.write(rowcount,8,line['qty2'], normal_style_float)
					subtotal_8 += line['qty2']
					if line['price_unit']:
						if inventory_type.code == 'Raw Material': 
							price = parser._price_per_base(data,line['price_unit'],line['inv_uom_id'],'KGS')
						else:
							price = line['price_unit']
						ext_cost = line['amount']
						subtotal_10 += ext_cost
					else:
						price = 0.0
						ext_cost = 0.0
					ws.write(rowcount,9,price, normal_style_float)
					ws.write(rowcount,10,ext_cost, normal_style_float)
					ws.write(rowcount,11,'', normal_style)
					ws.write(rowcount,12,line['subaccount'], normal_style)
					ws.write(rowcount,13,line['reason_code'], normal_style)
					ws.write(rowcount,14,line['reason_desc'], normal_style)
					rowcount+=1

				
				if inventory_type.code=='Raw Material' and not data['header_group_by']:
					ws.write_merge(rowcount,rowcount,0,6,' Subtotal Lot '+(key and str(key) or 'Undefined Lot'), subtotal_style)
					ws.write(rowcount,7, subtotal_7, subtotal_style2)
					if max_width_col[7] < len(str(subtotal_7)):
						max_width_col[7] = len(str(subtotal_7))
					ws.write(rowcount,8, subtotal_8, subtotal_style2)
					if max_width_col[8] < len(str(subtotal_8)):
						max_width_col[8] = len(str(subtotal_8))
					ws.write(rowcount, 9, " ", subtotal_style)
					ws.write(rowcount, 10, subtotal_10, subtotal_style2)
					if max_width_col[10] < len(str(subtotal_8)):
						max_width_col[10] = len(str(subtotal_8))
					ws.write_merge(rowcount,rowcount,11,14,' ', subtotal_style)
					rowcount+=1
				# elif data['header_group_by']=='site_wise' or data['header_group_by']=='analytic_account_wise' or data['header_group_by']=='code_wise' or data['header_group_by']=='material_type' :
				# 	ws.write_merge(rowcount,rowcount,0,6,(data['header_group_by']=='site_wise' and 'Subtotal Site ID : ' or (data['header_group_by']=='code_wise' and 'Total Product : '  or 'Subtotal Analytic Account : '))+(key and str(key) or 'Undefined'), subtotal_style)
				elif data['header_group_by']=='site_wise' or data['header_group_by']=='analytic_account_wise' or data['header_group_by']=='code_wise' or data['header_group_by']=='material_type' or data['header_group_by']=='department_wise' :
					ws.write_merge(rowcount,rowcount,0,6,(data['header_group_by']=='site_wise' and 'Subtotal Site ID : ' or data['header_group_by']=='analytic_account_wise' and 'Subtotal Analytic Account : ' or (data['header_group_by']=='code_wise' and 'Total Product : ' or data['header_group_by']=='material_type' and 'Total Material :' or data['header_group_by']=='department_wise' and 'Total Department : '))+(key and str(key) or 'Undefined'), subtotal_style)
					ws.write(rowcount,7, subtotal_7, subtotal_style2)
					if max_width_col[7] < len(str(subtotal_7)):
						max_width_col[7] = len(str(subtotal_7))
					ws.write(rowcount,8, subtotal_8, subtotal_style2)
					if max_width_col[8] < len(str(subtotal_8)):
						max_width_col[8] = len(str(subtotal_8))
					ws.write(rowcount, 9, " ", subtotal_style)
					ws.write(rowcount, 10, subtotal_10, subtotal_style2)
					if max_width_col[10] < len(str(subtotal_8)):
						max_width_col[10] = len(str(subtotal_8))
					ws.write_merge(rowcount,rowcount,11,14,' ', subtotal_style)
					rowcount+=1
				total_7+=subtotal_7
				total_8+=subtotal_8
				total_10+=subtotal_10
			ws.write_merge(rowcount,rowcount,0,6,' Grand Total', total_style)
			ws.write(rowcount,7, total_7, total_style2)
			if max_width_col[7] < len(str(total_7)):
				max_width_col[7] = len(str(total_7))
			ws.write(rowcount,8, total_8, total_style2)
			if max_width_col[8] < len(str(total_8)):
				max_width_col[8] = len(str(total_8))
			ws.write(rowcount, 9, " ", total_style)
			ws.write(rowcount, 10, total_10, total_style2)
			if max_width_col[10] < len(str(total_10)):
				max_width_col[10] = len(str(total_10))
			ws.write_merge(rowcount,rowcount,11,14,' ', total_style)
			rowcount+=1

			for x in range(0,11):
				ws.col(x).width = 256*int(max_width_col[x]*1.4)
			pass

issue_report_xls('report.issue.report','issue.report.wizard','addons/reporting_module/issue_report/issue_report.mako', parser=issue_report_parser, header=False)