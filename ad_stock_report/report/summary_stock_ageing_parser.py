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

class summary_stock_ageing_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(summary_stock_ageing_parser, self).__init__(cr, uid, name, context=context)
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
			location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('scrap_location','=',False),\
				('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
		else:
			location_ids = data['location_force']
		# if data['location_exception']:
		# 	exception_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', data['location_exception'])])
		# 	location_ids = list(set(location_ids)-set(exception_location_ids)-set(data['location_exception']))
		if location_ids:
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="location_id, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []

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
		from_date = data.get('prev_date',False)
		to_date = data.get('as_on',False)
		ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=',internal_type.code)])
		context = {
			'location':location_ids,
			'from_date':from_date,
			'to_date':to_date,
			'states':['done'],
			"prodlot_id":False,
			"internal_type":internal_type.code,
		}
		stock_lines = self.pool.get('product.product').get_product_stock_uncomputed_by_location(cr,uid,ids,context=context)
		return stock_lines or {}

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

	def _get_product_ageing(self,data,internal_type):
		# init basic var
		cr = self.cr
		uid = self.uid
		loc_pool = self.pool.get('stock.location')
		product_pool = self.pool.get('product.product')

		# init input parameters
		date_start = (datetime.strptime(data['as_on'],"%Y-%m-%d %H:%M:%S") + relativedelta(years=-2)).strftime("%Y-%m-%d %H:%M:%S")
		date_end = data['as_on']
		period_length = data['period_length']
		location_ids = [loc.id for loc in self.get_location(data)]
		product_ids = product_pool.search(cr,uid,[('internal_type','=',internal_type.code)])

		# init stock location
		loc_ids = loc_pool.search(cr,uid,[('id','in',location_ids),('usage','!=','view'),('usage','=','internal')])
		int_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','internal'),('usage','!=','view')])
		cust_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','customer'),('usage','!=','view')])
		supp_loc_ids = loc_pool.search(cr,uid,[('child_ids','=',False),('usage','=','supplier'),('usage','!=','view')])
		prod_loc_ids = loc_pool.search(cr,uid,[('usage','=','production'),('usage','!=','view')])
		adj_loc_ids = loc_pool.search(cr,uid,[('usage','=','inventory')])
		aged_products_grouped = {}
		if internal_type.code=='Finish':
			query_incoming = "\
				SELECT\
					incoming.loc_id as loc_id,\
					incoming.product_id,\
					incoming.qty,\
					sum(incoming_cum.qty) as qty_cumulative,\
					incoming.product_uop_qty,\
					sum(incoming_cum.product_uop_qty) as product_uop_qty_cumulative,\
					incoming.tracking_id,\
					incoming.date as date\
				FROM\
					(SELECT\
						incoming1.location_dest_id as loc_id,\
						incoming1.product_id,\
						sum(incoming1.qty_kg) as qty,\
						sum(incoming1.product_uop_qty) as product_uop_qty,\
						incoming1.tracking_id,\
						incoming1.sdate as date\
					FROM\
						(\
						SELECT\
							incoming1_a.location_dest_id, incoming1_a.product_id, incoming1_a.product_uop,\
							round(round(incoming1_a.product_qty/incoming1_d.factor,4)*incoming1_e.factor,4) as qty_kg,\
							incoming1_a.product_uop_qty, coalesce(incoming1_a.tracking_id,0) as tracking_id, to_char(incoming1_a.date,'YYYY-MM-DD') as sdate\
						FROM\
							stock_move incoming1_a\
							left join product_product incoming1_b on incoming1_b.id = incoming1_a.product_id\
							left join product_template incoming1_c on incoming1_c.id = incoming1_b.product_tmpl_id\
							left join product_uom incoming1_d on incoming1_d.id = incoming1_a.product_uom\
							left join product_uom incoming1_e on incoming1_e.id = incoming1_c.uom_id\
						WHERE\
							incoming1_a.location_dest_id = any(array"+str(loc_ids)+") and incoming1_a.location_id = any(array"+str(prod_loc_ids+supp_loc_ids+cust_loc_ids+int_loc_ids+adj_loc_ids)+")\
							and incoming1_a.product_id=any(array"+str(product_ids)+") and incoming1_a.state in ('done')\
							and incoming1_a.date >= '"+date_start+"' and incoming1_a.date <= '"+date_end+"'\
						) incoming1\
					GROUP BY\
						loc_id,\
						incoming1.product_id,\
						incoming1.tracking_id,\
						date\
					) incoming\
					INNER JOIN\
						(SELECT\
							incoming_cum1.location_dest_id as loc_id,\
							incoming_cum1.product_id,\
							sum(incoming_cum1.qty_kg) as qty,\
							sum(incoming_cum1.product_uop_qty) as product_uop_qty,\
							incoming_cum1.tracking_id,\
							incoming_cum1.sdate as date\
						FROM\
							(\
							SELECT\
								incoming_cum1_a.location_dest_id, incoming_cum1_a.product_id, incoming_cum1_a.product_uop,\
								round(round(incoming_cum1_a.product_qty/incoming_cum1_d.factor,4)*incoming_cum1_e.factor,4) as qty_kg,\
								incoming_cum1_a.product_uop_qty, coalesce(incoming_cum1_a.tracking_id,0) as tracking_id, to_char(incoming_cum1_a.date,'YYYY-MM-DD') as sdate\
							FROM\
								stock_move incoming_cum1_a\
								left join product_product incoming_cum1_b on incoming_cum1_b.id = incoming_cum1_a.product_id\
								left join product_template incoming_cum1_c on incoming_cum1_c.id = incoming_cum1_b.product_tmpl_id\
								left join product_uom incoming_cum1_d on incoming_cum1_d.id = incoming_cum1_a.product_uom\
								left join product_uom incoming_cum1_e on incoming_cum1_e.id = incoming_cum1_c.uom_id\
							WHERE\
								incoming_cum1_a.location_dest_id = any(array"+str(loc_ids)+") and incoming_cum1_a.location_id = any(array"+str(prod_loc_ids+supp_loc_ids+cust_loc_ids+int_loc_ids+adj_loc_ids)+")\
								and incoming_cum1_a.product_id=any(array"+str(product_ids)+") and incoming_cum1_a.state in ('done')\
								and incoming_cum1_a.date >= '"+date_start+"' and incoming_cum1_a.date <= '"+date_end+"'\
							) incoming_cum1\
						GROUP BY\
							loc_id,\
							incoming_cum1.product_id,\
							incoming_cum1.tracking_id,\
							date\
						) incoming_cum ON incoming_cum.loc_id=incoming.loc_id and incoming_cum.product_id=incoming.product_id and incoming_cum.tracking_id=incoming.tracking_id and incoming_cum.date<=incoming.date\
				GROUP BY\
					incoming.loc_id,\
					incoming.product_id,\
					incoming.qty,\
					incoming.product_uop_qty,\
					incoming.tracking_id,\
					incoming.date\
				ORDER BY\
					incoming.loc_id,\
					incoming.product_id,\
					incoming.tracking_id,\
					incoming.date ASC\
				"

			query_outgoing = "\
				SELECT\
					incoming.location_id as loc_id,\
					incoming.product_id,\
					sum(incoming.qty_kg) as qty,\
					sum(incoming.product_uop_qty) as product_uop_qty,\
					incoming.tracking_id\
				FROM\
					(\
					SELECT\
						incoming_a.location_id, incoming_a.product_id, incoming_a.product_uop,\
						round(round(incoming_a.product_qty/incoming_d.factor,4)*incoming_e.factor,4) as qty_kg,\
						incoming_a.product_uop_qty, coalesce(incoming_a.tracking_id,0) as tracking_id, to_char(incoming_a.date,'YYYY-MM-DD') as sdate\
					FROM\
						stock_move incoming_a\
						left join product_product incoming_b on incoming_b.id = incoming_a.product_id\
						left join product_template incoming_c on incoming_c.id = incoming_b.product_tmpl_id\
						left join product_uom incoming_d on incoming_d.id = incoming_a.product_uom\
						left join product_uom incoming_e on incoming_e.id = incoming_c.uom_id\
					WHERE\
						incoming_a.location_id = any(array"+str(loc_ids)+") and incoming_a.location_dest_id = any(array"+str(prod_loc_ids+supp_loc_ids+cust_loc_ids+int_loc_ids+adj_loc_ids)+")\
						and incoming_a.product_id=any(array"+str(product_ids)+") and incoming_a.state in ('done')\
						and incoming_a.date >= '"+date_start+"' and incoming_a.date <= '"+date_end+"'\
					) incoming\
				GROUP BY\
					loc_id,\
					incoming.product_id,\
					incoming.tracking_id\
				ORDER BY\
					loc_id,\
					incoming.product_id,\
					incoming.tracking_id ASC\
				"

			query_stock_status_date_wise = "\
				SELECT\
					c3.name as parent_loc_name,\
					c3.sequence as parent_loc_seq,\
					detail_incoming.loc_id as loc_id,\
					c1.name as loc_id_name,\
					c1.sequence as loc_id_seq,\
					detail_incoming.product_id,\
					a.wax,\
					a.sd_type,\
					a.count,\
					b.name as blend,\
					detail_incoming.qty as in_qty_kgs,\
					detail_incoming.qty_cumulative,\
					coalesce(total_outgoing.qty,0) as total_out_qty_kgs,\
					(detail_incoming.qty_cumulative-coalesce(total_outgoing.qty,0)) as selisih_qty_kgs,\
					detail_incoming.product_uop_qty as in_uop_qty,\
					detail_incoming.product_uop_qty_cumulative,\
					coalesce(total_outgoing.product_uop_qty,0) as total_in_uop_qty,\
					(detail_incoming.product_uop_qty_cumulative-coalesce(total_outgoing.product_uop_qty,0)) as selisih_uop_qty,\
					detail_incoming.tracking_id,\
					detail_incoming.date as date\
				FROM ("+query_incoming+"\
					) detail_incoming\
					LEFT JOIN ("+query_outgoing+"\
						) total_outgoing ON\
						detail_incoming.loc_id=total_outgoing.loc_id \
						and detail_incoming.product_id=total_outgoing.product_id \
						and detail_incoming.tracking_id=total_outgoing.tracking_id\
					LEFT JOIN product_product a ON a.id=detail_incoming.product_id\
					LEFT JOIN mrp_blend_code b ON b.id=a.blend_code\
					LEFT JOIN stock_location c1 ON c1.id=detail_incoming.loc_id\
					LEFT JOIN stock_location c2 ON c2.id=c1.location_id\
					LEFT JOIN stock_location c3 ON c3.id=c2.location_id\
				WHERE\
					((detail_incoming.qty_cumulative-coalesce(total_outgoing.qty,0))>0 or (detail_incoming.product_uop_qty_cumulative-coalesce(total_outgoing.product_uop_qty,0))>0)\
					and detail_incoming.qty_cumulative-coalesce(total_outgoing.qty,0)>=1\
				ORDER BY\
					detail_incoming.loc_id, detail_incoming.product_id, detail_incoming.tracking_id, detail_incoming.date ASC"
			cr.execute(query_stock_status_date_wise)
			result_stock_status = cr.dictfetchall()
			res_grouped = {}
			for res in result_stock_status:
				key = "%s|%s|%s"%(str(res['loc_id']),str(res['product_id']),str(res['tracking_id']))
				if key not in res_grouped:
					res_grouped.update({key:[]})
				res_grouped[key].append(res)

			aged_products = []
			for key in res_grouped.keys():
				x, y = 0, 0
				for res in res_grouped[key]:
					x += (datetime.strptime(data['as_on'],"%Y-%m-%d %H:%M:%S")-datetime.strptime(res['date'],"%Y-%m-%d")).days * res['in_qty_kgs']
					y += res['in_qty_kgs']
				res.update({'age':(x/y)})
				aged_products.append(res)

			aged_products_grouped = {}
			for res in aged_products:
				key1=(res['parent_loc_name'],res['parent_loc_seq'])
				if key1 not in aged_products_grouped:
					aged_products_grouped.update({key1:{}})
				key2=(res['loc_id'],res['loc_id_seq'])
				if key2 not in aged_products_grouped[key1]:
					aged_products_grouped[key1].update({key2:{}})
				key3=res['blend']
				if key3 not in aged_products_grouped[key1][key2]:
					aged_products_grouped[key1][key2].update({key3:{}})
				key4=res['count']
				if key4 not in aged_products_grouped[key1][key2][key3]:
					aged_products_grouped[key1][key2][key3].update({key4:{}})
				key5=res['sd_type']
				if key5 not in aged_products_grouped[key1][key2][key3][key4]:
					aged_products_grouped[key1][key2][key3][key4].update({key5:{}})
				key6=res['wax']
				if key6 not in aged_products_grouped[key1][key2][key3][key4][key5]:
					aged_products_grouped[key1][key2][key3][key4][key5].update({key6:{}})
				key7=res['product_id']
				if key7 not in aged_products_grouped[key1][key2][key3][key4][key5][key6]:
					aged_products_grouped[key1][key2][key3][key4][key5][key6].update({key7:{}})
				key8=res['tracking_id']
				if key8 not in aged_products_grouped[key1][key2][key3][key4][key5][key6][key7]:
					aged_products_grouped[key1][key2][key3][key4][key5][key6][key7].update({key8:[]})

				aged_products_grouped[key1][key2][key3][key4][key5][key6][key7][key8].append(res)
		else:
			query = "\
				SELECT\
					ageing.*,\
					sl3.name as parent_loc_name,\
					sl3.sequence as parent_loc_seq,\
					sl1.name as loc_id_name,\
					sl1.sequence as loc_id_seq,\
					pp.wax,\
					pp.sd_type,\
					pp.count,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' \
					end) as blend,\
					pp.default_code, \
					pt.name as prod_name \
				FROM get_ageing_fifo(to_timestamp('"+date_end+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(product_ids)+",array"+str(loc_ids)+",array"+str(loc_ids)+","+str(period_length)+") ageing\
					LEFT JOIN product_product pp ON pp.id=ageing.prod_id\
					LEFT JOIN product_template pt ON pt.id=pp.product_tmpl_id\
					LEFT JOIN mrp_blend_code mbc ON mbc.id=pp.blend_code\
					LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					LEFT JOIN stock_location sl1 ON sl1.id=ageing.loc_id\
					LEFT JOIN stock_location sl2 ON sl2.id=sl1.location_id\
					LEFT JOIN stock_location sl3 ON sl3.id=sl2.location_id\
				ORDER BY\
					ageing.loc_id, ageing.prod_id, ageing.track_id ASC"
			cr.execute(query)
			result_stock_status = cr.dictfetchall()
			aged_products_grouped = {}
			for res in result_stock_status:
				key1=(res['parent_loc_name'],res['parent_loc_seq'])
				if key1 not in aged_products_grouped:
					aged_products_grouped.update({key1:{}})
				key2=(res['loc_id'],res['loc_id_seq'])
				if key2 not in aged_products_grouped[key1]:
					aged_products_grouped[key1].update({key2:{}})
				key3=res['blend']
				if key3 not in aged_products_grouped[key1][key2]:
					aged_products_grouped[key1][key2].update({key3:{}})
				key4=res['prod_id']
				if key4 not in aged_products_grouped[key1][key2][key3]:
					aged_products_grouped[key1][key2][key3].update({key4:{}})
				key5=res['track_id']
				if key5 not in aged_products_grouped[key1][key2][key3][key4]:
					aged_products_grouped[key1][key2][key3][key4].update({key5:{}})
				key6=res['uom']
				if key6 not in aged_products_grouped[key1][key2][key3][key4][key5]:
					aged_products_grouped[key1][key2][key3][key4][key5].update({key6:{}})
				key7=res['uom']
				if key7 not in aged_products_grouped[key1][key2][key3][key4][key5][key6]:
					aged_products_grouped[key1][key2][key3][key4][key5][key6].update({key7:[]})
				
				aged_products_grouped[key1][key2][key3][key4][key5][key6][key7].append(res)
		
		return aged_products_grouped

class summary_stock_ageing_parser_xls(report_xls):
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
		blends = parser._get_first_segment_info()
		period_length = data['period_length']

		for inventory_type in parser._get_inventory_type(data): 
			# stock_lines,available_parent,location_line,product_line,track_lines,uop_lines = parser._get_stock(data,inventory_type)
			stock_lines_aged = parser._get_product_ageing(data,inventory_type)
			
			ws = wb.add_sheet('Class - %s'%inventory_type.name,cell_overwrite_ok=True)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 1 # Landscape
			ws.fit_width_to_pages = 1
			ws.preview_magn = 75
			ws.normal_magn = 75
			ws.print_scaling=75
			ws.page_preview = False
			ws.set_fit_width_to_pages(1)
			##Penempatan untuk template rows
			# title_style 					= xlwt.easyxf('font: height 220, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
			title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
			normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
			normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
			normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
			normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
			normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
			th_style 						= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center;')
			th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
			th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
			th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
			
			subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
			subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
			subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
			total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
			total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
			total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
			subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')

			if inventory_type.code == 'Finish':
				# Header of Ageing Summary Statement
				rowcount = 0
				ws.write_merge(rowcount,rowcount,0,6, c.name.upper(), title_style)
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,6, "%s AGEING SUMMARY STATEMENT"%inventory_type.name, title_style)
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,6, "AS ON : %s"%parser._get_date(data), title_style)
				rowcount+=3
				ws.write_merge(rowcount,rowcount,0,1, "Inventory", th_top_style)
				ws.write_merge(rowcount,rowcount+1,2,2, "Lot No.", th_both_style)
				# ws.write_merge(rowcount,rowcount+1,3,3, "UoP", th_both_style)
				
				ws.write_merge(rowcount,rowcount,3,5, "Closing", th_top_style)
				ws.write_merge(rowcount,rowcount+1,6,6, "Ageing\n(Days)", th_both_style)
				
				rowcount+=1
				
				ws.write(rowcount,0, "ID", th_bottom_style)
				ws.write(rowcount,1, "Name", th_bottom_style)
				rowcount+=1
				
				ws.write(rowcount-1,3,"2nd Qty",th_both_style)
				ws.write(rowcount-1,4,"Kgs",th_both_style)
				ws.write(rowcount-1,5,"Bales",th_both_style)

				rowcount+=1
				max_length_loc=0
				max_length_location = len("%s STOCK SUMMARY"%inventory_type.name.upper())
				max_length_prod_code = 0
				max_length_prod_name = 0
				max_length_uom_name = 0
				total_location={
					1:0.0,
					2:0.0,
					3:0.0,
					}
				total_blend = total_location.copy()
				total_wax = total_location.copy()
				total_sd = total_location.copy()
				total_ct = total_location.copy()
				total_parent = total_location.copy()
				grand_total = total_location.copy()

				for parent_loc,parent_loc_seq in sorted(stock_lines_aged.keys(),key=lambda pk:pk[1]):
					for loc_id,loc_seq in sorted(stock_lines_aged[parent_loc,parent_loc_seq].keys(),key=lambda lk:lk[1]):
						ws.write_merge(rowcount,rowcount,0,6,locs[loc_id]['name'],normal_bold_style_b)
						rowcount+=1
						for blend in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq].keys()):
							for count in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend].keys()):
								for sd in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend][count].keys()):
									for wax in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend][count][sd].keys()):
										for pl in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend][count][sd][wax].keys()):
											for tl in sorted(stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend][count][sd][wax][pl].keys()):
												for line in stock_lines_aged[parent_loc,parent_loc_seq][loc_id,loc_seq][blend][count][sd][wax][pl][tl]:
													ws.write(rowcount,0, prods[pl]['code'], normal_style)
													ws.write(rowcount,1, prods[pl]['name'], normal_style)
													if len(prods[pl]['name'])>max_length_prod_name:
														max_length_prod_name=len(prods[pl]['name'])
													if len(prods[pl]['code'])>max_length_prod_code:
														max_length_prod_code=len(prods[pl]['code'])

													if tl != 0:
														ws.write(rowcount,2, trackings[tl]['name'], normal_style)
													else:
														ws.write(rowcount,2, "Undef.Lot", normal_style)
													try:
														rounder=round(line['selisih_uop_qty']) or 0.0
														ws.write(rowcount,3, rounder !=0.0 and line['selisih_uop_qty'] or "", normal_style_float_round)
													except:
														ws.write(rowcount,3, "", normal_style)
													try:
														rounder=round(line['selisih_qty_kgs'],2) or 0.0
														ws.write(rowcount,4, rounder !=0.0 and line['selisih_qty_kgs'] or "", normal_style_float)
													except:
														ws.write(rowcount,4, "", normal_style)
													try:
														rounder=round(line['selisih_qty_kgs']/181.44,2) or 0.0
														ws.write(rowcount,5, rounder !=0.0 and line['selisih_qty_kgs']/181.44 or "", normal_style_float)
													except:
														ws.write(rowcount,5, "", normal_style)
													try:
														# rounder=round(line['age']) or 0.0
														# ws.write(rowcount,6, rounder !=0.0 and line['age'] or 0, normal_style_float_round)
														ws.write(rowcount,6, line['age'], normal_style_float_round)
													except:
														ws.write(rowcount,6, 0, normal_style)
													rowcount+=1
													total_wax.update({
															1:total_wax[1]+line['selisih_uop_qty'],
															2:total_wax[2]+line['selisih_qty_kgs'],
															3:total_wax[3]+(line['selisih_qty_kgs']/181.44),
														})
										# ws.write_merge(rowcount,rowcount,1,2,"Subtotal:",subtotal_title_style)
										# ws.write(rowcount,3,total_wax[1]!=0.0 and total_wax[1] or '',subtotal_style2)
										# ws.write(rowcount,4,total_wax[2]!=0.0 and total_wax[2] or '',subtotal_style2)
										# ws.write(rowcount,5,total_wax[3]!=0.0 and total_wax[3] or '',subtotal_style2)
										# ws.write(rowcount,6,'',subtotal_style2)
										# rowcount+=1
										total_blend.update({
											1:total_blend[1]+total_wax[1],
											2:total_blend[2]+total_wax[2],
											3:total_blend[3]+total_wax[3],
										})
										for i in range(1,4):
											total_wax[i]=0.0

							ws.write_merge(rowcount,rowcount,1,2,"Total Blend: %s"%blend,subtotal_title_style)
							ws.write(rowcount,3,total_blend[1]!=0.0 and total_blend[1] or '',subtotal_style2)
							ws.write(rowcount,4,total_blend[2]!=0.0 and total_blend[2] or '',subtotal_style2)
							ws.write(rowcount,5,total_blend[3]!=0.0 and total_blend[3] or '',subtotal_style2)
							ws.write(rowcount,6,'',subtotal_style2)
							rowcount+=1
							total_location.update({
								1:total_location[1]+total_blend[1],
								2:total_location[2]+total_blend[2],
								3:total_location[3]+total_blend[3],
							})
							for i in range(1,4):
								total_blend[i]=0.0

						ws.write_merge(rowcount,rowcount,0,2,"Total Location: %s"%locs[loc_id]['name'],subtotal_title_style)
						ws.write(rowcount,3,total_location[1]!=0.0 and total_location[1] or '',subtotal_style2)
						ws.write(rowcount,4,total_location[2]!=0.0 and total_location[2] or '',subtotal_style2)
						ws.write(rowcount,5,total_location[3]!=0.0 and total_location[3] or '',subtotal_style2)
						ws.write(rowcount,6,'',subtotal_style2)
						rowcount+=1
						total_parent.update({
							1:total_parent[1]+total_location[1],
							2:total_parent[2]+total_location[2],
							3:total_parent[3]+total_location[3],
						})
						for i in range(1,4):
							total_location[i]=0.0

					# ws.write_merge(rowcount,rowcount,0,2,"Total Parent Location: %s"%parent_loc,subtotal_title_style)
					# ws.write(rowcount,3,total_parent[1]!=0.0 and total_parent[1] or '',subtotal_style2)
					# ws.write(rowcount,4,total_parent[2]!=0.0 and total_parent[2] or '',subtotal_style2)
					# ws.write(rowcount,5,total_parent[3]!=0.0 and total_parent[3] or '',subtotal_style2)
					# ws.write(rowcount,6,'',subtotal_style2)
					# rowcount+=1
					grand_total.update({
						1:grand_total[1]+total_parent[1],
						2:grand_total[2]+total_parent[2],
						3:grand_total[3]+total_parent[3],
					})
					for i in range(1,4):
						total_parent[i]=0.0
				# ws.write_merge(rowcount,rowcount,0,2,"Grand Total:",subtotal_title_style)
				# ws.write(rowcount,3,grand_total[1]!=0.0 and grand_total[1] or '',subtotal_style2)
				# ws.write(rowcount,4,grand_total[2]!=0.0 and grand_total[2] or '',subtotal_style2)
				# ws.write(rowcount,5,grand_total[3]!=0.0 and grand_total[3] or '',subtotal_style2)
				# ws.write(rowcount,6,'',subtotal_style2)
				# rowcount+=1
			
				ws.col(0).width = 256*int(max_length_prod_code)>=2304 and 256*int(max_length_prod_code) or 2560
				# ws.col(1).width = 256*int(max_length_prod_name)>=2304 and 256*int(max_length_prod_name) or 2560
				ws.col(1).width = 256*int(max_length_prod_name)>=3304 and 256*int(max_length_prod_name) or 3560
				for i in range(1,4):
					ws.col(2+i).width = 256*len(str(round(grand_total[i],4)))>=2304 and 256*len(str(round(grand_total[i],4))) or 2560
			else:
				# Header of Ageing Summary Statement
				ws.portrait = 0
				rowcount = 0
				ws.write_merge(rowcount,rowcount,0,12, c.name.upper(), title_style)
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,12, "Summary Stock Ageing Report - %s"%inventory_type.name, title_style)
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,12, "AS ON : %s"%parser._get_date(data), title_style)
				rowcount+=2

				ws.write_merge(rowcount,rowcount+2,0,0, "Item Code\nFirst Segment", th_both_style)
				ws.write_merge(rowcount,rowcount+2,1,1, "Description", th_both_style)
				ws.write_merge(rowcount,rowcount+2,2,2, "Unit of\nMeasure", th_both_style)
				ws.write_merge(rowcount,rowcount+1,3,4, "Closing Qty", th_top_style)
				ws.write_merge(rowcount, rowcount, 5, 12, "Age - Days", th_top_style)
				ws.write_merge(rowcount+1,rowcount+1, 5, 6, "0 - "+str(period_length), th_style)
				ws.write_merge(rowcount+1,rowcount+1, 7, 8, str(period_length+1)+" - "+str(period_length*2), th_style)
				ws.write_merge(rowcount+1,rowcount+1, 9, 10, str((period_length*2)+1)+" - "+str(period_length*3), th_style)
				ws.write_merge(rowcount+1,rowcount+1, 11, 12, ">"+str(period_length*3), th_style)
				ws.write(rowcount+2, 3, "Quantity", th_bottom_style)
				ws.write(rowcount+2, 4, "Value", th_bottom_style)
				ws.write(rowcount+2, 5, "Quantity", th_bottom_style)
				ws.write(rowcount+2, 6, "Value", th_bottom_style)
				ws.write(rowcount+2, 7, "Quantity", th_bottom_style)
				ws.write(rowcount+2, 8, "Value", th_bottom_style)
				ws.write(rowcount+2, 9, "Quantity", th_bottom_style)
				ws.write(rowcount+2, 10, "Value", th_bottom_style)
				ws.write(rowcount+2, 11, "Quantity", th_bottom_style)
				ws.write(rowcount+2, 12, "Value", th_bottom_style)
				rowcount+=3
				grand_total = {3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0}
				for parent_loc in sorted(stock_lines_aged.keys(), key=lambda x:(x[1] and x[1] or x[0])):
					for loc_id in sorted(stock_lines_aged[parent_loc].keys(), key=lambda y:(y[1] and y[1] or y[0])):
						subtotal_loc = {3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0}
						ws.write_merge(rowcount,rowcount,0,12, locs[loc_id[0]]['name'], normal_bold_style_b)
						rowcount+=1
						for blend in sorted(stock_lines_aged[parent_loc][loc_id].keys()):
							subtotal_blend = {3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0}
							for product in sorted(stock_lines_aged[parent_loc][loc_id][blend].keys()):
								for tracking in sorted(stock_lines_aged[parent_loc][loc_id][blend][product].keys()):
									for uop_id in sorted(stock_lines_aged[parent_loc][loc_id][blend][product][tracking].keys()):
										for uom_id in sorted(stock_lines_aged[parent_loc][loc_id][blend][product][tracking][uop_id].keys()):
											for line in sorted(stock_lines_aged[parent_loc][loc_id][blend][product][tracking][uop_id][uom_id]):
												subtotal_blend[3]+=line['uom_quantity']
												subtotal_blend[4]+=line['amount_value']
												subtotal_blend[5]+=line['qty1']
												subtotal_blend[6]+=line['amount_value1']
												subtotal_blend[7]+=line['qty2']
												subtotal_blend[8]+=line['amount_value2']
												subtotal_blend[9]+=line['qty3']
												subtotal_blend[10]+=line['amount_value3']
												subtotal_blend[11]+=line['qty4']
												subtotal_blend[12]+=line['amount_value4']
							ws.write(rowcount,0, blend, normal_style)
							ws.write(rowcount,1, (blends.get(blend,False) and blends.get(blend,False).get('name',False) and blends[blend]['name'] or 'NOT DEFINED'), normal_style)
							for c in range(3,13):
								ws.write(rowcount,c,subtotal_blend[c] or '', normal_style_float)
								subtotal_loc[c]+=subtotal_blend[c]
							rowcount+=1
						ws.write_merge(rowcount,rowcount,0,2, 'Subtotal Location : '+locs[loc_id[0]]['name'], subtotal_style)
						for c in range(3,13):
							ws.write(rowcount,c,subtotal_loc[c] or '', subtotal_style2)
							grand_total[c]+=subtotal_loc[c]
						rowcount+=1

				ws.write_merge(rowcount,rowcount,0,2, 'Grand Total', subtotal_style)
				for c in range(3,13):
					ws.write(rowcount,c,grand_total[c] or '', subtotal_style2)
				rowcount+=1
		pass

report_sxw.report_sxw('report.summary.stock.ageing.report.pdf','summary.stock.ageing.wizard', 'addons/ad_stock_report/report/stock_ageing_report.mako',
							parser=summary_stock_ageing_parser)
summary_stock_ageing_parser_xls('report.summary.stock.ageing.report.xls','summary.stock.ageing.wizard', 'addons/ad_stock_report/report/stock_ageing_report.mako',
						parser=summary_stock_ageing_parser)