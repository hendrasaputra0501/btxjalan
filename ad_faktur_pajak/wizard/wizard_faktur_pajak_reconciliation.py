import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class wizard_faktur_pajak_reconciliation(osv.osv_memory):

	_name = "wizard.faktur.pajak.reconciliation"
	_columns = {
			# "start_date"        : fields.date('Start Date'),
			# "end_date"          : fields.date('End Date'),
			'fiscalyear_id'		: fields.many2one('account.fiscalyear', 'Fiscalyear', required=True),
			'period_id'			: fields.many2one('account.period', 'PPN Masa', required=True),
	}

	def _get_fiscalyear(self, cr, uid, context=None):
		if context is None:
			context = {}
		now = time.strftime('%Y-%m-%d')
		company_id = False
		ids = context.get('active_ids', [])
		if ids and context.get('active_model') == 'account.account':
			company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
		else:  # use current company id
			company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
		domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
		fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
		return fiscalyears and fiscalyears[0] or False

	
	_defaults = {
		# "start_date": lambda *a:time.strftime("%Y-%m-01"),
		# "end_date" : lambda *a:time.strftime("%Y-%m-%d"),
		"fiscalyear_id" : _get_fiscalyear,
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'advance.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'faktur.pajak.reconciliation',
				'report_type': 'webkit',
				'datas': datas,
				}

wizard_faktur_pajak_reconciliation()