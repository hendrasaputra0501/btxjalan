from openerp.osv import fields, osv

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class wizard_comm_open(osv.osv_memory):
	_name = "wizard.comm.open"

	_columns = {
	}

	def commission_open(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ai_pool = self.pool.get('account.invoice')
		
		active_ids = context.get('active_ids', [])
		if active_ids:
			ai_pool.action_commission_open(cr, uid, active_ids)
		return True

wizard_comm_open()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: