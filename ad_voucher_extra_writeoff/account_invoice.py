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

	_columns = {
		"other_charge_lines"	: fields.one2many("account.voucher.writeoff",'invoice_related_id',"Charge Lines"),
	}

account_invoice()