from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging
import json, ast
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula

class summary_stock_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(summary_stock_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_available_location':self._get_available_location,
			'get_parent_location':self._get_parent_location,
			'get_product_info':self._get_product_info,
			'get_tracking_info':self._get_tracking_info,
			'get_uom_info':self._get_uom_info,
			'get_stock'	: self._get_stock,
			'get_location':self.get_location,
			'get_date_range':self._get_date,
			'get_inventory_type': self._get_inventory_type,
		})

	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

	def _get_mode(self, data):
		dictionary_mode={
			'product' : "Product Wise",
			'location' : "Location Wise",
		}
		return dictionary_mode.get(data.get('grouping',False),'location')

	def _get_date_range(self,data):
		if data['filter_type']=='date_period':
			date_start = data['start_date']
			date_stop = data['end_date']
			if date_start and not date_stop:
				da = datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S")
				return "From : %s"%da.strftime("%Y-%m-%d")
			elif date_stop and not date_start:
				db = datetime.strptime(date_stop,"%Y-%m-%d %H:%M:%S")
				return "Until : %s"%db.strftime("%Y-%m-%d")
			elif date_stop and date_start:
				da = datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S")
				db = datetime.strptime(date_stop,"%Y-%m-%d %H:%M:%S")
				return "Range : %s - %s"%(da.strftime("%Y-%m-%d"),db.strftime("%Y-%m-%d"))
			else:
				return "Wholetime"
		else:
			as_on_date = data['as_on']
			as_on = datetime.strptime(as_on_date,"%Y-%m-%d %H:%M:%S")
			return "As Of : %s"%as_on.strftime("%Y-%m-%d")

	def _get_available_location(self,parent,locations):
		location_ids = self.pool.get('stock.location').search(self.cr,self.uid,[('name','=',parent)],order="name asc")
		location = self.pool.get('stock.location').browse(self.cr,self.uid,location_ids)
		location_idss=[]
		for x in location:
			for y in x.child_ids:
				for z in y.child_ids:
					location_idss.append(z.id)
		location_ids = self.pool.get('stock.location').search(self.cr,self.uid,[('id','in',location_idss)],order="name asc")
		return self.pool.get('stock.location').browse(self.cr,self.uid,location_idss)
	
	def _get_parent_location(self,data):
		location_ids = [loc.id for loc in self.get_location(data)]
		locsss = self.pool.get('stock.location').browse(self.cr,self.uid,location_ids)
		parent_location_ids = [ll.location_id.location_id.id for ll in locsss]
		parent_location_ids = list(set(parent_location_ids))
		parent_location_ids = self.pool.get('stock.location').search(self.cr,self.uid,[('id','in',parent_location_ids)],order="name asc")
		return self.pool.get('stock.location').browse(self.cr,self.uid,location_ids)

	def _get_product_info(self):
		prd_ids = self.pool.get('product.product').search(self.cr,self.uid,[('id',">",0)])
		prods = {}
		if prd_ids:
			products = self.pool.get('product.product').browse(self.cr,self.uid,prd_ids)
			for p_id in products:
				prods.update({
						p_id.id:{
							'name':p_id.name,
							'code':p_id.default_code or "NO CODE DEFINED",
						}
					})
		return prods

	def _get_first_segment_info(self):
		prd_ids = self.pool.get('product.first.segment.code').search(self.cr, self.uid, [('id',">",0)])
		prods = {}
		if prd_ids:
			products = self.pool.get('product.first.segment.code').browse(self.cr, self.uid, prd_ids)
			for p_id in products:
				prods.update({
						p_id.code:{
							'name':p_id.name or "NO DESC DEFINED",
					}
					})
		return prods
	
	def _get_tracking_info(self):
		tracking_ids = self.pool.get('stock.tracking').search(self.cr,self.uid,[('id',">",0)])
		trackings = {}
		if tracking_ids:
			tracking_datas = self.pool.get('stock.tracking').browse(self.cr,self.uid,tracking_ids)
			for track in tracking_datas:
				trackings.update({
						track.id:{
							'name':track.name,
						}
					})
		return trackings

	def _get_uom_info(self):
		uom_ids = self.pool.get('product.uom').search(self.cr,self.uid,[('id',">",0)])
		uoms = {}
		if uom_ids:
			uom_datas = self.pool.get('product.uom').browse(self.cr,self.uid,uom_ids)
			for uom in uom_datas:
				uoms.update({
						uom.id:{
							'name':uom.name,
						}
					})
		return uoms

	def _get_location_info(self):
		loc_ids = self.pool.get('stock.location').search(self.cr,self.uid,[('id',">",0)])
		locs = {}
		if loc_ids:
			loc_datas = self.pool.get('stock.location').browse(self.cr,self.uid,loc_ids)
			for loc in loc_datas:
				locs.update({
						loc.id:{
							'name':loc.name,
						}
					})
		return locs

	def get_location(self,data):
		cr = self.cr
		uid = self.uid
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('scrap_location','=',False),\
				('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
		else:
			location_ids = data['location_force']
			location_ids_2 = self.pool.get('stock.location').search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids+=location_ids_2

		if location_ids:
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="location_id, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []

	# def get_location(self,data):
	# 	cr = self.cr
	# 	uid = self.uid
		
	# 	location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('scrap_location','=',False),\
	# 			('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
	# 	if location_ids:
	# 		all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="location_id, name asc")
	# 		return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
	# 	return []

	def _get_inventory_type(self,data):
		if data['goods_type']:
			return self.pool.get('goods.type').browse(self.cr,self.uid,data['goods_type'])
		return []

	def _get_date(self,data):
		as_on = data['as_on']
		if as_on:
			da = datetime.strptime(as_on,"%Y-%m-%d %H:%M:%S")
			return da.strftime("%d %B %Y")
		return "As On not Defined"

	def _get_stock(self,data,internal_type):
		cr = self.cr
		uid = self.uid
		location_ids = [loc.id for loc in self.get_location(data)]
		from_date = data.get('date_start',False)
		to_date = data.get('date_stop',False)
		ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=',internal_type.code)])
		# print "----------product---------------",internal_type.code,"--",ids
		context = {
			'location':location_ids,
			'from_date':from_date,
			'to_date':to_date,
			'states':['done'],
			"prodlot_id":False,
			"internal_type":internal_type.code,
		}
		#print "data--------->",context
		stock_lines = self.pool.get('product.product').get_product_stock_uncomputed_by_location(cr,uid,ids,context=context)
		return stock_lines or {}

	def _get_result(self,data,internal_type):
		# init basic var
		cr = self.cr
		uid = self.uid
		loc_pool = self.pool.get('stock.location')
		product_pool = self.pool.get('product.product')

		# init input parameters
		prev_date = (datetime.strptime(data['as_on'],"%Y-%m-%d %H:%M:%S") + relativedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")
		as_on = data['as_on']
		location_ids = [loc.id for loc in self.get_location(data)]
		product_ids = product_pool.search(cr,uid,[('internal_type','=',internal_type.code)])

		# init stock location
		loc_ids = loc_pool.search(cr,uid,[('id','in',location_ids),('usage','!=','view'),('usage','=','internal')])
		int_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','internal'),('usage','!=','view')])
		cust_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','customer'),('usage','!=','view')])
		supp_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','supplier'),('usage','!=','view')])
		prod_loc_ids = loc_pool.search(cr,uid,[('usage','=','production'),('usage','!=','view')])
		adj_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','inventory'),('usage','!=','view')])

		query_closing = "\
			SELECT\
				move_present.loc_id,\
				sum(move_present.qty) as qty_kg_pres,\
				sum(move_present.qty/181.44) as qty_bale_pres,\
				sum(move_present.product_uop_qty) as product_uop_qty_pres\
			FROM\
				(SELECT\
					location_dest_id as loc_id,\
					product_id,\
					product_uop,\
					sum(qty_kg) as qty,\
					sum(product_uop_qty) as product_uop_qty,\
					tracking_id\
				FROM\
					(SELECT\
						sm.location_dest_id,\
						sm.product_id,\
						sm.product_uop,\
						round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
						sm.product_uop_qty,\
						coalesce(sm.tracking_id,0) as tracking_id\
					FROM\
						stock_move sm\
						LEFT JOIN product_product pp ON sm.product_id = pp.id\
						LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id\
						LEFT JOIN product_uom pu_sm ON sm.product_uom = pu_sm.id\
						LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id\
						LEFT JOIN stock_location e on e.id = sm.location_dest_id\
					WHERE\
						e.usage='internal'\
						AND sm.product_id=any(array%s)\
						AND sm.state in ('done')\
						AND sm.date <= '%s'\
					ORDER BY sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop\
					) incoming\
				GROUP BY location_dest_id, product_id,product_uop,tracking_id\
				UNION ALL\
				SELECT\
					location_id as loc_id,\
					product_id,\
					product_uop,\
					-1*sum(qty_kg) as qty,\
					-1*sum(product_uop_qty) as product_uop_qty,\
					tracking_id\
				FROM\
					(SELECT\
						sm.location_id,\
						sm.product_id,\
						sm.product_uop, \
						round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
						sm.product_uop_qty,\
						coalesce(sm.tracking_id,0) as tracking_id\
					FROM\
						stock_move sm\
						LEFT JOIN product_product pp ON sm.product_id = pp.id\
						LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id\
						LEFT JOIN product_uom pu_sm on sm.product_uom = pu_sm.id\
						LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id\
						LEFT JOIN stock_location e on e.id = sm.location_id\
					WHERE\
						e.usage='internal'\
						AND sm.product_id=any(array%s)\
						AND sm.state in ('done')\
						AND sm.date <= '%s'\
					ORDER BY sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop\
					) outgoing\
				GROUP BY location_id, product_id,product_uop,tracking_id\
				) move_present\
			GROUP BY move_present.loc_id\
			ORDER BY move_present.loc_id\
			"

		query_summary_stock_status = "\
			SELECT\
				sl3.name as parent_loc_name,\
				sl3.sequence as parent_loc_seq,\
				present.loc_id,\
				sl4.sequence as loc_seq,\
				present.qty_kg_pres,\
				present.qty_bale_pres,\
				present.product_uop_qty_pres,\
				previous.qty_bale_pres as qty_bale_prev\
			FROM\
				("+query_closing+"\
				) present\
				LEFT JOIN\
					("+query_closing+"\
					) previous ON previous.loc_id = present.loc_id\
				LEFT JOIN stock_location sl1 ON sl1.id=present.loc_id\
				LEFT JOIN stock_location sl2 ON sl2.id=sl1.location_id\
				LEFT JOIN stock_location sl3 ON sl3.id=sl2.location_id\
				LEFT JOIN stock_location sl4 ON sl4.id=present.loc_id\
			ORDER BY sl3.sequence,sl4.sequence ASC \
			"
		query_summary_stock_status = query_summary_stock_status%(str(product_ids),as_on,str(product_ids),as_on,str(product_ids),prev_date,str(product_ids),prev_date)
		# print "query--------------------",query_summary_stock_status
		cr.execute(query_summary_stock_status)
		results = cr.dictfetchall()
		res_grouped = {}
		for res in results:
			key1=(res['parent_loc_name'],res['parent_loc_seq'])
			if key1 not in res_grouped:
				res_grouped.update({key1:[]})
			res_grouped[key1].append(res)
		
		return res_grouped

	def compute_fifo_simple_valuation(self,code,data):
		cr = self.cr
		uid = self.uid
		location_ids=[loc.id for loc in self.get_location(data)]
		if data['filter_type'] == 'date_period':
			from_date = data.get('start_date',False)
			to_date = data.get('end_date',False)
		else:
			from_date = data.get('prev_date',False)
			to_date = data.get('as_on',False)
		ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=',code)])
		context = {
			'location':location_ids,
			'from_date':from_date,
			'to_date':to_date,
			'states':['done'],
			"prodlot_id":False,
			"internal_type":code,
		}
		stock_lines, available_parent_loc, available_loc, available_prod = self.pool.get('product.product').get_stock_fifo_valuation_by_location(cr, uid, ids,context=context)
		return (stock_lines,available_parent_loc,available_loc,available_prod) or ()

	def get_valuation(self,code,data):
		valuations = False
		if code in ('Stores','Packing','Raw Material'):
			valuations = self.compute_fifo_simple_valuation(code,data)
		return valuations

