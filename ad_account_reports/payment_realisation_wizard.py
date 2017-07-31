import time
from tools.translate import _
from osv import fields, osv

class payment_realisation_analysis_wizard(osv.osv_memory):
	_name = "payment.realisation.analysis.wizard"
	_columns = {
		"sale_type" : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"currency_id" : fields.many2one('res.currency',"Currency"),
		"filter" : fields.selection([('filter_no','No Filters'),('filter_date','Date'),('filter_period','Periods')], "Filter by", required=True),
		"from_date" : fields.date("From Date"),
		"to_date" : fields.date("To Date"),
		"period_id" : fields.many2one("account.period","Period"),
		# "account_ids" : fields.many2many("account.account","payment_real_wizard_rel_account","wizard_id","account_id","Filter Account"),
		# "journal_ids" : fields.many2many("account.journal","payment_real_wizard_rel_journal","wizard_id","journal_id", "Filter Journal"),
	}

	_defaults = {
		"sale_type" : lambda *s: 'local',
		"filter" : lambda *a: 'filter_no',
		# "journal_ids" : lambda self,cr,uid,context=None:self.pool.get('account.journal').search(cr,uid,[('type','in',['sale','sale_refund'])],context=None),
		# "account_ids" : lambda self,cr,uid,context=None:self.pool.get('account.account').search(cr,uid,[('type','=','receivable')],context=None),
	}

	def print_report(self, cr, uid, ids, context=None):
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'payment.realisation.analysis.wizard',
			'form': self.read(cr, uid, ids)[0],
		}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'payment.realisation.analysis',
				'report_type': 'webkit',
				'datas': datas,
				}
payment_realisation_analysis_wizard()

class sales_payment_realisation_wizard(osv.osv_memory):
	_name = "sales.payment.realisation.wizard"
	_columns = {
		"sale_type" : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"filter" : fields.selection([('filter_no','No Filters'),('filter_date','Date'),('filter_period','Periods')], "Filter by", required=True),
		"from_date" : fields.date("From Date"),
		"to_date" : fields.date("To Date"),
		"period_from" : fields.many2one("account.period","Period From"),
		"period_to" : fields.many2one("account.period","Period To"),
		"currency_id" : fields.many2one('res.currency',"Currency"),
		# "account_ids" : fields.many2many("account.account","payment_real_wizard_rel_account","wizard_id","account_id","Filter Account"),
		# "journal_ids" : fields.many2many("account.journal","payment_real_wizard_rel_journal","wizard_id","journal_id", "Filter Journal"),
	}

	_defaults = {
		"filter" : lambda *a: 'filter_no',
		# "journal_ids" : lambda self,cr,uid,context=None:self.pool.get('account.journal').search(cr,uid,[('type','in',['sale','sale_refund'])],context=None),
		# "account_ids" : lambda self,cr,uid,context=None:self.pool.get('account.account').search(cr,uid,[('type','=','receivable')],context=None),
	}

	def print_report(self, cr, uid, ids, context=None):
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'sales.payment.realisation.wizard',
			'form': self.read(cr, uid, ids)[0],
		}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'sales.payment.realisation.'+datas['form']['sale_type'],
				'report_type': 'webkit',
				'datas': datas,
				}


sales_payment_realisation_wizard()