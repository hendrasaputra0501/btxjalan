
import re
import time
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime as dt
 
class payment_overdue_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(payment_overdue_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_invoice_balance(self, data):
		cr = self.cr
		uid = self.uid

		# initialize pooler obj
		am_obj = self.pool.get('account.move')
		aml_obj = self.pool.get('account.move.line')
		ai_obj = self.pool.get('account.invoice')
		rp_obj = self.pool.get('res.partner')
		ip_obj = self.pool.get('ir.property')

		as_on_date = data['form']['as_on']
		journal_ids = data['form']['journal_ids']
		account_ids = data['form']['account_ids']
		adv_account_ids = data['form']['adv_account_ids']
		
		customer_ids = self.pool.get('res.partner').search(cr, uid, [('customer','=',True)])
		# ar transaction
		aml_ids = aml_obj.search(cr, uid, [('account_id','in',account_ids),('journal_id.type','!=','situation'),('journal_id','in',journal_ids),('state','=','valid'),('partner_id','in',customer_ids),('date','<=',as_on_date)])
		# ar advance transaction
		adv_aml_ids = []
		if adv_account_ids:
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
				curr_partner_ids = [x[0] for x in cr.fetchall()]
				
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
					curr_partner_ids += [x[0] for x in cr.fetchall()]
				
				if curr_partner_ids:
					adv_aml_ids = aml_obj.search(cr, uid, [('account_id','in',adv_account_ids),('state','=','valid'),('partner_id','in',curr_partner_ids),('date','<=',as_on_date)])
			else:
				adv_aml_ids = aml_obj.search(cr, uid, [('account_id','in',adv_account_ids),('state','=','valid'),('date','<=',as_on_date)])

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

		partner_for_diff_goods_type = []

		for aml in aml_obj.browse(cr, uid, aml_ids):
			if aml.partner_id.id in partner_for_diff_goods_type:
				continue
			# invoice
			if aml.invoice and aml.debit and not aml.credit:
				if data['form']['goods_type'] and aml.invoice.goods_type and data['form']['goods_type']!=aml.invoice.goods_type:
					if aml.partner_id.id not in partner_for_diff_goods_type:
						partner_for_diff_goods_type.append(aml.partner_id.id)
						continue
				if aml.invoice not in invoices:
					invoices.update({aml.invoice:[]})
				invoices[aml.invoice].append(aml)	
				# bank negotiation
				if aml.invoice.bank_negotiation_no and aml.invoice.bank_negotiation_no.liability_move_line_id and aml.invoice.bank_negotiation_no.liability_move_line_id.date<=as_on_date:
					aml_negosiation_ids.append(aml.id)
			# invoice refund
			if aml.invoice and aml.credit and not aml.debit:
				if data['form']['goods_type'] and aml.invoice.goods_type and data['form']['goods_type']!=aml.invoice.goods_type:
					if aml.partner_id.id not in partner_for_diff_goods_type:
						partner_for_diff_goods_type.append(aml.partner_id.id)
						continue
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
				if aml.partner_id.id in partner_for_diff_goods_type:
					continue
				# advance
				if not aml.invoice and aml.credit and not aml.debit and aml not in advances:
					advances.append(aml)
				if not aml.invoice and aml.debit and not aml.credit and aml not in debit_notes:
					debit_notes.append(aml)
		# take other moves that is not included in inv or advance
		if oth_aml_ids:
			for aml in aml_obj.browse(cr, uid, oth_aml_ids): 
				if aml.partner_id and aml.partner_id.id in partner_for_diff_goods_type:
					continue
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
		aml_negosiation_reconcile_ids = []
		for k,v in invoices.items()+invoices_refund.items():
			# temp var for ageing detail
			ref = k.internal_number
			as_on, ppn = False, False
			amount, balance, balance2, nego_amount, nego_amount_used = 0.0, 0.0, 0.0, 0.0, 0.0
			# temp var for ageing summary
			amount_not_due, amount_overdue, pending_nego = 0.0, 0.0, 0.0
			arr_overdue_days = [0.0, 0.0, 0.0, 0.0]

			for aml_ar in sorted(v, key=lambda x:x.date_maturity):
				sign = aml_ar.debit and 1 or -1
				balance_aml_ar = 0.0
				aml_reconciled_ids.append(aml_ar.id)
				
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
					balance_aml_ar=0.0
					balance=0.0

			if round(abs(balance),2)<0.01:
				continue

			key = (aml_ar.partner_id.id, aml_ar.partner_id.name, aml_ar.partner_id.partner_code)
			if key not in res_grouped.keys():
				res_grouped.update({key:{
					'amount_total' : 0.0,
					'group_id' : aml_ar.partner_id and aml_ar.partner_id.group_id and aml_ar.partner_id.group_id.id or False,
					'group_name' : aml_ar.partner_id and aml_ar.partner_id.group_id and aml_ar.partner_id.group_id.name or '',
					'partner_id' : aml_ar.partner_id and aml_ar.partner_id.id or False,
					'partner_code' : aml_ar.partner_id and aml_ar.partner_id.partner_code or False,
					'partner_name' : aml_ar.partner_id and aml_ar.partner_id.name or False,
					'amount_overdue' : 0.0,
					'overdue_days' : 0.0,
					'credit_limit' : aml_ar.partner_id and aml_ar.partner_id.group_id and (aml_ar.partner_id.group_id.credit_limit or aml_ar.partner_id.group_id.credit_limit>0) and aml_ar.partner_id.group_id.credit_limit or aml_ar.partner_id.credit_limit, 
					}})
				
			res_grouped[key]['amount_total']+=balance

		# mapping each advance and each credit note into res_grouped
		for adv in sorted(advances+credit_notes, key=lambda x:x.date_maturity):
			# append this id into reconciled ids. This is to evade double checking
			if adv.id not in aml_reconciled_ids:
				aml_reconciled_ids.append(adv.id)
			else:
				continue

			sign = adv.debit and 1 or -1
			amount, balance, balance2 = 0.0, 0.0, 0.0
			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
				balance2 = adv.debit - adv.credit
				amount = adv.amount_currency
				balance = adv.amount_currency
			else:
				amount = adv.debit - adv.credit
				balance = adv.debit - adv.credit
			for payment in (adv.reconcile_id and adv.reconcile_id.line_id or (adv.reconcile_partial_id and adv.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=adv.id and payment.date<=as_on_date:
					aml_reconciled_ids.append(payment.id)
					if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id:
						balance2+=(payment.debit - payment.credit)
						balance+=payment.amount_currency
					else:
						balance+=(payment.debit - payment.credit)

			if adv.currency_id and adv.currency_id.id!=adv.company_id.currency_id.id and balance2==0.0:
				balance=0.0

			
			if round(abs(balance),2)<=0.01:
				continue

			key = (adv.partner_id.id, adv.partner_id.name, adv.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:{
					'amount_total' : 0.0,
					'group_id' : adv.partner_id and adv.partner_id.group_id and adv.partner_id.group_id.id or False,
					'group_name' : adv.partner_id and adv.partner_id.group_id and adv.partner_id.group_id.name or '',
					'partner_id' : adv.partner_id and adv.partner_id.id or False,
					'partner_code' : adv.partner_id and adv.partner_id.partner_code or False,
					'partner_name' : adv.partner_id and adv.partner_id.name or False,
					'amount_overdue' : 0.0,
					'overdue_days' : 0.0,
					'credit_limit' : adv.partner_id and adv.partner_id.group_id and (adv.partner_id.group_id.credit_limit or adv.partner_id.group_id.credit_limit>0) and adv.partner_id.group_id.credit_limit or adv.partner_id.credit_limit,
					}})
			res_grouped[key]['amount_total']+=balance

		# mapping each debit note into res_grouped
		for dn in sorted(debit_notes, key=lambda x:x.date_maturity):
			# append this id into reconciled ids. This is to evade double checking
			if dn.id not in aml_reconciled_ids:
				aml_reconciled_ids.append(dn.id)
			else:
				continue

			sign = dn.debit and 1 or -1
			amount, balance, balance2 = 0.0, 0.0, 0.0
			if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id:
				balance2 = dn.debit - dn.credit
				amount = dn.amount_currency
				balance = dn.amount_currency
			else:
				amount = dn.debit - dn.credit
				balance = dn.debit - dn.credit
			for payment in (dn.reconcile_id and dn.reconcile_id.line_id or (dn.reconcile_partial_id and dn.reconcile_partial_id.line_partial_ids or [])):
				if payment.id!=dn.id and payment.date<=as_on_date:
					aml_reconciled_ids.append(payment.id)
					if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id:
						balance2+=(payment.debit - payment.credit)
						balance+=payment.amount_currency
					else:
						balance+=(payment.debit - payment.credit)

			if dn.currency_id and dn.currency_id.id!=dn.company_id.currency_id.id and balance2==0.0:
				balance = 0.0

			if round(abs(balance),2)<=0.01:
				continue

			key = (dn.partner_id.id, dn.partner_id.name, dn.partner_id.partner_code)
			if key not in res_grouped:
				res_grouped.update({key:{
					'amount_total' : 0.0,
					'group_id' : dn.partner_id and dn.partner_id.group_id and dn.partner_id.group_id.id or False,
					'group_name' : dn.partner_id and dn.partner_id.group_id and dn.partner_id.group_id.name or '',
					'partner_id' : dn.partner_id and dn.partner_id.id or False,
					'partner_code' : dn.partner_id and dn.partner_id.partner_code or False,
					'partner_name' : dn.partner_id and dn.partner_id.name or False,
					'amount_overdue' : 0.0,
					'overdue_days' : 0.0,
					'credit_limit' : dn.partner_id and dn.partner_id.group_id and (dn.partner_id.group_id.credit_limit or dn.partner_id.group_id.credit_limit>0) and dn.partner_id.group_id.credit_limit or dn.partner_id.credit_limit,
					}})
			res_grouped[key]['amount_total']+=balance

		return res_grouped

	def _get_result(self, data):
		res = []
		as_on =data['form']['as_on']
		sale_type =data['form']['sale_type']
		goods_type =data['form']['goods_type']
		query = "\
			SELECT \
				b.id, c.name as name_id, \
				b.bl_date as bl_date, \
				b.bank_negotiation_date as nego_date, \
				coalesce(sp2.estimation_arriv_date::date::text,'') as eta_date, \
				(select string_agg(name,'; ') from stock_picking where invoice_id=b.id) as surat_jalan,\
				b.internal_number as invoice_number, \
				c.group_id, e.name as group_name,\
				c.id as partner_id, \
				c.partner_code as partner_code, \
				c.name as partner_name, \
				b.date_due as due_date, \
				b.date_invoice as do_date, \
				case \
					when (select min(d.id) from account_invoice_tax d where d.invoice_id=b.id) is not NULL \
						then 'PPN' \
					else '' end as ttype, \
				case \
					when e.credit_limit is not NULL or e.credit_limit>0.0 \
						then e.credit_limit \
					else coalesce(c.credit_limit,0.0) end  as credit_limit, \
				case b.sale_type \
					when 'local' then ('%s'::date-b.date_invoice::date) \
					when 'export' then \
						(case when f.due_date_from_bl_date='t' or f.type='sight' \
							then b.date_due::date-(coalesce(b.bl_date,b.date_invoice)::date) \
							when f.due_date_from_bl_date='f' or f.type='usance' \
							then b.date_due::date-b.date_invoice::date \
							else 0 end) \
					end as total_days, \
				('%s'::date-b.date_due::date) as overdue_days, \
				case b.sale_type \
					when 'export' then f.name||' '||(case when f.due_date_from_bl_date='t' or f.type='sight' then 'SIGHT' else 'USANCE' end)\
					else (select \
						cast(x.days as text) ||' Days' \
						from account_payment_term_line x where x.payment_id=f.id limit 1) \
					end as term\
			FROM \
				account_move_line a \
				LEFT JOIN account_invoice b on b.move_id=a.move_id \
				LEFT JOIN res_partner c on c.id=a.partner_id \
				LEFT JOIN res_partner e on c.group_id=e.id \
				LEFT JOIN account_payment_term f on f.id=b.payment_term \
				LEFT JOIN (select invoice_id,max(id) as id from stock_picking group by invoice_id) sp on sp.invoice_id=b.id \
				LEFT JOIN stock_picking sp2 on sp.id = sp2.id \
			WHERE \
				b.id is not NULL \
				and b.type='out_invoice' \
				and a.credit!=0.0 \
				"

		if data['form']['account_ids']:
			query += " and b.account_id in ("+','.join([str(x) for x in data['form']['account_ids']])+") "
		# if data['form']['journal_ids']:
		# 	query += " and b.journal_id in ("+','.join([str(x) for x in data['form']['journal_ids']])+") "
		query += "and (b.payment_date is NULL or b.payment_date>'%s') \
				and b.sale_type = '%s' \
				and b.goods_type = '%s' \
			GROUP BY b.id, c.name, c.id,e.credit_limit,f.id, e.name, c.group_id, sp2.estimation_arriv_date\
			ORDER BY b.internal_number ASC\
			"
		query = query%(as_on,as_on,as_on,sale_type,goods_type)
		
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		inv_ids = [inv['id'] for inv in res]
		temp={}
		for inv_data in self.pool.get('account.invoice').browse(self.cr,self.uid,inv_ids):
			is_ar_tax = False
			total_payment_as_on, total_payment_tax_as_on, total_payment_in_company_curr = 0.0, 0.0, 0.0
			amount_ar, amount_ar_tax, amount_ar_on_company_curr = 0.0, 0.0, 0.0 
			for move_line in inv_data.move_id.line_id:
				if move_line.account_id == inv_data.account_id:
					amount_ar+=inv_data.currency_id.id!=move_line.company_id.currency_id.id and abs(move_line.amount_currency) or move_line.debit
					amount_ar_on_company_curr += move_line.debit
					if move_line.ar_ap_tax:
						is_ar_tax = True
						amount_ar_tax+=inv_data.currency_id.id!=move_line.company_id.currency_id.id and abs(move_line.amount_currency) or move_line.debit
				
					if move_line.reconcile_id and move_line.reconcile_id.line_id:
						for rec in move_line.reconcile_id.line_id:
							# if rec.id!=move_line.id and dt.strptime(rec.date,'%Y-%m-%d')<=dt.strptime(as_on,'%Y-%m-%d'):
							if rec.id!=move_line.id and rec.date<=as_on:
								total_payment_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit
								total_payment_in_company_curr+=rec.credit
								if move_line.ar_ap_tax:
									total_payment_tax_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit

					if move_line.reconcile_id and move_line.reconcile_id.line_partial_ids:
						for rec in move_line.reconcile_id.line_partial_ids:
							# if rec.id!=move_line.id and dt.strptime(rec.date,'%Y-%m-%d')<=dt.strptime(as_on,'%Y-%m-%d'):
							if rec.id!=move_line.id and rec.date<=as_on:
								total_payment_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit
								total_payment_in_company_curr+=rec.credit
								if move_line.ar_ap_tax:
									total_payment_tax_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit

					if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
						for rec in move_line.reconcile_partial_id.line_partial_ids:
							# if rec.id!=move_line.id and dt.strptime(rec.date,'%Y-%m-%d')<=dt.strptime(as_on,'%Y-%m-%d'):
							if rec.id!=move_line.id and rec.date<=as_on:
								total_payment_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit
								total_payment_in_company_curr+=rec.credit
								if move_line.ar_ap_tax:
									total_payment_tax_as_on+=inv_data.currency_id.id!=rec.company_id.currency_id.id and abs(rec.amount_currency) or rec.credit
			# temp.update({inv_data.id:{
			# 	'amount_total':sale_type=='export' and ((amount_ar_on_company_curr-total_payment_in_company_curr)>0 and amount_ar - total_payment_as_on or 0) or 0,
			# 	'amount_overdue':(amount_ar_on_company_curr-total_payment_in_company_curr)>0 and amount_ar - total_payment_as_on or 0,
			# 	'with_tax' : (amount_ar_on_company_curr-total_payment_in_company_curr)>0 and (amount_ar_tax-total_payment_tax_as_on)>0 and (amount_ar_tax-total_payment_tax_as_on)==(amount_ar - total_payment_as_on) and is_ar_tax or False,
			# 	}})
			temp.update({inv_data.id:{
				'amount_total':0.0,
				'amount_overdue':(amount_ar_on_company_curr-total_payment_in_company_curr)>0 and amount_ar - total_payment_as_on or 0,
				'with_tax' : (amount_ar_on_company_curr-total_payment_in_company_curr)>0 and (amount_ar_tax-total_payment_tax_as_on)>0 and (amount_ar_tax-total_payment_tax_as_on)==(amount_ar - total_payment_as_on) and is_ar_tax or False,
				}})
		for x in res:
			if temp.get(x['id'], {}):
				x.update(temp.get(x['id'],{}))

		# additional, to compute the balance of all related
		all_outstanding = self._get_invoice_balance(data)
		for k,v in all_outstanding.items():
			res.append(v)
		return res

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

class payment_overdue_xls(report_xls):
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
		ws = wb.add_sheet('Payment Overdue',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern : pattern solid, fore_color white;')
		title_style_1 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: vert centre, horiz center;' "borders:top dashed, bottom thin")
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed;')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; border:bottom dashed;')
		
		normal_style_round_2			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_round_1			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.0;-#,##0.0')
		normal_style_round_0			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0;-#,##0')
		normal_style_float_round_0 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0;-#,##0')
		normal_style_float_round_1 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.0;-#,##0.0')
		normal_style_float_round_2		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
		subtotal_style_round_0		  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0;-#,##0')
		subtotal_style2_round_2		 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0.00;-#,##0.00')
		subtotal_style2_round_1		 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0.0;-#,##0.0')
		subtotal_style2_round_0		 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top dashed;',num_format_str='#,##0;-#,##0')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: top thin, bottom thin;')
		total_style_round_2			 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		total_style_round_1			 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0.0;(#,##0.0)')
		total_style_round_0			 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; ')

		subtotal_style = subtotal_style_round_0
		subtotal_style2 = subtotal_style2_round_2
		total_style = total_style_round_2
		normal_style_float = normal_style_float_round_2
		normal_style = normal_style_round_2

		sale_type =data['form']['sale_type']
		if sale_type == 'local':
			if data['form']['rounding']==0:
				normal_style_float = normal_style_float_round_0
				normal_style = normal_style_round_0
				total_style = total_style_round_0
				subtotal_style2 = subtotal_style2_round_0
			elif data['form']['rounding']==1:
				normal_style_float = normal_style_float_round_1
				normal_style = normal_style_round_1
				total_style = total_style_round_1
				subtotal_style2 = subtotal_style2_round_1
			else:
				normal_style_float = normal_style_float_round_2
				normal_style = normal_style_round_2
				total_style = total_style_round_2
				subtotal_style2 = subtotal_style2_round_2
			ws.write_merge(0,0,0,10,"PT. BITRATEX INDUSTRIES", title_style)

			# ws.write_merge(1,1,0,10,"PAYMENT OVERDUE "+data['form']['sale_type'].encode("utf-8").upper()+" "+data['form']['account_id'][1].encode("utf-8").upper()+" - GROUP WISE", title_style)
			# ws.write_merge(1,1,0,10,"PAYMENT OVERDUE "+data['form']['account_id'][1].encode("utf-8").upper()+" - GROUP WISE", title_style)
			ws.write_merge(1,1,0,10,"PAYMENT OVERDUE- GROUP WISE", title_style)
			ws.write_merge(2,2,0,10,"AS ON "+dt.strptime(data['form']['as_on'],'%Y-%m-%d').strftime('%d/%m/%Y') , title_style)
			ws.write_merge(4,5,0,0,"NO",th_both_style)
			ws.write_merge(4,5,1,1,"Terms",th_both_style)
			ws.write_merge(4,4,2,4,"Surat Jalan",th_both_style)
			ws.write(5,2,"NO",title_style_1)
			ws.write(5,3,"Date",title_style_1)
			ws.write(5,4,"Due Date",title_style_1)
			ws.write_merge(4,5,5,5,"Type",th_both_style)
			ws.write_merge(4,5,6,6,"Credit Limits",th_both_style)
			ws.write(4,7,"Total O/S",th_top_style)
			ws.write(5,7,"Amount",th_bottom_style)
			ws.write_merge(4,5,8,8,"Overdue",th_both_style)
			ws.write(4,9,"Total",th_top_style)
			ws.write(5,9, "Days",th_bottom_style)
			ws.write(4,10,"Over Due",th_top_style)
			ws.write(5,10,"(Days)",th_bottom_style)

			rowcount=6
			max_width_col_2=0
			max_width_col_0=3

			result=parser._get_result(data)
			result_grouped={}
			for res in result:
				key = res['group_id'] and (res['group_id'],res['group_name']) or ('','General')
				if key not in result_grouped:
					result_grouped.update({key:[]})
				result_grouped[key].append(res)

			for key in result_grouped.keys():
				g = result_grouped[key]
				result_grouped2= {}
				for res in g:
					key2 = (res['partner_id'],res['partner_code'] and res['partner_code']+' '+res['partner_name'] or res['partner_name'], res['partner_name']) 
					if key2 not in result_grouped2:
						result_grouped2.update({key2:[]})
					result_grouped2[key2].append(res)
				result_grouped[key] = result_grouped2

			gtotal,gtotal1=0,0

			for key in result_grouped.keys():
				ws.write_merge(rowcount,rowcount,0,10,key[1],normal_bold_style)
				rowcount+=1
				no=1
				total,total1,=0,0

				for key2 in (result_grouped[key] and sorted(result_grouped[key].keys(), key=lambda x:x[2]) or []):
					ws.write(rowcount,0,no)
					no+=1
					ws.write_merge(rowcount,rowcount,1,10,key2[1],normal_bold_style)
					rowcount+=1
					lines = result_grouped[key][key2]
					subtotal,sub1,sub2,sub3,sub4=0,0,0,0,0
					for line in lines:
						if not line['amount_overdue'] or line['overdue_days']<=0:
							sub1+=line['amount_total']
							continue
						ws.write(rowcount,1,line['term'],normal_style)
						ws.write(rowcount,2,line['invoice_number'],normal_style)
						if len(line['invoice_number'] and line['invoice_number'] or '')>max_width_col_2:
							max_width_col_2 = len(line['invoice_number'])
						ws.write(rowcount,3,dt.strptime(line['do_date'],'%Y-%m-%d').strftime('%d/%m/%Y'),normal_style)
						ws.write(rowcount,4,dt.strptime(line['due_date'],'%Y-%m-%d').strftime('%d/%m/%Y'),normal_style)
						ws.write(rowcount,5,line['with_tax'] and 'PPN' or '',normal_style)
						ws.write(rowcount,6,'',normal_style_float)
						# ws.write(rowcount,7,line['amount_total'],normal_style_float)
						ws.write(rowcount,7,"",normal_style_float)
						ws.write(rowcount,8,line['amount_overdue'],normal_style_float)
						ws.write(rowcount,9,line['total_days'])
						ws.write(rowcount,10,line['overdue_days'])
						
						# subtotal+=line['credit_limit']
						sub1+=line['amount_total']
						sub2+=line['amount_overdue']
						# sub3+=line['total_days']
						# sub4+=line['overdue_days']
						rowcount+=1

					ws.write(rowcount,6,line['credit_limit'],subtotal_style2)
					ws.write(rowcount,7,sub1,subtotal_style2)
					ws.write(rowcount,8,sub2,subtotal_style2)
					ws.write(rowcount,9,'',subtotal_style)
					ws.write(rowcount,10,'',subtotal_style)
					rowcount+=1

					total+=sub1
					total1+=sub2
				ws.write_merge(rowcount,rowcount,0,5,"Group Total :",total_style)
				ws.write(rowcount,6,'',total_style)
				ws.write(rowcount,7,total,total_style)
				ws.write(rowcount,8,total1,total_style)
				ws.write(rowcount,9,'',total_style2)
				ws.write(rowcount,10,'',total_style2)
				rowcount+=1

				gtotal+=total
				gtotal1+=total1
			ws.write_merge(rowcount,rowcount,0,5,"Grand Total :", total_style)
			ws.write(rowcount,6,'',total_style)
			ws.write(rowcount,7,gtotal,total_style)
			ws.write(rowcount,8,gtotal1,total_style)
			ws.write(rowcount,9,'',total_style2)
			ws.write(rowcount,10,'',total_style2)
			rowcount+=1
			ws.col(0).width = 256 * int(max_width_col_0*1.4)
			ws.col(2).width = 256 * int(max_width_col_2*1.4)
		elif sale_type == 'export':
			ws.write_merge(0,0,0,10,"PT. BITRATEX INDUSTRIES", title_style)
			# ws.write_merge(1,1,0,10,"PAYMENT OVERDUE "+data['form']['sale_type'].encode("utf-8").upper()+" "+data['form']['account_id'][1].encode("utf-8").upper()+" - GROUP WISE", title_style)
			# ws.write_merge(1,1,0,10,"PAYMENT OVERDUE "+data['form']['account_id'][1].encode("utf-8").upper()+" - GROUP WISE", title_style)
			ws.write_merge(1,1,0,10,"PAYMENT OVERDUE", title_style)
			ws.write_merge(2,2,0,10,"AS ON "+dt.strptime(data['form']['as_on'],'%Y-%m-%d').strftime('%d/%m/%Y') , title_style)
			
			ws.write(4,0," ",th_both_style)
			ws.write(5,0,"NO",th_both_style)
			
			ws.write_merge(4,4,1,3,"Customer",th_both_style)
			ws.write(5,1,"Credit Terms",th_both_style)
			ws.write(5,2,"Period (days)",th_both_style)
			ws.write(5,3,"Total O/S",th_both_style)

			ws.write_merge(4,4,4,5,"Invoice",th_both_style)
			ws.write(5,4,"No",th_both_style)
			ws.write(5,5,"Date",th_both_style)
			
			ws.write_merge(4,5,6,6,"BL Date",th_both_style)
			ws.write_merge(4,5,7,7,"Negotitation\nDate",th_both_style)
			ws.write_merge(4,5,8,8,"ETA\nDate",th_both_style)
			ws.write_merge(4,5,9,9,"Due\nDate",th_both_style)
			ws.write_merge(4,5,10,10,"Amount",th_both_style)
			
			ws.write_merge(4,5,11,11,"Over Due\n(Days)",th_both_style)
			
			rowcount=6
			max_width_col_2=0
			max_width_col_0=3

			result=parser._get_result(data)
			result_grouped={}
			for res in result:
				key = (res['partner_id'],res['partner_code'] and res['partner_code']+' '+res['partner_name'] or res['partner_name'],res['partner_name'],res['partner_code'])
				if key not in result_grouped:
					result_grouped.update({key:[]})
				result_grouped[key].append(res)
				
			no=1
			total = {
				1:0.0,2:0.0,
			}
			for key in sorted(result_grouped.keys(), key=lambda x : x[3]):
				lines = result_grouped[key]
				if len(lines)==0:
					continue
				total_overdue = sum([x['amount_overdue'] for x in lines if x['overdue_days']>0])
				if total_overdue<=0:
					for line in lines:
						total[1]+=line['amount_total']
					continue
				
				ws.write(rowcount,0,no)
				no+=1
				ws.write_merge(rowcount,rowcount,1,11,key[1],normal_bold_style)
				rowcount+=1
				subtotal = {
					1 : 0.0,2 : 0.0,
				}
				for line in lines:
					if not line['amount_overdue'] or line['overdue_days']<=0:
						subtotal[1]+=line['amount_total']
						continue
					ws.write(rowcount,1,line['term'] and line['term'].upper() or '',normal_style)
					ws.write(rowcount,2,line['total_days'])
					ws.write(rowcount,3,"",normal_style)
					ws.write(rowcount,4,line['invoice_number'],normal_style)
					if len(line['invoice_number'] and line['invoice_number'] or '')>max_width_col_2:
						max_width_col_2 = len(line['invoice_number'])
					ws.write(rowcount,5,dt.strptime(line['do_date'],'%Y-%m-%d').strftime('%d/%m/%Y'),normal_style)
					ws.write(rowcount,6,line['bl_date'] and dt.strptime(line['bl_date'],'%Y-%m-%d').strftime('%d/%m/%Y') or '',normal_style)
					ws.write(rowcount,7,line['nego_date'] and dt.strptime(line['nego_date'],'%Y-%m-%d').strftime('%d/%m/%Y') or '',normal_style)
					ws.write(rowcount,8,line['eta_date'] and dt.strptime(line['eta_date'],'%Y-%m-%d').strftime('%d/%m/%Y') or '',normal_style)
					ws.write(rowcount,9,dt.strptime(line['due_date'],'%Y-%m-%d').strftime('%d/%m/%Y'),normal_style)
					ws.write(rowcount,10,line['amount_overdue'],normal_style_float)
					ws.write(rowcount,11,line['overdue_days'])
					
					# subtotal+=line['credit_limit']
					subtotal[1]+=line['amount_total']
					subtotal[2]+=line['amount_overdue']
					rowcount+=1
				# print str(key[3] or '')+","+str(key[2])+","+str(subtotal[1])+","+str(subtotal[2])
				ws.write(rowcount,3,subtotal[1],subtotal_style2)
				ws.write(rowcount,10,subtotal[2],subtotal_style2)
				rowcount+=1

				total[1]+=subtotal[1]
				total[2]+=subtotal[2]
			ws.write_merge(rowcount,rowcount,0,2,"Total O/S :",total_style)
			ws.write(rowcount,3,total[1],total_style)
			ws.write_merge(rowcount,rowcount,4,8,"",total_style)
			ws.write(rowcount,9,"Total :",total_style)
			ws.write(rowcount,10,total[2],total_style)
			ws.write(rowcount,11,"",total_style)
			rowcount+=1

			ws.col(0).width = 256 * int(max_width_col_0*1.4)
			ws.col(2).width = 256 * int(max_width_col_2*1.4)
		pass

payment_overdue_xls('report.pay.overdue.report','payment.overdue.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=payment_overdue_parser, header=False)