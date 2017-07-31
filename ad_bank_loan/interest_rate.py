from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta


class account_interest(osv.osv):
	_name = "account.interest"

	_columns = {
		"type" : fields.selection([('global_rate','Global Rate'),('nego','Invoice Negotiation Interest'),('tr','Transfer Receipt Interest'),('others','Others')],"Type"),
		"sale_type" : fields.selection([('export','Export'),('local','Local')],"Sale Type"),
		"bank_id" : fields.many2one("res.bank","Bank"),
		"rate_ids" : fields.one2many("account.interest.rate","interest_id","Interest Rate"),
		"journal_id" : fields.many2one("account.journal","Bank Journal"),
	}

	def _get_rate(self, cr, uid, bank_id=False, context=None):
		if context is None:
			context = {}
		#process the case where the account doesn't work with an outgoing currency rate method 'at date' but 'average'
		interest_rate_pool = self.pool.get('account.interest.rate')
		interest_ids = []
		if bank_id:
			interest_ids = self.search(cr, uid, [('bank_id','=',bank_id)], context=context)
		else:
			interest_ids = self.search(cr, uid, [('type','=','global_rate')], context=context)

		if interest_ids:
			rate_ids = interest_rate_pool.search(cr, uid, [('interest_id','=',interest_ids[0]),('date_from','<=',context.get('date',datetime.date.today().strftime('%Y-%m-%d')))], context=context)
			if rate_ids:
				rate = interest_rate_pool.browse(cr, uid, rate_ids, context=context)[0].rate
				return rate
			else:
				raise osv.except_osv(_('Warning!'), _('Please Insert Interest Rate Masters'))
		else:
			raise osv.except_osv(_('Warning!'), _('Please Insert Interest Masters'))

account_interest()

class account_interest_rate(osv.osv):
	_name = "account.interest.rate"

	_columns = {
		"interest_id" : fields.many2one("account.interest","Interest"),
		"rate" : fields.float("Rate", digits=(2,5)),
		"date_from" : fields.date("Valid From", required=True),
		"date_to" : fields.date("Valid To"),
	}

	_order = "id desc"
account_interest_rate()