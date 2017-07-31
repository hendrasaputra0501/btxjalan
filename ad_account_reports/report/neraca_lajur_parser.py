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
from account_financial_report_webkit.report.common_balance_reports import CommonBalanceReportHeaderWebkit
from account_financial_report_webkit.report.webkit_parser_header_fix import HeaderFooterTextWebKitParser


class NeracaLajurParser(report_sxw.rml_parse,
						 CommonBalanceReportHeaderWebkit):

	def __init__(self, cursor, uid, name, context):
		super(NeracaLajurParser, self).__init__(cursor, uid, name,
												 context=context)
		self.pool = pooler.get_pool(self.cr.dbname)
		self.cursor = self.cr

		company = self.pool.get('res.users').browse(self.cr, uid, uid,
													context=context).company_id
		header_report_name = ' - '.join((_('NERACA LAJUR'), company.name,
										 company.currency_id.name))

		footer_date_time = self.formatLang(str(datetime.today()),
										   date_time=True)

		self.localcontext.update({
			'cr': cursor,
			'uid': uid,
			'report_name': _('Trial Balance'),
			# 'display_account': self._get_display_account,
			# 'display_account_raw': self._get_display_account_raw,
			# 'filter_form': self._get_filter,
			# 'target_move': self._get_target_move,
			# 'display_target_move': self._get_display_target_move,
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

	def _get_counterpart_details(self, data, account, main_filter, start, stop):
		period_obj = self.pool.get('account.period')
		query = "SELECT \
					aml.account_id, sum(aml.debit) as debit, sum(aml.credit) as credit, sum(aml.debit)-sum(aml.credit) as balance, sum(aml.amount_currency) as amount_currency \
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
				WHERE aml.account_id!=%s \
				GROUP BY aml.account_id"
		filter_period = ""
		if main_filter in ('filter_period', 'filter_no'):
			periods = period_obj.build_ctx_periods(self.cursor, self.uid, start.id, start.id)
			filter_period = " and aml.period_id in ("+','.join([str(x) for x in periods])+") "
		elif main_filter=='filter_date':
			filter_period = " and aml.date between '"+start+"' and '"+stop+"' "
		else:
			raise osv.except_osv(
				_('No valid filter'), _('Please set a valid time filter'))
		query = query%(account.id, filter_period, account.id)
		self.cursor.execute(query)
		results = self.cursor.dictfetchall()
		res = []
		if results:
			for line in results:
				x = line.copy()
				x['account'] = self.pool.get('account.account').browse(self.cursor, self.uid, line['account_id'])
				res.append(x)
		return res



	def get_neraca_lajur_details(self, data, filter_report_type=None):
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

		start_period, stop_period, start, stop = \
			self._get_start_stop_for_filter(main_filter, fiscalyear,
											start_date, stop_date,
											start_period, stop_period)

		init_balance = self.is_initial_balance_enabled(main_filter)
		initial_balance_mode = init_balance and self._get_initial_balance_mode(
			start) or False

		# Retrieving accounts
		ctx = {}
		if data['form'].get('account_level'):
			# Filter by account level
			ctx['account_level'] = int(data['form']['account_level'])
		account_ids = self.get_all_accounts(
			new_ids, only_type=filter_report_type, context=ctx)

		# get details for each account, total of debit / credit / balance
		accounts_by_ids = self._get_account_details(
			account_ids, target_move, fiscalyear, main_filter, start, stop,
			initial_balance_mode)

		objects = self.pool.get('account.account').browse(self.cursor,
														  self.uid,
														  account_ids)

		to_display_accounts = dict.fromkeys(account_ids, True)
		init_balance_accounts = dict.fromkeys(account_ids, False)
		debit_accounts = dict.fromkeys(account_ids, False)
		credit_accounts = dict.fromkeys(account_ids, False)
		balance_accounts = dict.fromkeys(account_ids, False)
		detail_counterpart_accounts = dict.fromkeys(account_ids, False)


		for account in objects:
			# get details of the counterpart accounts of eacg account
			detail_counterpart_accounts[account.id] = self._get_counterpart_details(data, account, main_filter, start, stop)

			debit_accounts[account.id] = \
				accounts_by_ids[account.id]['debit']
			credit_accounts[account.id] = \
				accounts_by_ids[account.id]['credit']
			balance_accounts[account.id] = \
				accounts_by_ids[account.id]['balance']
			init_balance_accounts[account.id] =  \
				accounts_by_ids[account.id].get('init_balance', 0.0)

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
			'init_balance_accounts': init_balance_accounts,
			'debit_accounts': debit_accounts,
			'credit_accounts': credit_accounts,
			'balance_accounts': balance_accounts,
			'detail_counterpart_accounts' : detail_counterpart_accounts,
		}

		return objects, new_ids, context_report_values

	def set_context(self, objects, data, ids, report_type=None):
		"""Populate a ledger_lines attribute on each browse record that will
		   be used by mako template"""
		objects, new_ids, context_report_values = self.\
			get_neraca_lajur_details(data)

		self.localcontext.update(context_report_values)

		return super(NeracaLajurParser, self).set_context(
			objects, data, new_ids, report_type=report_type)


class neraca_lajur_xls(report_xls):
	column_sizes = [12, 12, 30, 17, 17, 17, 17, 17, 17]

	def generate_xls_report(self, _p, _xs, data, objects, wb):
		for account in objects:
			ws = wb.add_sheet(account.code)
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
			c_specs = [
				('report_name', 1, 0, 'text', account.name),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)

			# write empty row to define column sizes
			c_sizes = self.column_sizes
			c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None) for i in range(0, len(c_sizes))]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(ws, row_pos, row_data, set_column_size=True)

			# # Header Table
			# cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
			# cell_style = xlwt.easyxf(cell_format)
			# cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			# c_specs = [
			# 	('fy', 2, 0, 'text', _('Fiscal Year')),
			# 	('af', 2, 0, 'text', _('Accounts Filter')),
			# 	('df', 1, 0, 'text', _p.filter_form(data) ==
			# 	 'filter_date' and _('Dates Filter') or _('Periods Filter')),
			# 	('tm', 2, 0, 'text', _('Target Moves'), None, cell_style_center),
			# 	('ib', 1, 0, 'text', _('Initial Balance'),
			# 	 None, cell_style_center),
			# 	('coa', 1, 0, 'text', _('Chart of Account'),
			# 	 None, cell_style_center),
			# ]
			# row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			# row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)

			# cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
			# cell_style = xlwt.easyxf(cell_format)
			# cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			# c_specs = [
			# 	('fy', 2, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
			# 	('af', 2, 0, 'text', _p.accounts(data) and ', '.join(
			# 		[account.code for account in _p.accounts(data)]) or _('All')),
			# ]
			# df = _('From') + ': '
			# if _p.filter_form(data) == 'filter_date':
			# 	df += _p.start_date if _p.start_date else u''
			# else:
			# 	df += _p.start_period.name if _p.start_period else u''
			# df += ' ' + _('\nTo') + ': '
			# if _p.filter_form(data) == 'filter_date':
			# 	df += _p.stop_date if _p.stop_date else u''
			# else:
			# 	df += _p.stop_period.name if _p.stop_period else u''
			# c_specs += [
			# 	('df', 1, 0, 'text', df),
			# 	('tm', 2, 0, 'text', _p.display_target_move(
			# 		data), None, cell_style_center),
			# 	('ib', 1, 0, 'text', initial_balance_text[
			# 	 _p.initial_balance_mode], None, cell_style_center),
			# 	('coa', 1, 0, 'text', _p.chart_account.name,
			# 	 None, cell_style_center),
			# ]
			# row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			# row_pos = self.xls_write_row(
			# 	ws, row_pos, row_data, row_style=cell_style)

			row_pos += 1

			# Column Header Row
			cell_format = _xs['bold'] + _xs['fill_blue'] + \
				_xs['borders_all'] + _xs['wrap'] + _xs['top']
			cell_style = xlwt.easyxf(cell_format)
			cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
			cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			
			ws.write_merge(row_pos,row_pos+1,0,0, "Code", cell_style_center)
			ws.write_merge(row_pos,row_pos+1,1,1, "Old Code", cell_style_center)
			ws.write_merge(row_pos,row_pos+1,2,2, "Account", cell_style_center)
			ws.write_merge(row_pos,row_pos,3,4, "Bank", cell_style_center)
			ws.write(row_pos+1,3, "Debit", cell_style_center)
			ws.write(row_pos+1,4, "Credit", cell_style_center)
			ws.write_merge(row_pos,row_pos+1,5,5, "CCY\nAmount", cell_style_center)
			ws.write_merge(row_pos,row_pos,6,7, "General Journal", cell_style_center)
			ws.write(row_pos+1,6, "Debit", cell_style_center)
			ws.write(row_pos+1,7, "Credit", cell_style_center)
			ws.write_merge(row_pos,row_pos+1,8,8, "CCY\nAmount", cell_style_center)
			ws.set_horz_split_pos(row_pos)

			row_pos += 2
			# cell styles for account data
			view_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
			view_cell_style = xlwt.easyxf(view_cell_format)
			view_cell_style_center = xlwt.easyxf(view_cell_format + _xs['center'])
			view_cell_style_decimal = xlwt.easyxf(
				view_cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)
			view_cell_style_pct = xlwt.easyxf(
				view_cell_format + _xs['center'], num_format_str='0')
			regular_cell_format = _xs['borders_all']
			regular_cell_style = xlwt.easyxf(regular_cell_format)
			regular_cell_style_center = xlwt.easyxf(
				regular_cell_format + _xs['center'])
			regular_cell_style_decimal = xlwt.easyxf(
				regular_cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)
			regular_cell_style_pct = xlwt.easyxf(
				regular_cell_format + _xs['center'], num_format_str='0')

			total_debit = 0.0
			total_credit = 0.0
			total_ccy = 0.0
			debit_cells = []
			credit_cells = []
			ccy_cells = []
			for counterpart in _p['detail_counterpart_accounts'][account.id]:
				# if current_account.type == 'view':
				# 	cell_style = view_cell_style
				# 	cell_style_center = view_cell_style_center
				# 	cell_style_decimal = view_cell_style_decimal
				# 	cell_style_pct = view_cell_style_pct
				# else:
				# 	cell_style = regular_cell_style
				# 	cell_style_center = regular_cell_style_center
				# 	cell_style_decimal = regular_cell_style_decimal
				# 	cell_style_pct = regular_cell_style_pct
				c_specs = [
					('code', 1, 0, 'text', counterpart['account'].code, None, regular_cell_style),
					('code2', 1, 0, 'text', counterpart['account'].code2, None, regular_cell_style),
					('account', 1, 0, 'text', counterpart['account'].name, None, regular_cell_style),
					('debit1', 1, 0, 'number', counterpart['debit'], None, regular_cell_style_decimal),
					('credit1', 1, 0, 'number', counterpart['credit'], None, regular_cell_style_decimal),
					('ccy1', 1, 0, 'number', counterpart['amount_currency'], None, regular_cell_style_decimal),
					('debit2', 1, 0, 'number', None, None, regular_cell_style_decimal),
					('credit2', 1, 0, 'number', None, None, regular_cell_style_decimal),
					('ccy2', 1, 0, 'number', None, None	, regular_cell_style_decimal),
				]
				row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=regular_cell_style)
				
				debit_cells.append(rowcol_to_cell(row_pos,4))
				credit_cells.append(rowcol_to_cell(row_pos,5))
				ccy_cells.append(rowcol_to_cell(row_pos,6))
				
				total_debit += counterpart['debit']
				total_credit += counterpart['credit']
				total_ccy += counterpart['amount_currency']
			
			c_specs = [
				('code', 1, 0, 'text', 'Total', None, view_cell_style),
				('code2', 1, 0, 'text', '', None, view_cell_style),
				('account', 1, 0, 'text', '', None, view_cell_style),
				('debit1', 1, 0, 'number', total_debit , None, view_cell_style_decimal),
				('credit1', 1, 0, 'number', total_credit, None, view_cell_style_decimal),
				('ccy1', 1, 0, 'number', total_ccy, None, view_cell_style_decimal),
				('debit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('credit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('ccy2', 1, 0, 'number', None, None	, view_cell_style_decimal),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos_total = self.xls_write_row(ws, row_pos, row_data, row_style=view_cell_style)

			c_specs = [
				('code', 1, 0, 'text', 'Initial Balance', None, view_cell_style),
				('code2', 1, 0, 'text', '', None, view_cell_style),
				('account', 1, 0, 'text', '', None, view_cell_style),
				('debit1', 1, 0, 'number', _p['init_balance_accounts'][account.id], None, view_cell_style_decimal),
				('credit1', 1, 0, 'number', None, None, view_cell_style_decimal),
				('ccy1', 1, 0, 'number', None, None, view_cell_style_decimal),
				('debit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('credit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('ccy2', 1, 0, 'number', None, None	, view_cell_style_decimal),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos_init = self.xls_write_row(ws, row_pos_total, row_data, row_style=view_cell_style)

			init_cell = rowcol_to_cell(row_pos_init, 4)
			debit_cell = rowcol_to_cell(row_pos_total, 4)
			credit_cell = rowcol_to_cell(row_pos_total, 5)
			# bal_formula = init_cell + '+' + debit_cell + '-' + credit_cell
			
			c_specs = [
				('code', 1, 0, 'text', 'Closing Balance', None, view_cell_style),
				('code2', 1, 0, 'text', '', None, view_cell_style),
				('account', 1, 0, 'text', '', None, view_cell_style),
				('debit1', 1, 0, 'number', _p['init_balance_accounts'][account.id] + total_debit - total_credit, None, view_cell_style_decimal),
				('credit1', 1, 0, 'number', None, None, view_cell_style_decimal),
				('ccy1', 1, 0, 'number', None, None, view_cell_style_decimal),
				('debit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('credit2', 1, 0, 'number', None, None, view_cell_style_decimal),
				('ccy2', 1, 0, 'number', None, None	, view_cell_style_decimal),
			]
			row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(ws, row_pos_init, row_data, row_style=view_cell_style)

neraca_lajur_xls('report.account.account_neraca_lajur_xls',
				  'account.account',
				  parser=NeracaLajurParser)
