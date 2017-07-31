import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
 
class aging_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(aging_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			# 'get_result':self._get_result,
		})

	def _get_invoice_ap_balance(self, data):
		cr = self.cr
		uid = self.uid
		
		# initialize pooler obj
		am_obj = self.pool.get('account.move')
		aml_obj = self.pool.get('account.move.line')
		ai_obj = self.pool.get('account.invoice')
		rp_obj = self.pool.get('res.partner')
		
		as_on_date = data['form']['as_on_date']
		period_length = data['form']['period_length'] or 30
		journal_ids = data['form']['journal_ids']
		account_ids = data['form']['account_ids']
		
		supplier_ids = data['form']['partner_ids'] and data['form']['partner_ids'] or rp_obj.search(cr, uid, [('supplier','=',True)])
		# ar transaction ,('journal_id','in',journal_ids)
		aml_ids = aml_obj.search(cr, uid, [('account_id','in',account_ids),('journal_id.type','!=','situation'),('state','=','valid'),('partner_id','in',supplier_ids),('date','<=',as_on_date)])
		
		if not aml_ids:
			return {}

		invoices = {}
		invoices_refund = {}
		advances = []
		debit_notes = []
		credit_notes = []
		# take the invoices account move line object and put it into list of advance
		for aml in aml_obj.browse(cr, uid, aml_ids):
			# invoice
			if aml.invoice and aml.credit and not aml.debit:
				if aml.invoice not in invoices:
					invoices.update({aml.invoice:[]})
				invoices[aml.invoice].append(aml)   
			# invoice refund
			if aml.invoice and aml.debit and not aml.credit:
				if aml.invoice not in invoices_refund:
					invoices_refund.update({aml.invoice:[]})
				invoices_refund[aml.invoice].append(aml)
			# debit/credit note or opening
			if not aml.invoice and aml.credit and not aml.debit and aml not in debit_notes:
				debit_notes.append(aml)
			if not aml.invoice and aml.debit and not aml.credit and aml not in credit_notes:
				credit_notes.append(aml)

		# ============== MAPPING FOR RETURN VALUE =================
		res_grouped = {}
		for k,v in invoices.items()+invoices_refund.items():
			# temp var for ageing detail
			move = k.move_id.name
			ref = k.reference or k.internal_number
			balance, balance2, balance_usd = 0.0, 0.0, 0.0 # balance : balance asli, balance_usd : balance dalam usd, balance2 : dummy untuk menghitung balance jika mata uang move-nya bukan usd
			amount_not_due, amount_overdue = 0.0, 0.0
			# temp var for ageing summary
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]
			date_maturity = False
			currency = k.currency_id.name
			for aml_ap in v:
				sign = -1
				balance_aml_ap = 0.0 # karena 1 invoice bisa memiliki lebih dari 1 move_line, maka dibuat penampung per move_ap agar nanti total overdue amountnya diakumulasi per invoice
				if k.currency_id.id!=k.company_id.currency_id.id:
					balance += sign*aml_ap.amount_currency
					balance_aml_ap += sign*aml_ap.amount_currency
					balance_usd += sign*(aml_ap.debit-aml_ap.credit)
					balance2 += sign*(aml_ap.debit-aml_ap.credit)
				else:
					balance += sign*(aml_ap.debit-aml_ap.credit)
					balance_aml_ap += sign*(aml_ap.debit-aml_ap.credit)
					balance_usd += sign*(aml_ap.debit-aml_ap.credit)
					balance2 += sign*(aml_ap.debit-aml_ap.credit)
				
				for payment in (aml_ap.reconcile_id and aml_ap.reconcile_id.line_id or (aml_ap.reconcile_partial_id and aml_ap.reconcile_partial_id.line_partial_ids or [])):
					if payment.id!=aml_ap.id and payment.date<=as_on_date:
						# sign1 = payment.debit and 1 or -1
						if k.currency_id.id!=k.company_id.currency_id.id:
							balance -= payment.amount_currency
							balance_aml_ap -= payment.amount_currency
							balance_usd -= (payment.debit - payment.credit)
							balance2 -= (payment.debit - payment.credit)
						else:
							balance -= (payment.debit - payment.credit)
							balance_aml_ap -= (payment.credit - payment.debit)
							balance_usd -= (payment.debit - payment.credit)
							balance2 -= (payment.debit - payment.credit)
				
				if k.currency_id.id!=k.company_id.currency_id.id and balance2==0.0:
					balance_aml_ap = 0.0
					balance = 0.0

				date_maturity = aml_ap.date_maturity!=False and aml_ap.date_maturity or aml_ap.date
				if date_maturity>=as_on_date:
					amount_not_due+=balance_aml_ap
				else:
					amount_overdue+=balance_aml_ap
					dateformat = '%Y-%m-%d'
					diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(date_maturity,dateformat)).days
					if diff_day<=(1*int(period_length)):
						arr_overdue_days[0]+=balance_aml_ap
					elif diff_day<=(2*int(period_length)):
						arr_overdue_days[1]+=balance_aml_ap
					elif diff_day<=(3*int(period_length)):
						arr_overdue_days[2]+=balance_aml_ap
					else:
						arr_overdue_days[3]+=balance_aml_ap
				
			if round(abs(balance),2)<0.01:
				continue

			key = (aml_ap.partner_id.id, aml_ap.partner_id.name, aml_ap.partner_id.partner_code)
			if key not in res_grouped.keys():
				res_grouped.update({key:[]})
				
			res_grouped[key].append({
					'move':move or '',
					'ref' : ref or aml_ap.ref or aml_ap.name or 'Invoice',
					# 'as_on' : dt.strptime(aml_ap.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'as_on' : aml_ap.date,
					'date_due' : date_maturity,
					'ccy' : currency,
					'amount' : balance,
					'balance' : balance,
					'amount_not_due' : amount_not_due,
					'amount_overdue' : amount_overdue,
					'amt1' : arr_overdue_days[0],
					'amt2' : arr_overdue_days[1],
					'amt3' : arr_overdue_days[2],
					'amt4' : arr_overdue_days[3],
					'balance_usd' : balance_usd,
				})

		# mapping each advance and each debit note into res_grouped
		for adv in debit_notes:
			sign = -1
			balance, balance2, balance_usd= 0.0, 0.0, 0.0
			amount_not_due, amount_overdue = 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]
			currency = adv.currency_id and adv.currency_id.name or adv.company_id.currency_id.name
			
			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
				balance = sign*adv.amount_currency
				balance_usd = sign*(adv.debit - adv.credit)
				balance2 = sign*(adv.debit - adv.credit)
			else:
				balance = sign*(adv.debit - adv.credit)
				balance_usd = sign*(adv.debit - adv.credit)
				balance2 = sign*(adv.debit - adv.credit)
			
			for payment in (adv.reconcile_id and adv.reconcile_id.line_id or (adv.reconcile_partial_id and adv.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=adv.id and payment.date<=as_on_date:
					if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
						balance-=payment.amount_currency
						balance_usd -= (payment.debit - payment.credit)
						balance2-=(payment.debit - payment.credit)
					else:
						balance-=(payment.debit - payment.credit)
						balance_usd -= (payment.debit - payment.credit)
						balance2-=(payment.debit - payment.credit)
			
			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id and balance2==0.0:
				balance=0.0
				
			date_maturity = adv.date_maturity!=False and adv.date_maturity or adv.date
			if date_maturity>=as_on_date:
				amount_not_due+=balance
			else:
				amount_overdue+=balance
				dateformat = '%Y-%m-%d'
				diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(date_maturity,dateformat)).days
				if diff_day<=(1*int(period_length)):
					arr_overdue_days[0]+=balance
				elif diff_day<=(2*int(period_length)):
					arr_overdue_days[1]+=balance
				elif diff_day<=(3*int(period_length)):
					arr_overdue_days[2]+=balance
				else:
					arr_overdue_days[3]+=balance
			

			if round(abs(balance),2)<0.01:
				continue

			key = (adv.partner_id.id, adv.partner_id.name, adv.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append({
					'move':adv.name or adv.name or (sign==-1 and 'Advance' or 'Debit Note/Opening'),
					'ref' : adv.ref or '',
					'as_on' : adv.date,
					'date_due' : date_maturity,
					'ccy' : currency,
					'amount' : balance,
					'balance' : balance,
					'amount_not_due' : amount_not_due,
					'amount_overdue' : amount_overdue,
					'amt1' : arr_overdue_days[0],
					'amt2' : arr_overdue_days[1],
					'amt3' : arr_overdue_days[2],
					'amt4' : arr_overdue_days[3],
					'balance_usd' : balance_usd,
				})

		# mapping each debit note into res_grouped
		for cr in credit_notes:
			sign = -1
			balance, balance2, balance_usd = 0.0, 0.0, 0.0
			amount_not_due, amount_overdue = 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]
			if cr.currency_id and cr.currency_id.id!=cr.company_id.currency_id.id:
				balance = sign*cr.amount_currency
				balance_usd = sign*(cr.debit - cr.credit)
				balance2 = sign*(cr.debit - cr.credit)
			else:
				balance = sign*(cr.debit - cr.credit)
				balance_usd = sign*(cr.debit - cr.credit)
				balance2 = sign*(cr.debit - cr.credit)
			
			for payment in (cr.reconcile_id and cr.reconcile_id.line_id or (cr.reconcile_partial_id and cr.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=cr.id and payment.date<=as_on_date:
					if cr.currency_id and cr.currency_id.id!=cr.company_id.currency_id.id:
						balance-=payment.amount_currency
						balance_usd-=(payment.debit - payment.credit)
						balance2-=(payment.debit - payment.credit)
					else:
						balance-=(payment.debit - payment.credit)
						balance_usd-=(payment.debit - payment.credit)
						balance2-=(payment.debit - payment.credit)

			if cr.currency_id and cr.currency_id.id!=cr.company_id.currency_id.id and balance2==0.0:
				balance = 0.0

			date_maturity = cr.date_maturity!=False and cr.date_maturity or cr.date
			if date_maturity>=as_on_date:
				amount_not_due+=balance
			else:
				amount_overdue+=balance
				dateformat = '%Y-%m-%d'
				diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(date_maturity,dateformat)).days
				if diff_day<=(1*int(period_length)):
					arr_overdue_days[0]+=balance
				elif diff_day<=(2*int(period_length)):
					arr_overdue_days[1]+=balance
				elif diff_day<=(3*int(period_length)):
					arr_overdue_days[2]+=balance
				else:
					arr_overdue_days[3]+=balance

			if round(abs(balance),2)<0.01:
				continue

			key = (cr.partner_id.id, cr.partner_id.name, cr.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append({
					'move': cr.name or (sign==-1 and 'Advance' or 'Credit Note/Opening'),
					'ref' : cr.ref or '',
					'as_on' : cr.date,
					'date_due' : date_maturity,
					'ccy' : currency,
					'amount' : balance,
					'balance' : balance,
					'amount_not_due' : amount_not_due,
					'amount_overdue' : amount_overdue,
					'amt1' : arr_overdue_days[0],
					'amt2' : arr_overdue_days[1],
					'amt3' : arr_overdue_days[2],
					'amt4' : arr_overdue_days[3],
					'balance_usd' : balance_usd,
				})
		return res_grouped


	def _get_invoice_ar_balance(self, data):
		cr = self.cr
		uid = self.uid

		# initialize pooler obj
		am_obj = self.pool.get('account.move')
		aml_obj = self.pool.get('account.move.line')
		ai_obj = self.pool.get('account.invoice')
		rp_obj = self.pool.get('res.partner')
		ip_obj = self.pool.get('ir.property')

		as_on_date = data['form']['as_on_date']
		period_length = data['form']['period_length'] or 30
		journal_ids = data['form']['journal_ids']
		account_ids = data['form']['account_ids']
		adv_account_id = data['form'].get('adv_account_id',False) and data['form']['adv_account_id'][0] or False
		show_outstanding_advance = data['form']['show_outstanding_advance']
		
		customer_ids = data['form']['partner_ids'] and data['form']['partner_ids'] or rp_obj.search(cr, uid, [('customer','=',True)])
		# ar transaction
		# aml_ids = aml_obj.search(cr, uid, [('account_id','in',account_ids),('journal_id','in',journal_ids),('state','=','valid'),('partner_id','in',customer_ids),('date','<=',as_on_date)])
		aml_ids = aml_obj.search(cr, uid, [('account_id','in',account_ids),('journal_id.type','!=','situation'),('journal_id','in',journal_ids),('state','=','valid'),('partner_id','in',customer_ids),('date','<=',as_on_date)])
		# ar advance transaction
		adv_aml_ids = []
		if show_outstanding_advance and adv_account_id:
			if account_ids:
				curr_partner_query = "SELECT a.partner_id FROM \
										(SELECT \
											cast(substring(a1.value_reference from 17 for (char_length(a1.value_reference)-16)) as integer) as property_account_receivable_id, \
											cast(substring(a1.res_id from 13 for (char_length(a1.res_id)-12)) as integer) as partner_id \
										FROM ir_property a1 \
										WHERE a1.name='property_account_receivable') a \
										LEFT JOIN res_partner b ON b.id=a.partner_id and b.customer = 't' \
									WHERE a.property_account_receivable_id in ("+','.join([str(x) for x in account_ids])+")"
				cr.execute(curr_partner_query)
				curr_partner_ids = [x[0] in customer_ids and x[0] for x in cr.fetchall()]
				
				# check if the partner is not in ir_property, it means that the receivable account was taken from default chart template
				query_account_chart_template = "SELECT c.id \
												FROM \
													account_chart_template a \
													INNER JOIN account_account_template b on b.id=a.property_account_receivable \
													INNER JOIN account_account c on c.code=b.code and c.id in ("+','.join([str(x) for x in account_ids])+")"
				cr.execute(query_account_chart_template)
				ar_from_chart_template_ids = [x[0] for x in cr.fetchall()]
				if ar_from_chart_template_ids:
					curr_partner_query2 = "SELECT a.id FROM \
											res_partner a \
										WHERE a.customer='t'\
											AND a.id not in (SELECT \
												cast(substring(a1.res_id from 13 for (char_length(a1.res_id)-12)) as integer) as partner_id \
											FROM ir_property a1 \
											WHERE a1.name='property_account_receivable' AND a1.res_id is not NULL)"
					cr.execute(curr_partner_query2)
					curr_partner_ids += [x[0] in customer_ids and x[0] for x in cr.fetchall()]
				
				if curr_partner_ids:
					adv_aml_ids = aml_obj.search(cr, uid, [('account_id','=',adv_account_id),('state','=','valid'),('partner_id','in',curr_partner_ids),('date','<=',as_on_date)])
			else:
				adv_aml_ids = aml_obj.search(cr, uid, [('account_id','=',adv_account_id),('state','=','valid'),('date','<=',as_on_date)])

		oth_aml_ids = aml_obj.search(cr, uid, [('id','not in',aml_ids+adv_aml_ids),('account_id','in',account_ids),('journal_id.type','!=','situation'),('state','=','valid'),('partner_id','in',customer_ids),('date','<=',as_on_date)])
		
		if not aml_ids and not adv_aml_ids and not oth_aml_ids:
			return {}
		
		invoices = {}
		invoices_refund = {}
		advances = []
		debit_notes = []
		credit_notes = []
		aml_negosiation_ids = []
		negos = {}
		aml_reconciled_ids = []
		# take the invoices account move line object and put it into list of advance
		for aml in aml_obj.browse(cr, uid, aml_ids):
			# invoice
			if aml.invoice and aml.debit and not aml.credit:
				if aml.invoice not in invoices:
					invoices.update({aml.invoice:[]})
				invoices[aml.invoice].append(aml)   
				# bank negotiation
				if aml.invoice.bank_negotiation_no and aml.invoice.bank_negotiation_no.liability_move_line_id and aml.invoice.bank_negotiation_no.liability_move_line_id.date<=as_on_date:
					aml_negosiation_ids.append(aml.id)
			# invoice refund
			if aml.invoice and aml.credit and not aml.debit:
				if aml.invoice not in invoices_refund:
					invoices_refund.update({aml.invoice:[]})
				invoices_refund[aml.invoice].append(aml)
			# debit/credit note or opening
			if not aml.invoice and aml.debit and not aml.credit and aml not in debit_notes:
				debit_notes.append(aml)
			if not aml.invoice and aml.credit and not aml.debit and aml not in credit_notes:
				credit_notes.append(aml)

		# take the advances account move line object and put it into list of advance
		if adv_aml_ids:
			for aml in aml_obj.browse(cr, uid, adv_aml_ids): 
				# advance
				if not aml.invoice and aml.credit and not aml.debit and aml not in advances:
					advances.append(aml)

				if not aml.invoice and aml.debit and not aml.credit and aml not in debit_notes:
					debit_notes.append(aml)
		# take other moves that is not included in inv or advance
		if oth_aml_ids:
			for aml in aml_obj.browse(cr, uid, oth_aml_ids):
				# debit/credit note or opening
				if not aml.invoice and aml.debit and not aml.credit and aml not in debit_notes:
					debit_notes.append(aml)
				if not aml.invoice and aml.credit and not aml.debit and aml not in credit_notes:
					credit_notes.append(aml)	
		# ============== MAPPING FOR RETURN VALUE =================
		# for ageing detail
		res_grouped = {}
		# for ageing summary
		res_grouped2 = {}
		# mapping invoice list into res
		for k,v in invoices.items()+invoices_refund.items():
			# temp var for ageing detail
			ref = k.internal_number
			as_on, ppn = False, False
			amount, balance, balance2, nego_amount, nego_amount_used = 0.0, 0.0, 0.0, 0.0, 0.0
			# temp var for ageing summary
			amount_not_due, amount_overdue, pending_nego = 0.0, 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]

			date_maturity = False
			# if k.bank_negotiation_no and k.bank_negotiation_no.liability_move_line_id and not k.bank_negotiation_no.liability_move_line_id.reconcile_id:
			#   nego_amount = k.bank_negotiation_no.liability_move_line_id.reconcile_partial_id and k.bank_negotiation_no.liability_move_line_id.amount_residual or k.bank_negotiation_no.liability_move_line_id.credit
			if k.bank_negotiation_no and k.bank_negotiation_no.liability_move_line_id and k.bank_negotiation_no.liability_move_line_id.date<=as_on_date:
				if k.currency_id.id!=k.company_id.currency_id.id:
					nego_amount = abs(k.bank_negotiation_no.liability_move_line_id.amount_currency)
					nego_amount_used = abs(k.bank_negotiation_no.liability_move_line_id.amount_currency)
				else:
					nego_amount = k.bank_negotiation_no.liability_move_line_id.credit
					nego_amount_used = k.bank_negotiation_no.liability_move_line_id.credit
				if k.bank_negotiation_no.liability_move_line_id.reconcile_id:
					for rec_line in k.bank_negotiation_no.liability_move_line_id.reconcile_id.line_id:
						if rec_line.id!=k.bank_negotiation_no.liability_move_line_id.id and rec_line.date<=as_on_date:
							if k.currency_id.id!=k.company_id.currency_id.id:
								nego_amount-=rec_line.amount_currency
							else:
								nego_amount-=(rec_line.debit - rec_line.credit)
				if k.bank_negotiation_no.liability_move_line_id.reconcile_partial_id:
					for rec_line in k.bank_negotiation_no.liability_move_line_id.reconcile_partial_id.line_partial_ids:
						if rec_line.id!=k.bank_negotiation_no.liability_move_line_id.id and rec_line.date<=as_on_date:
							if k.currency_id.id!=k.company_id.currency_id.id:
								nego_amount-=rec_line.amount_currency
							else:
								nego_amount-=(rec_line.debit - rec_line.credit)

			for aml_ar in sorted(v, key=lambda x:x.date_maturity):
				# append this id into reconciled ids. This is to evade double checking
				aml_reconciled_ids.append(aml_ar.id)

				sign = aml_ar.debit and 1 or -1
				balance_aml_ar = 0.0
				# if k.currency_id.id!=k.company_id.currency_id.id and aml_ar.account_id.currency_id and aml_ar.amount_currency!=0.0:
				if k.currency_id.id!=k.company_id.currency_id.id and aml_ar.account_id.currency_id:
					amount += aml_ar.amount_currency
					balance2 += aml_ar.debit-aml_ar.credit
					balance += aml_ar.amount_currency
					balance_aml_ar += aml_ar.amount_currency
				else:
					amount += aml_ar.debit-aml_ar.credit
					balance += aml_ar.debit-aml_ar.credit
					balance_aml_ar += aml_ar.debit-aml_ar.credit
				for payment in (aml_ar.reconcile_id and aml_ar.reconcile_id.line_id or (aml_ar.reconcile_partial_id and aml_ar.reconcile_partial_id.line_partial_ids or [])):
					if payment.id!=aml_ar.id and payment.date<=as_on_date:
						# append this id into reconciled ids. This is to evade double checking
						aml_reconciled_ids.append(payment.id)
						
						sign1 = payment.debit and 1 or -1
						if k.currency_id.id!=k.company_id.currency_id.id and payment.account_id.currency_id:
							balance2-=(payment.credit - payment.debit)
							balance-=sign1*payment.amount_currency
							balance_aml_ar -= sign1*payment.amount_currency
						else:
							balance-=(payment.credit - payment.debit)
							balance_aml_ar -= (payment.credit - payment.debit)
				
				if k.currency_id.id!=k.company_id.currency_id.id and aml_ar.account_id.currency_id and balance2==0.0:
				# if k.currency_id.id!=k.company_id.currency_id.id and aml_ar.account_id.currency_id and aml_ar.amount_currency!=0.0 and balance2==0.0:
					balance_aml_ar=0.0
					balance=0.0

				if aml_ar.ar_ap_tax:
					ppn = True
				date_maturity = aml_ar.date
				if aml_ar.date_maturity!=False:
					date_maturity = aml_ar.date_maturity
					if aml_ar.date_maturity>=as_on_date:
						amount_not_due+=balance_aml_ar
					else:
						amount_overdue+=balance_aml_ar
						dateformat = '%Y-%m-%d'
						diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(aml_ar.date_maturity,dateformat)).days
						if diff_day<=(1*int(period_length)):
							arr_overdue_days[0]+=balance_aml_ar
						elif diff_day<=(2*int(period_length)):
							arr_overdue_days[1]+=balance_aml_ar
						elif diff_day<=(3*int(period_length)):
							arr_overdue_days[2]+=balance_aml_ar
						else:
							arr_overdue_days[3]+=balance_aml_ar
				
			if round(abs(balance),2)<0.01 and round(abs(balance2),2)<0.01:
				continue

			key = (aml_ar.partner_id.id, aml_ar.partner_id.name, aml_ar.partner_id.partner_code)
			if key not in res_grouped.keys():
				res_grouped.update({key:[]})
				
			res_grouped[key].append({
					'ref' : ref or aml_ar.ref or aml_ar.name or 'Invoice',
					'with_ppn' : True,
					'as_on' : dt.strptime(aml_ar.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'due_date' : dt.strptime(date_maturity or aml_ar.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'amount' : balance,
					'nego_amount' : nego_amount,
					'balance' : balance,
					'balance_usd' : balance2,
				})

			if key not in res_grouped2.keys():
				res_grouped2.update({key:{
					'balance':0.0,
					'balance_usd' : 0.0,
					'amount_not_due' : 0.0,
					'nego_amount' : 0.0,
					'amount_overdue' : 0.0,
					'amt1' : 0.0,
					'amt2' : 0.0,
					'amt3' : 0.0,
					'amt4' : 0.0,
					'pending_nego' : 0.0,
					}})

			res_grouped2[key]['balance'] += balance
			res_grouped2[key]['balance_usd'] += balance2
			res_grouped2[key]['amount_not_due'] += amount_not_due
			res_grouped2[key]['nego_amount'] += nego_amount
			res_grouped2[key]['amount_overdue'] += amount_overdue
			res_grouped2[key]['amt1'] += arr_overdue_days[0]
			res_grouped2[key]['amt2'] += arr_overdue_days[1]
			res_grouped2[key]['amt3'] += arr_overdue_days[2]
			res_grouped2[key]['amt4'] += arr_overdue_days[3]
		
		# mapping each advance and each credit note into res_grouped
		for adv in sorted(advances+credit_notes, key=lambda x:x.date_maturity):
			# append this id into reconciled ids. This is to evade double checking
			if adv.id not in aml_reconciled_ids:
				aml_reconciled_ids.append(adv.id)
			else:
				continue
			
			sign = adv.debit and 1 or -1
			amount, balance_aml_ar, balance, balance2 = 0.0, 0.0, 0.0, 0.0
			amount_not_due, amount_overdue, pending_nego = 0.0, 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]
			
			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
			# if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id and adv.amount_currency!=0.0:
				balance2 = adv.debit - adv.credit
				amount = adv.amount_currency
				balance = adv.amount_currency
				balance_aml_ar = adv.amount_currency
			else:
				amount = adv.debit - adv.credit
				balance = adv.debit - adv.credit
				balance_aml_ar = adv.debit - adv.credit
			for payment in (adv.reconcile_id and adv.reconcile_id.line_id or (adv.reconcile_partial_id and adv.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=adv.id and payment.date<=as_on_date:
					# append this id into reconciled ids. This is to evade double checking
					aml_reconciled_ids.append(payment.id)
					
					if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
						balance2+=(payment.debit - payment.credit)
						balance+=payment.amount_currency
						balance_aml_ar+=payment.amount_currency
					else:
						balance+=(payment.debit - payment.credit)
						balance_aml_ar+=(payment.debit - payment.credit)
			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id and balance2==0.0:
			# if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id and adv.amount_currency!=0.0 and balance2==0.0:
				balance=0.0

			date_maturity = adv.date_maturity!=False and adv.date_maturity or adv.date
			if date_maturity>=as_on_date:
				amount_not_due+=balance_aml_ar
			else:
				amount_overdue+=balance_aml_ar
				dateformat = '%Y-%m-%d'
				diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(date_maturity,dateformat)).days
				if diff_day<=(1*int(period_length)):
					arr_overdue_days[0]+=balance_aml_ar
				elif diff_day<=(2*int(period_length)):
					arr_overdue_days[1]+=balance_aml_ar
				elif diff_day<=(3*int(period_length)):
					arr_overdue_days[2]+=balance_aml_ar
				else:
					arr_overdue_days[3]+=balance_aml_ar
			

			if round(abs(balance),2)<0.01 and round(abs(balance2),2)<0.01:
				continue
			key = (adv.partner_id.id, adv.partner_id.name, adv.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append({
					'ref' : adv.ref or adv.name or (sign==-1 and 'Advance' or 'Debit Note/Opening'),
					'as_on' : dt.strptime(adv.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'due_date' : dt.strptime(date_maturity, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'amount' : balance,
					'nego_amount' : 0.0,
					'balance' : balance,
					'balance_usd' : balance2,
				})


			if key not in res_grouped2.keys():
				res_grouped2.update({key:{
					'balance':0.0,
					'balance_usd':0.0,
					'amount_not_due' : 0.0,
					'nego_amount' : 0.0,
					'amount_overdue' : 0.0,
					'amt1' : 0.0,
					'amt2' : 0.0,
					'amt3' : 0.0,
					'amt4' : 0.0,
					'pending_nego' : 0.0,
					}})

			res_grouped2[key]['balance'] += balance
			res_grouped2[key]['balance_usd'] += balance2
			res_grouped2[key]['amount_not_due'] += amount_not_due
			res_grouped2[key]['nego_amount'] += 0.0
			res_grouped2[key]['amount_overdue'] += amount_overdue
			res_grouped2[key]['amt1'] += arr_overdue_days[0]
			res_grouped2[key]['amt2'] += arr_overdue_days[1]
			res_grouped2[key]['amt3'] += arr_overdue_days[2]
			res_grouped2[key]['amt4'] += arr_overdue_days[3]

		# mapping each debit note into res_grouped
		for dn in sorted(debit_notes, key=lambda x: x.date_maturity):
			# append this id into reconciled ids. This is to evade double checking
			if dn.id not in aml_reconciled_ids:
				aml_reconciled_ids.append(dn.id)
			else:
				continue
			sign = dn.debit and 1 or -1
			amount_not_due, amount_overdue = 0.0, 0.0
			amount, balance, balance_aml_ar, balance2 = 0.0, 0.0, 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]

			if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id:
			# if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id and dn.amount_currency!=0.0:
				balance2 = dn.debit - dn.credit
				amount = dn.amount_currency
				balance = dn.amount_currency
				balance_aml_ar = dn.amount_currency
			else:
				amount = dn.debit - dn.credit
				balance = dn.debit - dn.credit
				balance_aml_ar = dn.debit - dn.credit
			for payment in (dn.reconcile_id and dn.reconcile_id.line_id or (dn.reconcile_partial_id and dn.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=dn.id and payment.date<=as_on_date:
					# append this id into reconciled ids. This is to evade double checking
					aml_reconciled_ids.append(payment.id)
					
					if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id:
						balance2+=(payment.debit - payment.credit)
						balance+=payment.amount_currency
						balance_aml_ar+=payment.amount_currency
					else:
						balance+=(payment.debit - payment.credit)
						balance_aml_ar+=(payment.debit - payment.credit)
			# if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id and dn.amount_currency!=0.0 and balance2==0.0:
			if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id and balance2==0.0:
				balance = 0.0

			date_maturity = dn.date_maturity!=False and dn.date_maturity or dn.date
			if date_maturity>=as_on_date:
				amount_not_due+=balance_aml_ar
			else:
				amount_overdue+=balance_aml_ar
				dateformat = '%Y-%m-%d'
				diff_day = (dt.strptime(as_on_date,dateformat)-dt.strptime(date_maturity,dateformat)).days
				if diff_day<=(1*int(period_length)):
					arr_overdue_days[0]+=balance_aml_ar
				elif diff_day<=(2*int(period_length)):
					arr_overdue_days[1]+=balance_aml_ar
				elif diff_day<=(3*int(period_length)):
					arr_overdue_days[2]+=balance_aml_ar
				else:
					arr_overdue_days[3]+=balance_aml_ar

			if round(abs(balance),2)<0.01 and round(abs(balance2),2)<0.01:
				continue

			key = (dn.partner_id.id, dn.partner_id.name, dn.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append({
					'ref' : dn.ref or dn.name or (sign==-1 and 'Advance' or 'Debit Note/Opening'),
					'as_on' : dt.strptime(adv.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'due_date' : dt.strptime(date_maturity, '%Y-%m-%d').strftime('%d/%m/%Y'),
					'amount' : balance,
					'nego_amount' : 0.0,
					'balance' : balance,
					'balance_usd' : balance2,
				})


			if key not in res_grouped2.keys():
				res_grouped2.update({key:{
					'balance':0.0,
					'balance_usd':0.0,
					'amount_not_due' : 0.0,
					'nego_amount' : 0.0,
					'amount_overdue' : 0.0,
					'amt1' : 0.0,
					'amt2' : 0.0,
					'amt3' : 0.0,
					'amt4' : 0.0,
					'pending_nego' : 0.0,
					}})

			res_grouped2[key]['balance'] += balance
			res_grouped2[key]['balance_usd'] += balance2
			res_grouped2[key]['amount_not_due'] += amount_not_due
			res_grouped2[key]['nego_amount'] += 0.0
			res_grouped2[key]['amount_overdue'] += amount_overdue
			res_grouped2[key]['amt1'] += arr_overdue_days[0]
			res_grouped2[key]['amt2'] += arr_overdue_days[1]
			res_grouped2[key]['amt3'] += arr_overdue_days[2]
			res_grouped2[key]['amt4'] += arr_overdue_days[3]

		return res_grouped, res_grouped2
			
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

class aging_report_xls(report_xls):
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
		ws = wb.add_sheet('Aging Report',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		title_style = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert centre, horiz center; ')
		title2 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz center;' "borders:top thin, bottom thin")
		title3 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert bottom, horiz center;' "borders:bottom thin")
		title4 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;' "borders:bottom thin")
		title5 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz left;' "borders:bottom thin")
		title7 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert bottom, horiz right;' "borders:bottom thin")
		title8 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz center;' "borders:bottom thin")
		title9 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz left;')
		label = xlwt.easyxf('font : name calibri, colour_index black; align: vert centre, horiz center;' "borders:top dashed, bottom thin")
		body_detail2 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;')
		body_detail = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz center;' "borders:top thin, bottom thin")
		body_detail3 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;', num_format_str='#,##0.00;-#,##0.00')
		body_detail4 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;' "borders:top thin, bottom thin", num_format_str='#,##0.00;-#,##0.00')

		if data['form']['account_type']=='receivable':
			ws.write_merge(0,0,0,12, "PT. Bitratex Industries", title_style)
			ws.write_merge(1,1,0,12, "RECEIVABLES AGEING STATEMENT", title_style)
			ws.write_merge(2,2,0,12, "As On: " + data['form']['as_on_date'], title_style)

			ws.write_merge(4,6,0,0, "No.", title2)
			ws.write_merge(4,5,1,2, "Customer", title2)
			ws.write(6,1, "Code", title4)
			ws.write(6,2, "Name", title8)
			ws.write_merge(4,6,3,3, "AMOUNT\nBALANCE", title2)
			ws.write_merge(4,6,4,4, "AMOUNT\nBALANCE\nUSD", title2)
			ws.write_merge(4,6,5,5, "NEGO'N\nAMOUNT", title2)
			ws.write_merge(4,6,6,6, "AMOUNT\nNOT DUE", title2)
			ws.write_merge(4,6,7,7, "AMOUNT\nOVERDUE", title2)
			ws.write_merge(4,4,8,11, "OVERDUE - DAYS", title2)

			period_length = data['form']['period_length'] or 30
			next_period = 0
			for i in range(0,3):
				ws.write_merge(5,6,i+8,i+8, str(next_period+1)+"-"+str(next_period+period_length),title3)
				next_period += period_length
			ws.write_merge(5,6,11,11, ">"+str(next_period),title4)
			ws.write_merge(4,6,12,12, "PENDING\nNEGO", title2)
			
			
			rowcount=7
			max_width_col_0=0
			max_width_col_1=0
			max_width_col_2=0
			max_width_col_3=5
			max_width_col_4=5
			max_width_col_5=5
			max_width_col_6=5
			max_width_col_7=5
			max_width_col_8=5
			max_width_col_9=5
			max_width_col_10=5
			max_width_col_11=5
			max_width_col_12=5
			total_3 = 0
			total_4 = 0
			total_5 = 0
			total_6 = 0
			total_7 = 0
			total_8 = 0
			total_9 = 0
			total_10 = 0
			total_11 = 0
			total_12 = 0
			
			all_results = parser._get_invoice_ar_balance(data)
			results1 = all_results[1]
			n = 0
			for key in sorted(results1.keys(), key=lambda k:(k[1][:1],k[2])):
				n+=1
				ws.write(rowcount,0,n)
				ws.write(rowcount,1,str(key[2]))
				ws.write(rowcount,2,str(key[1]))
				if len(key[1] and str(key[1]) or '')>max_width_col_2:
					max_width_col_2 = len(str(key[1]))      
				ws.write(rowcount,3,results1[key]['balance'], body_detail3)
				if len(results1[key]['balance'] and str(results1[key]['balance']) or '')>max_width_col_3:
					max_width_col_3 = len(str(results1[key]['balance']))
				total_3 += results1[key]['balance']
				ws.write(rowcount,4,results1[key]['balance_usd'], body_detail3)
				if len(results1[key]['balance_usd'] and  str(results1[key]['balance_usd']) or '')>max_width_col_4:
					max_width_col_4 = len(str(results1[key]['balance_usd']))
				total_4 += results1[key]['balance_usd']
				ws.write(rowcount,5,results1[key]['nego_amount'], body_detail3)
				if len(results1[key]['nego_amount'] and  str(results1[key]['nego_amount']) or '')>max_width_col_5:
					max_width_col_5 = len(str(results1[key]['nego_amount']))
				total_5 += results1[key]['nego_amount']
				ws.write(rowcount,6,results1[key]['amount_not_due'], body_detail3)
				if len(results1[key]['amount_not_due'] and  str(results1[key]['amount_not_due']) or '')>max_width_col_6:
					max_width_col_6 = len(str(results1[key]['amount_not_due']))
				total_6 += results1[key]['amount_not_due']
				ws.write(rowcount,7,results1[key]['amount_overdue'], body_detail3)
				if len(results1[key]['amount_overdue'] and str(results1[key]['amount_overdue']) or '')>max_width_col_7:
					max_width_col_7 = len(str(results1[key]['amount_overdue']))
				total_7 += results1[key]['amount_overdue']
				ws.write(rowcount,8,results1[key]['amt1'], body_detail3)
				if len(results1[key]['amt1'] and str(results1[key]['amt1']) or '')>max_width_col_8:
					max_width_col_8 = len(str(results1[key]['amt1']))
				total_8 += results1[key]['amt1']
				ws.write(rowcount,9,results1[key]['amt2'], body_detail3)
				if len(results1[key]['amt2'] and str(results1[key]['amt2']) or '')>max_width_col_9:
					max_width_col_9 = len(str(results1[key]['amt2']))
				total_9 += results1[key]['amt2']
				ws.write(rowcount,10,results1[key]['amt3'], body_detail3)
				if len(results1[key]['amt3'] and str(results1[key]['amt3']) or '')>max_width_col_10:
					max_width_col_10 = len(str(results1[key]['amt3']))
				total_10 += results1[key]['amt3']
				ws.write(rowcount,11,results1[key]['amt4'], body_detail3)
				if len(results1[key]['amt4'] and str(results1[key]['amt4']) or '')>max_width_col_11:
					max_width_col_11 = len(str(results1[key]['amt4']))
				total_11 += results1[key]['amt4']
				pending_nego = results1[key]['balance']-results1[key]['nego_amount']
				ws.write(rowcount,12,pending_nego, body_detail3)
				if len(pending_nego and str(pending_nego) or '')>max_width_col_12:
					max_width_col_12 = len(str(pending_nego))
				total_12 += pending_nego
				rowcount=rowcount+1
			
			ws.write_merge(rowcount,rowcount,0,2,  "Grand Total : ", body_detail)
			ws.write(rowcount,3, total_3, body_detail4)
			ws.write(rowcount,4, total_4, body_detail4)
			ws.write(rowcount,5, total_5, body_detail4)
			ws.write(rowcount,6, total_6, body_detail4)
			ws.write(rowcount,7, total_7, body_detail4)
			ws.write(rowcount,8, total_8, body_detail4)
			ws.write(rowcount,9, total_9, body_detail4)
			ws.write(rowcount,10, total_10, body_detail4)
			ws.write(rowcount,11, total_11, body_detail4)
			ws.write(rowcount,12, total_12, body_detail4)
			# ws.write(rowcount,13, total_13, body_detail4)
			# ws.write(rowcount,14, total_14, body_detail4)
			
			ws.col(2).width = 256*int(max_width_col_2*1.4)
			ws.col(3).width = 256*int(max_width_col_3*1.4)
			ws.col(4).width = 256*int(max_width_col_3*1.4)
			ws.col(5).width = 256*int(max_width_col_5*1.4)
			ws.col(6).width = 256*int(max_width_col_6*1.4)
			ws.col(7).width = 256*int(max_width_col_7*1.4)
			ws.col(8).width = 256*int(max_width_col_8*1.4)
			ws.col(9).width = 256*int(max_width_col_9*1.4)
			ws.col(10).width = 256*int(max_width_col_10*1.4)
			ws.col(11).width = 256*int(max_width_col_11*1.4)
			ws.col(12).width = 256*int(max_width_col_12*1.4)
		
			ws1 = wb.add_sheet('STATEMENT DETAIL',cell_overwrite_ok=True)
			
			ws1.write_merge(0,0,0,8, "PT.Bitratex Industries", title_style)
			ws1.write_merge(1,1,0,8, "STATEMENT OF ACCOUNT RECEIVABLES DETAIL", title_style)
			ws1.write_merge(2,2,0,8, "As On:" + dt.strptime(data['form']['as_on_date'], '%Y-%m-%d').strftime('%d/%m/%Y'), title_style)

			ws1.write(4,0, "Customer Code", title2)
			ws1.write(4,1, "Customer Name", title2)
			ws1.write(4,2, "Reference", title2)
			ws1.write(4,3, "Date Accrue", title2)
			ws1.write(4,4, "Date Due", title2)
			ws1.write(4,5, "Original Amount", title2)
			ws1.write(4,6, "Nego Amount", title2)
			# ws1.write(4,6, "Realised", title2)
			ws1.write(4,7, "Balance", title2)
			ws1.write(4,8, "Amount\nUSD", title2)

			results = all_results[0]
			rowcount = 5
			total = {
				1:0.0,
				2:0.0,
				3:0.0,
				4:0.0,
			}
			for key in sorted(results.keys(), key=lambda k:(k[1][:1],k[2])):
				len_val = len(results[key])
				if len_val==0:
					continue
				else:
					subtotal = {
						1:0.0,
						2:0.0,
						3:0.0,
						4:0.0,
					}
					results2 = sorted(results[key],key = lambda x : x['ref'])
					ws1.write(rowcount, 0, str(key[2]))
					ws1.write(rowcount, 1, str(key[1]))
					ws1.write(rowcount,2,results2[0]['ref'])
					ws1.write(rowcount,3,results2[0]['as_on'])
					ws1.write(rowcount,4,results2[0]['due_date'])
					ws1.write(rowcount,5,results2[0]['amount'], body_detail3)
					ws1.write(rowcount,6,results2[0]['nego_amount'], body_detail3)
					ws1.write(rowcount,7,results2[0]['balance'], body_detail3)
					ws1.write(rowcount,8,results2[0]['balance_usd'], body_detail3)
					subtotal[1]+=results2[0]['amount']
					subtotal[2]+=results2[0]['nego_amount']
					subtotal[3]+=results2[0]['balance']
					subtotal[4]+=results2[0]['balance_usd']
					rowcount+=1
					if len_val>1:
						index = 1
						for index in range(1,len_val):
							ws1.write(rowcount,2,results2[index]['ref'])
							ws1.write(rowcount,3,results2[index]['as_on'])
							ws1.write(rowcount,4,results2[index]['due_date'])
							ws1.write(rowcount,5,results2[index]['amount'], body_detail3)
							ws1.write(rowcount,6,results2[index]['nego_amount'], body_detail3)
							ws1.write(rowcount,7,results2[index]['balance'], body_detail3)
							ws1.write(rowcount,8,results2[index]['balance_usd'], body_detail3)
							rowcount+=1
							subtotal[1]+=results2[index]['amount']
							subtotal[2]+=results2[index]['nego_amount']
							subtotal[3]+=results2[index]['balance']
							subtotal[4]+=results2[index]['balance_usd']

					ws1.write_merge(rowcount,rowcount,2,4,'Subtotal '+str(key[2]),body_detail4)
					ws1.write(rowcount,5,subtotal[1], body_detail4)
					ws1.write(rowcount,6,subtotal[2], body_detail4)
					ws1.write(rowcount,7,subtotal[3], body_detail4)
					ws1.write(rowcount,8,subtotal[4], body_detail4)
					rowcount+=1

					total[1]+=subtotal[1]
					total[2]+=subtotal[2]
					total[3]+=subtotal[3]
					total[4]+=subtotal[4]

			ws1.write_merge(rowcount,rowcount,1,4,'Grand Total',body_detail4)
			ws1.write(rowcount,5,total[1], body_detail4)
			ws1.write(rowcount,6,total[2], body_detail4)
			ws1.write(rowcount,7,total[3], body_detail4)
			ws1.write(rowcount,8,total[4], body_detail4)
		else:
			ws.write_merge(0,0,0,11, "PT. Bitratex Industries", title_style)
			ws.write_merge(1,1,0,11, "PAYABLE AGEING STATEMENT DETAIL", title_style)
			ws.write_merge(2,2,0,11, "As On: " + parser.formatLang(data['form']['as_on_date'].decode().encode(), date=True), title_style)

			ws.write_merge(4,6,0,0, "No.", title2)
			ws.write_merge(4,5,1,2, "Supplier", title2)
			ws.write(6,1, "Code", title4)
			ws.write(6,2, "Name", title8)
			ws.write_merge(4,6,3,3, "Move", title2)
			ws.write_merge(4,6,4,4, "Reference", title2)
			ws.write_merge(4,6,5,5, "Date\nEffective", title2)
			ws.write_merge(4,6,6,6, "Date\nDue", title2)
			ws.write_merge(4,6,7,7, "Trans\nCurrency", title2)
			ws.write_merge(4,6,8,8, "AMOUNT TRANS\nBALANCE", title2)
			ws.write_merge(4,6,9,9, "AMOUNT TRANS\nNOT DUE", title2)
			ws.write_merge(4,6,10,10, "AMOUNT TRANS\nOVERDUE", title2)
			ws.write_merge(4,4,11,14, "OVERDUE - DAYS", title2)
			ws.write_merge(4,6,15,15, "AMOUNT\nBALANCE\nUSD", title2)

			period_length = data['form']['period_length'] or 30
			next_period = 0
			for i in range(0,3):
				ws.write_merge(5,6,i+11,i+11, str(next_period+1)+"-"+str(next_period+period_length),title3)
				next_period += period_length
			ws.write_merge(5,6,14,14, ">"+str(next_period),title4)

			results = parser._get_invoice_ap_balance(data)
			n = 0
			rowcount = 8
			total = {
				1:0.0,
				2:0.0,
				3:0.0,
				4:0.0,
			}
			for key in sorted(results.keys(), key=lambda k:(k[1][:1],k[2])):
				len_val = len(results[key])
				if len_val==0:
					continue
				else:
					n+=1
					subtotal = {
						1:0.0,
						2:0.0,
						3:0.0,
						4:0.0,
					}
					lines = sorted(results[key],key = lambda x : x['as_on'])
					ws.write(rowcount, 0, n)
					ws.write(rowcount, 1, str(key[2]))
					ws.write(rowcount, 2, str(key[1]))
					ws.write(rowcount, 3,lines[0]['move'])
					ws.write(rowcount, 4,lines[0]['ref'])
					ws.write(rowcount, 5,parser.formatLang(lines[0]['as_on'],date=True))
					ws.write(rowcount, 6,lines[0]['date_due'] and parser.formatLang(lines[0]['date_due'],date=True) or '')
					ws.write(rowcount, 7,lines[0]['ccy'])
					ws.write(rowcount, 8,lines[0]['balance'], body_detail3)
					ws.write(rowcount, 9,lines[0]['amount_not_due'], body_detail3)
					ws.write(rowcount, 10,lines[0]['amount_overdue'], body_detail3)
					ws.write(rowcount, 11,lines[0]['amt1'], body_detail3)
					ws.write(rowcount, 12,lines[0]['amt2'], body_detail3)
					ws.write(rowcount, 13,lines[0]['amt3'], body_detail3)
					ws.write(rowcount, 14,lines[0]['amt4'], body_detail3)
					ws.write(rowcount, 15,lines[0]['balance_usd'], body_detail3)

					subtotal[1]+=lines[0]['balance']
					subtotal[2]+=lines[0]['amount_not_due']
					subtotal[3]+=lines[0]['amount_overdue']
					subtotal[4]+=lines[0]['balance_usd']
					rowcount+=1
					if len_val>1:
						index = 1
						for index in range(1,len_val):
							ws.write(rowcount, 3, lines[index]['move'])
							ws.write(rowcount, 4, lines[index]['ref'])
							ws.write(rowcount, 5, parser.formatLang(lines[index]['as_on'],date=True))
							ws.write(rowcount, 6, lines[index]['date_due'] and parser.formatLang(lines[index]['date_due'],date=True) or '')
							ws.write(rowcount, 7, lines[index]['ccy'])
							ws.write(rowcount, 8, lines[index]['balance'], body_detail3)
							ws.write(rowcount, 9, lines[index]['amount_not_due'], body_detail3)
							ws.write(rowcount, 10, lines[index]['amount_overdue'], body_detail3)
							ws.write(rowcount, 11, lines[index]['amt1'], body_detail3)
							ws.write(rowcount, 12, lines[index]['amt2'], body_detail3)
							ws.write(rowcount, 13, lines[index]['amt3'], body_detail3)
							ws.write(rowcount, 14, lines[index]['amt4'], body_detail3)      
							ws.write(rowcount, 15, lines[index]['balance_usd'], body_detail3)
							rowcount+=1
							subtotal[1]+=lines[index]['balance']
							subtotal[2]+=lines[index]['amount_not_due']
							subtotal[3]+=lines[index]['amount_overdue']
							subtotal[4]+=lines[index]['balance_usd']

					ws.write_merge(rowcount,rowcount,2,7,'Subtotal '+str(key[2]),body_detail4)
					ws.write(rowcount,8,subtotal[1], body_detail4)
					ws.write(rowcount,9,subtotal[2], body_detail4)
					ws.write(rowcount,10,subtotal[3], body_detail4)
					ws.write_merge(rowcount,rowcount,11,14,'  ')
					ws.write(rowcount,15,subtotal[4], body_detail4)
					rowcount+=1

					total[1]+=subtotal[1]
					total[2]+=subtotal[2]
					total[3]+=subtotal[3]
					total[4]+=subtotal[4]

			ws.write_merge(rowcount,rowcount,0,7,'Grand Total',body_detail4)
			ws.write(rowcount,8,total[1], body_detail4)
			ws.write(rowcount,9,total[2], body_detail4)
			ws.write(rowcount,10,total[3], body_detail4)
			ws.write_merge(rowcount,rowcount,11,14,' ',body_detail4)
			ws.write(rowcount,15,total[4], body_detail4)
		pass
from netsvc import Service
try:
	del Service._services['report.aging.report']
	del Service._services['aging.report']
except:
	pass
aging_report_xls('report.aging.report','aging.report.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=aging_report_parser, header=False)