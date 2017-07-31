import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class general_ledger_bitratex_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(general_ledger_bitratex_parser, self).__init__(cr, uid, name, context=context)

		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
		})

	def _get_result(self, data):
		res = []
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		period_id=data['form']['period_id']
		journal_ids = data['form']['journal_ids']
		account_ids = data['form']['account_ids']
		query = "SELECT \
					c.id as account_id,\
					c.type as account_type,\
					c.name as account_name,\
					c.code2 as account_code,\
					h.id as analytic_account_id,\
					coalesce(h.name, 'Without Analytic') as analytic_account_name,\
					f.name as period_code,\
					l.date as ldate,\
					g.code as lcode,\
					coalesce(d.partner_alias, d.name) as partner_name,\
					l.ref as lref,\
					b.name as move,\
					l.name as lname,\
					coalesce(l.debit,0.0) as debit,\
					coalesce(l.credit,0.0) as credit,\
					coalesce(l.debit,0.0)-coalesce(l.credit,0.0) as progress,\
					coalesce(l.amount_currency,0.0) as amount_currency,\
					coalesce(e.name,'USD') as currency_code\
				FROM \
					account_move_line l\
					INNER JOIN account_move b ON b.id=l.move_id\
					INNER JOIN account_account c ON c.id=l.account_id\
					LEFT JOIN res_partner d ON d.id=l.partner_id\
					LEFT JOIN res_currency e ON e.id=l.currency_id\
					INNER JOIN account_period f ON f.id=l.period_id\
					INNER JOIN account_journal g ON g.id=l.journal_id\
					LEFT JOIN account_analytic_account h ON h.id=l.analytic_account_id\
				WHERE\
					l.state='valid'"
		query += self._get_query(data)
		query += "ORDER BY l.date ASC"
		self.cr.execute(query)
		res = self.cr.dictfetchall()

		query_init = "SELECT \
					c.id as account_id,\
					c.type as account_type,\
					c.name as account_name,\
					c.code2 as account_code,\
					'' as analytic_account_id,\
					'' as analytic_account_name,\
					'' as period_code,\
					'' as ldate,\
					'' as lcode,\
					'' as partner_name,\
					'*' as lref,\
					'' as move,\
					'Initial Balance' as lname,\
					sum(coalesce(l.debit,0.0)) as debit,\
					sum(coalesce(l.credit,0.0)) as credit,\
					sum(coalesce(l.debit,0.0)-coalesce(l.credit,0.0)) as progress,\
					sum(coalesce(l.amount_currency,0.0)) as amount_currency,\
					'' as currency_code\
				FROM \
					account_account c\
					LEFT JOIN account_move_line l ON l.account_id=c.id AND l.state='valid' "
		query_init += self._get_query(data, context={'initial_bal':True})
		query_init += "LEFT JOIN account_move b ON b.id=l.move_id\
					LEFT JOIN res_partner d ON d.id=l.partner_id\
					LEFT JOIN res_currency e ON e.id=l.currency_id\
					LEFT JOIN account_period f ON f.id=l.period_id\
					LEFT JOIN account_journal g ON g.id=l.journal_id\
					LEFT JOIN account_analytic_account h ON h.id=l.analytic_account_id\
				WHERE c.type<>'view'\
				"
		if data['form']['account_ids']:
			query_init += " AND c.id IN ("+','.join([str(x) for x in data['form']['account_ids']])+") "
		query_init += "GROUP BY c.id,c.type,c.name,c.code2,analytic_account_id,analytic_account_name,period_code,ldate,lcode,partner_name,lref,move,lname,currency_code"
		self.cr.execute(query_init)
		res2 = self.cr.dictfetchall()
		if data['form']['init_balance']:
			return res+res2
		else:
			return res

	def _get_start_date(self, data):
		if data.get('form', False) and data['form'].get('date_from', False):
			return data['form']['date_from']
		return ''

	def _get_end_date(self, data):
		if data.get('form', False) and data['form'].get('date_to', False):
			return data['form']['date_to']
		return ''

	def get_start_period(self, data):
		if data.get('form', False) and data['form'].get('period_id', False):
			return self.pool.get('account.period').browse(self.cr,self.uid,data['form']['period_id'][0]).name
		return ''

	def get_end_period(self, data):
		if data.get('form', False) and data['form'].get('period_to', False):
			return self.pool.get('account.period').browse(self.cr, self.uid, data['form']['period_to']).name
		return ''

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_query(self, data, context=None):
		if context is None:
			context = {}
		from_date=data['form']['from_date']
		to_date=data['form']['to_date']
		fiscalyear_id = data['form']['fiscalyear_id'][0]
		period_id=data['form'].get('period_id',False) and data['form']['period_id'][0] or False
		initial_bal=context.get('initial_bal',False)

		cr = self.cr
		uid = self.uid
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		fiscalperiod_obj = self.pool.get('account.period')
		query = ""
		opening_period_id = fiscalperiod_obj.search(cr, uid, [('fiscalyear_id','=',fiscalyear_id),('special','=',True)])
		opening_period = fiscalperiod_obj.browse(cr, uid, opening_period_id[0])

		if data['form']['account_ids']:
			query += " AND l.account_id IN ("+','.join([str(x) for x in data['form']['account_ids']])+") "
		if data['form']['journal_ids']:
			query += " AND l.journal_id in ("+','.join([str(x) for x in data['form']['journal_ids']])+") "

		if data['form']['partner_ids']:
			query += " AND l.partner_id is NOT NULL AND l.partner_id in ("+','.join([str(x) for x in data['form']['partner_ids']])+") "

		if data['form']['filter'] == 'filter_date':
			if initial_bal:
				if opening_period.date_start == from_date:
					query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +" and special='t') "
				elif opening_period.date_start < from_date:
					query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +") AND l.date >= '"+opening_period.date_start+"' AND l.date < '"+from_date+"' "
				else:
					query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +") AND l.date < '"+from_date+"' "
			else:
				query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +" and special='f') AND l.date between '"+from_date+"' and '"+to_date+"'"
		elif data['form']['filter'] == 'filter_period':
			# print ">>>>>>>>>>>>>>>>",
			period_id = fiscalperiod_obj.browse(cr, uid, period_id)
			if initial_bal:
				if opening_period.id == period_id.id:
					first_period = fiscalperiod_obj.search(cr, uid, [('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
					period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, first_period, period_id.id)
					query += " AND l.period_id not in (select id from account_period where fiscalyear_id="+str(fiscalyear_id)+" and id in ("+','.join([str(x) for x in (period_ids or [])])+")) "
				elif opening_period.date_start == period_id.date_start:
					query += " AND l.period_id=(select id from account_period where fiscalyear_id="+str(fiscalyear_id)+" and id="+str(opening_period.id)+" limit 1) "
				else:
					period_company_id = fiscalperiod_obj.browse(cr, uid, period_id, context=context).company_id.id
					period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, opening_period.id, period_id.id)
					query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +" and id IN ("+','.join([str(x) for x in (period_ids or [])])+")) "
			else:
				period_ids = fiscalperiod_obj.build_ctx_periods(cr, uid, period_id.id, period_id.id)
				query += " AND l.period_id in (select id from account_period where fiscalyear_id="+ str(fiscalyear_id) +" and id IN ("+','.join([str(x) for x in period_ids or []])+")) "

		return query

	def _sum_debit_account(self, account, data):
		if account[1] == 'view':
			return 0.0
		q = "\
				SELECT sum(debit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		q = q%(account[0])
		self.cr.execute(q)
		sum_debit = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(debit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_debit += self.cr.fetchone()[0] or 0.0
		return sum_debit

	def _sum_debit_analytic_account(self, account, data):
		if account[1] == 'view':
			return 0.0
		q = "\
				SELECT sum(debit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		if account[2]:
			q += " AND l.analytic_account_id = %s"
			q = q%(account[0],account[2])
		else:
			q += " AND l.analytic_account_id is NULL"
			q = q%(account[0])
		self.cr.execute(q)
		sum_debit = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(debit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			if account[2]:
				q2 += " AND l.analytic_account_id = %s"
				q2 = q2%(account[0],account[2])
			else:
				q2 += " AND l.analytic_account_id is NULL"
				q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_debit += self.cr.fetchone()[0] or 0.0
		return sum_debit

	def _sum_credit_account(self, account, data):
		if account[1] == 'view':
			return 0.0
		
		q = "\
				SELECT sum(credit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		q = q%(account[0])
		self.cr.execute(q)
		sum_credit = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(credit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_credit += self.cr.fetchone()[0] or 0.0
		return sum_credit

	def _sum_credit_analytic_account(self, account, data):
		if account[1] == 'view':
			return 0.0
		
		q = "\
				SELECT sum(credit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		if account[2]:
			q += " AND l.analytic_account_id = %s"
			q = q%(account[0],account[2])
		else:
			q += " AND l.analytic_account_id is NULL"
			q = q%(account[0])
		self.cr.execute(q)
		sum_credit = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(credit) \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			if account[2]:
				q2 += " AND l.analytic_account_id = %s"
				q2 = q2%(account[0],account[2])
			else:
				q2 += " AND l.analytic_account_id is NULL"
				q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_credit += self.cr.fetchone()[0] or 0.0
		return sum_credit

	def _sum_balance_account(self, account, data):
		if account[1] == 'view':
			return 0.0

		q = "\
				SELECT (sum(debit) - sum(credit)) as tot_balance \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		q = q%(account[0])
		self.cr.execute(q)
		sum_balance = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT (sum(debit) - sum(credit)) as tot_balance \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_balance += self.cr.fetchone()[0] or 0.0
		return sum_balance

	def _sum_balance_analytic_account(self, account, data):
		if account[1] == 'view':
			return 0.0

		q = "\
				SELECT (sum(debit) - sum(credit)) as tot_balance \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		if account[2]:
			q += " AND l.analytic_account_id = %s"
			q = q%(account[0],account[2])
		else:
			q += " AND l.analytic_account_id is NULL"
			q = q%(account[0])
		self.cr.execute(q)
		sum_balance = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT (sum(debit) - sum(credit)) as tot_balance \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			if account[2]:
				q2 += " AND l.analytic_account_id = %s"
				q2 = q2%(account[0],account[2])
			else:
				q2 += " AND l.analytic_account_id is NULL"
				q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_balance += self.cr.fetchone()[0] or 0.0
		return sum_balance

	def _sum_amount_currency_account(self, account, data):
		if account[1] == 'view':
			return 0.0

		q = "\
				SELECT sum(coalesce(amount_currency,0)) as tot_amt_curr \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		q = q%(account[0])
		self.cr.execute(q)
		sum_amount_currency = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(coalesce(amount_currency,0)) as tot_amt_curr \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_amount_currency += self.cr.fetchone()[0] or 0.0
		return sum_amount_currency

	def _sum_amount_currency_analytic_account(self, account, data):
		if account[1] == 'view':
			return 0.0

		q = "\
				SELECT sum(coalesce(amount_currency,0)) as tot_amt_curr \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE (l.account_id = %s) \
				AND l.state='valid' "
		q += self._get_query(data)
		if account[2]:
			q += " AND l.analytic_account_id = %s"
			q = q%(account[0],account[2])
		else:
			q += " AND l.analytic_account_id is NULL"
			q = q%(account[0])
		self.cr.execute(q)
		sum_amount_currency = self.cr.fetchone()[0] or 0.0
		if data['form']['init_balance']:
			q2 = "SELECT sum(coalesce(amount_currency,0)) as tot_amt_curr \
				FROM account_move_line l \
				JOIN account_move am ON (am.id = l.move_id) \
				WHERE l.account_id = %s \
				AND l.state='valid' "
			ctx={'initial_bal':True}
			q2 += self._get_query(data,context=ctx)
			if account[2]:
				q2 += " AND l.analytic_account_id = %s"
				q2 = q2%(account[0],account[2])
			else:
				q2 += " AND l.analytic_account_id is NULL"
				q2 = q2%(account[0])
			self.cr.execute(q2)
			# Add initial balance to the result
			sum_amount_currency += self.cr.fetchone()[0] or 0.0
		return sum_amount_currency

class general_ledger_bitratex_xls(report_xls):
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

	def _display_filter(self, parser, data):
		filter_string = ""
		if data['form']['filter'] == 'filter_date':
			filter_string = '%s -> %s' % (parser.formatLang(parser._get_start_date(data), date=True),
										  parser.formatLang(parser._get_end_date(data), date=True))
		elif data['form']['filter'] == 'filter_period':
			filter_string = '%s' % (parser.get_start_period(data))

		return 'Filter By: %s' % (filter_string)

	def _display_fiscalyear(self, parser, data):
		k = parser._get_fiscalyear(data)
		if k:
			k = 'Fiscal Year: %s' % (k)
		return k
 
	def generate_xls_report(self, parser, data, obj, wb):
		c = parser.localcontext['company']
		ws = wb.add_sheet(('General Ledger')[:31])
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1
		judul = "GENERAL LEDGER"

		cols_specs = [
			# Headers data
			('Title', 15, 0, 'text',
				lambda x, d, p: judul),
			('Kosong', 15, 0, 'text',
				lambda x, d, p: ""),
			('Fiscal Year', 13, 0, 'text',
				lambda x, d, p: ""),
			('Create Date', 2, 0, 'text',
				lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
			('Filter', 15, 0, 'text',
				lambda x, d, p: self._display_filter(p, d)),

			# Line
			('Date', 1, 65, 'text',
				lambda x, d, p: p.formatLang(x['ldate'],date=True)),
			('Period', 1, 65, 'text',
				lambda x, d, p: x['period_code']),
			('JNRL', 1, 28, 'text',
				lambda x, d, p: x['lcode']),
			('Partner Name', 4, 0, 'text',
				lambda x, d, p: x['partner_name']),
			('Ref.', 1, 60, 'text',
				lambda x, d, p: x['lref']),
			('Move', 1, 60, 'text',
				lambda x, d, p: x['move']),
			('Entry Label', 1, 175, 'text',
				lambda x, d, p: x['lname']),
			('Debit', 1, 90, 'number',
				lambda x, d, p: x['debit']),
			('Credit', 1, 90, 'number',
				lambda x, d, p: x['credit']),
			('Balance', 1, 90, 'number',
				lambda x, d, p: x['progress']),
			('Amount Currency', 1, 90, 'number',
				lambda x, d, p: x['amount_currency']),
			('Currency', 1, 90, 'text',
				lambda x, d, p: x['currency_code']),
					  
		   # Account Total
			('Account Code', 1, 0, 'text',
				lambda x, d, p: x[2]),
			('Account Name', 9, 0, 'text',
				lambda x, d, p: "Total Account : "+str(x[3])),
			('Account Title Name', 14, 0, 'text',
				lambda x, d, p: x[3]),
			('Account Debit', 1, 0, 'number',
				lambda x, d, p: p._sum_debit_account(x, d)),
			('Account Credit', 1, 0, 'number',
				lambda x, d, p: p._sum_credit_account(x, d)),
			('Account Balance', 1, 0, 'number',
				lambda x, d, p: p._sum_balance_account(x, d)),
			('Account Amount Currency', 1, 0, 'number',
				lambda x, d, p: p._sum_amount_currency_account(x, d)),

			# Analytic Account Total
			('Analytic Account Code', 1, 0, 'text',
				lambda x, d, p: ""),
			('Analytic Account Name', 9, 0, 'text',
				lambda x, d, p: "Total Analytic Account : "+str(x[3])),
			('Analytic Account Title Name', 14, 0, 'text',
				lambda x, d, p: x[3]),
			('Analytic Account Debit', 1, 0, 'number',
				lambda x, d, p: p._sum_debit_analytic_account(x, d)),
			('Analytic Account Credit', 1, 0, 'number',
				lambda x, d, p: p._sum_credit_analytic_account(x, d)),
			('Analytic Account Balance', 1, 0, 'number',
				lambda x, d, p: p._sum_balance_analytic_account(x, d)),
			('Analytic Account Amount Currency', 1, 0, 'number',
				lambda x, d, p: p._sum_amount_currency_analytic_account(x, d)),
		]
		
		row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
		row_hdr1 = self.xls_row_template(cols_specs, ['Kosong'])
		row_hdr2 = self.xls_row_template(cols_specs, ['Fiscal Year', 'Create Date'])
		row_hdr3 = self.xls_row_template(cols_specs, ['Filter'])
		row_hdr4 = self.xls_row_template(cols_specs, ['Kosong'])
		row_hdr5 = self.xls_row_template(cols_specs, ['Kosong'])
		hdr_line = ['Date', 'Period', 'JNRL', 'Partner Name', 'Ref.', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Amount Currency', 'Currency']
		hdr_account = ['Account Code', 'Account Title Name']
		hdr_account_total = ['Account Code', 'Account Name', 'Account Debit', 'Account Credit', 'Account Balance','Account Amount Currency']

		row_line = self.xls_row_template(cols_specs, hdr_line)
		row_account_hdr = self.xls_row_template(cols_specs, hdr_account)
		row_account_total = self.xls_row_template(cols_specs, hdr_account_total)

		if data['form']['show_analytic_account']:
			hdr_analytic_account = ['Analytic Account Code', 'Analytic Account Title Name']
			hdr_analytic_account_total = ['Analytic Account Code', 'Analytic Account Name', 'Analytic Account Debit', 'Analytic Account Credit', 'Analytic Account Balance','Analytic Account Amount Currency']
			row_analytic_account_hdr = self.xls_row_template(cols_specs, hdr_analytic_account)
			row_analytic_account_total = self.xls_row_template(cols_specs, hdr_analytic_account_total)

		# Style
		tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		row_hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
		row_account_style = xlwt.easyxf('font: bold on;borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		row_account_total_style = xlwt.easyxf('font: italic on, bold on;borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		row_analytic_account_style = xlwt.easyxf('font: italic on;borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		row_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		
		hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
		row_normal_style=  xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
		row_bold_style = xlwt.easyxf('font: bold on;',num_format_str='#,##0.00;(#,##0.00)')
		
		tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		subtittle_left_style = xlwt.easyxf('font: height 180, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		subtittle_right_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		subtittle_top_and_bottom_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		blank_style = xlwt.easyxf('font: height 650, name Arial, colour_index brown, bold off; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		normal_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off; align: wrap on, vert centre, horiz left;')
		total_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre;', num_format_str='#,##0.00;(#,##0.00)')
		
		self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style)
		self.xls_write_row(ws, None, data, parser, 1, row_hdr1, blank_style)
		self.xls_write_row(ws, None, data, parser, 2, row_hdr2, subtittle_left_style)
		self.xls_write_row(ws, None, data, parser, 3, row_hdr3, hdr_style)
		self.xls_write_row(ws, None, data, parser, 4, row_hdr4, blank_style)
		self.xls_write_row_header(ws, 5, row_account_total, row_hdr_style)
		self.xls_write_row_header(ws, 6, row_line, row_hdr_style, set_column_size=True)

		row_count = 7
		ws.horz_split_pos = row_count

		results = parser._get_result(data)
		result_grouped = {}
		for res in results:
			key = (res['account_id'], res['account_type'], res['account_code'], res['account_name'])
			key2= (res['account_id'], res['account_type'], res['analytic_account_id'] and res['analytic_account_id'] or False,res['analytic_account_name'])
			if key not in result_grouped.keys():
				if data['form']['show_analytic_account']:
					result_grouped.update({key:{}})
					if key2 not in result_grouped[key].keys():
						result_grouped[key].update({key2:[]})
				else:
					result_grouped.update({key:[]})
			elif data['form']['show_analytic_account'] and key2 not in result_grouped[key].keys():
				result_grouped[key].update({key2:[]})
			if data['form']['show_analytic_account']:
				result_grouped[key][key2].append(res)
			else:
				result_grouped[key].append(res)


		for o in result_grouped.keys():
			r = ws.row(row_count)
			self.xls_write_row(ws, o, data, parser,
						row_count, row_account_hdr, row_account_style)
			row_count += 1

			if data['form']['show_analytic_account']:
				for analytic in result_grouped[o].keys():
					self.xls_write_row(ws, analytic, data, parser,
						row_count, row_analytic_account_hdr, row_analytic_account_style)
					row_count += 1

					liness = sorted(result_grouped[o][analytic],key=lambda x:x['ldate'])
					for l in liness:
						self.xls_write_row(ws, l, data, parser,
										row_count, row_line, row_style)
						row_count += 1

					self.xls_write_row(ws, analytic, data, parser,
									row_count, row_analytic_account_total, row_analytic_account_style)
					row_count += 1
			else:
				liness = sorted(result_grouped[o],key=lambda x:x['ldate'])
				for l in liness:
					self.xls_write_row(ws, l, data, parser,
									row_count, row_line, row_style)
					row_count += 1

			self.xls_write_row(ws, o, data, parser,
							row_count, row_account_total, row_account_total_style)
			row_count += 1
		pass
general_ledger_bitratex_xls('report.general.ledger.bitratex.xls','general.ledger.wizard','addons/ad_account_reports/report/payment_overdue.mako', parser=general_ledger_bitratex_parser, header=False)