from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class shipping_instruction(osv.osv):
	_name = "container.booking"
	_columns = {
		'name' : fields.char('No',size=50),
		'date_instruction' : fields.date('Date Order'),
		'shipper' : fields.many2one('res.company','Shipper',required=True),
		'show_shipper_address' : fields.boolean('Use Customs Address Desc?'),
		's_address_text' : fields.text('Shipper Address Details'),
		
		'forwading' : fields.many2one('stock.transporter','Forwading', required=False),
		'shipping_lines' : fields.many2one('stock.transporter','Shipping Lines', required=False),

		'consignee' : fields.many2one('res.partner','Consignee/Buyer',domain=[('customer', '=', True)], required=False),
		'show_consignee_address' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text' : fields.text('Consignee Address Details'),

		'notify_party' : fields.many2one('res.partner','Notify Party',domain=[('customer', '=', True)], required=False),
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text' : fields.text('Notify Address Details'),

		'applicant' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)], required=False),
		'show_applicant_address' : fields.boolean('Use Customs Address Desc?'),
		'a_address_text' : fields.text('Applicant Address Details'),

		'buyer' : fields.many2one('res.partner','Buyer',domain=[('customer', '=', True)], required=False),
		'show_buyer_address' : fields.boolean('Use Customs Address Desc?'),
		'b_address_text' : fields.text('Buyer Address Details'),

		'stuffing_date' : fields.date('Stuffing Date',required=True),
		'estimation_date' : fields.date('Estimation Date',required=False),
		'goods_lines' : fields.one2many('container.booking.line','booking_id','Goods'),
		'package_details' : fields.one2many('packing.product.detail','container_book_id','Package Details'),
		'port_from' : fields.many2one('res.port','From Port'),
		'port_from_desc' : fields.char('From Port Desc', size=50),
		'port_to' : fields.many2one('res.port','To Port'),
		'port_to_desc' : fields.char('To Port Desc', size=50),
		'feeder_vessel' : fields.char('Feeder Vessel',size=50),
		'connect_vessel' : fields.char('Connect Vessel',size=50),
		'freight' : fields.char('Freight',size=50),
		'documentation' : fields.char('Documentation',size=50),
		'note' : fields.text('Note'),
		'picking_ids' : fields.one2many('stock.picking','container_book_id','Delivery Order(s)',readonly=False),
		'need_approval' : fields.boolean("Need Approval"),
		'approved_by' : fields.many2one("res.users","Approved By"),
		'state' : fields.selection([
			('cancel','Cancelled'),
			('draft','Draft'),
			('booked','Booked'),
			('instructed','Instructed')],'Status'),
		'is_final' : fields.boolean('Is Final'),
		'sending_date' : fields.date('Sending Date'),
		'booking_no': fields.char('Booking No', size=50),
		'peb_no': fields.char('PEB No', size=50),
		'peb_date' : fields.date('PEB Date'),
		'pkbe_no': fields.char('PKBE No', size=50),
		'packinglist_title'		: fields.char('Packing List Title', size=120),
		#note description SI for BL
		'desc_SIforBL': fields.text('Description SI for BL'),
		'desc_for_packinglist': fields.text('Description for Packing List'),
		'label_print' : fields.text('Label Print'),
		"model_id":fields.many2one('ir.model','Model'),
		'note_for_packinglist': fields.text('Packing List Note'),
		## consigne notify for packing list
		'consignee_pl' : fields.many2one('res.partner','Consignee/Buyer',domain=[('customer', '=', True)], required=False),
		'show_consignee_address_pl' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text_pl' : fields.text('Consignee Address Details'),

		'notify_party_pl' : fields.many2one('res.partner','Notify Party',domain=[('customer', '=', True)], required=False),
		'show_notify_address_pl' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text_pl' : fields.text('Notify Address Details'),

		'applicant_pl' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)], required=False),
		'show_applicant_address_pl' : fields.boolean('Use Customs Address Desc?'),
		'a_address_text_pl' : fields.text('Applicant Address Details'),
		
		'authorized_by' : fields.many2one('hr.employee','Authorized By'),
	}
	_defaults = {
		'state' : 'draft',
		'model_id': lambda self,cr,uid,context:self.pool.get('ir.model').search(cr,uid,[('model','=',self._name)])[0],
		'label_print':'{}',
		'note' : "PLEASE GIVE GOOD CONTAINER AND CLEAN CONDITION\nPLEASE GIVE  FREE DEMMURRAGE TIME\nPLEASE PROTECT THE CARGO, SHOULD NO ROLLOVER/DELAY\nIF ANY ROLLOVER AND CLAIM FROM OUR CUSTOMER, WE WILL PASS ON TO YOU/SERVICE PROVIDER"
	}
	_order = "id desc"

	def check_picking_state(self, cr, uid, picking_ids, context=None):
		done = True
		if picking_ids:
			for pick in self.pool.get('stock.picking').browse(cr,uid,picking_ids):
				#print "pick===========	",pick
				if pick.state=='done':
					done = False
		return done

	def action_booked(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		for picking_id in container_id.picking_ids:
			wf_service.trg_validate(uid, 'stock.picking', picking_id.id, 'booked', cr)
		# print "container_booking==================="
		return self.write(cr,uid,ids,{'state':'booked'})
	
	def action_instructed(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		for picking in container_id.picking_ids:
			if picking.state!='confirmed':
				raise osv.except_osv(_('Instructed is not Allowed! Please proceed your delivery document into stock checking step'), _(''))
		for picking in container_id.picking_ids:
			self.pool.get('stock.picking').write(cr,uid,picking.id,{'state':'instructed'})
			wf_service.trg_validate(uid, 'stock.picking', picking.id, 'instructed', cr)
		return self.write(cr,uid,ids,{'state':'instructed'})

	def action_booked_cancel(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		nodone=self.check_picking_state(cr,uid,[x.id for x in container_id.picking_ids],context)
		if nodone:
			for pick in  container_id.picking_ids:
				wf_service.trg_validate(uid, 'stock.picking', pick.id, 'booking_cancelled', cr)
		
			self.write(cr,uid,ids,{'state':'draft'})
		else:
			raise osv.except_osv(_('Cancel Denied!'), _('There are some Delivery Order that has Transfered to Customer'))
		return True 
	
	def action_instructed_cancel(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		nodone=self.check_picking_state(cr,uid,[x.id for x in container_id.picking_ids],context)
		if nodone:
			for pick in container_id.picking_ids:
				wf_service.trg_validate(uid, 'stock.picking', pick.id, 'cancel_instructed', cr)
				self.pool.get('stock.picking').write(cr,uid,pick.id,{'state':'booked'})
			self.write(cr,uid,ids,{'state':'booked'})
		else:
			raise osv.except_osv(_('Cancel Denied!'), _('There are some Delivery Order that has Transfered to Customer'))
		return True

	def action_cancel(self,cr,uid,ids,context=None):
		container_id = self.browse(cr,uid,ids[0],context=context)
		nodone = self.check_picking_state(cr,uid,container_id.picking_id.id,context)
		if nodone:
			for picking in container_id.picking_ids:
				picking_id = self.pool.get('stock.picking').write(cr,uid,picking.id,{'container_book_id':False})
			self.write(cr,uid,ids,{'state':'cancel'})
		else:
			raise osv.except_osv(_('Cancel Denied!'), _('There are some Delivery Order that has Transfered to Customer'))
		
		return True

	def action_finalized(self,cr,uid,ids,context=None):
		container_id = self.browse(cr,uid,ids[0],context=context)
		self.write(cr,uid,ids,{'is_final':True})

		return True

	def action_unfinalized(self,cr,uid,ids,context=None):
		container_id = self.browse(cr,uid,ids[0],context=context)
		self.write(cr,uid,ids,{'is_final':False})

		return True

	# def get_address(self, partner_obj):
	# 	if partner_obj:
	# 		partner_address = ''
	# 		partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
	# 		partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
	# 		partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
	# 		partner_address += partner_obj.city and partner_obj.city +' ' or ''
	# 		partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
	# 		partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''

	# 		return  partner_address
	# 	else:
	# 		return False

	def get_lc(self, picking_ids, product_ids):
		res1 = []
		res2 = []
		for picking in picking_ids:
			for move in picking.move_lines:
				# print ">>>>>>>>>>>>>>>>>>>>> cek", move.lc_product_line_id, move.lc_product_line_id not in res, move.product_id.id, move.product_id.id in product_ids
				if move.lc_product_line_id and move.lc_product_line_id not in res1 and move.product_id.id in product_ids:
					res1.append(move.lc_product_line_id)
					if move.lc_product_line_id.lc_id not in res2:
						res2.append(move.lc_product_line_id.lc_id)
			for lc in picking.lc_ids:
				if lc not in res2:
					res2.append(lc)
		return res1, res2

	def update_good_lines(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_pool = self.pool.get('container.booking.line')
		picking_pool = self.pool.get('stock.picking.out')
		for si in self.browse(cr, uid, ids, context=context):
			for line in si.goods_lines:
				line_pool.unlink(cr, uid, line.id)
			move_lines = []
			for move in [x for picking in si.picking_ids if picking.move_lines for x in picking.move_lines]:
				move_lines.append(picking_pool._prepare_shipping_instruction_line(cr, uid, move))
			m = picking_pool.group_shipping_instruction_lines(cr, uid, move_lines)
			# m = move_lines
			move_lines_grouped=map(lambda x:(0,0,x),m)
			self.write(cr, uid, si.id, {'goods_lines':move_lines_grouped})
		return True

	def update_description(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		for si in self.browse(cr, uid, ids, context=context):
			#update the good lines
			# res1 = self.update_good_lines(cr, uid, [si.id], context=context)

			shipper_id = False
			use_shipper = False
			shipper_desc = ""
			
			consignee_id = False
			use_consignee = False
			consignee_desc = ""
			consignee_id_pl = False
			use_consignee_pl = False
			consignee_desc_pl = ""
			
			applicant_id = False
			use_applicant = False
			applicant_desc = ""
			applicant_id_pl = False
			use_applicant_pl = False
			applicant_desc_pl = ""
			
			buyer_id = False
			use_buyer = False
			buyer_desc = ""
			
			notify_id = False
			use_notify = False
			notify_desc = ""
			notify_id_pl = False
			use_notify_pl = False
			notify_desc_pl = ""
			
			source_port_id = False
			source_port_desc = ""
			dest_port_id = False
			dest_port_desc = ""
			picking_ids = si.picking_ids
			sale_ids = []
			if picking_ids:
				product_ids = [x.product_id.id for x in si.goods_lines]
				lc_product_lines, lc_objs = self.get_lc(picking_ids,product_ids)
				# first, take desc from lc_product_lines
				# move_line_ids = [y.id for x in picking_ids for y in x.move_lines]
				if lc_product_lines:
					lc_product_lines_desc = {}
					for line in lc_product_lines:
						if line.consignee and not consignee_id:
							consignee_id = line.consignee.id
						if line.show_consignee_address and not use_consignee:
							use_consignee = line.show_consignee_address
						if line.c_address_text and not consignee_desc:
							consignee_desc = line.c_address_text
						if line.consignee_pl and not consignee_id_pl:
							consignee_id_pl = line.consignee_pl.id
						if line.show_consignee_address_pl and not use_consignee_pl:
							use_consignee_pl = line.show_consignee_address_pl
						if line.c_address_text_pl and not consignee_desc_pl:
							consignee_desc_pl = line.c_address_text_pl

						if line.notify and not notify_id:
							notify_id = line.notify.id
						if line.show_notify_address and not use_notify:
							use_notify = line.show_notify_address
						if line.n_address_text and not notify_desc:
							notify_desc = line.n_address_text
						if line.notify_pl and not notify_id_pl:
							notify_id_pl = line.notify_pl.id
						if line.show_notify_address_pl and not use_notify_pl:
							use_notify_pl = line.show_notify_address_pl
						if line.n_address_text_pl and not notify_desc_pl:
							notify_desc_pl = line.n_address_text_pl

						if line.lc_dest and not dest_port_id:
							dest_port_id = line.lc_dest.id
						if line.lc_dest_desc and not dest_port_desc:
							dest_port_desc = line.lc_dest_desc
						
						key1 = line.product_id.id
						key2 = line.sale_line_id.id
						if (key1,key2) not in lc_product_lines_desc:
							lc_product_lines_desc.update({(key1,key2):line.name})
					for prod in si.goods_lines:
						product_id = prod.product_id.id
						sale_line_ids = []
						if prod.booking_id and prod.booking_id.picking_ids:
							sale_line_ids = [move.sale_line_id.id for picking in prod.booking_id.picking_ids if picking.move_lines for move in picking.move_lines if move.sale_line_id and move.product_uop and prod.product_uop and (move.product_uop==prod.product_uop)] 
						for sale_line_id in sale_line_ids:
							if sale_line_id and (product_id,sale_line_id) in lc_product_lines_desc:
								self.pool.get('container.booking.line').write(cr, uid, prod.id, {'product_desc':lc_product_lines_desc[(product_id,sale_line_id)],'product_desc_pl':lc_product_lines_desc[(product_id,sale_line_id)]})

				if lc_objs:
					for lc in lc_objs:
						# if lc.shipper and not shipper_id:
						# 	shipper_id = lc.shipper.id
						if lc.show_shipper_address and not use_shipper:
							use_shipper = lc.show_shipper_address
						if lc.s_address_text and not shipper_desc:
							shipper_desc = lc.s_address_text
						
						if lc.applicant and not applicant_id:
							applicant_id = lc.applicant.id
						if lc.show_applicant_address and not use_applicant:
							use_applicant = lc.show_applicant_address
						if lc.a_address_text and not applicant_desc:
							applicant_desc = lc.a_address_text
						if lc.applicant_pl and not applicant_id_pl:
							applicant_id_pl = lc.applicant_pl.id
						if lc.show_applicant_address_pl and not use_applicant_pl:
							use_applicant_pl = lc.show_applicant_address_pl
						if lc.a_address_text_pl and not applicant_desc_pl:
							applicant_desc_pl = lc.a_address_text_pl
						
						if lc.consignee and not consignee_id:
							consignee_id = lc.consignee.id
						if lc.show_consignee_address and not use_consignee:
							use_consignee = lc.show_consignee_address
						if lc.c_address_text and not consignee_desc:
							consignee_desc = lc.c_address_text
						if lc.consignee_pl and not consignee_id_pl:
							consignee_id_pl = lc.consignee_pl.id
						if lc.show_consignee_address_pl and not use_consignee_pl:
							use_consignee_pl = lc.show_consignee_address_pl
						if lc.c_address_text_pl and not consignee_desc_pl:
							consignee_desc_pl = lc.c_address_text_pl
						
						if lc.notify and not notify_id:
							notify_id = lc.notify.id
						if lc.show_notify_address and not use_notify:
							use_notify = lc.show_notify_address
						if lc.n_address_text and not notify_desc:
							notify_desc = lc.n_address_text
						if lc.notify_pl and not notify_id_pl:
							notify_id_pl = lc.notify_pl.id
						if lc.show_notify_address_pl and not use_notify_pl:
							use_notify_pl = lc.show_notify_address_pl
						if lc.n_address_text_pl and not notify_desc_pl:
							notify_desc_pl = lc.n_address_text_pl
					update_val={}
					# if shipper_id:
					# update_val.update({'shipper':shipper_id})
					# if use_shipper:
					update_val.update({'show_shipper_address':use_shipper})
					# if shipper_desc:
					update_val.update({'s_address_text':shipper_desc})
					
					# if applicant_id:
					update_val.update({'applicant':applicant_id})
					# if use_applicant:
					update_val.update({'show_applicant_address':use_applicant})
					# if applicant_desc:
					update_val.update({'a_address_text':applicant_desc})
					# if applicant_id_pl:
					update_val.update({'applicant_pl':applicant_id_pl})
					# if use_applicant_pl:
					update_val.update({'show_applicant_address_pl':use_applicant_pl})
					# if applicant_desc_pl:
					update_val.update({'a_address_text_pl':applicant_desc_pl})

					# if consignee_id:
					update_val.update({'consignee':consignee_id})
					# if use_consignee:
					update_val.update({'show_consignee_address':use_consignee})
					# if consignee_desc:
					update_val.update({'c_address_text':consignee_desc})
					# if consignee_id_pl:
					update_val.update({'consignee_pl':consignee_id_pl})
					# if use_consignee_pl:
					update_val.update({'show_consignee_address_pl':use_consignee_pl})
					# if consignee_desc_pl:
					update_val.update({'c_address_text_pl':consignee_desc_pl})

					# if notify_id:
					update_val.update({'notify':notify_id})
					# if use_notify:
					update_val.update({'show_notify_address':use_notify})
					# if notify_desc:
					update_val.update({'n_address_text':notify_desc})
					# if notify_id_pl:
					update_val.update({'notify_pl':notify_id_pl})
					# if use_notify_pl:
					update_val.update({'show_notify_address_pl':use_notify_pl})
					# if notify_desc_pl:
					update_val.update({'n_address_text_pl':notify_desc_pl})

					# if dest_port_desc:
					update_val.update({'port_to_desc':dest_port_desc})
					# if dest_port_id:
					update_val.update({'port_to':dest_port_id})
					if update_val:
						self.write(cr, uid, si.id, update_val)
		return True

shipping_instruction()

class shipping_instruction_line(osv.osv):
	_name = "container.booking.line"
	_columns = {
		'sequence' : fields.integer('Sequence'),
		'product_id' : fields.many2one('product.product','Product'),
		'product_desc' : fields.text('Description on SI'),
		'product_desc_pl' : fields.text('Description on PL'),
		'gross_weight_per_uop' : fields.float('Gross Weight Per UoP',required=True, digits_compute= dp.get_precision('Product Unit of Measure')),
		'gross_weight' : fields.float('Gross Weight',required=True, digits_compute= dp.get_precision('Product Unit of Measure')),
		'net_weight_per_uop' : fields.float('Net Weight Per UoP',required=True, digits_compute= dp.get_precision('Product Unit of Measure')),
		'net_weight' : fields.float('Net Weight',required=True, digits_compute= dp.get_precision('Product Unit of Measure')),
		'cone_weight' : fields.float('Cone Weight',required=True, digits_compute= dp.get_precision('Product Unit of Measure')),
		'cones' : fields.integer('Cones',required=True),
		'volume' : fields.float('Volume',required=True, digits_compute= dp.get_precision('Account')),
		'booking_id' : fields.many2one('container.booking','Shipping ID'),
		'sale_line_id':fields.many2one('sale.order.line',"Sale line id"),
		'marks_nos' : fields.text('Marks & NOS'),
		'marks_nos_pl' : fields.text('Marks & NOS on PL'),
		'packages' : fields.float('Packages'),
		'packing_type' : fields.char('Package',size=50),
        'product_uop' : fields.many2one('product.uom', 'Packing Standard'),
        'length' : fields.char("Length",size=64),
        'width' : fields.char("Width",size=64),
        'height' : fields.char("Height",size=64),
        'tracking_name' : fields.char("Lot Number",size=64),
        'tracking_id' : fields.many2one('stock.tracking','Pack'),
	}
	_defaults = {
		'sequence' : 0,
	}

	def onchange_product_uop(self, cr, uid, ids, packages, product_uop):
		res = {
			'packing_type':'',
			'gross_weight_per_uop':0.0,
			'net_weight_per_uop':0.0,
			'gross_weight':0.0,
			'net_weight':0.0,
			'cone_weight':0.0,
			'cones':0,
			'volume':0.0,
			'length':'',
			'width':'',
			'height':'',
		}
		packages = packages and packages or 0
		uom_obj = self.pool.get("product.uom")
		if product_uop:
			product_uop = uom_obj.browse(cr, uid, product_uop)
			res['packing_type'] = product_uop.packing_type and product_uop.packing_type.name or ''
			res['gross_weight_per_uop'] = product_uop.gross_weight
			res['net_weight_per_uop'] = product_uop.net_weight
			res['cone_weight'] = product_uop.cone_weight
			res['cones'] = product_uop.cones
			res['length'] = product_uop.length
			res['width'] = product_uop.width
			res['height'] = product_uop.height

			volume = 0.0
			uom_categ, uom_length_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_meter')
			if uom_length_id and product_uop.dimension_uom:
				try:
					length = product_uop.length and float(product_uop.length) or 0.0
				except (orm.except_orm, ValueError):
					length = 0.0
				try:
					width = product_uop.width and float(product_uop.width) or 0.0
				except (orm.except_orm, ValueError):
					width = 0.0
				try:
					height = product_uop.height and float(product_uop.height) or 0.0
				except (orm.except_orm, ValueError):
					height = 0.0
				l = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, length, uom_length_id)
				w = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, width, uom_length_id)
				h = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, height, uom_length_id)
				volume = l*w*h
			res['volume'] = packages*volume
			res['gross_weight'] = packages*product_uop.gross_weight
			res['net_weight'] = packages*product_uop.net_weight

		return {'value':res}

	def onchange_dimension(self, cr, uid, ids, packages, product_uop, length, width, height):
		res = {'volume':0.0}
		packages = packages and packages or 0
		volume = 0.0
		uom_obj = self.pool.get("product.uom")
		if product_uop:
			product_uop = uom_obj.browse(cr, uid, product_uop)
			uom_categ, uom_length_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_meter')
			if uom_length_id and product_uop.dimension_uom:
				try:
					length = length and float(length) or 0.0
				except (orm.except_orm, ValueError):
					length = 0.0
				try:
					width = width and float(width) or 0.0
				except (orm.except_orm, ValueError):
					width = 0.0
				try:
					height = height and float(height) or 0.0
				except (orm.except_orm, ValueError):
					height = 0.0
				l = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, length, uom_length_id)
				w = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, width, uom_length_id)
				h = uom_obj._compute_qty(cr, uid, product_uop.dimension_uom.id, height, uom_length_id)
				volume = l*w*h
			res['volume'] = volume
		return {'value':res}

	def onchange_weight(self, cr, uid, ids, packages, gross_weight_per_uop, net_weight_per_uop):
		res = {
			# 'net_weight':0.0,
			# 'gross_weight':0.0,
		}
		packages = packages and packages or 0.0
		net_weight_per_uop = net_weight_per_uop or 0.0
		gross_weight_per_uop = gross_weight_per_uop or 0.0
		# res['net_weight'] = packages*net_weight_per_uop
		# res['gross_weight'] = packages*gross_weight_per_uop

		return {'value':res}

shipping_instruction_line()

class packing_type(osv.osv):
	_name = "packing.type"
	_columns = {
		"name" : fields.char('Name', size=128, required=True),
		"desc" : fields.text('Spesification'),
	}