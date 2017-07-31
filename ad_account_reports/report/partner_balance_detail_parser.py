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
from openerp.osv import fields, osv
from openerp.report import report_sxw
from report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
import xlwt
from openerp.tools.translate import _
import cStringIO

class PartnerDetail(report_sxw.rml_parse):

	def __init__(self, cursor, uid, name, context):
		super(PartnerDetail, self).__init__(cursor, uid, name,
												 context=context)
		self.pool = pooler.get_pool(self.cr.dbname)
		self.cursor = self.cr

		company = self.pool.get('res.users').browse(self.cr, uid, uid,
													context=context).company_id
		header_report_name = ' - '.join((_('AR Detail'), company.name,
										 company.currency_id.name))

		footer_date_time = self.formatLang(str(datetime.today()),
										   date_time=True)

		self.localcontext.update({
			'cr': cursor,
			'uid': uid,
			'report_name': _('AR Detail'),
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

	def _get_invoice_ids(self, data, order=" "):
		start_date = data['form']['start_date']
		end_date = data['form']['end_date']
		invoice_type = data['form']['invoice_type']
		query = """
			SELECT
				ai.id
			FROM
				account_invoice ai
			WHERE ai.state not in ('draft','cancel') 
			 %s"""
		where_clause = " and ai.date_invoice between '%s' and '%s' and ai.type='%s' "%\
							(start_date,end_date,invoice_type)
		group_clause = " "
		query = query%(where_clause+order+group_clause)
		
		self.cursor.execute(query)
		res = self.cursor.dictfetchall()
		invoice_ids = [x['id'] for x in res]
		return invoice_ids or []

	def _invoice_datas(self, data, invoice_ids):
		cr = self.cr
		uid = self.uid
		invoice_pool = self.pool.get('account.invoice')
		voucher_pool = self.pool.get('account.voucher')
		alocated_adv_pool = self.pool.get('voucher.split.advance.line')
		curr_obj = self.pool.get('res.currency')
		
		invoices = invoice_pool.browse(cr, uid, invoice_ids)
		res = []
		for invoice in  sorted(invoices, key=lambda x:x.date_invoice):
			# date_invoice = datetime.strptime(invoice.date_invoice,"%Y-%m-%d")
			# tax_date = invoice.tax_date !=False and invoice.tax_date or invoice.date_invoice
			# context_rate = {'date':tax_date or time.strftime('%Y-%m-%d'), 'trans_currency':invoice.currency_id.id}
			# tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',invoice.company_id.currency_id.id),('name','<=',tax_date)])
			
			# kmk_rate = invoice.currency_id.name!='IDR' and tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or False
			# acc_rate = curr_obj._get_conversion_rate(cr, uid, invoice.currency_id, invoice.company_id.currency_id, context={'date':invoice.date_invoice})
			# # dpp_usd = curr_obj.compute(cr,uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, context={'date':invoice.date_invoice})
			# dpp_usd = invoice.currency_id.name=='IDR' and curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, round=True, context={'date':tax_date or time.strftime('%Y-%m-%d'),'reverse':True}) or False
			# dpp_usd2 = curr_obj.compute(cr,uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, context={'date':invoice.date_invoice})
			# dpp_idr = invoice.currency_id.name=='IDR' and invoice.amount_untaxed or curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.tax_base_currency.id, invoice.amount_untaxed, round=True, context=context_rate)
			# tax_idr = invoice.currency_id.name=='IDR' and invoice.amount_tax or curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.tax_base_currency.id, invoice.amount_tax, round=True, context=context_rate)
			# # npwp_cust = invoice.partner_id.npwp and invoice.partner_id.npwp
			# fp_code = invoice.kode_transaksi_faktur_pajak and invoice.kode_transaksi_faktur_pajak[:2] or ''
			dict_result = {
				'period' : invoice.period_id.name,
				'invoice_number' : invoice.internal_number, 
				'date_invoice' : invoice.date_invoice,
				'partner_code' : invoice.partner_id.partner_code,
				'partner_name' : invoice.partner_id.name,
				'due_date' : invoice.date_due,
				'currency_name' : invoice.currency_id.name,
				'realisation' : []
			}
			if invoice.move_id:
				for line in invoice.move_id.line_id:
					if line.account_id.id==invoice.account_id.id:
						dict_result['realisation'].append({
								'type' : 'Accrual',
								'date' : line.date,
								'currency' : line.currency_id.name,
								'amount' : (line.debit-line.credit),
								'amount_currency' : line.amount_currency,
							})
						reconciliation_lines = line.reconcile_id and line.reconcile_id.line_id or (line.reconcile_partial_id and line.reconcile_partial_id.line_partial_ids or [])
						for rec_line in reconciliation_lines:
							if rec_line.id!=line.id:
								recon_type = 'Settlement'
								voucher_ids = voucher_pool.search(cr, uid, [('move_id','=',rec_line.move_id.id)])
								invoice_refund_ids = voucher_pool.search(cr, uid, [('type','!=',invoice.type),('move_id','=',rec_line.move_id.id)])
								if voucher_ids:
									for voucher in voucher_pool.browse(cr, uid, voucher_ids):
										voucher_line = [x for x in voucher.line_cr_ids+voucher.line_dr_ids if x.move_line_id.id==line.id]
										line_amount = voucher_line and curr_obj.compute(cr,uid, voucher.currency_id.id, voucher.company_id.currency_id.id, voucher_line[0].amount, context={'date':voucher.date}) or 0.0

										alocated_advance_ids = alocated_adv_pool.search(cr, uid, [('split_id.voucher_id','=',voucher.id),('invoice_id','=',invoice.id)])
										if alocated_advance_ids:
											recon_type = 'Advance'
											for alo_adv in alocated_adv_pool.browse(cr, uid, alocated_advance_ids):
												amount_alo = curr_obj.compute(cr,uid, voucher.currency_id.id, voucher.company_id.currency_id.id, alo_adv.amount, context={'date':voucher.date})
												rec_dict = {
													'type' : recon_type,
													'date' : rec_line.date,
													'currency' : rec_line.currency_id.name,
													'amount' : -1*amount_alo,
													'amount_currency' : voucher.currency_id.id!=voucher.company_id.currency_id.id and -1*amount_alo or 0.0,
													'adv_number' : alo_adv.advance_id.name,
													'adv_currency' : alo_adv.advance_id.currency_id.name,
													'adv_date' : alo_adv.advance_id.effective_date,
													'adv_amount' : alo_adv.advance_id.total_amount,
													}
												line_amount -= amount_alo
												dict_result['realisation'].append(rec_dict)
											if line_amount:
												recon_type = 'Settlement'
												rec_dict = {
													'type' : recon_type,
													'date' : rec_line.date,
													'currency' : rec_line.currency_id.name,
													'amount' : -1*line_amount,
													'amount_currency' : voucher.currency_id.id!=voucher.company_id.currency_id.id and -1*line_amount or 0.0,
													}
												line_amount -= line_amount
												dict_result['realisation'].append(rec_dict)
										else:
											recon_type = 'Settlement'
											rec_dict = {
												'type' : recon_type,
												'date' : rec_line.date,
												'currency' : rec_line.currency_id.name,
												'amount' : (line.debit-line.credit),
												'amount_currency' : line.amount_currency,
												}
											dict_result['realisation'].append(rec_dict)
								elif invoice_refund_ids:
									recon_type = 'Refund'
									rec_dict = {
										'type' : recon_type,
										'date' : rec_line.date,
										'currency' : rec_line.currency_id.name,
										'amount' : (line.debit-line.credit),
										'amount_currency' : line.amount_currency,
										}
									dict_result['realisation'].append(rec_dict)
			res.append(dict_result)
		return res

	def set_context(self, objects, data, ids, report_type=None):
		"""Populate a ledger_lines attribute on each browse record that will
		   be used by mako template"""		

		invoice_ids = self._get_invoice_ids(data)
		lines_result = self._invoice_datas(data, invoice_ids)
		context_report_values = {
			'start_date': data['form']['start_date'],
			'stop_date': data['form']['end_date'],
			'ar_lines' : lines_result,
		}

		self.localcontext.update(context_report_values)

		return super(PartnerDetail, self).set_context(
			objects, data, invoice_ids, report_type=report_type)

class PartnerDetailXls(report_xls):
	# column_sizes = [x[1] for x in _column_sizes]
	def generate_xls_report(self, _p, _xs, data, objects, wb):

		ws = wb.add_sheet(_p.report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0

		# set print header/footer
		ws.header_str = self.xls_headers['standard']
		ws.footer_str = self.xls_footers['standard']

		# Column Header Row
		cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
		c_hdr_cell_style = xlwt.easyxf(cell_format)
		c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
		c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
		c_hdr_cell_style_decimal = xlwt.easyxf(
			cell_format + _xs['right'],
			num_format_str=report_xls.decimal_format)

		c_specs = [
			('period', 1, 0, 'text', _('Period'), None, c_hdr_cell_style),
			('invoice_number', 1, 0, 'text', _('Invoice No.'), None, c_hdr_cell_style),
			('date_invoice', 1, 0, 'text', _('Date'), None, c_hdr_cell_style),
			('partner_code', 1, 0, 'text', _('Code'), None, c_hdr_cell_style),
			('partner_name', 1, 0, 'text', _('Partner'), None, c_hdr_cell_style),
			('due_date', 1, 0, 'text', _('Due Date'), None, c_hdr_cell_style),
			('currency', 1, 0, 'text', _('Inv Curry'), None, c_hdr_cell_style),
			('type_trans', 1, 0, 'text', _('TypeTrans'), None, c_hdr_cell_style),
			('date_effective', 1, 0, 'text', _('Effective Date'), None, c_hdr_cell_style),
			('currency', 1, 0, 'text', _('Currency'), None, c_hdr_cell_style),
			('amount', 1, 0, 'text', _('Amount'), None, c_hdr_cell_style),
			('amount_currency', 1, 0, 'text', _('Amount Currency'), None, c_hdr_cell_style),
			('adv_number', 1, 0, 'text', _('Advance No.'), None, c_hdr_cell_style),
			('adv_date', 1, 0, 'text', _('Advance Date'), None, c_hdr_cell_style),
			('adv_currency', 1, 0, 'text', _('Advance Currency'), None, c_hdr_cell_style),
			('adv_amount', 1, 0, 'text', _('Advance Amount'), None, c_hdr_cell_style),
		]
		c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(
				ws, row_pos, c_hdr_data, c_hdr_cell_style)
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
		for line in _p.ar_lines:
			# recon_lines = sorted(line['realisation'], key=lambda x:x['date'])
			for rec_line in sorted(line['realisation'], key=lambda x:x['date']):
				c_specs = [
					('period', 1, 0, 'text', line.get('period') or ''),
					('invoice_number', 1, 0, 'text', line.get('invoice_number') or ''),
					('date_invoice', 1, 0, 'text', line.get('date_invoice') or ''),
					('partner_code', 1, 0, 'text', line.get('partner_code') or ''),
					('partner_name', 1, 0, 'text', line.get('partner_name') or ''),
					('due_date', 1, 0, 'text', line.get('due_date') or ''),
					('currency', 1, 0, 'text', line.get('currency_name') or ''),
					('type_trans', 1, 0, 'text', rec_line.get('type') or ''),
					('date_effective', 1, 0, 'text', rec_line.get('date') or ''),
					('currency', 1, 0, 'text', rec_line.get('currency') or ''),
					('amount', 1, 0, 'number', rec_line.get('amount', 0.0), None, ll_cell_style_decimal),
					('amount_currency', 1, 0, 'number', rec_line.get('amount_currency', 0.0), None, ll_cell_style_decimal),
					('adv_number', 1, 0, 'text', rec_line.get('adv_number') or ''),
					('adv_date', 1, 0, 'text', rec_line.get('adv_date') or ''),
					('adv_currency', 1, 0, 'text', rec_line.get('adv_currency') or ''),
					('adv_amount', 1, 0, 'number', rec_line.get('adv_amount', False), None, ll_cell_style_decimal),
				]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)
		
PartnerDetailXls('report.ar.sales.detail', 'account.invoice',
	parser=PartnerDetail)
