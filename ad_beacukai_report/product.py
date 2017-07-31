from osv import fields, osv
import datetime
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _

class product_product(osv.Model):
	_inherit = "product.product"

	def get_product_available2(self, cr, uid, ids, context=None):
		""" Finds whether product is available or not in particular warehouse.
		@return: Dictionary of values
		"""
		if context is None:
			context = {}
		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		
		states = context.get('states',[])
		what = context.get('what',())
		if not ids:
			ids = self.search(cr, uid, [])
		res = {}.fromkeys(ids, 0.0)
		if not ids:
			return res

		if context.get('shop', False):
			warehouse_id = shop_obj.read(cr, uid, int(context['shop']), ['warehouse_id'])['warehouse_id'][0]
			if warehouse_id:
				context['warehouse'] = warehouse_id

		if context.get('warehouse', False):
			lot_id = warehouse_obj.read(cr, uid, int(context['warehouse']), ['lot_stock_id'])['lot_stock_id'][0]
			if lot_id:
				context['location'] = lot_id

		if context.get('location', False):
			if type(context['location']) == type(1):
				location_ids = [context['location']]
			elif type(context['location']) in (type(''), type(u'')):
				location_ids = location_obj.search(cr, uid, [('name','ilike',context['location'])], context=context)
			else:
				location_ids = context['location']
		else:
			location_ids = []
			wids = warehouse_obj.search(cr, uid, [], context=context)
			if not wids:
				return res
			for w in warehouse_obj.browse(cr, uid, wids, context=context):
				location_ids.append(w.lot_stock_id.id)

		# build the list of ids of children of the location given by id
		if context.get('compute_child',True):
			child_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids = child_location_ids or location_ids
		
		# this will be a dictionary of the product UoM by product id
		product2uom = {}
		uom_ids = []
		for product in self.read(cr, uid, ids, ['uom_id'], context=context):
			product2uom[product['id']] = product['uom_id'][0]
			uom_ids.append(product['uom_id'][0])
		# this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id
		uoms_o = {}
		for uom in self.pool.get('product.uom').browse(cr, uid, uom_ids, context=context):
			uoms_o[uom.id] = uom

		results = []
		results2 = []
		results3 = []
		results4 = []
		results5 = []
		results6 = []
		results7 = []
		results8 = []
		results9 = []
		
		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)
		fd = context.get('fd',False)
		td = context.get('td',False)
		
		date_str = False
		date_str_in = False
		date_str_out = False
		date_values = False
		date_str2 = False
		date_values2 = False
		inventory_loss_loc_ids  = self.pool.get('stock.location').search(cr,uid,[('usage','=','inventory')])
		stock_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','internal')])
		supp_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','supplier')])
		production_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','production')])
		customer_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','customer')])

		where = [tuple(location_ids),tuple(location_ids),tuple(ids),tuple(states)]
		where_in = [tuple(stock_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]
		where_out = [tuple(stock_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]
		whereia = [tuple(supp_loc_ids+production_loc_ids+customer_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]
		whereib = [tuple(stock_loc_ids),tuple(supp_loc_ids+production_loc_ids+customer_loc_ids),tuple(ids),tuple(states)]
		whereic = [tuple(stock_loc_ids),tuple(supp_loc_ids+production_loc_ids+customer_loc_ids),tuple(ids),tuple(states)]
		whereid = [tuple(inventory_loss_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]	
		whereie = [tuple(stock_loc_ids),tuple(inventory_loss_loc_ids),tuple(ids),tuple(states)]	

		if from_date and to_date:
			date_str = "date>=%s and date<=%s"
			date_str_in = "date<%s"
			date_str_out = "date<%s"
			where_in.append(tuple([from_date]))
			where_out.append(tuple([from_date]))
			where.append(tuple([from_date]))
			where.append(tuple([to_date]))
			whereia.append(tuple([from_date]))
			whereia.append(tuple([to_date]))
			whereib.append(tuple([from_date]))
			whereib.append(tuple([to_date]))
			whereic.append(tuple([from_date]))
			whereic.append(tuple([to_date]))
			whereid.append(tuple([from_date]))
			whereid.append(tuple([to_date]))
			whereie.append(tuple([from_date]))
			whereie.append(tuple([to_date]))
		# elif from_date:
		# 	date_str = "date>=%s"
		# 	date_values = [from_date]
		# elif to_date:
		# 	date_str = "date<=%s"
		# 	date_values = [to_date]
		# if date_values:
		# 	where.append(tuple(date_values))
		# 	where2.append(tuple(date_values))
		# 	where3.append(tuple(date_values))
		# 	where5.append(tuple(date_values))

		# if fd and td:
		# 	date_str2 = "date>=%s and date<=%s"
		# 	where4.append(tuple([fd]))
		# 	where4.append(tuple([td]))
		# elif fd:
		# 	date_str2 = "date>=%s"
		# 	date_values2 = [fd]
		# elif td:
		# 	date_str2 = "date<=%s"
		# 	date_values2 = [td]
		# if date_values2:
		# 	where4.append(tuple(date_values2))
			
		prodlot_id = context.get('prodlot_id', False)
		prodlot_clause = ''
		if prodlot_id:
			prodlot_clause = ' and prodlot_id = %s '
			wherein += [prodlot_id]
			whereout += [prodlot_id]
			whereia += [prodlot_id]
			whereib += [prodlot_id]
			whereic += [prodlot_id]
			whereid += [prodlot_id]
			whereie += [prodlot_id]
		# print "------------------",where
		# TODO: perhaps merge in one query.
		if 'in' in what:
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id NOT IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str_in and 'and '+date_str_in+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where_in))
			results = cr.fetchall()
			# print "####################################",where_in
		if 'out' in what:
			# all moves from a location in the set to a location out of the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id NOT IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str_out and 'and '+date_str_out+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where_out))
			results2 = cr.fetchall()

		#print "results2xxxxxxxxxxxxx",results2
		if 'ia' in what:
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(whereia))
			results3 = cr.fetchall()
		if 'ib' in what:
			# all moves from a location in the set to a location out of the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(whereib))
			results4 = cr.fetchall()
		
		if 'ic' in what:
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(whereic))
			results5 = cr.fetchall()

		if 'id' in what:
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(whereid))
			results6 = cr.fetchall()
		#print "resultsxxxxxxxxxxxxx",results
		if 'ie' in what:
			# all moves from a location in the set to a location out of the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(whereie))
			results7 = cr.fetchall()

		if 'isup' in what:
			# print 'wwwwwwwwwwwwwwwwwwwww',where4
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where5))
			result8 = cr.fetchall()
		#print "resultsxxxxxxxxxxxxx",results
		if 'xo' in what:
			# all moves from a location in the set to a location out of the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id NOT IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where4))
			results9 = cr.fetchall()

		# Get the missing UoM resources
		uom_obj = self.pool.get('product.uom')
		uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2) + map(lambda x: x[2], results3)+ map(lambda x: x[2], results4)+ map(lambda x: x[2], results5)+ map(lambda x: x[2], results6)+ map(lambda x: x[2], results7)+ map(lambda x: x[2], results8)+ map(lambda x: x[2], results9)
		if context.get('uom', False):
			uoms += [context['uom']]
		uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
		if uoms:
			uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
			for o in uoms:
				uoms_o[o.id] = o
				
		#TOCHECK: before change uom of product, stock move line are in old uom.
		context.update({'raise-exception': False})
		# Count the incoming quantities
		for amount, prod_id, prod_uom in results:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] += amount
		# Count the outgoing quantities
		for amount, prod_id, prod_uom in results2:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] -= amount

		for amount, prod_id, prod_uom in results3:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] += amount
		# Count the outgoing quantities
		for amount, prod_id, prod_uom in results4:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] += amount

		for amount, prod_id, prod_uom in results5:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] -= amount

		for amount, prod_id, prod_uom in results6:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] += amount

		for amount, prod_id, prod_uom in results7:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] -= amount

		for amount, prod_id, prod_uom in results8:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] -= amount
		# Count the outgoing quantities
		for amount, prod_id, prod_uom in results9:
			amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
					uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
			res[prod_id] -= amount
		
		return res
	
	def _product_previous(self, cr, uid, ids, field_names=None, arg=False, context=None):
		if not field_names:
			field_names = []
		if context is None:
			context = {}
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0.0)
		min_date = datetime.datetime.now().strftime('%Y-01-01 00:00:00')
		if context.get('from_date',False) and not context.get('to_date',False):
			from_date = context.get('from_date')
			to_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			c.update({'from_date':from_date,'to_date':to_date})
		elif not context.get('from_date',False) and context.get('to_date',False):
			from_date = min_date
			to_date = context.get('to_date',False)
		elif not context.get('from_date',False) and not context.get('to_date',False):
			from_date = min_date
			to_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		else:
			from_date = context.get('from_date')
			to_date = context.get('to_date',False)
		
		for f in field_names:
			c = context.copy()
			c.update({'from_date':from_date,'to_date':to_date})
			if f == 'previous_qty':
				c.update({'states': ('done',), 'what': ('in', 'out') })	
			if f == 'in_qty':
				c.update({'states': ('done',), 'what': ('ia')})
			if f == 'out_qty':
				c.update({'states': ('done',), 'what': ('ib'),})
			if f == 'all_qty':
				c.update({'states': ('done',), 'what': ('in','out','ia','ic','id','ie'),})
			if f == 'adj_qty':
				c.update({'states': ('done',), 'what': ('id','ie'),})	
			# if f == 'opname_qty':
			# 	c.update({'states': ('done',), 'what': ('in','out','ia','ic','id','ie'),})

			# if f == 'selisih_qty':
			# 	c.update({'states': ('done',), 'what': ('ia','ic'),})
			# if f == 'selisih_qty':
			# 	if context.get('from_date'):
			# 		from_date = datetime.datetime.strptime(context.get('from_date'),'%Y-%m-%d %H:%M:%S')
			# 		c.update({'fd':False,'td':(from_date-datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')})
			# 	else:
			# 		c.update({'fd':False,'td':(datetime.date.today()-datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')})
			# 	if context.get('from_date',False):
			# 		c.update({'states': ('done',), 'what': ('ii', 'io','oi','oo','in','iex','out')})
			# 	elif not context.get("from_date",False):
			# 		c.update({'states': ('done',), 'what': ('oi','oo','in','iex','out')})
			# 	c.update({'states2': ('done',), 'what2': ('oi', 'oo')})
			# 	c.update({'states3': ('done',), 'what3': ('oi', 'oo')})
			# 	if context.get('from_date'):
			# 		from_date = datetime.datetime.strptime(context.get('from_date'),'%Y-%m-%d %H:%M:%S')
			# 		c.update({'fd':False,'td':(from_date-datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')})
			# 	else:
			# 		c.update({'fd':False,'td':(datetime.date.today()-datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')})
			# 	if context.get('from_date',False):
			# 		c.update({'states': ('done',), 'what': ('ii', 'io','in','iex','out')})
			# 	elif not context.get("from_date",False):
			# 		c.update({'states': ('done',), 'what': ('oi','oo','in','iex','out')})
			# 	c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
			# if f == 'incoming_qty':
			# 	c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
			# if f == 'outgoing_qty':
			# 	c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
			stock = self.get_product_available2(cr, uid, ids, context=c)
			for id in ids:
				res[id][f] = stock.get(id, 0.0)
		return res



	_columns = {
		'previous_qty': fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Saldo Awal',),

		'in_qty': fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Stock Masuk',),

		'out_qty': fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Stock Keluar',),

		'opname_qty': fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Opname Qty',),
		'all_qty' : fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='On Hand Quantity',),
		"selisih_qty":fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Selisih',),
		'adj_qty': fields.function(_product_previous, multi='qty_previous',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Penyesuaian',),
	}