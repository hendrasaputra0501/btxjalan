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

class ReportStockValBitra(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(ReportStockValBitra, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
		'objects' : self._get_object,
		'get_mode' : self._get_mode,
		'get_date_range':self._get_date_range,
		'get_inventory_type': self._get_inventory_type,
		'get_location':self.get_location,
		'get_stock'	: self._get_stock,
		'get_product_info':self._get_product_info,
		'get_tracking_info':self._get_tracking_info,
		'get_uom_info':self._get_uom_info,
		'get_parent_location':self._get_parent_location,
		'get_available_location':self._get_available_location,
		})
	
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
		parent_location_ids = [ll.location_id.location_id.id for ll in locsss if ll.location_id and ll.location_id.location_id and ll.location_id.location_id.id]
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

	def _get_stock(self,data,internal_type):
		cr = self.cr
		uid = self.uid
		location_ids = [loc.id for loc in self.get_location(data)]
		# print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",location_ids
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

	def get_location(self,data):
		cr = self.cr
		uid = self.uid
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXX", "ADA" if data['location_exception'] else "TIDAK ADA"
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('scrap_location','=',False),\
				('usage',"not in",['view','customer','supplier','inventory','procurement','production']),('chained_location_type','=','none')])
			#print "-----------sssssssssssssssssss----------",location_ids
		else:
			location_ids = data['location_force']
			location_ids_2 = self.pool.get('stock.location').search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids+=location_ids_2
		if data['location_exception']:
			# print "llllllllllllllllllllllllllllllllllllllll",data['location_exception']
			exception_location_ids = self.pool.get('stock.location').search(cr, uid, [('location_id', 'child_of', data['location_exception'])])
			location_ids = list(set(location_ids)-set(exception_location_ids)-set(data['location_exception']))
		if location_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(location_ids)))
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="location_id, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []

	def _get_inventory_type(self,data):
		if data['goods_type']:
			return self.pool.get('goods.type').browse(self.cr,self.uid,data['goods_type'])
		return []

	def _get_date_range(self,data):
		date_start = data['date_start']
		date_stop = data['date_stop']
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

	def _get_mode(self,data):
		dictionary_mode={
			'product' : "Product Wise",
			'location' : "Location Wise",
		}
		return dictionary_mode.get(data['grouping'],'product')
	
	def _get_object(self,data):
		#print "-------------------",data['model']
		obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
		return obj_data

	def compute_fifo_simple_valuation(self,code,data):
		cr = self.cr
		uid = self.uid
		location_ids=[loc.id for loc in self.get_location(data)]
		from_date = data.get('date_start',False)
		to_date = data.get('date_stop',False)
		if data.get('product_ids',[]):
			ids = data['product_ids']
		else:
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

	
	def compute_finish_valuation(self,data):
		cr = self.cr
		uid = self.uid
		value = {}
		location_ids=[loc.id for loc in self.get_location(data)]
		from_date = data.get('date_start',False)
		to_date = data.get('date_stop',False)
		from_date_min_1 = (datetime.strptime(from_date,'%Y-%m-%d %H:%M:%S')-relativedelta(months=1)).strftime('%Y-%m-%d')
		to_date_min_1 = (datetime.strptime(to_date,'%Y-%m-%d %H:%M:%S')-relativedelta(months=1)).strftime('%Y-%m-%d')
		if data.get('product_ids',[]):
			ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=','Finish'),('id','in',data['product_ids'])])
		else:
			ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=','Finish')])
		context = {
			'location':location_ids,
			'from_date':from_date,
			'to_date':to_date,
			'states':['done'],
			"prodlot_id":False,
			"internal_type":'Finish',
		}
		stock_lines,available_parent_loc,available_loc,available_prod = self.pool.get('product.product').get_stock_valuation_by_location(cr,uid,ids,context=context)
		val_month_ids_min_1 = self.pool.get('stock.value.monthly').search(cr,uid,[('start_date','<=',from_date_min_1),('end_date','>=',to_date_min_1),('state','=','approved')])
		val_month_line_ids_min_1 = self.pool.get('stock.value.monthly.lines').search(cr,uid,[('value_id','in',val_month_ids_min_1)])
		values_min_1 = {}

		## get opening values
		for val_line in self.pool.get('stock.value.monthly.lines').browse(cr,uid,val_month_line_ids_min_1):
			for prod in val_line.valuation_lines:
				if not values_min_1.get(val_line.location_id.location_id.location_id.name,False):
					values_min_1.update({
							val_line.location_id.location_id.location_id.name:{val_line.location_id.id:{prod.product_id.id:{
								'closing_qty':prod.closing_qty,
								'closing_qty_bale':prod.closing_qty_bale,
								'value':prod.value,
								'qty_process':prod.qty_process,
								'uom_id':prod.uom_id.id
								}
							}}})
				else:
					if not values_min_1[val_line.location_id.location_id.location_id.name].get(val_line.location_id.id,False):
						values_min_1[val_line.location_id.location_id.location_id.name].update({
							val_line.location_id.id:{prod.product_id.id:{
								'closing_qty':prod.closing_qty,
								'closing_qty_bale':prod.closing_qty_bale,
								'value':prod.value,
								'qty_process':prod.qty_process,
								'uom_id':prod.uom_id.id
								}
							}})
					else:
						if not values_min_1[val_line.location_id.location_id.location_id.name][val_line.location_id.id].get(prod.product_id.id,False):
							values_min_1[val_line.location_id.location_id.location_id.name][val_line.location_id.id].update({
									prod.product_id.id:{
										'closing_qty':prod.closing_qty,
										'closing_qty_bale':prod.closing_qty_bale,
										'value':prod.value,
										'qty_process':prod.qty_process,
										'uom_id':prod.uom_id.id
										}
									})
						else:
							values_min_1[val_line.location_id.location_id.location_id.name][val_line.location_id.id][prod.product_id.id].update({
										'closing_qty':prod.closing_qty,
										'closing_qty_bale':prod.closing_qty_bale,
										'value':prod.value,
										'qty_process':prod.qty_process,
										'uom_id':prod.uom_id.id
									})

				# if val_line.location_id.id==977:
				# 	print "===========",values_min_1[val_line.location_id.location_id.location_id.name][977]	
		## get closing values
		val_month_ids = self.pool.get('stock.value.monthly').search(cr,uid,[('start_date','<=',from_date),('end_date','>=',to_date),('state','=','approved')])
		val_month_line_ids = self.pool.get('stock.value.monthly.lines').search(cr,uid,[('value_id','in',val_month_ids)])
		values = {}
		for val_line in self.pool.get('stock.value.monthly.lines').browse(cr,uid,val_month_line_ids):
			for prod in val_line.valuation_lines:
				if not values.get(val_line.location_id.location_id.location_id.name,False):
					values.update({
							val_line.location_id.location_id.location_id.name:{val_line.location_id.id:{prod.product_id.id:{
								'closing_qty':prod.closing_qty,
								'closing_qty_bale':prod.closing_qty_bale,
								'value':prod.value,
								'qty_process':prod.qty_process,
								'uom_id':prod.uom_id.id
								}
							}}})
				else:
					if not values[val_line.location_id.location_id.location_id.name].get(val_line.location_id.id,False):
						values[val_line.location_id.location_id.location_id.name].update({
							val_line.location_id.id:{prod.product_id.id:{
								'closing_qty':prod.closing_qty,
								'closing_qty_bale':prod.closing_qty_bale,
								'value':prod.value,
								'qty_process':prod.qty_process,
								'uom_id':prod.uom_id.id
								}
							}})
					else:
						if not values[val_line.location_id.location_id.location_id.name][val_line.location_id.id].get(prod.product_id.id,False):
							values[val_line.location_id.location_id.location_id.name][val_line.location_id.id].update({
									prod.product_id.id:{
										'closing_qty':prod.closing_qty,
										'closing_qty_bale':prod.closing_qty_bale,
										'value':prod.value,
										'qty_process':prod.qty_process,
										'uom_id':prod.uom_id.id
										}
									})
						else:
							values[val_line.location_id.location_id.location_id.name][val_line.location_id.id][prod.product_id.id].update({
										'closing_qty':prod.closing_qty,
										'closing_qty_bale':prod.closing_qty_bale,
										'value':prod.value,
										'qty_process':prod.qty_process,
										'uom_id':prod.uom_id.id
									})
		sale_values = {}
		customer_location = self.pool.get("stock.location").search(cr,uid,[("usage","=","customer")])
		

		sale_return_values = {}
		# customer_location = self.pool.get("stock.location").search(cr,uid,[("usage","=","customer")])
		sale_return_move_ids = self.pool.get("stock.move").search(cr,uid,[("date",">=",from_date),("date","<=",to_date),("location_dest_id","in",available_loc),("location_id","in",customer_location)],order="location_id asc,product_id asc")
		for sale_ret in self.pool.get("stock.move").browse(cr,uid,sale_return_move_ids):
			parent_sl = sale_ret.location_id.location_id.location_id.name
			location_id = sale_ret.location_id.id
			product_id = sale_ret.product_id.id
			
			if not sale_return_values.get(parent_sl,False):
				sale_return_values.update({parent_sl:{location_id:{product_id:{"total_fob":sale_ret.fob_rate or 0.0,'n_move':1}}}})
				
			else: 
				if not sale_return_values[parent_sl].get(location_id,False):
					sale_return_values[parent_sl].update({location_id:{product_id:{"total_fob":sale_ret.fob_rate or 0.0,'n_move':1}}})
				else:
					if not sale_return_values[parent_sl][location_id].get(product_id,False):
						sale_return_values[parent_sl][location_id].update({product_id:{"total_fob":sale_ret.fob_rate or 0.0,'n_move':1}})
					else:
						if not sale_return_values[parent_sl][location_id][product_id].get("total_fob",False):
							sale_return_values[parent_sl][location_id][product_id].update({"total_fob":sale_ret.fob_rate or 0.0,'n_move':1})
						else:	
							sale_return_values[parent_sl][location_id][product_id].update({
								"total_fob":sale_return_values[parent_sl][location_id][product_id].get('total_fob' or 0.0)+sale_ret.fob_rate,
								'n_move':sale_return_values[parent_sl][location_id][product_id].get('n_move' or 0)+1
								})
		for parent_location in stock_lines.keys():
			for location in stock_lines[parent_location].keys():
				for mbc_name in stock_lines[parent_location][location].keys():
					for product_id in stock_lines[parent_location][location][mbc_name].keys():
						val_open = stock_lines[parent_location][location][mbc_name][product_id].get('opening',False)
						if val_open:
							price = values_min_1.get(parent_location,False) and values_min_1[parent_location].get(location,False) and values_min_1[parent_location][location].get(product_id,False) and values_min_1[parent_location][location][product_id].get('value',0.0) or 0.0
							op_qty = values_min_1.get(parent_location,False) and values_min_1[parent_location].get(location,False) and values_min_1[parent_location][location].get(product_id,False) and values_min_1[parent_location][location][product_id].get('qty_process',0.0) or 0.0
							val_open.update({
								'price_kg': price,
								'amount': val_open.get('uom_qty',0.0)* price or 0.0,
								'qty_process':op_qty or 0.0, 
								"qty_process_amt":op_qty*price or 0.0,
								})
							stock_lines[parent_location][location][mbc_name][product_id]['opening'].update(val_open)
						val_sale = stock_lines[parent_location][location][mbc_name][product_id].get('outgoing',False)
						if val_sale:
							#total_sale = sale_values.get(parent_location,False) and sale_values[parent_location].get(location,False) and sale_values[parent_location][location].get(product_id,False) and sale_values[parent_location][location][product_id].get("total_fob",0.0) or 0.0
							#n_sale = sale_values.get(parent_location,False) and sale_values[parent_location].get(location,False) and sale_values[parent_location][location].get(product_id,0.0) and sale_values[parent_location][location][product_id].get("n_move",0.0) or 0.0
							total_sale = val_sale.get("total_fob",0.0)
							qty_sale = val_sale.get("uom_qty",0.0) or 0.0
							price_kg_sale = qty_sale>0.0 and (total_sale/qty_sale) or 0.0
							val_sale.update({
								'price_kg': price_kg_sale,
								'amount': total_sale or 0.0,
								})
						val_sale_ret = stock_lines[parent_location][location][mbc_name][product_id].get('out_return',False)
						if val_sale_ret:
							total_return = sale_return_values.get(parent_location,False) and sale_return_values[parent_location].get(location,False) and sale_return_values[parent_location][location].get(product_id,False) and  sale_return_values[parent_location][location][product_id].get("total_fob",0.0) or 0.0
							n_return = sale_return_values.get(parent_location,False) and sale_return_values[parent_location].get(location,False) and sale_return_values[parent_location][location].get(product_id,False) and  sale_return_values[parent_location][location][product_id].get("n_move",0.0) or 0.0
							qty_sale = val_sale_ret.get("uom_qty",0.0) or 0.0
							price_kg_sale = qty_sale>0.0 and n_return>0.0 and ((total_return/n_return)/qty_sale) or 0.0
							val_sale_ret.update({
								'price_kg': price_kg_sale,
								'amount': total_sale or 0.0,
								})

						val_closing = stock_lines[parent_location][location][mbc_name][product_id].get('closing',{})
						if val_closing:
							price = values.get(parent_location,False) and values[parent_location].get(location,False) and values[parent_location][location].get(product_id,False) and values[parent_location][location][product_id].get('value',0.0) or 0.0
							op_qty = values.get(parent_location,False) and values[parent_location].get(location,False) and values[parent_location][location].get(product_id,False) and values[parent_location][location][product_id].get('qty_process',0.0) or 0.0
							# net_qty = op_qty - (val_open and val_open.get('qty_process',0.0)) or 0.0
							val_closing.update({
								'price_kg': price,
								'amount': val_closing.get('uom_qty',0.0)* price or 0.0,
								"qty_process":op_qty or 0.0,
								"qty_process_amt":op_qty*price or 0.0,
								# "net_prod_qty":net_qty,
								# "net_prod_price":net_qty,
								})
							stock_lines[parent_location][location][mbc_name][product_id]['closing'].update(val_closing)
						else:
							price = values.get(parent_location,False) and values[parent_location].get(location,False) and values[parent_location][location].get(product_id,False) and values[parent_location][location][product_id].get('value',0.0) or 0.0
							op_qty = values.get(parent_location,False) and values[parent_location].get(location,False) and values[parent_location][location].get(product_id,False) and values[parent_location][location][product_id].get('qty_process',0.0) or 0.0
							# net_qty = op_qty - (val_open and val_open.get('qty_process',0.0)) or 0.0
							val_closing.update({
								'price_kg': price,
								'amount': 0.0,
								"qty_process":op_qty or 0.0,
								"qty_process_amt":op_qty*price or 0.0,
								# "net_prod_qty":net_qty,
								# "net_prod_price":net_qty,
								})
							stock_lines[parent_location][location][mbc_name][product_id].update({'closing':val_closing})
						# if location==977 and product_id==1792:
						# 	print "=====1======",stock_lines[parent_location][location][mbc_name][product_id]	
						# 	print "=====2======",val_open	
						# 	print "=====3======",val_sale	
						# 	print "=====4======",val_sale_ret	
						# 	print "=====5======",val_closing	
		# print "###########################"
		# print "###########################"
		return (stock_lines,available_parent_loc,available_loc,available_prod) or {}

	def get_valuation(self,code,data):
		valuations = False
		if code =='Finish':
			valuations = self.compute_finish_valuation(data)
		elif code in ('Stores','Packing','Raw Material'):
			valuations = self.compute_fifo_simple_valuation(code,data)
		# print "===============valuations===================",valuations
		return valuations
# report_sxw.report_sxw('report.stock.report',
#						 'stock.report.bitratex.wizard', 
#						 'addons/ad_stock_report/report/ad_stock_report.mako', parser=ReportStockBitra)
# report_sxw.report_sxw('report.penjualan.form', 'report.keuangan', 'addons/ad_laporan_keuangan/report/salesreport.mako', parser=ReportKeu)