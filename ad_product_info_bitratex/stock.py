from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
from openerp import netsvc
import math

class stock_picking(osv.Model):
	_inherit = "stock.picking"

	def action_revert_done(self, cr, uid, ids, context=None):
		if not len(ids):
			return False
		account_move_obj = self.pool.get('account.move')
		move_obj = self.pool.get('stock.move')
		for picking in self.browse(cr, uid, ids, context):
			if not picking.is_allow_cancel:
				raise osv.except_osv(_('Error Re-Open'),
					_('You are not allow to Re-Open this Picking'))
			for line in picking.move_lines:
				if self.has_valuation_moves(cr, uid, line):
					# raise osv.except_osv(_('Error'),
					#    _('Line %s has valuation moves (%s). Remove them first')
					#    % (line.name, line.picking_id.name))
					move_all_ids = account_move_obj.search(cr, uid, [('ref','=',picking.name),('journal_id','=',9)])
					account_move_obj.button_cancel(cr,uid,move_all_ids)
					account_move_obj.unlink(cr,uid,move_all_ids)
					
				if line.state!='cancel':
					move_obj.action_cancel(cr, uid, [line.id])
				line.write({'state': 'draft'})
			self.write(cr, uid, [picking.id], {'state': 'draft'})
			if picking.invoice_state == 'invoiced' and not picking.invoice_id:
				self.write(cr, uid, [picking.id], {'invoice_state': '2binvoiced'})
			wf_service = netsvc.LocalService("workflow")
			# Deleting the existing instance of workflow
			wf_service.trg_delete(uid, 'stock.picking', picking.id, cr)
			wf_service.trg_create(uid, 'stock.picking', picking.id, cr)
		for (id,name) in self.name_get(cr, uid, ids):
			message = _("The stock picking '%s' has been set in draft state.") %(name,)
			self.log(cr, uid, id, message)
		for picking in self.browse(cr, uid, ids, context=context):
			self.write(cr, uid, picking.id, {'is_allow_cancel':False})
		return True

	def compute_rm_quantity(self, cr, uid, ids, context=None):
		if context is None:
			context={}
		move_obj = self.pool.get('stock.move')
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.type!='internal':
				for move in picking.move_line:
					if move.product_id and move.product_id.internal_type!='Raw Material':
						continue
					product_qty = move_obj.get_rm_quantity_avg(cr, uid, ids, move.product_id.id, move.product_uop_qty, move.location_id.id, tracking_id=move.tracking_id and move.tracking_id.id or None, context={'date':picking.date_done!='False' and picking.date_done or move.date})
					move_obj.write(cr, uid, move.id, {'product_qty':product_qty})
		return True


