from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class stock_tracking(osv.osv):
	_inherit = "stock.tracking"
	_columns = {
		'alias' : fields.char('Alias', size=64),
	}
	_sql_constraints = [
		('name_uniq', 'unique(name)', 'Name of Lot/Pack Number must be unique! You can not create new Lot/Pack number with the same name.'),
	] 

class stock_location(osv.osv):
	_inherit = "stock.location"

	_columns = {
		'alias' : fields.char('Alias/Location Code', size=10),
		'sequence' : fields.char('Sequence',size=13),
	}

	def _complete_name(self, cr, uid, ids, name, args, context=None):
		""" Forms complete name of location from parent location to child location.
		@return: Dictionary of values
		"""
		res = {}
		for m in self.browse(cr, uid, ids, context=context):
			names = [m.name]
			if m.alias:
				names = [("[%s] %s"%(m.alias, m.name))] 
			res[m.id] = names[0]
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('alias', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

class stock_picking(osv.osv):
	_inherit = "stock.picking"
	_columns = {
		'show_partner_address' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text' : fields.text('Consignee Address Details'),
		# 'partner_name' : fields.char('Customer Name', size=128),
		# 'street': fields.char('Street', size=128),
		# 'street2': fields.char('Street2', size=128),
		# 'street3': fields.char('Street3', size=128),
		# 'zip': fields.char('Zip', change_default=True, size=24),
		# 'city': fields.char('City', size=128),
		# 'state_id': fields.many2one("res.country.state", 'State'),
		# 'country_id': fields.many2one('res.country', 'Country'),

		'container_book_id' : fields.many2one('container.booking', 'Shipping Instruction', readonly=False),
		'forwading' : fields.many2one('stock.transporter','Forwading', required=False),
		"forwading_charge":fields.many2one("stock.transporter.charge","Forwading Charge"),
		"shipping_lines":fields.many2one("stock.transporter","Transporter Container"),
		"trucking_company":fields.many2one("stock.transporter","Transporter Trucking"),
		"trucking_charge":fields.many2one("stock.transporter.charge","Trucking Charge"),
		"porters":fields.many2one("stock.porters","Porters"),
		"porters_charge":fields.many2one("stock.porters.charge","Porters Charge"),
		'seal_number' : fields.char('Seal No.', size=50, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
		'fumigation_remarks' : fields.char('Fumigation', size=50),
		'notify' : fields.related('sale_id','notify',type='many2one',relation='res.partner',string='Notify Party', store=True),
		
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text' : fields.text('Consignee Address Details'),
		# 'n_name' : fields.char('Notify', size=128),
		# 'n_street': fields.char('Street', size=128),
		# 'n_street2': fields.char('Street2', size=128),
		# 'n_street3': fields.char('Street3', size=128),
		# 'n_zip': fields.char('Zip', change_default=True, size=24),
		# 'n_city': fields.char('City', size=128),
		# 'n_state_id': fields.many2one("res.country.state", 'State'),
		# 'n_country_id': fields.many2one('res.country', 'Country'),

		'container_number' : fields.char('Container No.', size=50),
		'tare_weight' : fields.float('Container Tare Weight', digits_compute=dp.get_precision("Product Unit of Measure")),
		'gross_weight' : fields.float('Gross Weight', digits_compute=dp.get_precision("Product Unit of Measure")),
		'destination_country' : fields.char('Destination Country', size=50),
		'truck_number' : fields.char('Truck No.', size=50),
		'driver_id' : fields.many2one('driver','Driver'),
		'truck_type' : fields.many2one('stock.transporter.truck','Truck Type'),
		'container_size' : fields.many2one('container.size','Container Size'),
		'teus' : fields.char('TEUS.', help="Container Type Code Bitratex",size=50),
		'seal_number' : fields.char('Seal No.', size=50),
		'estimation_deliv_date' : fields.datetime('Estimated Delivery Date',states={'done':[('readonly', False)], 'cancel':[('readonly',False)]}),
		'estimation_arriv_date' : fields.datetime('Estimated Arrival Date',states={'done':[('readonly', False)], 'cancel':[('readonly',False)]}),
		'surat_jalan_number' : fields.char('Surat Jalan No.',size=128),
		'stuffing_ids' : fields.many2many('stuffing.memo','stock_picking_stuffing_rel','stuffing_id','picking_id','Related Stuffing Memo(s)',readonly=False),
		'state': fields.selection([
			('draft', 'Draft'),
			('cancel', 'Cancelled'),
			('auto', 'Waiting Another Operation'),
			('booking_created', 'Ready to book'),
			('booked', 'Booked'),
			('confirmed', 'Waiting Availability'),
			('instructed', 'Instructed'),
			('assigned', 'Ready to Transfer'),
			('done', 'Transferred'),
			], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
			* Draft: not confirmed yet and will not be scheduled until confirmed\n
			* Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
			* Waiting Availability: still waiting for the availability of products\n
			* Booked: container booking has been created and confirmed\n
			* Instructed: Shipping Instruction has been Created\n
			* Ready to Transfer: products reserved, simply waiting for confirmation.\n
			* Transferred: has been processed, can't be modified or cancelled anymore\n
			* Cancelled: has been cancelled, can't be confirmed anymore"""
		),
		'default_location_id':fields.many2one('stock.location','Set Default Source Location'),
		'default_dest_location_id':fields.many2one('stock.location','Set Default Destination Location'),

		'draft_invoice_number' : fields.char('Draft Invoice Number', readonly=True),
		'draft_invoice_id' : fields.many2one('stock.proforma.invoice','Draft Invoice Number', readonly=True),
		'internal_shipment_type' : fields.selection([
			('rm_issue','Raw Material Issue'),
			('rm_return','Raw Material Return'),
			('ss_issue','Stores Issue'),
			('ss_transfer','Stores Transfer'),
			('ss_return','Stores Department Return'),
			('pm_issue','Packing Material Issue'),
			('pm_transfer','Packing Material Transfer'),
			('pm_return','Packing Material Department Return'),
			('fg_receipt','Receive Finish Good'),
			('fg_return','Return Finish Good'),
			('fg_move','Internal Move Finish Good'),
			('fgo_issue','Finish Good Other Issue'),
			('fgo_receipt','Finish Good Other Receipt'),
			('wm_issue','Waste Material Issue'),
			('wm_receipt','Waste Material Receipt'),
			],string='Move Type'),
		'sale_type': fields.selection([('export','Export'),('local','Local')],"Sale Type",required=False),
		'date_done_2' : fields.date('Date of Transfer', help="Date of Completion", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
	}

	def onchange_trucking_company(self, cr, uid, uds, trucking_company, context=None):
		res = {'truck_type':False}
		if trucking_company:
			truck_ids = self.pool.get('stock.transporter.truck').search(cr, uid, [('transporter_id','=',trucking_company)])
			if truck_ids:
				res['truck_type'] = truck_ids[0]
		return {'value':res}

	def onchange_forwading_charge(self, cr, uid, uds, forwading_charge, context=None):
		res = {'destination_country':False}
		if forwading_charge:
			charge_id = self.pool.get('stock.transporter.charge').search(cr, uid, [('id','=',forwading_charge)])
			if charge_id:
				charge = self.pool.get('stock.transporter.charge').browse(cr, uid, charge_id)
				res['destination_country'] = charge.port_id and charge.port_id.name+', '+charge.country_id.name or charge.country_id.name
		return {'value':res}

	def onchange_date_done_2(self, cr, uid, uds, date_done_2, context=None):
		res = {'date_done':False}
		if date_done_2:
			res['date_done'] = datetime.strptime(date_done_2,"%Y-%m-%d").strftime("%Y-%m-%d 12:00:00")
		return {'value':res}
	
	def onchange_def_location_id(self,cr,uid,ids,location_id,context=None):
		if location_id:
			return {'context':{'location_id':location_id}}
		return {'context':{'location_id':False},'value':{'location_id':False}}

	def onchange_def_location_dest_id(self,cr,uid,ids,location_dest_id,context=None):
		if location_dest_id:
			return {'context':{'location_dest_id':location_dest_id}}
		return {'context':{'location_dest_id':False},'value':{'location_dest_id':location_dest_id}}



	_defaults = {
		'internal_shipment_type' : lambda self, cr, uid, context : context.get('internal_shipment_type',False),
		
	}

	# def force_assign(self, cr, uid, ids, *args):
	# 	""" Changes state of picking to available if moves are confirmed or waiting.
	# 	@return: True
	# 	"""
	# 	wf_service = netsvc.LocalService("workflow")
	# 	for pick in self.browse(cr, uid, ids):
	# 		move_ids = [x.id for x in pick.move_lines if x.state in ['confirmed','waiting']]
	# 		self.pool.get('stock.move').force_assign(cr, uid, move_ids)
	# 		wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
	# 	return True

	


	# This is modified to check if the DOs sale_type is Export and to check wether the Shipping Instruction is already created or not
	# def draft_force_assign(self, cr, uid, ids, *args):
	# 	""" Confirms picking directly from draft state.
	# 	@return: True
	# 	"""
	# 	print ">>>>>>>>>>>>>>>>> disini kok"
	# 	wf_service = netsvc.LocalService("workflow")
	# 	for pick in self.browse(cr, uid, ids):
	# 		if not pick.move_lines:
	# 			raise osv.except_osv(_('Error!'),_('You cannot process picking without stock moves.'))
	# 		print ">>>>masuk", pick.state, pick.container_book_id, pick.sale_type, pick.chained_picking_type 
	# 		if pick.sale_type == 'export' and pick.type=='out':
	# 			print ">>>>masuk sini"
	# 			if pick.container_book_id:
	# 				wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booked', cr)
	# 				if pick.container_book_id.state == 'booked':
	# 					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booking_confirmed', cr)
	# 				elif pick.container_book_id.state == 'instructed':
	# 					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'instructed', cr)
	# 		else:
	# 			wf_service.trg_validate(uid, 'stock.picking', pick.id,
	# 				'button_confirm', cr)
	# 	return True

	def set_default_location(self, cr, uid, ids, context=None):
		if context is None:
			context={}
		for picking in self.browse(cr, uid, ids, context=context):
			update_vals = {}
			if picking.default_location_id:
				update_vals.update({'location_id':picking.default_location_id.id})
			if picking.default_dest_location_id:
				update_vals.update({'location_id':picking.default_dest_location_id.id})

			if update_vals:
				move_line_ids = [line.id for line in picking.move_lines]
				self.pool.get('stock.move').write(cr, uid, move_line_ids, update_vals, context=context)
		return True

	def compute_product_uom_qty_rm(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('stock.move')
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.state in ('done','cancel'):
				continue
			for move in picking.move_lines:
				if move.product_id and move.product_id.internal_type!='Raw Material':
					continue
				else:
					uom_qty = move_pool.get_rm_quantity_avg(cr, uid, ids, move.product_id.id, move.product_uop_qty, move.location_id.id, tracking_id=move.tracking_id and move.tracking_id.id or None, context={'date':picking.date_done!='False' and picking.date_done or move.date})
					move_pool.write(cr, uid, move.id, {'product_qty':uom_qty})
		return True

	def create(self, cr, user, vals, context=None):
		if context is None:
			context = {}
		user_data = self.pool.get('res.users').browse(cr,user,user)
		company_id = user_data.company_id or False 
		if ('name' not in vals) or (vals.get('name')=='/'):
			seq_obj_name =  self._inherit
			company_code = ''
			company_pooler = self.pool.get('res.company')
			type_ship = vals.get('type',False)
			if type_ship=='internal':
				seq_obj_name += '.internal'
				if vals.get('goods_type',False) and (vals.get('internal_shipment_type',False) or context.get('internal_shipment_type',False)):
					internal_shipment_type = (vals.get('internal_shipment_type',False) or context.get('internal_shipment_type',False))
					if internal_shipment_type in ('rm_return','fg_receipt','fgo_receipt','wm_receipt'):
						seq_obj_name += '.r'
						goods_type = vals.get('goods_type',False)
						if goods_type == 'finish_others':
							goods_type = "finisho"
						elif goods_type not in ('finish','raw','asset','stores','packing','service'):
							goods_type = 'others'
						seq_obj_name += '.'+goods_type
					elif internal_shipment_type in ('rm_issue','fg_return','fgo_issue','wm_issue'):
						seq_obj_name += '.i'
						goods_type = vals.get('goods_type',False)
						if goods_type == 'finish_others':
							goods_type = "finisho"
						elif goods_type not in ('finish','raw','asset','stores','packing','service'):
							goods_type = 'others'
						seq_obj_name += '.'+goods_type
			if vals.get('company_id',False):
				company_id = company_pooler.browse(cr, user, vals.get('company_id',False))
			if company_id:
				company_code=company_id.prefix_sequence_code
			cd = {}
			if vals.get('date',False):
				cd = {'date':vals['date']}
			vals['name'] = company_code + self.pool.get('ir.sequence').get(cr, user, seq_obj_name, context=cd)
		res = super(stock_picking, self).create(cr, user, vals, context)
		return res

	def copy(self, cr, uid, id, default=None, context=None):
		if default is None:
			default = {}
		default = default.copy()
		picking_obj = self.browse(cr, uid, id, context=context)
		company_id = False
		if ('name' not in default) or (picking_obj.name == '/'):
			default['container_book_id'] = False
			seq_obj_name =  self._inherit
			company_code = ''
			company_pooler = self.pool.get('res.company')
			
			type_ship = picking_obj.type
			if type_ship=='internal':
				seq_obj_name += '.internal'
				if picking_obj.goods_type and picking_obj.internal_shipment_type:
					internal_shipment_type = picking_obj.internal_shipment_type
					if internal_shipment_type in ('rm_return','fg_receipt','fgo_receipt','wm_receipt'):
						seq_obj_name += '.r'
						goods_type = picking_obj.goods_type
						if goods_type == 'finish_others':
							goods_type = "finisho"
						elif goods_type not in ('finish','raw','asset','stores','packing','service'):
							goods_type = 'others'
						seq_obj_name += '.'+goods_type
					elif internal_shipment_type in ('rm_issue','fg_return','fgo_issue','wm_issue'):
						seq_obj_name += '.i'
						goods_type = picking_obj.goods_type
						if goods_type == 'finish_others':
							goods_type = "finisho"
						elif goods_type not in ('finish','raw','asset','stores','packing','service'):
							goods_type = 'others'
						seq_obj_name += '.'+goods_type
			if picking_obj.company_id:
				company_code=picking_obj.company_id.prefix_sequence_code
			else:
				company_code = company_pooler.browse(cr, uid, self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,context=context).prefix_sequence_code
			cd = {}
			if default.get('date',False):
				cd = {'date':default['date']}
			elif picking_obj.date:
				cd = {'date':picking_obj.date}
			default['name'] = company_code + self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
		if ('date_done' not in default) or ('date_done_2' not in default):
			default['date_done'] = False
			default['date_done_2'] = False
		res = super(stock_picking, self).copy(cr, uid, id, default, context)
		return res

	def compute_prod_lot_ids(self,cr,uid,ids,context=None):
		if not context:context={}
		move_obj = self.pool.get("stock.move")
		uom_obj = self.pool.get("product.uom")
		for picking in self.browse(cr,uid,ids,context=context):
			mvl_lines = [mvl.id for mvl in picking.move_lines]
			for move in picking.move_lines:
				if move.prodlot_id and move.prodlot_id.id:
					continue

				move_qty = move.product_qty
				quantity_rest = move.product_qty
				uos_qty_rest = move.product_uos_qty
				new_move = []
				# if data.use_exist:
				# 	lines = [l for l in data.line_exist_ids if l]
				# else:
				# 	lines = [l for l in data.line_ids if l]
				context_lot = context.copy()
				context_lot.update({'location_id':move.location_id.id,})
				#prodlot_ids = self.pool.get('stock.production.lot').search(cr,uid,[('product_id','=',move.product_id.id),()],order="date asc",context=context_lot)
				incoming_moves = self.pool.get('stock.move').search(cr,uid,[('location_dest_id','=',move.location_id.id),\
								('product_uom','=',move.product_uom.id),('product_id','=',move.product_id.id)])
				lots = {}
				for im in self.pool.get('stock.move').browse(cr,uid,incoming_moves):
					if im.prodlot_id and im.prodlot_id.id and im.prodlot_id.id not in lots:
						lots[im.prodlot_id.id]=im.product_qty
					elif im.prodlot_id and im.prodlot_id.id and im.prodlot_id.id in lots:
						lots[im.prodlot_id.id]=lots[im.prodlot_id.id]+im.product_qty

				outgoing_moves = self.pool.get('stock.move').search(cr,uid,[('location_id','=',move.location_id.id),\
								('product_uom','=',move.product_uom.id),('product_id','=',move.product_id.id)])
				# print "==========outgoing==========",outgoing_moves
				for om in self.pool.get('stock.move').browse(cr,uid,outgoing_moves):
					if om.prodlot_id and om.prodlot_id.id and om.prodlot_id.id not in lots:
						lots[om.prodlot_id.id]=om.product_qty
					elif om.prodlot_id and om.prodlot_id.id and om.prodlot_id.id in lots:
						lots[om.prodlot_id.id]=lots[om.prodlot_id.id]-om.product_qty
					# print "=================>",om.product_qty
				lot_ids = self.pool.get('stock.production.lot').search(cr,uid,[('id','in',lots.keys())],order="date asc")
				for x in lot_ids:
					if lots[x]>=move.product_qty:
						move_obj.write(cr, uid, [move.id], {'prodlot_id': x,})
						move_qty = 0.0
						uos_qty_rest = 0.0
					else:
						total_move_qty = 0.0
						uos_x = (move.product_uos) or (move.product_id.uos_id) or move.product_uom
						lots_uos_qty = uom_obj._compute_qty_obj(cr, uid, move.product_uom, lots[x], uos_x, context=context)
						default_val = {
								'product_qty': move_qty-lots[x],
								'product_uos_qty': uos_qty_rest-lots_uos_qty,
								'state': move.state,
							}
						move_qty = move_qty-lots[x]
						uos_qty_rest = uos_qty_rest-lots_uos_qty
						if move_qty >0.0:
							current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
							move_obj.write(cr,uid,[current_move],{
								'product_qty': lots[x],
								'product_uos_qty': lots_uos_qty,
								'state': move.state,
								'prodlot_id':x,})
							#print "===============",move_qty,lots[x],lots
						else:
							move_obj.write(cr,uid,[move.id],{'product_qty':move_qty,'product_uos_qty':uos_qty_rest,'prodlot_id':x})
							move_qty = 0.0
							uos_qty_rest = 0.0
				if move_qty>0.0:
					move_obj.write(cr,uid,[move.id],{'product_qty':move_qty,'product_uos_qty':uos_qty_rest,'prodlot_id':False})
		return True

	def test_assigned(self, cr, uid, ids):
		""" Tests whether the move is in assigned state or not.
		@return: True or False
		"""
		#TOFIX: assignment of move lines should be call before testing assigment otherwise picking never gone in assign state
		old_ok = super(stock_picking,self).test_assigned(cr,uid,ids)
		ok = True

		for pick in self.browse(cr, uid, ids):
			mt = pick.move_type
			# incomming shipments are always set as available if they aren't chained
			if pick.type == 'in':
				if all([x.state != 'waiting' for x in pick.move_lines]):
					return True
			for move in pick.move_lines:
				if (move.state in ('confirmed', 'draft')) and (mt == 'one'):
					return False
				if (mt == 'direct') and (move.state == 'assigned') and (move.product_qty):
					return True
				ok = ok and (move.state in ('cancel', 'done', 'assigned'))
		
		old_ok = ok
		return old_ok

	def check_book(self,cr,uid,ids,state,context=None):
		if not context:context={}
		if isinstance(ids,(tuple,list)):
			if len(ids)>0:
				picking = self.browse(cr,uid,ids[0],context)
			else:
				pass
		else:
			picking = self.browse(cr,uid,ids,context)
		# print "33333333333333333333",picking.container_book_id.state,state
		if picking.container_book_id and picking.container_book_id.state == state:
			#print "========================bbbbbb-----------------"
			return True
		# print "FAAAAAAAAAAAALSE"
		return False

	def action_done(self, cr, uid, ids, context=None):
		"""Changes picking state to done.
		
		This method is called at the end of the workflow by the activity "done".
		@return: True
		"""
		picking = self.browse(cr, uid, ids, context=context)[0]
		self.write(cr, uid, ids, {'state': 'done', 'date_done': picking.date_done!='False' and picking.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
		return True

	def do_partial(self, cr, uid, ids, partial_datas, context=None):
		""" Makes partial picking and moves done.
		@param partial_datas : Dictionary containing details of partial picking
						  like partner_id, partner_id, delivery_date,
						  delivery moves with product_id, product_qty, uom
		@return: Dictionary of values
		"""
		# vals = super(stock_picking,self).do_partial(cr, uid, ids, partial_datas, context=context)
		if context is None:
			context = {}
		else:
			context = dict(context)
		res = {}
		sj_number = ""
		move_obj = self.pool.get('stock.move')
		product_obj = self.pool.get('product.product')
		currency_obj = self.pool.get('res.currency')
		uom_obj = self.pool.get('product.uom')
		sequence_obj = self.pool.get('ir.sequence')
		wf_service = netsvc.LocalService("workflow")
		for pick in self.browse(cr, uid, ids, context=context):
			new_picking = None
			complete, too_many, too_few = [], [], []
			move_product_qty, move_product_uop_qty, prodlot_ids, tracking_ids, partial_qty,partial_uop_qty, product_uoms,product_uops, product_prices= {},{},{}, {}, {}, {},{}, {}, {}
			for move in pick.move_lines:
				if move.state in ('done', 'cancel'):
					continue
				partial_data = partial_datas.get('move%s'%(move.id), {})
				product_qty = partial_data.get('product_qty',0.0)
				product_uop_qty = partial_data.get('product_uop_qty',0.0)
				move_product_qty[move.id] = product_qty
				move_product_uop_qty[move.id] = product_uop_qty
				product_uom = partial_data.get('product_uom',False)
				product_uop = partial_data.get('product_uop',False)
				product_price = partial_data.get('product_price',0.0)
				prodlot_id = partial_data.get('prodlot_id')
				prodlot_ids[move.id] = prodlot_id
				tracking_id = partial_data.get('tracking_id')
				tracking_ids[move.id] = tracking_id
				product_uoms[move.id] = product_uom
				product_uops[move.id] = product_uop
				product_prices[move.id] = product_price
				if product_uoms[move.id]!=move.product_uom.id:
					partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
				else:
					partial_qty[move.id] = product_qty
				if product_uops[move.id]!= move.product_uop.id:
					# if pick.type=='in':
					# 	partial_uop_qty[move.id]=product_uop_qty
					# else:
					partial_uop_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uops[move.id], product_uop_qty, move.product_uop.id)
				else:
					partial_uop_qty[move.id] = product_uop_qty
				if move.product_qty == partial_qty[move.id]:
					complete.append(move)
				elif move.product_qty > partial_qty[move.id]:
					too_few.append(move)
				else:
					too_many.append(move)

			if context.get('split_delivery',False) and not too_few:
				raise osv.except_osv(_('Split Delivery Error'),
					_('Cannot Split the Delivery Order because you were not Delete the lines or reduce the quantity'))
			
			for move in too_few:
				product_qty = move_product_qty[move.id]
				product_uop_qty = move_product_uop_qty[move.id]
				if not new_picking:
					ccode = pick.company_id.prefix_sequence_code
					new_picking_name = pick.name
					if pick.type=='internal':
						newval = {'name': ccode+sequence_obj.get(cr, uid,
												'stock.picking.%s'%(pick.type)),
								   'date_done': context.get('split_delivery',False) and context.get('use_existing_book',False) and context.get('existing_book_id',False) and pick.date_done!='False' and pick.date_done or False,
								   'date_done_2': context.get('split_delivery',False) and context.get('use_existing_book',False) and context.get('existing_book_id',False) and pick.date_done_2!='False' and pick.date_done or False,
								   'surat_jalan_number' : False,
								   }
					else:
						newval = {'name': sequence_obj.get(cr, uid,
												'stock.picking.%s'%(pick.type)),
								   'date_done': context.get('split_delivery',False) and context.get('use_existing_book',False) and context.get('existing_book_id',False) and pick.date_done!='False' and pick.date_done or False,
								   'date_done_2': context.get('split_delivery',False) and context.get('use_existing_book',False) and context.get('existing_book_id',False) and pick.date_done_2!='False' and pick.date_done or False,
								   'surat_jalan_number' : False,
								   }
					
					self.write(cr, uid, [pick.id], newval)
					date_done = False
					date_done_2 = False
					if not context.get('split_delivery',False):
						date_done = pick.date_done!=False and pick.date_done or datetime.now().strftime('%Y-%m-%d 19:00:00')
						date_done_2 = pick.date_done_2!=False and pick.date_done_2 or (pick.date_done!=False and datetime.strptime(pick.date_done,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') or time.strftime('%Y-%m-%d'))
					elif context.get('split_delivery',False):
						date_done = pick.date_done!=False and pick.date_done or False
						date_done_2 = pick.date_done_2!=False and pick.date_done_2 or (pick.date_done!=False and datetime.strptime(pick.date_done,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') or False)
					
					new_picking = self.copy(cr, uid, pick.id,
							{
								'name': new_picking_name,
								'move_lines' : [],
								'state':'draft',
								# 'date_done':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								'date_done' : date_done,
								'date_done_2' : date_done_2,
							})
				if product_qty != 0:
					defaults = {
							'product_qty' : product_qty,
							'product_uos_qty': product_qty, #TODO: put correct uos_qty
							'product_uop_qty' : product_uop_qty,
							'picking_id' : new_picking,
							'state': context.get('split_delivery',False) and 'draft' or 'assigned',
							'move_dest_id': False,
							'price_unit': product_prices[move.id],
							'product_uom': product_uoms[move.id],
							'date':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d 19:00:00'),
					}
					prodlot_id = prodlot_ids[move.id]
					if prodlot_id:
						defaults.update(prodlot_id=prodlot_id)
					tracking_id = tracking_ids[move.id]
					if tracking_id:
						defaults.update(tracking_id=tracking_id)
					move_obj.copy(cr, uid, move.id, defaults)
				move_obj.write(cr, uid, [move.id],
						{
							'product_qty': move.product_qty - partial_qty[move.id],
							'product_uop_qty': move.product_uop_qty - partial_uop_qty[move.id],
							'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
							'prodlot_id': move.prodlot_id and move.prodlot_id.id or False,
							'tracking_id': move.tracking_id and move.tracking_id.id or False,
							'date':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						})

			if new_picking:
				move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
			for move in complete:
				if move.product_id.cost_method=='standard' and move.product_id.valuation=='manual_periodic':
					defaults = {
						'product_uom': product_uoms[move.id],
						'date':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						'product_qty': move_product_qty[move.id],
						}
				else:
					defaults = {
					'product_uom': product_uoms[move.id],
					'date':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					'product_qty': move_product_qty[move.id],
					'price_unit':product_prices[move.id],}
				if prodlot_ids.get(move.id):
					defaults.update({'prodlot_id': prodlot_ids[move.id]})
				# print "=====================",move.product_id.name,defaults
				move_obj.write(cr, uid, [move.id], defaults)
			for move in too_many:
				product_qty = move_product_qty[move.id]
				product_uop_qty = move_product_uop_qty[move.id]
				defaults = {
					'date':pick.date_done!='False' and pick.date_done or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					'product_qty' : product_qty,
					'product_uop_qty' : product_uop_qty,
					'product_uos_qty': product_qty, #TODO: put correct uos_qty
					'product_uom': product_uoms[move.id],
					'price_unit':product_prices[move.id],
				}
				prodlot_id = prodlot_ids.get(move.id)
				if prodlot_ids.get(move.id):
					defaults.update(prodlot_id=prodlot_id)
				if new_picking:
					defaults.update(picking_id=new_picking)
				move_obj.write(cr, uid, [move.id], defaults)

			# At first we confirm the new picking (if necessary)
			if new_picking:
				if not context.get('split_delivery',False):
				# if pick.type!='internal':
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
				
				created_picking = self.browse(cr,uid,new_picking)
				if created_picking.type =='out' and created_picking.sale_type=='export' and created_picking.container_book_id and created_picking.container_book_id.state == 'booked':
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booked', cr)
					if pick.state == 'confirmed':
						wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booking_confirmed', cr)	
				elif created_picking.type =='out' and created_picking.sale_type=='export' and created_picking.container_book_id and created_picking.container_book_id.state == 'instructed':
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booked', cr)
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booking_confirmed', cr)
					self.write(cr,uid,new_picking,{'state':'instructed'})
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'instructed', cr)
				elif created_picking.type =='out' and created_picking.sale_type=='export' and not context.get('split_delivery',False):
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booked', cr)
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'booking_confirmed', cr)
					self.write(cr,uid,new_picking,{'state':'instructed'})
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'instructed', cr)
				
				if not context.get('split_delivery',False):
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
				
				# Then we finish the good picking
				existing_book = context.get('use_existing_book',False) and context.get('existing_book_id',False) or False
				self.write(cr, uid, [pick.id], {'backorder_id': new_picking,'container_book_id':existing_book})

				if not context.get('split_delivery',False):
					self.action_move(cr, uid, [new_picking], context=context)
					wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
					# Update Number into Surat Jalan Number Format
					if pick.type=='out' and not pick.surat_jalan_number:
						company_id = pick.company_id
						company_code = ''
						goods_type = pick.sale_id.goods_type
						if goods_type not in ('finish','finish_others','raw','asset','stores','packing','service'):
							goods_type = 'others'
							
						if company_id:
							company_code=company_id.prefix_sequence_code
						if goods_type=='finish_others':
							sj_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.'+pick.sale_type+'.finisho') or '/')
						else:
							sj_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.'+pick.sale_type+'.'+goods_type) or '/')
						if sj_number:
							self.write(cr, uid, [new_picking], {'name': sj_number,'surat_jalan_number':sj_number})
					elif pick.type=='out' and pick.surat_jalan_number:
						self.write(cr, uid, [new_picking], {'name': pick.surat_jalan_number,'surat_jalan_number':pick.surat_jalan_number})
						self.write(cr, uid, [pick.id], {'surat_jalan_number':''})
				
				if pick.type == 'out' and pick.sale_type=='export' and not existing_book:
					move_ids = [x.id for x in pick.move_lines]

					# this needed when we split delivery order when the state is already in "assigned" 
					self.action_draft_moves(cr, uid, [pick.id])
					wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
					
					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'cancel_instructed', cr)
					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booking_cancelled', cr)
					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'book_to_book1', cr)
					
					# this needed when we deliver product partially
					self.action_draft_moves(cr, uid, [pick.id])
					wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
				
				wf_service.trg_write(uid, 'stock.picking', new_picking, cr)
				delivered_pack_id = new_picking
				back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
				self.message_post(cr, uid, ids, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
			else:
				self.action_move(cr, uid, [pick.id], context=context)
				wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
				delivered_pack_id = pick.id

				# Update Number into Surat Jalan Number Format
				if pick.type=='out' and not pick.surat_jalan_number:
					company_id = pick.company_id
					company_code = ''
					goods_type = pick.sale_id.goods_type
					if goods_type not in ('finish','finish_others','raw','asset','stores','packing','service'):
						goods_type = 'others'
					if pick.date_done!=False:
						cd = {'date':pick.date_done}
					if company_id:
						company_code=company_id.prefix_sequence_code
					if goods_type=='finish_others':
						sj_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.'+pick.sale_type+'.finisho', context=cd) or '/')
					else:
						sj_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.'+pick.sale_type+'.'+goods_type, context=cd) or '/')
					if sj_number:
						self.write(cr, uid, [pick.id], {'name': sj_number,'surat_jalan_number':sj_number})
			
			delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
			res[pick.id] = {'delivered_picking': delivered_pack.id or False}
		return res

	def action_draft_moves(self, cr, uid, ids, context=None):
		for pick in self.browse(cr, uid, ids, context=context):
			todo = []
			for move in pick.move_lines:
				if move.state !='draft':
					todo.append(move.id)
			if len(todo):
					self.pool.get('stock.move').write(cr, uid, todo ,{'state':'draft'},context=context)
		return True

	def action_cancel(self, cr, uid, ids, context=None):
		""" Changes picking state to cancel.
		@return: True
		"""
		for pick in self.browse(cr, uid, ids, context=context):
			ids2 = [move.id for move in pick.move_lines]
			self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
		self.write(cr, uid, ids, {'state': 'cancel'})
		return True

	def _prepare_stuffing(self, cr, uid, picking, manufacturer_id, context=None):
		""" Builds the dict containing the values for the invoice
			@param picking: picking object
			@return: dict that will be used to create the stuffing memo object
		"""
		stuffing_vals = {
			'manufacturer' : manufacturer_id!='null' and manufacturer_id or False,
			'name': (picking.name or ''),
			'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
			'creation_date': context.get('creation_date', False),
			'stuffing_date' : datetime.strptime(picking.min_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
			'picking_ids' : [(6,0,[picking.id])],
		}
		return stuffing_vals

	def _prepare_stuffing_group(self, cr, uid, picking, stuffing, context=None):
		""" Builds the dict for grouped invoices
			@param picking: picking object
			@param stuffing: object of the stuffing memo that we are updating
			@return: dict that will be used to update the stuffing memo
		"""
		return {
			'name': (stuffing.name or '') + '; ' + (picking.name or ''),
			'origin': (stuffing.origin or '') + ', ' + (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
			'creation_date': context.get('creation_date', False),
			'stuffing_date' : datetime.strptime(picking.min_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
		}

	def _prepare_stuffing_line(self, cr, uid, group, picking, move_line, stuffing_id,
		stuffing_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: move_line: move_line object
			@param: stuffing_id: ID of the related stuffing memo
			@param: stuffing_vals: dict used to created the stuffing memo
			@return: dict that will be used to create the stuffing memo line
		"""
		if group:
			name = (picking.name or '') + '-' + move_line.name
		else:
			name = move_line.name
		
		# set UoS if it's a sale and the picking doesn't have one
		uom_id = move_line.product_uom and move_line.product_uom.id or False
		uop_id = move_line.product_uop and move_line.product_uop.id or False
		
		return {
			'name': name,
			'stuffing_id': stuffing_id,
			'product_id': move_line.product_id.id,
			'product_qty': move_line.product_qty,
			'product_uom': uom_id,
			'product_uop_qty': move_line.product_uop_qty,
			'product_uop': uop_id,
			'stock_move_id':move_line.id,
			'picking_id':picking.id,
			'prodlot_id': move_line.prodlot_id and move_line.prodlot_id.id or False,
			'tracking_id': move_line.tracking_id and move_line.tracking_id.id or False,
			'state' : 'draft',
			'container_size' : picking.container_size and picking.container_size.id or (move_line.sale_line_id and move_line.sale_line_id.container_size and move_line.sale_line_id.container_size.id or False),
		}

	def action_stuffing_memo_create(self, cr, uid, ids, group=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param group: Whether to create a group stuffing memo or not
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		stuffing_obj = self.pool.get('stuffing.memo')
		stuffing_line_obj = self.pool.get('stuffing.memo.line')
		partner_obj = self.pool.get('res.partner')
		stuffings_group_by_manufacturer = {}

		for picking in self.browse(cr, uid, ids, context=context):	
			for move_line in picking.move_lines:
				if move_line.state == 'cancel':
					continue
				if move_line.scrapped:
					# do no invoice scrapped products
					continue
				if move_line.product_id.manufacturer:
					if move_line.product_id.manufacturer.id in stuffings_group_by_manufacturer:
						stuffings_group_by_manufacturer[move_line.product_id.manufacturer.id].append(move_line)
					else:
						stuffings_group_by_manufacturer.update({move_line.product_id.manufacturer.id:[]})
						stuffings_group_by_manufacturer[move_line.product_id.manufacturer.id].append(move_line)
				else:
					# grouping for Product that doesnt have information of its manufacturer 
					if 'null' in stuffings_group_by_manufacturer:
						stuffings_group_by_manufacturer['null'].append(move_line)
					else:
						stuffings_group_by_manufacturer.update({'null':[]})
						stuffings_group_by_manufacturer['null'].append(move_line)


		res = {}
		for manufacturer_id in stuffings_group_by_manufacturer.keys():
			stuffings_group_by_date = {}
			for picking in self.browse(cr, uid, ids, context=context):	
				# min_date=datetime.strptime(picking.min_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
				if group and "min_date" in stuffings_group_by_date:
					stuffing_id = stuffings_group_by_date["min_date"]
					stuffing = stuffing_obj.browse(cr, uid, stuffing_id)
					if picking.id not in [x.id for x in stuffing.picking_ids]:
						stuffing.write({'picking_ids':[(4,picking.id)]})
					stuffing_vals_group = self._prepare_stuffing_group(cr, uid, picking, stuffing, context=context)
					stuffing_obj.write(cr, uid, [stuffing_id], stuffing_vals_group, context=context)
				else:
					stuffing_vals = self._prepare_stuffing(cr, uid, picking, manufacturer_id,context=context)
					stuffing_id = stuffing_obj.create(cr, uid, stuffing_vals, context=context)
					stuffings_group_by_date["min_date"] = stuffing_id
				res[picking.id] = stuffing_id
				for move_line in picking.move_lines:
					if move_line.state == 'cancel':
						continue
					if move_line.scrapped:
						# do no invoice scrapped products
						continue
					if move_line.product_id.manufacturer:
						if move_line.product_id.manufacturer.id==manufacturer_id:
							vals = self._prepare_stuffing_line(cr, uid, group, picking, move_line,
									stuffing_id, stuffing_vals, context=context)
							if vals:
								stuffing_line_id = stuffing_line_obj.create(cr, uid, vals, context=context)
					else:
						if 'null'==manufacturer_id:
							vals = self._prepare_stuffing_line(cr, uid, group, picking, move_line,
										stuffing_id, stuffing_vals, context=context)
							if vals:
								stuffing_line_id = stuffing_line_obj.create(cr, uid, vals, context=context)
						
				# self.write(cr, uid, [picking.id], {
				# 	'stuffing_id': stuffing_id,
				# 	}, context=context)
		return res

	def _invoice_hook(self, cursor, user, picking, invoice_id):
		sale_obj = self.pool.get('sale.order')
		order_line_obj = self.pool.get('sale.order.line')
		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		
		# there is possibility that one stock.picking.out contains more than one sale.order
		# so we will create list variable of sale.order, and than update the invoice_ids fields for each sale.order
		sale_ids = []
		if picking.move_lines:
			for move in picking.move_lines:
				if move.sale_line_id and move.sale_line_id.order_id:
					sale_ids.append(move.sale_line_id.order_id.id)
			sale_obj.write(cursor, user, sale_ids, {
				'invoice_ids': [(4, invoice_id)],
			})
		return super(stock_picking, self)._invoice_hook(cursor, user, picking, invoice_id)

	def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
		""" Builds the dict containing the values for the invoice
			@param picking: picking object
			@param partner: object of the partner to invoice
			@param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
			@param journal_id: ID of the accounting journal
			@return: dict that will be used to create the invoice object
		"""
		invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
		
		if picking.draft_invoice_number and inv_type=='out_invoice':
			invoice_vals.update({'internal_number':picking.draft_invoice_number})
		if picking.sale_type and picking.sale_type=='export':
			invoice_vals.update({'separate_tax':False})
		elif picking.sale_type and picking.sale_type=='local':
			invoice_vals.update({'separate_tax':True})
		
		curr_idr_id = self.pool.get('res.currency').search(cr,uid,[('name','=','IDR')],context=context)
		if inv_type=='out_invoice' and invoice_vals.get('currency_id',False) and curr_idr_id and invoice_vals.get('currency_id',False) == curr_idr_id[0]:
			invoice_vals.update({'use_kmk_ar_ap':True})
		elif inv_type=='in_invoice':
			invoice_vals.update({'currency_tax_id':picking.company_id and picking.company_id.currency_id.id or False})

		if 'comment' in invoice_vals.keys():
			del invoice_vals['comment']
		return invoice_vals

	def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
		invoice_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: move_line: move_line object
			@param: invoice_id: ID of the related invoice
			@param: invoice_vals: dict used to created the invoice
			@return: dict that will be used to create the invoice line
		"""

		res=super(stock_picking,self)._prepare_invoice_line(cr, uid, group, picking, move_line,invoice_id, invoice_vals, context=context)
		# remove stock_picking reference from name
		if group:
			if ((picking.name or '') + '-') in res['name']:
				res.update({'name':res['name'].replace(((picking.name or '') + '-'),'')})
		
		lc_obj=self.pool.get("letterofcredit")
		lc_product_line_obj=self.pool.get("letterofcredit.product.line")
		proforma_obj=self.pool.get("proforma.invoice")
		proforma_line_obj=self.pool.get("proforma.invoice.line")
		
		# set invoice line name : define description/name in invoice base on spesific contidion
		name_set = res['name']
		if picking.sale_id:
			if picking.sale_id.payment_method=='lc':
				if move_line.lc_product_line_id:
					name_set = move_line.lc_product_line_id.name
				else:
					lc_ids=[]
					for lc in picking.lc_ids:
						lc_ids.append(lc.id)
					if lc_ids:
						lc_product_line_ids=lc_product_line_obj.search(cr, uid, [('lc_id','in',lc_ids),('product_id','=',move_line.product_id.id),('price_unit','=',move_line.sale_line_id.price_unit),('cone_weight','=',move_line.sale_line_id.cone_weight),('application','=',move_line.sale_line_id.application)])
						if lc_product_line_ids:
							for line in lc_product_line_obj.browse(cr,uid,lc_product_line_ids):
								name_set=line.name
						
			elif picking.sale_id.payment_method=='tt' and picking.sale_id.advance_percentage!=0.0:
				proforma_ids=[]
				for proforma in picking.sale_id.proforma_ids:
					proforma_ids.append(proforma.id)
				if proforma_ids:
					proforma_line_ids=proforma_line_obj.search(cr,uid, [('invoice_id','in',proforma_ids),('product_id','=',move_line.product_id.id),('price_unit','=',move_line.sale_line_id.price_unit)])
					if proforma_line_ids:
						for line in proforma_line_obj.browse(cr,uid,proforma_line_ids):
							name_set=line.name


			res.update({'name':name_set})
		# set invoice line name end
		return res

class stock_picking_out(osv.osv):
	_inherit = "stock.picking.out"
	_columns = {
		'show_partner_address' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text' : fields.text('Consignee Address Details'),
		
		'container_book_id' : fields.many2one('container.booking', 'Shipping Instruction', readonly=False),
		'notify' : fields.many2one('res.partner','Notify Party'),
		
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text' : fields.text('Notify Address Details'),
		
		'forwading' : fields.many2one('stock.transporter','Forwading', required=False),
		"forwading_charge":fields.many2one("stock.transporter.charge","Forwading Charge"),
		"shipping_lines":fields.many2one("stock.transporter","Shipping Lines"),
		'container_size' : fields.many2one('container.size','Container Size'),
		'teus' : fields.char('TEUS.', help="Container Type Code Bitratex",size=50),
		'container_number' : fields.char('Container No.', size=50),
		'tare_weight' : fields.float('Container Tare Weight', digits_compute=dp.get_precision("Product Unit of Measure")),
		'gross_weight' : fields.float('Gross Weight', digits_compute=dp.get_precision("Product Unit of Measure")),
		'destination_country' : fields.char('Destination Country', size=50),
		'truck_number' : fields.char('Truck No.', size=50),
		'driver_id' : fields.many2one('driver','Driver'),
		'truck_type' : fields.many2one('stock.transporter.truck','Truck Type'),
		'seal_number' : fields.char('Seal No.', size=50),
		'fumigation_remarks' : fields.char('Fumigation', size=50),
		"trucking_company":fields.many2one("stock.transporter","EMKL/Transport Vendor"),
		"trucking_charge":fields.many2one("stock.transporter.charge","Trucking Charge"),
		"porters":fields.many2one("stock.porters","Porters"),
		"porters_charge":fields.many2one("stock.porters.charge","Porters Charge"),
		'estimation_deliv_date' : fields.datetime('Estimated Delivery Date',states={'done':[('readonly', False)], 'cancel':[('readonly',False)]}),
		'estimation_arriv_date' : fields.datetime('Estimated Arrival Date',states={'done':[('readonly', False)], 'cancel':[('readonly',False)]}),
		'stuffing_ids' : fields.many2many('stuffing.memo','stock_picking_stuffing_rel','stuffing_id','picking_id','Related Stuffing Memo(s)',readonly=True),
		'state': fields.selection([
			('draft', 'Draft'),
			('cancel', 'Cancelled'),
			('auto', 'Waiting Another Operation'),
			('booking_created', 'Ready to book'),
			('booked', 'Booked'),
			('confirmed', 'Waiting Availability'),
			('instructed', 'Instructed'),
			('assigned', 'Ready to Transfer'),
			('done', 'Shipped'),
			], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
			* Draft: not confirmed yet and will not be scheduled until confirmed\n
			* Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
			* Waiting Availability: still waiting for the availability of products\n
			* Booked: container booking has been created and confirmed\n
			* Instructed: Shipping Instruction has been Created\n
			* Ready to Transfer: products reserved, simply waiting for confirmation.\n
			* Shipped: has been processed, can't be modified or cancelled anymore\n
			* Cancelled: has been cancelled, can't be confirmed anymore"""
		),
		'surat_jalan_number' : fields.char('Surat Jalan No.',size=128),
		'draft_invoice_number' : fields.char('Draft Invoice Number', readonly=True),
		'draft_invoice_id' : fields.many2one('stock.proforma.invoice','Draft Invoice Number', readonly=True),
		'sale_type': fields.selection([('export','Export'),('local','Local')],"Sale Type",required=False),
		'date_done_2' : fields.date('Date of Delivery', help="Date of Completion", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
	}

	def onchange_trucking_company(self, cr, uid, uds, trucking_company, context=None):
		res = {'truck_type':False}
		if trucking_company:
			truck_ids = self.pool.get('stock.transporter.truck').search(cr, uid, [('transporter_id','=',trucking_company)])
			if truck_ids:
				res['truck_type'] = truck_ids[0]
		return {'value':res}

	def onchange_forwading_charge(self, cr, uid, uds, forwading_charge, context=None):
		res = {'destination_country':False}
		if forwading_charge:
			charge_id = self.pool.get('stock.transporter.charge').search(cr, uid, [('id','=',forwading_charge)])
			if charge_id:
				charge = self.pool.get('stock.transporter.charge').browse(cr, uid, charge_id)[0]
				res['destination_country'] = charge.port_id and charge.port_id.name+', '+charge.country_id.name or charge.country_id.name
		return {'value':res}
	
	def onchange_date_done_2(self, cr, uid, uds, date_done_2, context=None):
		res = {'date_done':False}
		if date_done_2:
			res['date_done'] = datetime.strptime(date_done_2,"%Y-%m-%d").strftime("%Y-%m-%d 12:00:00")
		return {'value':res}

	def compute_prod_lot_ids(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.pool.get('stock.picking').compute_prod_lot_ids(cr,uid,ids,context=context)

	def _prepare_shipping_instruction(self, cr, uid, picking):
		vals = {}
		vals.update({
			'name': self.pool.get('ir.sequence').get(cr, uid, 'container.booking'),
			'date_instruction' : datetime.now(),
			'shipper' : picking.company_id.id,
			# 'show_shipper_address' : picking.show_partner_address,
			# 's_address_text' : picking.c_address_text or '',

			'consignee' : picking.partner_id.id,
			'show_consignee_address' : picking.show_partner_address,
			'c_address_text' : picking.c_address_text or '',

			'consignee_pl' : picking.partner_id.id,
			'show_consignee_address_pl' : picking.show_partner_address,
			'c_address_text_pl' : picking.c_address_text or '',
			
			'notify_party' : picking.sale_id and (picking.sale_id.notify and picking.sale_id.notify.id or False) or False,
			'show_notify_address' : picking.show_notify_address,
			'n_address_text' : picking.n_address_text or '',
			
			'stuffing_date' : picking.min_date,
			'estimation_date' : picking.estimation_deliv_date,
			'port_from' : picking.sale_id and (picking.sale_id.source_port_id and picking.sale_id.source_port_id.id or False) or False,
			'port_from_desc' : picking.sale_id and (picking.sale_id.source_port_id and picking.sale_id.source_port_id.name or '') or '',
			'port_to' : picking.sale_id and (picking.sale_id.dest_port_id and picking.sale_id.dest_port_id.id or False) or False,
			'port_to_desc' : picking.sale_id and (picking.sale_id.dest_port_id and picking.sale_id.dest_port_id.name or '') or '',
			# 'note' : picking.note,
			# 'picking_ids' : ids,
			"shipping_lines":picking.shipping_lines and picking.shipping_lines.id or False,
			"forwading":picking.forwading and picking.forwading.id or False,
			'state' : 'draft',
			})
		
		# if picking.move_lines:
		# 	for line in picking.move_lines:
		# 		if line.lc_product_line_id

		return vals

	def _prepare_shipping_instruction_line(self, cr, uid, line):
		lc_obj=self.pool.get("letterofcredit")
		lc_product_line_obj=self.pool.get("letterofcredit.product.line")
		proforma_obj=self.pool.get("proforma.invoice")
		proforma_line_obj=self.pool.get("proforma.invoice.line")
		uom_obj = self.pool.get('product.uom')
		
		vals = {}
		name_set =  line.sale_line_id and line.sale_line_id.name + (line.sale_line_id.sale_type=='export' and '\n'+line.sale_line_id.export_desc or line.sale_line_id.local_desc) or line.name
		if line.picking_id.sale_id:
			if line.picking_id.sale_id.payment_method=='lc':
				if line.lc_product_line_id:
					name_set = line.lc_product_line_id.name
				elif line.picking_id:
					lc_ids=[]
					if line.picking_id.lc_ids:
						for lc in line.picking_id.lc_ids:
							lc_ids.append(lc.id)
					elif line.picking_id.sale_id.lc_ids:
						for lc in line.picking_id.sale_id.lc_ids:
							lc_ids.append(lc.id)
					if lc_ids:
						lc_product_line_ids=lc_product_line_obj.search(cr, uid, [('lc_id','in',lc_ids),('product_id','=',line.product_id.id),('price_unit','=',line.sale_line_id.price_unit),('cone_weight','=',line.sale_line_id.cone_weight),('application','=',line.sale_line_id.application)])
						if lc_product_line_ids:
							for line1 in lc_product_line_obj.browse(cr,uid,lc_product_line_ids):
								name_set=line1.name
			elif line.picking_id.sale_id.payment_method=='tt' and line.picking_id.sale_id.advance_percentage!=0.0:
				proforma_ids=[]
				for proforma in line.picking_id.sale_id.proforma_ids:
					proforma_ids.append(proforma.id)
				if proforma_ids:
					proforma_line_ids=proforma_line_obj.search(cr,uid, [('invoice_id','in',proforma_ids),('product_id','=',line.product_id.id),('price_unit','=',line.sale_line_id.price_unit)])
					if proforma_line_ids:
						for line1 in proforma_line_obj.browse(cr,uid,proforma_line_ids):
							name_set=line1.name
		
		kgs_uom = uom_obj.search(cr,uid,[('name','=','KGS')])
		if not kgs_uom:
			raise osv.except_osv(_('Configuration Error !'),
				_('There are no KGS uom in the master !'))
		kgs_brw = uom_obj.browse(cr,uid,kgs_uom[0])
		gross_weight_per_package = line.product_uop and line.product_id and line.product_id.internal_type=='Finish' and line.product_id.sd_type=='2' and line.product_uop.gross_weight_double or line.product_uop.gross_weight
		gross_weight_per_package = uom_obj._compute_qty_obj(cr, uid, kgs_brw, gross_weight_per_package, line.product_uom) or 0.0
		net_weight_per_package = line.product_uop and uom_obj._compute_qty_obj(cr, uid, kgs_brw, line.product_uop.net_weight, line.product_uom) or 0.0
		gross_weight = line.product_uop_qty * gross_weight_per_package
		net_weight = line.product_uop_qty * net_weight_per_package
		volume = 0.0
		if line.product_uop and line.product_uop.dimension_uom:
			uom_categ, uom_length_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_meter')
			if uom_length_id:
				try:
					length = line.product_uop.length and float(line.product_uop.length) or 0.0
				except (orm.except_orm, ValueError):
					length = 0.0
				try:
					width = line.product_uop.width and float(line.product_uop.width) or 0.0
				except (orm.except_orm, ValueError):
					width = 0.0
				try:
					height = line.product_uop.height and float(line.product_uop.height) or 0.0
				except (orm.except_orm, ValueError):
					height = 0.0
				l = uom_obj._compute_qty(cr, uid, line.product_uop.dimension_uom.id, length, uom_length_id)
				w = uom_obj._compute_qty(cr, uid, line.product_uop.dimension_uom.id, width, uom_length_id)
				h = uom_obj._compute_qty(cr, uid, line.product_uop.dimension_uom.id, height, uom_length_id)
				volume = l*w*h

		temp = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","1","2","3","4","5","6","7","8","9","0"," "]
		tracking = list(line.tracking_id and line.tracking_id.name or "")
		for indx in range(0,len(tracking)):
			if tracking[indx] not in temp:
				tracking.pop(indx)

		try:
			name_set = name_set.decode("utf-8").encode("utf-8"),
		except:
			name_set = name_set

		vals.update({
			'product_id' : line.product_id.id,
			'product_desc' : name_set,
			'product_desc_pl' : name_set,
			'packing_type': line.product_uop and line.product_uop.packing_type and line.product_uop.packing_type.name or '',
			'product_uop' : line.product_uop and line.product_uop.id or False,
			'gross_weight' : gross_weight,
			'net_weight' : line.product_qty,
			'sale_line_id': line.sale_line_id and line.sale_line_id.id or False,
			'volume' : line.product_uop_qty*volume,
			'packages':line.product_uop_qty or 0.0,
			'tracking_name':tracking and "".join(tracking) or "",
			
			'gross_weight_per_uop' : line.product_id and line.product_id.internal_type=='Finish' and line.product_id.sd_type=='2' and line.product_uop.gross_weight_double or line.product_uop.gross_weight,
			'net_weight_per_uop' : line.product_uop.net_weight,
			'cone_weight' : line.product_uop.cone_weight,
			'cones' : line.product_uop.cones,
			'length' : line.product_uop.length,
			'width' : line.product_uop.width,
			'height' : line.product_uop.height,
			})
		return vals

	def group_shipping_instruction_lines(self, cr, uid, line):
		line2 = {}
		i = 0
		for l in line:
			key="%s-%s-%s"%(l['product_id'],l['product_uop'],l['tracking_name'])

			if key in line2:
				line2[key]['gross_weight'] += l['gross_weight']
				line2[key]['net_weight'] += l['net_weight']
				line2[key]['packages'] += l['packages']
				line2[key]['volume'] += l['volume']
			else:
				line2[key] = l

		line = []
		for key, val in line2.items():
			line.append(val)
		return line

	def button_create_container_booking(self, cr, uid, ids, context=None):
		cont_booking_obj = self.pool.get('container.booking')
		cont_booking_line_obj = self.pool.get('container.booking.line')
		picking = self.browse(cr, uid, ids)[0]
		
		if picking.container_book_id:
			raise osv.except_osv(_('Creation Abort!'), _('There is Container Booking that has created for this Document'))
		else:
			cont_booking = cont_booking_obj.create(cr, uid, self._prepare_shipping_instruction(cr, uid, picking))
			move_lines = []
			for line in picking.move_lines:
				move_lines.append(self._prepare_shipping_instruction_line(cr, uid, line))
			m = self.group_shipping_instruction_lines(cr, uid, move_lines)
			# m = move_lines
			# for index in range(0,len(m)):
			# 	del m[index]['product_uop']
			move_lines_grouped=map(lambda x:(0,0,x),m)

			cont_booking_obj.write(cr, uid, cont_booking, {'goods_lines':move_lines_grouped})

			self.pool.get('stock.picking').write(cr, uid, ids, {'container_book_id':cont_booking})

		return True

	def draft_force_assign(self, cr, uid, ids, *args):
		""" Confirms picking directly from draft state.
		@return: True
		"""
		wf_service = netsvc.LocalService("workflow")
		for pick in self.browse(cr, uid, ids):
			if not pick.move_lines:
				raise osv.except_osv(_('Error!'),_('You cannot process picking without stock moves.'))
			if pick.sale_type == 'export' and pick.type=='out':
				wf_service.trg_validate(uid, 'stock.picking', pick.id,
					'button_confirm', cr)
				if pick.container_book_id:
					wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booked', cr)
					if pick.container_book_id.state == 'booked':
						wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booking_confirmed', cr)
					elif pick.container_book_id.state == 'instructed':
						wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booking_confirmed', cr)
						self.write(cr,uid,pick.id,{'state':'instructed'})
						wf_service.trg_validate(uid, 'stock.picking', pick.id, 'instructed', cr)
			else:
				wf_service.trg_validate(uid, 'stock.picking', pick.id,
					'button_confirm', cr)
		return True

	def _prepare_draft_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
		""" Builds the dict containing the values for the invoice
			@param picking: picking object
			@param partner: object of the partner to invoice
			@param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
			@param journal_id: ID of the accounting journal
			@return: dict that will be used to create the invoice object
		"""
		if isinstance(partner, int):
			partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
		if inv_type in ('out_invoice', 'out_refund'):
			payment_term = partner.property_payment_term.id or False
		else:
			payment_term = partner.property_supplier_payment_term.id or False
		# comment = self._get_comment_invoice(cr, uid, picking)
		invoice_vals = {
			'name': picking.name,
			'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
			'type': inv_type,
			# 'account_id': account_id,
			'partner_id': partner.id,
			# 'comment': '',
			'payment_term': payment_term,
			'date_invoice': context.get('date_inv', False),
			'company_id': picking.company_id.id,
			'user_id': uid,
		}
		cur_id = self.get_currency_id(cr, uid, picking)
		if cur_id:
			invoice_vals['currency_id'] = cur_id
		if journal_id:
			invoice_vals['journal_id'] = journal_id

		return invoice_vals

	def _prepare_draft_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
		""" Builds the dict for grouped invoices
			@param picking: picking object
			@param partner: object of the partner to invoice (not used here, but may be usefull if this function is inherited)
			@param invoice: object of the invoice that we are updating
			@return: dict that will be used to update the invoice
		"""
		return {
			'name': (invoice.name or '') + ', ' + (picking.name or ''),
			'origin': (invoice.origin or '') + ', ' + (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
			'date_invoice': context.get('date_inv', False),
		}

	def _prepare_draft_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
		invoice_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: move_line: move_line object
			@param: invoice_id: ID of the related invoice
			@param: invoice_vals: dict used to created the invoice
			@return: dict that will be used to create the invoice line
		"""
		if group:
			name = (picking.name or '') + '-' + move_line.name
		else:
			name = move_line.name
		origin = move_line.picking_id.name or ''
		if move_line.picking_id.origin:
			origin += ':' + move_line.picking_id.origin
		# set UoS if it's a sale and the picking doesn't have one
		uos_id = move_line.product_uos and move_line.product_uos.id or False
		if not uos_id and invoice_vals['type'] in ('out_invoice', 'out_refund'):
			uos_id = move_line.product_uom.id

		res = {
			'name': name,
			'origin': origin,
			'invoice_id': invoice_id,
			'uos_id': uos_id,
			'product_id': move_line.product_id.id,
			# 'account_id': account_id,
			'price_unit': self._get_price_unit_invoice(cr, uid, move_line, invoice_vals['type']),
			# 'discount': self._get_discount_invoice(cr, uid, move_line),
			'quantity': move_line.product_uos_qty or move_line.product_qty,
			'invoice_line_tax_id': [(6, 0, self._get_taxes_invoice(cr, uid, move_line, invoice_vals['type']))],
			# 'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
		}

		# remove stock_picking reference from name
		if group:
			if ((picking.name or '') + '-') in res['name']:
				res.update({'name':res['name'].replace(((picking.name or '') + '-'),'')})
		
		lc_obj=self.pool.get("letterofcredit")
		lc_product_line_obj=self.pool.get("letterofcredit.product.line")
		proforma_obj=self.pool.get("proforma.invoice")
		proforma_line_obj=self.pool.get("proforma.invoice.line")
		
		# set invoice line name : define description/name in invoice base on spesific contidion
		name_set = res['name']
		if picking.sale_id:
			if picking.sale_id.payment_method=='lc':
				if move_line.lc_product_line_id:
					name_set = move_line.lc_product_line_id.name
				else:
					lc_ids=[]
					for lc in picking.lc_ids:
						lc_ids.append(lc.id)
					if lc_ids:
						lc_product_line_ids=lc_product_line_obj.search(cr, uid, [('lc_id','in',lc_ids),('product_id','=',move_line.product_id.id),('price_unit','=',move_line.sale_line_id.price_unit),('cone_weight','=',move_line.sale_line_id.cone_weight),('application','=',move_line.sale_line_id.application)])
						if lc_product_line_ids:
							for line in lc_product_line_obj.browse(cr,uid,lc_product_line_ids):
								name_set=line.name
						
			elif picking.sale_id.payment_method=='tt' and picking.sale_id.advance_percentage!=0.0:
				proforma_ids=[]
				for proforma in picking.sale_id.proforma_ids:
					proforma_ids.append(proforma.id)
				if proforma_ids:
					proforma_line_ids=proforma_line_obj.search(cr,uid, [('invoice_id','in',proforma_ids),('product_id','=',move_line.product_id.id),('price_unit','=',move_line.sale_line_id.price_unit)])
					if proforma_line_ids:
						for line in proforma_line_obj.browse(cr,uid,proforma_line_ids):
							name_set=line.name


			res.update({'name':name_set})
		# set invoice line name end
		return res

	def action_draft_invoice_create(self, cr, uid, ids, journal_id=False,
			group=False, type='out_invoice', context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: Id of journal
		@param group: Whether to create a group invoice or not
		@param type: Type invoice to be created
		@return: Ids of created invoices for the pickings
		"""
		if context is None:
			context = {}

		invoice_obj = self.pool.get('stock.proforma.invoice')
		invoice_line_obj = self.pool.get('stock.proforma.invoice.line')
		partner_obj = self.pool.get('res.partner')
		invoices_group = {}
		res = {}
		inv_type = type
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.invoice_state != '2binvoiced':
				continue
			partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the picking list if you want to generate invoice.'))

			if not inv_type:
				inv_type = self._get_invoice_type(picking)

			invoice_vals = self._prepare_draft_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_draft_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
				invoices_group[partner.id] = invoice_id
			res[picking.id] = invoice_id
			for move_line in picking.move_lines:
				if move_line.state == 'cancel':
					continue
				if move_line.scrapped:
					# do no invoice scrapped products
					continue
				vals = self._prepare_draft_invoice_line(cr, uid, group, picking, move_line,
								invoice_id, invoice_vals, context=context)
				if vals:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
					move_line.write({'draft_invoice_line_id': invoice_line_id})

			# invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
			# 		set_total=(inv_type in ('in_invoice', 'in_refund')))
			# self.write(cr, uid, [picking.id], {
			# 	'invoice_state': 'invoiced',
			# 	}, context=context)
			# self._invoice_hook(cr, uid, picking, invoice_id)
		# self.write(cr, uid, res.keys(), {
		# 	'invoice_state': 'invoiced',
		# 	}, context=context)
		return res
stock_picking_out()


class stock_move(osv.osv):
	_inherit = "stock.move"

	def _get_ids_from_stock_picking(self, cr, uid, ids, context=None):
		res = []
		for picking in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
			for line in picking.move_line:
				if line.id not in res:
					res.append(line.id)
		return res

	def get_sequence(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		result={}
		no=1
		for line in self.browse(cr,uid,sorted(ids)):
			if not line.picking_id:
				result[line.id]=0
				continue
			line_ids = self.search(cr,uid,[('picking_id','=',line.picking_id.id),('sequence_no','!=',0)])
			curr_total_line = len(line_ids)
			n = 0
			for line_id in sorted(line_ids):
				n += 1
				result[line_id] = n
			
			if line.id not in result.keys() and not line.sequence_no:
				result[line.id]=int(curr_total_line+1)
		return result

	_columns = {
		'draft_invoice_line_id' : fields.many2one('stock.proforma.invoice.line','Draft Invoice Line', readonly=True),
		"gross_weight" : fields.float('Gross Weight',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information for bitratex MRR"),
		"net_weight" : fields.float('Net Weight',digits_compute=dp.get_precision('Product Unit of Measure'),help="additional information for bitratex MRR"),
		'picking_ids' : fields.many2many('stock.picking','stock_move_stock_picking_rel','move_line_id','picking_id','Issue',domain=[('type','=','internal'),('state','=','done')]),
		'stock_move_line_ids' : fields.one2many('stock.move.line','move_line_id','Detail Issues'),
		'remarks' : fields.text("remarks"),
		'sequence_no' : fields.function(get_sequence, type='integer', string='Seq', method=True, 
			store={
				'stock.picking':(_get_ids_from_stock_picking,['move_line'],10),
				'stock.move':(lambda self,cr,uid,ids,context={}:ids,['picking_id'],10),
			}),
	}


	def onchange_picking_ids(self, cr, uid, ids, product_id, picking_ids):
		values = {}
		product_obj = self.pool.get('product.product')
		picking_obj = self.pool.get('stock.picking')
		if product_id and picking_ids:
			values.update({'stock_move_line_ids':[]})
			product = product_obj.browse(cr, uid, product_id)
			
			if product.blend_id:
				product_component_ids = [x.product_id.id for x in product.blend_id.bom_lines if x.product_id]
				for picking in picking_obj.browse(cr, uid, picking_ids[0][2]):
					for move in picking.move_lines:
						if move.product_id and move.product_id.id in product_component_ids:
						# if move.product_id:
							values['stock_move_line_ids'].append({
									'source_move_line_id' : move.id,
									'product_id' : move.product_id.id,
									'description' : move.name,
									'product_qty' : move.product_qty,
									'product_uom' : move.product_uom and move.product_uom.id or False,
								})

		return {'value':values}

	def action_assign(self, cr, uid, ids, *args):
		""" Changes state to confirmed or waiting.
		@return: List of values
		"""
		todo = []
		for move in self.browse(cr, uid, ids):
			if move.state in ('confirmed', 'waiting'):
				todo.append(move.id)
			elif move.picking_id.type=='out' and move.picking_id.sale_type=='local':
				todo.append(move.id)
		res = self.check_assign(cr, uid, todo)
		return res

	def _default_location_destination(self, cr, uid, context=None):
		""" Gets default address of partner for destination location
		@return: Address id or False
		"""
		mod_obj = self.pool.get('ir.model.data')
		picking_type = context.get('picking_type')
		location_id = False
		# print "==========dest=========",context
		if context is None:
			context = {}
		if context.get('move_line', []):
			if context['move_line'][0]:
				if isinstance(context['move_line'][0], (tuple, list)):
					location_id = context['move_line'][0][2] and context['move_line'][0][2].get('location_dest_id',False)
				else:
					move_list = self.pool.get('stock.move').read(cr, uid, context['move_line'][0], ['location_dest_id'])
					location_id = move_list and move_list['location_dest_id'][0] or False
		elif context.get('address_out_id', False):
			property_out = self.pool.get('res.partner').browse(cr, uid, context['address_out_id'], context).property_stock_customer
			location_id = property_out and property_out.id or False
		elif context.get('location_dest_id',False):
			location_id=context.get('location_dest_id',False)
		else:
			location_xml_id = False
			if picking_type in ('in', 'internal'):
				location_xml_id = 'stock_location_stock'
			elif picking_type == 'out':
				location_xml_id = 'stock_location_customers'
			if location_xml_id:
				try:
					location_model, location_id = mod_obj.get_object_reference(cr, uid, 'stock', location_xml_id)
					with tools.mute_logger('openerp.osv.orm'):
						self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
				except (orm.except_orm, ValueError):
					location_id = False

		return location_id

	
	def _default_location_source(self, cr, uid, context=None):
		""" Gets default address of partner for source location
		@return: Address id or False
		"""
		# print "==========source=========",context
		mod_obj = self.pool.get('ir.model.data')
		picking_type = context.get('picking_type')
		location_id = False

		if context is None:
			context = {}
		if context.get('move_line', []):
			try:
				location_id = context['move_line'][0][2]['location_id']
			except:
				pass
		elif context.get('address_in_id', False):
			part_obj_add = self.pool.get('res.partner').browse(cr, uid, context['address_in_id'], context=context)
			if part_obj_add:
				location_id = part_obj_add.property_stock_supplier.id
		elif context.get('location_id',False):
			# print "------------",location
			location_id=context.get('location_id',False)
		else:
			location_xml_id = False
			if picking_type == 'in':
				location_xml_id = 'stock_location_suppliers'
			elif picking_type in ('out', 'internal'):
				location_xml_id = 'stock_location_stock'
			if location_xml_id:
				try:
					location_model, location_id = mod_obj.get_object_reference(cr, uid, 'stock', location_xml_id)
					with tools.mute_logger('openerp.osv.orm'):
						self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
				except (orm.except_orm, ValueError):
					location_id = False

		return location_id

	_defaults = {
		'location_id': _default_location_source,
		'location_dest_id': _default_location_destination,
		'sequence_no' : 0,
	}


	# def write(self, cr, uid, ids, vals, context=None):
	# 	if isinstance(ids, (int, long)):
	# 		ids = [ids]
	# 	access = self.pool.get('ir.model.access').check(cr, uid, 'stock.move', 'write', context)
	# 	if uid != 1 and uid!=175:
	# 		res= super(stock_move, self).write(cr, uid, ids, vals, context=context)
	# 	elif uid==175:
	# 		res= super(stock_move, self).write(cr, 1, ids, vals, context=context)
	# 		tuple_ids = tuple(ids)
	# 		query = "update stock_move set write_uid="+str(uid)+" where id in "+ str(tuple_ids)[:-2]+")"
	# 		cr.execute(query)ick
	# 	else:
	# 		res =super(stock_move, self).write(cr, uid, ids, vals, context=context)

	# 	return  res


class stock_move_line(osv.Model):
	_name = "stock.move.line"
	_rec_name = "product_id"
	_columns = {
		"move_line_id" : fields.many2one("stock.move","Move Line"),
		"source_move_line_id" : fields.many2one("stock.move","Source Move Line"),
		"product_id" : fields.many2one("product.product","Product"),
		"description" : fields.char("Description", size=128),
		"product_qty" : fields.float("Quantity",digits_compute=dp.get_precision("Product Unit of Measure")),
		"product_uom" : fields.many2one("product.uom","Unit of Measure"),
	}

stock_move_line()