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

class RawSalesReportWebkit(report_sxw.rml_parse):

	def __init__(self, cursor, uid, name, context):
		super(RawSalesReportWebkit, self).__init__(cursor, uid, name,
												 context=context)
		self.pool = pooler.get_pool(self.cr.dbname)
		self.cursor = self.cr

		company = self.pool.get('res.users').browse(self.cr, uid, uid,
													context=context).company_id
		header_report_name = ' - '.join((_('Sales Report'), company.name,
										 company.currency_id.name))

		footer_date_time = self.formatLang(str(datetime.today()),
										   date_time=True)

		self.localcontext.update({
			'cr': cursor,
			'uid': uid,
			'report_name': _('Sales Report'),
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

	def _get_stock_move_ids(self, data, order=" "):
		goods_type = data['form']['goods_type']
		start_date = data['form']['date_from']
		end_date = data['form']['date_to']
		sale_type = data['form']['sale_type']
		usage = data['form']['usage']=='customer' and 'out' or 'in'
		query = """
			SELECT
				sm.id
			FROM
				stock_move sm
				INNER JOIN stock_picking sp ON sp.id=sm.picking_id
				INNER JOIN account_invoice_line ail ON ail.id=sm.invoice_line_id
				INNER JOIN account_invoice ai ON ai.id=ail.invoice_id and ai.id=sp.invoice_id
				INNER JOIN sale_order_line sol ON sol.id=sm.sale_line_id
				INNER JOIN sale_order so ON so.id=sol.order_id
			WHERE sm.state='done' and sp.state='done' 
			 %s"""
		where_clause = " and so.goods_type='%s' and ai.date_invoice between '%s' and '%s' and sp.type='%s' and so.sale_type='%s' "%\
							(goods_type,start_date,end_date,usage,sale_type)
		query = query%(where_clause)
		# try:
		self.cursor.execute(query)
		res = self.cursor.dictfetchall()
		move_ids = [x['id'] for x in res]
		# except Exception:
			# self.cursor.rollback()
			# raise osv.except_osv(_('No Id Found'), _('Please repeat your work'))
		return move_ids or []

	def _sale_datas(self, stock_move_ids):
		cr = self.cr
		uid = self.uid
		move_lines = self.pool.get('stock.move').browse(cr, uid, stock_move_ids)

		sale_line_grouped = {}
		for line in  sorted(move_lines, key=lambda x:x.date):
			key = (line.sale_line_id.id, line.invoice_line_id.id)
			sale_obj = line.sale_line_id.order_id
			invoice_obj = line.invoice_line_id.invoice_id
			
			date_invoice = datetime.strptime(invoice_obj.date_invoice,"%Y-%m-%d")
			tax_date = invoice_obj.tax_date !=False and invoice_obj.tax_date or invoice_obj.date_invoice
			tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',invoice_obj.currency_id.id),('name','<=',tax_date)])
			if key not in sale_line_grouped:
				sale_line_grouped.update({key:{
					'inv_year' : date_invoice.strftime('%Y'),
					'goods_type' : sale_obj.goods_type,
					'production_unit' : line.location_id.alias[:3],
					'inv_period' : date_invoice.strftime('%m/%Y'),
					'sale_type' : sale_obj.sale_type,
					'picking_no' : line.picking_id.name,
					'invoice_no' : invoice_obj.internal_number,
					'peb_number' : invoice_obj.peb_number,
					# 'peb_date' : invoice_obj.peb_date!=False and datetime.strptime(invoice_obj.peb_date,"%Y-%m-%d") or False,
					'peb_date' : invoice_obj.peb_date,
					'customer_name' : invoice_obj.partner_id.name,
					'currency_name' : invoice_obj.currency_id.name,
					'price_subtotal' : 0.0,
					'kmk_rate' : tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 1,
					'price_subtotal_idr' :0.0,
					'count_number' : "%s%s"%(str(line.product_id.count or ''),str(line.product_id.sd_type or '')),
					'blend_code' : line.product_id.blend_code.name,
					'product_name' : line.product_id.name,
					'product_qty' : 0.0,
					'uom' : line.product_id.uom_id.name,
					'lc_number' : line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.name or '',
					'dest_port' : line.lc_product_line_id and line.lc_product_line_id.lc_dest and line.lc_product_line_id.lc_dest.name or '',
					'bl_number' : invoice_obj.bl_number,
					# 'bl_date' : invoice_obj.bl_date!=False and datetime.strptime(invoice_obj.bl_date,"%Y-%m-%d") or False,
					'bl_date' : invoice_obj.bl_date,
					'shipping_line': line.picking_id.shipping_lines and line.picking_id.shipping_lines.name or '',
					'container_number' : line.picking_id.container_number,
					'nego_bank' : invoice_obj.bank_negotiation_no and invoice_obj.bank_negotiation_no.journal_id.name or '',
					'nego_date' : invoice_obj.bank_negotiation_date,
					'real_bank' : invoice_obj.bank_negotiation_no and invoice_obj.bank_negotiation_no.journal_id.name or '',
					'real_date' : invoice_obj.bank_negotiation_date,
					}})
			context_rate = {'date':tax_date or time.strftime('%Y-%m-%d'), 'trans_currency':invoice_obj.currency_id.id}
			sale_line_grouped[key]['price_subtotal']+=line.invoice_line_id.price_subtotal
			sale_line_grouped[key]['price_subtotal_idr']+=self.pool.get('res.currency').computerate(cr, uid, invoice_obj.currency_id.id, invoice_obj.company_id.tax_base_currency.id, line.invoice_line_id.price_subtotal, round=True, context=context_rate)
			sale_line_grouped[key]['product_qty']+=self.pool.get('product.uom')._compute_qty(cr, uid, line.product_uom.id, line.product_qty, to_uom_id=line.product_id.uom_id.id)
		res = [x for x in sale_line_grouped.values()]
		return res

	def _get_invoice_ids(self, data, order=" "):
		goods_type = data['form']['goods_type']
		start_date = data['form']['date_from']
		end_date = data['form']['date_to']
		sale_type = data['form']['sale_type']
		usage = data['form']['usage']=='customer' and 'out' or 'in'
		query = """
			SELECT
				ai.id
			FROM
				account_invoice ai
				INNER JOIN stock_picking sp ON sp.invoice_id=ai.id
				INNER JOIN sale_order so ON so.id=sp.sale_id
			WHERE sp.state='done' 
			 %s"""
		where_clause = " and so.goods_type='%s' and ai.date_invoice between '%s' and '%s' and sp.type='%s' and so.sale_type='%s' "%\
							(goods_type,start_date,end_date,usage,sale_type)
		group_clause = " GROUP BY ai.id "
		query = query%(where_clause+order+group_clause)
		# try:
		self.cursor.execute(query)
		res = self.cursor.dictfetchall()
		move_ids = [x['id'] for x in res]
		# except Exception:
			# self.cursor.rollback()
			# raise osv.except_osv(_('No Id Found'), _('Please repeat your work'))
		return move_ids or []

	def _invoice_datas(self, invoice_ids):
		cr = self.cr
		uid = self.uid
		invoices = self.pool.get('account.invoice').browse(cr, uid, invoice_ids)
		res = []
		# sale_line_grouped = {}
		for invoice in  sorted(invoices, key=lambda x:x.date_invoice):
			# key = (line.sale_line_id.id, line.invoice_line_id.id)
			# sale_obj = line.sale_line_id.order_id
			# invoice_obj = line.invoice_line_id.invoice_id
			curr_obj = self.pool.get('res.currency')
			
			date_invoice = datetime.strptime(invoice.date_invoice,"%Y-%m-%d")
			tax_date = invoice.tax_date !=False and invoice.tax_date or invoice.date_invoice
			context_rate = {'date':tax_date or time.strftime('%Y-%m-%d'), 'trans_currency':invoice.currency_id.id}
			tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',invoice.company_id.currency_id.id),('name','<=',tax_date)])
			
			kmk_rate = invoice.currency_id.name!='IDR' and tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or False
			acc_rate = curr_obj._get_conversion_rate(cr, uid, invoice.currency_id, invoice.company_id.currency_id, context={'date':invoice.date_invoice})
			# dpp_usd = curr_obj.compute(cr,uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, context={'date':invoice.date_invoice})
			dpp_usd = invoice.currency_id.name=='IDR' and curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, round=True, context={'date':tax_date or time.strftime('%Y-%m-%d'),'reverse':True}) or False
			dpp_usd2 = curr_obj.compute(cr,uid, invoice.currency_id.id, invoice.company_id.currency_id.id, invoice.amount_untaxed, context={'date':invoice.date_invoice})
			dpp_idr = invoice.currency_id.name=='IDR' and invoice.amount_untaxed or curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.tax_base_currency.id, invoice.amount_untaxed, round=True, context=context_rate)
			tax_idr = invoice.currency_id.name=='IDR' and invoice.amount_tax or curr_obj.computerate(cr, uid, invoice.currency_id.id, invoice.company_id.tax_base_currency.id, invoice.amount_tax, round=True, context=context_rate)
			# npwp_cust = invoice.partner_id.npwp and invoice.partner_id.npwp
			fp_code = invoice.kode_transaksi_faktur_pajak and invoice.kode_transaksi_faktur_pajak[:2] or ''
			res.append({
				'inv_month' : date_invoice.strftime('%m'),
				'fp_code' : fp_code,
				'cust_npwp_type' : '',
				'customer_name' : invoice.partner_id.name,
				'cust_npwp' : invoice.partner_id.npwp or '',
				'no_faktur' : invoice.nomor_faktur_id and "%s.%s-%s.%s"%(invoice.kode_transaksi_faktur_pajak or '',invoice.nomor_faktur_id.nomor_perusahaan or '',invoice.nomor_faktur_id.tahun_penerbit or '',invoice.nomor_faktur_id.nomor_urut or '') or '',
				'inv_date' : date_invoice,
				'currency_name' : invoice.currency_id.name,
				'dpp_usd' : invoice.currency_id.name=='IDR' and dpp_usd or False,
				'dpp_usd2' : invoice.currency_id.name!='IDR' and dpp_usd2 or False,
				'acc_rate' : invoice.currency_id.name=='IDR' and 1/acc_rate or False,
				'kmk_rate' : invoice.currency_id.name=='IDR' and False or kmk_rate,
				'dpp_01' : fp_code=='01' and dpp_idr or False,
				'dpp_09' : fp_code=='09' and dpp_idr or False,
				'dpp_07' : fp_code=='07' and dpp_idr or False,
				'dpp_08' : fp_code=='08' and dpp_idr or False,
				'ppn_0109' : fp_code in ('01','09') and tax_idr or False,
				'ppn_0708' : fp_code in ('07','08') and tax_idr or False,
			})
		return res

	def set_context(self, objects, data, ids, report_type=None):
		"""Populate a ledger_lines attribute on each browse record that will
		   be used by mako template"""		

		move_line_ids = []
		lines_result = []
		if data['form']['sale_type'] == 'export':
			move_line_ids = self._get_stock_move_ids(data)
			lines_result = self._sale_datas(move_line_ids)
		elif data['form']['sale_type'] == 'local':
			invoice_ids = self._get_invoice_ids(data)
			lines_result = self._invoice_datas(invoice_ids)
		context_report_values = {
			'sale_type': data['form']['sale_type'],
			'start_date': data['form']['date_from'],
			'stop_date': data['form']['date_from'],
			'goods_type': data['form']['goods_type'],
			'sale_lines' : lines_result,
		}

		self.localcontext.update(context_report_values)

		return super(RawSalesReportWebkit, self).set_context(
			objects, data, move_line_ids, report_type=report_type)

