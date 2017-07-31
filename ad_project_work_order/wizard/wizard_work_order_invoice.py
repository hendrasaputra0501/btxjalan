import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class wizard_work_order_invoice(osv.osv_memory):
	_name = "wizard.work.order.invoice"
	_columns = {
		'line_ids': fields.one2many('wizard.work.order.invoice.line', 'wizard_id', 'Work Orders', required=True),
		'date': fields.date('Invoice Date', required=True),
		'project_id': fields.many2one('project.project', 'Project Ref'),
	}

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = super(wizard_work_order_invoice, self).default_get(cr, uid, fields, context=context)
		wo_ids = context.get('active_ids', [])
		active_model = context.get('active_model')

		if not wo_ids:
			return res
		wo = self.pool.get('project.work.order').browse(cr, uid, wo_ids, context=context)
		if len(list(set([x.project_id for x in wo])))>1:
			# Hanya bisa membuat invoice dari satu Project yg sama
			return res
		assert active_model=='project.work.order', 'Bad context propagation'
		if 'project_id' in fields:
			res.update(project_id=wo[0].project_id.id)
		if 'line_ids' in fields:
			lines = []
			for line in wo:
				lines.append({
					'work_order_id': line.id,
					'name': line.name,
					'product_id' : line.product_id.id,
					'quantity' : 1.0,
					'uom_id' : False,
					'unit_price' : line.amount_subtotal or 0.0,
					})
			res.update(line_ids=lines)
		if 'date' in fields:
			res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
		return res

	def create_invoice(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		data =  self.browse(cr, uid, ids, context=context)[0]

		line_ids = data.line_ids
		project = data.project_id
		if not line_ids or not project:
			return {'type': 'ir.actions.act_window_close'}
		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		work_order_obj = self.pool.get('project.work.order')
		currency_obj = self.pool.get('res.currency')
		data_pool = self.pool.get('ir.model.data')

		if not project.is_work_order:
			return {'type': 'ir.actions.act_window_close'}
		
		partner = project.analytic_account_id.partner_id
		account_id = partner.property_account_payable.id
		journal_id = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'purchase')])
		invoice_vals = {
			'name': project.name,
			'origin': '',
			'type': 'in_invoice',
			'account_id': account_id,
			'partner_id': partner.id,
			'comment': '',
			'payment_term': False,
			'fiscal_position': False,
			'date_invoice': data.date,
			'company_id': project.company_id.id,
			'user_id': uid,
			'journal_id':journal_id and journal_id[0] or False,
			'currency_id' : project.currency_id.id,
		}

		invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
		for line in line_ids:
			if not line.unit_price:
				continue
			vals = {
				'name': line.name,
				'origin': '',
				'invoice_id': invoice_id,
				'uos_id': False,
				'product_id': line.product_id.id,
				'account_id': line.product_id.property_account_expense.id,
				'price_unit': line.unit_price,
				'quantity': 1.0,
				'work_order_id' : line.work_order_id.id, 
			}
			if vals:
				invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
				
		invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
				set_total=True)
		action_model = False
		action = {}
		invoice_ids = [invoice_id]
		if not invoice_ids:
			raise osv.except_osv(_('Error!'), _('Please create Invoices.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree2")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
		return action
		
wizard_work_order_invoice()


class wizard_work_order_invoice_line(osv.osv_memory):
	_name = "wizard.work.order.invoice.line"
	_columns = {
		'wizard_id': fields.many2one('wizard.work.order.invoice', 'Ref', ondelete='cascade', required=True, select="1"),
		'work_order_id': fields.many2one('project.work.order', 'Work Order', required=True),
		'name': fields.char('Work summary', size=128),
		'product_id' : fields.many2one('product.product', 'Product', domain=[('type','=','service')], required=True),
		'quantity' : fields.float('Quantity', digits_compute= dp.get_precision('Account')),
		'uom_id' : fields.many2one('product.uom', 'UoS'),
		'unit_price' : fields.float('Price Unit', digits_compute= dp.get_precision('Account')),
		# 'amount_subtotal' : fields.function(_get_amount_subtotal, type='float', digits_compute= dp.get_precision('Account'), string='Amount Subtotal'),
	}
wizard_work_order_invoice_line()