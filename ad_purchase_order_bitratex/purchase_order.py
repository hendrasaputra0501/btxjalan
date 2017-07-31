from openerp.osv import fields,osv
import datetime
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class purchase_schedule(osv.Model):
	_name="purchase.schedule"
	#_rec_name = "delivery_date"
	_columns = {
		"delivery_date"		: fields.date("Scheduled Date",required=True),
		'product_id'		: fields.many2one('product.product',"Product"),
		'quantity'			: fields.float("Quantity"),
		'uom'				: fields.many2one('product.uom',"Unit of Measure",),
		"purchase_id"		: fields.many2one("purchase.order","Purchase Order",required=True,ondelete='cascade'),
	}

	_defaults = {
		'delivery_date':lambda *a:datetime.date.today().strftime('%Y-%m-%d')
	}

class purchase_order(osv.Model):
	_inherit = "purchase.order"
	


	def _get_order(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
			result[line.order_id.id] = True
		return result.keys()

	def _minimum_planned_date(self, cr, uid, ids, field_name, arg, context=None):
		res={}
		purchase_obj=self.browse(cr, uid, ids, context=context)
		for purchase in purchase_obj:
			res[purchase.id] = False
			if purchase.order_line:
				min_date=purchase.order_line[0].date_planned
				for line in purchase.order_line:
					if line.date_planned < min_date:
						min_date=line.date_planned
				res[purchase.id]=min_date
		return res
		
	def _set_minimum_planned_date(self, cr, uid, ids, name, value, arg, context=None):
		if not value: return False
		if type(ids)!=type([]):
			ids=[ids]
		for po in self.browse(cr, uid, ids, context=context):
			if po.order_line:
				cr.execute("""update purchase_order_line set
						date_planned=%s
					where
						order_id=%s and
						(date_planned=%s or date_planned<%s)""", (value,po.id,po.minimum_planned_date,value))
			cr.execute("""update purchase_order set
					minimum_planned_date=%s where id=%s""", (value, po.id))
		return True

	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
			}
			val = val1 = 0.0
			cur = order.pricelist_id.currency_id
			for line in order.order_line:
				val1 += line.price_subtotal
				disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit,line.product_qty,context=context)
				price_after = disc.get('price_after',line.price_unit)
				for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, price_after, line.product_qty, line.product_id, order.partner_id)['taxes']:
					val += c.get('amount', 0.0)
			res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
			res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
			res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
		return res

	_columns = {
		"partner_ref_date"		: fields.date("Supplier Reference Date"),
		'extra_name'			: fields.char("Name Extra Info",size=32),
		"incoming_address_id"	: fields.many2one('res.partner',"Supplier Ship Address",readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Shipment address from supplier"),
		'notify'				: fields.many2one('res.partner', 'Notify', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Notify Partner for current PO."),
		'consignee'				: fields.many2one('res.partner', 'Consignee', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Consignee Partner for current PO."),
		'agent'					: fields.many2one('res.partner', 'Agent', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Consignee Partner for current PO."),
		"goods_type"			: fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('asset','Fixed Asset'),('other','Other'),('packing','Packing Material')],'Goods Type',required=True),
		'purchase_type'			: fields.selection([('import','Import'),('local','Local')],"Purchase Type",required=True),
		'locale_sale_type'		: fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Purchase Type",required=False),
		"carrier_id"			: fields.many2one('stock.transporter',"Planned Transporter"),
		'purchase_schedule_ids'	: fields.one2many('purchase.schedule','purchase_id',"Incoming Schedule"),
		"advance_ids"			: fields.many2many('account.advance.payment','purchase_order_advance_rel','adv_id','order_id',"Advance Payment(s)"),
		"advance_percentage"	: fields.float("Advance Percentage"),
		'use_bc_on_mrr' 		: fields.boolean("Use BC for MRR?"),
		'knock_off_picking' 	: fields.boolean("Incoming Shipment Knock Off?", readonly=True),
		'original_order_id' 	: fields.many2one('purchase.order','Original PO'),
		'prev_order_id' 		: fields.many2one('purchase.order','Previous PO'),
		'tolerance_percentage'	: fields.float("Min. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)"),
		'tolerance_percentage_max'	: fields.float("Max. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)"),
		'minimum_planned_date'	:fields.function(_minimum_planned_date, fnct_inv=_set_minimum_planned_date, string='Expected Date', type='date', select=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
									store = {
										'purchase.order.line': (_get_order, ['date_planned'], 10),
									}),
		'amount_untaxed'		: fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
									store={
										'purchase.order.line': (_get_order, None, 10),
									}, multi="sums", help="The amount without tax", track_visibility='always'),
		'amount_tax'			: fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
									store={
										'purchase.order.line': (_get_order, None, 10),
									}, multi="sums", help="The tax amount"),
		'amount_total'			: fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
									store={
										'purchase.order.line': (_get_order, None, 10),
									}, multi="sums",help="The total amount"),
		"template_special_condition" : fields.many2one('template.special.condition','Template Special Condition'),
		'invoice_method': fields.selection([('manual','Based on Purchase Order lines'),('order','Based on generated draft invoice'),('picking','Based on incoming shipments')], 'Invoicing Control', required=True,
						readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]},
						help="Based on Purchase Order lines: place individual lines in 'Invoice Control > Based on P.O. lines' from where you can selectively create an invoice.\n" \
						"Based on generated invoice: create a draft invoice you can validate later.\n" \
						"Bases on incoming shipments: let you create an invoice when receptions are validated."),
		'remit_to' : fields.many2one('res.bank', 'Remit To',help=''),
		'credit_to' : fields.many2one('res.bank', 'Credit To',help=''),
		'bank_account_dest' : fields.many2one('res.partner.bank', 'Bank Account Payment To'),
		"payment_date"		: fields.date("Payment Date"),
		"remark_po"			: fields.text("Remark"),
		
		'pending_itemdesc'	:	fields.char('Description',size=50),
		'divy_by'	:	fields.char('Divy By',size=10),
		'shipment_etd_dt'	: fields.date('Shipment ETD Date'),
		'last_shipment_date' : fields.date('Last Shipment Date'),
		'arrival_harbour' : fields.date('Arrival Harbour'),
		'arrival_factory' : fields.date('Arrival Factory'),
		'shipment_remarks' : fields.char('Remarks',size=50),
		'actual_shipment_date': fields.date('Actual Shipment Date'),
		'transit_shipment_date': fields.date('Transit Shipment Date'),
		# 'eta_date' : fields.date('ETA Date'),
		'document_ref' : fields.char('Document Reference'),
		'department'		: fields.many2one('hr.department', 'Department'),
		'po_suffix_number': fields.char("Suffix PO Number"),
		}

	def _get_term(self,cr,uid,context=None):
		if not context:context={}
		term_ids = self.pool.get('account.payment.term').search(cr,uid,[('active','=',True)],context=context)
		term_id = False
		if term_ids:
			try:
				term_id = term_ids[0]
			except:
				term_id = term_ids
		return term_id
	def _get_invoice_method(self,cr,uid,context=None):
		print "-----------I call it here------------------"
		return 'picking'
		
	_defaults = {
		# 'goods_type':'raw',
		'purchase_type':'import',
		'invoice_method': _get_invoice_method,
		'payment_term_id': _get_term,
	}

	def _prepare_order_picking(self, cr, uid, order, context=None):
		if not context:context={}
		res = super(purchase_order,self)._prepare_order_picking(cr,uid,order,context=context)
		if order.incoming_address_id and order.incoming_address_id.id:
			res.update({
				'partner_id':order.incoming_address_id.id or order.partner_id.id or False,
				})
		res.update({
			'purchase_type' : order.purchase_type or 'import',
			'goods_type': order.goods_type,
			})
		return res
	
	def onchange_template_special_condition(self, cr, uid, ids, note, temp, context=None):
		temp_pooler = self.pool.get('template.special.condition')
		temp_id = temp and temp_pooler.browse(cr,uid,temp,context) or False
		if temp_id:
			return {'value':{'notes':(note and note or '') + '\n\n' + temp_id.desc}}
		else:
			return {'value':{'notes': (note and note or '')}}

	def copy(self, cr, uid, id, default=None, context=None):
		if not context:
			context = {}
		if default is None:
			default = {}
		default.update({
					'knock_off_picking':False,
				})
		if not default.get('original_order_id',False):
			default.update({'original_order_id':False})
		if not default.get('prev_order_id',False):
			default.update({'prev_order_id':False})
		res =  super(purchase_order, self).copy(cr, uid, id, default, context)
		return res

	def knock_off(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		self.write(cr, uid, ids, {'shipped':1,'knock_off_picking':1,'state':'approved'}, context=context)
		pol_ids = self.pool.get('purchase.order.line').search(cr, uid, [('order_id','in',ids)])
		self.pool.get('purchase.order.line').button_knock_off(cr, uid, pol_ids)
		
		wf_service = netsvc.LocalService("workflow")
		for id in ids:
			wf_service.trg_write(uid, 'purchase.order', id, cr)
		return True

	def knock_off_revise(self, cr, uid, ids, context=None):
		if context is None:
			context = {} 
		new_order_ids = []
		for order in self.browse(cr, uid, ids, context=context):
			original_order = order.original_order_id and order.original_order_id or order
			childs = self.search(cr, uid, [('original_order_id','=',original_order.id)])
			
			n = len(childs) + 1
			defaults={
				'original_order_id':original_order.id,
				'prev_order_id':original_order.id==order.id and False or order.id,
				'order_line':[],
			}
			new_id = self.copy(cr, uid, order.id, defaults, context=context)
			update_val = {
				'name' : original_order and original_order.name + ' Rev.' + str(n) or '/',
			}
			self.write(cr, uid, new_id, update_val, context=context)
			for line in order.order_line:
				qty_received = 0.0
				for move in line.move_ids:
					if move.state=='done':
						qty_received += self.pool.get('product.uom')._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, line.product_uom, context=context)
				qty_outstanding = line.product_qty - qty_received
				line_defaults = {
					'order_id':new_id,
					'product_qty' : qty_outstanding,
				}
				self.pool.get('purchase.order.line').copy(cr, uid, line.id, line_defaults, context=context)
			new_order_ids.append(new_id)
		self.write(cr, uid, ids, {'shipped':1,'knock_off_picking':1,'state':'approved'}, context=context)
		pol_ids = self.pool.get('purchase.order.line').search(cr, uid, [('order_id','in',ids)])
		self.pool.get('purchase.order.line').button_knock_off(cr, uid, pol_ids)

		wf_service = netsvc.LocalService("workflow")
		for id in ids:
			wf_service.trg_write(uid, 'purchase.order', id, cr)
		
		data_pool = self.pool.get('ir.model.data')
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'purchase', "purchase_draft")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,new_order_ids))+"])]"
		return action
	
	def create(self, cr, uid, vals, context=None):
		company_pooler = self.pool.get('res.company')
		company_code = ''
		goods_code = ''
		company_id = False
		month = ''
		if vals.get('name','/')=='/':
			if vals.get('company_id',False):
				company_id = company_pooler.browse(cr, uid, vals.get('company_id',False))
			if company_id:
				company_code=company_id.prefix_sequence_code
			goods_type = vals.get('goods_type',False)
			if goods_type == 'raw':
				goods_code = 'R'
			elif goods_type == 'stores':
				goods_code = 'S'
			elif goods_type == 'packing':
				goods_code = 'P'
			else:
				goods_code = 'O'

			date = vals.get('date_order',False) or time.strftime(DEFAULT_SERVER_DATE_FORMAT)
			date2 = vals.get('date_order',False) and datetime.datetime.strptime(vals['date_order'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT) or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
			month = datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).strftime('%b').lower()

			po_type = vals.get('purchase_type',False)
			if goods_type=='raw':
				if po_type=='import':
					vals['name'] = ('O'+ company_code + 'I-' + goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+po_type+'.'+month, context={'date':date2}) or '/'))
				elif po_type=='local':
					vals['name'] = ('O'+ company_code +'L-'+ goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+po_type+'.'+month, context={'date':date2}) or '/'))
			else:
				vals['name'] = '/'
		res=super(purchase_order, self).create(cr, uid, vals, context=context)
		return res

	def wkf_confirm_order(self, cr, uid, ids, context=None):
		company_pooler = self.pool.get('res.company')
		company_code = ''
		goods_code = ''
		company_id = False
		month = False
		name='/'
		for vals in self.browse(cr,uid,ids,context=context):
			if vals.name=='/' or vals.name[:1]=='/' or vals.name[:2]=='PO':
				if vals.company_id and vals.company_id.id:
					company_id = vals.company_id
				if company_id:
					company_code=company_id.prefix_sequence_code
				goods_type = vals.goods_type
				if goods_type == 'raw':
					goods_code = 'R'
				elif goods_type == 'stores':
					goods_code = 'S'
				elif goods_type == 'packing':
					goods_code = 'P'
				else:
					goods_code = 'O'

				date = vals.date_order
				date2 = datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
				month = datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).strftime('%b').lower()

				po_type = vals.purchase_type
				if goods_type=='raw':
					if po_type=='import':
						# print "disini1", 'purchase.order.'+po_type+'.'+month
						name = ('O'+ company_code + 'I-' + goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+po_type+'.'+month, context={'date':date2}) or '/'))
					elif po_type=='local':
						name = ('O'+ company_code +'L-'+ goods_code + (self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+po_type+'.'+month, context={'date':date2}) or '/'))
				elif goods_type == 'packing':
					if po_type=='import':
						name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+goods_type+po_type+'.'+month, context={'date':date2}) or '/'
					else:
						name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+goods_type+'.'+po_type+'.'+month, context={'date':date2}) or '/'
				else:
					name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.'+goods_type+'.'+po_type+'.'+month, context={'date':date2}) or '/'
				vals.write({'name':name})
		res=super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
		return res

	def is_advance_paid(self,cr,uid,ids,context=None):
		if not context:context={}
		#check whether the advance has been paid or not
		for purchase in self.browse(cr,uid,ids,context):
			if purchase.payment_method in ('tt','cash'):
				total = 0.0
				for adv in purchase.advance_ids:
					if adv.state in ('posted',):
						total+=adv.total_amount or 0.0
				if total >= (purchase.advance_percentage/100.0*purchase.amount_total):
					return True
		return False

	def onchange_purchase_type(self,cr,uid,ids,purchase_type,context=None):
		if not context:context={}
		value={}
		if purchase_type:
			if purchase_type == 'import':
				value.update({'locale_sale_type':False})
		return {'value':value}

	def action_done(self, cr, uid, ids, context=None):
		todo = []
		for po in self.browse(cr, uid, ids, context=context):
			for line in po.order_line:
				todo.append(line.id)

		self.pool.get('purchase.order.line').action_done(cr, uid, todo, context)
		for id in ids:
			self.write(cr, uid, [id], {'state' : 'done'})
		return True

