

import time
import netsvc
# from report import report_sxw
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
# from report import report_sxw
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class outstanding_commision_wizard(osv.osv_memory):
	_name = "outstanding.commision.wizard"
	_columns = {
		"as_on"             : fields.date('As on',required=True),
		"sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"fiscalyear_id"     : fields.many2one('account.fiscalyear','Fiscal Year'),
		"company_id"        : fields.many2one('res.company','Company'),
	} 
	_defaults = {
		"as_on"     : time.strftime("%Y-%m-%d"),
		"sale_type" : "export",
        "company_id" : lambda self, cr, uid, context : self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
		'ids': context.get('active_ids',[]),
		'model': 'outstanding.commision.wizard',
		'form': self.read(cr, uid, ids)[0],
		}
		return {
		'type': 'ir.actions.report.xml',
		'report_name': 'outstanding.commision.report',
		'report_type': 'webkit',
		'datas': datas,
		}
		outstanding_commision_wizard()