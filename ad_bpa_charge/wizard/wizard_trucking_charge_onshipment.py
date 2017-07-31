from openerp.osv import fields, osv

from openerp.tools.translate import _

class wizard_trucking_charge_onshipment(osv.osv_memory):
	def _get_currency_idr(self, cr, uid, context=None):
		if context is None:
			context = {}
		curr_ids = self.pool.get('res.currency').search(cr, uid, [('name','=','IDR')], context=context)
		if curr_ids:
			curr_idr = self.pool.get('res.currency').browse(cr, uid, curr_ids, context=context)[0].id
			return curr_ids
		else:
			return False

	def _get_journal(self, cr, uid, context=None):
		res = self._get_journal_id(cr, uid, context=context)
		if res:
			return res[0][0]
		return False

	def _get_journal_id(self, cr, uid, context=None):
		if context is None:
			context = {}

		model = context.get('active_model')
		if not model or 'stock.picking' not in model:
			return []

		model_pool = self.pool.get(model)
		journal_obj = self.pool.get('account.journal')
		res_ids = context and context.get('active_ids', [])
		vals = []
		browse_picking = model_pool.browse(cr, uid, res_ids, context=context)

		for pick in browse_picking:
			if not pick.move_lines:
				continue
			src_usage = pick.move_lines[0].location_id.usage
			dest_usage = pick.move_lines[0].location_dest_id.usage
			type = pick.type
			if type == 'out' and dest_usage == 'supplier':
				# journal_type = 'purchase_refund'
				journal_type = 'purchase'
			elif type == 'out' and dest_usage == 'customer':
				# journal_type = 'sale'
				journal_type = 'purchase'
			elif type == 'in' and src_usage == 'supplier':
				journal_type = 'purchase'
			elif type == 'in' and src_usage == 'customer':
				# journal_type = 'sale_refund'
				journal_type = 'purchase'
			else:
				journal_type = 'purchase'

			value = journal_obj.search(cr, uid, [('type', '=',journal_type )])
			for jr_type in journal_obj.browse(cr, uid, value, context=context):
				t1 = jr_type.id,jr_type.name
				if t1 not in vals:
					vals.append(t1)
		return vals


	_name = "wizard.trucking.charge.onshipment"
	_description = "Wizard Trucking Charge OnShipment"

	_columns = {
		'journal_id': fields.selection(_get_journal_id, 'Destination Journal',required=True),
		'group': fields.boolean("Group by Partner"),
		'currency_id' : fields.many2one('res.currency','Currency',required=True),
		'invoice_date': fields.date('Invoice date', required=True),
		'number' : fields.char("BPA Number", size=64),
	}

	_defaults = {
		'group' : True,
		'currency_id' : _get_currency_idr,
		# 'currency_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr,uid,uid,c).company_id.currency_id.id, 
		'journal_id' : _get_journal,
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(wizard_trucking_charge_onshipment, self).view_init(cr, uid, fields_list, context=context)
		pick_obj = self.pool.get('stock.picking')
		count = 0
		active_ids = context.get('active_ids',[])
		if not context.get('transport_less_load',False) and not context.get('dispensation',False):
			for pick in pick_obj.browse(cr, uid, active_ids, context=context):
				# if pick.trucking_invoice_id:
				# 	count += 1

				if pick.state != 'done':
					raise osv.except_osv(_('Warning!'), _('Delivery Order not transfered yet'))	

				if not pick.trucking_charge:
					raise osv.except_osv(_('Warning!'), _('Please Define Trucking Charge'))	
			# if len(active_ids) == 1 and count:
			# 	raise osv.except_osv(_('Warning!'), _('This picking list does not require trucking Invoice.'))
			# if len(active_ids) == count:
			# 	raise osv.except_osv(_('Warning!'), _('None of these picking lists require trucking Invoice.'))
		return res

	def open_trucking_invoice(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		invoice_ids = []
		data_pool = self.pool.get('ir.model.data')
		res = self.create_trucking_invoice(cr, uid, ids, context=context)
		invoice_ids += res.values()
		action_model = False
		action = {}
		if not invoice_ids:
			raise osv.except_osv(_('Error!'), _('Please create trucking Invoice.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_invoice_charge', "action_invoice_charge")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
		return action

	def create_trucking_invoice(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		picking_pool = self.pool.get('stock.picking')
		onshipdata_obj = self.read(cr, uid, ids, ['journal_id', 'group', 'invoice_date', 'currency_id','number'])
		context['date_inv'] = onshipdata_obj[0]['invoice_date']
		context['currency_id'] = onshipdata_obj[0]['currency_id'][0]
		context['number'] = onshipdata_obj[0]['number']
		active_ids = context.get('active_ids', [])
		if isinstance(onshipdata_obj[0]['journal_id'], tuple):
			onshipdata_obj[0]['journal_id'] = onshipdata_obj[0]['journal_id'][0]
		if context.get('transport',False) or context.get('transport_less_load',False) or context.get('dispensation',False):
			res = picking_pool.action_transport_invoice_create(cr, uid, active_ids,
				journal_id = onshipdata_obj[0]['journal_id'],
				group = onshipdata_obj[0]['group'],
				context=context)
		else:
			res = picking_pool.action_trucking_invoice_create(cr, uid, active_ids,
				journal_id = onshipdata_obj[0]['journal_id'],
				group = onshipdata_obj[0]['group'],
				context=context)
		return res

wizard_trucking_charge_onshipment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
