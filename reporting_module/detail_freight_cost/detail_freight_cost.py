from openerp.osv import fields,osv
import datetime as dt
from openerp.tools.translate import _

class detail_freight_cost(osv.osv_memory):
	_name = "detail.freight.cost"
	_columns = {
		"filter_by"		: fields.selection([('dt',"Date Range"),('period',"Period")],"Filtered By",required=True),
		"period_id"		: fields.many2one("account.period","Period"),
		"date_start"	: fields.date("Start Date"),
		"date_stop"		: fields.date("End Date"),
		"outstanding"	: fields.boolean("Print only Outstanding"),
		"currency_filters" : fields.many2many("res.currency","currency_freight_cost_rel","detail_id","currency_id","Currencies to be filtered"),
	}
	def _get_current_period(self,cr,uid,context=None):
		if not context:
			context={'account_period_prefer_normal':True}
		period_id = self.pool.get('account.period').find(cr, uid, context=context)
		return period_id or False

	def _get_currencies_used(self,cr,uid,context=None):
		if not context:context={}
		user = self.pool.get("res.users").browse(cr,uid,uid,context=context)
		currencies = [user.company_id.currency_id.id, user.company_id.tax_base_currency.id]
		return currencies
	
	_defaults = {
		"filter_by" : lambda *a : "dt",
		"period_id"	: _get_current_period,
		"date_start": lambda *a: dt.date.today().strftime('%Y-%m-01'),
		"date_start": lambda *a: dt.date.today().strftime('%Y-%m-01'),
		"currency_filters" : _get_currencies_used,
	}

	def onchange_date(self,cr,uid,ids,date_start,date_stop,outstanding,context=None):
		if not context:context={}
		value = {}
		warning = False
		if not outstanding:
			if date_start and date_stop:
				ds1 = dt.datetime.strptime(date_start,"%Y-%m-%d")
				ds2 = dt.datetime.strptime(date_stop,"%Y-%m-%d")
				if ds2 < ds1 :
					value.update({'date_stop':False})
					warning = {
	 				'title': _('Warning!'),
					'message': _('Invalid Date Range. End Date must be bigger than Start Date !')
					}
				#raise osv.except_osv(_('Invalid Date Range !'), _("End Date must be bigger than Start Date !"))
				
		return {'value':value,'warning':warning}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		form_data=self.read(cr, uid, ids)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'detail.freight.cost',
			'form': form_data,
			}
		if not form_data['outstanding']:
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'detail.freight.cost.report',
					'report_type': 'webkit',
					'datas': datas,
					}
		else:
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'detail.outstanding.freight.cost.report',
					'report_type': 'webkit',
					'datas': datas,
					}
