from openerp.osv import fields,osv

class product_product(osv.Model):
	_inherit = "product.product"
	_columns = {

	}

	def get_stock_fifo_valuation_by_location(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		
		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		uom_obj = self.pool.get('product.uom')

		# res = {}
		res = []
		# if context.get('location', False):
		# 	res = {}.fromkeys(context.get('location'), {})
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
		if context.get('compute_child',True):
			child_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids = child_location_ids or location_ids

		# location_ids = location_obj.search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		location_ids = location_obj.search(cr,uid,[('id','in',location_ids),('usage','!=','view')])
		opening_location = location_obj.search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		internal_locations = location_obj.search(cr,uid,[('id','in',location_ids),('usage','!=','view'),('usage','=','internal')])
		customer_locations = location_obj.search(cr,uid,[('child_ids','=',False),('usage','=','customer'),('usage','!=','view')])
		supplier_locations = location_obj.search(cr,uid,[('child_ids','=',False),('usage','=','supplier'),('usage','!=','view')])
		production_locations = location_obj.search(cr,uid,[('usage','=','production'),('usage','!=','view')])
		adjustment_locations = location_obj.search(cr,uid,[('child_ids','=',False),('usage','=','inventory'),('usage','!=','view')])
		issue_locations = location_obj.search(cr,uid,[('usage','in',('production','inventory')),('usage','!=','view')])
		issue_locations2 = location_obj.search(cr,uid,[('child_ids','=',False),('usage','in',('internal','inventory')),('usage','!=','view')])
		incoming_locations = location_obj.search(cr,uid,[('child_ids','=',False),('usage','in',('supplier','production'))])
		closing_locations = location_obj.search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])

		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)


		available_parent_loc = []
		available_loc = []
		available_prod = []
		stock = {}
		if ids:
			##############################################################################
			############################## OPENING STOCK #################################
			##############################################################################
			query_opening = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
				(case pp.internal_type \
					when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
					when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
					when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
					else '' end) as blend_name,pp.name_template as prod_name, q1.* \
				FROM (SELECT * FROM get_opening_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+\
				str(ids)+",array"+str(internal_locations)+",array"+str(internal_locations)+")) q1 \
				LEFT JOIN product_product pp on q1.prod_id=pp.id \
				LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
				LEFT JOIN stock_location sl on q1.loc_id=sl.id \
				LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
				LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
				ORDER BY sl2.name asc ,sl.name asc, mbc.name asc;"
			cr.execute(query_opening)
			result_open1 = cr.fetchall()
			if result_open1:
				for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_open1:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if parent_loc not in stock.keys():
						stock.update({parent_loc:{}})
					if location_id not in stock[parent_loc].keys():
						stock[parent_loc].update({location_id:{}})
					if mbc_name not in stock[parent_loc][location_id].keys():
						stock[parent_loc][location_id].update({mbc_name:{}})
					if product_id not in stock[parent_loc][location_id][mbc_name].keys():
						stock[parent_loc][location_id][mbc_name].update({product_id:{}})
					if context.get('internal_type','Raw Material') == 'Raw Material':
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'opening' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'opening':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['opening']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['opening']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['opening']['uom_qty_value'] += amount
					else:
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'opening' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'opening':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['opening']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['opening']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['opening']['uom_qty_value'] += amount
			
			##############################################################################
			############################## INCOMING STOCK ################################ 
			##############################################################################
			############### incoming from SUPPLIER to INTERNAL #######################
			query_incoming1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
				(case pp.internal_type \
					when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
					when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
					when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
					else '' end) as blend_name,pp.name_template as prod_name,q1.* \
				FROM (SELECT * FROM get_incoming_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
				to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
				array"+str([0,0,0])+",array"+str(supplier_locations)+") ) q1 \
				LEFT JOIN product_product pp on q1.prod_id=pp.id \
				LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
				LEFT JOIN stock_location sl on q1.loc_id=sl.id \
				LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
				LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
				ORDER BY sl2.name asc ,sl.name asc, mbc.name asc;"
			cr.execute(query_incoming1)
			result_incoming1 = cr.fetchall()
			if result_incoming1:
				for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_incoming1:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if parent_loc not in stock.keys():
						stock.update({parent_loc:{}})
					if location_id not in stock[parent_loc].keys():
						stock[parent_loc].update({location_id:{}})
					if mbc_name not in stock[parent_loc][location_id].keys():
						stock[parent_loc][location_id].update({mbc_name:{}})
					if product_id not in stock[parent_loc][location_id][mbc_name].keys():
						stock[parent_loc][location_id][mbc_name].update({product_id:{}})
					if context.get('internal_type','Raw Material') == 'Raw Material':
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'receipt' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'receipt':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['receipt']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['receipt']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['receipt']['uom_qty_value'] += amount
					else:
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'receipt' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'receipt':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['receipt']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['receipt']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['receipt']['uom_qty_value'] += amount

			############### return incoming from INTERNAL to SUPPLIER #######################
			query_incoming2 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
				(case pp.internal_type \
					when 'Finish' then mbc.name \
					when 'Finish_others' then mbc.name \
					when 'Waste' then mbc.name \
					when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
					when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
					when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
					else '' end) as blend_name,pp.name_template as prod_name,q1.* \
				FROM (SELECT * FROM get_incoming_return_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
				to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
				array"+str([0,0,0])+",array"+str(supplier_locations)+")) q1 \
				LEFT JOIN product_product pp on q1.prod_id=pp.id \
				LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
				LEFT JOIN stock_location sl on q1.loc_id=sl.id \
				LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
				LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
				ORDER BY sl2.name asc ,sl.name asc,mbc.name asc;"
			cr.execute(query_incoming2)
			result_incoming2 = cr.fetchall()
			if result_incoming2:
				for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_incoming2:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if parent_loc not in stock.keys():
						stock.update({parent_loc:{}})
					if location_id not in stock[parent_loc].keys():
						stock[parent_loc].update({location_id:{}})
					if mbc_name not in stock[parent_loc][location_id].keys():
						stock[parent_loc][location_id].update({mbc_name:{}})
					if product_id not in stock[parent_loc][location_id][mbc_name].keys():
						stock[parent_loc][location_id][mbc_name].update({product_id:{}})
					if context.get('internal_type','Raw Material') == 'Raw Material':
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'return_receipt' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'return_receipt':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_receipt']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_receipt']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_receipt']['uom_qty_value'] += amount
					else:
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'return_receipt' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'return_receipt':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_receipt']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_receipt']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_receipt']['uom_qty_value'] += amount

			###############################################################################
			############################### OUTGOING STOCK ################################ 
			###############################################################################
			if context.get('internal_type','Finish') in ('Raw Material'):
				############### outgoing from INTERNAL to PRODUCTION #######################
				query_outgoing1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* \
					FROM (SELECT * FROM get_outgoing_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
					array"+str(production_locations)+")) q1 \
					LEFT JOIN product_product pp on q1.prod_id=pp.id \
					LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
					LEFT JOIN stock_location sl on q1.loc_id=sl.id \
					LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
					LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
					ORDER BY sl2.name asc ,sl.name asc,mbc.name asc;"
				
				cr.execute(query_outgoing1)
				result_outgoing1 = cr.fetchall()

				if result_outgoing1:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_outgoing1:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'issue' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'issue':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['issue']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['issue']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['issue']['uom_qty_value'] += amount
				
				############### return outgoing from PRODUCTION to INTERNAL #######################
				query_outgoing2 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* \
					FROM (SELECT * FROM get_outgoing_return_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
					array"+str(production_locations)+")) q1 \
					LEFT JOIN product_product pp on q1.prod_id=pp.id \
					LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
					LEFT JOIN stock_location sl on q1.loc_id=sl.id \
					LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
					LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
					ORDER BY sl2.name asc ,sl.name asc,mbc.name asc;"
				cr.execute(query_outgoing2)
				result_outgoing2 = cr.fetchall()
				if result_outgoing2:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_outgoing2:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'return_issue' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'return_issue':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_issue']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_issue']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['return_issue']['uom_qty_value'] += amount

			elif context.get('internal_type','Finish') in ('Stores','Packing'):
				############### outgoing from INTERNAL to ADJUSTMENT(as Consume Product) #######################
				query_outgoing1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* FROM (select * from get_outgoing_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
					array"+str(issue_locations)+")) q1 \
					left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id \
					left join stock_location sl on q1.loc_id=sl.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
					order by sl2.name asc ,sl.name asc,mbc.name asc;"
				
				cr.execute(query_outgoing1)
				result_outgoing1 = cr.fetchall()

				if result_outgoing1:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_outgoing1:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'issue' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'issue':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['issue']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['issue']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['issue']['uom_qty_value'] += amount

				############### return outgoing from ADJUSTMENT(as Consume Product) to INTERNAL #######################
				query_outgoing2 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* from (select * from get_outgoing_return_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
					array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
					order by sl2.name asc ,sl.name asc,mbc.name asc;"
				
				cr.execute(query_outgoing2)
				result_outgoing2 = cr.fetchall()
				if result_outgoing2:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_outgoing2:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'return_issue' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'return_issue':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_issue']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_issue']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['return_issue']['uom_qty_value'] += amount

			##################################################################################
			############################### ADJUSTMENT STOCK ################################# 
			##################################################################################
			if context.get('internal_type','Finish') in ('Finish','Finish_others','Waste','Scrap'):
				############### adjustment or internal transfer from INTERNAL/INVENTORY to INTERNAL/INVENTORY #######################
				query_issue1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* from (select * from get_issue(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
					array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
					order by sl2.name asc ,sl.name asc,mbc.name asc;"
				cr.execute(query_issue1)
				result_issue1 = cr.fetchall()
				if result_issue1:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_issue1:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'adjustment' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'adjustment':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uom_qty_value'] += amount
			elif context.get('internal_type','Finish') in ('Stores','Packing','Raw Material'):
				############### adjustment as Opname from INTERNAL to ADJUSTMENT #######################
				query_issue1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
					(case pp.internal_type \
						when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
						when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
						when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
						when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
						else '' end) as blend_name,pp.name_template as prod_name,q1.* from (select * from get_adjustment_fifo(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
					to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+")) q1 \
					LEFT JOIN product_product pp on q1.prod_id=pp.id \
					LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
					LEFT JOIN stock_location sl on q1.loc_id=sl.id \
					LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
					LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
					ORDER BY sl2.name asc ,sl.name asc,mbc.name asc;"
				cr.execute(query_issue1)
				result_issue1 = cr.fetchall()
				if result_issue1:
					for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_issue1:
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)

						if parent_loc not in stock.keys():
							stock.update({parent_loc:{}})
						if location_id not in stock[parent_loc].keys():
							stock[parent_loc].update({location_id:{}})
						if mbc_name not in stock[parent_loc][location_id].keys():
							stock[parent_loc][location_id].update({mbc_name:{}})
						if product_id not in stock[parent_loc][location_id][mbc_name].keys():
							stock[parent_loc][location_id][mbc_name].update({product_id:{}})
						if context.get('internal_type','Raw Material') == 'Raw Material':
							if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
								stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
							if 'adjustment' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
								stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'adjustment':{
									'uop_qty' : 0.0,
									'uom_qty' : 0.0,
									'uom_qty_value' : 0.0,
									}})
							stock[parent_loc][location_id][mbc_name][product_id][uom_id]['adjustment']['uop_qty'] += uop_qty
							stock[parent_loc][location_id][mbc_name][product_id][uom_id]['adjustment']['uom_qty'] += qty
							stock[parent_loc][location_id][mbc_name][product_id][uom_id]['adjustment']['uom_qty_value'] += amount
						else:
							if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
								stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
							if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
								stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
							if 'adjustment' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
								stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'adjustment':{
									'uop_qty' : 0.0,
									'uom_qty' : 0.0,
									'uom_qty_value' : 0.0,
									}})
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uop_qty'] += uop_qty
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uom_qty'] += qty
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['adjustment']['uom_qty_value'] += amount
		
			#############################################################################
			############################## CLOSING STOCK ################################
			#############################################################################
			query_closing1 = "SELECT sl.name as loc_name, sl2.name as parent_loc,\
				(case pp.internal_type \
					when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
					when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
					when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
					when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
					else '' end) as blend_name,pp.name_template as prod_name,q1.* \
				FROM (SELECT * FROM get_closing_fifo(to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+\
				",array"+str(internal_locations)+")) q1 \
				LEFT JOIN product_product pp on q1.prod_id=pp.id \
				LEFT JOIN mrp_blend_code mbc on pp.blend_code=mbc.id \
				LEFT JOIN stock_location sl on q1.loc_id=sl.id \
				LEFT JOIN product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				LEFT JOIN product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				LEFT JOIN stock_location sl1 on sl.location_id = sl1.id \
				LEFT JOIN stock_location sl2 on sl1.location_id=sl2.id \
				ORDER BY sl2.name asc ,sl.name asc,mbc.name asc;"
			cr.execute(query_closing1)
			result_closing1 = cr.fetchall()
			if result_closing1:
				for loc_name, parent_loc, mbc_name, prod_name, location_id, product_id, tracking_id, uop_id, uop_qty, uom_id, qty, amount in result_closing1:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if parent_loc not in stock.keys():
						stock.update({parent_loc:{}})
					if location_id not in stock[parent_loc].keys():
						stock[parent_loc].update({location_id:{}})
					if mbc_name not in stock[parent_loc][location_id].keys():
						stock[parent_loc][location_id].update({mbc_name:{}})
					if product_id not in stock[parent_loc][location_id][mbc_name].keys():
						stock[parent_loc][location_id][mbc_name].update({product_id:{}})
					if context.get('internal_type','Raw Material') == 'Raw Material':
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({uom_id:{}})
						if 'closing' not in stock[parent_loc][location_id][mbc_name][product_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][uom_id].update({'closing':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['closing']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['closing']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][uom_id]['closing']['uom_qty_value'] += amount
					else:
						if tracking_id not in stock[parent_loc][location_id][mbc_name][product_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id].update({tracking_id:{}})
						if uom_id not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id].update({uom_id:{}})
						if 'closing' not in stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].keys():
							stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id].update({'closing':{
								'uop_qty' : 0.0,
								'uom_qty' : 0.0,
								'uom_qty_value' : 0.0,
								}})
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['closing']['uop_qty'] += uop_qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['closing']['uom_qty'] += qty
						stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uom_id]['closing']['uom_qty_value'] += amount
		return stock, available_parent_loc, available_loc, available_prod

	def get_stock_valuation_by_location(self, cr, uid, ids, context=None):
		what = context.get('what',[])
		stock = {}
		if context is None:
			context = {}
		
		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		uom_obj = self.pool.get('product.uom')
		
		states = context.get('states',[])
		what = context.get('what',())
		
		res = {}
		if context.get('location', False):
			res = {}.fromkeys(context.get('location'), {})
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
		if context.get('compute_child',True):
			child_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids = child_location_ids or location_ids
		location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		opening_location = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		internal_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view'),('usage','=','internal')])
		customer_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','customer'),('usage','!=','view')])
		supplier_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','supplier'),('usage','!=','view')])
		production_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','production'),('usage','!=','view')])
		adjustment_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','inventory'),('usage','!=','view')])
		issue_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','in',('internal','production','inventory')),('usage','!=','view')])
		issue_locations2 = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','in',('internal','inventory')),('usage','!=','view')])
		incoming_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','in',('supplier','production'))])
		closing_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])

		locsss = self.pool.get('stock.location').browse(cr,uid,location_ids)
		parent_location_ids = [ll.location_id.location_id.id for ll in locsss if ll.location_id and ll.location_id.location_id and ll.location_id.location_id.id]
		parent_location_ids = list(set(parent_location_ids))
		parent_location_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',parent_location_ids)],order="name asc")
		parent_locations = self.pool.get('stock.location').browse(cr,uid,parent_location_ids)
		parent_location_datas = [ppx.name for ppx in parent_locations]
		
		del(stock)
		stock = {}.fromkeys(parent_location_datas, {})
		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)
		available_prod = []
		available_loc = []
		available_parent_loc = []

		if ids:
			query_opening = "select \
				sl.name as loc_name, sl2.name as parent_loc,mbc.name as blend_name,pp.name_template as prod_name,\
				q1.* from (select * from get_opening_2(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+\
				str(ids)+",array"+str(location_ids)+",array"+str(location_ids)+")) q1 left join product_product pp on q1.prod_id=pp.id \
				left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
				left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				left join stock_location sl1 on sl.location_id = sl1.id \
				left join stock_location sl2 on sl1.location_id=sl2.id \
				order by sl2.name asc ,sl.name asc,mbc.name asc,pp.name_template asc;"
			cr.execute(query_opening)
			result_open1 = cr.fetchall()
			if result_open1:
				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_open1:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if not stock.get(parent_loc,False):
						available_parent_loc.append(parent_loc)
						stock[parent_loc]={location_id:{mbc_name:{product_id:{'opening':{"uom_qty":qty}}}}}
					else:
						if not stock[parent_loc].get(location_id,False):
							stock[parent_loc][location_id]={mbc_name:{product_id:{'opening':{"uom_qty":qty}}}}
						else:
							if not stock[parent_loc][location_id].get(mbc_name,False):
								stock[parent_loc][location_id][mbc_name]={product_id:{'opening':{"uom_qty":qty}}}
							else:
								if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
									stock[parent_loc][location_id][mbc_name][product_id]={'opening':{"uom_qty":qty}}
								else:
									if not stock[parent_loc][location_id][mbc_name][product_id].get('opening',False):
										stock[parent_loc][location_id][mbc_name][product_id]['opening']={"uom_qty":qty}
									else:
										stock[parent_loc][location_id][mbc_name][product_id]['opening']={"uom_qty":qty}

			query_transfer = "select \
				sl.name as loc_name, sl2.name as parent_loc,mbc.name as blend_name,pp.name_template as prod_name,\
				q1.* from (select * from get_transfers(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
				to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
				array"+str(production_locations)+",array"+str(supplier_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
				left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
				left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				left join stock_location sl1 on sl.location_id = sl1.id \
				left join stock_location sl2 on sl1.location_id=sl2.id \
				order by sl2.name asc ,sl.name asc,mbc.name asc,pp.name_template asc;"
			cr.execute(query_transfer)
			result_transfer = cr.fetchall()
			if result_transfer:
				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_transfer:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if not stock.get(parent_loc,False):
						available_parent_loc.append(parent_loc)
						stock[parent_loc]={location_id:{mbc_name:{product_id:{'transfer':{"uom_qty":qty}}}}}
					else:
						if not stock[parent_loc].get(location_id,False):
							stock[parent_loc][location_id]={mbc_name:{product_id:{'transfer':{"uom_qty":qty}}}}
						else:
							if not stock[parent_loc][location_id].get(mbc_name,False):
								stock[parent_loc][location_id][mbc_name]={product_id:{'transfer':{"uom_qty":qty}}}
							else:
								if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
									stock[parent_loc][location_id][mbc_name][product_id]={'transfer':{"uom_qty":qty}}
								else:
									if not stock[parent_loc][location_id][mbc_name][product_id].get('transfer',False):
										stock[parent_loc][location_id][mbc_name][product_id]['transfer']={"uom_qty":qty}
									else:
										stock[parent_loc][location_id][mbc_name][product_id]['transfer']={"uom_qty":qty}

			query_outgoing1 = "select \
				sl.name as loc_name, sl2.name as parent_loc,mbc.name as blend_name,pp.name_template as prod_name,\
				q1.* from (select * from get_outgoing_fg_2(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
				to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
				array"+str(customer_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
				left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
				left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				left join stock_location sl1 on sl.location_id = sl1.id \
				left join stock_location sl2 on sl1.location_id=sl2.id \
				order by sl2.name asc ,sl.name asc,mbc.name asc,pp.name_template asc;"

			cr.execute(query_outgoing1)
			result_outgoing1 = cr.fetchall()
			if result_outgoing1:
				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_outgoing1:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)
				move_ids = self.pool.get('stock.move').search(cr,uid,[('type','=','out'),('date','>=',from_date),('date','<=',to_date),
									('location_id','in',location_ids),('location_dest_id','in',customer_locations),('product_id','in',available_prod),('state','=','done')],order="product_id asc")
				fob = {}
				for move in self.pool.get('stock.move').browse(cr,uid,move_ids):
					parent_ll = move.location_id.location_id.location_id.name
					loc_ll = move.location_id.id
					bc_ll = move.product_id.blend_code.name
					prod_ll = move.product_id.id
					# fob_rate = move.fob_rate*uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, to_uom_id=move.product_id.uom_id.id) or 0.0
					fob_rate = move.fob_rate*uom_obj._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, move.product_id.uom_id, context=context) or 0.0

					if not fob.get(parent_ll,False):
						fob.update({
							parent_ll:{loc_ll:{bc_ll:{prod_ll:{'total_fob_rate':fob_rate,'total_trans':1}}}}
							})
					else:
						if not fob[parent_ll].get(loc_ll,False):
							fob[parent_ll].update({
								loc_ll:{bc_ll:{prod_ll:{'total_fob_rate':fob_rate,'total_trans':1}}}
								})
						else:
							if not fob[parent_ll][loc_ll].get(bc_ll,False):
								fob[parent_ll][loc_ll].update({
									bc_ll:{prod_ll:{'total_fob_rate':fob_rate,'total_trans':1}}
									})
							else:
								if not fob[parent_ll][loc_ll][bc_ll].get(prod_ll,False):
									fob[parent_ll][loc_ll][bc_ll].update({
										prod_ll:{'total_fob_rate':fob_rate,'total_trans':1}
										})
								else:
									curr_fob = fob[parent_ll][loc_ll][bc_ll][prod_ll].get('total_fob_rate',0.0)+fob_rate
									curr_trans = fob[parent_ll][loc_ll][bc_ll][prod_ll].get('total_trans',1)+1
									fob[parent_ll][loc_ll][bc_ll][prod_ll].update({
										'total_fob_rate':curr_fob,
										'total_trans':curr_trans
										})

				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_outgoing1:
					try:
						fob_to_apply = fob[parent_loc][location_id][mbc_name][product_id]['total_fob_rate'] or 0.0
						n_move = fob[parent_loc][location_id][mbc_name][product_id]['total_trans'] or 0.0
					except:
						fob_to_apply = 0.0
						
					if not stock.get(parent_loc,False):
						available_parent_loc.append(parent_loc)
						stock[parent_loc]={location_id:{mbc_name:{product_id:{'outgoing':{"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}}}}}
					else:
						if not stock[parent_loc].get(location_id,False):
							stock[parent_loc][location_id]={mbc_name:{product_id:{'outgoing':{"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}}}}
						else:
							if not stock[parent_loc][location_id].get(mbc_name,False):
								stock[parent_loc][location_id][mbc_name]={product_id:{'outgoing':{"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}}}
							else:
								if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
									stock[parent_loc][location_id][mbc_name][product_id]={'outgoing':{"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}}
								else:
									if not stock[parent_loc][location_id][mbc_name][product_id].get('outgoing',False):
										stock[parent_loc][location_id][mbc_name][product_id]['outgoing']={"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}
									else:
										stock[parent_loc][location_id][mbc_name][product_id]['outgoing']={"uom_qty":qty,'total_fob':fob_to_apply,"n_move":n_move}




			query_outgoing_return = "select \
				sl.name as loc_name, sl2.name as parent_loc,mbc.name as blend_name,pp.name_template as prod_name,\
				q1.* from (select * from get_outgoing_fg_return_2(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
				to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
				array"+str(customer_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
				left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
				left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
				left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
				left join stock_location sl1 on sl.location_id = sl1.id \
				left join stock_location sl2 on sl1.location_id=sl2.id \
				order by sl2.name asc ,sl.name asc,mbc.name asc,pp.name_template asc;"

			cr.execute(query_outgoing_return)
			result_query_outgoing_return = cr.fetchall()
			if result_query_outgoing_return:
				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_query_outgoing_return:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)

					if not stock.get(parent_loc,False):
						available_parent_loc.append(parent_loc)
						stock[parent_loc]={location_id:{mbc_name:{product_id:{'out_return':{"uom_qty":qty}}}}}
					else:
						if not stock[parent_loc].get(location_id,False):
							stock[parent_loc][location_id]={mbc_name:{product_id:{'out_return':{"uom_qty":qty}}}}
						else:
							if not stock[parent_loc][location_id].get(mbc_name,False):
								stock[parent_loc][location_id][mbc_name]={product_id:{'out_return':{"uom_qty":qty}}}
							else:
								if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
									stock[parent_loc][location_id][mbc_name][product_id]={'out_return':{"uom_qty":qty}}
								else:
									if not stock[parent_loc][location_id][mbc_name][product_id].get('out_return',False):
										stock[parent_loc][location_id][mbc_name][product_id]['out_return']={"uom_qty":qty}
									else:
										stock[parent_loc][location_id][mbc_name][product_id]['out_return']={"uom_qty":qty}


			query_closing = "select sl.name as loc_name, sl2.name as parent_loc,mbc.name as blend_name,pp.name_template as prod_name,q1.* \
					from (select * from get_closing_2(to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+\
					",array"+str(location_ids)+")) q1 left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
					order by sl2.name asc ,sl.name asc,mbc.name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"

			cr.execute(query_closing)
			result_query_closing = cr.fetchall()

			if result_query_closing:
				for loc_name,parent_loc,mbc_name,prod_name,location_id,product_id,qty in result_query_closing:
					if parent_loc not in available_parent_loc:
						available_parent_loc.append(parent_loc)
					if location_id not in available_loc:
						available_loc.append(location_id)
					if product_id not in available_prod:
						available_prod.append(product_id)
					
					if not stock.get(parent_loc,False):
						available_parent_loc.append(parent_loc)
						stock[parent_loc]={location_id:{mbc_name:{product_id:{'closing':{"uom_qty":qty}}}}}
					else:
						if not stock[parent_loc].get(location_id,False):
							stock[parent_loc][location_id]={mbc_name:{product_id:{'closing':{"uom_qty":qty}}}}
						else:
							if not stock[parent_loc][location_id].get(mbc_name,False):
								stock[parent_loc][location_id][mbc_name]={product_id:{'closing':{"uom_qty":qty}}}
							else:
								if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
									stock[parent_loc][location_id][mbc_name][product_id]={'closing':{"uom_qty":qty}}
								else:
									if not stock[parent_loc][location_id][mbc_name][product_id].get('closing',False):
										stock[parent_loc][location_id][mbc_name][product_id]['closing']={"uom_qty":qty}
									else:
										stock[parent_loc][location_id][mbc_name][product_id]['closing']={"uom_qty":qty}

		available_parent_loc=sorted(list(set(available_parent_loc)))
		if stock:
			for s in stock.keys():
				if s not in available_parent_loc:
					# stock[s]={}	
					stock.pop(s)
		
		return stock,available_parent_loc,available_loc,available_prod






	def get_product_stock_uncomputed_by_location(self, cr, uid, ids, context=None):
		# print "self, cr, uid, ids, context=None*******************",cr, uid, ids, context
		""" Finds whether product is available or not in particular warehouse.
		@return: Dictionary of values
		"""
		what = context.get('what',[])
		stock = {}
		if context is None:
			context = {}
		
		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		
		states = context.get('states',[])
		what = context.get('what',())
		
		res = {}
		if context.get('location', False):
			res = {}.fromkeys(context.get('location'), {})
		if not ids:
			# print "--------------------",res
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
		location_ids = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		opening_location = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		internal_locations = self.pool.get('stock.location').search(cr,uid,[('id','in',location_ids),('usage','!=','view'),('usage','=','internal')])
		customer_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','customer'),('usage','!=','view')])
		supplier_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','supplier'),('usage','!=','view')])
		production_locations = self.pool.get('stock.location').search(cr,uid,[('usage','=','production'),('usage','!=','view')])
		adjustment_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','=','inventory'),('usage','!=','view')])
		issue_locations = self.pool.get('stock.location').search(cr,uid,[('usage','in',('internal','production','inventory')),('usage','!=','view')])
		issue_locations2 = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','in',('internal','inventory')),('usage','!=','view')])
		incoming_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('usage','in',('supplier','production'))])
		closing_locations = self.pool.get('stock.location').search(cr,uid,[('child_ids','=',False),('id','in',location_ids),('usage','!=','view')])
		
		locsss = self.pool.get('stock.location').browse(cr,uid,location_ids)
		# print "========================",locsss
		parent_location_ids = [ll.location_id and ll.location_id.location_id and ll.location_id.location_id.id or False for ll in locsss]
		# print "**********************",parent_location_ids
		parent_location_ids = list(set(parent_location_ids))
		parent_location_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',parent_location_ids)],order="name asc")
		parent_locations = self.pool.get('stock.location').browse(cr,uid,parent_location_ids)
		parent_location_datas = [ppx.name for ppx in parent_locations]
		# print "location_ids---------------------->",parent_location_datas
		del(stock)
		stock = {}.fromkeys(parent_location_datas, {})
		# print "======================",stock
		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)

		where_opening = [tuple(location_ids),tuple(ids),tuple(states)]
		where_incoming_purchase = [tuple(supplier_locations),tuple(location_ids),tuple(ids),tuple(states)]
		where_incoming_production = [tuple(production_locations),tuple(location_ids),tuple(ids),tuple(states)]
		where_outgoing = [tuple(internal_locations),tuple(customer_locations),tuple(ids),tuple(states)]
		where_issue = [tuple(internal_locations),tuple(issue_locations),tuple(ids),tuple(states)]
		where_issue2 = [tuple(issue_locations2),tuple(internal_locations),tuple(ids),tuple(states)]
		where_transfer = [tuple(internal_locations),tuple(internal_locations),tuple(ids),tuple(states)]
		where_adjustment1 = [tuple(internal_locations),tuple(issue_locations),tuple(ids),tuple(states)]
		where_adjustment2 = [tuple(adjustment_locations),tuple(internal_locations),tuple(ids),tuple(states)]
		# where_closing = 

		result_open1 = False
		result_open2 = False
		result_incoming1 = False
		result_incoming2 = False
		result_incoming3 = False
		result_incoming4 = False
		result_outgoing1 = False
		result_outgoing2 = False
		result_issue1 = False
		result_issue2 = False
		result_closing1 = False
		available_uop = []
		available_prod = []
		available_loc = []
		available_parent_loc = []
		available_track = []
		available_blend = []
		date_str_opening = False
		date_val_opening = False
		date_str_incoming = False
		date_val_incoming = False
		date_str_outgoing = False
		date_val_outgoing = False
		date_str_issue = False
		date_val_issue = False
		date_str_issue2 = False
		date_val_issue2 = False
		if ids:
			if from_date and to_date:
				date_str_incoming = 'sm.date>=%s and sm.date<=%s '
				where_incoming_purchase.append(tuple([from_date]))
				where_incoming_purchase.append(tuple([to_date]))
				where_incoming_production.append(tuple([from_date]))
				where_incoming_production.append(tuple([to_date]))
				date_str_outgoing = 'sm.date>=%s and sm.date<=%s '
				where_outgoing.append(tuple([from_date]))
				where_outgoing.append(tuple([to_date]))
				date_str_issue = 'sm.date>=%s and sm.date<=%s '
				where_issue.append(tuple([from_date]))
				where_issue.append(tuple([to_date]))
				date_str_issue2 = 'sm.date>=%s and sm.date<=%s '
				where_issue2.append(tuple([from_date]))
				where_issue2.append(tuple([to_date]))
			elif from_date:
				date_str_incoming = 'sm.date>=%s '
				date_val_incoming = [from_date]
				date_str_outgoing = 'sm.date>=%s '
				date_val_outgoing = [from_date]
				date_str_issue = 'sm.date>=%s '
				date_val_issue = [from_date]
				date_str_issue2 = 'sm.date>=%s '
				date_val_issue2 = [from_date]
			elif to_date:
				date_str_opening = ' sm.date<%s '
				date_val_opening = [to_date]
				date_str_incoming = 'sm.date<=%s '
				date_val_incoming = [to_date]
				date_str_outgoing = 'sm.date<=%s '
				date_val_outgoing = [to_date]
				date_str_issue = 'sm.date<=%s '
				date_val_issue = [to_date]
				date_str_issue2 = 'sm.date<=%s '
				date_val_issue2 = [to_date]

			if date_val_opening:
				where_opening.append(tuple(date_val_opening))

			if date_val_incoming:
				where_incoming_purchase.append(tuple(date_val_incoming))
				where_incoming_production(tuple(date_val_incoming))

			if date_val_outgoing:
				where_outgoing.append(tuple(date_val_outgoing))
			
			if date_val_issue:
				where_issue.append(tuple(date_val_issue))
			
			if date_val_issue2:
				where_issue2.append(tuple(date_val_issue2))

			blend_name = "(case pp.internal_type \
				when 'Finish' then coalesce(left(pp.default_code,3),mbc.name) \
				when 'Finish_others' then coalesce(left(pp.default_code,3),mbc.name) \
				when 'Scrap' then coalesce(left(pp.default_code,3),mbc.name) \
				when 'Waste' then coalesce(left(pp.default_code,3),mbc.name) \
				when 'Raw Material' then coalesce(left(pp.default_code,3),prtc.code) \
				when 'Stores' then coalesce(left(pp.default_code,3),pfsc.code) \
				when 'Packing' then coalesce(left(pp.default_code,3),pfsc.code) \
				else '' end)"
			
			group_query = ""
			if context.get('internal_type','Finish') == 'Finish' :
				columns_function_result = " q1.loc_id, q1.prod_id, q1.uop_id, q1.uom_qty, q1.uop_qty, q1.track_id"
			if context.get('internal_type','Finish') == 'Raw Material' :
				columns_function_result = " q1.loc_id, q1.prod_id, 0 as product_uop_id, sum(q1.uom_qty) as uom_qty, sum(q1.uop_qty) as uop_qty, q1.track_id"
				group_query = " group by sl.name, sl2.name, blend_name, pp.name_template, pp.count, pp.sd_type, pp.wax,\
								q1.loc_id, q1.prod_id, product_uop_id, q1.track_id"
			elif context.get('internal_type','Finish') in ('Stores','Packing','Finish_others','Waste','Scrap','Fixed'):
				columns_function_result = " q1.loc_id, q1.prod_id, 0 as product_uop_id, sum(q1.uom_qty) as uom_qty, sum(q1.uop_qty) as uop_qty, 0 as tracking_id "
				group_query = " group by sl.name, sl2.name, blend_name, pp.name_template, pp.count, pp.sd_type, pp.wax,\
								q1.loc_id, q1.prod_id, product_uop_id, tracking_id"

			##############################################################################
			############################## OPENING STOCK #################################
			##############################################################################

			# print "################### OPENING STOCK ###########################"
			query_opening = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
				pp.name_template as prod_name, pp.count, pp.sd_type, pp.wax, "+columns_function_result+" \
				from (select * from get_opening(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+\
					str(ids)+",array"+str(location_ids)+",array"+str(location_ids)+")) q1 \
					left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl on q1.loc_id=sl.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
				"+group_query+ "\
				order by sl2.name asc ,sl.name asc, blend_name asc, pp.count asc, pp.sd_type asc, pp.wax asc;"
			# print "query_opening===================",query_opening
			cr.execute(query_opening)
			result_open1 = cr.fetchall()
			
			##############################################################################
			############################## INCOMING STOCK ################################ 
			##############################################################################
			
			# print "################### INCOMING STOCK ###########################"
			if context.get('internal_type','Finish') in ('Finish','Finish_others','Waste','Scrap','Fixed'):
				############### incoming from PRODUCTION+SUPPLIER to INTERNAL #######################
				query_incoming1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name, pp.count, pp.sd_type, pp.wax, "+columns_function_result+" \
					from (select * from get_incoming(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
						array"+str(production_locations)+",array"+str(supplier_locations)+") ) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc, blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				# print "=======================",query_incoming1
				cr.execute(query_incoming1)
				result_incoming1 = cr.fetchall()
			elif context.get('internal_type','Finish') in ('Stores','Packing','Raw Material'):
				############### incoming from SUPPLIER to INTERNAL #######################
				query_incoming1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name, pp.count, pp.sd_type, pp.wax,"+columns_function_result+" \
					from (select * from get_incoming(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(internal_locations)+",\
						array"+str([0,0,0])+",array"+str(supplier_locations)+") ) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				# print "=======================",query_incoming1
				cr.execute(query_incoming1)
				result_incoming1 = cr.fetchall()

			# print "################### RETURN INCOMING STOCK ###########################"
			if context.get('internal_type','Finish') in ('Finish','Finish_others','Waste','Scrap','Fixed'):
				############### return incoming from INTERNAL to SUPPLIER+PRODUCTION #######################
				query_incoming2 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name, pp.count, pp.sd_type, pp.wax,"+columns_function_result+" \
					from (select * from get_incoming_return(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(production_locations)+",array"+str(supplier_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_incoming2)
				result_incoming2 = cr.fetchall()
			elif context.get('internal_type','Finish') in ('Stores','Packing','Raw Material'):
				############### return incoming from INTERNAL to SUPPLIER #######################
				query_incoming2 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_incoming_return(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str([0,0,0])+",array"+str(supplier_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_incoming2)
				result_incoming2 = cr.fetchall()

			###############################################################################
			############################### OUTGOING STOCK ################################ 
			###############################################################################

			if context.get('internal_type','Finish') in ('Finish','Finish_others','Waste','Scrap','Fixed'):
				############### outgoing from INTERNAL to CUSTOMER #######################
				query_outgoing1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(customer_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				# print "xxxxxxxxxxxxxxxxxxxxxxxxxxx",query_outgoing1
				cr.execute(query_outgoing1)
				result_outgoing1 = cr.fetchall()
				
				############### return outgoing from CUSTOMER to INTERNAL #######################
				query_outgoing2 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg_return(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(customer_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				# print "======================",query_outgoing1
				cr.execute(query_outgoing2)
				result_outgoing2 = cr.fetchall()
			elif context.get('internal_type','Finish') in ('Raw Material'):
				############### outgoing from INTERNAL to PRODUCTION #######################
				query_outgoing1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(production_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				
				cr.execute(query_outgoing1)
				result_outgoing1 = cr.fetchall()
				
				############### return outgoing from PRODUCTION to INTERNAL #######################
				query_outgoing2 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg_return(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(production_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_outgoing2)
				result_outgoing2 = cr.fetchall()
			elif context.get('internal_type','Finish') in ('Stores','Packing'):
				############### outgoing from INTERNAL to ADJUSTMENT(as Consume Product) #######################
				query_outgoing1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				
				cr.execute(query_outgoing1)
				result_outgoing1 = cr.fetchall()
				
				############### return outgoing from ADJUSTMENT(as Consume Product) to INTERNAL #######################
				query_outgoing2 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_outgoing_fg_return(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_outgoing2)
				result_outgoing2 = cr.fetchall()

			##################################################################################
			############################### ADJUSTMENT STOCK ################################# 
			##################################################################################

			if context.get('internal_type','Finish') in ('Finish','Finish_others','Waste','Scrap','Raw Material','Fixed'):
				############### adjustment or internal transfer from INTERNAL/INVENTORY to INTERNAL/INVENTORY #######################
				query_issue1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_issue(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_issue1)
				result_issue1 = cr.fetchall()
			elif context.get('internal_type','Finish') in ('Stores','Packing'):
				############### adjustment as Opname from INTERNAL to ADJUSTMENT #######################
				query_issue1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
					pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
					from (select * from get_opname_moves(to_timestamp('"+from_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,\
						to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+",\
						array"+str(issue_locations)+")) q1 left join product_product pp on q1.prod_id=pp.id \
						left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
						left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
						left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
						left join stock_location sl1 on sl.location_id = sl1.id \
						left join stock_location sl2 on sl1.location_id=sl2.id \
					"+group_query+"\
					order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
				cr.execute(query_issue1)
				result_issue1 = cr.fetchall()
		
			#############################################################################
			############################## CLOSING STOCK ################################
			#############################################################################

			query_closing1 = "select sl.name as loc_name, sl2.name as parent_loc,"+blend_name+" as blend_name,\
				pp.name_template as prod_name,pp.count,pp.sd_type,pp.wax,"+columns_function_result+" \
				from (select * from get_closing(to_timestamp('"+to_date+"','YYYY-MM-DD HH24:MI:SS')::timestamp without time zone,array"+str(ids)+",array"+str(location_ids)+\
					",array"+str(location_ids)+")) q1 left join product_product pp on q1.prod_id=pp.id \
					left join mrp_blend_code mbc on pp.blend_code=mbc.id left join stock_location sl on q1.loc_id=sl.id \
					left join product_first_segment_code pfsc on pp.first_segment_code=pfsc.id \
					left join product_rm_type_category prtc on pp.rm_class_id=prtc.id \
					left join stock_location sl1 on sl.location_id = sl1.id \
					left join stock_location sl2 on sl1.location_id=sl2.id \
				"+group_query+"\
				order by sl2.name asc ,sl.name asc,blend_name asc,pp.count asc, pp.sd_type asc, pp.wax asc;"
			# print "------------------------",query_closing1
			cr.execute(query_closing1)
			result_closing1 = cr.fetchall()

			# print "--------------------->",stock
			############################################################################
			############################ OPENING MAPPING ############################### 
			############################################################################
			if result_open1:
				# n=0
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_open1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'opening':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('opening',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') == 'Raw Material':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_open1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'opening':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('opening',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_open1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'opening':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'opening':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('opening',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['opening']={"uom_qty":qty,"uop_qty":uop_qty}													
			# print "stock====opening===========",stock
			
			############################################################################
			############################ INCOMING MAPPING ############################## 
			############################################################################
			if result_incoming1:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming1:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)
						# if product_id==1792:
						# 	print "\n^^^^^^^^^^product_id,uop_id,qty,uop_qty,tracking_id^^^^^^^^^^^^^",product_id,uop_id,qty,uop_qty,tracking_id
							# print "\n*************1**************",stock[parent_loc][location_id][mbc_name][count][singd][wax]

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('incoming',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['incoming']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['incoming']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'incoming':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('incoming',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['incoming']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['incoming']={"uom_qty":qty,"uop_qty":uop_qty}

					# if product_id==1792:
					# 	print "\n**************2*************",stock[parent_loc][location_id][mbc_name][count][singd][wax][1792][15145][481]
			# print "stock====incoming===========",stock

			############################################################################
			############################ INCOMING RETURN MAPPING ####################### 
			############################################################################
			if result_incoming2:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming2:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('in_return',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['in_return']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['in_return']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming2:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'in_return':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('in_return',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['in_return']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['in_return']={"uom_qty":qty,"uop_qty":uop_qty}
			# print "stock====in_return===========",stock											

			############################################################################
			############################ OUTGOING MAPPING ############################## 
			############################################################################
			if result_outgoing1:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing1:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('outgoing',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['outgoing']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['outgoing']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'outgoing':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('outgoing',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['outgoing']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['outgoing']={"uom_qty":qty,"uop_qty":uop_qty}
									
			############################################################################
			############################ OUTGOING RETURN MAPPING #######################
			############################################################################
			if result_outgoing2:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing2:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('out_return',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['out_return']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['out_return']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing2:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'out_return':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('out_return',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['out_return']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['out_return']={"uom_qty":qty,"uop_qty":uop_qty}
			
			############################################################################
			############################ ADJUSTMENT MAPPING ############################
			############################################################################
			if result_issue1:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_issue1:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'issue':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('issue',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['issue']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['issue']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_issue1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'issue':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'issue':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('issue',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['issue']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['issue']={"uom_qty":qty,"uop_qty":uop_qty}
	
			############################################################################
			############################# CLOSING LOOP #################################
			############################################################################
			if result_closing1:
				if context.get('internal_type','Finish') == 'Finish':
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_closing1:
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={count:{singd:{wax:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(count,False):
										stock[parent_loc][location_id][mbc_name][count]={singd:{wax:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][count].get(singd,False):
											stock[parent_loc][location_id][mbc_name][count][singd]={wax:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][count][singd].get(wax,False):
												stock[parent_loc][location_id][mbc_name][count][singd][wax]={product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
											else:
												if not stock[parent_loc][location_id][mbc_name][count][singd][wax].get(product_id,False):
													stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id]={tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}
												else:
													if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id].get(tracking_id,False):
														stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id]={uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}
													else:
														if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id].get(uop_id,False):
															stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]={'closing':{"uom_qty":qty,"uop_qty":uop_qty}}
														else:
															if not stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id].get('closing',False):
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['closing']={"uom_qty":qty,"uop_qty":uop_qty}
															else:
																stock[parent_loc][location_id][mbc_name][count][singd][wax][product_id][tracking_id][uop_id]['closing']={"uom_qty":qty,"uop_qty":uop_qty}
				elif context.get('internal_type','Finish') in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material','Fixed'):
					for loc_name,parent_loc,mbc_name,prod_name,count,singd,wax,location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_closing1:
						# n+=1
						# print "=-=-------------------",location_id,product_id,uop_id,qty,uop_qty,tracking_id
						if parent_loc not in available_parent_loc:
							available_parent_loc.append(parent_loc)
						if uop_id not in available_uop:
							available_uop.append(uop_id)
						if location_id not in available_loc:
							available_loc.append(location_id)
						if product_id not in available_prod:
							available_prod.append(product_id)
						if tracking_id not in available_track:
							available_track.append(tracking_id)

						if not stock.get(parent_loc,False):
							available_parent_loc.append(parent_loc)
							stock[parent_loc]={location_id:{mbc_name:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}}
						else:
							if not stock[parent_loc].get(location_id,False):
								stock[parent_loc][location_id]={mbc_name:{product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}}
							else:
								if not stock[parent_loc][location_id].get(mbc_name,False):
									stock[parent_loc][location_id][mbc_name]={product_id:{tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}}
								else:
									if not stock[parent_loc][location_id][mbc_name].get(product_id,False):
										stock[parent_loc][location_id][mbc_name][product_id]={tracking_id:{uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}}
									else:
										if not stock[parent_loc][location_id][mbc_name][product_id].get(tracking_id,False):
											stock[parent_loc][location_id][mbc_name][product_id][tracking_id]={uop_id:{'closing':{"uom_qty":qty,"uop_qty":uop_qty}}}
										else:
											if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id].get(uop_id,False):
												stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]={'closing':{"uom_qty":qty,"uop_qty":uop_qty}}
											else:
												if not stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id].get('closing',False):
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['closing']={"uom_qty":qty,"uop_qty":uop_qty}
												else:
													stock[parent_loc][location_id][mbc_name][product_id][tracking_id][uop_id]['closing']={"uom_qty":qty,"uop_qty":uop_qty}


		available_parent_loc=sorted(list(set(available_parent_loc)))
		if stock:
			for s in stock.keys():
				if s not in available_parent_loc:
					# stock[s]={}	
					stock.pop(s)
		
		return stock,available_parent_loc,available_loc,available_prod,available_track,available_uop