class purchase_order_line(osv.Model):
	def _get_ids_from_purchase_order(self, cr, uid, ids, context=None):
		res = []
		for order in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
			for line in order.order_line:
				if line.id not in res:
					res.append(line.id)

		return res
	
	def get_sequence(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res={}
		no=1
		for line in self.browse(cr,uid,sorted(ids)):
			line_ids = self.search(cr,uid,[('order_id','=',line.order_id.id),('sequence','!=',0)])
			curr_total_line = len(line_ids)
			n = 0
			for line_id in sorted(line_ids):
				n += 1
				res[line_id] = n
			
			if line.id not in res.keys() and not line.sequence:
				res[line.id]=int(curr_total_line+1)
		return res

	_inherit = "purchase.order.line"

	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		res = {}
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		for line in self.browse(cr, uid, ids, context=context):
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit,line.product_qty,context=context)
			price_after = disc.get('price_after',line.price_unit)
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price_after, line.product_qty, line.product_id, line.order_id.partner_id)
			order_id = line.order_id or line.old_order_id
			cur = order_id.pricelist_id.currency_id
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
		return res

	def _get_stock_moves_related(self, cr, uid, ids, context=None):
		res=[]

		for move in self.pool.get('stock.move').browse(cr, uid, ids):
			if move.purchase_line_id and move.purchase_line_id.id not in res:
				res.append(move.purchase_line_id.id)
		
		return res

	def _get_qty_shipped(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		uom_pool = self.pool.get('product.uom')
		for line in self.browse(cr,uid,ids,context):
			res[line.id] = {
				'product_uom_qty_received' : 0.0,
				'product_uom_qty_outstanding' : 0.0,
			}
			if line.state in ('draft','cancel'):
				continue
			res[line.id]['product_uom_qty_outstanding'] = line.product_qty
			if line.move_ids:
				for move in line.move_ids:	
					if move.state == 'done':
						if move.product_uom.category_id!=line.product_uom.category_id:
							res[line.id]['product_uom_qty_received'] += move.product_qty
						else:
							res[line.id]['product_uom_qty_received'] += uom_pool._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, line.product_uom, context=context)
				res[line.id]['product_uom_qty_outstanding'] = line.product_qty - res[line.id]['product_uom_qty_received']
			res[line.id]['product_uom_qty_outstanding'] = res[line.id]['product_uom_qty_outstanding']>0.0 and res[line.id]['product_uom_qty_outstanding'] or 0.0
		return res

	_columns = {
		'sequence' : fields.function(get_sequence, type='integer', string='Seq', method=True, 
			store={
				'purchase.order':(_get_ids_from_purchase_order,['order_line'],10),
				'purchase.order.line':(lambda self,cr,uid,ids,context={}:ids,['order_id'],10),
			}),
		"discount_ids" : fields.many2many('price.discount','price_discount_po_line_rel','po_line_id','disc_id',"Discounts"),
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
		"header_for_print"	: fields.text("Header"),
		"other_cost_type"	: fields.selection([('freight','Freight')],'Other Cost Type'),
		"remark"			: fields.text("Remark"),
		'knock_off'			: fields.boolean('Knock Off'),
		'date_knock_off'	: fields.date('Knock Off Date', readonly=True, select=True, help="Date on which purchase order line is knock off."),
		'product_uom_qty_received' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Shipped.', 
									store={
										'purchase.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"
									),
		'product_uom_qty_outstanding' : fields.function(_get_qty_shipped,digits_compute=dp.get_precision('Product Unit of Measure'), method=True, type='float', string='Qty Outstanding', 
									store={
										'purchase.order.line':(lambda self,cr,uid,ids,context={}:ids,['move_ids'],10),
										'stock.move':(_get_stock_moves_related,['state'],10),
									}, multi="all_shipped_qty"
									),
	}

	_defaults = {
		'sequence' : 0,
		'knock_off': False,
	}

	_order = 'id asc'

	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
			partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
			name=False, price_unit=False, context=None):
		"""
		Here we can inherit anything related to onchange product_id
		"""
		res = super(purchase_order_line,self).onchange_product_id(cr,uid,ids,pricelist_id,product_id,qty,uom_id,partner_id,
			date_order=date_order,fiscal_position_id=fiscal_position_id,date_planned=date_planned,name=name,price_unit=price_unit,context=context)
		if product_id:
			prod = self.pool.get('product.product').browse(cr,uid,product_id)
			name = prod.name
			if prod.description_purchase:
				name += '\n' + prod.description_purchase
			if prod.export_desc or prod.local_desc:
				name=prod.export_desc or prod.local_desc or prod.name
			
			res['value']['name']=name
		return res

	def get_line_price_after_disc(self,cr,uid,line,context=None):
		disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit,line.product_qty,context=context)
		price_after = disc.get('price_after',line.price_unit)
		return price_after

	def action_done(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state': 'done'}, context=context)
		return True

	def button_knock_off(self, cr, uid, ids, context=None):
		if context is None:
			context={}
		# wf_service = netsvc.LocalService("workflow")
		for line in self.browse(cr, uid, ids, context=context):
			self.write(cr, uid, line.id, {
				'knock_off': True, 
				'state' : 'done',
				'date_knock_off': context.get('date_knock_off',False) and context.get('date_knock_off',False) or fields.date.context_today(self, cr, uid, context=context), })
			# wf_service.trg_write(uid, 'purchase.order', line.order_id.id, cr)
		return True