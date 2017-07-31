from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

from tools.translate import _
#from bsddb.dbtables import _columns

class stock_split_move(osv.TransientModel):
	_name="stock.split.move"
	_columns = {
		"move_id":fields.many2one("stock.move","Move ID"),
		"product_id":fields.many2one("product.product","Product",required=True),
		"product_qty":fields.float("Qty",required=True),
		"source_location":fields.many2one("stock.location","Source Location",required=True),
		"destination_location":fields.many2one("stock.location","Destination Location",required=True),
		"line_ids":fields.one2many("stock.split.move.line","split_id","Split Lines"),
		"dest_address_id":fields.many2one("res.partner","Partner",required=True),
		"internal_type":fields.selection([('Finish','Finish Goods'),
				('Finish_others','Finish Goods(Others)'),
				('Raw Material','Raw Material'),
				('Stores','Stores'),
				('Waste','Waste'),
				('Scrap','Scrap'),
				('Packing','Packing Material'),
				('Fixed','Fixed Asset'),
				('Mixed Lot',"Mixed"),
				],
				string='Goods Type Purpose', required=True),
			}

	def onchange_line_ids(self,cr,uid,ids,line_ids,move_id,context=None):
		if not context:context={}
		uom_obj = self.pool.get('product.uom')
		if not line_ids:
			return {}
		total=0.0
		move = self.pool.get('stock.move').browse(cr,uid,move_id,context)
		move_qty = move.product_qty or 0.0
		move_uom = move.product_uom and move.product_uom.id or False
		if move.picking_id.type=='out':
			# print "==========ini panggil================="
			for line in line_ids:
				if line[2]:
					qty = uom_obj._compute_qty(cr, uid, line[2]['product_uom'], line[2]['product_uom_qty'], move_uom)
					total += qty
			max_tolerance_qty = move_qty + (move_qty * move.sale_line_id.order_id.tolerance_percentage/100.0)
			if max_tolerance_qty < total:
				warning = {
						'title': _('Warning!'),
						'message': _('Total quantity is out of tolerance range, maximum value is %s !'% (max_tolerance_qty,))
					}

				line_ids = [[0,0,x[2]] for x in line_ids]

				line_ids = line_ids[0:len(line_ids)-1]

			return {'warning':warning,'value':{'line_ids':line_ids}}
		return {}

	def default_get(self,cr,uid,fields,context=None):
		if context is None:
			context = {}
		res = super(stock_split_move, self).default_get(cr, uid, fields, context=context)
		if not context.has_key('active_ids'):
			move_id=False
		else:
			move_id=context.get('active_ids',False)
			if move_id:
				move = self.pool.get("stock.move").browse(cr,uid,move_id,context=context)[0] 
		if 'move_id' in fields:
			res.update({
						'move_id': move_id,
						'product_id':move.product_id and move.product_id.id or False,
						'product_qty':move.product_qty or 0.0,
						'source_location':move.location_id and move.location_id.id or False,
						'destination_location':move.location_dest_id and move.location_dest_id.id or False,
						'dest_address_id':move.partner_id and move.partner_id.id or False,
						'internal_type':move.product_id and move.product_id.id and move.product_id.internal_type or 'Finish',
						})
		return res
	
	def split(self,cr,uid,ids,context=None):
		if not context:context={}
		rest_qty=0.0
		rest_uop_qty=0.0
		uom_obj = self.pool.get('product.uom')
		move_pool=self.pool.get('stock.move')
		picking_pool=self.pool.get('stock.picking')
		pick_ids = []
		for split_data in self.browse(cr,uid,ids,context):
			move_id = split_data.move_id.id
			move_line = []
			move_uom = split_data.move_id.product_uom and split_data.move_id.product_uom.id or False
			v_tolerance = 0.0
			max_tolerance_qty = 0.0
			outstanding_qty = 0.0
			if split_data.move_id.picking_id.type=='out':
				so_id = split_data.move_id.sale_line_id and split_data.move_id.sale_line_id.order_id or (split_data.move_id.picking_id and (split_data.move_id.picking_id.sale_id and split_data.move_id.picking_id.sale_id or False))
				if so_id and so_id.payment_method == 'lc':
					if split_data.move_id.lc_product_line_id and split_data.move_id.lc_product_line_id.lc_id and split_data.move_id.sale_line_id and split_data.move_id.lc_product_line_id.sale_line_id:
						v_tolerance = split_data.move_id.lc_product_line_id.lc_id.tolerance_percentage_max
						max_tolerance_qty = split_data.move_id.lc_product_line_id.product_uom_qty + (split_data.move_id.lc_product_line_id.product_uom_qty * v_tolerance/100)
						outstanding_qty = max_tolerance_qty - split_data.move_id.lc_product_line_id.qty_shipped
						outstanding_qty = uom_obj._compute_qty(cr, uid, split_data.move_id.lc_product_line_id.sale_line_id.product_uom.id, outstanding_qty, move_uom)
					elif split_data.move_id.picking_id and split_data.move_id.picking_id.lc_ids:
						for lc in split_data.move_id.picking_id.lc_ids:
							v_tolerance = lc.tolerance_percentage_max
					elif so_id.lc_ids:
						for lc in so_id.lc_ids:
							v_tolerance = lc.tolerance_percentage_max
					else:
						v_tolerance = so_id and so_id.tolerance_percentage_max or 0.0

				# activate this code if you want to use tolerance in tt as valid tolerance
				# elif so_id and so_id.payment_method == 'tt':
				# 	if move.lc_product_line_id and move.lc_product_line_id.lc_id:
				# 		v_tolerance = move.lc_product_line_id.lc_id.tolerance_percentage
				# 		max_tolerance_qty = move.lc_product_line_id.product_qty * v_tolerance
				# 		outstanding_qty = max_tolerance_qty - move.lc_product_line_id.qty_shipped
				# 	elif move.picking_id and move.picking_id.lc_ids:
				# 		for lc in move.picking_id.lc_ids:
				# 			v_tolerance = lc.tolerance_percentage	
				# 	else:
				# 		for lc in so_id.lc_ids:
				# 			v_tolerance = lc.tolerance_percentage
				else:
					v_tolerance = so_id and so_id.tolerance_percentage_max or 0.0

				if not max_tolerance_qty and not outstanding_qty and split_data.move_id.sale_line_id:
					max_tolerance_qty = split_data.move_id.sale_line_id.product_uom_qty + (split_data.move_id.sale_line_id.product_uom_qty*v_tolerance/100)
					outstanding_qty = max_tolerance_qty - split_data.move_id.sale_line_id.product_uom_qty_shipped
					outstanding_qty = uom_obj._compute_qty(cr, uid, split_data.move_id.sale_line_id.product_uom.id, outstanding_qty, move_uom)
					# max_tolerance_qty = move_qty + (move_qty * v_tolerance/100.0)

				max_qty_deliver = outstanding_qty
			else:
				max_qty_deliver = split_data.product_qty
			rest_qty = split_data.product_qty
			rest_uop_qty = split_data.move_id.product_uop_qty
			i=0
			n_line = len(split_data.line_ids)
			if split_data.move_id.picking_id:
				pick_ids.append(split_data.move_id.picking_id.id)
			for split_line in split_data.line_ids:
				i+=1
				qty=split_line.product_uom_qty
				if qty <= 0.0 or qty==0.0:
					continue
				
				rest_qty-=qty
				max_qty_deliver-=qty
				if max_qty_deliver<0:
					# max_tolerance_qty=qty
					break

				default_val={
					'product_qty':qty,
					'product_uos_qty':qty,
					'product_uop_qty':split_line.product_uop_qty or 0.0,
					'product_uop':split_line.product_uop and split_line.product_uop.id or split_line.product_uom.id,
					'product_uom':split_line.product_uom and split_line.product_uom.id or split_data.move_id.product_uom.id,
					'tracking_id':split_line.pack_id and split_line.pack_id.id or split_data.move_id.tracking_id.id or False,
					'prodlot_id':split_line.prodlot_id and split_line.prodlot_id.id or False,
					'location_id':split_data.source_location.id,
					'location_dest_id':split_data.destination_location.id,
					'return_ref_id' :  split_data.move_id and split_data.move_id.return_ref_id and split_data.move_id.return_ref_id.id or False,
					'state' : split_data.move_id and split_data.move_id.state or 'draft',
				}

				if rest_qty > 0:
					# create new copy with spesific information base on default_val
					move_pool.copy(cr, uid, move_id, default_val)

					# update old move with information updated base on update_val
					update_val = {
						'product_qty' : rest_qty,
						'product_uos_qty' : rest_qty,
						'product_uop_qty': split_line.product_uop == split_data.move_id.product_uop and split_data.move_id.product_uop_qty-split_line.product_uop_qty or 0.0,
						# 'state' : split_data.move_id and split_data.move_id.state or 'confirmed',
						'location_id':split_data.source_location.id,
						'location_dest_id':split_data.destination_location.id,
						"return_ref_id" : split_data.move_id and split_data.move_id.return_ref_id and split_data.move_id.return_ref_id.id or False
					}
					move_pool.write(cr, uid, [move_id], update_val)
				elif rest_qty == 0:
					update_val = {
						'product_qty' : qty,
						'product_uos_qty' : qty,
						'product_uop_qty':split_line.product_uop_qty or 0.0,
						'product_uop':split_line.product_uop and split_line.product_uop.id or split_line.product_uom.id,
						'product_uom':split_line.product_uom and split_line.product_uom.id or split_data.move_id.product_uom.id,
						'tracking_id':split_line.pack_id and split_line.pack_id.id or split_data.move_id.tracking_id.id,
						'prodlot_id':split_line.prodlot_id and split_line.prodlot_id.id or False,
						# 'state' : split_data.move_id and split_data.move_id.state or 'confirmed',
						'location_id':split_data.source_location.id,
						'location_dest_id':split_data.destination_location.id,
						"return_ref_id" : split_data.move_id and split_data.move_id.return_ref_id and split_data.move_id.return_ref_id.id or False
					}
					move_pool.write(cr, uid, [move_id], update_val)
				elif (rest_qty < 0 and max_tolerance_qty>0) or (rest_qty < 0 and max_tolerance_qty==0):
					if i<n_line:
						# create new copy with spesific information base on default_val
						move_pool.copy(cr, uid, move_id, default_val)

						# update old move with information updated base on update_val
						update_val = {
							'product_qty' : rest_qty,
							'product_uos_qty' : rest_qty,
							'product_uop_qty': split_line.product_uop == split_data.move_id.product_uop and split_data.move_id.product_uop_qty-split_line.product_uop_qty or 0.0,
							# 'state' : split_data.move_id and split_data.move_id.state or 'confirmed',
							'location_id':split_data.source_location.id,
							'location_dest_id':split_data.destination_location.id,
							"return_ref_id" : split_data.move_id and split_data.move_id.return_ref_id and split_data.move_id.return_ref_id.id or False
						}
						move_pool.write(cr, uid, [move_id], update_val)
					else:
						update_val = {
							'product_qty' : qty,
							'product_uos_qty' : qty,
							'product_uop_qty':split_line.product_uop_qty or 0.0,
							'product_uop':split_line.product_uop and split_line.product_uop.id or split_line.product_uom.id,
							'product_uom':split_line.product_uom and split_line.product_uom.id or split_data.move_id.product_uom.id,
							'tracking_id':split_line.pack_id and split_line.pack_id.id or split_data.move_id.tracking_id.id or False,
							'prodlot_id':split_line.prodlot_id and split_line.prodlot_id.id or False,
							# 'state' : split_data.move_id and split_data.move_id.state or 'confirmed',
							'location_id':split_data.source_location.id,
							'location_dest_id':split_data.destination_location.id,
							"return_ref_id" : split_data.move_id and split_data.move_id.return_ref_id and split_data.move_id.return_ref_id.id or False
						}
						move_pool.write(cr, uid, [move_id], update_val)
		x = picking_pool.write(cr, uid, pick_ids, {'move_lines':[]})
		return True
		