class summary_stock_parser_xls(report_xls):
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

		prods = parser._get_product_info()
		trackings = parser._get_tracking_info()
		uoms = parser._get_uom_info()
		locs = parser._get_location_info()

		for inventory_type in parser._get_inventory_type(data): 
			ws = wb.add_sheet('Class - %s'%inventory_type.name,cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 1 # Landscape
			ws.fit_width_to_pages = 1
			ws.preview_magn = 100
			ws.normal_magn = 100
			ws.print_scaling=100
			ws.page_preview = False
			ws.set_fit_width_to_pages(1)
			
			##Penempatan untuk template rows
			title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			title_style_center				= xlwt.easyxf('font: height 220, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
			normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
			normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
			normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
			th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
			th_both_style_left 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left;')
			th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
			th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
			th_both_style_dashed 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom dashed',num_format_str='#,##0.00;-#,##0.00')
			th_both_style_dashed_bottom 	= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right; border:bottom dashed',num_format_str='#,##0.00;-#,##0.00')
			
			subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: top thin, bottom thin;')
			subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
			subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0.00;-#,##0.00')
			total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
			total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
			total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
			subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
			
			if inventory_type.code=='Finish':
				stock_summary = parser._get_result(data,inventory_type)	

				# Header of Ageing Summary Statement
				rowcount = 0
				ws.write_merge(rowcount,rowcount,0,1, c.name.upper(), title_style)
				ws.write(rowcount,2, "Fm")
				ws.write(rowcount,3, "MKT-SMG")
				ws.write_merge(rowcount,rowcount,5,6, "Circulation")
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,1, "%s STOCK SUMMARY"%inventory_type.name, title_style)
				ws.write(rowcount,2, "To")
				ws.write(rowcount,3, "MKT-JKT/BDG")
				# ws.write(rowcount,5, "Mr. Singh")
				ws.write(rowcount,5, "Mr. Sunil Kumar & Mr. Shailendra")
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,1, "AS ON : %s"%parser._get_date(data), title_style)
				ws.write(rowcount,2, "Cc")
				ws.write(rowcount,3, "PRES. DIR")
				ws.write(rowcount,5, "Mr. Ladha")
				ws.write(rowcount,6, "Mr. Yadav")
				rowcount+=2
				ws.write_merge(rowcount,rowcount+1,0,1, "Quality", th_both_style)
				ws.write_merge(rowcount,rowcount,2,4, "Present Stock", th_top_style)
				ws.write(rowcount+1,2, "BOX/BAG", th_bottom_style)
				ws.write(rowcount+1,3, "KGS", th_bottom_style)
				ws.write(rowcount+1,4, "BALES", th_bottom_style)
				ws.write_merge(rowcount,rowcount+1,5,5, "Previous\nBALES", th_both_style)
				
				rowcount+=2
				
				max_length_0 = len("%s STOCK SUMMARY"%inventory_type.name.upper())
				total_location={
					1:0.0,
					2:0.0,
					3:0.0,
					4:0.0,
					}
				total_parent = total_location.copy()
				grand_total = total_location.copy()

				for parent_loc in sorted(stock_summary.keys(),key=lambda k:k[1]):
					ws.write_merge(rowcount,rowcount,0,5,parent_loc[0],normal_bold_style_b)
					rowcount+=1
					for line in stock_summary[parent_loc]:
						rounder=line.get('product_uop_qty_pres',False) and round(line.get('product_uop_qty_pres',0.0),2) or 0					
						rounder_kg_pres=line.get('qty_kg_pres',False) and round(line.get('qty_kg_pres',0.0),2) or 0.0
						rounder_bales_pres=line.get('qty_bale_pres',False) and round(line.get('qty_bale_pres',0.0),2) or 0.0
						rounder_prev_bale=line.get('qty_bale_prev',False) and round(line.get('qty_bale_prev',0.0),2) or 0.0
						if rounder_bales_pres==0.0 and rounder_prev_bale==0.0:
							continue
						ws.write_merge(rowcount,rowcount,0,1, locs[line['loc_id']]['name'], normal_style)
						if len(locs[line['loc_id']]['name'])>max_length_0:
							max_length_0=len(locs[line['loc_id']]['name'])
						
						ws.write(rowcount,2, rounder !=0.0 and line.get('product_uop_qty_pres',0.0) or 0, normal_style_float_round)
						if rounder_bales_pres ==0.0:
							ws.write(rowcount,3, rounder_kg_pres !=0.0 and 0.0 or 0.0, normal_style_float)
						else:
							ws.write(rowcount,3, rounder_kg_pres !=0.0 and line.get('qty_kg_pres',0.0) or 0.0, normal_style_float)
							
						ws.write(rowcount,4, rounder_bales_pres !=0.0 and line.get('qty_bale_pres',0.0) or 0.0, normal_style_float)
						
						ws.write(rowcount,5, rounder !=0.0 and line.get('qty_bale_prev',0.0) or 0.0, normal_style_float)

						rowcount+=1
						total_parent.update({
							1:total_parent[1]+(line.get('product_uop_qty_pres',False) and line.get('product_uop_qty_pres',0.0) or 0.0),
							2:total_parent[2]+(rounder_bales_pres !=0.0 and line.get('qty_kg_pres',False) and line.get('qty_kg_pres',0.0) or 0.0) ,
							3:total_parent[3]+(line.get('qty_bale_pres',False) and line.get('qty_bale_pres',0.0) or 0.0) ,
							4:total_parent[4]+(line.get('qty_bale_prev',False) and line.get('qty_bale_prev',0.0) or 0.0),
						})
					ws.write_merge(rowcount,rowcount,0,1,"Total: ",subtotal_title_style)
					ws.write(rowcount,2,total_parent[1]!=0.0 and total_parent[1] or 0,subtotal_style2)
					ws.write(rowcount,3,total_parent[2]!=0.0 and total_parent[2] or 0.0,subtotal_style2)
					ws.write(rowcount,4,total_parent[3]!=0.0 and total_parent[3] or 0.0,subtotal_style2)
					ws.write(rowcount,5,total_parent[4]!=0.0 and total_parent[4] or 0.0,subtotal_style2)
					rowcount+=1
					grand_total.update({
						1:grand_total[1]+total_parent[1],
						2:grand_total[2]+total_parent[2],
						3:grand_total[3]+total_parent[3],
						4:grand_total[4]+total_parent[4],
					})
					for i in range(1,5):
						total_parent[i]=0.0
				ws.write_merge(rowcount,rowcount,0,1,"Grand Total:",subtotal_title_style)
				ws.write(rowcount,2,grand_total[1]!=0.0 and grand_total[1] or 0,subtotal_style2)
				ws.write(rowcount,3,grand_total[2]!=0.0 and grand_total[2] or 0.0,subtotal_style2)
				ws.write(rowcount,4,grand_total[3]!=0.0 and grand_total[3] or 0.0,subtotal_style2)
				ws.write(rowcount,5,grand_total[4]!=0.0 and grand_total[4] or 0.0,subtotal_style2)
				rowcount+=3

				ws.write(rowcount,0,'Godown Keeper :', normal_style)
				ws.write(rowcount,1,'Prepared By :', normal_style)
				ws.write(rowcount,3,'Approved By :', normal_style)
				rowcount+=3

				ws.write(rowcount,0,'( IN CHARGE )', normal_style)
				ws.write(rowcount,1,'( IN CHARGE )', normal_style)
				ws.write(rowcount,3,'( MANAGER )', normal_style)
				ws.col(0).width = 256*int(max_length_0)>=2304 and 256*int(max_length_0) or 2560
				# ws.col(1).width = 256*int(max_length_prod_name)>=3304 and 256*int(max_length_prod_name) or 3560
				ws.col(1).width = 256 * int(len("Prepared By :"))
				for i in range(1,5):
					ws.col(i+1).width = 256*len(str(round(grand_total[i],4)))>=2304 and 256*len(str(round(grand_total[i],4))) or 2560
				if int(len("Approved By :")) > int(len(str(round(grand_total[2],4)))):
					ws.col(3).width = 256 * int(len("Approved By :"))

			elif inventory_type.code in ('Stores','Packing'):
				call_valuation = parser.get_valuation(inventory_type.code,data)
				try:
					stocks,available_parent_loc,available_loc,available_prod = call_valuation
				except:
					stock, available_parent_loc, available_loc, available_prod ={}, [], [], []
				max_width_col = {0:5.0, 1:8.0, 2:4.0}
				ws.write_merge(0,0,0,16, c.name, title_style_center)
				ws.write_merge(1,1,0,16, "SUMMMARY STOCK STATUS - %s"%parser._get_mode(data), title_style_center)
				ws.write_merge(2,2,0,16, "Class ID - %s"%inventory_type.name, title_style_center)
				ws.write_merge(3,3,0,16, "As on - %s"%parser._get_date_range(data), title_style_center)
				
				ws.write_merge(5,5,0,1, "Inventory", th_top_style)
				ws.write(6,0, "Item Code\nFirst Segment", th_bottom_style)
				ws.write(6,1, "Description", th_bottom_style)
				ws.write_merge(5,6,2,2, "UoM", th_both_style)

				ws.write_merge(5,5,3,4, "Opening", th_top_style)
				ws.write_merge(5,5,5,6, "Receipt", th_top_style)
				ws.write_merge(5,5,7,8, "Return", th_top_style)
				ws.write_merge(5,5,9,10, "Issue", th_top_style)
				ws.write_merge(5,5,11,12, "Return", th_top_style)
				ws.write_merge(5,5,13,14, "Adjustment", th_top_style)
				ws.write_merge(5,5,15,16, "Closing", th_top_style)
				
				for cols in range(3,17):
					if cols%2==0:
						ws.write(6, cols, "Amount", th_both_style)
					elif cols%2!=0:
						ws.write(6, cols, "Qty", th_both_style)
				
				rowcount=7
				locations = parser.get_location(data)
				product_info = parser._get_product_info()
				first_segment = parser._get_first_segment_info()
				grand_total = {}
				for i in range(3,17):
					grand_total.update({i:0.0})
				for parent in available_parent_loc:
					totalparent = {}
					for i in range(3,17):
						totalparent.update({i:0.0})
					if stocks.get(parent,False):
						ws.write_merge(rowcount,rowcount,0,2, parent, th_both_style_left)
						rowcount+=2
						for locs in sorted(locations, key = lambda x: x.sequence and x.sequence or x.id):
							location = locs.id
							total_location = {}
							for i in range(3,17):
								total_location.update({i:0.0})
							if stocks[parent].get(location, False):
								ws.write_merge(rowcount,rowcount,0,2, locs.name, th_both_style_left)
								rowcount+=2
								totalmbc = {}
								for mbc in sorted(stocks[parent][location].keys()):
									for i in range(3,17):
										totalmbc.update({i:0.0})
									if stocks[parent][location].get(mbc,False):
										pname_dict = {}
										pid_dict = {}
										for dummy_pname_dict in stocks[parent][location][mbc]:
											pname_dict.update({
												(dummy_pname_dict, product_info[dummy_pname_dict]['code']) : dummy_pname_dict
												})
										for product in sorted(pname_dict.keys(), key=lambda p : p[1]):
											for track_id in stocks[parent][location][mbc][pname_dict[product]].keys():
												for uom_id in stocks[parent][location][mbc][pname_dict[product]][track_id].keys():
													line = stocks[parent][location][mbc][pname_dict[product]][track_id][uom_id]
													cols = {}
													cols.update({
														0:product_info[pname_dict[product]]['code'],
														1:product_info[pname_dict[product]]['name'],
														2:uoms[uom_id]['name'],
														3:('opening' in line.keys()) and line['opening'].get("uom_qty",0.0) or 0.0,
														4:('opening' in line.keys()) and line['opening'].get("uom_qty_value",0.0) or 0.0,
														5:('receipt' in line.keys()) and line['receipt'].get("uom_qty",0.0) or 0.0,
														6:('receipt' in line.keys()) and line['receipt'].get("uom_qty_value",0.0) or 0.0,
														7:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty",0.0) or 0.0,
														8:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty_value",0.0) or 0.0,
														9:('issue' in line.keys()) and line['issue'].get("uom_qty",0.0) or 0.0,
														10:('issue' in line.keys()) and line['issue'].get("uom_qty_value",0.0) or 0.0,
														11:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty",0.0) or 0.0,
														12:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty_value",0.0) or 0.0,
														13:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty",0.0) or 0.0,
														14:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty_value",0.0) or 0.0,
														15:('closing' in line.keys()) and line['closing'].get("uom_qty",0.0) or 0.0,
														16:('closing' in line.keys()) and line['closing'].get("uom_qty_value",0.0) or 0.0,
														})

													if cols[3]<0.0001 and cols[5]<0.0001 and cols[7]<0.0001 and cols[9]<0.0001 and cols[11]<0.0001 and cols[13]<0.0001 and cols[15]<0.0001:
														continue


													for i in range(3,17):
														totalmbc.update({
															i:totalmbc.get(i,0.0)+cols[i],
															})
													
													for i in range(3,17):
														total_location.update({
															i:total_location.get(i,0.0)+cols[i],
															})
														
													for i in range(3,17):
														totalparent.update({
															i:totalparent.get(i,0.0)+cols[i],
															})

										ws.write(rowcount,0,str(mbc), normal_style)
										desc = str(first_segment.get(mbc,False) and first_segment.get(mbc,False).get('name',False) and first_segment[mbc]['name'] or "Not Found Desc For %s"%str(mbc))
										ws.write(rowcount,1, desc, normal_style)
										if desc and len(desc) > max_width_col[1]:
											max_width_col[1] = len(desc)
										ws.write(rowcount,2, "" , normal_style)
										for i in range(3,17):
											ws.write(rowcount, i, totalmbc.get(i,0.0), normal_style_float)
										rowcount+=1

								ws.write_merge(rowcount,rowcount,0,2,"*** Total Location "+str(locs.name)+" ***", th_both_style_dashed_bottom)
								for i in range(3,17):
									ws.write(rowcount, i, total_location.get(i,0.0), th_both_style_dashed_bottom)
								rowcount+=1	
						
						ws.write_merge(rowcount,rowcount,0,2,"*** Total "+str(parent)+" ***", th_both_style_dashed_bottom)
						for i in range(3,17):
							ws.write(rowcount,i,totalparent.get(i,0.0),th_both_style_dashed_bottom)
							grand_total[i]+=totalparent.get(i,0.0)
						rowcount+=1
				
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,2,"*** Grand Total ***", th_both_style_dashed_bottom)
				for i in range(3,17):
					ws.write(rowcount,i,grand_total.get(i,0.0),th_both_style_dashed_bottom)

				for c in range(0,3):
					ws.col(c).width = 256 * int(max_width_col[c]*1.4)
				

		pass

report_sxw.report_sxw('report.summary.stock.report.pdf','summary.stock.wizard', 'addons/ad_stock_report/report/summary_stock_report.mako',
							parser=summary_stock_parser)
summary_stock_parser_xls('report.summary.stock.report.xls','summary.stock.wizard', 'addons/ad_stock_report/report/summary_stock_report.mako',
						parser=summary_stock_parser)