import time
import datetime

from openerp.osv import fields, osv
from openerp import pooler
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class project_project(osv.osv):
	_inherit = 'project.project'

	_columns = {
		'is_work_order': fields.boolean('Work Order'),
		'work_order_ids': fields.one2many('project.work.order', 'project_id', "Work Order Progress"),
	}

	# def open_timesheets(self, cr, uid, ids, context=None):
	# 	""" open Timesheets view """
	# 	mod_obj = self.pool.get('ir.model.data')
	# 	act_obj = self.pool.get('ir.actions.act_window')

	# 	project = self.browse(cr, uid, ids[0], context)
	# 	view_context = {
	# 		'search_default_account_id': [project.analytic_account_id.id],
	# 		'default_account_id': project.analytic_account_id.id,
	# 	}
	# 	help = _("""<p class="oe_view_nocontent_create">Record your timesheets for the project '%s'.</p>""") % (project.name,)
	# 	try:
	# 		if project.to_invoice and project.partner_id:
	# 			help+= _("""<p>Timesheets on this project may be invoiced to %s, according to the terms defined in the contract.</p>""" ) % (project.partner_id.name,)
	# 	except:
	# 		# if the user do not have access rights on the partner
	# 		pass

	# 	res = mod_obj.get_object_reference(cr, uid, 'hr_timesheet', 'act_hr_timesheet_line_evry1_all_form')
	# 	id = res and res[1] or False
	# 	result = act_obj.read(cr, uid, [id], context=context)[0]
	# 	result['name'] = _('Timesheets')
	# 	result['context'] = view_context
	# 	result['help'] = help
	# 	return result

project_project()

