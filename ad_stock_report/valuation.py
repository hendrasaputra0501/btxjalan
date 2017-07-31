from openerp.osv import fields,osv
import datetime

class stock_value_monthly(osv.Model):
	_name = "stock.value.monthly"
	_columns = {
		"name"			: fields.char("Description",size=128,required=True),
		"period_id"		: fields.many2one('account.period',"Period",required=True),
		"start_date"	: fields.date("Start Date",required=True),
		"end_date"		: fields.date("End Date",required=True),
		"line_ids"		: fields.one2many("stock.value.monthly.lines",'value_id',"Valuation Lines"),
		"state"			: fields.selection([('draft','Draft'),('approved','Approved'),('cancel','Cancelled')],"State",required=True),
	}
	_defaults = {
		"state"	: lambda *a:'draft'
	}

	def onchange_period(self,cr,uid,ids,period_id,context=None):
		if not context:context={}
		value = {'period_id':False,'start_date':False,'end_date':False}
		if period_id:
			period = self.pool.get('account.period').browse(cr,uid,period_id,context=context)
			value.update({
				'period_id':period.id,
				'start_date':period.date_start,
				'end_date':period.date_stop,
				})
		return {'value':value}

	def set_draft(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'draft'},context=context)
	def set_approved(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'approved'},context=context)
	def set_cancel(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'cancel'},context=context)

