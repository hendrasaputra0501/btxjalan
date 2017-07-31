from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta

class account_voucher_writeoff(osv.Model):
	_inherit = "account.voucher.writeoff"
	_columns = {
		"interest_id" : fields.many2one("account.bank.loan.interest","Interest",ondelete="cascade"),
	}