from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class sales_order_agent(osv.osv):
	_name = "sale.order.agent"
	_rec_name = "sale_line_id"
	_columns = {
		"sale_id" : fields.many2one('sale.order','Sale Order'),
		"sale_line_id" : fields.many2one('sale.order.line','Sale Order Line',required=True),
		"agent_id" : fields.many2one('res.partner','Agent',required=True),
		"partner_id" : fields.many2one('res.partner','Partner Company'),
		"invoice_partner_id" : fields.many2one('res.partner','Payment To', required=True),
		"commission_percentage" : fields.float('Commission Percentage',digits_compute=dp.get_precision('Commission Amount')),
	}
	
	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['sale_line_id'], context)
		res = []
		for record in reads:
			sale_line_id = record['sale_line_id'][0]
			sale_line = self.pool.get('sale.order.line').browse(cr, uid, sale_line_id)
			
			name = sale_line.sequence_line or str(record['id'])
			res.append((record['id'], name))
		return res

	def unlink(self, cr, uid, ids, context=None):
		aic_obj = self.pool.get('account.invoice.commission')
		aicl_obj = self.pool.get('account.invoice.commission.line')
		check = False
		for agent in self.browse(cr, uid, ids, context=context):
			aicl_ids = aicl_obj.search(cr, uid, [('sale_order_agent_id','=',agent.id)])
			if aicl_obj:
				for line in aicl_obj.browse(cr, uid, aicl_ids):
					if line.commission_id and line.commission_id.bill_ids:
						check = True
		if len(ids)==1 and check:
			raise osv.except_osv(_('Error, Deletion Abort!'),
					_('You cant delete this because this Commission have relation to Outstanding Commission in Invoice'))
		elif len(ids)>1 and check:
			raise osv.except_osv(_('Error, Deletion Abort!'),
					_('You cant delete these because these Commission has relation to Outstanding Commission in Invoice'))
		else:
			return super(sales_order_agent,self).unlink(cr, uid, ids, context=context)