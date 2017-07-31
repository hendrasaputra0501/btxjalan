from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class stock_incoterms(osv.osv):
	_inherit = 'stock.incoterms'

	_columns = {
		'fob_compute' : fields.text('FOB Compute'),
	}

	_defaults = {
		'fob_compute' : '''# total_freight : total freight that related to its shipment\n# total_insurance : total insurance that related to its shipment\n# amount_invoice : total invoice of its shipment\n\nresult = amount_invoice - total_freight - total_insurance''',
 	}