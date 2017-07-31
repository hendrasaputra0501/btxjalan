from openerp.osv import fields,osv

class budget_forecast_mr(osv.Model):
	_name = "budget.forecast.mr"
	_rec_name ="analytic_account_id"
	_columns = {
		"mr_id"					: fields.many2one('material.request','Material Request',required=True,ondelete="cascade"),
		"analytic_account_id"	: fields.many2one('account.analytic.account','Analytic Account',required=True),
		"transaction_amount"	: fields.float("Current Transaction Amount"),
		"total_budget"			: fields.float("Total Budget"),
		"total_residual_budget"	: fields.float("Available Budget"),
		"forecast_amount"		: fields.float("Forecast Budget"),
		"forecast_amount_other"	: fields.float("Forecast Budget Extra"),
		"theoretical_amount"	: fields.float("Theoretical Amount"),
		"practical_amount"		: fields.float("Budget Spent"),
	}