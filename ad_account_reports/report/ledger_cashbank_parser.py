# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from datetime import datetime

from openerp import pooler
from openerp.report import report_sxw
from report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
import xlwt
from openerp.tools.translate import _
from account_financial_report_webkit.report.common_reports import CommonReportHeaderWebkit
from account_financial_report_webkit.report.webkit_parser_header_fix import HeaderFooterTextWebKitParser

_column_sizes = [
	('date', 12),
	('period', 12),
	('move', 20),
	('journal', 12),
	('account_code', 12),
	('partner', 30),
	('label', 45),
	('counterpart', 30),
	('debit', 15),
	('credit', 15),
	('cumul_bal', 15),
	('curr_bal', 15),
	('curr_code', 7),
]

class LedgerCashBankWebkit(report_sxw.rml_parse,
						 CommonReportHeaderWebkit):

	def __init__(self, cursor, uid, name, context):
		super(LedgerCashBankWebkit, self).__init__(cursor, uid, name,
												 context=context)
		self.pool = pooler.get_pool(self.cr.dbname)
		self.cursor = self.cr

		company = self.pool.get('res.users').browse(self.cr, uid, uid,
													context=context).company_id
		header_report_name = ' - '.join((_('Ledger CashBank'), company.name,
										 company.currency_id.name))

		footer_date_time = self.formatLang(str(datetime.today()),
										   date_time=True)

		self.localcontext.update({
			'cr': cursor,
			'uid': uid,
			'report_name': _('Ledger CashBank'),
			'display_account': self._get_display_account,
			'display_account_raw': self._get_display_account_raw,
			'filter_form': self._get_filter,
			'target_move': self._get_target_move,
			'display_target_move': self._get_display_target_move,
			'accounts': self._get_accounts_br,
			'additional_args': [
				('--header-font-name', 'Helvetica'),
				('--footer-font-name', 'Helvetica'),
				('--header-font-size', '10'),
				('--footer-font-size', '6'),
				('--header-left', header_report_name),
				('--header-spacing', '2'),
				('--footer-left', footer_date_time),
				('--footer-right', ' '.join((_('Page'), '[page]', _('of'),
											 '[topage]'))),
				('--footer-line',),
			],
		})

	def _get_counterpart_details(self, account_id, main_filter, start, stop):
		period_obj = self.pool.get('account.period')
		query = "SELECT \
					aml.id \
				FROM \
					(SELECT \
						aml.move_id \
					FROM \
						account_move_line aml \
						inner join account_account aa on aa.id=aml.account_id \
						inner join account_period ap on ap.id=aml.period_id \
					WHERE aa.id=%s and ap.special='f' %s and aml.debit-aml.credit!=0.0 \
					GROUP BY aml.move_id) move \
					inner join account_move_line aml on aml.move_id=move.move_id and aml.debit-aml.credit!=0.0 \
					inner join account_account aa on aa.id=aml.account_id \
				WHERE aml.account_id!=%s "
		filter_period = ""
		if main_filter in ('filter_period', 'filter_no'):
			periods = period_obj.build_ctx_periods(self.cursor, self.uid, start.id, start.id)
			filter_period = " and aml.period_id in ("+','.join([str(x) for x in periods])+") "
		elif main_filter=='filter_date':
			filter_period = " and aml.date between '"+start+"' and '"+stop+"' "
		else:
			raise osv.except_osv(
				_('No valid filter'), _('Please set a valid time filter'))
		query = query%(account_id, filter_period, account_id)
		self.cursor.execute(query)
		results = self.cursor.dictfetchall()
		res = [x['id'] for x in results]
		return res

	def get_move_lines_ids(self, account_id, main_filter, start, stop, target_move, mode='include_opening'):
		"""Get account move lines base on form data"""
		move_line_ids = []
		if mode not in ('include_opening', 'exclude_opening'):
			raise osv.except_osv(
				_('Invalid query mode'),
				_('Must be in include_opening, exclude_opening'))

		if main_filter in ('filter_period', 'filter_no'):
			move_line_ids = self._get_move_ids_from_periods(account_id, start, stop,
												   target_move)

		elif main_filter == 'filter_date':
			move_line_ids = self._get_move_ids_from_dates(account_id, start, stop,
												 target_move, mode='exclude_opening')
		else:
			raise osv.except_osv(
				_('No valid filter'), _('Please set a valid time filter'))

		return move_line_ids + self._get_counterpart_details(account_id, main_filter, start, stop)

	def _compute_account_ledger_lines(self, accounts_id,
									  init_balance_memoizer, main_filter,
									  target_move, start, stop):
		res = {}
		# for acc_id in accounts_ids:
		move_line_ids = self.get_move_lines_ids(
			accounts_id, main_filter, start, stop, target_move)
		if not move_line_ids:
			# res[acc_id] = []
			return []

		lines = self._get_ledger_lines(move_line_ids, accounts_id)
		# res[acc_id] = lines
		return lines

	def _get_move_line_datas(self, move_line_ids,
							 order='per.special DESC, l.account_id ASC, l.date ASC, \
							 per.date_start ASC, m.name ASC'):
		# Possible bang if move_line_ids is too long
		# We can not slice here as we have to do the sort.
		# If slice has to be done it means that we have to reorder in python
		# after all is finished. That quite crapy...
		# We have a defective desing here (mea culpa) that should be fixed
		#
		# TODO improve that by making a better domain or if not possible
		# by using python sort
		if not move_line_ids:
			return []
		if not isinstance(move_line_ids, list):
			move_line_ids = [move_line_ids]
		monster = """
SELECT l.id AS id,
			l.date AS ldate,
			j.code AS jcode ,
			j.type AS jtype,
			l.currency_id,
			l.account_id,
			aa.code2 as code,
			l.amount_currency,
			l.ref AS lref,
			l.name AS lname,
			COALESCE(l.debit, 0.0) - COALESCE(l.credit, 0.0) AS balance,
			l.debit,
			l.credit,
			l.period_id AS lperiod_id,
			per.code as period_code,
			per.special AS peropen,
			l.partner_id AS lpartner_id,
			p.name AS partner_name,
			m.name AS move_name,
			COALESCE(partialrec.name, fullrec.name, '') AS rec_name,
			COALESCE(partialrec.id, fullrec.id, NULL) AS rec_id,
			m.id AS move_id,
			c.name AS currency_code,
			i.id AS invoice_id,
			i.type AS invoice_type,
			i.number AS invoice_number,
			l.date_maturity
FROM account_move_line l
	INNER JOIN account_account aa on aa.id=l.account_id
	JOIN account_move m on (l.move_id=m.id)
	LEFT JOIN res_currency c on (l.currency_id=c.id)
	LEFT JOIN account_move_reconcile partialrec
		on (l.reconcile_partial_id = partialrec.id)
	LEFT JOIN account_move_reconcile fullrec on (l.reconcile_id = fullrec.id)
	LEFT JOIN res_partner p on (l.partner_id=p.id)
	LEFT JOIN account_invoice i on (m.id =i.move_id)
	LEFT JOIN account_period per on (per.id=l.period_id)
	JOIN account_journal j on (l.journal_id=j.id)
	WHERE l.id in %s"""
		monster += (" ORDER BY %s" % (order,))
		try:
			self.cursor.execute(monster, (tuple(move_line_ids),))
			res = self.cursor.dictfetchall()
		except Exception:
			self.cursor.rollback()
			raise
		return res or []

	def _get_ledger_lines(self, move_line_ids, account_id):
		if not move_line_ids:
			return []
		res = self._get_move_line_datas(move_line_ids)
		return res

	# def get_neraca_lajur_details(self, data, filter_report_type=None):
	def set_context(self, objects, data, ids, report_type=None):
		"""Populate a ledger_lines attribute on each browse record that will
		   be used by mako template"""		
		main_filter = self._get_form_param('filter', data, default='filter_no')

		fiscalyear = self.get_fiscalyear_br(data)

		start_period = self.get_start_period_br(data)
		stop_period = self.get_end_period_br(data)

		target_move = self._get_form_param('target_move', data, default='all')
		start_date = self._get_form_param('date_from', data)
		stop_date = self._get_form_param('date_to', data)
		chart_account = self._get_chart_account_id_br(data)
		new_ids = (data['form']['account_ids'] or
				   self.pool.get('account.account').search(self.cursor, self.uid, [('user_type.code','in',['bank','cash'])]))

		# Reading form
		# main_filter = self._get_form_param('filter', data, default='filter_no')
		# target_move = self._get_form_param('target_move', data, default='all')
		# start_date = self._get_form_param('date_from', data)
		# stop_date = self._get_form_param('date_to', data)
		# do_centralize = self._get_form_param('centralize', data)
		# start_period = self.get_start_period_br(data)
		# stop_period = self.get_end_period_br(data)
		# fiscalyear = self.get_fiscalyear_br(data)
		# chart_account = self._get_chart_account_id_br(data)

		if main_filter == 'filter_no':
			start_period = self.get_first_fiscalyear_period(fiscalyear)
			stop_period = self.get_last_fiscalyear_period(fiscalyear)

		# computation of ledger lines
		if main_filter == 'filter_date':
			start = start_date
			stop = stop_date
		else:
			start = start_period
			stop = stop_period

		init_balance = self.is_initial_balance_enabled(main_filter)
		initial_balance_mode = init_balance and self._get_initial_balance_mode(
			start) or False

		# Retrieving accounts
		ctx = {}
		if data['form'].get('account_level'):
			# Filter by account level
			ctx['account_level'] = int(data['form']['account_level'])
		account_ids = self.get_all_accounts(
			new_ids, only_type=None, context=ctx)

		# get details for each account, total of debit / credit / balance
		# accounts_by_ids = self._get_account_details(
		# 	account_ids, target_move, fiscalyear, main_filter, start, stop,
		# 	initial_balance_mode)

		objects = self.pool.get('account.account').browse(self.cursor,
														  self.uid,
														  account_ids)

		to_display_accounts = dict.fromkeys(account_ids, True)
		init_balance_accounts = dict.fromkeys(account_ids, False)
		debit_accounts = dict.fromkeys(account_ids, False)
		credit_accounts = dict.fromkeys(account_ids, False)
		balance_accounts = dict.fromkeys(account_ids, False)
		counterpart_ledger_lines = dict.fromkeys(account_ids, False)


		for account in objects:
			init_balance_memoizer = {}
			
			ledger_lines_memoizer = self._compute_account_ledger_lines(
				account.id, init_balance_memoizer, main_filter, target_move, start,
				stop)
			
			counterpart_ledger_lines[account.id] = ledger_lines_memoizer

		context_report_values = {
			'fiscalyear': fiscalyear,
			'start_date': start_date,
			'stop_date': stop_date,
			'start_period': start_period,
			'stop_period': stop_period,
			'chart_account': chart_account,
			'initial_balance': init_balance,
			'initial_balance_mode': initial_balance_mode,
			'to_display_accounts': to_display_accounts,
			'amount_currency': self._get_amount_currency,
			'ledger_lines' : counterpart_ledger_lines,
		}

		self.localcontext.update(context_report_values)

		return super(LedgerCashBankWebkit, self).set_context(
			objects, data, new_ids, report_type=report_type)
	

