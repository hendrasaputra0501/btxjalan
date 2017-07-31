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

# _column_sizes = [
# 	('date', 12),
# 	('period', 12),
# 	('move', 20),
# 	('journal', 12),
# 	('account_code', 12),
# 	('partner', 30),
# 	('label', 45),
# 	('counterpart', 30),
# 	('debit', 15),
# 	('credit', 15),
# 	('cumul_bal', 15),
# 	('curr_bal', 15),
# 	('curr_code', 7),
# ]

class PurchaseReceiptDetailsParser(report_sxw.rml_parse):

	def __init__(self, cursor, uid, name, context):
		super(PurchaseReceiptDetailsParser, self).__init__(cursor, uid, name,
												 context=context)
		self.pool = pooler.get_pool(self.cr.dbname)
		self.cursor = self.cr

		company = self.pool.get('res.users').browse(self.cr, uid, uid,
													context=context).company_id
		header_report_name = ' - '.join((_('Purchase Receipt Details'), company.name,
										 company.currency_id.name))

		footer_date_time = self.formatLang(str(datetime.today()),
										   date_time=True)

		self.localcontext.update({
			'cr': cursor,
			'uid': uid,
			'report_name': _('Purchase Receipt Details'),
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
		start_date = data['form']['date_start']
		end_date = data['form']['date_stop']
		purchase_type = data['form']['purchase_type']
		# usage = data['form']['usage']=='customer' and 'out' or 'in'
		query = """
			SELECT
				sm.id
			FROM
				stock_move sm
				INNER JOIN stock_picking sp ON sp.id=sm.picking_id
				LEFT JOIN account_invoice_line ail ON ail.id=sm.invoice_line_id
				LEFT JOIN account_invoice ai ON ai.id=ail.invoice_id and ai.id=sp.invoice_id
				LEFT JOIN purchase_order_line pol ON pol.id=sm.purchase_line_id
				LEFT JOIN purchase_order po ON po.id=pol.order_id
			WHERE sm.state='done' and sp.state='done' and sp.type in ('in','out') 
			 %s"""
		where1 = goods_type and " and (po.goods_type='%s' or sp.goods_type='%s') "%(goods_type,goods_type) or " "
		where2 = purchase_type and purchase_type=='all' and " and (po.purchase_type in ('local','import') or sp.purchase_type in ('local','import')) " or (purchase_type and " and (po.purchase_type='%s' or sp.purchase_type='%s') "%(purchase_type,purchase_type) or '')
		where_clause = " and sm.date between '%s 00:00:00' and '%s 23:59:59' %s %s "%\
							(start_date,end_date,where1,where2)
 		query = query%(where_clause)
 		self.cursor.execute(query)
		res = self.cursor.dictfetchall()
		move_ids = [x['id'] for x in res]
		return move_ids or []

	def _get_price_unit(self, move):
		cr = self.cr
		uid = self.uid
		if move.purchase_line_id:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in move.purchase_line_id.discount_ids],move.purchase_line_id.price_unit,move.purchase_line_id.product_qty)
			price_after = disc.get('price_after',move.purchase_line_id.price_unit)
		else:
			price_after = move.price_unit
		return price_after

	def _get_price_subtotal_po(self, move):
		tax_obj = self.pool.get('account.tax')
		cr = self.cr
		uid = self.uid
		if move.purchase_line_id:
			purchase_line = move.purchase_line_id
			price_subtotal = tax_obj.compute_all(cr, uid, purchase_line.taxes_id, self._get_price_unit(move), move.product_qty, product=move.product_id, partner=purchase_line.order_id.partner_id)['total']
		else:
			price_subtotal = move.price_unit*move.product_qty
		return price_subtotal

	def _get_inv_price_unit(self, move):
		cr = self.cr
		uid = self.uid
		if move.invoice_line_id:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in move.invoice_line_id.discount_ids],move.invoice_line_id.price_unit,move.invoice_line_id.product_qty)
			price_after = disc.get('price_after',move.invoice_line_id.price_unit)
		else:
			price_after = move.price_unit
		return price_after

	def _get_price_subtotal_inv(self, move):
		tax_obj = self.pool.get('account.tax')
		cr = self.cr
		uid = self.uid
		if move.invoice_line_id:
			invoice_line = move.invoice_line_id
			price_subtotal = tax_obj.compute_all(cr, uid, invoice_line.invoice_line_tax_id, self._get_price_unit(move), move.product_qty, product=move.product_id, partner=move.picking_id.partner_id)['total']
		else:
			price_subtotal = move.price_unit*move.product_qty
		return price_subtotal

	def _purchase_datas(self, stock_move_ids):
		cr = self.cr
		uid = self.uid
		move_lines = self.pool.get('stock.move').browse(cr, uid, stock_move_ids)

		# sale_line_grouped = {}
		res = []
		curr_obj = self.pool.get('res.currency')
		add_inv_info = True
		for line in  sorted(move_lines, key=lambda x:x.date):
			key = (line.sale_line_id.id, line.invoice_line_id.id)
			
			picking_date = datetime.strptime(line.date,"%Y-%m-%d %H:%M:%S")
			purchase_obj = line.purchase_line_id and line.purchase_line_id.order_id or False
			# tax_date = invoice_obj.tax_date !=False and invoice_obj.tax_date or invoice_obj.date_invoice
			# tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',invoice_obj.currency_id.id),('name','<=',tax_date)])
			sign = line.picking_id.type=='in' and 1 or -1
			price_subtotal = self._get_price_subtotal_po(line)
			result_dict = {
				'goods_type' : line.product_id.internal_type,
				'module_type' : 'PO',
				'picking_type' : line.picking_id.type=='in' and 'Receipt' or 'Retur',
				'whunit' : line.picking_id.type=='in' and line.location_dest_id.alias[:3] or line.location_id.alias[:3],
				'picking_no' : line.picking_id.name,
				'picking_date' : picking_date.strftime('%Y-%m-%d'),
				'partner_code' : purchase_obj and purchase_obj.partner_id.partner_code or (line.picking_id.partner_id and line.picking_id.partner_id.partner_code or ''),
				'partner_name' : purchase_obj and purchase_obj.partner_id.name or (line.picking_id.partner_id and line.picking_id.partner_id.name or ''),
				'currency_name' : purchase_obj and purchase_obj.pricelist_id.currency_id.name or 'USD',
				'inv_period' : picking_date.strftime('%m/%Y'),
				'price_subtotal' : sign*price_subtotal,
				'price_subtotal_usd' : sign*(line.product_qty*line.price_unit),
				'product_qty' : sign*line.product_qty,
				'product_code' : line.product_id.default_code,
			}

			if add_inv_info and line.invoice_line_id:
				invoice = line.invoice_line_id.invoice_id 
				inv_price_subtotal = self._get_price_subtotal_inv(line)
				result_dict.update({
					'inv_ref' : invoice.reference,
					'inv_number' : invoice.internal_number,
					'inv_price_subtotal' : sign*inv_price_subtotal,
					'inv_price_subtotal_usd' : sign*curr_obj.compute(cr, uid, invoice.currency_id.id, invoice.company_id.currency_id.id, price_subtotal, context={'date':invoice.date_invoice}),
					'ppv' : sign*(price_subtotal - inv_price_subtotal),
				})
			
				if line.invoice_line_id.invoice_id.faktur_pajak_lines:
					faktur_pajak_lines = line.invoice_line_id.invoice_id.faktur_pajak_lines
					fp_no = ["%s%s.%s-%s.%s"%(fp.kdJenisTransaksi or '00',fp.fgPengganti or '0',fp.nomorFaktur[:3],fp.nomorFaktur[3:5],fp.nomorFaktur[5:]) for fp  in faktur_pajak_lines]
					total_dpp = [fp.jumlahDpp for fp in faktur_pajak_lines]
					total_tax = [fp.jumlahPpn for fp in faktur_pajak_lines]
					
					result_dict.update({'faktur_pajak_no' : ", ".join(list(set(fp_no)))})
					result_dict.update({'total_dpp' : sum(total_dpp)})
					result_dict.update({'total_ppn' : sum(total_tax)})

			res.append(result_dict)
		return res

	def set_context(self, objects, data, ids, report_type=None):
		"""Populate a ledger_lines attribute on each browse record that will
		   be used by mako template"""		

		move_line_ids = self._get_stock_move_ids(data)
		lines_result = self._purchase_datas(move_line_ids)
		context_report_values = {
			'purchase_type': data['form']['purchase_type'],
			'start_date': data['form']['date_start'],
			'stop_date': data['form']['date_stop'],
			'goods_type': data['form']['goods_type'],
			'purchase_lines' : lines_result,
		}

		self.localcontext.update(context_report_values)

		return super(PurchaseReceiptDetailsParser, self).set_context(
			objects, data, move_line_ids, report_type=report_type)

