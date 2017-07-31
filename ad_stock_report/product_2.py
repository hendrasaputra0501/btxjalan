from openerp.osv import fields,osv

class product_product(osv.Model):
	_inherit = "product.product"
	_columns = {

	}

	def get_product_stock_uncomputed_by_location(self, cr, uid, ids, context=None):
		# print "self, cr, uid, ids, context=None*******************",cr, uid, ids, context
		""" Finds whether product is available or not in particular warehouse.
		@return: Dictionary of values
		"""
		what = context.get('what',[])
		if context is None:
			context = {}
		
		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		
		states = context.get('states',[])
		what = context.get('what',())
		if not ids:
			ids = self.search(cr, uid, [])
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
		# build the list of ids of children of the location given by id
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
		#print "location_ids---------------------->",incoming_locations
		stock=False
		stock = {}.fromkeys(location_ids, {})
		# print "======================",stock
		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)

		#########################################################################
		############################### OPENING #################################
		#########################################################################
		# print "############################### OPENING #################################"
		where_opening = [tuple(location_ids),tuple(ids),tuple(states)]
		where_incoming = [tuple(incoming_locations),tuple(location_ids),tuple(ids),tuple(states)]
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
		result_outgoing1 = False
		result_outgoing2 = False
		result_issue1 = False
		result_issue2 = False
		available_uop = []
		available_prod = []
		available_loc = []
		available_track = []
		if ids:
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
				if from_date and to_date:
					date_str_incoming = 'sm.date>=%s and sm.date<=%s '
					where_incoming.append(tuple([from_date]))
					where_incoming.append(tuple([to_date]))
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
					where_incoming.append(tuple(date_val_incoming))
				if date_val_outgoing:
					where_outgoing.append(tuple(date_val_outgoing))
				if date_val_issue:
					where_issue.append(tuple(date_val_issue))
				if date_val_issue2:
					where_issue2.append(tuple(date_val_issue2))

				# print "###################OPENING###########################"
				cr.execute('select location_dest_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_opening and ' and  ' +date_str_opening+'  '  or ' ') +' \
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_dest_id, product_id,product_uop,tracking_id \
					order by location_dest_id, product_id,tracking_id, product_uop \
					',tuple(where_opening))
				
		 		result_open1 = cr.fetchall()
				cr.execute('select location_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_opening and ' and  ' +date_str_opening+'  '  or ' ') +' \
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_id, product_id,product_uop,tracking_id \
					order by location_id, product_id,tracking_id, product_uop \
					',tuple(where_opening))
				result_open2 = cr.fetchall()
				#########################################################################
				############################### INCOMING ################################ 
				#########################################################################
				# print "###################INCOMING###########################"
				
				cr.execute('select location_dest_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_incoming and ' and  ' +date_str_incoming+'  '  or ' ') +' \
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_dest_id, product_id,product_uop,tracking_id \
					order by location_dest_id, product_id,tracking_id, product_uop \
					',tuple(where_incoming))
				result_incoming1 = cr.fetchall()

				cr.execute('select location_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_dest_id IN %s and sm.location_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_incoming and ' and  ' +date_str_incoming+'  '  or ' ') +' \
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_id, product_id,product_uop,tracking_id \
					order by location_id, product_id,tracking_id, product_uop \
					',tuple(where_incoming))
				result_incoming2 = cr.fetchall()

				#########################################################################
				############################### OUTGOING ################################ 
				#########################################################################
				# print "###################OUTGOING###########################"
				if context.get('internal_type','Finish') not in ('Packing','Raw Material'):
					cr.execute('select location_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
						left join product_uom pu_pt on pt.uom_id = pu_pt.id \
						where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
							+ (date_str_outgoing and ' and  ' +date_str_outgoing+'  '  or ' ') +' \
						order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
						group by location_id, product_id,product_uop,tracking_id \
						order by location_id, product_id,tracking_id, product_uop \
						',tuple(where_outgoing))
					result_outgoing1 = cr.fetchall()
					cr.execute('select location_dest_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
						left join product_uom pu_pt on pt.uom_id = pu_pt.id \
						where  sm.location_dest_id IN %s and sm.location_id IN %s and sm.product_id IN %s and sm.state in %s ' \
							+ (date_str_outgoing and ' and  ' +date_str_outgoing+'  '  or ' ') +' \
						order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
						group by location_dest_id, product_id,product_uop,tracking_id \
						order by location_dest_id, product_id,tracking_id, product_uop \
						',tuple(where_outgoing))
					result_outgoing2 = cr.fetchall()
				elif context.get('internal_type','Finish') in ('Raw Material'):
					# product_fg_ids = self.pool.get('product.product').search(cr,uid,[('internal_type','in',('Finish','Finish_others'))])
					# where_rm_out = where_outgoing
					# where_rm_out[2] = tuple(product_fg_ids)
					cr.execute('select location_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
						left join product_uom pu_pt on pt.uom_id = pu_pt.id \
						where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
							+ (date_str_outgoing and ' and  ' +date_str_outgoing+'  '  or ' ') +' \
						order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
						group by location_id, product_id,product_uop,tracking_id \
						order by location_id, product_id,tracking_id, product_uop \
						',tuple(where_outgoing))

					result_outgoing1 = cr.fetchall()

				#########################################################################
				###############################  ISSUE  ################################# 
				#########################################################################
				# print "###################ISSUE###########################"
				
				#print "------------",date_val_issue,date_val_issue2
				
				cr.execute('select location_dest_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_issue and ' and  ' +date_str_issue+'  '  or ' ') +' \
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_dest_id, product_id,product_uop,tracking_id \
					order by location_dest_id, product_id,tracking_id, product_uop \
					',tuple(where_issue))
				result_issue1 = cr.fetchall()
				cr.execute('select location_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
					from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
					sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
					left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
					left join product_uom pu_pt on pt.uom_id = pu_pt.id \
					where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
						+ (date_str_issue2 and ' and  ' +date_str_issue2+'  '  or ' ') +' \
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
					group by location_id, product_id,product_uop,tracking_id \
					order by location_id, product_id,tracking_id, product_uop \
					',tuple(where_issue2))
				result_issue2 = cr.fetchall()

				#########################################################################
				###############################  TRANSFER ############################### 
				#########################################################################
				
				# cr.execute('select location_dest_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id \
				# 	from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,\
				# 	sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id \
				# 	left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id \
				# 	left join product_uom pu_pt on pt.uom_id = pu_pt.id \
				# 	where  sm.location_id IN %s and sm.location_dest_id IN %s and sm.product_id IN %s and sm.state in %s ' \
				# 		+ (date_str_transfer and ' and  ' +date_str_transfer+'  '  or ' ') +' \
				# 	order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy \
				# 	group by location_dest_id, product_id,product_uop,tracking_id \
				# 	order by location_dest_id, product_id,tracking_id, product_uop \
				# 	',tuple(where_transfer))
				# result_transfer1 = cr.fetchall()

		
		
		#########################################################################
		############################ OPENING LOOP ############################### 
		#########################################################################
		if result_open1:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_open1:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)
				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('opening'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'opening':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['opening']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['opening']['uop_qty'] += uop_qty

		if result_open2:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_open2:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)

				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'opening':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('opening'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'opening':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					#print "stock4---------------",stock[4]
					stock[location_id][product_id][tracking_id][uop_id]['opening']['uom_qty'] -= qty
					stock[location_id][product_id][tracking_id][uop_id]['opening']['uop_qty'] -= uop_qty
				# stock[location_id][product_id][tracking_id][uop_id]['opening'].update({'uom_qty':curr_uom_qty,'uop_qty':curr_uop_qty})
		
		#########################################################################
		############################ INCOMING LOOP ############################## 
		#########################################################################

		if result_incoming1:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming1:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)

				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'incoming':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'incoming':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'incoming':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('incoming'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'incoming':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['incoming']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['incoming']['uop_qty'] += uop_qty

		if result_incoming2:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_incoming2:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)

				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'in_return':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'in_return':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'in_return':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('in_return'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'in_return':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['in_return']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['in_return']['uop_qty'] += uop_qty

		#########################################################################
		############################ OUTGOING LOOP ############################## 
		#########################################################################
		if result_outgoing1:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing1:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)
				#print "#############",stock[location_id],product_id
				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'outgoing':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'outgoing':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'outgoing':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('outgoing'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'outgoing':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['outgoing']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['outgoing']['uop_qty'] += uop_qty
		if result_outgoing2:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_outgoing2:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)

				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'out_return':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'out_return':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'out_return':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				if not stock[location_id][product_id][tracking_id][uop_id].has_key('out_return'):
					stock[location_id][product_id][tracking_id][uop_id].update({
						'out_return':{'uom_qty':qty,'uop_qty':uop_qty}					
						})
					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['out_return']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['out_return']['uop_qty'] += uop_qty

		#########################################################################
		############################# ISSUE LOOP ################################ 
		#########################################################################
		if result_issue1:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_issue1:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)
				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['issue']['uom_qty'] += qty
					stock[location_id][product_id][tracking_id][uop_id]['issue']['uop_qty'] += uop_qty
		if result_issue2:
			for location_id,product_id,uop_id,qty,uop_qty,tracking_id in result_issue2:
				if uop_id not in available_uop:
					available_uop.append(uop_id)
				if location_id not in available_loc:
					available_loc.append(location_id)
				if product_id not in available_prod:
					available_prod.append(product_id)
				if tracking_id not in available_track:
					available_track.append(tracking_id)
				if not stock[location_id].has_key(product_id):
					stock[location_id].update({
						product_id:{tracking_id:{uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}}}
						})
					if location_id not in available_loc:
						available_loc.append(location_id)
					continue
				if not stock[location_id][product_id].has_key(tracking_id):
					stock[location_id][product_id].update({tracking_id:{uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}}})

					continue
				if not stock[location_id][product_id][tracking_id].has_key(uop_id):
					stock[location_id][product_id][tracking_id].update({uop_id:{'issue':{'uom_qty':qty,'uop_qty':uop_qty}}})

					continue
				else:
					stock[location_id][product_id][tracking_id][uop_id]['issue']['uom_qty'] -= qty
					stock[location_id][product_id][tracking_id][uop_id]['issue']['uop_qty'] -= uop_qty
		if stock:
			for s in stock.keys():
				if s not in available_loc:
					stock[s]={}	
		# print "----------------333333333333333333333----------",stock
		return stock,available_loc,available_prod,available_track,available_uop