class stock_split_move_line(osv.TransientModel):
	_name="stock.split.move.line"
	_columns = {
		"split_id":fields.many2one("stock.split.move","Split ID"),
		"product_uom_qty":fields.float("Product Qty",digits_compute=dp.get_precision('Product Unit of Measure'),required=True),
		"product_uop_qty":fields.float("Packing Qty",digits_compute=dp.get_precision('Product Unit of Measure'),required=True),
		"product_uom":fields.many2one("product.uom","UoM",required=True),
		"product_uop":fields.many2one("product.uom","UoP",required=True),
		"packaging_id":fields.many2one("product.packaging","Packaging"),
		"pack_id":fields.many2one("stock.tracking","Pack"),
		"prodlot_id":fields.many2one("stock.production.lot","Lot Number"),
			}

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = super(stock_split_move_line, self).default_get(cr, uid, fields, context=context)
		if not context.has_key('move_id'):
			move_id=False
		else:
			move_id=context.get('move_id',False)
			if move_id:
				move = self.pool.get("stock.move").browse(cr,uid,move_id,context=context) 
		if 'product_uom' in fields:
			res.update({
						'product_uom': move.product_uom and move.product_uom.id or False,
						})
			return res

	def onchange_product_qty(self,cr,uid,ids,product_uom_qty,product_uom,move_id,line_ids,context=None):
		if not context:context={}
			
		if product_uom and product_uom_qty and move_id:
			uom_obj = self.pool.get('product.uom')
			total=0.0
			move = self.pool.get('stock.move').browse(cr,uid,move_id,context)
			move_qty = move.product_qty or 0.0
			move_uom = move.product_uom and move.product_uom.id or False
			so_id = move.sale_line_id and move.sale_line_id.order_id or (move.picking_id and (move.picking_id.sale_id and move.picking_id.sale_id or False))
			v_tolerance = 0.0
			max_tolerance_qty = 0.0
			outstanding_qty = 0.0
			if so_id and so_id.payment_method == 'lc':
				if move.lc_product_line_id and move.lc_product_line_id.lc_id and move.sale_line_id and move.lc_product_line_id.sale_line_id:
					v_tolerance = move.lc_product_line_id.lc_id.tolerance_percentage_max
					max_tolerance_qty = move.lc_product_line_id.product_uom_qty + (move.lc_product_line_id.product_uom_qty * v_tolerance/100)
					outstanding_qty = max_tolerance_qty - move.lc_product_line_id.qty_shipped
					outstanding_qty = uom_obj._compute_qty(cr, uid, move.lc_product_line_id.sale_line_id.product_uom.id, outstanding_qty, move_uom)
				elif move.picking_id and move.picking_id.lc_ids:
					for lc in move.picking_id.lc_ids:
						v_tolerance = lc.tolerance_percentage_max	
				elif so_id.lc_ids:
					for lc in so_id.lc_ids:
						v_tolerance = lc.tolerance_percentage_max
				else:
					v_tolerance = so_id and so_id.tolerance_percentage_max or 0.0	
			# activate this code if you want to use tolerance in tt as valid tolerance
			# elif so_id and so_id.payment_method == 'tt':
			# 	if move.lc_product_line_id and move.lc_product_line_id.lc_id:
			# 		v_tolerance = move.lc_product_line_id.lc_id.tolerance_percentage
			# 		max_tolerance_qty = move.lc_product_line_id.product_qty * v_tolerance
			# 		outstanding_qty = max_tolerance_qty - move.lc_product_line_id.qty_shipped
			# 	elif move.picking_id and move.picking_id.lc_ids:
			# 		for lc in move.picking_id.lc_ids:
			# 			v_tolerance = lc.tolerance_percentage	
			# 	else:
			# 		for lc in so_id.lc_ids:
			# 			v_tolerance = lc.tolerance_percentage
			else:
				v_tolerance = so_id and so_id.tolerance_percentage_max or 0.0
			if not max_tolerance_qty and not outstanding_qty and move.sale_line_id:
				max_tolerance_qty = move.sale_line_id.product_uom_qty + (move.sale_line_id.product_uom_qty*v_tolerance/100)
				outstanding_qty = max_tolerance_qty - move.sale_line_id.product_uom_qty_shipped
				outstanding_qty = uom_obj._compute_qty(cr, uid, move.sale_line_id.product_uom.id, outstanding_qty, move_uom)
				# max_tolerance_qty = move_qty + (move_qty * v_tolerance/100.0)
			
			for line in line_ids:
				if line[2]:
					qty = uom_obj._compute_qty(cr, uid, line[2]['product_uom'], line[2]['product_uom_qty'], move_uom)
					total += qty
			total += uom_obj._compute_qty(cr, uid, product_uom, product_uom_qty, move_uom)
			if outstanding_qty < total and move.picking_id.type=='out':
				warning = {
						'title': _('Warning!'),
						'message': _('Total quantity is out of tolerance range, maximum value is %s !'% (outstanding_qty,))
					}
				return {'warning':warning,'value':{'product_uom_qty':0.0,'product_uop_qty':0.0}}

		return {}

	def onchange_product_uop(self,cr,uid,ids,product_uom,product_uop_qty,product_uop,move_id,line_ids,context=None):
		if not context:context={}
		if product_uom and product_uop and product_uop_qty and move_id:
			uom_obj = self.pool.get('product.uom')
			
			line_uop=uom_obj.browse(cr,uid,product_uop)
			line_uom=uom_obj.browse(cr,uid,product_uom)

			if line_uop.category_id!=line_uom.category_id:
				warning = {
						'title': _('Warning!'),
						'message': _('System cannot convert Packing Quantity into UoM Quantity \n because UoM Category of UoP is different with UoM Category of UoM')
					}
				return {'warning':warning,'value':{'product_uom_qty':0.0,'product_uop_qty':0.0}}
			else:
				total=0.0
				line_uom_qty=uom_obj._compute_qty(cr, uid, product_uop, product_uop_qty, product_uom)
				
				res = self.onchange_product_qty(cr,uid,ids,line_uom_qty,product_uom,move_id,line_ids,context=context)
				if not res:
					return {'value':{'product_uom_qty':line_uom_qty}}
				else:
					return res
		return {}