class PurchaseReceiptExcel(report_xls):
	# column_sizes = [x[1] for x in _column_sizes]
	def generate_xls_report(self, _p, _xs, data, objects, wb):

		ws = wb.add_sheet("%s %s"%(_p.report_name or '',_p.purchase_type.upper()))
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
			('goods_type', 1, 0, 'text', _('Product Type'), None, c_hdr_cell_style),
			('module_type', 1, 0, 'text', _('Module'), None, c_hdr_cell_style),
			('picking_type', 1, 0, 'text', _('TransType'), None, c_hdr_cell_style),
			('whunit', 1, 0, 'text', _('Unit'), None, c_hdr_cell_style),
			('picking_no', 1, 0, 'text', _('MRR/Retur No.'), None, c_hdr_cell_style),
			('picking_date', 1, 0, 'text', _('MRR/Retur Date'), None, c_hdr_cell_style),
			('partner_code', 1, 0, 'text', _('Vendor Code'), None, c_hdr_cell_style),
			('partner_name', 1, 0, 'text', _('Vendor name'), None, c_hdr_cell_style),
			('currency_name', 1, 0, 'text', _('Ccy'), None, c_hdr_cell_style),
			('inv_period', 1, 0, 'text', _('Period'), None, c_hdr_cell_style),
			
			('price_subtotal', 1, 0, 'text', _('Cury Amount'), None, c_hdr_cell_style),
			('price_subtotal_usd', 1, 0, 'text', _('USD Amount'), None, c_hdr_cell_style),
			('product_qty', 1, 0, 'text', _('Quantity'), None, c_hdr_cell_style),
			('product_code', 1, 0, 'text', _('Product Code'), None, c_hdr_cell_style),
			
		]
		add_inv_info = True
		if add_inv_info:
			c_specs += [
			('inv_ref', 1, 0, 'text', _('Invoice No.'), None, c_hdr_cell_style),
			('inv_number', 1, 0, 'text', _('Voucher No.'), None, c_hdr_cell_style),
			('inv_price_subtotal', 1, 0, 'text', _('Cury Inv Amount'), None, c_hdr_cell_style),
			('inv_price_subtotal_usd', 1, 0, 'text', _('USD Inv Amount'), None, c_hdr_cell_style),
			('ppv', 1, 0, 'text', _('PPV'), None, c_hdr_cell_style),
			('faktur_pajak_no', 1, 0, 'text', _('No. Faktur'), None, c_hdr_cell_style),
			('total_dpp', 1, 0, 'text', _('Total DPP'), None, c_hdr_cell_style),
			('total_ppn', 1, 0, 'text', _('Total PPN'), None, c_hdr_cell_style),
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
		for line in _p.purchase_lines:
			c_specs = [
				('goods_type', 1, 0, 'text', line.get('goods_type') or ''),
				('module_type', 1, 0, 'text', line.get('module_type') or ''),
				('picking_type', 1, 0, 'text', line.get('picking_type') or ''),
				('whunit', 1, 0, 'text', line.get('whunit') or ''),
				('picking_no', 1, 0, 'text', line.get('picking_no') or ''),
				('picking_date', 1, 0, 'text', line.get('picking_date') or ''),
				('partner_code', 1, 0, 'text', line.get('partner_code') or ''),
				('partner_name', 1, 0, 'text', line.get('partner_name') or ''),
				('currency_name', 1, 0, 'text', line.get('currency_name') or ''),
				('period', 1, 0, 'text', line.get('inv_period') or ''),
				('price_subtotal', 1, 0, 'number', line.get('price_subtotal', 0.0), None, ll_cell_style_decimal),
				('price_subtotal_usd', 1, 0, 'number', line.get('price_subtotal_usd', 0.0), None, ll_cell_style_decimal),
				('product_qty', 1, 0, 'number', line.get('product_qty', 0.0), None, ll_cell_style_decimal),
				('product_code', 1, 0, 'text', line.get('product_code') or ''),
			]
			if add_inv_info:
				c_specs += [
				('inv_ref', 1, 0, 'text', line.get('inv_ref') or ''),
				('inv_number', 1, 0, 'text', line.get('inv_number') or ''),
				('inv_price_subtotal', 1, 0, 'number', line.get('inv_price_subtotal', 0.0), None, ll_cell_style_decimal),
				('inv_price_subtotal_usd', 1, 0, 'number', line.get('inv_price_subtotal_usd', 0.0), None, ll_cell_style_decimal),
				('ppv', 1, 0, 'number', line.get('ppv', 0.0), None, ll_cell_style_decimal),
				('faktur_pajak_no', 1, 0, 'text', line.get('faktur_pajak_no') or ''),
				('total_dpp', 1, 0, 'number', line.get('total_dpp', 0.0), None, ll_cell_style_decimal),
				('total_ppn', 1, 0, 'number', line.get('total_ppn', 0.0), None, ll_cell_style_decimal),
				]
			row_data = self.xls_row_template(
				c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, ll_cell_style)
		
PurchaseReceiptExcel('report.purchase.receipt_details', 'stock.move', 
	parser=PurchaseReceiptDetailsParser)
