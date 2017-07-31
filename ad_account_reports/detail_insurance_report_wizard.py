import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class detail_insurance_report_wizard(osv.osv_memory):
	_name = "detail.insurance.report.wizard"
	_columns = {
			"from_date" : fields.date("From Date"),
			"to_date" : fields.date("To Date"),
	}
	_defaults = {
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'detail.insurance.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'detail.insurance.report',
				'report_type': 'webkit',
				'datas': datas,
				}