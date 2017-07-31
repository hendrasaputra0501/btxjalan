from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class sale_order(osv.Model):
	_inherit = "sale.order"

	def _compute_percentage(self, cr, uid, ids, name, args, context=None):
		rs_data = {}
			
		for order in self.browse(cr, uid, ids, context=None):
			#print "order==================",order
			rs_data[order.id]={'payment_pct':0.0,'delivery_pct':0.0,}
			pay = 0.0
			delivery = 0.0
			total_product = 0.0
			for order_line in order.order_line:
				total_product += order_line.product_uom_qty

			tolerance_min = total_product >0.0 and total_product - order.tolerance_percentage or total_product
			tolerance_max = total_product >0.0 and total_product + order.tolerance_percentage or total_product
			for invoice in order.invoice_ids:
				if invoice.state in ('open','paid'):
					pay += invoice.amount_total - invoice.residual
			for picking in order.picking_ids:
#				print "picking===============",picking,
				if picking.state == 'done':
					for dline in picking.move_lines:
						delivery += dline.product_qty
			delivery_pct = delivery < tolerance_min and delivery/total_product * 100.0 or \
							delivery > total_product and delivery/tolerance_max * 100.0 or \
							delivery >= tolerance_min and delivery <= tolerance_max and 100.0 or 0.0
			try:
				rs_data[order.id].update({'payment_pct'  : order.amount_total and pay/order.amount_total*100.0 or 0.0}),
			except:
				pass
			try:	
				rs_data[order.id].update({'delivery_pct':delivery_pct}),
			except:
				pass
			#print "rs-data=============>",rs_data,pay/order.amount_total*100.0
		return rs_data
	
	def _get_move_line(self, cr, uid, ids, context=None):
		result = {}
		move_ids = []
		for move_line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
			if move_line.move_id and move_line.move_id.id not in move_ids:
				move_ids.append(move_line.move_id.id)
		invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move_ids)])
		if invoice_ids:
			for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids):
				for sale_id in invoice.sale_ids:
					result[sale_id.id] = True
		return result.keys()
	
	def _get_invoice(self, cr, uid, ids, context=None):
		result = {}
		for invoice in self.pool.get('account.invoice').browse(cr, uid, ids, context=context):
			for sale_id in invoice.sale_ids:
				result[sale_id.id] = True
		return result.keys()

	def _get_picking_out(self, cr, uid, ids, context=None):
		result = {}
		for picking in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
			result[picking.sale_id.id] = True
		return result.keys()

	_columns = {
		'client_order_ref_date'	: fields.date('Customer Ref. Date'),

		'notify'				: fields.many2one('res.partner', 'Notify', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Notify Partner for current sales contract."),
		'consignee'				: fields.many2one('res.partner', 'Consignee', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Consignee Partner for current sales contract."),
		
		"payment_pct"			: fields.function(_compute_percentage, method=True, multi='dc', type='float', string='Payment', 
									store={
									'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['state','order_line','invoice_ids','picking_ids'], 20),
									'account.invoice': (_get_invoice, ['state','invoice_line','residual','payment_ids'], 20),
									'account.move.line': (_get_move_line, ['state','reconcile_id','reconcile_partial_id'], 20),
									}
									),
		"delivery_pct"			: fields.function(_compute_percentage, method=True, multi='dc', type='float', string='Delivery',
									store={
									'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['state','order_line','invoice_ids','picking_ids'], 20),
									'stock.picking': (_get_picking_out, ['state','move_line'], 20),
									}
									),
		# 'source_country_id'		: fields.related('company_id','country_id',type="many2one",relation='res.country',string="Origin Country"),
		# 'dest_country_id'		: fields.related('partner_id','country_id',type="many2one",relation='res.country',string="Destination Country"),
		"allow_delivery"		: fields.boolean("Allow Delivery"),
		'source_country_id'		: fields.many2one('res.country',"Origin Country"),
		'dest_country_id'		: fields.many2one('res.country',"Destination Country"),
		"source_port_id"		: fields.many2one('res.port',"Origin Port"),
		"proforma_ids"			: fields.one2many('proforma.invoice','sale_id','Proforma Invoice'),
		"dest_port_id"			: fields.many2one('res.port',"Destination Port"),
		"goods_type"			: fields.selection([
						('finish','Finish Goods'),
						('finish_others','Finish Goods(Others)'),
						('raw','Raw Material'),
						('service','Services'),
						('stores','Stores'),
						('waste','Waste'),
						('scrap','Scrap'),
						('packing','Packing Material'),
						('asset','Fixed Asset')],'Goods Type',required=True),
		'sale_type'				: fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		'locale_sale_type'		: fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
		'tolerance_percentage'	: fields.float("Min. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)"),
		'tolerance_percentage_max'	: fields.float("Max. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)"),
		'payment_method'		: fields.selection([('cash','Cash'),('tt','Telegraphic Transfer (TT)'),('lc','LC')],"Payment Method"),
		'max_est_delivery_date'	: fields.date(' Max. Estimated Delivery Date'),
		"advance_ids"			: fields.many2many('account.advance.payment','sale_order_advance_rel','adv_id','order_id',"Advance Payment(s)"),
		"freight_rate_value"	: fields.float("Freight Rate"),
		"freight_rate_currency"	: fields.many2one("res.currency","Freight Rate Currency"),
		"freight_rate_uom"		: fields.many2one('product.uom', 'Freight Rate UoM '),
		"template_special_condition" : fields.many2one('template.special.condition','Template Special Condition'),
		"contract_internal_info" : fields.text('Sales Internal Info'),
		# 'opening_bank' 			: fields.many2one('res.partner.bank', 'Bank Account',
		# 	help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Supplier Refund, otherwise a Partner bank account number.'),
		# 'intermed_bank' 		: fields.many2one('res.partner.bank', 'Bank Account',
		# 	help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Supplier Refund, otherwise a Partner bank account number.'),
		# 'negotiate_bank' 		: fields.many2one('res.partner.bank', 'Bank Account',
		# 	help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Supplier Refund, otherwise a Partner bank account number.'),
		'advance_percentage'	: fields.float('Advance Percentage'),
		'is_on_ship_wkf'		: fields.boolean("Is on_ship Flow state"),
		'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
		'state': fields.selection([
			('draft', 'Draft Sales Confirmation'),
			('sent', 'Sales Confirmation Sent'),
			('cancel', 'Cancelled'),
			('waiting_date', 'Waiting Schedule'),
			('progress', 'Sales Order'),
			('lc_draft', 'LC Checking Form'),
			('advance', 'Waiting for Advance'),
			('ready_to_deliver', 'Ready for Delivery'),
			('manual', 'Sale to Invoice'),
			('shipping_except', 'Shipping Exception'),
			('invoice_except', 'Invoice Exception'),
			('done', 'Done'),
			], 'Status', readonly=True,
			help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
		'date_done': fields.date('Done Date', readonly=True, select=True, help="Date on which sales order is doned."),
		'date_cancel': fields.date('Cancel Date', readonly=True, select=True, help="Date on which sales order is canceled."),
	}
	_defaults = {
		'sale_type'	:lambda *a: 'export',
		'goods_type': lambda *a: "finish",
		'advance_percentage': lambda *a:0.0,
		'source_country_id':lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.country_id.id,
		'order_policy':lambda*a:'picking',
		'tolerance_percentage':lambda*a:0.0,
		'tolerance_percentage_max':lambda*a:0.0,
		'freight_rate_currency':lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id.id,
	}

	# def action_view_delivery(self, cr, uid, ids, context=None):
	# 	'''
	# 	This function returns an action that display existing delivery orders of given sales order ids. It can either be a in a list or in a form view, if there is only one delivery order to show.
	# 	'''
	# 	mod_obj = self.pool.get('ir.model.data')
	# 	act_obj = self.pool.get('ir.actions.act_window')

	# 	result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree')
	# 	id = result and result[1] or False
	# 	result = act_obj.read(cr, uid, [id], context=context)[0]
	# 	#compute the number of delivery orders to display
	# 	pick_ids = []
	# 	for so in self.browse(cr, uid, ids, context=context):
	# 		pick_ids += [picking.id for picking in so.picking_ids]
	# 	#choose the view_mode accordingly
	# 	if len(pick_ids) > 1:
	# 		result['domain'] = "[('id','in',["+','.join(map(str, pick_ids))+"])]"
	# 	else:
	# 		res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_out_form')
	# 		result['views'] = [(res and res[1] or False, 'form')]
	# 		result['res_id'] = pick_ids and pick_ids[0] or False
	# 	return result

	def reverse_manual_delivery(self,cr,uid,ids,context=None):
		if not context:context={}
		sale = self.browse(cr,uid,ids)[0]
		picking_exists = False
		for pick in sale.picking_ids:
			if pick.state!='cancel':
				picking_exists=True
		if picking_exists:
			raise osv.except_osv(_('Warning!'), _('Please cancel all picking for this document first!'))
		else:
			wf_service = netsvc.LocalService("workflow")
			if not sale.is_on_ship_wkf:
				wf_service.trg_validate(uid, 'sale.order', ids[0], 'reverse_manual_delivery', cr)
			else:
				wf_service.trg_validate(uid, 'sale.order', ids[0], 'reverse_ship', cr)
		return True

	def reverse_manual_delivery_lc(self,cr,uid,ids,context=None):
		if not context:context={}
		sale = self.browse(cr,uid,ids)[0]
		picking_exists = False

		for pick in sale.picking_ids:
			if pick.state!='cancel':
				picking_exists=True
		if picking_exists:
			raise osv.except_osv(_('Warning!'), _('Please cancel all picking for this document first!'))
		else:
			wf_service = netsvc.LocalService("workflow")
			if not sale.is_on_ship_wkf:
				wf_service.trg_validate(uid, 'sale.order', ids[0], 'reverse_manual_delivery_lc', cr)
			else:
				wf_service.trg_validate(uid, 'sale.order', ids[0], 'reverse_ship', cr)
		return True

	def test_state(self, cr, uid, ids, mode, *args):
		res = super(sale_order,self).test_state(cr,uid,ids,mode,*args)
		assert mode in ('finished', 'canceled'), _("invalid mode for test_state")
		finished = True
		canceled = False
		tolerance = False
		write_done_ids = []
		write_cancel_ids = []
		uom_pool = self.pool.get('product.uom')
		for order in self.browse(cr, uid, ids, context={}):
			orders_states=[]
			for line in order.order_line:
				# tolerance_qty = 0.0
				
				product_qty = 0.0 # qty shipped
				if (not line.procurement_id) or (line.procurement_id.state=='done'):
					if line.state != 'done':
						write_done_ids.append(line.id)
				else:
					finished = False
				if line.procurement_id:
					if (line.procurement_id.state == 'cancel'):
						canceled = True
						if line.state != 'exception':
							write_cancel_ids.append(line.id)
				if order.order_policy == 'picking':
					if line.move_ids:
						for move_line in line.move_ids:
							if move_line.state =='done':
								product_qty += uom_pool._compute_qty_obj(cr, uid, move_line.product_uom, move_line.product_qty, line.product_uom)
					# tolerance_qty = line.product_uom_qty - (order.tolerance_percentage/100.0 * line.product_uom_qty)
				
				if not product_qty or (line.product_uom_qty - product_qty) > line.min_knock_off_qty:
					finished = False
					# print "====xxxfinished1=====",finished
				else:
					if line.id not in write_done_ids:
						write_done_ids.append(line.id)
						finished=True
						# print "====xxxfinished2=====",finished
				if line.knock_off:
					if line.id not in write_done_ids:
						write_done_ids.append(line.id)
					finished = finished and True
				orders_states.append(finished)
			
		if write_done_ids:
			self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
		if write_cancel_ids:
			self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'exception'})
		#print "======= finished =======",finished
		if mode == 'finished':
			 res= all(os==True for os in orders_states) #finished
		elif mode == 'canceled':
			 res= all(os==True for os in orders_states) #canceled
		print "res----------",res,write_done_ids
		return res

	def create(self, cr, uid, vals, context=None):
		company_pooler = self.pool.get('res.company')
		sale_pooler = self.pool.get('sale.shop')
		company_code = ''
		company_id = False
		if vals.get('name','/')=='/':
			if vals.get('company_id',False):
				company_id = company_pooler.browse(cr, uid, vals.get('company_id',False))
			elif vals.get('shop_id',False):
				company_id = sale_pooler.browse(cr, uid, vals.get('shop_id',False)).company_id
			
			if company_id:
				company_code=company_id.prefix_sequence_code
			
			sale_type = vals.get('sale_type',False)
			goods_type = vals.get('goods_type',False)
			if goods_type not in ('finish','finish_others','raw','asset','stores','packing','service'):
				goods_type = 'others'
			date = datetime.datetime.strptime(vals['date_order'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
			vals['name'] = (company_code + (self.pool.get('ir.sequence').get(cr, uid, 'sale.order.'+sale_type+'.'+goods_type, context={'date':date}) or '/'))
			
		res=super(sale_order, self).create(cr, uid, vals, context=context)
		return res

	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		company_pooler = self.pool.get('res.company')
		sale_line_pooler = self.pool.get('sale.order.line')
		
		res = super(sale_order, self).copy(cr, uid, id, default, context=context)
		sale_id = self.browse(cr, uid, res)

		company_code = ''
		company_id = False
		if sale_id.company_id:
			company_id = sale_id.company_id
		elif sale_id.shop_id:
			company_id = sale_id.shop_id.company_id
			
		if company_id:
			company_code=company_id.prefix_sequence_code
			
		sale_type = sale_id.sale_type	
		goods_type = sale_id.goods_type
		if sale_type and goods_type:
			default.update({'name':company_code + (self.pool.get('ir.sequence').get(cr, uid, 'sale.order.'+sale_type+'.'+goods_type) or '/')})

		self.write(cr,uid,res,default)
		curr_total_line = 0
		for so_line_id in sale_id.order_line:
			print "hereeee"
			curr_total_line+=1
			sale_line_pooler.write(cr, uid, so_line_id.id, {'sequence_line':curr_total_line})
			print "hereeee2", curr_total_line

		default.update({
			'date_done': False,
			'date_cancel': False,
		})
		return res

	def onchange_sale_type(self,cr,uid,ids,sale_type,context=None):
		if sale_type:
			return {'context':{'sale_type':sale_type}}
		return {'context':{'sale_type':'export'},'value':{'sale_type':'export'}}

	def onchange_partner_id(self,cr,uid,ids,part,context=None):
		res = super(sale_order,self).onchange_partner_id(cr,uid,ids,part,context=context)
		if part:
			partner = self.pool.get('res.partner').browse(cr,uid,part,context)
			res['value'].update({'dest_country_id':partner.country_id.id or False})
		return res

	def action_cancel(self, cr, uid, ids, context=None):
		res = super(sale_order,self).action_cancel(cr,uid,ids,context=context)
		self.write(cr, uid, ids, {'date_cancel': fields.date.context_today(self, cr, uid, context=context)})
		return res

	def action_done(self, cr, uid, ids, context=None):
		res = super(sale_order,self).action_done(cr,uid,ids,context=context)
		self.write(cr, uid, ids, {'date_done': fields.date.context_today(self, cr, uid, context=context)})
		return res

	def action_cancel_draft(self, cr, uid, ids, *args):
		if not len(ids):
			return False
		res = super(sale_order,self).action_cancel_draft(cr,uid,ids)
		self.write(cr, uid, ids, {'date_cancel': False})
		return True

	def action_button_confirm_force(self, cr, uid, ids, context=None):
		assert len(ids) == 1, 'This option should only be used for a single id at a time.'
		wf_service = netsvc.LocalService('workflow')
		wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)

		# redisplay the record as a sales order
		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
		view_id = view_ref and view_ref[1] or False,
		return {
			'type': 'ir.actions.act_window',
			'name': _('Sales Order'),
			'res_model': 'sale.order',
			'res_id': ids[0],
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'current',
			'nodestroy': True,
		}

	def onchange_delivery_date(self,cr,uid,ids,max_date,date_order,context=None):
		if not context:context={}
		res = {}
		if max_date and date_order:
			maximum = datetime.datetime.strptime(max_date,'%Y-%m-%d')
			order_date = datetime.datetime.strptime(date_order,'%Y-%m-%d')
			if maximum <= order_date:
				warning = {
						'title': _('Entry Warning!'),
						'message' : _('Estimated Delivery Date should be bigger than Order Date')}
				value = {'max_est_delivery_date':False}
				res.update({'warning':warning,'value':value,
					'context':context.update({'max_est_delivery_date':order_date})})
			else:
				res.update({'context':context.update({'max_est_delivery_date':maximum})})
		return res

	def onchange_tolerance(self,cr,uid,ids,tolerance,context=None):
		if not context:context={}
		res = {}
		if tolerance:
			if tolerance < 0.0 or tolerance >100.0 :
				warning = {
						'title': _('Entry Warning!'),
						'message' : _('Tolerance Percentage should be in range 0.0 until 100.0 (%)')}
				value = {'tolerance_percentage':False}
				res.update({'warning':warning,'value':value})
		return res

	def onchange_template_special_condition(self, cr, uid, ids, note, temp, context=None):
		temp_pooler = self.pool.get('template.special.condition')
		temp_id = temp and temp_pooler.browse(cr,uid,temp,context) or False
		if temp_id:
			return {'value':{'note':(note and note or '') + '\n\n' + temp_id.desc}}
		else:
			return {'value':{'note': (note and note or '')}}


	def force_delivery(self,cr,uid,ids,context=None):
		if not context:context={}
		order = self.browse(cr,uid,ids,context=context)[0]
		self.write(cr,uid,ids,{'allow_delivery':True})

		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'sale.order', order.id, 'manual_delivery_confirmed', cr)
		return True

	def force_no_delivery(self,cr,uid,ids,context=None):
		if not context:context={}
		sale = self.browse(cr,uid,ids,context)[0]
		allow_delivery=False
		if sale.allow_delivery and sale.is_on_ship_wkf:
			allow_delivery=False
		return self.write(cr,uid,ids,{'allow_delivery':allow_delivery})

	def is_advance_paid(self,cr,uid,ids,context=None):
		if not context:context={}
		#check whether the advance has been paid or not
		for sale in self.browse(cr,uid,ids,context):
			if sale.payment_method != 'lc':
				total = 0.0
				for adv in sale.advance_ids:
					if adv.state in ('posted',):
						total+=adv.total_amount or 0.0
				if total >= (0.3*sale.amount_total):
					return True
		return False

	def is_all_picked(self,cr,uid,ids,context=None):
		if not context:context={}
		#check whether the picking has been moved or not
		return False
	
	def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
		return {
			'sequence_line':line.sequence_line,
			'name': line.name,
			'origin': order.name,
			'date_planned': date_planned,
			'product_id': line.product_id.id,
			'product_qty': line.product_uom_qty,
			'product_uom': line.product_uom.id,
			'product_uos_qty': (line.product_uos and line.product_uos_qty)\
					or line.product_uom_qty,
			'product_uos': (line.product_uos and line.product_uos.id)\
					or line.product_uom.id,
			'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
			'procure_method': line.type,
			'move_id': move_id,
			'company_id': order.company_id.id,
			'note': line.name,
			'property_ids': [(6, 0, [x.id for x in line.property_ids])],
		}

	def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
		location_id = line.default_location_id and line.default_location_id.id or order.shop_id.warehouse_id.lot_stock_id.id
		output_id = order.shop_id.warehouse_id.lot_output_id.id
		product_uop_qty = line.product_uop_qty or 0.0
		product_uop = line.product_uop and line.product_uop.id or line.product_id.uop_id.id
		tracking_id = line.tracking_id and line.tracking_id.id or False
		return {
			'sequence_line':line.sequence_line,
			'name': line.name,
			'picking_id': picking_id,
			'product_id': line.product_id.id,
			'date': date_planned,
			'date_expected': date_planned,
			'product_qty': line.product_uom_qty,
			'product_uom': line.product_uom.id,
			'product_uop_qty': product_uop_qty,
			'product_uop': product_uop,
			'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
			'product_uos': (line.product_uos and line.product_uos.id)\
					or line.product_uom.id,
			'tracking_id' : tracking_id,
			'product_packaging': line.product_packaging.id,
			'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
			'location_id': location_id,
			'location_dest_id': output_id,
			'sale_line_id': line.id,
			# 'tracking_id': False,
			'state': 'draft',
			#'state': 'waiting',
			'company_id': order.company_id.id,
			'price_unit': line.product_id.standard_price or 0.0,
		}
	def _prepare_order_picking(self, cr, uid, order, context=None):
		pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
		
		c_address_text = (order.partner_shipping_id.name or '') + "\n" +\
						 (order.partner_shipping_id.street or '') + "\n" +\
						 (order.partner_shipping_id.street2 or '') + "\n" +\
						 (order.partner_shipping_id.street3 or '') + "\n" +\
						 (order.partner_shipping_id.city or '') + ", " +\
						 (order.partner_shipping_id.zip or '') + "\n" +\
						 (order.partner_shipping_id.state_id and order.partner_shipping_id.state_id.name or '') + ", " +\
						 (order.partner_shipping_id.country_id and order.partner_shipping_id.country_id.name or '')
		
		if order.notify:
			n_address_text = (order.notify.name or '') + "\n" +\
							 (order.notify.street or '') + "\n" +\
							 (order.notify.street2 or '') + "\n" +\
							 (order.notify.street3 or '') + "\n" +\
							 (order.notify.city or '') + ", " +\
							 (order.notify.zip or '') + "\n" +\
							 (order.notify.state_id and order.notify.state_id.name or '') + ", "+\
							 (order.notify.country_id and order.notify.country_id.name or '')
			
		if order.payment_method=='lc':
			lc_obj=False
			if order.lc_ids:
				for lc in order.lc_ids:
					if lc.state=='open':
						lc_obj=lc
			if lc_obj:
				c_address_text = lc_obj.consignee.c_address_text
				n_address_text = lc_obj.consignee.n_address_text
				notify = lc_obj.notify and lc_obj.notify.id or False
		
		return {
			'name': pick_name,
			'origin': order.name,
			'sale_type':order.sale_type,
			'date': self.date_to_datetime(cr, uid, datetime.date.today().strftime("%Y-%m-%d"), context),
			'type': 'out',
			'state': 'auto',
			'move_type': order.picking_policy,
			'sale_id': order.id,
			'partner_id': order.partner_shipping_id.id,
			
			# 'note': order.note,
			'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
			'company_id': order.company_id.id,
			'goods_type':order.goods_type,
		}

	def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
		start_date = self.date_to_datetime(cr, uid, start_date, context)
		if line.est_delivery_date:
			lsd = self.date_to_datetime(cr, uid, line.est_delivery_date, context)
			date_planned = (datetime.datetime.strptime(lsd, DEFAULT_SERVER_DATETIME_FORMAT)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		elif order.max_est_delivery_date:
			max_est_delivery_date = self.date_to_datetime(cr, uid, order.max_est_delivery_date, context)
			date_planned = (datetime.datetime.strptime(max_est_delivery_date, DEFAULT_SERVER_DATETIME_FORMAT)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		else:
			date_planned = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=line.delay or 0.0)
			date_planned = (date_planned - datetime.timedelta(days=order.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		return date_planned
	
	def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
		"""Create the required procurements to supply sales order lines, also connecting
		the procurements to appropriate stock moves in order to bring the goods to the
		sales order's requested location.

		If ``picking_id`` is provided, the stock moves will be added to it, otherwise
		a standard outgoing picking will be created to wrap the stock moves, as returned
		by :meth:`~._prepare_order_picking`.

		Modules that wish to customize the procurements or partition the stock moves over
		multiple stock pickings may override this method and call ``super()`` with
		different subsets of ``order_lines`` and/or preset ``picking_id`` values.

		:param browse_record order: sales order to which the order lines belong
		:param list(browse_record) order_lines: sales order line records to procure
		:param int picking_id: optional ID of a stock picking to which the created stock moves
							   will be added. A new picking will be created if ommitted.
		:return: True
		"""
		move_obj = self.pool.get('stock.move')
		picking_obj = self.pool.get('stock.picking')
		procurement_obj = self.pool.get('procurement.order')
		proc_ids = []

		for line in order_lines:
			if line.state == 'done':
				continue

			date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

			if line.product_id:
				if line.product_id.type in ('product', 'consu'):
					if not picking_id:
						print "here 0 ",self._prepare_order_picking(cr, uid, order, context=context)
						picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
						print "here 10", picking_id
					move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
				else:
					# a service has no stock move
					move_id = False

				proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
				proc_ids.append(proc_id)
				line.write({'procurement_id': proc_id})
				self.ship_recreate(cr, uid, order, line, move_id, proc_id)

		wf_service = netsvc.LocalService("workflow")
		if picking_id:
			picking_data = picking_obj.browse(cr,uid,picking_id,context)
			wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
		for proc_id in proc_ids:
			wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

		val = {}
		if order.state == 'shipping_except':
			val['state'] = 'progress'
			val['shipped'] = False

			if (order.order_policy == 'manual'):
				for line in order.order_line:
					if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
						val['state'] = 'manual'
						break
		order.write(val)
		return True
	
class sale_order_line(osv.Model):
	def _get_amount_tax(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
			res[line.id] = taxes['total_included'] - taxes['total']
			if line.order_id:
				cur = line.order_id.pricelist_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	def _set_sequence_line(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		for so_line_id in self.browse(cr,uid,ids,context):
			if so_line_id.sequence_line_1 or so_line_id.sequence_line_2:
				res[so_line_id.id]=so_line_id.order_id.name+' - '+str(so_line_id.sequence_line_1 or '')+(so_line_id.sequence_line_2 or '')
			else:
				so_ids = self.search(cr,uid,[('order_id','=',so_line_id.order_id.id),('sequence_line','!=',"/")])
				curr_total_line = len(so_ids)

				if so_line_id.sequence_line=='/':
					res[so_line_id.id]=so_line_id.order_id.name+' - '+str(curr_total_line+1)

		return res

	def _get_stock_moves_related(self, cr, uid, ids, context=None):
		res=[]

		for move in self.pool.get('stock.move').browse(cr, uid, ids):
			if move.sale_line_id and move.sale_line_id.id not in res:
				res.append(move.sale_line_id.id)
		
		return res

	def _get_so_related(self, cr, uid, ids, context=None):
		res=[]

		for order in self.pool.get('sale.order').browse(cr, uid, ids):
			if order.order_line:
				for line in order.order_line:
					if line.id not in res:
						res.append(line.id)
		return res

	def _get_min_knock_off_qty(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res = {}
		uom_pool = self.pool.get('product.uom')
		for line in self.browse(cr, uid, ids, context=context):
			bale_uom_ids = uom_pool.search(cr, uid, [('name','=','BALES')], context=context)
			bale_uoms = uom_pool.browse(cr, uid, bale_uom_ids, context=context)
			from_uom = False
			for bale in bale_uoms:
				if bale.category_id.id == line.product_uom.category_id.id:
					from_uom = bale
			if from_uom:
				res[line.id]=uom_pool._compute_qty_obj(cr, uid, from_uom, 5, line.product_uom, context=context)
			else:
				res[line.id]=0

		return res

	def _get_qty_shipped(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		uom_pool = self.pool.get('product.uom')
		for line in self.browse(cr,uid,ids,context):
			res[line.id] = {
				'product_uom_qty_shipped' : 0.0,
				'product_uom_qty_outstanding' : 0.0,
				'product_uom_qty_outstanding_kgs' : uom_pool._compute_qty_obj(cr, uid, line.product_uom, line.product_uom_qty, line.product_id.uom_id, context=context) or 0.0,
				'outstanding_min_tolerance' : 0.0,
				'is_less_than_knockoff_qty' : False,
			}
			if line.move_ids:
				for move in line.move_ids:
					if move.state == 'done':
						res[line.id]['product_uom_qty_shipped'] += uom_pool._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, line.product_uom, context=context)
						res[line.id]['product_uom_qty_outstanding_kgs'] -= uom_pool._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, line.product_id.uom_id, context=context)
				res[line.id]['product_uom_qty_outstanding'] = line.product_uom_qty - res[line.id]['product_uom_qty_shipped']
				min_out_qty = ((100-line.order_id.tolerance_percentage)/100 * line.product_uom_qty)
				if min_out_qty > res[line.id]['product_uom_qty_shipped']:
					res[line.id]['outstanding_min_tolerance'] = min_out_qty - res[line.id]['product_uom_qty_shipped']
					if res[line.id]['outstanding_min_tolerance'] <= line.min_knock_off_qty:
						res[line.id]['is_less_than_knockoff_qty'] = True
		return res

	# def _search_seq_line(self, cr, uid, obj, name, args, context):
	# 	ids = set()
	# 	for cond in args:
	# 		sequence_line = cond[2]
	# 		if isinstance(cond[2],(list,tuple)):
	# 			if cond[1] in ['in','not in']:
	# 				amount = tuple(cond[2])
	# 			else:
	# 				continue
	# 		else:
	# 			if cond[1] in ['=like', 'like', 'not like', 'ilike', 'not ilike', 'in', 'not in', 'child_of']:
	# 				continue
	# 		print "cond=================",cond
	# 		cr.execute("select id from sale_order_line %s %%s" % (cond[1]),(sequence_line,))
	# 		res_ids = set(id[0] for id in cr.fetchall())
	# 		ids = ids and (ids & res_ids) or res_ids
	# 	if ids:
	# 		return [('id', 'in', tuple(ids))]
	# 	return [('id', '=', '0')]

	_inherit = "sale.order.line"
	_columns = {
		'tax_amount':fields.function(_get_amount_tax, type='float', method=True, string='Tax Amount', digits_compute=dp.get_precision('Account'),store={
				'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['tax_id'],10),
			}),
		'product_uom_qty_shipped' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Shipped.', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"
									),
		'product_uom_qty_outstanding' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Outstanding', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"
									),
		'product_uom_qty_outstanding_kgs' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Outstanding(KGS)', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"
									),
		'outstanding_min_tolerance' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Tolerance', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'sale.order':(_get_so_related,['tolerance_percentage'],10),
									}, multi="all_shipped_qty"
									),
		'is_less_than_knockoff_qty' : fields.function(_get_qty_shipped, method=True, type='boolean', string='Less than Quantity Knock Off', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"),
		'min_knock_off_qty' 		: fields.function(_get_min_knock_off_qty,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Min Knock Off', 
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['product_uom_qty','product_uom'],10),
									}),
		'knock_off_qty' 			: fields.float('Quantity Knock Off',digits_compute=dp.get_precision('Product Unit of Measure')),
		'sequence_line_1'			: fields.integer('Nomor Urut', readonly=True, states={'draft':[('readonly',False)]}),
		'sequence_line_2'			: fields.char('Huruf',size=3, readonly=True, states={'draft':[('readonly',False)]}),
		'sequence_line' 			: fields.function(_set_sequence_line, method=True, type='char', size=50, string='Delivery Ref.',
									store={
										'sale.order.line':(lambda self,cr,uid,ids,context={}:ids,['sequence_line_1','sequence_line_2','order_id'],10),
									}
									),
		'efisiensi_rate'		: fields.float('Efisiensi Rate'),
		'other_description'		: fields.text('Other Description'),
		'remarks'				: fields.text('Remarks Contract', help="Remarks for additional Information of this contract order"),
		'application'			: fields.selection([('knitting',"Knitting"),('weaving',"Weaving")],'Application', readonly=True, states={'draft':[('readonly',False)]}),
		'tpi' 					: fields.char('TPI',size=10,help='Turn per Inch', readonly=True, states={'draft':[('readonly',False)]}),
		'tpm' 					: fields.char('TPM',size=10,help='Turn per Meter', readonly=True, states={'draft':[('readonly',False)]}),
		'packing_type' 			: fields.many2one('packing.type','Packing',help='Packing Type on Negotiation', readonly=True, states={'draft':[('readonly',False)]}),
		'container_size'		: fields.many2one('container.size','Container Size', readonly=True, states={'draft':[('readonly',False)]}),
		'packing_detail'		: fields.text('Packing Details', readonly=True, states={'draft':[('readonly',False)]}),
		'cone_weight'			: fields.float('Cone Weight',required=False, readonly=True, states={'draft':[('readonly',False)]}, digits=(1, 3)),
		'count_number'			: fields.float('Count Number',required=False,help="Yarn Count Number", readonly=True, states={'draft':[('readonly',False)]}),
		'bom_id'				: fields.many2one('mrp.bom','Blend',required=False,help="Yarn Blend Code", readonly=True, states={'draft':[('readonly',False)]}),
		'wax'					: fields.selection([('none','None'),('waxed',"Waxed"),('unwaxed',"Unwaxed")],'Wax',help="Select waxed if the product that will be sold is using wax", readonly=True, states={'draft':[('readonly',False)]}),
		'est_delivery_date'		: fields.date('Estimated Delivery Date', readonly=True, states={'draft':[('readonly',False)]}),
		'sale_type'				: fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True, readonly=True, states={'draft':[('readonly',False)]}),
		# 'production_location'	: fields.related('product_id','property_stock_production',type='many2one',relation='stock.location',string='Production Location',domain="[('usage','=','production')]", store=True),
		'production_location'	: fields.many2one('stock.location','Production Location',domain="[('usage','=','production')]"),
		'default_location_id'	: fields.many2one('stock.location','Default Source Location',domain="[('usage','=','internal')]"),
		'product_uop'			: fields.many2one('product.uom', 'Unit of Picking'),
		'product_uop_qty' 		: fields.float("Quantity UoP", digits_compute=dp.get_precision('Product Unit of Measure')),
		'tracking_id'			: fields.many2one('stock.tracking','Pack'),
		'knock_off'				: fields.boolean('Knock Off'),
		'date_knock_off'		: fields.date('Knock Off Date', readonly=True, select=True, help="Date on which sales order line is knock off."),
		'use_nomenclature'		: fields.boolean("Use 'Ne' in Desc Product?"),
		'order_state'			: fields.selection([('hold','Hold'),('doubtful','Doubtful'),('cancel','Cancel'),('active','Active')],"Order State",required=True),
		'reschedule_date'		: fields.date('Reschedule Date'),
	}

	_defaults = {
	'sale_type': lambda self,cr,uid,context: context.get('sale_type','export'),
	'est_delivery_date': lambda self,cr,uid,context : context.get('est_delivery_date',False),
	'sequence_line' : '/', 
	'state': 'draft',
	'is_less_than_knockoff_qty': lambda *a: False,
	'date_knock_off': False,
	'use_nomenclature':True,
	'order_state': 'active',
	}
	_order="id asc, sequence_line_1 asc"

	def button_knock_off(self, cr, uid, ids, context=None):
		wf_service = netsvc.LocalService("workflow")
		for line in self.browse(cr, uid, ids, context=context):
			self.write(cr, uid, line.id, {'knock_off': True, 'date_knock_off': fields.date.context_today(self, cr, uid, context=context), 'knock_off_qty':line.product_uom_qty_outstanding})
			wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
		return True

	def onchange_delivery_date(self,cr,uid,ids,est_date,max_est_date, order_date,context=None):
		if not context:context={}
		res = {}
		if est_date and max_est_date and order_date:
			est_date = datetime.datetime.strptime(est_date,'%Y-%m-%d')
			max_est_date = datetime.datetime.strptime(max_est_date,'%Y-%m-%d')
			order_date = datetime.datetime.strptime(order_date,'%Y-%m-%d')
			if est_date > max_est_date or est_date <= order_date:
				warning = {
						'title': _('Entry Warning!'),
						'message' : _('Estimated Delivery Date on this Order Lines should be bigger than Order Date abouse, or less than or equal to Estimated Delivery Date on above')}
				value = {'est_delivery_date':False}
				res.update({'warning':warning,'value':value})
		return res

	def onchange_application(self, cr, uid, ids, product_id, application, use_nomenclature, context=None):
		product_id = product_id and self.pool.get('product.product').browse(cr,uid,product_id)
		if product_id:
			code = product_id.default_code or ''
			name = product_id.name or ''
			nomenclature = product_id.nomenclature or ''
			app = ''
			if application:
				app = application=='knitting' and ' for knitting' or ' for weaving'

			#desc = ('[' + code + '] ' + name + app).upper()
			desc = (name + app).upper()
			return {'value':{'name':use_nomenclature and (nomenclature+' '+desc) or desc}}
		return {'value':{'name':''}}

	def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
			uom=False, qty_uos=0, uos=False, name='', partner_id=False,
			lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
		context = context or {}
		product_uom_obj = self.pool.get('product.uom')
		partner_obj = self.pool.get('res.partner')
		product_obj = self.pool.get('product.product')
		warning = {}
		res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
			uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
			lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
		result=res['value']
		result['application']=False
		nomenclature = ''
		if product:
			product_obj = product_obj.browse(cr, uid, product, context=context)
			# additional for Finish Good Information
			if product_obj.internal_type=='Finish':
				result['count_number']=product_obj.count
				# result['cone_weight']
				result['bom_id']=product_obj.blend_id.id
				result['wax']=product_obj.wax
				nomenclature = product_obj.nomenclature
			result['local_desc']=product_obj.local_desc and product_obj.local_desc.upper() or ''
			result['export_desc']=product_obj.export_desc and product_obj.export_desc.upper() or ''
			result['production_location'] = product_obj.property_stock_production and product_obj.property_stock_production.id or False
		# to remove Inventory ID from desc,var index is index of the Invn ID
		name = result.get('name','')
		if name:
			index = name.find(']') > 0 and name.find(']')+1 or 0 
			result['name']=nomenclature and (nomenclature + name[index:]) or name[index:]
		# to remove onchange price from base product_id_change
		if 'price_unit' in result.keys():
			del result['price_unit']

		res.update({'value': result})
		# to delete warning of available quantity
		if 'warning' in res.keys():
			del res['warning']
		
		return res

	def onchange_use_nomenclature(self, cr, uid, ids, use_nomenclature, product_id, name, context=None):
		context = context or {}
		product_obj = self.pool.get('product.product')
		# additional for Finish Good Information
		if use_nomenclature and product_id:
			product = product_obj.browse(cr, uid, product_id, context=context)
			if product.internal_type=='Finish':
				nomenclature = product.nomenclature
				words = name.split(' ')
				new_words = []
				for i in range(0,len(words)):
					if i == 0:
						new_words.append(nomenclature)
					new_words.append(words[i])
				name = ' '.join(new_words)
		elif not use_nomenclature and product_id:
			product = product_obj.browse(cr, uid, product_id, context=context)
			if product.internal_type=='Finish':
				nomenclature = product.nomenclature
				words = name.split(' ')
				to_pop = []
				for i in range(0,len(words)):
					if words[i] == nomenclature:
						to_pop.append(i)
				for t in to_pop:
					words.pop(t)
				name = ' '.join(words)

		return {'value':{'name':name}}

class template_special_condition(osv.osv):
	_name = "template.special.condition"
	_columns = {
		"name" : fields.char('Number', size=128),
		"desc" : fields.text('Special Condition', required=True),
	}

class packing_type(osv.osv):
	_inherit = "packing.type"
	_columns = {
		"name" : fields.char('Name', size=128, required=True),
		"desc" : fields.text('Spesification'),
		"alias" : fields.text('Alias'),
	}

class container_size(osv.osv):
	_inherit = "container.size"
	_columns = {
		"name" : fields.char('Size', size=128, required=True),
		"desc" : fields.text('Description'),
		'teus' : fields.float('TEUS.', help="Container Type Code Bitratex"),
		# "size" : fields.selection([("20'","20'"),("40'","40'"),("40' HC","40' HC"),("LCL","LCL")], string='Size Container', required=True),
		"type" : fields.many2one('container.type','Size'),
		"total_container" : fields.integer('Total', required=True),
	}

	_defaults = {
		# "size" : "40'",
		"total_container" : 1,
	}
