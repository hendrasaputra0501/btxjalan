from openerp.osv import fields, osv

from openerp.tools.translate import _

class wizard_lifton_charge_onshipment(osv.osv_memory):
	def _get_currency_idr(self, cr, uid, context=None):
		if context is None:
			context = {}
		curr_ids = self.pool.get('res.currency').search(cr, uid, [('name','=','IDR')], context=context)
		if curr_ids:
			curr_idr = self.pool.get('res.currency').browse(cr, uid, curr_ids, context=context)[0].id
			return curr_idr
		else:
			return False
	
	def _get_journal(self, cr, uid, context=None):
		journal_obj = self.pool.get('account.journal')
		journal_type = ['bank','cash']
		idr_value = journal_obj.search(cr, uid, [('type', 'in',journal_type ),('currency.name','=','IDR')])
		journal_id = len(idr_value)>=1 and idr_value[0] or False
		res = self._get_journal_id(cr, uid, context=context)
		for x in res:
			if journal_id == x[0]:
				return x
		
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
				journal_type = ['bank','cash']
			elif type == 'out' and dest_usage == 'customer':
				# journal_type = 'sale'
				journal_type = ['bank','cash']
			elif type == 'in' and src_usage == 'supplier':
				journal_type = ['bank','cash']
			elif type == 'in' and src_usage == 'customer':
				# journal_type = 'sale_refund'
				journal_type = ['bank','cash']
			else:
				journal_type = ['bank','cash']

			value = journal_obj.search(cr, uid, [('type', 'in',journal_type )])
			for jr_type in journal_obj.browse(cr, uid, value, context=context):
				currency = jr_type.currency and '('+jr_type.currency.name+')' or '('+jr_type.company_id.currency_id.name+')'
				t1 = jr_type.id,jr_type.name+currency
				if t1 not in vals:
					vals.append(t1)
		return vals


	_name = "wizard.lifton.charge.onshipment"
	_description = "Wizard Lifton Charge OnShipment"

	_columns = {
		'journal_id': fields.selection(_get_journal_id, 'Destination Journal',required=True),
		'currency_id' : fields.many2one('res.currency','Currency',required=False),
		'bpa_date': fields.date('BPA Request Date', required=True),
		'due_date': fields.date('BPA Due Date'),
		'number' : fields.char("BPA Number", size=64),
	}

	_defaults = {
		'journal_id' : _get_journal,
		'currency_id' : _get_currency_idr,
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(wizard_lifton_charge_onshipment, self).view_init(cr, uid, fields_list, context=context)
		pick_obj = self.pool.get('stock.picking')
		count = 0
		active_ids = context.get('active_ids',[])
		for pick in pick_obj.browse(cr, uid, active_ids, context=context):
			if pick.lifton_bpa_id:
				count += 1

			if pick.state != 'done':
				raise osv.except_osv(_('Warning!'), _('Delivery Order not transfered yet'))
				
		# if len(active_ids) == 1 and count:
		# 	raise osv.except_osv(_('Warning!'), _('This picking list does not require Lift On BPA.'))
		# if len(active_ids) == count:
		# 	raise osv.except_osv(_('Warning!'), _('None of these picking lists require Lift On BPA.'))
		return res

	def open_lifton_bpa(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		bpa_ids = []
		data_pool = self.pool.get('ir.model.data')
		res = self.create_lifton_bpa(cr, uid, ids, context=context)
		bpa_ids += res.values()
		action_model = False
		action = {}
		if not bpa_ids:
			raise osv.except_osv(_('Error!'), _('Please create Lift On Lift Off BPA.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_ext_transaksi', "action_bpa")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,bpa_ids))+"])]"
		return action

	def create_lifton_bpa(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		picking_pool = self.pool.get('stock.picking')
		onshipdata_obj = self.read(cr, uid, ids, ['journal_id', 'group', 'bpa_date','due_date', 'currency_id','number'])
		# onshipdata_obj = self.read(cr, uid, ids, ['journal_id', 'group', 'bpa_date'])
		context['bpa_date'] = onshipdata_obj[0]['bpa_date']
		context['due_date'] = onshipdata_obj[0]['due_date']
		context['number'] = onshipdata_obj[0]['number']
		context['currency_id'] = onshipdata_obj[0]['currency_id'][0]
		active_ids = context.get('active_ids', [])
		if isinstance(onshipdata_obj[0]['journal_id'], tuple):
			onshipdata_obj[0]['journal_id'] = onshipdata_obj[0]['journal_id'][0]
		res = picking_pool.action_lifton_bpa_create(cr, uid, active_ids,
			  journal_id = onshipdata_obj[0]['journal_id'],
			  context=context)
		return res

wizard_lifton_charge_onshipment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
