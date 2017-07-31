import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
 
class negotiation_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(negotiation_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_nego_datas':self._get_nego_datas,
			'get_liability_nego_datas':self._get_liability_nego_datas,
		})

	def _get_nego_datas(self, data):
		cr = self.cr
		uid = self.uid

		abl_obj = self.pool.get('account.bank.loan')
		
		start_date = data['form']['start_date']
		end_date = data['form']['end_date']
		
		abl_ids = abl_obj.search(cr, uid, [('loan_type','=','nego'),('state','not in',['cancel','draft']),('effective_date','>=',start_date),('effective_date','<=',end_date)])
		if not abl_ids:
			return {}
		
		res_grouped = {}
		for abl in abl_obj.browse(cr, uid, abl_ids):
			if not abl.invoice_related_id and not abl.liability_move_line_id:
				continue
			key = abl.effective_date
			if key not in res_grouped:
				res_grouped.update({key:[]})
			
			current_currency = abl.journal_id.currency and abl.journal_id.currency or abl.journal_id.company_id.currency_id
			nego_amount = abl.total_amount
			nego_amount_company_curr = self._get_amount_company_currency(current_currency.id, nego_amount, abl.effective_date)
			inv_amount = abl.invoice_related_id.amount_total
			inv_amount_company_curr = self._get_amount_company_currency(current_currency.id, inv_amount, abl.effective_date)
			res_grouped[key].append({
				'inv_number' : abl.invoice_related_id.internal_number,
				'inv_date' : self.formatLang(abl.invoice_related_id.date_invoice,date=True),
				'lc_batch' : '.'.join(list(set([y.lc_product_line_id.lc_id.name for y in [x.move_line_ids[0] for x in abl.invoice_related_id.invoice_line if x.move_line_ids] if y.lc_product_line_id and y.lc_product_line_id.lc_id]))),
				'customer' : abl.invoice_related_id.partner_id.partner_alias or abl.invoice_related_id.partner_id.name,
				'giro_number' : '',
				'payment_bank' : abl.journal_id.name,
				'nego_bank' : abl.journal_id.name,
				'cury' : current_currency.name,
				'dispatch_amt' : inv_amount,
				'dispatch_amt_company_curr' : inv_amount_company_curr,
				'received_amt' : nego_amount,
				'received_amt_company_curr' : nego_amount_company_curr,
				})
		return res_grouped

	def _get_liability_nego_datas(self, data):
		cr = self.cr
		uid = self.uid

		abl_obj = self.pool.get('account.bank.loan')
		curr_obj = self.pool.get('res.currency')
		
		as_on = data['form']['as_on']
		
		query = "SELECT \
					move_lines.id \
				FROM \
					(SELECT a1.id, a2.reconcile_id FROM \
						account_bank_loan a1 \
						INNER JOIN account_move_line a2 ON a2.id = a1.liability_move_line_id \
					WHERE a1.loan_type='nego' and a1.effective_date<='%s') as move_lines \
					LEFT JOIN ( \
						SELECT \
							sum(b1.debit-b1.credit) as balance, \
							b1.reconcile_id \
						FROM \
							account_move_line b1 \
						WHERE b1.reconcile_id is NOT NULL AND b1.date<='%s' \
						GROUP BY b1.reconcile_id \
						) as reconcile_ids ON reconcile_ids.reconcile_id=coalesce(move_lines.reconcile_id,0) \
				WHERE reconcile_ids.balance is NULL OR reconcile_ids.balance!=0"
		query = query % (as_on,as_on)
		cr.execute(query)
		abl_ids = [x[0] for x in cr.fetchall()]
		if not abl_ids:
			return {}
		
		res_grouped = {}
		for abl in abl_obj.browse(cr, uid, abl_ids):
			if not abl.invoice_related_id or not abl.liability_move_line_id:
				continue
			key = abl.effective_date
			if key not in res_grouped:
				res_grouped.update({key:[]})
			
			current_currency = abl.journal_id.currency and abl.journal_id.currency or abl.journal_id.company_id.currency_id
			nego_amount = abl.total_amount
			nego_amount_company_curr = self._get_amount_company_currency(current_currency.id, nego_amount, abl.effective_date)
			residual_amount = nego_amount
			for payment in (abl.liability_move_line_id.reconcile_id and abl.liability_move_line_id.reconcile_id.line_id or (abl.liability_move_line_id.reconcile_partial_id and abl.liability_move_line_id.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=abl.liability_move_line_id.id and payment.date<=as_on:
					if payment.currency_id and payment.currency_id.id!=current_currency.id:
						residual_amount-=curr_obj.compute(cr, uid, payment.currency_id.id, current_currency.id, payment.amount_currency, context={'date':payment.date})
					elif not payment.currency_id and current_currency.id!=abl.company_id.currency_id.id:
						residual_amount-=curr_obj.compute(cr, uid, abl.company_id.currency_id.id, current_currency.id, (payment.credit-payment.debit), context={'date':payment.date})
					else:
						residual_amount-=(payment.credit-payment.debit)
			res_grouped[key].append({
				'inv_number' : abl.invoice_related_id.internal_number,
				'inv_date' : abl.invoice_related_id.date_invoice,
				'lc_batch' : '.'.join(list(set([y.lc_product_line_id.lc_id.name for y in [x.move_line_ids[0] for x in abl.invoice_related_id.invoice_line if x.move_line_ids] if y.lc_product_line_id and y.lc_product_line_id.lc_id]))),
				'customer' : abl.invoice_related_id.partner_id.partner_alias or abl.invoice_related_id.partner_id.name,
				'reference' : abl.ref,
				'nego_bank' : abl.journal_id.name,
				'cury' : current_currency.name,
				'residual_amount' : residual_amount,
				'received_amt' : nego_amount,
				'received_amt_company_curr' : nego_amount_company_curr,
				'due_date' : abl.liability_move_line_id.date_maturity,
				})
		return res_grouped

	def _get_charges_type(self,data):
		# sale_type = data['form']['sale_type']
		charge_pool = self.pool.get('charge.type')
		charge_ids = charge_pool.search(self.cr, self.uid, [('trans_type','=','sale'),('type','=','invoicing'),('name','like','%Interest%')])
		temp = []
		if charge_ids:
			for x in charge_pool.browse(self.cr,self.uid, charge_ids):
				if x.code:
					key = x.code and x.code or 'OTH' 
					if key and x.code not in temp:
						temp.append(key)
		return temp

	def _get_repayment_nego_datas(self, data):
		cr = self.cr
		uid = self.uid

		ablr_obj = self.pool.get('account.bank.loan.repayment')
		curr_obj = self.pool.get('res.currency')
		
		start_date = data['form']['start_date']
		end_date = data['form']['end_date']
		
		ablr_ids = ablr_obj.search(cr, uid, [('payment_date','>=',start_date),('payment_date','<=',end_date),('state','=','paid'),('loan_id.loan_type','=','nego')])
		if not ablr_ids:
			return {}
		
		
		chg = self._get_charges_type(data)
		res_grouped = {}
		for ablr in ablr_obj.browse(cr, uid, ablr_ids):
			if not ablr.loan_id and not ablr.loan_id.invoice_related_id or not ablr.loan_id.liability_move_line_id:
				continue
			key = ablr.payment_date
			if key not in res_grouped:
				res_grouped.update({key:[]})

			chg_dict = {}
			for x in chg:
				if x not in chg_dict.keys():
					chg_dict.update({x:0.0})
			
			for interest in ablr.loan_id.int_line:
				if interest.type_of_charge and interest.type_of_charge.code in chg_dict.keys():
					int_amt = interest.total_paid_amount
					for oth_cost in interest.writeoff_lines:
						int_amt-=oth_cost.amount
					chg_dict[interest.type_of_charge.code]+=int_amt

			current_currency = ablr.journal_id.currency and ablr.journal_id.currency or ablr.journal_id.company_id.currency_id
			nego_amount = ablr.loan_id.total_amount
			nego_amount_company_curr = self._get_amount_company_currency(current_currency.id, nego_amount, ablr.loan_id.effective_date)
			repayment_amount = ablr.real_amount
			repayment_amount_company_curr = self._get_amount_company_currency(current_currency.id, ablr.real_amount, ablr.payment_date)
			res_line = {
				'inv_number' : ablr.loan_id.invoice_related_id.internal_number,
				'inv_date' : ablr.loan_id.invoice_related_id.date_invoice,
				'lc_batch' : '.'.join(list(set([y.lc_product_line_id.lc_id.name for y in [x.move_line_ids[0] for x in ablr.loan_id.invoice_related_id.invoice_line if x.move_line_ids] if y.lc_product_line_id and y.lc_product_line_id.lc_id]))),
				'customer' : ablr.loan_id.invoice_related_id.partner_id.partner_alias or ablr.loan_id.invoice_related_id.partner_id.name,
				'nego_date' : ablr.loan_id.effective_date,
				'reference' : ablr.loan_id.ref,
				'repayment_bank' : ablr.journal_id.name,
				'cury' : current_currency.name,
				'received_amt' : nego_amount,
				'received_amt_company_curr' : nego_amount_company_curr,
				'repayment_amt' : repayment_amount,
				'repayment_amt_company_curr' : repayment_amount_company_curr,
				}
			
			if chg_dict:
				for k, v in chg_dict.items():
					res_line.update({k:v})

			res_grouped[key].append(res_line)
		return res_grouped

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, currency_usd.id, amount, context={'date':date})