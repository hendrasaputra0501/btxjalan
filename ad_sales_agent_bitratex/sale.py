from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class sale(osv.osv):
	_inherit = "sale.order"
	_columns = {
		"agent_ids" : fields.one2many('sale.order.agent','sale_id','Agent(s)'),
	}