from openerp.osv import fields, osv
import time
from tools.translate import _

class internal_remark_wizard(osv.TransientModel):
	_name = "internal.remark.wizard"
	_columns = {
		'remark':fields.text("Internal Remarks"),
	}
	
	def set_internal_remark(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('sale.order.line')
		internal_remark = self.browse(cr, uid, ids[0], context=context).remark or ''
		pool_obj.write(cr, uid, context['active_ids'], {'other_description':internal_remark}, context=context)
		return {'type': 'ir.actions.act_window_close'}

internal_remark_wizard()

class eff_rate_wizard(osv.TransientModel):
	_name = "efisiensi.rate.wizard"
	_columns = {
		'rate' : fields.float('Efisiensi Rate'),
	}
	
	def set_eff_rate(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('sale.order.line')
		rate = self.browse(cr, uid, ids[0], context=context).rate or ''
		pool_obj.write(cr, uid, context['active_ids'], {'efisiensi_rate':rate}, context=context)
		return {'type': 'ir.actions.act_window_close'}

eff_rate_wizard()

class order_state_wizard(osv.TransientModel):
	_name = "order.state.wizard"
	_columns = {
		'order_state' : fields.selection([('hold','Hold'),('doubtful','Doubtful'),('cancel','Cancel'),('active','Active')],"Order State",required=True),
	}

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = {}
		line_id = context.get('active_id', [])
		if not line_id or not context.get('active_model') == 'sale.order.line':
			return res
		if 'order_state' in fields:
			line = self.pool.get('sale.order.line').browse(cr, uid, line_id, context=context)
			res.update(order_state=line.order_state)
		return res
	
	def set_order_state(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('sale.order.line')
		order_state = self.browse(cr, uid, ids[0], context=context).order_state or ''
		pool_obj.write(cr, uid, context['active_ids'], {'order_state':order_state}, context=context)
		return {'type': 'ir.actions.act_window_close'}

order_state_wizard()

class reschedule_date_wizard(osv.TransientModel):
	_name = "reschedule.date.wizard"
	_columns = {
		'reschedule_date':fields.date("Reschedule Date"),
	}
	
	def set_reschedule_date(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('sale.order.line')
		reschedule_date = self.browse(cr, uid, ids[0], context=context).reschedule_date or ''
		pool_obj.write(cr, uid, context['active_ids'], {'reschedule_date':reschedule_date}, context=context)
		return {'type': 'ir.actions.act_window_close'}

reschedule_date_wizard()

