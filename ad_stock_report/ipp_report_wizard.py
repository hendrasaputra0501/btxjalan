from openerp.osv import fields,osv
import datetime

class ipp_wizard(osv.osv_memory):
	_name = "ipp.wizard"
	_columns = {
		'filter'			: fields.selection([('date','Date'),('period','Period')],"Filter",required=True),
		'date_start'		: fields.date('Start Date'),
		'date_end'			: fields.date('End Date'),
		'period_id'			: fields.many2one('account.period',"Period"),
		'sub_account_ids'	: fields.many2many('account.analytic.account', 'ipp_wiz_aaa', 'wiz_id', 'aaa_id', 'Sub Account', 
							domain=[('type','=','normal')],required=True),
	}

	def _get_date_start(self,cr,uid,context=None):
		if not context:context={}
		today = datetime.date.today()
		first = today.replace(day=1)
		lastMonth = first - datetime.timedelta(days=1)
		lastMonthfirst =lastMonth.replace(day=1)
		return lastMonthfirst.strftime("%Y-%m-%d")

	def _get_date_end(self,cr,uid,context=None):
		if not context:context={}
		today = datetime.date.today()
		first = today.replace(day=1)
		lastMonth = first - datetime.timedelta(days=1)
		return lastMonth.strftime("%Y-%m-%d")

	def _get_period(self,cr,uid,context=None):
		if not context:context={}
		lastMonthfirst = self._get_date_end(cr,uid,context=context)
		context.update({'account_period_prefer_normal':True})
		period_id = self.pool.get('account.period').find(cr, uid, dt=lastMonthfirst, context=context)
		try:
			period_id=period_id[0]
		except:
			period_id=period_id
		return period_id

	_defaults = {
		'filter'		: lambda *a :'period',
		'date_start'	: _get_date_start,
		'date_end'		: _get_date_end,
		'period_id'		: _get_period,
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'ipp.wizard',
			'filter':wizard.filter,
			'period_id': wizard.filter=='period' and wizard.period_id and wizard.period_id.id or False,
			'date_start': wizard.filter =='date' and wizard.date_start or False,
			'date_end': wizard.filter =='date' and wizard.date_end or False,
			'sub_account_ids':[x.id for x in wizard.sub_account_ids],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'ipp.report.xls',
				'report_type': 'webkit',
				'datas': datas,
				}