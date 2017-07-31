import re
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
 
class sales_payment_realisation_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(sales_payment_realisation_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_query(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		period_from=data['form'].get('period_from',False) and data['form']['period_from'][0] or False
		period_to=data['form'].get('period_to',False) and data['form']['period_to'][0] or False
		
		cr = self.cr
		uid = self.uid
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		fiscalperiod_obj = self.pool.get('account.period')
		query = ""
		
		# if data['form']['account_ids']:
		# 	query += " AND l.account_id IN ("+','.join([str(x) for x in data['form']['account_ids']])+") "
		# if data['form']['journal_ids']:
		# 	query += " AND l.journal_id in ("+','.join([str(x) for x in data['form']['journal_ids']])+") "

		# if data['form']['partner_ids']:
		# 	query += " AND l.partner_id is NOT NULL AND l.partner_id in ("+','.join([str(x) for x in data['form']['partner_ids']])+") "

		if data['form']['filter'] == 'filter_date':
			query += " AND b.date between '"+from_date+"' and '"+to_date+"'"
		elif data['form']['filter'] == 'filter_period':
			period_ids = []
			period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, period_from, period_to)
			
			query += " AND b.period_id IN ("+','.join([str(x) for x in period_ids or []])+") "

		return query
		
	def _get_result(self, data):
		cr = self.cr
		uid = self.uid
		voucher_pool_obj = self.pool.get('account.voucher')
		vline_pool_obj = self.pool.get('account.voucher.line')
		invoice_pool_obj = self.pool.get('account.invoice')
		mline_pool_obj = self.pool.get('account.move.line')
		curr_pool_obj = self.pool.get('res.currency')

		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		period_from=data['form']['period_from']
		period_to=data['form']['period_to']
		inv_type = data.get('inv_type',"out_invoice")
		if data['form']['filter']=='filter_period':
			period_from_obj = self.pool.get(self.cr, self.uid, period_from)
			period_to_obj = self.pool.get(self.cr, self.uid, period_to)
			from_date = period_from_obj.date_start
			to_date = period_to_obj.date_stop
		# journal_ids = data['form']['journal_ids']
		# account_ids = data['form']['account_ids']
		sale_type = data['form']['sale_type']
		currency_id = data['form'].get('currency_id',False) and data['form']['currency_id'][0] or False

		query = "\
				SELECT\
					a.id as line_id,\
					a.voucher_id,\
					d.id as invoice_id\
				FROM\
					account_voucher_line a\
					INNER JOIN account_voucher b ON b.id=a.voucher_id\
					INNER JOIN account_move_line c ON a.move_line_id=c.id\
					INNER JOIN account_invoice d ON d.move_id=c.move_id\
				WHERE\
					a.move_line_id is not NULL\
					AND b.move_id is not NULL\
					AND d.type='"+inv_type+"'\
					 "
		if sale_type:
			query += " AND d.sale_type='"+sale_type+"' "

		if currency_id:
			query += " AND d.currency_id="+str(currency_id)+" "
		query += self._get_query(data)
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		result_grouped = {}
		if inv_type in ('out_invoice','out_refund'):
			if sale_type=='export':
				## BEGIN : collecting all adjustment AR
				adv_dict = {}
				nego_dict = {}
				adj_dict = {}
				# adjustment from advance
				for voucher in voucher_pool_obj.browse(cr, uid, list(set([x['voucher_id'] for x in res]))):
					for adv_line in voucher.advance_split_lines:
						for adv_inv in adv_line.lines:
							if adv_inv.amount and adv_inv.advance_id and adv_inv.advance_id.move_id:
								key_adv_dict = (voucher.id, adv_inv.invoice_id.id)
								if key_adv_dict not in adv_dict.keys():
									adv_dict.update({key_adv_dict:{
										'move_id':adv_inv.advance_id.move_id.id,
										'amount':0.0,}})
								adv_dict[key_adv_dict]['amount']+=adv_inv.amount

				# adjustment from bank negotiation
				for line in vline_pool_obj.browse(cr, uid, [x['line_id'] for x in res]):
					if not line.move_line_id or not line.move_line_id.invoice or not line.voucher_id:
						continue
					key_nego_dict = (line.voucher_id.id,line.move_line_id.invoice.id)
					if line.move_line_id.invoice.bank_negotiation_no and line.move_line_id.invoice.bank_negotiation_no.move_id and key_nego_dict not in nego_dict.keys():
						nego_dict.update({key_nego_dict:line.move_line_id.invoice.bank_negotiation_no.move_id.id})

				# adjustment from other advance or refund
				for line in vline_pool_obj.browse(cr, uid, [x['line_id'] for x in res]):
					if not line.move_line_id or not line.voucher_id:
						continue
					# nyari refund
					# if [for x in line.voucer_id.line_id]

				## END : collecting all adjustment AR

				for line in vline_pool_obj.browse(cr, uid, [x['line_id'] for x in res]):
					if not line.move_line_id or not line.move_line_id.invoice or not line.voucher_id:
						continue

					key0 = line.voucher_id.date
					if key0 not in result_grouped:
						result_grouped.update({key0:[]})

					use_nego = False
					if line.move_line_id.invoice.bank_negotiation_no:
						use_nego = True
					# due_date = line.move_line_id.date_maturity!='False' and line.move_line_id.date_maturity or line.move_line_id.date
					# amount_paid = self._get_amount_company_currency(line.voucher_id.currency_id.id, line.amount, line.voucher_id.date)
					from_curr = line.voucher_id.journal_id.currency and line.voucher_id.journal_id.currency or self._get_company_currency()
					# received_amt = self._get_amount_company_currency(from_curr.id, line.amount, line.voucher_id.date)

					if line.move_line_id.invoice.currency_id.id!=line.voucher_id.currency_id.id:
						received_amt = self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, line.amount, line.voucher_id.date)
					else:
						received_amt = line.amount
					
					if not received_amt:
						continue

					chg = self._get_charges_type(data)
					chg_dict = {'chg_amt_others':0.0}
					if chg:
						for k in chg:
							chg_dict.update({k:0.0})
					
					exchange_account_ids = []
					if line.voucher_id.company_id.income_receivable_currency_exchange_account_id:
						exchange_account_ids.append(line.voucher_id.company_id.income_receivable_currency_exchange_account_id.id)
					if line.voucher_id.company_id.expense_receivable_currency_exchange_account_id:
						exchange_account_ids.append(line.voucher_id.company_id.expense_receivable_currency_exchange_account_id.id)

					total_payment_amount = sum([x.amount for x in line.voucher_id.line_ids if not x.ar_ap_tax])
					writeoff_amount = line.voucher_id.amount - total_payment_amount
					if writeoff_amount!=0.0 and not line.ar_ap_tax:
						if line.voucher_id.extra_writeoff:
							for wline in line.voucher_id.writeoff_lines:
								if wline.invoice_related_id and wline.invoice_related_id.id==line.move_line_id.invoice.id:
									if wline.type and wline.type.code and wline.type.code in chg_dict:
										chg_key_dummy = wline.type.code in chg_dict.keys() and wline.type.code or 'OTH'
										if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
											chg_dict[chg_key_dummy] += wline.amount
										else:
											chg_dict[chg_key_dummy] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, wline.amount, line.voucher_id.date)
										# chg_dict[wline.type.code] += self._get_amount_company_currency(from_curr.id, wline.amount, line.voucher_id.date)
									else:
										if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
											chg_dict['chg_amt_others'] += wline.amount
										else:
											chg_dict['chg_amt_others'] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, wline.amount, line.voucher_id.date)
										# chg_dict['chg_amt_others'] += self._get_amount_company_currency(from_curr.id, wline.amount, line.voucher_id.date)
						else:
							if line.voucher_id.writeoff_acc_id and line.voucher_id.writeoff_acc_id.id not in exchange_account_ids:
								ratio_rcvd = line.amount/total_payment_amount
								if line.move_line_id.invoice.currency_id.id==line.voucher_id.currency_id.id:
									chg_dict['chg_amt_others'] += ratio_rcvd*writeoff_amount
								else:
									chg_dict['chg_amt_others'] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
							# chg_dict['chg_amt_others'] += self._get_amount_company_currency(from_curr.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
					if use_nego:
						# if not line.move_line_id.invoice.bank_negotiation_no.repayment_line and line.move_line_id.invoice.bank_negotiation_no.int_line:
						if line.move_line_id.invoice.bank_negotiation_no.int_line:
							for interest in line.move_line_id.invoice.bank_negotiation_no.int_line:
								if interest.payment_date>=from_date and interest.payment_date<=to_date \
										and interest.type_of_charge and interest.type_of_charge.code in chg_dict:
									int_curr = interest.journal_id.currency and interest.journal_id.currency or interest.journal_id.company_id.currency_id
									int_amt = interest.total_paid_amount
									for oth_cost in interest.writeoff_lines:
										# if oth_cost.invoice_related_id and oth_cost.invoice_related_id.id=line.move_line_id.invoice.id:
										chg_key_dummy = oth_cost.type.code in chg_dict.keys() and oth_cost.type.code or 'OTH'
										if interest.journal_id.currency and interest.journal_id.currency.id==line.voucher_id.currency_id.id:
											chg_dict[chg_key_dummy] += -1*oth_cost.amount
										else:
											chg_dict[chg_key_dummy] += -1*self._get_amount_converted(int_curr.id, line.move_line_id.invoice.currency_id.id, oth_cost.amount, line.voucher_id.date)
										int_amt-=oth_cost.amount

									chg_key_dummy = interest.type_of_charge.code in chg_dict.keys() and interest.type_of_charge.code or 'OTH'
									if interest.journal_id.currency and interest.journal_id.currency.id==line.voucher_id.currency_id.id:
										chg_dict[chg_key_dummy] += -1*int_amt
									else:
										chg_dict[chg_key_dummy] += -1*self._get_amount_converted(int_curr.id, line.move_line_id.invoice.currency_id.id, int_amt, line.voucher_id.date)
					res_line = {
							'inv_number' : line.move_line_id.invoice.internal_number or line.move_line_id.invoice.number or '',
							'inv_date1' : line.move_line_id.invoice.date_invoice,
							'inv_date2' : datetime.strptime(line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
							'customer' : line.move_line_id.invoice.partner_id.partner_alias or line.move_line_id.invoice.partner_id.name or '',
							'giro_no' : line.voucher_id.reference,
							'payment_bank' : line.voucher_id.journal_id.name,
							'nego_bank' : use_nego and line.move_line_id.invoice.bank_negotiation_no.journal_id.name or "",
							'nego_cury' : use_nego and (line.move_line_id.invoice.bank_negotiation_no.journal_id.currency and line.move_line_id.invoice.bank_negotiation_no.journal_id.currency.name or line.move_line_id.invoice.bank_negotiation_no.journal_id.company_id.currency_id.name) or "",
							'sales_amt' : line.move_line_id.invoice.amount_total,
							'bl_date' : datetime.strptime(line.move_line_id.invoice.bl_date!=False and line.move_line_id.invoice.bl_date or line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
							'nego_date' : use_nego and datetime.strptime(line.move_line_id.invoice.bank_negotiation_date, '%Y-%m-%d').strftime('%d/%m/%Y') or "",
							'due_date' : datetime.strptime(line.move_line_id.invoice.date_due, '%Y-%m-%d').strftime('%d/%m/%Y'),
							'coll_days' : 0.0,
							'usance_days' : 0.0,
							'received_amt' : received_amt,
						}
					if chg_dict:
						for key, val in chg_dict.items():
							res_line.update({key:val})

					result_grouped[key0].append(res_line)

			elif sale_type=='local':
				for line in vline_pool_obj.browse(cr, uid, [x['line_id'] for x in res]):
					if not line.move_line_id or not line.move_line_id.invoice or not line.voucher_id:
						continue

					key0 = line.voucher_id.date
					if key0 not in result_grouped:
						result_grouped.update({key0:[]})

					# due_date = line.move_line_id.date_maturity!='False' and line.move_line_id.date_maturity or line.move_line_id.date
					# amount_paid = self._get_amount_company_currency(line.voucher_id.currency_id.id, line.amount, line.voucher_id.date)
					
					from_curr = line.voucher_id.journal_id.currency and line.voucher_id.journal_id.currency or self._get_company_currency()
					# received_amt = self._get_amount_company_currency(from_curr.id, line.amount, line.voucher_id.date)
					# received_amt = line.move_line_id and line.move_line_id.invoice and (line.move_line_id.ar_ap_tax or line.ar_ap_tax) and line.move_line_id.invoice.amount_tax or line.move_line_id.invoice.amount_untaxed
					if line.move_line_id.invoice.currency_id.id!=line.voucher_id.currency_id.id:
						received_amt = self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, line.amount, line.voucher_id.date)
					else:
						received_amt = line.amount
					chg_amt = 0.0

					exchange_account_ids = []
					if line.voucher_id.company_id.income_receivable_currency_exchange_account_id:
						exchange_account_ids.append(line.voucher_id.company_id.income_receivable_currency_exchange_account_id.id)
					if line.voucher_id.company_id.expense_receivable_currency_exchange_account_id:
						exchange_account_ids.append(line.voucher_id.company_id.expense_receivable_currency_exchange_account_id.id)

					total_payment_amount = sum([(x.type=='cr' and x.amount or -1*x.amount) for x in line.voucher_id.line_ids])
					total_alocation = sum([(x.type=='cr' and not x.ar_ap_tax and x.amount or 0.0) for x in line.voucher_id.line_ids])
					writeoff_amount = line.voucher_id.amount-total_payment_amount
					if writeoff_amount!=0.0 and not line.ar_ap_tax:
						if line.voucher_id.extra_writeoff:
							for wline in line.voucher_id.writeoff_lines:
								if wline.invoice_related_id and wline.invoice_related_id.id==line.move_line_id.invoice.id and wline.account_id.id not in exchange_account_ids:
									if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
										chg_amt += wline.amount
									else:
										chg_amt += self._get_amount_converted(from_curr.id, wline.invoice_related_id.currency_id.id, wline.amount, line.voucher_id.date)
						else:
							if line.voucher_id.writeoff_acc_id and line.voucher_id.writeoff_acc_id.id not in exchange_account_ids:
								ratio_rcvd = line.amount/total_alocation
								if line.move_line_id.invoice.currency_id.id==line.voucher_id.currency_id.id:
									chg_amt += ratio_rcvd*writeoff_amount
								else:
									chg_amt += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
							else:
								ratio_rcvd = line.amount/total_alocation
								if line.move_line_id.invoice.currency_id.id==line.voucher_id.currency_id.id:
									received_amt += ratio_rcvd*writeoff_amount
								else:
									received_amt += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
							# chg_amt += self._get_amount_company_currency(from_curr.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
					result_grouped[key0].append({
							'inv_number' : line.move_line_id.invoice.internal_number or line.move_line_id.invoice.number or '',
							'inv_date1' : line.move_line_id.invoice.date_invoice,
							'inv_date2' : datetime.strptime(line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
							'customer' : line.move_line_id.invoice.partner_id.partner_alias or line.move_line_id.invoice.partner_id.name or '',
							'giro_no' : "",
							'payment_bank' : line.voucher_id.journal_id.name,
							'received_amt' : received_amt,
							'cash_amt' : 0.0,
							'others_amt' : 0.0,
							'chg_amt' : chg_amt,
							'payment_advice' : line.voucher_id.reference or "",
							'batch' : line.voucher_id.number or "",
						})
		elif inv_type in ('in_invoice','in_refund'):
			for line in vline_pool_obj.browse(cr, uid, sorted([x['line_id'] for x in res])):
				if not line.move_line_id or not line.move_line_id.invoice or not line.voucher_id:
					continue

				key0 = line.voucher_id.date
				if key0 not in result_grouped:
					result_grouped.update({key0:[]})

				# voucher currency
				from_curr = line.voucher_id.journal_id.currency and line.voucher_id.journal_id.currency or self._get_company_currency()
				
				if line.move_line_id.invoice.currency_id.id!=line.voucher_id.currency_id.id:
					received_amt = self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, line.amount, line.voucher_id.date)
				else:
					received_amt = line.amount
				
				chg = self._get_charges_type(data)
				chg_dict = {'chg_amt_others':0.0}
				if chg:
					for k in chg:
						chg_dict.update({k:0.0})
				
				exchange_account_ids = []
				if line.voucher_id.company_id.income_receivable_currency_exchange_account_id:
					exchange_account_ids.append(line.voucher_id.company_id.income_receivable_currency_exchange_account_id.id)
				if line.voucher_id.company_id.expense_receivable_currency_exchange_account_id:
					exchange_account_ids.append(line.voucher_id.company_id.expense_receivable_currency_exchange_account_id.id)

				total_payment_amount = sum([x.amount for x in line.voucher_id.line_ids if not x.ar_ap_tax])
				writeoff_amount = line.voucher_id.amount - total_payment_amount
				if writeoff_amount!=0.0 and not line.ar_ap_tax:
					if line.voucher_id.extra_writeoff:
						for wline in line.voucher_id.writeoff_lines:
							if wline.invoice_related_id and wline.invoice_related_id.id==line.move_line_id.invoice.id:
								if wline.type and wline.type.code and wline.type.code in chg_dict:
									chg_key_dummy = wline.type.code in chg_dict.keys() and wline.type.code or 'OTH'
									if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
										chg_dict[chg_key_dummy] += wline.amount
									else:
										chg_dict[chg_key_dummy] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, wline.amount, line.voucher_id.date)
									# chg_dict[wline.type.code] += self._get_amount_company_currency(from_curr.id, wline.amount, line.voucher_id.date)
								else:
									if wline.invoice_related_id.currency_id.id==line.voucher_id.currency_id.id:
										chg_dict['chg_amt_others'] += wline.amount
									else:
										chg_dict['chg_amt_others'] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, wline.amount, line.voucher_id.date)
									# chg_dict['chg_amt_others'] += self._get_amount_company_currency(from_curr.id, wline.amount, line.voucher_id.date)
					else:
						if line.voucher_id.writeoff_acc_id and line.voucher_id.writeoff_acc_id.id not in exchange_account_ids:
							ratio_rcvd = line.amount/total_payment_amount
							if line.move_line_id.invoice.currency_id.id==line.voucher_id.currency_id.id:
								chg_dict['chg_amt_others'] += ratio_rcvd*writeoff_amount
							else:
								chg_dict['chg_amt_others'] += self._get_amount_converted(from_curr.id, line.move_line_id.invoice.currency_id.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
						# chg_dict['chg_amt_others'] += self._get_amount_company_currency(from_curr.id, ratio_rcvd*writeoff_amount, line.voucher_id.date)
				if use_nego:
					# if not line.move_line_id.invoice.bank_negotiation_no.repayment_line and line.move_line_id.invoice.bank_negotiation_no.int_line:
					if line.move_line_id.invoice.bank_negotiation_no.int_line:
						for interest in line.move_line_id.invoice.bank_negotiation_no.int_line:
							if interest.payment_date>=from_date and interest.payment_date<=to_date \
									and interest.type_of_charge and interest.type_of_charge.code in chg_dict:
								int_curr = interest.journal_id.currency and interest.journal_id.currency or interest.journal_id.company_id.currency_id
								int_amt = interest.total_paid_amount
								for oth_cost in interest.writeoff_lines:
									# if oth_cost.invoice_related_id and oth_cost.invoice_related_id.id=line.move_line_id.invoice.id:
									chg_key_dummy = oth_cost.type.code in chg_dict.keys() and oth_cost.type.code or 'OTH'
									if interest.journal_id.currency and interest.journal_id.currency.id==line.voucher_id.currency_id.id:
										chg_dict[chg_key_dummy] += -1*oth_cost.amount
									else:
										chg_dict[chg_key_dummy] += -1*self._get_amount_converted(int_curr.id, line.move_line_id.invoice.currency_id.id, oth_cost.amount, line.voucher_id.date)
									int_amt-=oth_cost.amount

								chg_key_dummy = interest.type_of_charge.code in chg_dict.keys() and interest.type_of_charge.code or 'OTH'
								if interest.journal_id.currency and interest.journal_id.currency.id==line.voucher_id.currency_id.id:
									chg_dict[chg_key_dummy] += -1*int_amt
								else:
									chg_dict[chg_key_dummy] += -1*self._get_amount_converted(int_curr.id, line.move_line_id.invoice.currency_id.id, int_amt, line.voucher_id.date)
				res_line = {
						'inv_number' : line.move_line_id.invoice.internal_number or line.move_line_id.invoice.number or '',
						'inv_date1' : line.move_line_id.invoice.date_invoice,
						'inv_date2' : datetime.strptime(line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
						'customer' : line.move_line_id.invoice.partner_id.partner_alias or line.move_line_id.invoice.partner_id.name or '',
						'giro_no' : line.voucher_id.reference,
						'payment_bank' : line.voucher_id.journal_id.name,
						'nego_bank' : use_nego and line.move_line_id.invoice.bank_negotiation_no.journal_id.name or "",
						'nego_cury' : use_nego and (line.move_line_id.invoice.bank_negotiation_no.journal_id.currency and line.move_line_id.invoice.bank_negotiation_no.journal_id.currency.name or line.move_line_id.invoice.bank_negotiation_no.journal_id.company_id.currency_id.name) or "",
						'sales_amt' : line.move_line_id.invoice.amount_total,
						'bl_date' : datetime.strptime(line.move_line_id.invoice.bl_date!=False and line.move_line_id.invoice.bl_date or line.move_line_id.invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
						'nego_date' : use_nego and datetime.strptime(line.move_line_id.invoice.bank_negotiation_date, '%Y-%m-%d').strftime('%d/%m/%Y') or "",
						'due_date' : datetime.strptime(line.move_line_id.invoice.date_due, '%Y-%m-%d').strftime('%d/%m/%Y'),
						'coll_days' : 0.0,
						'usance_days' : 0.0,
						'received_amt' : received_amt,
					}
				if chg_dict:
					for key, val in chg_dict.items():
						res_line.update({key:val})

				result_grouped[key0].append(res_line)
		return result_grouped

	def _get_charges_type(self,data):
		sale_type = data['form']['sale_type']
		charge_pool = self.pool.get('charge.type')
		charge_ids = charge_pool.search(self.cr, self.uid, [('trans_type','=','sale'),('type','=','invoicing'),('sale_type','=',sale_type)])
		temp = []
		if charge_ids:
			for x in charge_pool.browse(self.cr,self.uid, charge_ids):
				if x.code:
					key = x.code and x.code or 'OTH' 
					if key and x.code not in temp:
						temp.append(key)
		if 'OTH' not in temp:
			temp.append('OTH')
		return temp
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_amount_converted(self, from_curr, to_curr, amount, date):
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, to_curr, amount, context={'date':date})

class sales_payment_realisation_xls(report_xls):
	def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
		if not context:
			context = {}
		context = context.copy()
		rml_parser = self.parser(cr, uid, self.name2, context=context)
		objs = []
		rml_parser.set_context(objs, data, ids, 'xls')
		n = cStringIO.StringIO()
		wb = xlwt.Workbook(encoding='utf-8')
		self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
		wb.save(n)
		n.seek(0)
		return (n.read(), 'xls')
 
	def generate_xls_report(self, parser, data, obj, wb):
		ws = wb.add_sheet('Advance Report',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		company = "PT.BITRATEX INDUSTRIES"
		doc_name = data['form']['sale_type'].upper()+" NEGOTIATION STATEMENT - DATE WISE"
		sale_type=data['form']['sale_type']
		if data['form']['filter'] == 'filter_date':
			from_date = datetime.strptime(data['form']['from_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			to_date = datetime.strptime(data['form']['to_date'],'%Y-%m-%d').strftime('%d/%m/%Y')
			doc_name = "Payment Realisation Date between "+str(from_date)+" and "+str(to_date)
		elif data['form']['filter'] == 'filter_period':
			period_from = data['form']['period_from'][1]
			period_to = data['form']['period_to'][1]
			doc_name = "Payment Realisation Period between "+period_from+" and "+period_to
		
		# :::: Write header
		ws.write_merge(2,3,0,0, "Sr.\nNo", th_both_style)
		ws.write_merge(2,2,1,2, "Invoice", th_both_style)
		ws.write(3,1, "No.", th_both_style)
		ws.write(3,2, "Date", th_both_style)
		chg = {}
		if sale_type=='export':
			chg = parser._get_charges_type(data)
			ws.write_merge(2,3,3,3, "LC\nBat.Nbr", th_both_style)
			ws.write_merge(2,3,4,4, "Customer", th_both_style)
			ws.write_merge(2,3,5,5, "Giro No.", th_both_style)
			ws.write_merge(2,3,6,6, "Payment\nBank.", th_both_style)
			ws.write_merge(2,3,7,7, "Negotiation\nBank", th_both_style)
			ws.write_merge(2,3,8,8, "Cury\nId", th_both_style)
			ws.write_merge(2,3,9,9, "Sales\nAmount", th_both_style)
			ws.write_merge(2,3,10,10, "B/L\nDate", th_both_style)
			ws.write_merge(2,3,11,11, "Nego's\nDate", th_both_style)
			ws.write_merge(2,3,12,12, "Due\nDate", th_both_style)
			ws.write_merge(2,3,13,13, "Coll\nDays", th_both_style)
			ws.write_merge(2,3,14,14, "US'C\nDays", th_both_style)

			if chg:
				ws.write_merge(2,2,15,14+len(chg), "C h a r g e s", th_both_style)
				c = 15
				for k in chg:
					ws.write(3,c, k, th_both_style)
					c+=1
				ws.write_merge(2,3,c,c, "Net Realisation\n(USD)", th_both_style)
				# main title
				ws.write_merge(0,0,0,c, company, title_style)
				ws.write_merge(1,1,0,c, doc_name, title_style)
			else:
				ws.write_merge(2,3,15,15, "Chg\nOthers", th_both_style)
				ws.write_merge(2,3,16,16, "Net Realisation\n(USD)", th_both_style)
				# main title
				ws.write_merge(0,0,0,16, company, title_style)
				ws.write_merge(1,1,0,16, doc_name, title_style)
		elif sale_type=='local':
			# main title
			ws.write_merge(0,0,0,12, company, title_style)
			ws.write_merge(1,1,0,12, doc_name, title_style)

			ws.write_merge(2,3,3,3, "Giro No.", th_both_style)
			ws.write_merge(2,3,4,4, "Customer", th_both_style)
			ws.write_merge(2,3,5,5, "Bank Name", th_both_style)
			ws.write_merge(2,3,6,6, "Received", th_both_style)
			ws.write_merge(2,3,7,7, "C a s h", th_both_style)
			ws.write_merge(2,3,8,8, "Others", th_both_style)
			ws.write_merge(2,3,9,9, "Bank\nCharges", th_both_style)
			ws.write_merge(2,3,10,10, "N e t\nRealisation", th_both_style)
			ws.write_merge(2,3,11,11, "Payment\nAdvice", th_both_style)
			ws.write_merge(2,3,12,12, "Batch", th_both_style)
		rowcount=4
		# END:::: Write header
		ws.horz_split_pos = rowcount
		
		# :::: Init variable
		# init grand total variable and column width variable
		if sale_type=='export':
			total = {1:0}
			max_width_col = {0:3,1:10,2:8,3:10,4:10,5:10,6:12,7:12,8:5,9:12,10:8,11:8,12:8,13:12,14:12}
			if chg:
				s = 2
				c = 15
				for k in chg:
					total.update({s:0})
					max_width_col.update({c:10})
					s+=1
					c+=1
				total.update({s:0})
				max_width_col.update({c:12})
			else:
				total.update({2:0,3:0})
				max_width_col.update({15:12,16:12})
		else:
			total = {1:0.0,2:0.0,3:0.0,4:0.0,5:0.0,6:0.0,7:0.0,8:0.0,}
			max_width_col = {0:3,1:10,2:8,3:10,4:10,5:12,6:12,7:12,8:12,9:12,10:12,11:10,12:10,13:5,14:5,15:5,16:5,}
		# END:::: Init variable

		# :::: Write Datas Content
		results = parser._get_result(data)
		summary_per_bank = {}
		for key in sorted(results.keys()):
			date1 = datetime.strptime(key, '%Y-%m-%d').strftime('%d/%m/%Y')
			ws.write_merge(rowcount,rowcount,0,16, "Realisation Date : "+date1, normal_bold_style)
			rowcount+=1

			# :::: Init Subtotal Var
			if sale_type=='export':
				subtotal = {1:0}
				if chg:
					c = 2
					for k in chg:
						subtotal.update({c:0})
						c+=1
					subtotal.update({c:0})
				else:
					subtotal.update({2:0,3:0})
			else:
				subtotal = {1:0.0,2:0.0,3:0.0,4:0.0,5:0.0,6:0.0,7:0.0,8:0.0,}
			# END:::: Init Subtotal Var

			nos = 0
			for payment in sorted(results[key],key = lambda x : x['inv_date1']):
				nos += 1
				ws.write(rowcount, 0, nos, normal_style_float_round)
				ws.write(rowcount, 1, payment['inv_number'],normal_style)
				ws.write(rowcount, 2, payment['inv_date2'],normal_style)
				# :::: Write Datas Content for Export Payment
				if sale_type=='export':
					ws.write(rowcount, 3, "",normal_style)
					ws.write(rowcount, 4, payment['customer'],normal_style)
					if payment['customer'] and len(payment['customer'])>max_width_col[4]:
						max_width_col[4]=len(payment['customer'])
					
					ws.write(rowcount, 5, payment['giro_no'],normal_style)
					if payment['giro_no'] and len(payment['giro_no'])>max_width_col[5]:
						max_width_col[5]=len(payment['giro_no'])
					
					ws.write(rowcount, 6, payment['payment_bank'],normal_style)
					if payment['payment_bank'] and len(payment['payment_bank'])>max_width_col[6]:
						max_width_col[6]=len(payment['payment_bank'])
					if payment['payment_bank'] not in summary_per_bank:
						summary_per_bank.update({payment['payment_bank']:[0.0,{},0.0]})

					ws.write(rowcount, 7, payment['nego_bank'],normal_style)
					if payment['nego_bank'] and len(payment['nego_bank'])>max_width_col[7]:
						max_width_col[7]=len(payment['nego_bank'])

					ws.write(rowcount, 8, payment['nego_cury'],normal_style)
					ws.write(rowcount, 9, payment['sales_amt'],normal_style_float)
					summary_per_bank[payment['payment_bank']][0]+=payment['sales_amt']
					
					ws.write(rowcount, 10, payment['bl_date'],normal_style_float)
					ws.write(rowcount, 11, payment['nego_date'],normal_style_float)
					ws.write(rowcount, 12, payment['due_date'],normal_style_float)
					ws.write(rowcount, 13, payment['coll_days'],normal_style_float)
					ws.write(rowcount, 14, payment['usance_days'],normal_style_float)
					net_amount = payment['received_amt']
					if chg:
						c = 15
						for k in chg:
							if k not in summary_per_bank[payment['payment_bank']][1].keys():
								summary_per_bank[payment['payment_bank']][1].update({k:0.0})
							ws.write(rowcount,c, (-1*payment[k]), normal_style_float)
							summary_per_bank[payment['payment_bank']][1][k]+=(-1*payment[k])
							
							c+=1
							net_amount += payment[k]
						ws.write(rowcount, c, net_amount,normal_style_float)
						summary_per_bank[payment['payment_bank']][2]+=net_amount
					
					else:
						ws.write(rowcount,15, (-1*payment['chg_amt_others']), normal_style_float)
						
						if 'chg_amt_others' not in summary_per_bank[payment['payment_bank']][1].keys():
							summary_per_bank[payment['payment_bank']][1].update({'chg_amt_others':0.0})
						summary_per_bank[payment['payment_bank']][1]['chg_amt_others']+=(-1*payment['chg_amt_others'])

						net_amount = payment['received_amt'] + payment['chg_amt_others']
						ws.write(rowcount, 16, net_amount,normal_style_float)
						
						summary_per_bank[payment['payment_bank']][2]+=net_amount
				# END:::: Write Datas Content for Export Payment
				# :::: Write Datas Content for Local Payment
				else:
					ws.write(rowcount, 3, payment['giro_no'],normal_style)
					if payment['giro_no'] and len(payment['giro_no'])>max_width_col[3]:
						max_width_col[3]=len(payment['giro_no'])
					
					ws.write(rowcount, 4, payment['customer'],normal_style)
					if payment['customer'] and len(payment['customer'])>max_width_col[4]:
						max_width_col[4]=len(payment['customer'])
					
					ws.write(rowcount, 5, payment['payment_bank'],normal_style)
					if payment['payment_bank'] and len(payment['payment_bank'])>max_width_col[5]:
						max_width_col[5]=len(payment['payment_bank'])
					if payment['payment_bank'] not in summary_per_bank:
						summary_per_bank.update({payment['payment_bank']:0.0})
					
					ws.write(rowcount, 6, payment['received_amt'],normal_style_float)
					ws.write(rowcount, 7, payment['cash_amt'],normal_style_float)
					ws.write(rowcount, 8, payment['others_amt'],normal_style_float)
					ws.write(rowcount, 9, (-1*payment['chg_amt']),normal_style_float)
					net_amount = payment['received_amt'] + payment['chg_amt']
					ws.write(rowcount, 10, net_amount, normal_style_float)
					summary_per_bank[payment['payment_bank']]+=net_amount
					ws.write(rowcount, 11, payment['payment_advice'],normal_style)
					if payment['payment_advice'] and len(payment['payment_advice'])>max_width_col[11]:
						max_width_col[11]=len(payment['payment_advice'])

					ws.write(rowcount, 12, payment['batch'],normal_style)
					if payment['batch'] and len(payment['batch'])>max_width_col[12]:
						max_width_col[12]=len(payment['batch'])
				# END:::: Write Datas Content for Local Payment
				rowcount+=1
				
				# :::: Increment Subtotal
				if sale_type=='export':
					subtotal[1]+=payment['sales_amt']
					if chg:
						s = 2
						for k in chg:
							subtotal[s]+=(-1*payment[k])
							s+=1
						subtotal[s]+=net_amount
					else:
						subtotal[2]+=(-1*payment['chg_amt_others'])
						subtotal[3]+=net_amount
				else:
					subtotal[1]+=payment['received_amt']
					subtotal[2]+=payment['cash_amt']
					subtotal[3]+=payment['others_amt']
					subtotal[4]+=(-1*payment['chg_amt'])
					subtotal[5]+=net_amount
				# END:::: Increment Subtotal
			
			# :::: Write Subtotal and Increment GrandTotal
			if sale_type=="export":
				ws.write_merge(rowcount,rowcount,0,8, "Subtotal",subtotal_style)
				ws.write(rowcount, 9, subtotal[1],subtotal_style2)
				total[1] += subtotal[1]
				ws.write_merge(rowcount,rowcount,10,14, "",subtotal_style)
				if chg:
					c = 15
					s = 2
					for k in chg:
						ws.write(rowcount, c, subtotal[s],subtotal_style2)
						total[s] += subtotal[s]
						c+=1
						s+=1
					ws.write(rowcount, c, subtotal[s],subtotal_style2)
					total[s] += subtotal[s]
				else:
					ws.write(rowcount, 15, subtotal[2],subtotal_style2)
					ws.write(rowcount, 16, subtotal[3],subtotal_style2)
					total[2] += subtotal[2]
					total[3] += subtotal[3]
			else:
				ws.write_merge(rowcount,rowcount,4,5, "Subtotal",subtotal_style)
				s = 1
				for c in range(6,11):
					ws.write(rowcount, c, subtotal[s],subtotal_style2)
					s+=1
				for t in range(1,9):
					total[t]+=subtotal[t]
			# END:::: Write Subtotal and Increment GrandTotal
			rowcount+=1

		# :::: Write Grand Total
		if sale_type=="export":
			ws.write_merge(rowcount,rowcount,0,8, "Total",subtotal_style)
			ws.write(rowcount, 9, total[1],subtotal_style2)
			if total[1] and len(str(total[1]))>max_width_col[9]:
				max_width_col[9]=len(str(total[1]))
			ws.write_merge(rowcount,rowcount,10,14, "",subtotal_style)
			if chg:
				c, s = 15, 2
				for k in chg:
					ws.write(rowcount, c, total[s],subtotal_style2)
					if not total[s]:
						max_width_col[c] = 10
					elif total[s] and len(str(total[s]))>max_width_col[c]:
						max_width_col[c]=len(str(total[s]))
					c+=1
					s+=1
				ws.write(rowcount, c, total[s],subtotal_style2)
			else:
				ws.write(rowcount, 15, total[2],subtotal_style2)
				ws.write(rowcount, 16, total[3],subtotal_style2)
				c = 15
				for t in range(2,4):
					if total[t] and len(str(total[t]))>max_width_col[c]:
						max_width_col[c]=len(str(total[t]))
					c+=1
			rowcount+=2

			# :::: Write Summary Export Payment
			ws.write_merge(rowcount,rowcount+1,9,12,'Payment\nBank', th_both_style)
			ws.write_merge(rowcount,rowcount+1,13,14,'Received\nAmount', th_both_style)
			if chg:
				ws.write_merge(rowcount,rowcount,15,14+len(chg), "C h a r g e s", th_both_style)
				c = 15
				for k in chg:
					ws.write(rowcount+1,c, k, th_both_style)
					c+=1
				ws.write_merge(rowcount,rowcount+1,c,c, "N e t\nRealisation", th_both_style)

			else:
				ws.write_merge(rowcount,rowcount+1,15,15, "Chg\nOthers", th_both_style)
				ws.write_merge(rowcount,rowcount+1,16,16, "Net Realisation\n(USD)", th_both_style)
				
			if summary_per_bank:
				rowcount+=2
				totalsumarry = {1:0}
				if chg:
					s = 2
					for k in chg:
						totalsumarry.update({s:0})
						s+=1
						c+=1
					totalsumarry.update({s:0})
				else:
					totalsumarry.update({2:0,3:0})

				for summ in summary_per_bank.keys():
					ws.write_merge(rowcount,rowcount,9,12,summ,normal_bold_style_a)
					ws.write_merge(rowcount,rowcount,13,14,summary_per_bank[summ][0],normal_style_float_bold)
					totalsumarry[1]+=summary_per_bank[summ][0]
					if chg:
						c, s = 15, 2
						for k in chg:
							ws.write(rowcount, c, summary_per_bank[summ][1][k],normal_style_float_bold)
							totalsumarry[s]+=summary_per_bank[summ][1][k]
							c+=1
							s+=1
						ws.write(rowcount, c, summary_per_bank[summ][2],normal_style_float_bold)
						totalsumarry[s]+=summary_per_bank[summ][2]
					else:
						ws.write(rowcount, 15, summary_per_bank[summ][1]['chg_amt_others'],normal_style_float_bold)
						ws.write(rowcount, 16, summary_per_bank[summ][2],normal_style_float_bold)
						totalsumarry[2]+=summary_per_bank[summ][1]['chg_amt_others']
						totalsumarry[3]+=summary_per_bank[summ][2]
					rowcount+=1
				
				ws.write_merge(rowcount,rowcount,9,12,"Total :", subtotal_style2)
				ws.write_merge(rowcount,rowcount,13,14,totalsumarry[1], subtotal_style2)
				if chg:
					c, s = 15, 2
					for k in chg:
						ws.write(rowcount, c, totalsumarry[s], subtotal_style2)
						c+=1
						s+=1
					ws.write(rowcount, c, totalsumarry[s], subtotal_style2)
				else:
					ws.write(rowcount, 15, totalsumarry[2], subtotal_style2)
					ws.write(rowcount, 16, totalsumarry[2], subtotal_style2)
				rowcount+=1
			# END:::: Write Summary Export Payment
		else:
			ws.write_merge(rowcount,rowcount,4,5, "Total",subtotal_style)
			s = 1
			for c in range(6,11):
				ws.write(rowcount, c, total[s],subtotal_style2)
				s+=1
			c = 6
			for t in range(1,9):
				if total[t] and len(str(total[t]))>max_width_col[c]:
					max_width_col[c]=len(str(total[t]))
				c+=1
			rowcount+=2

			ws.write(rowcount,6,'Total',subtotal_style)
			rowcount+=1
			# :::: Write Summary Local Payment
			if summary_per_bank:
				gtotal = 0
				for k in summary_per_bank.keys():
					ws.write(rowcount,5,k,normal_bold_style_a)
					ws.write(rowcount,6,summary_per_bank[k],normal_style_float_bold)
					gtotal+=summary_per_bank[k]
					rowcount+=1
				ws.write(rowcount,6,gtotal,subtotal_style2)
			# END:::: Write Summary Local Payment
		# :::: Write Grand Total
		rowcount+=1
		for indx in range(0,len(max_width_col.keys())):
			ws.col(indx).width = 256 * int(max_width_col[indx]*1.4)
		pass

sales_payment_realisation_xls('report.sales.payment.realisation.export','sales.payment.realisation.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=sales_payment_realisation_parser, header=False)
sales_payment_realisation_xls('report.sales.payment.realisation.local','sales.payment.realisation.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=sales_payment_realisation_parser, header=False)