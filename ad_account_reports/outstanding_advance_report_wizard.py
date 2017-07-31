import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class outstanding_advance_report_wizard(osv.osv_memory):
	_name = "outstanding.advance.report.wizard"
	_columns = {
			"as_on_date" : fields.date('As On Date',required=True),
			# "journal_ids" : fields.many2many("account.journal","outstanding_advance_report_wizard_rel_journal","ageing_id","journal_id", "Filter Journals", domain=[('type','in',['sale','sale_refund','situation'])]),
			"account_ids" : fields.many2many("account.account","outstanding_advance_report_wizard_rel_account","ageing_id","account_id","Filter Accounts", domain=[('reconcile','=',True)]),
	}
	_defaults = {
		"as_on_date": lambda *a : time.strftime("%Y-%m-%d"),
		# "journal_ids" : lambda self,cr,uid,context=None:self.pool.get('account.journal').search(cr,uid,[('type','in',['sale','sale_refund'])],context=None),
		# "account_ids" : lambda self,cr,uid,context=None:self.pool.get('account.account').search(cr,uid,[('type','=','receivable')],context=None),
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'outstanding.advance.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'outstanding.advance.report',
				'report_type': 'webkit',
				'datas': datas,
				}