class ledger_cashbank_xls(report_xls):
	column_sizes = [x[1] for x in _column_sizes]

	def generate_xls_report(self, _p, _xs, data, objects, wb):

		for account in objects:
			ws = wb.add_sheet(account.code2)
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0  # Landscape
			ws.fit_width_to_pages = 1
			row_pos = 0

			# set print header/footer
			ws.header_str = self.xls_headers['standard']
			ws.footer_str = self.xls_footers['standard']

			# Title
			cell_style = xlwt.easyxf(_xs['xls_title'])
			report_name = ' - '.join([_p.report_name.upper(),
									 _p.company.partner_id.name,
									 _p.company.currency_id.name])
			c_specs = [
				('report_name', 1, 0, 'text', report_name),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, row_style=cell_style)

			# write empty row to define column sizes
			c_sizes = self.column_sizes
			c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
					   for i in range(0, len(c_sizes))]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, set_column_size=True)

			# Header Table
			cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
			cell_style = xlwt.easyxf(cell_format)
			cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			c_specs = [
				('coa', 3, 0, 'text', _('Chart of Account')),
				('fy', 1, 0, 'text', _('Fiscal Year')),
				('df', 3, 0, 'text', _p.filter_form(data) ==
				 'filter_date' and _('Dates Filter') or _('Periods Filter')),
				('af', 1, 0, 'text', _('Accounts Filter')),
				('tm', 2, 0, 'text', _('Target Moves'))

			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, row_style=cell_style_center)

			cell_format = _xs['borders_all']
			cell_style = xlwt.easyxf(cell_format)
			cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			c_specs = [
				('coa', 3, 0, 'text', _p.chart_account.name),
				('fy', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
			]
			df = _('From') + ': '
			if _p.filter_form(data) == 'filter_date':
				df += _p.start_date if _p.start_date else u''
			else:
				df += _p.start_period.name if _p.start_period else u''
			df += ' ' + _('To') + ': '
			if _p.filter_form(data) == 'filter_date':
				df += _p.stop_date if _p.stop_date else u''
			else:
				df += _p.stop_period.name if _p.stop_period else u''
			c_specs += [
				('df', 3, 0, 'text', df),
				('af', 1, 0, 'text', account.code2 ),
				('tm', 2, 0, 'text', _p.display_target_move(data)),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, row_style=cell_style_center)
			ws.set_horz_split_pos(row_pos)
			row_pos += 1

			# Column Title Row
			cell_format = _xs['bold']
			c_title_cell_style = xlwt.easyxf(cell_format)

			# Column Header Row
			cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
			c_hdr_cell_style = xlwt.easyxf(cell_format)
			c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
			c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			c_hdr_cell_style_decimal = xlwt.easyxf(
				cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)

			# Column Initial Balance Row
			cell_format = _xs['italic'] + _xs['borders_all']
			c_init_cell_style = xlwt.easyxf(cell_format)
			c_init_cell_style_decimal = xlwt.easyxf(
				cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)

			c_specs = [
				('date', 1, 0, 'text', _('Date'), None, c_hdr_cell_style),
				('period', 1, 0, 'text', _('Period'), None, c_hdr_cell_style),
				('move', 1, 0, 'text', _('Entry'), None, c_hdr_cell_style),
				('ref', 1, 0, 'text', _('Ref'), None, c_hdr_cell_style),
				('journal', 1, 0, 'text', _('Journal'), None, c_hdr_cell_style),
				('account_code', 1, 0, 'text',
				 _('Account'), None, c_hdr_cell_style),
				('partner', 1, 0, 'text', _('Partner'), None, c_hdr_cell_style),
				('label', 1, 0, 'text', _('Label'), None, c_hdr_cell_style),
				('debit', 1, 0, 'text', _('Debit'), None, c_hdr_cell_style_right),
				('credit', 1, 0, 'text', _('Credit'),
				 None, c_hdr_cell_style_right),
				# ('cumul_bal', 1, 0, 'text', _('Cumul. Bal.'),
				#  None, c_hdr_cell_style_right),
			]
			if _p.amount_currency(data):
				c_specs += [
					('curr_bal', 1, 0, 'text', _('Curr. Bal.'),
					 None, c_hdr_cell_style_right),
					('curr_code', 1, 0, 'text', _('Curr.'),
					 None, c_hdr_cell_style_center),
				]
			c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])

			# cell styles for ledger lines
			ll_cell_format = _xs['borders_all']
			ll_cell_style = xlwt.easyxf(ll_cell_format)
			ll_cell_style_center = xlwt.easyxf(ll_cell_format + _xs['center'])
			ll_cell_style_date = xlwt.easyxf(
				ll_cell_format + _xs['left'],
				num_format_str=report_xls.date_format)
			ll_cell_style_decimal = xlwt.easyxf(
				ll_cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)

			cnt = 0

			display_ledger_lines = _p['ledger_lines'][account.id]

			if _p.display_account_raw(data) == 'all' or \
					display_ledger_lines:
				# TO DO : replace cumul amounts by xls formulas
				cnt += 1
				row_pos = self.xls_write_row(ws, row_pos, c_hdr_data)
				row_start = row_pos

				for line in _p['ledger_lines'][account.id]:
					if line['account_id']!=account.id:
						continue

					label_elements = [line.get('lname') or '']
					if line.get('invoice_number'):
						label_elements.append(
							"(%s)" % (line['invoice_number'],))
					label = ' '.join(label_elements)

					if line.get('ldate'):
						c_specs = [
							('ldate', 1, 0, 'date', datetime.strptime(
								line['ldate'], '%Y-%m-%d'), None,
							 ll_cell_style_date),
						]
					else:
						c_specs = [
							('ldate', 1, 0, 'text', None),
						]
					c_specs += [
						('period', 1, 0, 'text',
						 line.get('period_code') or ''),
						('move', 1, 0, 'text', line.get('move_name') or ''),
						('ref', 1, 0, 'text', line.get('lref') or ''),
						('journal', 1, 0, 'text', line.get('jcode') or ''),
						('account_code', 1, 0, 'text', line.get('code')),
						('partner', 1, 0, 'text',
						 line.get('partner_name') or ''),
						('label', 1, 0, 'text', label),
						('debit', 1, 0, 'number', line.get('debit', 0.0),
						 None, ll_cell_style_decimal),
						('credit', 1, 0, 'number', line.get('credit', 0.0),
						 None, ll_cell_style_decimal),
					]
					if _p.amount_currency(data):
						c_specs += [
							('curr_bal', 1, 0, 'number', line.get(
								'amount_currency') or 0.0, None,
							 ll_cell_style_decimal),
							('curr_code', 1, 0, 'text', line.get(
								'currency_code') or '', None,
							 ll_cell_style_center),
						]
					row_data = self.xls_row_template(
						c_specs, [x[0] for x in c_specs])
					row_pos = self.xls_write_row(
						ws, row_pos, row_data, ll_cell_style)

				for line in _p['ledger_lines'][account.id]:
					if line['account_id']==account.id:
						continue

					label_elements = [line.get('lname') or '']
					if line.get('invoice_number'):
						label_elements.append(
							"(%s)" % (line['invoice_number'],))
					label = ' '.join(label_elements)

					if line.get('ldate'):
						c_specs = [
							('ldate', 1, 0, 'date', datetime.strptime(
								line['ldate'], '%Y-%m-%d'), None,
							 ll_cell_style_date),
						]
					else:
						c_specs = [
							('ldate', 1, 0, 'text', None),
						]
					c_specs += [
						('period', 1, 0, 'text',
						 line.get('period_code') or ''),
						('move', 1, 0, 'text', line.get('move_name') or ''),
						('ref', 1, 0, 'text', line.get('lref') or ''),
						('journal', 1, 0, 'text', line.get('jcode') or ''),
						('account_code', 1, 0, 'text', line.get('code')),
						('partner', 1, 0, 'text',
						 line.get('partner_name') or ''),
						('label', 1, 0, 'text', label),
						('debit', 1, 0, 'number', line.get('debit', 0.0),
						 None, ll_cell_style_decimal),
						('credit', 1, 0, 'number', line.get('credit', 0.0),
						 None, ll_cell_style_decimal),
					]
					if _p.amount_currency(data):
						c_specs += [
							('curr_bal', 1, 0, 'number', line.get(
								'amount_currency') or 0.0, None,
							 ll_cell_style_decimal),
							('curr_code', 1, 0, 'text', line.get(
								'currency_code') or '', None,
							 ll_cell_style_center),
						]
					row_data = self.xls_row_template(
						c_specs, [x[0] for x in c_specs])
					row_pos = self.xls_write_row(
						ws, row_pos, row_data, ll_cell_style)

ledger_cashbank_xls('report.account.account_ledger_cashbank_xls',
				  'account.account',
				  parser=LedgerCashBankWebkit)