class stock_move(osv.Model):
	_inherit = "stock.move"
	_columns = {
		'product_uop_qty': fields.float('Quantity (UOP)', digits_compute=dp.get_precision('Product Unit of Picking'),required=True, states={'done': [('readonly', True)]}),
		'product_uop': fields.many2one('product.uom', 'Product UOP',required=True, states={'done': [('readonly', True)]}),
		'bom_id'        : fields.many2one('mrp.bom',"Bill of Material"),
		'internal_type' : fields.related('product_id','internal_type',type='selection',selection=[('Finish','Finish Goods'),
			('Finish_others','Finish Goods(Others)'),
			('Raw Material','Raw Material'),
			('Stores','Stores'),
			('Waste','Waste'),
			('Scrap','Scrap'),
			('Packing','Packing Material'),
			('Fixed','Fixed Asset')],
			string='Goods Type',store=True),
		'move_component_lines' : fields.one2many('stock.move.composition','move_id','Component Raw Material'),
	}

	_order = "product_id asc"
	
	def _get_uom_id(self, cr, uid, *args):
		cr.execute('select id from product_uom order by id limit 1')
		res = cr.fetchone()
		return res and res[0] or False

	_defaults = {
		'product_uop_qty': lambda *a: 0.0,
		"product_uop":_get_uom_id,
	}

	def get_rm_quantity_avg(self, cr, uid, ids, product_id, product_uop_qty, location_id, tracking_id=None, context=None):
		# this method is use to compute the average quantity of product that has fifo costing method
		if context is None:
			context = {'date':time.strftime("%Y-%m-%d %H:%M:%S")}
		qty = 0.0
		if not product_id or not product_uop_qty or not location_id:
			return qty
		# if ids:
			# move_out = self.browse(cr, uid, ids)[0]
		product_obj = self.pool.get('product.product')
		uom_obj = self.pool.get('product.uom')

		product = product_obj.browse(cr, uid, product_id)
		company_id = product.company_id.id
		fifo = product.cost_method == 'fifo'
		if fifo:
			order = 'date, id'
		else: 
			order = 'date desc, id desc'
		if fifo:
			domain = [('company_id', '=', company_id), 
					('qty_remaining', '>', 0.0), 
					('state', '=', 'done'), 
					('location_id', '!=', location_id),
					('location_dest_id.usage', '=', 'internal'), 
					('location_dest_id', '=', location_id),
					('product_id', '=', product.id)]
			if tracking_id is not None:
				domain.append(('tracking_id','=',tracking_id))
			move_in_ids = self.search(cr, uid, domain, order = order, context=context)
			for move in self.browse(cr, uid, move_in_ids):
				# print "::::::::::::::: move in ", move.id, move.qty_remaining
				if not product_uop_qty:
					continue
				uom_move = move.product_uom.id
				qty_move = move.product_qty
				product_qty = uom_obj._compute_qty(cr, uid, uom_move, qty_move, product.uom_id.id, round=False)
				avg_weight = move.product_uop_qty and product_qty/move.product_uop_qty or 0.0
				# qty_remaining = move.qty_remaining
				product_qty_remaining = uom_obj._compute_qty(cr, uid, uom_move, move.qty_remaining, product.uom_id.id, round=False)
				uop_remaining = avg_weight and product_qty_remaining/avg_weight or 0.0
				# if move_out and move_out.date<='2016-04-30 23:59:59':
					# system using average total of all available stock_move. and soon in may 2016, we change the rule
					# print "::::::::::::::int()"
					# uop_remaining = int(uop_remaining)
				# else:
					# print "::::::::::::::round()"
				uop_remaining = round(uop_remaining)

				# print "::::::::::::::: uop_remaining ", move.id, avg_weight, product_qty_remaining, uop_remaining
				# if uop_remaining == 1:
				#   diff = product_qty_remaining-avg_weight
				#   uop_remaining += (diff and abs(avg_weight%diff)<1.0 and 1 or 0)
				# print "::::::::::::", product_uop_qty, move.id, product_qty, move.product_uop_qty, avg_weight, product_qty_remaining, uop_remaining
				if uop_remaining <= 0:
					# print "case 0"
					qty += product_qty_remaining
				else:
					if uop_remaining >= product_uop_qty:
						if uop_remaining == product_uop_qty:
							# print "case 1"
							qty += round(product_qty_remaining,4)
						else:
							# print "case 2"
							qty += round(product_uop_qty*avg_weight,4)

						product_uop_qty = 0.0
						break
					else:
						# print "case 3"
						qty += round(product_qty_remaining,4)
						product_uop_qty-=uop_remaining
			# print "LLLLLLLLLLLLLLLLLL, QTY", qty
		return qty

	def onchange_uop_quantity(self, cr, uid, ids, product_id=None, product_uop_qty=None, product_uom=None, \
								product_uos=None, product_uop=None, location_id=None, date=None, tracking_id=None, prodlot_id=None, context=None):
		if context is None:
			context = {}

		result = {
			'product_uos_qty': 0.00,
			'product_qty': 0.00,
			}
		warning = {}
		if not product_uom or not product_uop:
			return {'value':{}}

		if (not product_id) or (product_uop_qty <=0.0):
			result['product_uop_qty'] = 0.0
			return {'value': result}

		product_obj = self.pool.get('product.product')
		uom_obj = self.pool.get('product.uom')
		product = product_obj.browse(cr, uid, product_id)
		# this variable is only use to check the stock_move type, and
		if ids:
			sm_temporary = self.read(cr, uid, ids, ['type','picking_id'])
			for move in sm_temporary:
				if not move['picking_id']:
					return {'value':{}}
				if move['type'] and move['type']!='internal':
					return {'value':{}}
		if product.internal_type == 'Raw Material':
			uom_qty = self.get_rm_quantity_avg(cr, uid, ids, product.id, product_uop_qty, location_id, tracking_id=tracking_id or  None, context={'date':date})
			uos_qty = uom_qty
		else:
			uom_cat = uom_obj.read(cr, uid, product_uom, ['category_id'])
			uop_cat = uom_obj.read(cr, uid, product_uop, ['category_id'])
			if uom_cat['category_id'][0]!=uop_cat['category_id'][0]:
				return {'value':{}}

			uom_qty = uom_obj._compute_qty(cr, uid, product_uop, product_uop_qty, product_uom)
			uos_qty = uom_qty
		
		result['product_qty'] = uom_qty
		result['product_uos_qty'] = uos_qty

		return {'value':result,'context':context.update({'uop_changed':True})}

	def onchange_quantity(self, cr, uid, ids, product_id=None, product_qty=None, product_uom=None, product_uos=None,product_uop=None, context=None):
		if context is None:
			context = {}
		
		if not context.get('uop_changed',True):         
			result = {
				'product_uos_qty': 0.00,
				'product_uop_qty': 0.00,
				}
		else:
			result = {
				'product_uos_qty': 0.00,
				}

		warning = {}

		if (not product_id) or (product_qty <=0.0):
			result['product_qty'] = 0.0
			return {'value': result}

		product_obj = self.pool.get('product.product')
		uos_coeff = product_obj.read(cr, uid, product_id, ['uos_coeff','uop_coeff'])
		
		# Warn if the quantity was decreased 
		if ids:
			for move in self.read(cr, uid, ids, ['product_qty']):
				if product_qty < move['product_qty']:
					warning.update({
					'title': _('Information'),
					'message': _("By changing this quantity here, you accept the "
								"new quantity as complete: OpenERP will not "
								"automatically generate a back order.") })
				break

		if product_uos and product_uom and (product_uom != product_uos):
			result['product_uos_qty'] = product_qty * uos_coeff['uos_coeff']
		else:
			result['product_uos_qty'] = product_qty

		if context.get('uop_changed',False):
			if product_uop and product_uom and (product_uom != product_uop):
				result['product_uop_qty'] = product_qty * uos_coeff['uop_coeff']
			else:
				result['product_uop_qty'] = product_qty

		return {'value':result,'warning':warning,'context':context}

	def onchange_uos_quantity(self, cr, uid, ids, product_id=None, product_uos_qty=None,
						  product_uos=None, product_uom=None,product_uop=None, context=None):
		""" On change of product quantity finds UoM and UoS quantities
		@param product_id: Product id
		@param product_uos_qty: Changed UoS Quantity of product
		@param product_uom: Unit of measure of product
		@param product_uos: Unit of sale of product
		@return: Dictionary of values
		"""
		result = {
				  'product_qty': 0.00,
				  # 'product_uop_qty':0.00
		  }
		warning = {}

		if (not product_id) or (product_uos_qty <=0.0):
			result['product_uos_qty'] = 0.0
			return {'value': result}

		product_obj = self.pool.get('product.product')
		uos_coeff = product_obj.read(cr, uid, product_id, ['uos_coeff','uop_coeff'])
		
		# Warn if the quantity was decreased 
		for move in self.read(cr, uid, ids, ['product_uos_qty']):
			if product_uos_qty < move['product_uos_qty']:
				warning.update({
				   'title': _('Warning: No Back Order'),
				   'message': _("By changing the quantity here, you accept the "
								"new quantity as complete: OpenERP will not "
								"automatically generate a Back Order.") })
				break

		if product_uos and product_uom and (product_uom != product_uos):
			result['product_qty'] = product_uos_qty / uos_coeff['uos_coeff']
		else:
			result['product_qty'] = product_uos_qty
		# if product_uop and product_uom and (product_uom != product_uop):
		#   result['product_uop_qty'] = (product_uos_qty / uos_coeff['uos_coeff'])* uos_coeff['uop_coeff']
		# else:
		#   result['product_uop_qty'] = (product_uos_qty / uos_coeff['uos_coeff'])

		return {'value': result, 'warning': warning}

	def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
							loc_dest_id=False, partner_id=False, context=None):
		""" On change of product id, if finds UoM, UoS, quantity and UoS quantity.
		@param prod_id: Changed Product id
		@param loc_id: Source location id
		@param loc_dest_id: Destination location id
		@param partner_id: Address id of partner
		@return: Dictionary of values
		"""
		# res = super(stock_move,self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id,
		#                   loc_dest_id=loc_dest_id, partner_id=partner_id)
		if not prod_id:
			return {}
		user = self.pool.get('res.users').browse(cr, uid, uid)
		lang = user and user.lang or False
		if partner_id:
			addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id)
			if addr_rec:
				lang = addr_rec and addr_rec.lang or False
		ctx = {'lang': lang}

		product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
		uos_id  = product.uos_id and product.uos_id.id or False
		uop_id  = product.uop_id and product.uop_id.id or False
		result = {
			'product_uom': product.uom_id.id,
			'product_uos': uos_id,
			'product_uop': uop_id,
			'product_qty': 1.00,
			'product_uos_qty' : self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id, uop_id)['value']['product_uos_qty'],
			'product_uop_qty': self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id, uop_id,context={'uop_changed':False})['value']['product_uop_qty'],
			'prodlot_id' : False,
			'internal_type':product.internal_type,
		}
		if not ids:
			result['name'] = product.partner_ref
		if loc_id:
			result['location_id'] = loc_id
		if loc_dest_id:
			result['location_dest_id'] = loc_dest_id
		
		return {'value':result}

	def _create_composition_moves(self, cr, uid, move, context=None):
		"""
		Generate the raw material moves if the product being moved is subject
		to FIFO costing method, and the internal_type is raw material or finish good.
		If the internal_type is finish good, then we need to calculate the composition first
		
		Depending on the matches it will create the necessary moves
		"""
		ctx = context.copy()
		ctx['force_company'] = move.company_id.id
		product = self.pool.get("product.product").browse(cr, uid, move.product_id.id, context=ctx)
		move_composition_obj = self.pool.get('stock.move.composition')
		# print ":::::::::::::::", move_composition_obj
		if (move.location_id.usage=='internal' and move.location_dest_id.usage=='production') or (move.location_id.usage=='production' and move.location_dest_id.usage=='internal'):
			if product.internal_type == 'Finish':
				if not product.blend_code:
					raise osv.except_osv(_('Error'), _("Please correct your product configuration."+str(product.internal_type or product.name)+" doenst have Blend Code."))
				for blend_line in product.blend_code.blend_lines:
					if not blend_line.rm_type_id:
						raise osv.except_osv(_('Error'), _("Please correct your product configuration."+str(product.internal_type or product.name)+" doenst have RM Category of its Blend Compositions."))
					product_qty = (blend_line.percentage/100.0) * move.product_qty
					move_composition_obj.create(cr, uid,
							{
							 'move_id': move.id,
							 'date': move.picking_id and move.picking_id.date_done!=False and move.picking_id.date_done or move.date,
							 'rm_category_id': blend_line.rm_type_id.category_id.id or False,
							 'product_uom': move.product_uom.id,
							 'product_qty' : product_qty or 0.0,
							 'location_id' : move.location_id.id,
							 'location_dest_id' : move.location_dest_id.id,
							 'state' : 'done',
						})
			elif product.internal_type == 'Raw Material':
				if not product.rm_class_id:
					raise osv.except_osv(_('Error'), _("Please correct your product configuration."+str(product.internal_type or product.name)+" doenst have Raw Material Type."))
				
				move_composition_obj.create(cr, uid,
						{
						 'move_id': move.id,
						 'date': move.picking_id and move.picking_id.date_done!=False and move.picking_id.date_done or move.date,
						 'rm_category_id': product.rm_class_id and product.rm_class_id.id or False,
						 'product_uom': move.product_uom.id,
						 'product_qty' : move.product_qty or 0.0,
						 'location_id' : move.location_id.id,
						 'location_dest_id' : move.location_dest_id.id,
						 'state' : 'done',
					})

	def action_done(self, cr, uid, ids, context=None):
		""" Makes the move done and if all moves are done, it will finish the picking.
		@return:
		"""
		picking_ids = []
		move_ids = []
		wf_service = netsvc.LocalService("workflow")
		if context is None:
			context = {}
		todo = []
		for move in self.browse(cr, uid, ids, context=context):
			if move.state=="draft":
				todo.append(move.id)
		if todo:
			self.action_confirm(cr, uid, todo, context=context)
			todo = []

		#Do price calculation on moves
		matchresults = self.price_calculation(cr, uid, ids, context=context)

		for move in self.browse(cr, uid, ids, context=context):
			if move.state in ['done','cancel']:
				continue
			move_ids.append(move.id)

			if move.picking_id:
				picking_ids.append(move.picking_id.id)
			if move.move_dest_id.id and (move.state != 'done'):
				# Downstream move should only be triggered if this move is the last pending upstream move
				other_upstream_move_ids = self.search(cr, uid, [('id','!=',move.id),('state','not in',['done','cancel']),
											('move_dest_id','=',move.move_dest_id.id)], context=context)
				if not other_upstream_move_ids:
					self.write(cr, uid, [move.id], {'move_history_ids': [(4, move.move_dest_id.id)]})
					if move.move_dest_id.state in ('waiting', 'confirmed'):
						self.force_assign(cr, uid, [move.move_dest_id.id], context=context)
						if move.move_dest_id.picking_id:
							wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
						if move.move_dest_id.auto_validate:
							self.action_done(cr, uid, [move.move_dest_id.id], context=context)

			self._create_product_valuation_moves(cr, uid, move, move.id in matchresults and matchresults[move.id] or [], context=context)
			if move.state not in ('confirmed','done','assigned'):
				todo.append(move.id)

			# this modification only for spesific company
			self._create_composition_moves(cr, uid, move, context=context)

		if todo:
			self.action_confirm(cr, uid, todo, context=context)

		self.write(cr, uid, move_ids, {'state': 'done', 'date': move.date or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
		for id in move_ids:
			 wf_service.trg_trigger(uid, 'stock.move', id, cr)

		for pick_id in picking_ids:
			wf_service.trg_write(uid, 'stock.picking', pick_id, cr)

		return True

	# this is created to delete stock_move_matching of module product_fifo_lifo when the stock_move is being canceled
	def action_cancel(self, cr, uid, ids, context=None):
		if not len(ids):
			return True
		if context is None:
			context = {}

		matching_obj = self.pool.get('stock.move.matching')
		for move in self.browse(cr, uid, ids, context=context):
			# only check when the stock_move is for sending goods, because product_fifo_lifo only create
			# stock_move_mathing when sending goods
			if move.matching_ids_out and move.location_id.usage == 'internal' and (move.location_dest_id.usage != 'internal' or move.location_dest_id.usage == 'internal'):
				to_update = []
				for match in move.matching_ids_out:
					to_update.append(match.id)
					matching_obj.write(cr, uid, match.id, {'qty':-1*match.qty}, context=context)
				# if to_update:

				matching_obj.unlink(cr, uid, to_update)
			# print "::::::::::;;;", move.move_component_lines
			if move.move_component_lines:
				to_delete = []
				for comp in move.move_component_lines:
					to_delete.append(comp.id)
				self.pool.get('stock.move.composition').unlink(cr, uid, to_delete)
		res = super(stock_move, self).action_cancel(cr, uid, ids, context=context)
		return res


class stock_tracking(osv.Model):
	_inherit="stock.tracking"
	_columns = {
		'internal_type' : fields.selection([('Finish','Finish Goods'),
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