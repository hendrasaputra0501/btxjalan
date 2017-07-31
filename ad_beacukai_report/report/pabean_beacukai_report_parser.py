import re
import time
import xlwt
from report import report_sxw
from report_xls.report_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
import netsvc
 
class pabean_beacukai_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(pabean_beacukai_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
		})

_column_sizes = [
	('seq', 4),
	('document_type', 10),
	('registration_no', 12),
	('registration_date', 12),
	('picking_no', 12),
	('picking_date', 12),
	('partner', 30),
	('product_code', 15),
	('product_name', 30),
	('product_uom', 8),
	('product_qty', 15),
	('currency_id', 7),
	('price_unit', 15),
]

_document_type = {
	1:'BC 2.3',
	6:'BC 2.5',
	71:'BC 2.61',
	72:'BC 2.62',
	21:'BC 2.7 Masukan',
	22:'BC 2.7 Keluaran',
	5:'BC 3.0',
	3:'BC 4.0',
	4:'BC 4.1',
}

class pabean_beacukai_report_xls_report(report_xls):
	column_sizes = [x[1] for x in _column_sizes]
	# document_type = _document_type.copy()
	def generate_xls_report(self, parser, xls_style, data, objects, wb):
		shipment_type = objects and objects[0].sm_id and objects[0].sm_id.picking_id and objects[0].sm_id.type in ('in','out') and objects[0].sm_id.type or False
		if shipment_type == 'in':
			report_name = 'Laporan Penerimaan Barang'
		elif shipment_type == 'out':
			report_name = 'Laporan Pengeluaran Barang'
		else:
			report_name = 'Unidentify'

		ws = wb.add_sheet(report_name)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 90
		ws.normal_magn = 90
		ws.print_scaling = 100
		ws.page_preview = True
		# ws.set_fit_width_to_pages(1)
		row_pos = 0

		# set print header/footer
		ws.header_str = self.xls_headers['standard']
		ws.footer_str = self.xls_footers['standard']

		# cf. account_report_general_ledger.mako
		
		# initial_balance_text = {'initial_balance': _('Computed'),
		# 						'opening_balance': _('Opening Entries'),
		# 						False: _('No')}

		# Title
		cell_style = xlwt.easyxf(xls_style['xls_title'])
		report_name = report_name.upper()+" PER DOKUMEN PABEAN"
		c_specs = [
			('report_name', 13, 0, 'text', report_name),
		]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(
			ws, row_pos, row_data, row_style=cell_style)
		
		report_name2 = "KAWASAN BERIKAT %s"%parser.company.partner_id.name.upper()
		c_specs = [
			('report_name', 13, 0, 'text', report_name2),
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
		cell_format = xls_style['bold'] + xls_style['fill'] + xls_style['borders_all']
		cell_style = xlwt.easyxf(cell_format)
		cell_style_center = xlwt.easyxf(cell_format + xls_style['center'])
		# c_specs = [
		# 	('seq', 1, 0, 'text', _('No.'), None, cell_style_center),
		# 	('document_type', 1, 0, 'text', _('Jenis'), None, cell_style_center),
		# 	('registration_no', 1, 0, 'text', _('Nomer'), None, cell_style_center),
		# 	('registration_date', 1, 0, 'text', _('Tanggal'), None, cell_style_center),
		# 	('picking_no', 1, 0, 'text', _('Nomer'), None, cell_style_center),
		# 	('picking_date', 1, 0, 'text', _('Tanggal'), None, cell_style_center),
		# 	('partner', 1, 0, 'text', (shipment_type=='in' and 'Supplier' or (shipment_type=='out' and 'Customer' or 'Invalid Partner')), None, cell_style_center),
		# 	('product_code', 1, 0, 'text', _('Kode'), None, cell_style_center),
		# 	('product_name', 1, 0, 'text', _('Nama/Deskripsi'), None, cell_style_center),
		# 	('product_uom', 1, 0, 'text', _('Satuan'), None, cell_style_center),
		# 	('product_qty', 1, 0, 'text', _('Jumlah'), None, cell_style_center),
		# 	('currency_id', 1, 0, 'text', _('Valas'), None, cell_style_center),
		# 	('price_unit', 1, 0, 'text', _('Harga Barang'), None, cell_style_center),
		# 	]

		ws.write_merge(row_pos, row_pos+1, 0, 0, "No.", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 1, 1, "Jenis\nDokumen", cell_style_center)
		ws.write_merge(row_pos, row_pos, 2, 3, "Dokumen Pabean", cell_style_center)
		ws.write(row_pos+1, 2, "Nomor", cell_style_center)
		ws.write(row_pos+1, 3, "Tanggal", cell_style_center)
		ws.write_merge(row_pos, row_pos, 4, 5, shipment_type=='in' and "Bukti Penerimaan Barang" or "Bukti / Dokumen Pengeluaran", cell_style_center)
		ws.write(row_pos+1, 4, "Nomor", cell_style_center)
		ws.write(row_pos+1, 5, "Tanggal", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 6, 6, (shipment_type=='in' and 'Supplier' or (shipment_type=='out' and 'Customer' or 'Invalid Partner')), cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 7, 7, "Kode\nBarang", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 8, 8, "Nama Barang", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 9, 9, "Sat", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 10, 10, "Jumlah", cell_style_center)
		ws.write_merge(row_pos, row_pos+1, 11, 12, "Nilai Barang", cell_style_center)
		row_pos+=2
		# row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		# row_pos = self.xls_write_row(
		# 	ws, row_pos, row_data, row_style=cell_style_center)

		ws.set_horz_split_pos(row_pos)

		# cell styles for ledger lines
		ll_cell_format = xls_style['borders_all'] + xls_style['wrap'] + xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)

		cnt = 0
		for line in objects:

			# TO DO : replace cumul amounts by xls formulas
			cnt += 1
			cumul_debit = 0.0
			
			c_specs = [
					('seq', 1, 0, 'number', cnt, None, ll_cell_style),
					('document_type', 1, 0, 'text', _document_type.get(line.jns_pabean,False) and _document_type[line.jns_pabean] or '', None, ll_cell_style),
					('registration_no', 1, 0, 'text', line.no_pabean, None, ll_cell_style),
				]
			
			if line.tgl_pabean!=False:
				c_specs += [
					('registration_date', 1, 0, 'date', datetime.strptime(
						line.tgl_pabean, '%Y-%m-%d'), None,
					 ll_cell_style_date),
				]
			else:
				c_specs += [
					('ldate', 1, 0, 'text', None),
				]

			c_specs += [
				('picking_no', 1, 0, 'text',
				 line.picking_id and line.picking_id.name or ''),
				]

			if line.date!=False:
				c_specs += [
					('picking_date', 1, 0, 'date', datetime.strptime(
						line.date, '%Y-%m-%d'), None,
					 ll_cell_style_date),
				]
			else:
				c_specs += [
					('ldate', 1, 0, 'text', None),
				]

			c_specs+=[
				('partner', 1, 0, 'text', line.partner_name or '',
					None, ll_cell_style),
				('product_code', 1, 0, 'text', line.product_code or '',
					None, ll_cell_style),
				('product_name', 1, 0, 'text', line.product_name or '',
					None, ll_cell_style),
				('product_uom', 1, 0, 'text', line.product_uom and line.product_uom.name or '',
					None, ll_cell_style),
				('product_qty', 1, 0, 'number', line.product_qty or 0.0,
					None, ll_cell_style_decimal),
				('currency_id', 1, 0, 'text', line.currency_id and line.currency_id.name or '',
					None, ll_cell_style),
				('price_unit', 1, 0, 'number', line.subtotal or 0.0,
					None, ll_cell_style_decimal),
			]
			row_data = self.xls_row_template(
				c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, ll_cell_style)

pabean_beacukai_report_xls_report('report.pabean.report.xls','report.stock.move.pabean', parser=pabean_beacukai_report_parser, header=False)