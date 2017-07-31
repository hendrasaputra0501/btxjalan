import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class advance_payment(osv.Model):
	_inherit = "account.advance.payment"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC', readonly=True, states={'draft':[('readonly',False)]}),
	}

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(advance_payment, self).action_validate(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for advance in self.browse(cr, uid, ids, context=context):
			if advance.lc_id:
				lc_history_pool.create(cr, uid, {
					'lc_id' : advance.lc_id.id,
					'value_source':'account.advance.payment,%s'%advance.id,
					'name' : "%s Advance : %s"%((advance.type=='in' and 'Customer' or 'Supplier'),(advance.name or '')),
					})
		return res

	def action_cancel(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(advance_payment, self).action_cancel(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for advance in self.browse(cr, uid, ids, context=context):
			if advance.lc_id:
				value_source = 'account.advance.payment,%s'%advance.id
				lc_history_ids = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',advance.lc_id.id)])
				if lc_history_ids:
					lc_history_pool.unlink(cr, uid, lc_history_ids)
		return res