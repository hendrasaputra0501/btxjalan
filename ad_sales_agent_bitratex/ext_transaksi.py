import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools

class ext_transaksi_line(osv.osv):
	_inherit = "ext.transaksi.line"
	
	_columns = {
		'commission_id' : fields.many2one('account.invoice.commission','Related Commission'),
		'state' : fields.related('ext_transaksi_id','state',type='selection', selection=[('draft','Draft'), ('posted','Posted')], string='State', readonly=True),
		'transaction_date' : fields.related('ext_transaksi_id','date',type='date', string='Posted Date', readonly=True),
		'parent_currency_id': fields.related('ext_transaksi_id','currency_id', type='many2one', relation='res.currency', string='Currency', readonly=True),
	}
	
	