class stock_value_monthly_lines(osv.Model):
	_name = "stock.value.monthly.lines"
	_rec_name = "location_id"
	_columns = {
		"location_id"	: fields.many2one('stock.location', 'Location',required=True),
		"value_id"		: fields.many2one("stock.value.monthly","Valuation ID",ondelete="cascade"),
		"period_id"		: fields.many2one("account.period","Period",required=True),
		"start_date"	: fields.date("Start Date",required=True),
		"end_date"		: fields.date("End Date",required=True),
		"valuation_type": fields.selection([('uom',"Per Unit of Measure"),("uop","Per Unit of Picking")],"Valuation Base",required=True),
		"valuation_lines": fields.one2many("stock.valuation.value","line_id","Valuation Lines"),
	}
	_order = "location_id asc"
	
	def _get_period_1(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.id
			except:
				return period[0].id

	def _get_period_2(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.date_start
			except:
				return period[0].date_start

	def _get_period_3(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.date_stop
			except:
				return period[0].date_stop

	_defaults = {
		# "active":True,
		"valuation_type": lambda *a:'uop',
		"period_id": _get_period_1,
		"start_date": _get_period_2,
		"end_date": _get_period_3,
	}

	def onchange_period(self,cr,uid,ids,period_id,context=None):
		if not context:context={}
		value = {'period_id':False,'start_date':False,'end_date':False}
		if period_id:
			period = self.pool.get('account.period').browse(cr,uid,period_id,context=context)
			value.update({
				'period_id':period.id,
				'start_date':period.date_start,
				'end_date':period.date_stop,
				})
		return {'value':value}

	def onchange_location_id(self,cr,uid,ids,location_id,period_id,context=None):
		if not context:context={}
		value = {"valuation_lines":False}
		if period_id:
			period = self.pool.get('account.period').browse(cr,uid,period_id,context=context)
			# date_start_lm = (datetime.datetime.strptime(period.date_start,"%Y-%m-%d")-datetime.timedelta(1)).strftime("%Y-%m-%d")
			date_stop_lm = (datetime.datetime.strptime(period.date_start,"%Y-%m-%d")-datetime.timedelta(1)).strftime("%Y-%m-%d")
			context.update({
				'from_date':period.date_start+" 00:00:00",
				'to_date':period.date_stop+" 23:59:59",
				})
		if location_id and period_id:
			context.update({'location':[location_id]})
			parent_loc = self.pool.get('stock.location').browse(cr,uid,location_id,context=context)
			parent_location = parent_loc.location_id and parent_loc.location_id.location_id.name or False
			product_ids = self.pool.get('product.product').search(cr,uid,[('internal_type','=','Finish')],context=context)
			# print "-------------",location_id
			stock,available_parent_loc,available_loc,available_prod = self.pool.get('product.product').get_stock_valuation_by_location(cr,uid,product_ids,context=context)
			# print "stock------------->",stock,parent_location
			#products = self.pool.get('product.product').browse(cr,uid,product_ids,context=context)
			valuation_lines=[]
			if stock.get(parent_location,False):
				if stock[parent_location].get(location_id,False):
					for mbc in stock[parent_location][location_id].keys():
						for prod in stock[parent_location][location_id][mbc].keys():
							p = self.pool.get('product.product').browse(cr,uid,prod)
							n_close_stock = stock[parent_location][location_id][mbc][prod].get('closing',False) and stock[parent_location][location_id][mbc][prod]["closing"].get('uom_qty',0.0) 
							n_open_stock = stock[parent_location][location_id][mbc][prod].get('opening',False) and stock[parent_location][location_id][mbc][prod]["opening"].get('uom_qty',0.0) 
							if abs(n_close_stock)<0.01:
								continue
							valuation_lines.append({
								"location_id":location_id,
								"product_id":prod,
								"uom_id":p.uom_id and p.uom_id.id,
								"period_id":period_id,
								"start_date":period.date_start,
								"end_date":period.date_stop,
								"closing_qty": n_close_stock or 0.0,
								"closing_qty_bale":n_close_stock/181.44 or 0.0,
								"opening_qty":n_open_stock or 0.0,
								"opening_qty_bale":n_open_stock/181.44 or 0.0,
								})
						value.update({"valuation_lines":valuation_lines})
		return {"value":value}

class stock_valuation_value(osv.Model):
	_name = "stock.valuation.value"
	_rec_name = "line_id"
	_columns = {
		"line_id"		: fields.many2one("stock.value.monthly.lines","Valuation Line",ondelete="cascade", required=True),
		"location_id"	: fields.many2one("stock.location","Location",required=True),
		"product_id"	: fields.many2one("product.product","Product",required=True),
		"value"			: fields.float("Price Closing Process",required=True),
		"qty_process"	: fields.float("Qty Closing Process",required=True),
		"uom_id"		: fields.many2one("product.uom","UoM reference for Price",required=True),
		"period_id"		: fields.many2one("account.period","Period",required=True),
		"start_date"	: fields.date("Start Date",required=True),
		"end_date"		: fields.date("End Date",required=True),
		"closing_qty"	: fields.float("Closing as on Period (KGS)"),
		"closing_qty_bale"	: fields.float("Closing as on Period (Bales)"),
		"opening_qty"	: fields.float("Opening as on Period (KGS)"),
		"opening_qty_bale"	: fields.float("Opening as on Period (Bales)"),
	}
	def _get_period_1(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.id
			except:
				return period[0].id

	def _get_period_2(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.date_start
			except:
				return period[0].date_start

	def _get_period_3(self,cr,uid,context=None):
		if not context:
			context={}
			period_id=self.pool.get('account.period').find(cr,uid,context={'account_period_prefer_normal':True})
		else:
			period_id=self.pool.get('account.period').find(cr,uid,dt=context.get('start_date',False),context={'account_period_prefer_normal':True})
		if period_id:
			period =self.pool.get('account.period').browse(cr,uid,period_id,context)
			try:
				return period.date_stop
			except:
				return period[0].date_stop
	_defaults = {
		"location_id": lambda self,cr,uid,context:context.get('location_id',False),
		"period_id": _get_period_1,
		"start_date": _get_period_2,
		"end_date": _get_period_3,
		"qty_process":0.0,
		"value":0.0,
	}
	def onchange_period(self,cr,uid,ids,period_id,context=None):
		if not context:context={}
		value = {'period_id':False,'start_date':False,'end_date':False}
		if period_id:
			period = self.pool.get('account.period').browse(cr,uid,period_id,context=context)
			value.update({
				'period_id':period.id,
				'start_date':period.date_start,
				'end_date':period.date_stop,
				})
		return {'value':value}