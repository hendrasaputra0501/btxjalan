from openerp.osv import fields,osv

class mr_line_injection(osv.osv_memory):
	_name = "mr.line.injection"

	_columns = {
		"mr_lines" 	: fields.many2many('material.request.line','mr_line_inject_rel',"inject_id","line_id","Material Request Lines"),
		"pr_id"		: fields.many2one('purchase.requisition',"Purchase Requisition",required=True,),
		"inject_po"	: fields.boolean('Inject into existing RFQ(s)'),
		"po_ids"	: fields.many2many('purchase.order','mr_line_po_rel',"inject_id","line_id","RFQ(s)"),
	}
	_defaults = {
		'inject_po':lambda *a:True
	}

	def onchange_pr_id(self,cr,uid,ids,pr_id,inject_po,context=None):
		if not context:
			context={}
		pr_pool = self.pool.get('purchase.requisition')
		po_pool = self.pool.get('purchase.order')
		val={}
		if inject_po:
			if pr_id:
				pr = pr_pool.browse(cr,uid,pr_id)
				rfqs = [po.id for po in pr.purchase_ids if po.state in ('draft','sent')]
				val.update({'po_ids':rfqs or False})
			else:
				val.update({'po_ids':False})
		return {'value':val}

	def onchange_po_ids(self,cr,uid,ids,pr_id,rfqs,inject_po,context=None):
		if not context:
			context={}
		pr_pool = self.pool.get('purchase.requisition')
		po_pool = self.pool.get('purchase.order')
		val={}

		po_ids = rfqs and rfqs[0] and rfqs[0][2] or False
		if inject_po:
			if po_ids and not pr_id:
				pos = po_pool.browse(cr,uid,po_ids)
				pr_id = [po.requisition_id.id for po in pos if po.requisition_id and po.requisition_id.id]
				val.update({'pr_id':pr_id or False})
		return {'value':val}

	def default_get(self, cr, user, fields_list, context=None):
		"""
		Returns default values for fields
		@param fields_list: list of fields, for which default values are required to be read
		@param context: context arguments, like lang, time zone

		@return: Returns a dict that contains default values for fields
		"""
		if not context:
			context = {}
		values = super(mr_line_injection, self).default_get(cr, user, fields_list, context=context)
		mr_line_ids = context.get('active_ids',False)
		mr_line_pool = self.pool.get('material.request.line')
		mr_lines = []
		if mr_line_ids:
			mr_lines = mr_line_ids

		values.update({
			'mr_lines':mr_lines,
		})
		return values

	def inject(self,cr,uid,ids,context=None):
		if not context:
			context={}
		inject = self.browse(cr,uid,ids,context=context)[0]
		fiscal_position = self.pool.get('account.fiscal.position')
		purchase_order_line = self.pool.get('purchase.order.line')
		purchase_order_sca = self.pool.get('purchase.order.sca')
		print "==============",inject.mr_lines
		for mr_line in inject.mr_lines:	
			if not mr_line.requisition_id.bypass_stock:
				product_qty = uom_obj._compute_qty(cr, uid, mr_line.product_uom_id.id, mr_line.product_qty, mr_line.product_id.uom_id.id, round=False)
				if product_qty <= mr_line.current_qty_available:
					continue
			line = {
			'material_req_line_id'	: mr_line.id,
			'location_dest_id'		: mr_line.requisition_id and mr_line.requisition_id.location_dest_id and mr_line.requisition_id.location_dest_id.id or False,
			'product_id'			: mr_line.product_id and mr_line.product_id.id or False,
			'product_qty'			: mr_line.product_qty or 0.0,
			'account_analytic_id'	: mr_line.account_analytic_id and mr_line.account_analytic_id.id or False,
			'price'					: mr_line.price,
			'product_uom_id'		: mr_line.product_uom_id and mr_line.product_uom_id.id or False,
			"part_number"			: mr_line.part_number or False,
			"catalogue_id"			: mr_line.catalogue_id and mr_line.catalogue_id.id or False,
			"machine_number"		: mr_line.machine_number or False,
			"requisition_id"		: inject.pr_id and inject.pr_id.id or False,
			}
			pr_line_id = self.pool.get('purchase.requisition.line').create(cr,uid,line,context=context)
			pr_line =self.pool.get('purchase.requisition.line').browse(cr,uid,pr_line_id)
			if inject.inject_po:
				product = mr_line.product_id
				for po in inject.po_ids:
					supplier = po.partner_id
					seller_price, qty, default_uom_po_id, date_planned = self.pool.get('purchase.requisition')._seller_details(cr, uid, pr_line, supplier, context=context)
					taxes_ids = product.supplier_taxes_id
					taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
					po_line_id =purchase_order_line.create(cr, uid, {
							'order_id': po.id,
							'name': product.partner_ref,
							'product_qty': qty,
							'product_id': product.id,
							'product_uom': default_uom_po_id,
							'price_unit': seller_price,
							'date_planned': date_planned,
							'taxes_id': [(6, 0, taxes)],
							"requisition_line_id": pr_line_id or False,
							"requisition_id":inject.pr_id and inject.pr_id.id,
							"part_number":line.get('part_number',False),
							"catalogue_id":line.get('catalogue_id',False),
							"machine_number":line.get('machine_number', False),
							"pr_lines" : [(6,0,[pr_line_id])]
						}, context=context)
					purchase_order_sca.create(cr, uid, {
							'tobe_purchased': False,
							'requisition_id': inject.pr_id and inject.pr_id.id or False,
							'po_line_id': po_line_id,
							"requisition_line_id": pr_line_id or False,
							"po_id":po.id,
							"partner_id":supplier.id,
							"product_id":product.id,
							"name":product.partner_ref,
							"product_qty":qty,
							"pro_qty": qty,
							"product_uom":default_uom_po_id,
							"price_unit":seller_price,
						}, context=context)
				self.pool.get('material.request.line').write(cr, uid, mr_line.id,{'state':'submit','pr_id':inject.pr_id.id,'pr_line_id':pr_line_id})
		return {'type': 'ir.actions.act_window_close'}