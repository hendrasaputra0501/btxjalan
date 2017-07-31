import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class account_invoice(osv.Model):
	_inherit = "account.invoice"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC', readonly=True, states={'draft':[('readonly',False)],'proforma2':[('readonly',False)]}),
	}

	def invoice_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for invoice in self.browse(cr, uid, ids, context=context):
			if invoice.charge_type:
				for line in invoice.invoice_line:
					if line.lc_id:
						lc_history_pool.create(cr, uid, {
							'lc_id' : line.lc_id.id,
							'value_source':'account.invoice.line,%s'%line.id,
							'name' : "%s : %s"%('Invoice Charge',(line.name or '')),
							})
			else:
				if invoice.lc_id:
					lc_history_pool.create(cr, uid, {
						'lc_id' : invoice.lc_id.id,
						'value_source':'account.invoice,%s'%invoice.id,
						'name' : "%s : %s"%((invoice.type=='in_invoice' and 'Supplier Invoice' or 'Customer Invoice'),(invoice.internal_number or '')),
						})
		return res

	def action_cancel(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for invoice in self.browse(cr, uid, ids, context=context):
			if invoice.lc_id:
				value_source = 'account.invoice,%s'%invoice.id
				lc_history_ids1 = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',invoice.lc_id.id)])
				if lc_history_ids1:
					lc_history_pool.unlink(cr, uid, lc_history_ids1)
			for line in invoice.invoice_line:
				if line.lc_id:
					value_source = 'account.invoice.line,%s'%line.id
					lc_history_ids2 = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',line.lc_id.id)])
					if lc_history_ids2:
						lc_history_pool.unlink(cr, uid, lc_history_ids2)
		return res

class account_invoice_line(osv.Model):
	_inherit = "account.invoice.line"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC', readonly=True, states={'draft':[('readonly',False)]}),
	}