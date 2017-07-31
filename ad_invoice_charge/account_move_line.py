from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta

class account_move_line(osv.Model):
	_inherit = "account.move.line"

	_columns = {
		"invoice_related_id"	: fields.many2one('account.invoice','Charge Related Invoice'),
	}