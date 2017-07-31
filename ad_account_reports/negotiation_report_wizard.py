import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class negotiation_report_wizard(osv.osv_memory):
	_name = "negotiation.report.wizard"
	_columns = {
			"report_type" : fields.selection([('nego','Negotiation Statement Report'),('liabnego','Negotation Liability Report'),('negopaid','Negotation Paid Report')], "Report Name"),
			"as_on" : fields.date('As On Date'),
			"start_date" : fields.date('Start Date'),
			"end_date" : fields.date('End Date'),
	}
	_defaults = {
		"report_type": lambda *r: "nego",
		"as_on": lambda *a : time.strftime("%Y-%m-%d"),
		"start_date": lambda *a : time.strftime("%Y-%m-01"),
		"end_date": lambda *a : time.strftime("%Y-%m-%d"),
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'negotiation.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': datas['form']['report_type']+'.report',
				'report_type': 'webkit',
				'datas': datas,
				}