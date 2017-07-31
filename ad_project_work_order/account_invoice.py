import time
import datetime

from openerp.osv import fields, osv
from openerp import pooler
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_invoice_line(osv.osv):
	_inherit = 'account.invoice.line'

	_columns = {
		"work_order_id" : fields.many2one('project.work.order','Related Work Order'),
	}
