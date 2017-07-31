import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class account_bank_loan(osv.Model):
	_inherit = "account.bank.loan"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC', readonly=True, states={'draft':[('readonly',False)]}),
	}

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan, self).action_validate(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.loan_type=='tr' and loan.lc_id:
				loan_type = dict(self._columns['loan_type'].selection).get(loan.loan_type)
				lc_history_pool.create(cr, uid, {
					'lc_id' : loan.lc_id.id,
					'value_source':'account.bank.loan,%s'%loan.id,
					'name' : "%s : %s"%((loan_type or 'Bank Loan'),(loan.name or '')),
					})
		return res

	def action_cancel_loan(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan, self).action_cancel_loan(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for loan in self.browse(cr, uid, ids, context=context):
			if loan.loan_type=='tr' and loan.lc_id:
				value_source = 'account.bank.loan,%s'%loan.id
				lc_history_ids = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',loan.lc_id.id)])
				if lc_history_ids:
					lc_history_pool.unlink(cr, uid, lc_history_ids)
		return res
			
class account_bank_loan_interest(osv.Model):
	_inherit = "account.bank.loan.interest"

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan_interest, self).action_validate(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		loan_pool = self.pool.get('account.bank.loan')
		for interest in self.browse(cr, uid, ids, context=context):
			if interest.loan_id and interest.loan_id.loan_type=='tr' and interest.loan_id.lc_id:
				loan_type = dict(loan_pool._columns['loan_type'].selection).get(interest.loan_id.loan_type)
				lc_history_pool.create(cr, uid, {
					'lc_id' : interest.loan_id.lc_id.id,
					'value_source':'account.bank.loan.interest,%s'%interest.id,
					'name' : "%s %s: %s"%((loan_type or 'Bank Loan'),'Interest',(interest.loan_id.name or '')),
					})
		return res

	def action_unreconcile(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan_interest, self).action_unreconcile(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for interest in self.browse(cr, uid, ids, context=context):
			if interest.loan_id.loan_type=='tr' and interest.loan_id.lc_id:
				value_source = 'account.bank.loan.interest,%s'%interest.id
				lc_history_ids = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',interest.loan_id.lc_id.id)])
				if lc_history_ids:
					lc_history_pool.unlink(cr, uid, lc_history_ids)
		return res

class account_bank_loan_repayment(osv.Model):
	_inherit = "account.bank.loan.repayment"

	def action_validate(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan_repayment, self).action_validate(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		loan_pool = self.pool.get('account.bank.loan')
		for repayment in self.browse(cr, uid, ids, context=context):
			if repayment.loan_id and repayment.loan_id.loan_type=='tr' and repayment.loan_id.lc_id:
				loan_type = dict(loan_pool._columns['loan_type'].selection).get(repayment.loan_id.loan_type)
				lc_history_pool.create(cr, uid, {
					'lc_id' : repayment.loan_id.lc_id.id,
					'value_source':'account.bank.loan.repayment,%s'%repayment.id,
					'name' : "%s %s: %s"%((loan_type or 'Bank Loan'),'Repayment',(repayment.loan_id.name or '')),
					})
		return res

	def action_unreconcile(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_bank_loan_repayment, self).action_unreconcile(cr, uid, ids, context=context)
		lc_history_pool = self.pool.get('letterofcredit.history')
		for repayment in self.browse(cr, uid, ids, context=context):
			if repayment.loan_id.loan_type=='tr' and repayment.loan_id.lc_id:
				value_source = 'account.bank.loan.repayment,%s'%repayment.id
				lc_history_ids = lc_history_pool.search(cr, uid, [('value_source','=',value_source),('lc_id','=',repayment.loan_id.lc_id.id)])
				if lc_history_ids:
					lc_history_pool.unlink(cr, uid, lc_history_ids)
		return res