import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class ext_transaksi(osv.Model):
	_inherit = "ext.transaksi"

	def posted_action(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(ext_transaksi, self).posted_action(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for ext_pay in self.browse(cr, uid, ids, context=context):
			for line in ext_pay.ext_line:
				if line.lc_id:
					lc_history_pool.create(cr, uid, {
						'lc_id' : line.lc_id.id,
						'value_source':'ext.transaksi.line,%s'%line.id,
						'name' : "%s : %s"%(ext_pay.type_transaction=='receipt' and 'Extra Receipt' or (ext_pay.type_transaction=='payment' and 'Extra Payment' or 'Journal Voucher'),(line.name or '')),
						})
		return res

	def cancel_transaction(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(ext_transaksi, self).cancel_transaction(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for ext_pay in self.browse(cr, uid, ids, context=context):
			for line in ext_pay.ext_line:
				if line.lc_id:
					value_source = 'ext.transaksi.line,%s'%line.id
					lc_history_ids = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',line.lc_id.id)])
					if lc_history_ids:
						lc_history_pool.unlink(cr, uid, lc_history_ids)
		return res

class ext_transaksi_line(osv.Model):
	_inherit = "ext.transaksi.line"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC'),
	}