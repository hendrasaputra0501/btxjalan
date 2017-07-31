import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class aging_report_wizard(osv.osv_memory):
	_name = "aging.report.wizard"
	_columns = {
			"account_type" : fields.selection([('receivable','Account Receivable'), ('payable','Account Payable')],"Account Type",required=True),
			"as_on_date" : fields.date('As On Date',required=True),
			"journal_ids" : fields.many2many("account.journal","aging_report_wizard_rel_journal","ageing_id","journal_id", "Filter Journals"),
			"account_ids" : fields.many2many("account.account","aging_report_wizard_rel_account","ageing_id","account_id","Filter Accounts"),
			"show_outstanding_advance" : fields.boolean('Show Outstanding Advance?'),
			"adv_account_id" : fields.many2one("account.account","Advance Account", domain=[('type','=','receivable')]),
			"period_length" : fields.integer("Period Length (days)", required=True),
			"partner_ids" : fields.many2many("res.partner","aging_report_wizard_rel_partner","wizard_id","partner_id","Filter Partners",),
	}
	_defaults = {
		"account_type" : lambda self, cr, uid, context:context.get('account_type','receivable'),
		"as_on_date": lambda *a : time.strftime("%Y-%m-%d"),
		"period_length": lambda *n : 10,
	}

	def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
		if context is None: context = {}
		res = super(aging_report_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		for field in res['fields']:
			if field=='journal_ids':
				if context.get('account_type',False) and context.get('account_type',False) == 'receivable':
					res['fields'][field]['domain'] = [('type','in',['sale','sale_refund','situation'])]
				if context.get('account_type',False) and context.get('account_type',False) == 'payable':
					res['fields'][field]['domain'] = [('type','in',['purchase','purchase_refund','situation','general'])]
		return res

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'aging.report.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'aging.report',
				'report_type': 'webkit',
				'datas': datas,
				}