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
import logging
_logger = logging.getLogger(__name__)

class sale_order(osv.osv):
	_inherit = "sale.order"
	_columns = {
		'memo_ids' : fields.one2many('production.memo','sale_id','Production Memo',readonly=False),
	}
sale_order()
