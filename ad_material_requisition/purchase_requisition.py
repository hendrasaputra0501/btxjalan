import time
import netsvc
from openerp.tools.translate import _
from osv import fields,osv
from random import random,randint

class purchase_requisition(osv.osv):
	_inherit = "purchase.requisition"
	
	def _total_price_get(self, cr, uid, ids, name, arg=None, context=None):
		res = {}
		for sca in self.browse(cr, uid, ids, context=context):
			res[sca.id] = 0
			
			for line in sca.sca_ids:
				if line.tobe_purchased==True:
					res[sca.id] += (line.po_line_id.price_unit and line.pro_qty*line.po_line_id.price_unit) or 0.0
		return res

	_columns = {
			# 'int_move_id'		: fields.many2one('stock.picking', 'Internal Move Number', readonly=True),
			"mr_lines"			: fields.one2many("material.request.line","pr_id","Material Request Lines"),
			"goods_type"		: fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('asset','Fixed Asset'),('other','Other'),('packing','Packing Material')],'Goods Type',required=True),
			'origin'			: fields.char('Origin', size=512),
			'assigned_employee'	: fields.many2one('hr.employee',"Assigned Buyer"), 
			'category_id'		: fields.many2one('product.category',"Product Category",required=False),
			'sca_ids'			: fields.one2many('purchase.order.sca','requisition_id',"SCA Lines"),
			'rfq_number'		: fields.char('RFQ Number',size=64),
			'counter_rfq'		: fields.integer('Counter RFQ'),
			'total'				: fields.function(_total_price_get, method=True, string='Total', type='float' ),
			'state'				: fields.selection([('draft','New'),('in_progress','Sent to Suppliers'),('price_received','Price Received'),('wait_manager',"Waiting for Manager"),\
				('wait_budget_keeper',"Budget Keeper"),('wait_finance',"Finance"),('wait_cfo_approval',"Waiting for CFO"),('wait_ceo_approval',"Waiting for CEO"),
				('cancel','Cancelled'),('done_pr','PR Done'),('done','Purchase Done')],'State', track_visibility='onchange', required=True),
			'sca_date'			: fields.date('Sca Date'),
			# 'material_req_id'	: fields.many2one('material.request', 'Material Requisition'),
			# 'is_mr'				: fields.boolean('is merge MR'),
			# 'mr_ids'			: fields.one2many('material.request','pr_id','Material Req'),	
			#'purchase_history_ids': fields.function('purchase.history_ids',"")
				}
	_defaults={
			   'counter_rfq':0,
			   'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'pr_skc'),
			   'goods_type' : lambda *a : 'stores'
			   }
		
	def print_sca(self,cr,uid,ids,context=None):
		if not context:context={}
		datas = {
			'ids': ids,
			'model':'purchase.requisition',
			}
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'sca.analysis.xls',
			'report_type': 'webkit',
			'datas': datas,
			} 
	def done(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'done'}, context=context)
	
	def done_pr(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'done_pr'}, context=context)
	
	def in_progress(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'in_progress'}, context=context)

	def tender_in_progress(self, cr, uid, ids, context=None):
		if not context:context={}
		wf_service = netsvc.LocalService("workflow")
		for pr in self.browse(cr,uid,ids,context=context):
			for po in pr.purchase_ids:
				wf_service.trg_validate(uid, 'purchase.order', po.id , 'send_rfq', cr)

		return self.write(cr, uid, ids, {'state':'in_progress'} ,context=context)	
	
	def price_received(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'price_received'}, context=context)
	
	def wait_manager(self,cr,uid,ids,context=None):
		
		return self.write(cr, uid, ids, {'state':'wait_manager'}, context=context)

	def wait_budget_keeper(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'wait_budget_keeper'}, context=context)

	def wait_finance(self,cr,uid,ids,context=None):
		
		return self.write(cr, uid, ids, {'state':'wait_finance'}, context=context)

	def wait_cfo_approval(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'wait_cfo_approval'}, context=context)

	def wait_ceo_approval(self,cr,uid,ids,context=None):
		return self.write(cr, uid, ids, {'state':'wait_ceo_approval'}, context=context)


	def tender_done(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
	
	def check_supplier_send(self,cr,uid,ids,context=None):
		stat = False
		for data in self.browse(cr,uid,ids):
			if data.purchase_ids: stat=True
		return stat
	
	def check_price_receive(self,cr,uid,ids,context=None):
		stat = True
		for data in self.browse(cr,uid,ids):
			for line in data.purchase_ids:
				if line.amount_total==0:
					stat=False
					break
		return stat
	

	def update_rfq(self,cr,uid,ids,context=None):
		if not context: context={}
		po_line_pool = self.pool.get('purchase.order.line')
		for req in self.browse(cr,uid,ids,context=context):
			line_ids = [dt.product_id.id for dt in req.line_ids]
			total = {}
			total2 = {}
			for sca in req.line_ids:
				total[sca.product_id.id]=0
				total2[sca.product_id.id]=sca.product_qty
			for loop in req.sca_ids:
				total[loop.product_id.id]+= loop.tobe_purchased and loop.pro_qty or 0
			
			#for sca in req.line_ids:
			#	if total[sca.product_id.id]>total2[sca.product_id.id]:
			#		raise osv.except_osv(_('Warning!'), _('You can\'t Update RFQ , because total of product different with Qty Purchase Order in Line for Item %s.'%sca.product_id.name))

			if req.purchase_ids and req.sca_ids:
				rfq_ids = [purchase.id for purchase in req.purchase_ids if purchase.state in ('draft','confirmed','sent')]
				po_ids_other_purchased = [sc.po_id.id for sc in req.sca_ids if sc.tobe_purchased]
				
				for sca in req.sca_ids:
					po_line_pool.write(cr,uid,sca.po_line_id.id,{'product_qty':sca.pro_qty,'price_unit':sca.price_unit})
					if sca.tobe_purchased:
						
						self.pool.get('purchase.order').write(cr,uid,sca.po_line_id.order_id.id,{'tobe_purchased':True})
#					 else:
#						 self.pool.get('purchase.order').write(cr,uid,sca.po_line_id.order_id.id,{'tobe_purchased':False})
					# print "---------tt---------",po_ids_other_purchased,sca.po_id.id,rfq_ids,sca.tobe_purchased
					if sca.po_id.id in rfq_ids and not sca.tobe_purchased:
						# print "===++===",sca.po_line_id.id,sca.po_id.id
						ix=self.pool.get('purchase.order.line').write(cr,uid,sca.po_line_id.id,{'old_order_id':sca.po_id.id,'order_id':False})
		return True

purchase_requisition()

class purchase_requisition_line(osv.osv):
	_inherit = "purchase.requisition.line"

	def _get_history(self,cr,uid,ids,field_name,arg,context=None):
		if not context:context={}
		res={}
		prod = {}
		for req_line in self.browse(cr,uid,ids,context=context):
			if req_line.product_id and req_line.product_id.id:
				print "-----------"
				prod[req_line.product_id.id]={
						'max_price':req_line.product_id.max_price or 0.0,
						'max_order_id':req_line.product_id.max_order_id and req_line.product_id.max_order_id.id or False,
						'max_partner_id':req_line.product_id.max_partner_id and req_line.product_id.max_partner_id.id or False,
						'max_date_order':req_line.product_id.max_date_order or False,
						'last_price':req_line.product_id.last_price or 0.0 ,
						'last_order_id':req_line.product_id.last_order_id and req_line.product_id.last_order_id.id or False,
						'last_partner_id':req_line.product_id.last_partner_id and req_line.product_id.last_partner_id.id or False ,
						'last_date_order':req_line.product_id.last_date_order or False ,
						'min_price':req_line.product_id.min_price or 0.0 ,
						'min_order_id':req_line.product_id.min_order_id and req_line.product_id.min_order_id.id or False ,
						'min_partner_id':req_line.product_id.min_partner_id and req_line.product_id.min_partner_id.id or False ,
						'min_date_order':req_line.product_id.min_date_order or False ,
						}

		for line in ids:
			res[line]={
				'max_price':0.0,
				'max_order_id':False,
				'max_partner_id':False,
				'max_date_order':False,
				'last_price':0.0,
				'last_order_id':False,
				'last_partner_id':False,
				'last_date_order':False,
				'min_price':0.0,
				'min_order_id':False,
				'min_partner_id':False,
				'min_date_order':False,
			}
		
		for req_linex in self.browse(cr,uid,ids,context=context):
			res[req_line.id]=req_linex.product_id and req_linex.product_id.id and prod.get(req_linex.product_id.id,res[req_linex.id]) or res[req_linex.id]
		return res
		
	_columns = {
			'material_req_line_id': fields.many2one('material.request.line', 'MR Line'),
			# 'po_ids': fields.many2one('purchase.order', 'PO line'),
			'account_analytic_id':fields.many2one('account.analytic.account',"Analytic Account"),
			'location_dest_id'	: fields.many2one('stock.location',"Site ID",required=False),
			"last_price" 		: fields.function(_get_history,type="float",multi='fetch_info',string="Latest Purchase Price",),
			"last_order_id"		: fields.function(_get_history,type="many2one",relation="purchase.order",multi='fetch_info',string="Latest PO",),
			"last_partner_id"	: fields.function(_get_history,type="many2one",relation="res.partner",multi='fetch_info',string="Latest Vendor",),
			"last_date_order"	: fields.function(_get_history,type="date",multi='fetch_info',string="Latest Purchase Date",),
			"min_price" 		: fields.function(_get_history,type="float",multi='fetch_info',string="Min. Purchase Price",),
			"min_order_id"		: fields.function(_get_history,type="many2one",relation="purchase.order",multi='fetch_info',string="Min. PO",),
			"min_partner_id"	: fields.function(_get_history,type="many2one",relation="res.partner",multi='fetch_info',string="Min. Vendor",),
			"min_date_order"	: fields.function(_get_history,type="date",multi='fetch_info',string="Min. Purchase Date",),
			"max_price" 		: fields.function(_get_history,type="float",multi='fetch_info',string="Max. Purchase Price",),
			"max_order_id"		: fields.function(_get_history,type="many2one",relation="purchase.order",multi='fetch_info',string="Max. PO",),
			"max_partner_id"	: fields.function(_get_history,type="many2one",relation="res.partner",multi='fetch_info',string="Max. Vendor",),
			"max_date_order"	: fields.function(_get_history,type="date",multi='fetch_info',string="Max. Purchase Date",),
			'machine_number'	: fields.char('Machine Number', size=200, required=False),	
			'part_number'		: fields.char(string='Part Number',size=300),
			'catalogue_id'		: fields.many2one('product.catalogue', 'Catalogue'),
				}
	

	def onchange_product_id(self,cr,uid,ids,product_id,context=None):
		if not context:context={}
		vals = {}
		if product_id:
			try:
				product = self.pool.get('product.product').browse(cr,uid,product_id,context=context)[0]
			except:
				product = self.pool.get('product.product').browse(cr,uid,product_id,context=context) 
			vals.update({
				'max_price':product.max_price or 0.0,
				'max_order_id':product.max_order_id and product.max_order_id.id or False,
				'max_partner_id':product.max_partner_id and product.max_partner_id.id or False,
				'max_date_order':product.max_date_order or False,
				'last_price':product.last_price or 0.0 ,
				'last_order_id':product.last_order_id and product.last_order_id.id or False,
				'last_partner_id':product.last_partner_id and product.last_partner_id.id or False ,
				'last_date_order':product.last_date_order or False ,
				'min_price':product.min_price or 0.0 ,
				'min_order_id':product.min_order_id and product.min_order_id.id or False ,
				'min_partner_id':product.min_partner_id and product.min_partner_id.id or False ,
				'min_date_order':product.min_date_order or False ,
				})
		return {'value':vals}
	def write(self,cr,uid,ids,vals,context=None):
		if not context:
			context={}
		res =super(purchase_requisition_line,self).write(cr,uid,ids,vals,context)
		return res
purchase_requisition_line()



class purchase_requisition_wizard_assign(osv.osv_memory):
	_name = 'purchase.requisition.wizard.assign'
	_description = 'Wizard Create RFQ'
	_columns = {
		'partner_ids':fields.many2many('res.partner', 'purchase_req_partner_wiz_rel', 'pr_wiz_id','partner_id', 'Supplier', domain=[('supplier','=',True)]),
		'pr_ids':fields.many2many('purchase.requisition', 'purchase_req_wiz_rel', 'pr_wiz_id','pr_id', 'Purchase Requisition', domain=[('state','not in',('done','cancel'))]),
	}
	_defaults = {
		
	}

	def default_get(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(purchase_requisition_wizard_assign, self).default_get(cr, uid, fields_list, context=context)
		record_ids = context and context.get('active_ids', False) or False
		res.update({'pr_ids': record_ids})
		return res

	def create_rfqs(self,cr,uid,ids,context=None):
		"""
		Create New RFQ for Supplier
		# """
		purchase_order_line = self.pool.get('purchase.order.line')
		purchase_order_sca = self.pool.get('purchase.order.sca')
		res_partner = self.pool.get('res.partner')
		purchase_order = self.pool.get('purchase.order')
		fiscal_position = self.pool.get('account.fiscal.position')
		
		for wiz in self.browse(cr,uid,ids,context=context):
			i = 1
			for partner in wiz.partner_ids:
				supplier_pricelist = partner.property_product_pricelist_purchase or False
				supplier = partner
				res = {}
				### group  pr by location ID ###
				for requisition in wiz.pr_ids:
					# if partner.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
					#	 raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
					location_id = requisition.warehouse_id.lot_input_id.id
					counter = len(str(requisition.counter_rfq + i)) == 1 and '00%s'%str(requisition.counter_rfq +i) or \
					len(str(requisition.counter_rfq+i)) == 2 and '0%s'%len(str(requisition.counter_rfq+i)) or \
					len(str(requisition.counter_rfq+i)) >= 3 and '%s'%len(str(requisition.counter_rfq+i))
					name_rfq = 'RFQ/%s/%s'%(requisition.name, counter)
					self.pool.get('purchase.requisition').write(cr,uid,requisition.id,{'counter_rfq': requisition.counter_rfq + i})
					i+=1
					
					name_po = '/Draft-%s'% randint(1,10000)
					
					purchase_id = purchase_order.create(cr, uid, {
								'origin': requisition.name,
								'partner_id': supplier.id,
								'pricelist_id': supplier_pricelist.id,
								'location_id': location_id,
								'company_id': requisition.company_id.id,
								'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
								'requisition_id':requisition.id,
								'notes':requisition.description,
								'warehouse_id':requisition.warehouse_id.id ,
								'name2': name_rfq,
								'name': name_po,
					})
					res[requisition.id] = purchase_id
					for line in requisition.line_ids:
						product = line.product_id
						seller_price, qty, default_uom_po_id, date_planned = self.pool.get('purchase.requisition')._seller_details(cr, uid, line, supplier, context=context)
						taxes_ids = product.supplier_taxes_id
						taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
						po_line_id =purchase_order_line.create(cr, uid, {
							'order_id': purchase_id,
							'name': product.partner_ref,
							'product_qty': qty,
							'product_id': product.id,
							'product_uom': default_uom_po_id,
							'price_unit': seller_price,
							'date_planned': date_planned,
							'taxes_id': [(6, 0, taxes)],
							"requisition_line_id":line and line.id or False,
							"requisition_id":requisition.id,
							"part_number":line.part_number or False,
							"catalogue_id":line.catalogue_id and line.catalogue_id.id or False,
							"machine_number":line.machine_number or False,
						}, context=context)
						purchase_order_sca.create(cr, uid, {
							'tobe_purchased': False,
							'requisition_id': requisition.id,
							'po_line_id': po_line_id,
							"requisition_line_id":line and line.id or False,
							"po_id":purchase_id,
							"partner_id":supplier.id,
							"product_id":product.id,
							"name":product.partner_ref,
							"product_qty":qty,
							"pro_qty": qty,
							"product_uom":default_uom_po_id,
							"price_unit":seller_price,
						}, context=context)

		return {'type': 'ir.actions.act_window_close'}

purchase_requisition_wizard_assign()



class purchase_order_sca(osv.osv):
	_name = "purchase.order.sca"

	def _get_description(self, cr, uid, ids, field_names, args, context=None):
		if context is None:
			context={}
		res = {}
		for sca in self.browse(cr, uid, ids, context=context):
			
			res[sca.id] = {
				'product_id': sca.po_line_id and sca.po_line_id.product_id.id or False,
				'product_qty': sca.po_line_id and sca.po_line_id.product_qty or 0.0,
				'product_uom': sca.po_line_id and sca.po_line_id.product_uom.id or False,
				'price_unit':sca.po_line_id and sca.po_line_id.price_unit or 0.0,
			}
		return res
	_columns = {
		"tobe_purchased"		: fields.boolean('To be Purchased?'),
		"requisition_id"		: fields.many2one('purchase.requisition',"Requisition ID"),
		"po_line_id"			: fields.many2one('purchase.order.line',"RFQ Line"),
		"requisition_line_id"	: fields.many2one("purchase.requisition.line","Req. Line" ),
		"po_id"					: fields.many2one("purchase.order","RFQ Number"),
		"partner_id"			: fields.many2one("res.partner","Supplier"),
		"product_id"			: fields.many2one("product.product","Product"),
		"name"					: fields.char("Description",size=128),
		"price_subtotal"		: fields.float("Price Subtotal"),
		"product_id"			: fields.related("po_line_id","product_id",type="many2one",relation="product.product", string="Product"),
		"product_qty"			: fields.related("po_line_id","product_qty",type="float", string="Qty"),
		"product_uom"			: fields.related("po_line_id","product_uom",type="many2one",relation="product.uom", string="Unit"),
		"price_unit"			: fields.related("po_line_id","price_unit",type="float", string="Price Unit"),
		# "price_unit"			: fields.float('Price Unit',required=True),
		#"price_unit"		 : fields.function(_get_description,type="float", string="Price Unit",multi="get_description"),
		#"product_qty"	   : fields.float("Qty"),
		#"product_uom"	   : fields.many2one("product.uom","Unit"),
		#"price_unit"		: fields.float("Price Unit"),
		"pro_qty"				: fields.float('MR QTY'),
		# "product_id"			: fields.function(_get_description,type="many2one",relation="product.product", string="Product",multi="get_description"),
		# "product_qty"			: fields.function(_get_description,type="float", string="Qty",multi="get_description"),
		# "product_uom"			: fields.function(_get_description,type="many2one",relation="product.uom", string="Unit",multi="get_description"),
	}
	_order = "requisition_line_id asc, partner_id asc"

	def onchange_price_qty(self,cr,uid,ids,price_unit,pro_qty,context=None):
		if not context:
			context={}
		val = {}
		if price_unit and pro_qty:
			val.update({'price_subtotal':price_unit*pro_qty})
		return {'value':val}

	def onchange_tobe_purchased(self,cr,uid,ids,tobe_purchased,po_line_id,po_id,context=None):
		if not context:context={}
		purchase_pool = self.pool.get('purchase.order')
		sca = self.browse(cr,uid,ids[0],context=context)
		val = {}
		if sca.po_id.state not in ('draft','confirmed','sent'):
			raise osv.except_osv(_('Warning!'), _('You can\'t change this value, because the RFQ have been converted to Purchase Order.'))
			val.update=({'tobe_purchased':sca.tobe_purchased,})			
		else:
			if not tobe_purchased:
				self.write(cr,uid,ids,{'tobe_purchased':False})
				ix=self.pool.get('purchase.order.line').write(cr,uid,sca.po_line_id.id,{'old_order_id':sca.po_id.id,'order_id':False})
			else:
				self.write(cr,uid,ids,{'tobe_purchased':True})
				ix=self.pool.get('purchase.order.line').write(cr,uid,sca.po_line_id.id,{'old_order_id':False,'order_id':sca.po_id.id,'price_unit':True})
		return {'value':val}

purchase_order_sca()