class project_work_order(osv.osv):
	def _get_amount_subtotal(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			subtotal = line.quantity * line.unit_price
			res[line.id] = subtotal
		return res

	def _progress_payment_rate(self, cr, uid, ids, names, arg, context=None):
		if context is None:
			context = {}
		res = {}
		for wo in self.browse(cr, uid, ids, context=context):
			if wo.amount_subtotal:
				paid_amount = sum([line.price_unit for line in wo.invoice_line_ids])
				progress = round((paid_amount/wo.amount_subtotal)*100.0,2) 
			else:
				progress = 0.0
			res[wo.id] = progress
		return res

	_name = "project.work.order"	
	_columns={
		'project_id': fields.many2one('project.project', 'Project Ref', ondelete='cascade', required=True, select="1"),
		'name': fields.char('Work summary', size=128),
		'date': fields.date('Date', select="1"),
		'company_id': fields.related('project_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
		'product_id' : fields.many2one('product.product', 'Product', domain=[('type','=','service')], required=True),
		'quantity' : fields.float('Quantity', digits_compute= dp.get_precision('Account')),
		'uom_id' : fields.many2one('product.uom', 'UoS'),
		'unit_price' : fields.float('Price Unit', digits_compute= dp.get_precision('Account')),
		'amount_subtotal' : fields.function(_get_amount_subtotal, type='float', digits_compute= dp.get_precision('Account'), string='Amount Subtotal'),
		'invoice_line_ids' : fields.one2many('account.invoice.line', 'work_order_id', 'Invoice Lines'),
		'progress_payment_rate': fields.function(_progress_payment_rate, string='Progress Payment', type='float', help="Percent of Work Order's payment closed according to the total of outstanding amount to pay",
			store = {
				'project.work.order': (lambda self,cr,uid,ids,context={}:ids, ['invoice_line_ids','unit_price','quantity'], 10),
			}),
	}

	_defaults = {
		'date': lambda *a: time.strftime('%Y-%m-%d'),
	}
	
project_work_order()

class project_task(osv.osv):
	_inherit = "project.task"

	# def get_user_related_details(self, cr, uid, user_id):
	# 	res = {}
	# 	emp_obj = self.pool.get('hr.employee')
	# 	emp_id = emp_obj.search(cr, uid, [('user_id', '=', user_id)])
	# 	if not emp_id:
	# 		user_name = self.pool.get('res.users').read(cr, uid, [user_id], ['name'])[0]['name']
	# 		raise osv.except_osv(_('Bad Configuration!'),
	# 			 _('Please define employee for user "%s". You must create one.')% (user_name,))
	# 	emp = emp_obj.browse(cr, uid, emp_id[0])
	# 	if not emp.product_id:
	# 		raise osv.except_osv(_('Bad Configuration!'),
	# 			 _('Please define product and product category property account on the related employee.\nFill in the HR Settings tab of the employee form.'))

	# 	if not emp.journal_id:
	# 		raise osv.except_osv(_('Bad Configuration!'),
	# 			 _('Please define journal on the related employee.\nFill in the timesheet tab of the employee form.'))

	# 	acc_id = emp.product_id.property_account_expense.id
	# 	if not acc_id:
	# 		acc_id = emp.product_id.categ_id.property_account_expense_categ.id
	# 		if not acc_id:
	# 			raise osv.except_osv(_('Bad Configuration!'),
	# 					_('Please define product and product category property account on the related employee.\nFill in the timesheet tab of the employee form.'))

	# 	res['product_id'] = emp.product_id.id
	# 	res['journal_id'] = emp.journal_id.id
	# 	res['general_account_id'] = acc_id
	# 	res['product_uom_id'] = emp.product_id.uom_id.id
	# 	return res

	def create(self, cr, uid, vals, *args, **kwargs):
		# timesheet_obj = self.pool.get('hr.analytic.timesheet')
		work_order_obj = self.pool.get('project.work.order')
		# task_obj = self.pool.get('project.task')
		project_obj = self.pool.get('project.project')
		uom_obj = self.pool.get('product.uom')
		product_obj = self.pool.get('product.product')

		vals_line = {} #parameters for work order
		context = kwargs.get('context', {})
		if not context.get('no_analytic_entry',False):
			# task_obj = task_obj.browse(cr, uid, vals['task_id'])
			project_obj = project_obj.browse(cr, uid, vals['project_id'])
			vals_line['project_id'] = project_obj.id
			# result = self.get_user_related_details(cr, uid, vals.get('user_id', uid))
			vals_line['name'] = '%s: %s' % (tools.ustr(project_obj.name), tools.ustr(vals['name'] or '/'))
			# vals_line['user_id'] = vals['user_id']

			product_ids = product_obj.search(cr, uid, [('type','=','service')])
			if product_ids:
				product = product_obj.browse(cr, uid, product_ids[0])
				vals_line['product_id'] = product.id
				vals_line['uom_id'] = product.uom_id.id
			else:
				raise osv.except_osv(_('Bad Configuration!'),
					_('Please define product and product category of Service Product in your Product Masters'))
			# vals_line['date'] = vals['date'][:10]

			vals_line['unit_price'] = 0.0
			vals_line['quantity'] = 1.0
			
			# acc_id = task_obj.project_id and task_obj.project_id.analytic_account_id.id or False
			if project_obj.is_work_order:
				# vals_line['account_id'] = acc_id
				# res = timesheet_obj.on_change_account_id(cr, uid, False, acc_id)
				# if res.get('value'):
				# 	vals_line.update(res['value'])
				# vals_line['general_account_id'] = result['general_account_id']
				# vals_line['journal_id'] = result['journal_id']
				# vals_line['amount'] = 0.0
				# vals_line['product_uom_id'] = result['product_uom_id']
				# amount = vals_line['unit_amount']
				# prod_id = vals_line['product_id']
				# unit = False
				# timeline_id = timesheet_obj.create(cr, uid, vals=vals_line, context=context)
				work_order_id = work_order_obj.create(cr, uid, vals=vals_line, context=context)

				# Compute based on pricetype
				# amount_unit = timesheet_obj.on_change_unit_amount(cr, uid, timeline_id,
				# 	prod_id, amount, False, unit, vals_line['journal_id'], context=context)
				# if amount_unit and 'amount' in amount_unit.get('value',{}):
				# 	updv = { 'amount': amount_unit['value']['amount'] }
				# 	timesheet_obj.write(cr, uid, [timeline_id], updv, context=context)
				vals['work_order_id'] = work_order_id
		return super(project_task,self).create(cr, uid, vals, *args, **kwargs)

	def write(self, cr, uid, ids, vals, context=None):
		"""
		When a project task work gets updated, handle its hr analytic timesheet.
		"""
		if context is None:
			context = {}
		# timesheet_obj = self.pool.get('hr.analytic.timesheet')
		work_order_obj = self.pool.get('project.work.order')
		uom_obj = self.pool.get('product.uom')
		product_obj = self.pool.get('product.product')
		result = {}

		if isinstance(ids, (long, int)):
			ids = [ids]

		for task in self.browse(cr, uid, ids, context=context):
			line_id = task.work_order_id
			if not line_id:
				# if a record is deleted from timesheet, the line_id will become
				# null because of the foreign key on-delete=set null
				continue

			vals_line = {}
			if 'name' in vals:
				vals_line['name'] = '%s: %s' % (tools.ustr(task.task_id.name), tools.ustr(vals['name'] or '/'))
			# if 'user_id' in vals:
			# 	vals_line['user_id'] = vals['user_id']
			# if 'date' in vals:
			# 	vals_line['date'] = vals['date'][:10]
			# if 'hours' in vals:
			# 	vals_line['unit_amount'] = vals['hours']
			# 	prod_id = vals_line.get('product_id', line_id.product_id.id) # False may be set

			# 	# Put user related details in analytic timesheet values
			# 	details = self.get_user_related_details(cr, uid, vals.get('user_id', task.user_id.id))
			# 	for field in ('product_id', 'general_account_id', 'journal_id', 'product_uom_id'):
			# 		if details.get(field, False):
			# 			vals_line[field] = details[field]

			# 	# Check if user's default UOM differs from product's UOM
			# 	user_default_uom_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.project_time_mode_id.id
			# 	if details.get('product_uom_id', False) and details['product_uom_id'] != user_default_uom_id:
			# 		vals_line['unit_amount'] = uom_obj._compute_qty(cr, uid, user_default_uom_id, vals['hours'], details['product_uom_id'])

			# 	# Compute based on pricetype
			# 	amount_unit = timesheet_obj.on_change_unit_amount(cr, uid, line_id.id,
			# 		prod_id=prod_id, company_id=False,
			# 		unit_amount=vals_line['unit_amount'], unit=False, journal_id=vals_line['journal_id'], context=context)

			# 	if amount_unit and 'amount' in amount_unit.get('value',{}):
			# 		vals_line['amount'] = amount_unit['value']['amount']

			if vals_line:
				work_order_obj.write(cr, uid, [line_id.id], vals_line, context=context)

		return super(project_task,self).write(cr, uid, ids, vals, context)

	def unlink(self, cr, uid, ids, *args, **kwargs):
		work_order_obj = self.pool.get('project.work.order')
		wo_ids = []
		for task in self.browse(cr, uid, ids):
			if task.work_order_id:
				wo_ids.append(task.work_order_id.id)
		# Delete entry from timesheet too while deleting entry to task.
		if wo_ids:
			work_order_obj.unlink(cr, uid, wo_ids, *args, **kwargs)
		return super(project_task,self).unlink(cr, uid, ids, *args, **kwargs)
	
	_columns={
		'work_order_id':fields.many2one('project.work.order','Related Work Order', ondelete='set null'),
	}
project_task()