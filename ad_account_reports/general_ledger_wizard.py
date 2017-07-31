import time
from tools.translate import _
from osv import fields, osv

class general_ledger_wizard(osv.osv_memory):
	_name = "general.ledger.wizard"
	_columns = {
		"filter" : fields.selection([('filter_no','No Filters'),('filter_date','Date'),('filter_period','Periods')], "Filter by", required=True),
		"from_date" : fields.date("From Date"),
		"to_date" : fields.date("To Date"),
		"period_id" : fields.many2one("account.period","Period"),
		"fiscalyear_id" : fields.many2one('account.fiscalyear','Fiscalyear'),
		
		"account_ids" : fields.many2many("account.account","gl_wizard_rel_account","wizard_id","account_id","Filter Accounts",domain=[('type','!=','view')]),
		"journal_ids" : fields.many2many("account.journal","gl_wizard_rel_journal","wizard_id","journal_id", "Filter Journals"),
		"partner_ids" : fields.many2many("res.partner","gl_wizard_rel_partner","wizard_id","partner_id","Filter Partners",),
		"sort_by" : fields.selection([('date','Date'),('journa_and_partner','Journal a& Partner')], "Sort By"),
		"init_balance" : fields.boolean('Show Initial Balance? '),
		"show_analytic_account" : fields.boolean('Show Analytic Accounts? '),
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
		"filter" : lambda *a: 'filter_no',
		"fiscalyear_id" : _get_fiscalyear,
	}



	def print_report(self, cr, uid, ids, context=None):
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'general.ledger.wizard',
			'form': self.read(cr, uid, ids)[0],
		}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'general.ledger.bitratex.xls',
				'report_type': 'webkit',
				'datas': datas,
				}

general_ledger_wizard()