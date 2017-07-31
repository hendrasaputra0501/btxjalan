from openerp.osv import fields, osv

from openerp.tools.translate import _

class stock_move_set_location(osv.osv_memory):
	_name = "stock.move.set.location"
	
	_columns = {
		'default_location_id':fields.many2one('stock.location','Set Default Source Location'),
		'default_dest_location_id':fields.many2one('stock.location','Set Default Destination Location'),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(stock_move_set_location, self).view_init(cr, uid, fields_list, context=context)
		move_pool = self.pool.get('stock.move')
		count = 0
		active_ids = context.get('active_ids',[])
		for inv in move_pool.browse(cr, uid, active_ids, context=context):
			if inv.state not in ('draft','confirmed'):
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This Move was not in draft or confirmed state'))
		if count>1:
			raise osv.except_osv(_('Warning!'), _('None of these Moves was in draft or confirmed state'))
		return res

	def set_location(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('stock.move')
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['default_location_id','default_dest_location_id'])
		update_val = {}
		if data[0]['default_location_id']:
			update_val.update({'location_id':data[0]['default_location_id'][0]})
		if data[0]['default_dest_location_id']:
			update_val.update({'location_dest_id':data[0]['default_dest_location_id'][0]})
		move_pool.write(cr, uid, active_ids, update_val)
		return True

stock_move_set_location()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: