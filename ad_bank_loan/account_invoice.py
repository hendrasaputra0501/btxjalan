from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):
	_inherit = "account.invoice"

	def _get_bank_loan(self, cr, uid, ids, context=None):
		res = []
		for r in self.pool.get('account.bank.loan').browse(cr, uid, ids, context=context):
			if r.loan_type=='nego' and r.state in ('open','paid') and r.invoice_related_id and r.invoice_related_id.id not in res:
				res.append(r.invoice_related_id.id)
		return res

	def _get_bank_negotiation(self, cr, uid, ids, name, args, context=None):
		bank_loan_pool = self.pool.get('account.bank.loan')
		res = {}
		for invoice in self.browse(cr, uid, ids, context=context):
			res[invoice.id] ={
				'bank_negotiation_no' : False,
				'bank_negotiation_date' : False,
			}
			bnego_ids = bank_loan_pool.search(cr, uid, [('invoice_related_id','=',invoice.id)])
			if bnego_ids:
				bnego = bank_loan_pool.browse(cr, uid, bnego_ids[0])
				res[invoice.id]['bank_negotiation_no'] = bnego.id
				res[invoice.id]['bank_negotiation_date'] = bnego.effective_date!=False and bnego.effective_date or bnego.date_request or False
		return res

	_columns = {
		'bank_negotiation_no' : fields.function(_get_bank_negotiation, type="many2one", obj="account.bank.loan", string="Bank Negotitation No",
			store={
				'account.bank.loan' : (_get_bank_loan, ['invoice_related_id','state'], 10),
			}, method=True, multi="all_get_nego"
			),
		'bank_negotiation_date' : fields.function(_get_bank_negotiation, type="date", string="Bank Negotitation Date",
			store={
				'account.bank.loan' : (_get_bank_loan, ['invoice_related_id','state'], 10),
			}, method=True, multi="all_get_nego"
			),
		}

account_invoice()