from openerp.osv import fields, osv

from openerp.tools.translate import _

class stuffing_memo_onshipping(osv.osv_memory):

	_name = "stuffing.memo.onshipping"
	_description = "Stuffing Memo Onshipping"

	_columns = {
		'group': fields.boolean("Group by Schedule Date"),
		'creation_date': fields.date('Creation date'),
	}

	_defaults = {
		'group' : True,
	}

	# def view_init(self, cr, uid, fields_list, context=None):
	# 	if context is None:
	# 		context = {}
	# 	res = super(stuffing_memo_onshipping, self).view_init(cr, uid, fields_list, context=context)
	# 	pick_obj = self.pool.get('stock.picking')
	# 	count = 0
	# 	active_ids = context.get('active_ids',[])
	# 	for pick in pick_obj.browse(cr, uid, active_ids, context=context):
	# 		if pick.stuffing_id:
	# 			count += 1
	# 	if len(active_ids) == 1 and count:
	# 		raise osv.except_osv(_('Warning!'), _('This picking list does not require Stuffing Memo.'))
	# 	if len(active_ids) == count:
	# 		raise osv.except_osv(_('Warning!'), _('None of these picking lists require Stuffing Memo.'))
	# 	return res

	def open_stuffing_memo(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		stuffing_ids = []
		data_pool = self.pool.get('ir.model.data')
		res = self.create_stuffing_memo(cr, uid, ids, context=context)
		stuffing_ids += res.values()
		action_model = False
		action = {}
		if not stuffing_ids:
			raise osv.except_osv(_('Error!'), _('Please create Stuffing Memo.'))
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_container_booking', "action_stuffing_memo")
		if action_model:
			action_pool = self.pool.get(action_model)
			action = action_pool.read(cr, uid, action_id, context=context)
			action['domain'] = "[('id','in', ["+','.join(map(str,stuffing_ids))+"])]"
		return action

	def create_stuffing_memo(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		picking_pool = self.pool.get('stock.picking')
		onshipdata_obj = self.read(cr, uid, ids, ['group', 'creation_date'])
		context['creation_date'] = onshipdata_obj[0]['creation_date']
		active_ids = context.get('active_ids', [])
		res = picking_pool.action_stuffing_memo_create(cr, uid, active_ids,
			  group = onshipdata_obj[0]['group'],
			  context=context)
		return res

stuffing_memo_onshipping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
