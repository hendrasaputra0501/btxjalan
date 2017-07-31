from openerp.osv import fields,osv
import time
import netsvc
import pooler
import datetime
from dateutil.relativedelta import relativedelta
import base64, urllib
import decimal_precision as dp
from tools.translate import _
from openerp import SUPERUSER_ID

class material_request(osv.Model):
	_name = "material.request"

	def _get_incoming_shipment(self,cr,uid,ids,field_name,arg,context=None):
		if not context:context={}
		res={}
		mr_ids=self.browse(cr,uid,ids,context)
		for mr in mr_ids:
			res[mr.id]={
				'stock_incoming_move_ids':[],
				'stock_incoming_ids':[],
					}
		for mr in mr_ids:
			pr_lines = []
			for mr_line in mr.line_ids:
				if mr_line.pr_line_id and mr_line.pr_line_id.id:
					pr_lines.append(mr_line.pr_line_id.id)
			if pr_lines and pr_lines!=[]:
				po_lines = self.pool.get('purchase.order.line').search(cr,uid,[('pr_lines','in',pr_lines)])
				if po_lines:
					move_ids = self.pool.get('stock.move').search(cr,uid,[('purchase_line_id','in',po_lines)])
					if move_ids:
						res[mr.id]['stock_incoming_move_ids']=list(set(move_ids))
						pick_ids = []
						for move in self.pool.get('stock.move').browse(cr,uid,move_ids):
							if move.picking_id and move.picking_id.id:
								pick_ids.append(move.picking_id.id)
						# pick_ids=list(set(pick_ids))
						res[mr.id]['stock_incoming_ids']=list(set(pick_ids))
		return res
	_columns ={
		'name'						: fields.char('Requisition Reference', size=32,required=True),
		'origin'					: fields.char('Reference', size=32),
		'date_start'				: fields.datetime('Requisition Date',required=True),
		'date_end'					: fields.datetime('Requisition Deadline', required=True),
		# 'user_id'					: fields.many2one('res.users', 'Responsible', readonly=True),
		'location_id'				: fields.many2one('stock.location',"Site ID",required=True),
		'location_dest_id'			: fields.many2one('stock.location',"Consumtion Location",required=True),
		'exclusive'				 	: fields.selection([('exclusive','Purchase Requisition (exclusive)'),('multiple','Multiple Requisitions')],'Requisition Type', required=False, help="Purchase Requisition (exclusive):	On the confirmation of a purchase order, it cancels the remaining purchase order.\nPurchase Requisition(Multiple):	It allows to have multiple purchase orders.On confirmation of a purchase order it does not cancel the remaining orders"""),
		'description'				: fields.text('Description'),
		'company_id'				: fields.many2one('res.company', 'Company', required=True),
		'line_ids'					: fields.one2many('material.request.line','requisition_id','Products to Purchase',required=True),
		'warehouse_id'				: fields.many2one('stock.warehouse', 'Warehouse'),
		'state'		 				: fields.selection([('draft','Draft'),('lv_1','Waitting Manager Approve'),
											('lv_2','Waitting Head of Division'),
											('lv_3','Waiting Warehouse User'),
											('cancel','Cancelled'),('done','Done')], 'State', required=True),
		'purchase_suggestion'		: fields.selection([('local','Local'),('import','Import')],"Purchase Suggestion"),
		'issue_created'				: fields.boolean('Issue Document Exists?',readonly=False),
		'department'				: fields.many2one('hr.department', 'Department'),
		'department_req_employee'	: fields.related('req_employee', 'department_id', relation='hr.department',type='many2one', string='Department',store=True, readonly=True),
		'req_employee'				: fields.many2one('hr.employee', 'Request By', required=False),
		'req_employee_name'			: fields.char('Request By', char=100, required=True),
		'user_id'					: fields.many2one('res.users', 'Created By',required=True),
		'user_app'					: fields.datetime('User Approve Date'),
		'manager_app'				: fields.datetime('Manager Approve Date'),
		'proc_app'					: fields.datetime('MMD Approve Date'),
		'ceo_app'					: fields.datetime('CEO Approve Date'),
		'warehouse_app'				: fields.datetime('Warehouse Approve Date'),
		'cancel_app'				: fields.datetime("Cancellation Date"),
		'bypass_stock'				: fields.boolean('By Pass Stock Checking?'),
		'ext_note'					: fields.text('Extra Notes', readonly=False,),
		'stock_picking_ids'			: fields.one2many('stock.picking','material_req_id','Internal Moves'),
		'budget_forecast_ids'		: fields.one2many('budget.forecast.mr', 'mr_id', 'Budget Forecasted Line', readonly=True),
		#'purchase_ids'				: fields.one2many('purchase.order','requisition_id','Purchase Orders',states={'done': [('readonly', True)]}),
		#'pr_id'						: fields.many2one('purchase.requisition','PR id'),
		"stock_incoming_move_ids"	: fields.function(_get_incoming_shipment,type="one2many",relation="stock.move",multi='fetch_move',string="Related Incoming Shipment",),
		"stock_incoming_ids"		: fields.function(_get_incoming_shipment,type="one2many",relation="stock.picking",multi='fetch_move',string="Related Incoming Shipment",),
		"material_type"				: fields.many2one('product.material.type',"Material Type")
	}

	_defaults = {
		'date_start': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'state': 'draft',
		'exclusive': 'multiple',
		'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id,
		'user_id': lambda self, cr, uid, context: uid,
		"bypass_stock":True,
		'name': '/',
		'purchase_suggestion':'local',
		}

	_order = "date_start desc"

	def copy(self, cr, uid, id, default=None, context=None):
		if default is None:
			default = {}
		default.update({
			'user_id':uid,
			'name':'/',
			'stock_picking_ids':[],
			'budget_forecast_ids':[],
		})
		if 'date_start' not in default:
			default['date_start'] = time.strftime('%Y-%m-%d %H:%M:%S')
		mr = self.browse(cr, uid, id, context=context)
		lines = []
		for line in mr.line_ids:
			line_dic = self.pool.get('material.request.line').copy_data(cr, uid, line.id)
			
			line_dic['pr_line_id'] = False
			line_dic['pr_id'] = False

			lines.append((0,0,line_dic))
		default.update({'line_ids':lines})
		return super(material_request, self).copy(cr, uid, id, default=default, context=context)

	def create(self, cr, uid, vals, context=None):
		if vals.get('name','/')=='/':
			seq_name = 'mr_stores'
			cd = {}
			if vals.get('purchase_suggestion',False):
				seq_name = 'mr_'+vals.get('purchase_suggestion',False)
			if vals.get('date_start',False):
				cd = {'date':vals['date_start']}
			name = self.pool.get('ir.sequence').get(cr, uid, seq_name, context=cd)
			if not name:
				name ='/'
			if vals.get('department',False):
				dept = self.pool.get('hr.department').browse(cr, uid, vals.get('department',False))
				# print ">>>>>>>>>>>>>>>", dept.name, dept.name[:3], name
				name = name.replace('Dept',str(dept.name and len(dept.name)>3 and dept.name[:3] or dept.name or ''))
				# print ">>>>>>>>>>>>>>>", dept.name, name
			else:
				name = name.replace('Dept','')
			vals.update({'name': name})
		return super(material_request, self).create(cr, uid, vals, context)

	def onchange_deadline(self,cr,uid,ids,date_start,date_end,context=None):
		if not context:context={}
		res={}
		if date_start and date_end:
			startd=datetime.datetime.strptime(date_start,"%Y-%m-%d %H:%M:%S")		
			endd=datetime.datetime.strptime(date_end,"%Y-%m-%d %H:%M:%S")
			if (endd - startd).days<2:
				warn = {'title': 'Warning', 'message': 'End Date must be at least 2 days greater than Start Date'}
				res.update({"warning":warn,'value':{"date_end":False}})
		return res

	
	def onchange_request_employee(self,cr,uid,ids,req_employee,context=None):
		#print "req_employee",req_employee
		if not context:
			context={}
			
		if req_employee:
			employee = self.pool.get('hr.employee').browse(cr,uid,req_employee,context)
			return {'value':{'department':employee.department_id and employee.department_id.id or False}}
		else:
			return {'value':{'department':False, 'req_employee':False}}

	def action_cancel_draft(self, cr, uid, ids, context=None):
		# self.write(cr, uid, ids, {'user_app':time.strftime('%Y-%m-%d %H:%M:%S')})
		if not context:context={}
		#wf=
		#for mr in self.browse(cr,uid,ids,context=context):
		#	wf_service.trg_delete(uid, 'material.request', mr.id, cr)
		#	wf_service.trg_create(uid, 'material.request', mr.id, cr)
		return self.write(cr, uid, ids, {'state':'draft'}, context=context)

	def lv_1_approve(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'lv_1','user_app':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)


	def lv_2_approve(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'done','proc_app':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)


	def picking_cancel(self, cr, uid, ids, context=None):
		if not context:context={}
		wf_service = netsvc.LocalService("workflow")
		for mr in self.browse(cr,uid,ids,context=context):
			for pick in mr.stock_picking_ids:
				wf_service.trg_validate(uid, 'stock.picking', pick.id , 'button_cancel', cr)
			mr.write({
				'issue_created':False,
				})
		return True

	def tender_done(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state':'done','warehouse_app':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)



	def create_order(self, cr, uid, ids, context=None):
		if not context:context={}
		mr_obj = self.pool.get('material.request')
		mr_line_obj = self.pool.get('material.request.line')
		stock_picking_obj = self.pool.get('stock.picking')
		stock_move_obj = self.pool.get('stock.move')
		
		
		for id_mr in self.browse(cr,uid,ids,context):
			if not id_mr.issue_created:
				record = {
							'origin'			: id_mr.name,
							'type'				: "internal",
							'req_employee'		: id_mr.req_employee.id,
							'material_req_id' 	: id_mr.id,
							'mr_description'	: id_mr.origin,
							'internal_shipment_type':'ss_issue',
							'issue_state'		:'draft_department',
							}
				
				sp_id = stock_picking_obj.create(cr, uid, record)
				
				location_id = self.pool.get('stock.location').search(cr,uid,[('usage','=','internal'),('name','=','Stock')])
				if location_id:
					try:
						location_id = location_id[0]
					except:
						pass
				location_dest_id = id_mr.department and id_mr.department.general_location_id and id_mr.department.general_location_id.id or location_id

				for id_mr_line in id_mr.line_ids:
					location_id = id_mr_line.location_id and id_mr_line.location_id.id or (location_id and location_id or False)
					location_dest_id = id_mr_line.location_dest_id and id_mr_line.location_dest_id.id or location_dest_id
					move_line_data = {
							'product_uos_qty'		: id_mr_line.product_qty,
							'date_expected'		 	: time.strftime('%Y-%m-%d %H:%M:%S'),
							'date'					: time.strftime('%Y-%m-%d %H:%M:%S'),
							'product_qty'			: id_mr_line.product_qty,
							'name'					: id_mr_line.product_id.name,
							'product_id'			: id_mr_line.product_id.id,
							'company_id'			: id_mr.company_id and id_mr.company_id.id or False,
							'analytic_account_id'	: id_mr_line.account_analytic_id and id_mr_line.account_analytic_id.id or False,
							'picking_id'			: sp_id,
							'state'				 	: "draft",
							'location_dest_id'		: id_mr_line.location_id and id_mr_line.location_id.id or location_dest_id,
							'product_uom'			: id_mr_line.product_uom_id.id or id_mr_line.stock_uom_id.i,
							'price_unit'			: id_mr_line.price,
							'analytic_id'			: id_mr_line.account_analytic_id.id,
							'note'					: id_mr_line.description,
							'reason_code'			: id_mr_line.reason_code and id_mr_line.reason_code.id or False,
							'material_type'			: id_mr_line.material_type and id_mr_line.material_type.id or False,
							}
					# 'location_id'			: location_id,
					# 'location_id'			: location_id,
					if location_id:
						move_line_data.update({'location_id' : location_id})
					if location_dest_id:
						move_line_data.update({'location_dest_id' : location_dest_id})
					stock_move_obj.create(cr, uid, move_line_data)
				id_mr.write({
					"issue_created":True,
					})
			else:
				 raise osv.except_osv(_('Can not create new issue document!'),_("Issue Document has already created before!") )
		return True

	def create_pr(self,cr,uid,ids,context=None):
		if not context:context={'goods_type':'stores'}
		uom_obj = self.pool.get('product.uom')
		for mr in self.browse(cr,uid,ids,context=context):
			data = {
				"name"				: self.pool.get('ir.sequence').get(cr, uid, 'pr_skc'),
				'origin'			: mr.name,
				'int_move_ids'		: [x.id for x in mr.stock_picking_ids],
				'mr_description'	: mr.origin or mr.description or False,
				'line_ids'			: [],
				"material_req_id"	: mr.id,
				"date_end"			: mr.date_end,
				"mr_description"	: mr.origin,
				}
			lines=[]
			for mr_line in mr.line_ids:	
				if not mr.bypass_stock:
					product_qty = uom_obj._compute_qty(cr, uid, mr_line.product_uom_id.id, mr_line.product_qty, mr_line.product_id.uom_id.id, round=False)
					if product_qty <= mr_line.current_qty_available:
						continue
				line = (0,0,{
				'material_req_line_id':mr_line.id,
				'product_id'		: mr_line.product_id and mr_line.product_id.id or False,
				'product_qty'		: mr_line.product_qty or 0.0,
				'account_analytic_id': mr_line.account_analytic_id and mr_line.account_analytic_id.id or False,
				'price'				: mr_line.price,
				'product_uom_id'	: mr_line.product_uom_id and mr_line.product_uom_id.id or False,
				# 'note'				: mr_line.info,
				})
				lines.append(line)
			data.update({'line_ids':lines})
			if lines and len(lines)>0:
				self.pool.get('purchase.requisition').create(cr,uid,data,context=context)
		return True

	def _get_forecast_other(self,cr,uid,ids,analytic_ids,context):
		value = {}
		if analytic_ids:
			for analytic in analytic_ids:
				value.update({analytic:0.0})
			this_year = datetime.date.today().strftime('%Y-01-01')
			today = datetime.date.today().strftime('%Y-%m-%d')
			#get forecast from material request line
			mr_search = self.pool.get('material.request').search(cr,uid,[('date_start','>=',this_year),('date_start','<=',today),('id','not in',ids),('state','not in',('draft','cancel'))])
			mr_line_ids = self.pool.get('material.request.line').search(cr,uid,[('id','in',mr_search),('account_analytic_id','in',analytic_ids)])
			# print "mr_line_ids =======mr_line_ids========",mr_line_ids
			mr_ids = []
			for mr_line in self.pool.get('material.request.line').browse(cr,uid,mr_line_ids):
				value.update({
					mr_line.account_analytic_id.id:value.get(mr_line.account_analytic_id.id,0.0)+mr_line.subtotal
					})
				mr_ids.append(mr_line.requisition_id.id)
			#get forecast from purchase order line
			purchase_request_ids = self.pool.get('purchase.requisition').search(cr,uid,[('mr_lines','in',mr_line_ids)])
			purchase_order_exists = []
			if purchase_request_ids:
				# print "-------------",[rfq.purchase_ids for rfq in [pr for pr in self.pool.get('purchase.requisition').browse(cr,uid,purchase_request_ids)] if rfq.purchase_ids]
				for pr in self.pool.get('purchase.requisition').browse(cr,uid,purchase_request_ids):
					if pr.purchase_ids:
						for purchase in pr.purchase_ids:
							purchase_order_exists.append(purchase.id)
				
				# purchase_order_exists = [po.id for po in [rfq.purchase_ids for rfq in [pr for pr in self.pool.get('purchase.requisition').browse(cr,uid,purchase_request_ids)] if rfq.purchase_ids]]
			purchase_order = self.pool.get('purchase.order').search(cr,uid,[('state','not in',['cancel']),('date_order','>=',this_year),('date_order','<=',today)])
			purchase_order_line_ids = self.pool.get('purchase.order.line').search(cr,uid,[('order_id','not in',purchase_order_exists),('order_id','in',purchase_order_exists),\
				('account_analytic_id','in',analytic_ids)])
			for line in self.pool.get('purchase.order.line').browse(cr,uid,purchase_order_line_ids):
				value.update({
					mr_line.account_analytic_id.id:value.get(line.account_analytic_id.id,0.0)+line.price_subtotal
					})
			#get forecast from supplier invoices
			invoice_ids = self.pool.get('account.invoice').search(cr,uid,[('state','not in',['cancel','open','paid']),('type','=','in_invoice'),('date_invoice','>=',this_year),('date_invoice','<=',today)],context=context)
			if invoice_ids:
				invoice_line_ids = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','in',invoice_ids),('account_analytic_id','in',analytic_ids)])
				for inv_line in self.pool.get('account.invoice.line').browse(cr,uid,invoice_line_ids):
					value.update({
						inv_line.account_analytic_id.id:value.get(inv_line.account_analytic_id.id,0.0)+inv_line.price_subtotal
					})
		return value

	def compute_forecast(self,cr,uid,ids,context=None):
		if not context:context={}
		for mr in self.browse(cr,uid,ids,context=context):
			self.pool.get('budget.forecast.mr').unlink(cr,uid,[bfm.id for bfm in mr.budget_forecast_ids])
			analytic_ids = list(set([line.account_analytic_id.id for line in mr.line_ids]))
			# print "========analytic_ids========",analytic_ids
			dummy = {}
			for analytic in analytic_ids:
				dummy.update({analytic:0.0})
			for line in mr.line_ids:
				dummy.update({
					line.account_analytic_id.id: dummy.get(line.account_analytic_id.id,0.0) + line.subtotal
					})
			this_year = datetime.date.today().strftime('%Y-01-01')
			today = datetime.date.today().strftime('%Y-%m-%d')
			budget_ids = self.pool.get('crossovered.budget').search(cr,SUPERUSER_ID,[('date_from','>=',this_year),('date_to','>=',today),('state','in',('draft','confirm','validate'))],order="id desc",context=context)
			if budget_ids:
				budget_line_ids = self.pool.get('crossovered.budget.lines').search(cr,uid,[('date_from','>=',this_year),('date_to','>=',today),('analytic_account_id','in',analytic_ids),('crossovered_budget_id','in',budget_ids)],order="id desc",context=context)
				budget_lines = self.pool.get('crossovered.budget.lines').browse(cr,uid,budget_line_ids,context=context)
				forecast_other = self._get_forecast_other(cr,uid,[mr.id],analytic_ids,context)
				# forecast_other = {}
				for budget_line in budget_lines:
					forecast = {
						"mr_id"					: mr.id,
						"analytic_account_id"	: budget_line.analytic_account_id and budget_line.analytic_account_id.id or False,
						"transaction_amount"	: dummy.get(budget_line.analytic_account_id.id,0.0),
						"total_budget"			: budget_line.planned_amount,
						"practical_amount"		: budget_line.practical_amount,
						"total_residual_budget"	: budget_line.planned_amount - budget_line.practical_amount,
						"forecast_amount"		: budget_line.practical_amount + dummy.get(budget_line.analytic_account_id.id,0.0),
						"forecast_amount_other"	: budget_line.practical_amount+forecast_other.get(budget_line.analytic_account_id.id,0.0)+dummy.get(budget_line.analytic_account_id.id,0.0),
						"theoretical_amount"	: budget_line.theoritical_amount,
					}
					self.pool.get('budget.forecast.mr').create(cr,uid,forecast,context=context)
		return True

	def action_set_to_draft(self, cr, uid, ids, context=None):
		if not len(ids):
			return False
		mr_obj = self.pool.get('material.request')
		for mr in self.browse(cr, uid, ids, context):
			print "::::::::::::::", mr.id
			wf_service = netsvc.LocalService("workflow")
			wf_service.trg_delete(uid, 'material.request', mr.id, cr)
			wf_service.trg_create(uid, 'material.request', mr.id, cr)
			self.write(cr, uid, [mr.id], {'state': 'draft'})
		# for (id,name) in self.name_get(cr, uid, ids):
		# 	message = _("The material request '%s' has been set in draft state.") %(name,)
		# 	self.log(cr, uid, id, message)
		return True

class material_request_line(osv.Model):
	_name="material.request.line"
	_rec_name = 'product_id'

	def get_sequence(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		lines = self.browse(cr,uid,sorted(ids))
		req_id = lines[0].requisition_id.id
		
		result={}
		no=1

		mat_req_line_obj = self.pool.get('material.request.line')
		mat_req_line_ids = mat_req_line_obj.search(cr, uid, [('requisition_id','=',req_id)])
		for mat_req_line in mat_req_line_obj.browse(cr, uid,  sorted(mat_req_line_ids)) :
			if mat_req_line:
				result[mat_req_line.id]=no
				no+=1
		return result

	def _get_ids_from_material_request(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		mr_line_ids = []
		for mr in self.pool.get('material.request').browse(cr, uid, ids, context=context):
			for mr_line in mr.line_ids:
				if mr_line.id not in mr_line_ids:
					mr_line_ids.append(mr_line.id)
		return mr_line_ids
	
	def _get_ids_from_purchase_order(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		mr_line_ids = []
		for order in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
			for line in order.order_line:
				if line.pr_lines:
					mr_line_ids_dummy = self.pool.get('material.request.line').search(cr, uid, [('pr_line_id','in',[x.id for x in line.pr_lines])])
					if mr_line_ids_dummy:
						for mr_line_id in mr_line_ids_dummy:
							if mr_line_id not in mr_line_ids:
								mr_line_ids.append(mr_line_id)
		return mr_line_ids
	
	def _get_ids_from_stock_move_in(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		mr_line_ids = []
		for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
			if move.purchase_line_id and move.purchase_line_id.pr_lines:
				mr_line_ids_dummy = self.pool.get('material.request.line').search(cr, uid, [('pr_line_id','in',[x.id for x in move.purchase_line_id.pr_lines])])
				if mr_line_ids_dummy:
					for mr_line_id in mr_line_ids_dummy:
						if mr_line_id not in mr_line_ids:
							mr_line_ids.append(mr_line_id)
		return mr_line_ids

	def _get_ids_from_stock_move_out(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		mr_line_ids = []
		for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
			if move.picking_id and move.picking_id.type=='internal' and move.picking_id.material_req_id:
				for line in move.picking_id.material_req_id.line_ids:
					if line.product_id.id==move.product_id.id and line.id not in mr_line_ids:
						mr_line_ids.append(line.id)
		return mr_line_ids

	def _get_incoming_moves(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		purchase_line_pool = self.pool.get('purchase.order.line')
		stock_move_pool = self.pool.get('stock.move')
		result = {}
		for mr_line in self.browse(cr, uid, ids):
			result[mr_line.id] = {
				'state' : 'draft',
				'received_qty' : 0.0,
				'issued_qty' : 0.0,
				'qty_remaining' : 0.0,
			}
			if mr_line.requisition_id:
				if mr_line.requisition_id.state=='draft':
					state = 'draft'
				elif mr_line.requisition_id.state=='cancel':
					state = 'cancel'
				else:
					state = 'submit'
				received_qty = 0.0
				issued_qty = 0.0

				if mr_line.pr_line_id:
					pr_line_ids = [mr_line.pr_line_id.id]
					purchase_line_ids = purchase_line_pool.search(cr, uid, [('pr_lines','in',pr_line_ids),('order_id.state','not in',['draft','sent','cancel','except_picking'])])
					if purchase_line_ids:
						state = 'indented'
						move_in_ids = stock_move_pool.search(cr, uid, [('purchase_line_id','in',purchase_line_ids),('state','=','done')])
						if move_in_ids:
							state = 'arrived'
						for move_in in stock_move_pool.browse(cr, uid, move_in_ids):
							received_qty += move_in.product_qty

				issue_ids = [x.id for x in mr_line.requisition_id.stock_picking_ids]
				if issue_ids:
					move_out_ids = stock_move_pool.search(cr, uid, [('product_id','=',mr_line.product_id.id),('state','=','done'),('picking_id.type','=','internal'),('picking_id.id','in',issue_ids)])
					if move_out_ids:
						state='issued'
					for move_out in stock_move_pool.browse(cr, uid, move_out_ids):
						issued_qty += move_out.product_qty
				result[mr_line.id]['state'] = state
				result[mr_line.id]['received_qty'] = received_qty
				result[mr_line.id]['issued_qty'] = issued_qty
				result[mr_line.id]['qty_remaining'] = (received_qty-issued_qty)>0 and (received_qty>mr_line.product_qty and ((mr_line.product_qty-issued_qty)>0 and (mr_line.product_qty-issued_qty) or 0.0) or ((received_qty-issued_qty)>0 and (received_qty-issued_qty) or 0.0)) or 0.0
		return result

		
	_columns = {
		'name'					: fields.char('Information',size=128),
		'product_id'			: fields.many2one('product.product', 'Product'),
		'catalogue_id'			: fields.many2one('product.catalogue', 'Catalogue'),
		'part_number'			: fields.char(string='Part Number',size=300),
		'machine_number'		: fields.char('Machine Number', size=200, required=False),
		'product_requisition_id': fields.many2one('product.requisition.line',"Product name by request"),
		'location_id'			: fields.many2one('stock.location',"Site ID"),
		'location_dest_id'		: fields.many2one('stock.location',"Consumtion Location"),
		'consumption'			: fields.selection([('internal','Keep in Stock'),('inventory','Consume Directly')],"Directly Consume Products ?",required=True, help="If this field is checked, site id that will be shown is for consumption only"),
		'req_employee'			: fields.related('requisition_id','req_employee',type='many2one',obj='hr.employee', string='Request By', readonly="1"),
		'req_employee_name'		: fields.related('requisition_id','req_employee_name',type='char', string='Request By', readonly="1"),
		'user_id'				: fields.related('requisition_id','user_id',type='many2one',obj='res.users', string='Created By',readonly=True),
		'product_uom_id'		: fields.many2one('product.uom', 'Product UoM'),
		'current_qty_available'	: fields.related('product_id','qty_available',type="float",string="Available Qty"),
		'current_qty_virtual'	: fields.related('product_id','virtual_available',type="float",string="Forecasted Qty"),
		'stock_uom_id'			: fields.related('product_id','uom_id',type="many2one",relation='product.uom',string="Stock UoM"),
		'product_qty'			: fields.float('Quantity', digits=(16,2)),
		'requisition_id'		: fields.many2one('material.request','Material Requisition', ondelete='cascade'),
		'location_dest_id'		: fields.related('requisition_id',"location_dest_id",type="many2one",relation="stock.location", string="Site ID",store=True),
		'date_start'			: fields.related('requisition_id',"date_start",type="datetime", string="Requisition Date",store=True),
		'date_end'				: fields.related('requisition_id',"date_end",type="datetime", string="Deadline Date",store=True),
		'pr_id'					: fields.many2one("purchase.requisition","Purchase Requisition",ondelete="set null"),
		'pr_line_id'			: fields.many2one("purchase.requisition.line","Purchase Requisition Line",ondelete="set null"),
		'company_id'			: fields.many2one('res.company', 'Company', required=True),
		'price'				 	: fields.float('Last Price', required=False),
		'pricelist_id'			: fields.many2one('product.pricelist',"Currency", required=False),
		'last_po_id'			: fields.many2one('purchase.order',"Last PO", required=False),
		'account_analytic_id'	: fields.many2one('account.analytic.account', 'Analytic Account',),
		'subtotal'				: fields.float('Subtotal', required=False),
		'description'			: fields.char('Description', size=32,required=False),
		'detail'				: fields.text('Detail'),
		'remark'				: fields.text('Remark'),
		'currency_id'			: fields.many2one('res.currency',"Currency",required=True),
		"reason_code"			: fields.many2one('product.reason.code',"Reason Code",required=True),
		"material_type"			: fields.many2one('product.material.type',"Material Type"),
		'purchase_suggestion'	: fields.selection([('local','Local'),('import','Import')],"Purchase Suggestion"),
		# 'state'					: fields.selection([
		# 	('draft','Draft'),
		# 	('submit','Tobe Requested'),
		# 	('request','Requested'),
		# 	('indented','Waiting for Product'),
		# 	('arrived','Received'),
		# 	('issued','Issued'),
		# 	('rejected','Rejected'),
		# 	('cancel','Cancelled'),
		# 	]
		# 	,"Status",required=True),
		'header_for_print'		:fields.text("Header"),
		'sequence_line'	: fields.function(get_sequence, type='int' ,string='No'),
		'state' : fields.function(_get_incoming_moves, type="selection", selection=[('draft','Draft'),('submit','To Be Requested'),('indented','Waiting for Incoming Product'),('arrived','Received'),('issued','Issued'),('cancel','Cancelled')], string="Line State",
			store={
				'material.request' : (_get_ids_from_material_request, ['state'], 10),
				'purchase.order' : (_get_ids_from_purchase_order, ['state','picking_ids'], 10),
				'stock.move' : (_get_ids_from_stock_move_in, ['state'], 10),
				'stock.move' : (_get_ids_from_stock_move_out, ['state'], 10),
			}, method = True, multi='all_mr_line'),
		'received_qty' : fields.function(_get_incoming_moves, type="float", string="Received Qty", digits = (2,4), 
			store={
				'material.request' : (_get_ids_from_material_request, ['state'], 10),
				'purchase.order' : (_get_ids_from_purchase_order, ['state','picking_ids'], 10),
				'stock.move' : (_get_ids_from_stock_move_in, ['state'], 10),
				'stock.move' : (_get_ids_from_stock_move_out, ['state'], 10),
			}, method = True, multi='all_mr_line'),
		'issued_qty' : fields.function(_get_incoming_moves, type="float", string="Issued Qty", digits = (2,4), 
			store={
				'material.request' : (_get_ids_from_material_request, ['state'], 10),
				'purchase.order' : (_get_ids_from_purchase_order, ['state','picking_ids'], 10),
				'stock.move' : (_get_ids_from_stock_move_in, ['state'], 10),
				'stock.move' : (_get_ids_from_stock_move_out, ['state'], 10),
			}, method = True, multi='all_mr_line'),
		'qty_remaining' : fields.function(_get_incoming_moves, type="float", string="Qty Remaining to Issue", digits = (2,4), 
			store={
				'material.request' : (_get_ids_from_material_request, ['state'], 10),
				'purchase.order' : (_get_ids_from_purchase_order, ['state','picking_ids'], 10),
				'stock.move' : (_get_ids_from_stock_move_in, ['state'], 10),
				'stock.move' : (_get_ids_from_stock_move_out, ['state'], 10),
			}, method = True, multi='all_mr_line'),
	}
	_defaults = {
		'consumption'			: 'inventory',
		'company_id'			: lambda self, cr, uid, c: self.pool.get('res.users').browse(cr,uid,uid).company_id.id,
		'product_qty'			: 1.0,
		'state'					: lambda *a:'draft',
		'purchase_suggestion'	: lambda self, cr, uid, context : context.get('purchase_suggestion','local'),
		'location_id'			: lambda self, cr, uid, context : context.get('location_id',False),
		'location_dest_id'		: lambda self, cr, uid, context : context.get('location_dest_id',False),
		'header_for_print'		: lambda *a:' ',
	}

	_order = "requisition_id desc, id asc"

	def onchange_product_requisition_id(self, cr, uid, ids, prod_req_id, purchase_suggestion,\
					department, date_start, product_uom_id, context=None):
		if not context:context={}
		if prod_req_id:
			prid = self.pool.get('product.requisition.line').browse(cr,uid,prod_req_id,context=context)
			if prid.product_id and prid.product_id.id:
				value = self.onchange_product_id(cr, uid, ids, purchase_suggestion, department,date_start,prid.product_id.id,product_uom_id, context=None)
				new_val=value.get('value',{})
				new_val.update({
					'product_id':prid.product_id.id,
					})
		else:
			raise osv.except_osv(_('Warning!'), _('New Item Code for your product request has not been created. Please ask for the authorized user to create new code'))
		return {'value':new_val}

	def onchange_product_id(self, cr, uid, ids, purchase_suggestion, department, date_start, product_id, product_uom_id, context=None):
		""" Changes UoM and name if product_id changes.
		@param name: Name of the field
		@param product_id: Changed product_id
		@return:	Dictionary of changed values
		"""
		if not context:context={}
		user =self.pool.get('res.users').browse(cr,uid,uid,context=context)
		company_currency = user.company_id and user.company_id.currency_id and user.company_id.currency_id.id or False
		budget_analytic = False
		value = {'product_uom_id': ''}
		
		if not department:
			raise osv.except_osv(_('No Department Defined !'),_("You must first select an Employee or Department!") )
		
		if product_id:
			context.update({'date_order':datetime.datetime.strptime(date_start,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')})
			if purchase_suggestion:
				context.update({'purchase_type':purchase_suggestion})
			prod = self.pool.get('product.product').browse(cr, SUPERUSER_ID, product_id, context=context)
			
			account_expense = prod.property_account_expense.id
			type_product	= prod.type
			#print "account_expense ::", account_expense
			#print "product ::::", product_id.name
			if type_product == 'consu':
				value = {'product_id':False, 'product_uom_id': False,'product_qty':1.0,'price':False ,'account_analytic_id':False}
				warning = {
					"title": ("Product Type"),
					"message": (("You Can not Product selected with Type Consumable"))
				}
				return {'warning': warning ,'value': value}
			
			if not account_expense:
				value = {'product_id':False, 'product_uom_id': False,'product_qty':1.0,'price':False ,'account_analytic_id':False}
				warning = {
					"title": ("Account Expense Product is not defined"),
					"message": (("Please Define Account Expense for Product '%s'") % (prod.name))
				}
				return {'warning': warning ,'value': value}
			analytic_id = False
			if prod.property_account_expense.user_type.report_type == 'asset':
				analytic_account_search = self.pool.get('account.analytic.account').search(cr, uid, [('department_id','=',department)])
				if analytic_account_search:
					acc_budget_post_ids = self.pool.get('account.budget.post').search(cr,uid,[('account_ids','in',prod.property_account_expense.id)])

					if acc_budget_post_ids:
						cbl_ids = self.pool.get('crossovered.budget.lines').search(cr,uid,[('analytic_account_id','in',analytic_account_search),
							("date_from","<=",date_start),("date_to",">=",date_start),('general_budget_id','in',acc_budget_post_ids)])
						cbl = self.pool.get('crossovered.budget.lines').browse(cr,uid,cbl_ids,context=context)
						try:
							analytic_id = cbl.analytic_account_id and cbl.analytic_account_id.id or False
						except:
							analytic_id = cbl[0].analytic_account_id and cbl[0].analytic_account_id.id or False

				value = {
					'product_uom_id': prod.uom_id.id or company_currency or False,
					'price':prod.last_price or 0.0,
					'account_analytic_id':analytic_id,
					'pricelist_id':prod.last_order_id and prod.last_order_id.pricelist_id and prod.last_order_id.pricelist_id.id or False,
					'currency_id':prod.last_order_id and prod.last_order_id.pricelist_id and prod.last_order_id.pricelist_id.currency_id and prod.last_order_id.pricelist_id.currency_id.id or False,
					}
				
			else:
				analytic_account_search = self.pool.get('account.analytic.account').search(cr, uid, [('department_id','=',department)])
				if analytic_account_search:
					acc_budget_post_ids = self.pool.get('account.budget.post').search(cr,uid,[('account_ids','in',prod.property_account_expense.id)])

					if acc_budget_post_ids:
						cbl_ids = self.pool.get('crossovered.budget.lines').search(cr,uid,[('analytic_account_id','in',analytic_account_search),
							("date_from","<=",date_start),("date_to",">=",date_start),('general_budget_id','in',acc_budget_post_ids)])
						cbl = self.pool.get('crossovered.budget.lines').browse(cr,uid,cbl_ids,context=context)
						try:
							analytic_id = cbl.analytic_account_id and cbl.analytic_account_id.id or False
						except:
							analytic_id = cbl[0].analytic_account_id and cbl[0].analytic_account_id.id or False
				value = {
					'product_uom_id': prod.uom_id.id,
					'price':prod.last_price or 0.0,
					'account_analytic_id':analytic_id,
					'pricelist_id':prod.last_order_id and prod.last_order_id.pricelist_id and prod.last_order_id.pricelist_id.id or False,
					'currency_id':prod.last_order_id and prod.last_order_id.pricelist_id and prod.last_order_id.pricelist_id.currency_id \
							and prod.last_order_id.pricelist_id.currency_id.id or company_currency or False,
					}
			value.update({
				'name':prod.name or '/',
				'current_qty_available'	: prod.qty_available ,
				'current_qty_virtual'	: prod.virtual_available ,
				'stock_uom_id'			: prod.uom_id.id,
				# "reason_code"			: prod.first_segment_code and prod.first_segment_code.id or False,
				# "material_type"		: prod.second_segment_code and prod.second_segment_code.id or False,
				'catalogue_id'			: prod.catalogue_number_id and prod.catalogue_number_id.id or False,
				'part_number'			: prod.part_number or False,
				'machine_number'		: prod.catalogue_number_id and prod.catalogue_number_id.machine_number or '',
				"last_po_id"			: prod.last_order_id and prod.last_order_id.id or False,
				})
		return {'value': value}

	def onchange_catalogue_id(self, cr, uid, ids, catalogue_id, context=None):
		res = {}
		if catalogue_id:
			catalogue = self.pool.get('product.catalogue').browse(cr, uid, catalogue_id)
			res.update({'machine_number':catalogue.machine_number or ''})
		return {'value':res}

	def onchange_price_qty(self,cr,uid,ids,price,product_qty,context=None):
		if not context:context={}
		value={}
		if price and product_qty:
			value.update({'subtotal':price*product_qty})
		return {'value':value}
