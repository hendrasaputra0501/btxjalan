from openerp.osv import fields, osv
import time
from tools.translate import _

class wizard_set_picking_related(osv.TransientModel):
	_name = "wizard.set.picking.related"
	_columns = {
		'picking_related_id':fields.many2one("stock.picking","Related Picking",required=False),
	}

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		# no call to super!
		res = {}
		line_id = context.get('active_id', [])
		if not line_id or not context.get('active_model') == 'ext.transaksi.line':
			return res
		if 'picking_related_id' in fields:
			line = self.pool.get('ext.transaksi.line').browse(cr, uid, line_id, context=context)
			res.update(desc=line.picking_related_id and line.picking_related_id.id or False)
		return res
	
	def set_picking_related_id(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		pool_obj = self.pool.get('ext.transaksi.line')
		datas = self.browse(cr, uid, ids[0], context=context)
		picking_related_id = datas.picking_related_id and datas.picking_related_id.id or False
		pool_obj.write(cr, uid, context['active_ids'], {'picking_related_id':picking_related_id}, context=context)
		return {'type': 'ir.actions.act_window_close'}

wizard_set_picking_related()