from openerp.osv import osv,fields
import datetime

class material_request_group(osv.osv_memory):
	_name="material.request.group"
	_columns = {
		'responsible_id'		: fields.many2one('res.users','Responsible User',required=True),
		'assigned_buyer'		: fields.many2one('hr.employee','Assigned Buyer',required=True),
		'requisition_deadline'	: fields.datetime('Requisition Deadline'),
		'requisition_date'		: fields.datetime("Requisition Date"),
		'mr_lines'				: fields.many2many('material.request.line','mr_line_group_rel',"group_id","mr_id","Material Request Line"),
	}

	def get_max_deadline(self,cr,uid,context=None):
		if not context:context={}
		ids = context.get('active_ids',False)
		max_deadline = False
		if ids:
			cr.execute('select max(mr.date_end) from material_request_line mrl left join material_request mr on mrl.requisition_id=mr.id \
				where mrl.id in %s ',(tuple(ids),))

			max_deadline = cr.fetchone()
		return max_deadline
	def _get_buyer_default(self,cr,uid,context=None):
		if not context:context={}
		employee_id = self.pool.get("hr.employee").search(cr,uid,[('user_id','=',uid)])
		if employee_id:
			try:
				return employee_id[0]
			except:
				return employee_id
		return False
	_defaults = {
		"responsible_id": lambda self,cr,uid,context=None:uid,
		"mr_lines": lambda self,cr,uid,context=None:[x for x in context.get('active_ids',False)],
		'requisition_date': lambda self,cr,uid,context=None: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'requisition_deadline': get_max_deadline,
		"assigned_buyer":_get_buyer_default,
	}

	def generate_batch_pr(self,cr,uid,ids,context=None):
		if not context:context={}
		line_ids = []
		uom_obj= self.pool.get("product.uom")
		for group in self.browse(cr,uid,ids,context=context):
			data = {
				"name"				: self.pool.get('ir.sequence').get(cr, uid, 'pr_skc', context={'date':group.requisition_date}),
				'origin'			: "; ".join([x.requisition_id and x.requisition_id.name or '' for x in group.mr_lines]),
				'line_ids'			: [],
				"date_end"			: group.requisition_deadline,
				"date_start"		: group.requisition_date,
				"assigned_employee"	: group.assigned_buyer and group.assigned_buyer.id or False,
				"user_id"			: group.responsible_id and group.responsible_id.id or False,
				}
			lines=[]
			for mr_line in group.mr_lines:	
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
				}
				lines.append(line)


			if lines and len(lines)>0:
				created_id=self.pool.get('purchase.requisition').create(cr,uid,data,context=context)
				for l in lines:
					l.update({'requisition_id':created_id})
					prl_id = self.pool.get('purchase.requisition.line').create(cr,uid,l)
					self.pool.get('material.request.line').write(cr,uid,l.get('material_req_line_id'),{'state':'submit','pr_id':created_id,'pr_line_id':prl_id})
		data_pool = self.pool.get('ir.model.data')
		action_model = False
		action = {}
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'purchase_requisition', "action_purchase_requisition")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','=', "+str(created_id)+")]"
		return action