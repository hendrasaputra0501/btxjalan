import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class apvendor_report_wizard(osv.osv_memory):
	_name = "apvendor.report.wizard"
	_columns = {
			"filter" : fields.selection([('filter_no','No Filters'),('filter_date','Date'),('filter_period','Periods')], "Filter by", required=True),
			"from_date" : fields.date("From Date"),
			"to_date" : fields.date("To Date"),
			"period_from" : fields.many2one("account.period","Period From"),
			"period_to" : fields.many2one("account.period","Period To"),
			"journal_ids" : fields.many2many("account.journal","apvendor_report_wizard_rel_journal","wizard_id","journal_id", "Filter Journals", domain=[('type','in',['purchase','purchase_refund','situation'])]),
			"account_ids" : fields.many2many("account.account","apvendor_report_wizard_rel_account","wizard_id","account_id","Filter Accounts", domain=[('type','=','payable')]),
			"partner_ids" : fields.many2many("res.partner","apvendor_report_wizard_rel_partner","wizard_id","partner_id","Filter Partners", domain=[('supplier','=',True)]),
			"fiscalyear_id" : fields.many2one('account.fiscalyear','Fiscalyear'),
			# "show_outstanding_advance" : fields.boolean('Show Outstanding Advance?'),
			# "adv_account_id" : fields.many2one("account.account","Advance Account", domain=[('type','=','receivable')]),
			# "period_length" : fields.integer("Period Length (days)", required=True),
	}

	def _get_fiscalyear(self, cr, uid, context=None):
		if context is None:
			context = {}
		now = time.strftime('%Y-%m-%d')
		company_id = False
		ids = context.get('active_ids', [])
		company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
		domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
		fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
		return fiscalyears and fiscalyears[0] or False
	
	_defaults = {
		"filter" : lambda *f : 'filter_no',
		"fiscalyear_id" : _get_fiscalyear,
		# "journal_ids" : lambda self,cr,uid,context=None:self.pool.get('account.journal').search(cr,uid,[('type','in',['sale','sale_refund'])],context=None),
		# "account_ids" : lambda self,cr,uid,context=None:self.pool.get('account.account').search(cr,uid,[('type','=','receivable')],context=None),
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'apvendor.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'apvendor.report',
				'report_type': 'webkit',
				'datas': datas,
				}