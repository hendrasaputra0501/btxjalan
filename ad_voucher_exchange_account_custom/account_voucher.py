import time
from lxml import etree

from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw

class res_company(osv.osv):
	_inherit = "res.company"
	_columns = {
		'income_receivable_currency_exchange_account_id': fields.many2one(
			'account.account',
			string="Gain Exchange Rate Account for AR Transaction",
			domain="[('type', '=', 'other')]",),
		'expense_receivable_currency_exchange_account_id': fields.many2one(
			'account.account',
			string="Loss Exchange Rate Account for AR Transaction",
			domain="[('type', '=', 'other')]",),
		'income_payable_currency_exchange_account_id': fields.many2one(
			'account.account',
			string="Gain Exchange Rate Account for AP Transaction",
			domain="[('type', '=', 'other')]",),
		'expense_payable_currency_exchange_account_id': fields.many2one(
			'account.account',
			string="Loss Exchange Rate Account for AP Transaction",
			domain="[('type', '=', 'other')]",),
	}

res_company()

class account_config_settings(osv.osv_memory):
	_inherit = 'account.config.settings'
	_columns = {
		'income_receivable_currency_exchange_account_id': fields.related(
			'company_id', 'income_receivable_currency_exchange_account_id',
			type='many2one',
			relation='account.account',
			string="Gain Exchange Rate Account for AR Transaction", 
			domain="[('type', '=', 'other')]"),
		'expense_receivable_currency_exchange_account_id': fields.related(
			'company_id', 'expense_receivable_currency_exchange_account_id',
			type="many2one",
			relation='account.account',
			string="Loss Exchange Rate Account for AR Transaction",
			domain="[('type', '=', 'other')]"),
		'income_payable_currency_exchange_account_id': fields.related(
			'company_id', 'income_payable_currency_exchange_account_id',
			type='many2one',
			relation='account.account',
			string="Gain Exchange Rate Account for AP Transaction", 
			domain="[('type', '=', 'other')]"),
		'expense_payable_currency_exchange_account_id': fields.related(
			'company_id', 'expense_payable_currency_exchange_account_id',
			type="many2one",
			relation='account.account',
			string="Loss Exchange Rate Account for AP Transaction",
			domain="[('type', '=', 'other')]"),

	}

	def onchange_company_id(self, cr, uid, ids, company_id, context=None):
		res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
		if company_id:
			company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
			res['value'].update({'income_receivable_currency_exchange_account_id': company.income_receivable_currency_exchange_account_id and company.income_receivable_currency_exchange_account_id.id or False, 
								 'expense_receivable_currency_exchange_account_id': company.expense_receivable_currency_exchange_account_id and company.expense_receivable_currency_exchange_account_id.id or False,
								 'income_payable_currency_exchange_account_id': company.income_payable_currency_exchange_account_id and company.income_payable_currency_exchange_account_id.id or False,
								 'expense_payable_currency_exchange_account_id': company.expense_payable_currency_exchange_account_id and company.expense_payable_currency_exchange_account_id.id or False})
		else: 
			res['value'].update({'income_receivable_currency_exchange_account_id': False, 
								 'expense_receivable_currency_exchange_account_id': False,
								 'income_payable_currency_exchange_account_id': False,
								 'expense_payable_currency_exchange_account_id': False})
		return res


class account_voucher(osv.Model):
	_inherit = "account.voucher"
	def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
		'''
		Prepare the two lines in company currency due to currency rate difference.

		:param line: browse record of the voucher.line for which we want to create currency rate difference accounting
			entries
		:param move_id: Account move wher the move lines will be.
		:param amount_residual: Amount to be posted.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
		:rtype: tuple of dict
		'''

		res = super(account_voucher, self)._get_exchange_lines(cr, uid, line, move_id, amount_residual, company_currency, current_currency, context)

		if amount_residual > 0:
			account_id = line.voucher_id.type=='receipt' and line.voucher_id.company_id.expense_receivable_currency_exchange_account_id or line.voucher_id.company_id.expense_payable_currency_exchange_account_id
			if not account_id:
				raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account for "+(line.voucher_id.type=='receipt' and "AR" or "AP")+" Transaction' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		else:
			account_id = line.voucher_id.type=='receipt' and line.voucher_id.company_id.income_receivable_currency_exchange_account_id or line.voucher_id.company_id.income_payable_currency_exchange_account_id
			if not account_id:
				raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account for "+(line.voucher_id.type=='receipt' and "AR" or "AP")+" Transaction' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
		
		if res and res[1].get('account_id'):
			res[1]['account_id'] = account_id.id
		
		return (res[0], res[1])