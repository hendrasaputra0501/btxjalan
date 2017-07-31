from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
from datetime import datetime

class mrp_bom(osv.Model):
	_inherit = "mrp.bom"
	_columns = {
		"comp_percentage":fields.float("Component Percentage",required=False),
		"waste_product_id":fields.many2one("product.product","Waste Product",required=False),
		"waste_percentage":fields.float("Waste Percentage",required=False),
		"waste_qty":fields.float("Waste Qty",required=False),
		"blend_code":fields.many2one("mrp.blend.code","Code",required=False),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		reads = self.read(cr, uid, ids, ['name','blend_code'], context=context)
		res = []
		for record in reads:
			name = record['name']
			if record['blend_code']:
				bc=self.pool.get("mrp.blend.code").browse(cr,uid,[record['blend_code'][0]])
				name = '[' + bc[0].name + '] ' + name
			res.append((record['id'], name))
		return res

class product_rm_type_category(osv.Model):

	def get_product_available(self, cr, uid, ids, context=None):
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

		results_all_in = []
		results_all_out = []
		results_in = []
		results_out = []
		results_out2 = []
		results_adj_in = []
		results_adj_out = []
		
		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)
		
		date_str = False
		date_str_in = False
		date_str_out = False
		
		inventory_loss_loc_ids  = self.pool.get('stock.location').search(cr,uid,[('usage','=','inventory')])
		stock_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','internal')])
		# supp_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','supplier')])
		production_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','production')])
		# customer_loc_ids = self.pool.get('stock.location').search(cr,uid,[('usage','=','customer')])

		where = [tuple(production_loc_ids),tuple(production_loc_ids),tuple(ids),tuple(states)]
		where_all_in = [tuple(production_loc_ids),tuple(production_loc_ids),tuple(ids),tuple(states)]
		where_all_out = [tuple(production_loc_ids),tuple(production_loc_ids),tuple(ids),tuple(states)]
		where_in = [tuple(stock_loc_ids),tuple(production_loc_ids),tuple(ids),tuple(states)]
		where_out = [tuple(production_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]
		where_out2 = [tuple(production_loc_ids),tuple(stock_loc_ids),tuple(ids),tuple(states)]
		where_adj_in = [tuple(inventory_loss_loc_ids),tuple(production_loc_ids),tuple(ids),tuple(states)]	
		where_adj_out = [tuple(production_loc_ids),tuple(inventory_loss_loc_ids),tuple(ids),tuple(states)]	

		if from_date and to_date:
			date_str = "date>=%s and date<=%s"
			date_str_in = "date<%s"
			date_str_out = "date<%s"
			where.append(tuple([from_date]))
			where.append(tuple([to_date]))
			where_all_in.append(tuple([from_date]))
			where_all_out.append(tuple([from_date]))
			where_in.append(tuple([from_date]))
			where_in.append(tuple([to_date]))
			where_out.append(tuple([from_date]))
			where_out.append(tuple([to_date]))
			where_out2.append(tuple([from_date]))
			where_out2.append(tuple([to_date]))
			where_adj_in.append(tuple([from_date]))
			where_adj_in.append(tuple([to_date]))
			where_adj_out.append(tuple([from_date]))
			where_adj_out.append(tuple([to_date]))
		
		if 'all_in' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id NOT IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state IN %s ' + (date_str_in and 'and '+date_str_in+' ' or '') +' '\
				'group by rm_category_id,product_uom',tuple(where_all_in))
			results_all_in = cr.fetchall()
		if 'all_out' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id NOT IN %s '\
				'and rm_category_id IN %s '\
				'and state in %s ' + (date_str_out and 'and '+date_str_out+' ' or '') + ' '\
				'group by rm_category_id,product_uom',tuple(where_all_out))
			results_all_out = cr.fetchall()
		if 'in' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				'group by rm_category_id,product_uom',tuple(where_in))
			results_in = cr.fetchall()
		if 'out' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				'group by rm_category_id,product_uom',tuple(where_out))
			results_out = cr.fetchall()
		if 'out2' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				'group by rm_category_id,product_uom',tuple(where_out))
			results_out2 = cr.fetchall()
		if 'adj_in' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				'group by rm_category_id,product_uom',tuple(where_adj_in))
			results_adj_in = cr.fetchall()
		if 'adj_out' in what:
			cr.execute(
				'select sum(product_qty), rm_category_id, product_uom '\
				'from stock_move_composition '\
				'where location_id IN %s '\
				'and location_dest_id IN %s '\
				'and rm_category_id IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				'group by rm_category_id,product_uom',tuple(where_adj_out))
			results_adj_out = cr.fetchall()
		
		# Get the missing UoM resources
		uom_obj = self.pool.get('product.uom')
		uoms = map(lambda x: x[2], results_all_in) + map(lambda x: x[2], results_all_out) + map(lambda x: x[2], results_in)+ map(lambda x: x[2], results_out)+ map(lambda x: x[2], results_out2)+ map(lambda x: x[2], results_adj_in)+ map(lambda x: x[2], results_adj_out)
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
		for quantity, rm_category_id, prod_uom in results_all_in:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					 uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] += quantity
		# Count the outgoing quantities
		for quantity, rm_category_id, prod_uom in results_all_out:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] -= quantity

		for quantity, rm_category_id, prod_uom in results_in:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					 uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] += quantity
		# Count the outgoing quantities
		for quantity, rm_category_id, prod_uom in results_out:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] += quantity

		for quantity, rm_category_id, prod_uom in results_out2:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] -= quantity

		for quantity, rm_category_id, prod_uom in results_adj_in:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] += quantity

		for quantity, rm_category_id, prod_uom in results_adj_out:
			quantity = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], quantity,
					uoms_o[context.get('uom', False) or product2uom[rm_category_id]], context=context)
			res[rm_category_id] -= quantity

		return res

	def _product_mutation(self, cr, uid, ids, field_names=None, arg=False, context=None):
		if not field_names:
			field_names = []
		if context is None:
			context = {}
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0.0)
		min_date = datetime.now().strftime('%Y-01-01 00:00:00')
		if context.get('from_date',False) and not context.get('to_date',False):
			from_date = context.get('from_date')
			to_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			c.update({'from_date':from_date,'to_date':to_date})
		elif not context.get('from_date',False) and context.get('to_date',False):
			from_date = min_date
			to_date = context.get('to_date',False)
		elif not context.get('from_date',False) and not context.get('to_date',False):
			from_date = min_date
			to_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		else:
			from_date = context.get('from_date')
			to_date = context.get('to_date',False)
		
		for f in field_names:
			c = context.copy()
			c.update({'from_date':from_date,'to_date':to_date})
			if f == 'available_qty':
				c.update({'states': ('done',), 'what': ('all_in', 'all_out') })
			if f == 'opening_qty':
				c.update({'states': ('done',), 'what': ('all_in', 'all_out') })
			if f == 'in_qty':
				c.update({'states': ('done',), 'what': ('in')})
			if f == 'out_qty':
				c.update({'states': ('done',), 'what': ('out'),})
			if f == 'all_qty':
				c.update({'states': ('done',), 'what': ('all_in','all_out','in','out2','adj_in','adj_out'),})
			if f == 'adj_qty':
				c.update({'states': ('done',), 'what': ('adj_in','adj_out'),})	
			stock = self.get_product_available(cr, uid, ids, context=c)
			for id in ids:
				res[id][f] = stock.get(id, 0.0)
		return res

	_name = "product.rm.type.category"
	_columns = {
		"name": fields.char("Type Name",size=64,required=True),
		"code": fields.char("Code",size=12,required=True),
		'uom_id': fields.many2one('product.uom',"Default UoM"),
		
		'available_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Current Qty',),

		'opening_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Saldo Awal',),

		'in_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Stock Masuk',),

		'out_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Stock Keluar',),

		'opname_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Opname Qty',),
		
		'all_qty' : fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='On Hand Quantity',),
		
		"difference_qty":fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Selisih',),

		'adj_qty': fields.function(_product_mutation, multi='qty_mutation',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Penyesuaian',),
	}
	
	def _get_default_uom(self,cr,uid,context=None):
		if not context:context={}
		uom_categ = self.pool.get('product.uom.categ').search(cr,uid,[('name','=','Bitratex Weight')])
		uom_id=False
		if uom_categ:
			try:
				uom_categ_id = uom_categ[0]
			except:
				uom_categ_id = uom_categ
			
			uom_id=self.pool.get('product.uom').search(cr,uid,[('name','=','KGS'),('category_id','=',uom_categ_id)])[0]

		return uom_id
	
	_defaults = {
		'uom_id' : _get_default_uom,
	}


class product_rm_type(osv.Model):
	_name = "product.rm.type"
	_columns = {
		"name": fields.char("Type Name",size=64,required=True),
		"code": fields.char("Code",size=12,required=True),
		'category_id': fields.many2one("product.rm.type.category","RM Category",required=True),
		"description":fields.text("Description")
	}

class mrp_blend_code(osv.Model):
	_name = "mrp.blend.code"
	_columns = {
		"name" : fields.char("Code",size=64,required=True),
		"desc" : fields.text("Description"),
		"blend_lines" : fields.one2many("mrp.blend.code.line","blend_id","Composition")
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		reads = self.read(cr, uid, ids, ['name'], context=context)
		res = []
		for record in reads:
			name = record['name']
			res.append((record['id'], name))
		return res

class mrp_blend_code_lines(osv.Model):
	_name = "mrp.blend.code.line"
	_rec_name = "rm_type_id"
	_columns = {
		"rm_type_id":fields.many2one("product.rm.type","Raw Material",required=True),
		"blend_id" : fields.many2one("mrp.blend.code","Blend Code"),
		"percentage":fields.float("Percentage",required=True),
		"waste_percentage":fields.float("Waste Percentage",required=False),
	}
