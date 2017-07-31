from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class res_company(osv.osv):
	_inherit = 'res.company'
	_columns = {
		'prefix_sequence_code': fields.char('Prefix Sequence Code', size=3,
			help='This will be use for define any prefix sequence code, s.a Sales Contract, Invoice, etc'),
		}
res_company()