class RawSalesReportExcel(report_xls):
	# column_sizes = [x[1] for x in _column_sizes]
	def generate_xls_report(self, _p, _xs, data, objects, wb):

		ws = wb.add_sheet("%s %s"%(_p.report_name or '',_p.sale_type.upper()))
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		row_pos = 0

		# set print header/footer
		ws.header_str = self.xls_headers['standard']
		ws.footer_str = self.xls_footers['standard']

		if _p.sale_type == 'export' :
			# Column Header Row
			cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
			c_hdr_cell_style = xlwt.easyxf(cell_format)
			c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
			c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			c_hdr_cell_style_decimal = xlwt.easyxf(
				cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)

			c_specs = [
				('inv_year', 1, 0, 'text', _('Year'), None, c_hdr_cell_style),
				('goods_type', 1, 0, 'text', _('Product Type'), None, c_hdr_cell_style),
				('production_unit', 1, 0, 'text', _('Unit'), None, c_hdr_cell_style),
				('period', 1, 0, 'text', _('Period'), None, c_hdr_cell_style),
				('sale_type', 1, 0, 'text', _('Type'), None, c_hdr_cell_style),
				('picking_no', 1, 0, 'text', _('DO. No.'), None, c_hdr_cell_style),
				('invoice_number', 1, 0, 'text', _('Invoice No.'), None, c_hdr_cell_style),
				('peb_number', 1, 0, 'text', _('PEB No.'), None, c_hdr_cell_style),
				('peb_date', 1, 0, 'text', _('PEB Date'), None, c_hdr_cell_style),
				('customer_name', 1, 0, 'text', _('Customer'), None, c_hdr_cell_style),
				('currency', 1, 0, 'text', _('Curry'), None, c_hdr_cell_style),
				('price_subtotal', 1, 0, 'text', _('Inv. Amount'), None, c_hdr_cell_style),
				('kmk_rate', 1, 0, 'text', _('Rate KMK'), None, c_hdr_cell_style),
				('price_subtotal_idr', 1, 0, 'text', _('Rp as per Sales'), None, c_hdr_cell_style),
				('count', 1, 0, 'text', _('Count'), None, c_hdr_cell_style),
				('blend_code', 1, 0, 'text', _('Blend'), None, c_hdr_cell_style),
				('product_name', 1, 0, 'text', _('Description'), None, c_hdr_cell_style),
				('product_qty', 1, 0, 'text', _('Quantity'), None, c_hdr_cell_style),
				('product_uom', 1, 0, 'text', _('UoM'), None, c_hdr_cell_style),
				('lc_number', 1, 0, 'text', _('LC/TT No.'), None, c_hdr_cell_style),
				('dest_port', 1, 0, 'text', _('Destination'), None, c_hdr_cell_style),
				('bl_number', 1, 0, 'text', _('BL No.'), None, c_hdr_cell_style),
				('bl_date', 1, 0, 'text', _('BL Date'), None, c_hdr_cell_style),
				('shipping_line', 1, 0, 'text', _('Shipping Line'), None, c_hdr_cell_style),
				('container_number', 1, 0, 'text', _('Container No.'), None, c_hdr_cell_style),
				('nego_date', 1, 0, 'text', _('Nego Date'), None, c_hdr_cell_style),
				('nego_bank', 1, 0, 'text', _('Nego Bank'), None, c_hdr_cell_style),
				('real_date', 1, 0, 'text', _('Real Date'), None, c_hdr_cell_style),
				('real_bank', 1, 0, 'text', _('Real Bank'), None, c_hdr_cell_style),
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
			for line in _p.sale_lines:
				c_specs = [
					('inv_year', 1, 0, 'text', line.get('inv_year') or ''),
					('goods_type', 1, 0, 'text', line.get('goods_type') or ''),
					('production_unit', 1, 0, 'text', line.get('production_unit') or ''),
					('period', 1, 0, 'text', line.get('inv_period') or ''),
					('sale_type', 1, 0, 'text', line.get('sale_type') or ''),
					('picking_no', 1, 0, 'text', line.get('picking_no') or ''),
					('invoice_no', 1, 0, 'text', line.get('invoice_no') or ''),
					('peb_number', 1, 0, 'text', line.get('peb_number') or ''),
					('peb_date', 1, 0, 'text', line.get('peb_date') or ''),
					# ('peb_date', 1, 0, 'text', ''),
					('customer_name', 1, 0, 'text', line.get('customer_name') or ''),
					('currency', 1, 0, 'text', line.get('currency_name') or ''),
					('price_subtotal', 1, 0, 'number', line.get('price_subtotal', 0.0), None, ll_cell_style_decimal),
					('kmk_rate', 1, 0, 'number', line.get('kmk_rate', 0.0), None, ll_cell_style_decimal),
					('price_subtotal_idr', 1, 0, 'number', line.get('price_subtotal_idr', 0.0), None, ll_cell_style_decimal),
					('count', 1, 0, 'text', line.get('count_number') or ''),
					('blend_code', 1, 0, 'text', line.get('blend_code') or ''),
					('product_name', 1, 0, 'text', line.get('product_name') or ''),
					('product_qty', 1, 0, 'number', line.get('product_qty', 0.0), None, ll_cell_style_decimal),
					('product_uom', 1, 0, 'text', line.get('product_uom') or ''),
					('lc_number', 1, 0, 'text', line.get('lc_number') or ''),
					('dest_port', 1, 0, 'text', line.get('dest_port') or ''),
					('bl_number', 1, 0, 'text', line.get('bl_number') or ''),
					('bl_date', 1, 0, 'text', line.get('bl_date') or ''),
					# ('bl_date', 1, 0, 'text', ''),
					('shipping_line', 1, 0, 'text', line.get('shipping_line') or ''),
					('container_number', 1, 0, 'text', line.get('container_number') or ''),
					('nego_date', 1, 0, 'text', line.get('nego_date') or ''),
					# ('nego_date', 1, 0, 'text', ''),
					('nego_bank', 1, 0, 'text', line.get('nego_bank') or ''),
					('real_date', 1, 0, 'text', line.get('real_date') or ''),
					# ('real_date', 1, 0, 'text', ''),
					('real_bank', 1, 0, 'text', line.get('real_bank') or ''),
				]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)
		elif _p.sale_type == 'local' :
			# Column Header Row
			cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
			c_hdr_cell_style = xlwt.easyxf(cell_format)
			c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
			c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
			c_hdr_cell_style_decimal = xlwt.easyxf(
				cell_format + _xs['right'],
				num_format_str=report_xls.decimal_format)

			c_specs = [
				('inv_month', 1, 0, 'text', _('Month'), None, c_hdr_cell_style),
				('fp_code', 1, 0, 'text', _('Code'), None, c_hdr_cell_style),
				('cust_npwp_type', 1, 0, 'text', _('Type'), None, c_hdr_cell_style),
				('customer_name', 1, 0, 'text', _('Customer'), None, c_hdr_cell_style),
				('cust_npwp', 1, 0, 'text', _('NPWP'), None, c_hdr_cell_style),
				('no_faktur', 1, 0, 'text', _('No. Faktur Pajak'), None, c_hdr_cell_style),
				('inv_date', 1, 0, 'text', _('Tanggal'), None, c_hdr_cell_style),
				('currency_name', 1, 0, 'text', _('Ccy'), None, c_hdr_cell_style),
				('dpp_usd', 1, 0, 'text', _('DPP USD (IDR Sales)'), None, c_hdr_cell_style),
				('dpp_usd2', 1, 0, 'text', _('DPP USD (USD Sales)'), None, c_hdr_cell_style),
				('acc_rate', 1, 0, 'text', _('Rate ACC'), None, c_hdr_cell_style),
				('kmk_rate', 1, 0, 'text', _('Rate KMK'), None, c_hdr_cell_style),
				('dpp_01', 1, 0, 'text', _('DPP 1111 I A.2'), None, c_hdr_cell_style),
				('dpp_09', 1, 0, 'text', _('DPP 1111 I A.3'), None, c_hdr_cell_style),
				('dpp_07', 1, 0, 'text', _('DPP 1111 I A.4'), None, c_hdr_cell_style),
				('dpp_08', 1, 0, 'text', _('DPP 1111 I A.5'), None, c_hdr_cell_style),
				('ppn_0109', 1, 0, 'text', _('PPN Code FP:01,09'), None, c_hdr_cell_style),
				('ppn_0708', 1, 0, 'text', _('PPN Code FP:07,08'), None, c_hdr_cell_style),
				('no_faktur_pengganti', 1, 0, 'text', _('Faktur Pajak\nDigantikan/Diretur/Dibatalkan'), None, c_hdr_cell_style),
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
			for line in _p.sale_lines:
				c_specs = [
					('inv_month', 1, 0, 'text', line.get('inv_month') or ''),
					('fp_code', 1, 0, 'text', line.get('fp_code') or ''),
					('cust_npwp_type', 1, 0, 'text', line.get('cust_npwp_type') or ''),
					('customer_name', 1, 0, 'text', line.get('customer_name') or ''),
					('cust_npwp', 1, 0, 'text', line.get('cust_npwp') or ''),
					('no_faktur', 1, 0, 'text', line.get('no_faktur') or ''),
					('inv_date', 1, 0, 'date', line.get('inv_date') or ''),
					('currency_name', 1, 0, 'text', line.get('currency_name') or ''),
					('dpp_usd', 1, 0, 'number', line.get('dpp_usd', 0.0), None, ll_cell_style_decimal),
					('dpp_usd2', 1, 0, 'number', line.get('dpp_usd2', 0.0), None, ll_cell_style_decimal),
					('acc_rate', 1, 0, 'number', line.get('acc_rate', 0.0), None, ll_cell_style_decimal),
					('kmk_rate', 1, 0, 'number', line.get('kmk_rate', 0.0), None, ll_cell_style_decimal),
					('dpp_01', 1, 0, 'number', line.get('dpp_01', 0.0), None, ll_cell_style_decimal),
					('dpp_09', 1, 0, 'number', line.get('dpp_09', 0.0), None, ll_cell_style_decimal),
					('dpp_07', 1, 0, 'number', line.get('dpp_07', 0.0), None, ll_cell_style_decimal),
					('dpp_08', 1, 0, 'number', line.get('dpp_08', 0.0), None, ll_cell_style_decimal),
					('ppn_0109', 1, 0, 'number', line.get('ppn_0109', 0.0), None, ll_cell_style_decimal),
					('ppn_0708', 1, 0, 'number', line.get('ppn_0708', 0.0), None, ll_cell_style_decimal),
					('no_faktur_pengganti', 1, 0, 'text', line.get('no_faktur_pengganti') or ''),
				]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)
RawSalesReportExcel('report.raw.sales.report', 'stock.move', 
	# 'addons/ad_sales_report/report/sales_report.mako', 
	parser=RawSalesReportWebkit)
