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

class ReportStockBitra(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(ReportStockBitra, self).__init__(cr, uid, name, context=context)
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

	def _get_stock(self,data,internal_type):
		cr = self.cr
		uid = self.uid
		location_ids = [loc.id for loc in self.get_location(data)]
		# print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",location_ids
		from_date = data.get('date_start',False)
		to_date = data.get('date_stop',False)

		if data.get('product_ids',[]):
			ids = data['product_ids']
		else:
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
		if data['location_exception']:
			# print "llllllllllllllllllllllllllllllllllllllll",data['location_exception']
			exception_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', data['location_exception'])])
			location_ids = list(set(location_ids)-set(exception_location_ids)-set(data['location_exception']))
		if location_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(location_ids)))
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="sequence asc, name asc")
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
			return "From : %s"%da.strftime("%d/%m/%Y")
		elif date_stop and not date_start:
			db = datetime.strptime(date_stop,"%Y-%m-%d %H:%M:%S")
			return "Until : %s"%db.strftime("%d/%m/%Y")
		elif date_stop and date_start:
			da = datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S")
			db = datetime.strptime(date_stop,"%Y-%m-%d %H:%M:%S")
			return "Range : %s - %s"%(da.strftime("%d/%m/%Y"),db.strftime("%d/%m/%Y"))
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
	
		
# report_sxw.report_sxw('report.stock.report',
#						 'stock.report.bitratex.wizard', 
#						 'addons/ad_stock_report/report/ad_stock_report.mako', parser=ReportStockBitra)
# report_sxw.report_sxw('report.penjualan.form', 'report.keuangan', 'addons/ad_laporan_keuangan/report/salesreport.mako', parser=ReportKeu)