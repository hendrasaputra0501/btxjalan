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
 
class export_ceisa_template_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(export_ceisa_template_parser, self).__init__(cr, uid, name, context=context)
		# if context.get('active_model',False) == 'beacukai.document.line.in':
		# 	report_name = 'Laporan Penerimaan Barang'
		# 	shipment_type = 'in'
		# else:
		# 	report_name = 'Laporan Pengeluaran Barang'
		# 	shipment_type = 'out'
		self.localcontext.update({
			'time': time,
			# 'report_name': report_name,
			# 'shipment_type': shipment_type,

		})
# report_sxw.report_sxw('report.beacukai.out.form':'beacukai.document.line':'beacukai/report/beacukai_line.mako', parser=export_ceisa_template_parser, header=False)

_document_type = {
	'23':'BC 2.3',
	'25':'BC 2.5',
	'261':'BC 2.61',
	'262':'BC 2.62',
	'27in':'BC 2.7 Masukan',
	'27out':'BC 2.7 Keluaran',
	'30':'BC 3.0',
	'40':'BC 4.0',
	'41':'BC 4.1',
}

class beacukai_doc_report_xls(report_xls):
	def generate_xls_report(self, parser, xls_style, data, objects, wb):
		# Sheet Header
		ws = wb.add_sheet("Header")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('kode_kantor', 1, 0, 'text', _('KPPBC'), None), #B
			('nama_pengusaha', 1, 0, 'text', _('PERUSAHAAN'), None), #C
			('nama_pemasok', 1, 0, 'text', _('PEMASOK'), None), #D
			('state', 1, 0, 'text', _('STATUS'), None), #E
			('kode_dokumen_pabean', 1, 0, 'text', _('KODE DOKUMEN PABEAN'), None), #F
			('nppjk', 1, 0, 'text', _('NPPJK'), None), #G
			('alamat_pemasok', 1, 0, 'text', _('ALAMAT PEMASOK'), None), #H
			('alamat_pemilik', 1, 0, 'text', _('ALAMAT PEMILIK'), None), #I
			('alamat_penerima_barang', 1, 0, 'text', _('ALAMAT PENERIMA BARANG'), None), #J
			('alamat_pengirim', 1, 0, 'text', _('ALAMAT PENGIRIM'), None), #K
			('alamat_pengusaha', 1, 0, 'text', _('ALAMAT PENGUSAHA'), None), #L
			('alamat_ppjk', 1, 0, 'text', _('ALAMAT PPJK'), None), #M
			('api_pemilik', 1, 0, 'text', _('API PEMILIK'), None), #N
			('api_penerima', 1, 0, 'text', _('API PENERIMA'), None), #O
			('api_pengusaha', 1, 0, 'text', _('API PENGUSAHA'), None), #P
			('asal_data', 1, 0, 'text', _('ASAL DATA'), None), #Q
			('asuransi', 1, 0, 'text', _('ASURANSI'), None), #R
			('biaya_tambahan', 1, 0, 'text', _('BIAYA TAMBAHAN'), None), #S
			('bruto', 1, 0, 'text', _('BRUTO'), None), #T
			('cif', 1, 0, 'text', _('CIF'), None), #U
			('cif_rupiah', 1, 0, 'text', _('CIF RUPIAH'), None), #V
			('diskon', 1, 0, 'text', _('DISKON'), None), #W
			('flag_pemilik', 1, 0, 'text', _('FLAG PEMILIK'), None), #X
			('url_dokumen_pabean', 1, 0, 'text', _('URL DOKUMEN PABEAN'), None), #Y
			('fob', 1, 0, 'text', _('FOB'), None), #Z
			('freight', 1, 0, 'text', _('FREIGHT'), None), #AA
			('harga_barang_ldp', 1, 0, 'text', _('HARGA BARANG LDP'), None), #AB
			('harga_invoice', 1, 0, 'text', _('HARGA INVOICE'), None), #AC
			('harga_penyerahan', 1, 0, 'text', _('HARGA PENYERAHAN'), None), #AD
			('harga_total', 1, 0, 'text', _('HARGA TOTAL'), None), #AE
			('id_modul', 1, 0, 'text', _('ID MODUL'), None), #AF
			('id_pemasok', 1, 0, 'text', _('ID PEMASOK'), None), #AG
			('id_pemilik', 1, 0, 'text', _('ID PEMILIK'), None), #AH
			('id_penerima_barang', 1, 0, 'text', _('ID PENERIMA BARANG'), None), #AI
			('id_pengirim', 1, 0, 'text', _('ID PENGIRIM'), None), #AJ
			('id_pengusaha', 1, 0, 'text', _('ID PENGUSAHA'), None), #AK
			('id_ppjk', 1, 0, 'text', _('ID PPJK'), None), #AL
			('jabatan_ttd', 1, 0, 'text', _('JABATAN TTD'), None), #AM
			('jumlah_barang', 1, 0, 'text', _('JUMLAH BARANG'), None), #AN
			('jumlah_kemasan', 1, 0, 'text', _('JUMLAH KEMASAN'), None), #AO
			('jumlah_kontainer', 1, 0, 'text', _('JUMLAH KONTAINER'), None), #AP
			('kesesuaian_dokumen', 1, 0, 'text', _('KESESUAIAN DOKUMEN'), None), #AQ
			('keterangan', 1, 0, 'text', _('KETERANGAN'), None), #AR
			('kode_asal_barang', 1, 0, 'text', _('KODE ASAL BARANG'), None), #AS
			('kode_asuransi', 1, 0, 'text', _('KODE ASURANSI'), None), #AT
			('kode_bendera', 1, 0, 'text', _('KODE BENDERA'), None), #AU
			('kode_cara_angkut', 1, 0, 'text', _('KODE CARA ANGKUT'), None), #AV
			('kode_cara_bayar', 1, 0, 'text', _('KODE CARA BAYAR'), None), #AW
			('kode_daerah_asal', 1, 0, 'text', _('KODE DAERAH ASAL'), None), #AX
			('kode_fasilitas', 1, 0, 'text', _('KODE FASILITAS'), None), #AY
			('kode_ftz', 1, 0, 'text', _('KODE FTZ'), None), #AZ
			('kode_harga', 1, 0, 'text', _('KODE HARGA'), None), #BA
			('kode_id_pemasok', 1, 0, 'text', _('KODE ID PEMASOK'), None), #BB
			('kode_id_pemilik', 1, 0, 'text', _('KODE ID PEMILIK'), None), #BC
			('kode_id_penerima_barang', 1, 0, 'text', _('KODE ID PENERIMA BARANG'), None), #BD
			('kode_id_pengirim', 1, 0, 'text', _('KODE ID PENGIRIM'), None), #BE
			('kode_id_pengusaha', 1, 0, 'text', _('KODE ID PENGUSAHA'), None), #BF
			('kode_id_ppjk', 1, 0, 'text', _('KODE ID PPJK'), None), #BG
			('kode_jenis_api', 1, 0, 'text', _('KODE JENIS API'), None), #BH
			('kode_jenis_api_pemilik', 1, 0, 'text', _('KODE JENIS API PEMILIK'), None), #BI
			('kode_jenis_api_penerima', 1, 0, 'text', _('KODE JENIS API PENERIMA'), None), #BJ
			('kode_jenis_api_pengusaha', 1, 0, 'text', _('KODE JENIS API PENGUSAHA'), None), #BK
			('kode_jenis_barang', 1, 0, 'text', _('KODE JENIS BARANG'), None), #BL
			('kode_jenis_bc25', 1, 0, 'text', _('KODE JENIS BC25'), None), #BM
			('kode_jenis_nilai', 1, 0, 'text', _('KODE JENIS NILAI'), None), #BN
			('kode_jenis_pemasukan01', 1, 0, 'text', _('KODE JENIS PEMASUKAN01'), None), #BO
			('kode_jenis_pemasukan02', 1, 0, 'text', _('KODE JENIS PEMASUKAN 02'), None), #BP
			('kode_jenis_tpb', 1, 0, 'text', _('KODE JENIS TPB'), None), #BQ
			('kode_kantor_bongkar', 1, 0, 'text', _('KODE KANTOR BONGKAR'), None), #BR
			('kode_kantor_tujuan', 1, 0, 'text', _('KODE KANTOR TUJUAN'), None), #BS
			('kode_loakasi_bayar', 1, 0, 'text', _('KODE LOKASI BAYAR'), None), #BT
			('empty_column01', 1, 0, 'text', _(''), None), #BU
			('kode_negara_pemasok', 1, 0, 'text', _('KODE NEGARA PEMASOK'), None), #BV
			('kode_negara_pengirim', 1, 0, 'text', _('KODE NEGARA PENGIRIM'), None), #BW
			('kode_negara_pemilik', 1, 0, 'text', _('KODE NEGARA PEMILIK'), None), #BX
			('kode_negara_tujuan', 1, 0, 'text', _('KODE NEGARA TUJUAN'), None), #BY
			('kode_pel_bongkar', 1, 0, 'text', _('KODE PEL BONGKAR'), None), #BZ
			('kode_pel_muat', 1, 0, 'text', _('KODE PEL MUAT'), None), #CA
			('kode_pel_transit', 1, 0, 'text', _('KODE PEL TRANSIT'), None), #CB
			('kode_pembayar', 1, 0, 'text', _('KODE PEMBAYAR'), None), #CC
			('kode_status_pengusaha', 1, 0, 'text', _('KODE STATUS PENGUSAHA'), None), #CD
			('status_perbaikan', 1, 0, 'text', _('STATUS PERBAIKAN'), None), #CE
			('kode_tps', 1, 0, 'text', _('KODE TPS'), None), #CF
			('kode_tujuan_pemasukan', 1, 0, 'text', _('KODE TUJUAN PEMASUKAN'), None), #CG
			('kode_tujuan_pengiriman', 1, 0, 'text', _('KODE TUJUAN PENGIRIMAN'), None), #CH
			('kode_tujuan_tpb', 1, 0, 'text', _('KODE TUJUAN TPB'), None), #CI
			('kode_tutup_pu', 1, 0, 'text', _('KODE TUTUP PU'), None), #CJ
			('kode_valuta', 1, 0, 'text', _('KODE VALUTA'), None), #CK
			('kota_ttd', 1, 0, 'text', _('KOTA TTD'), None), #CL
			('nama_pemilik', 1, 0, 'text', _('NAMA PEMILIK'), None), #CM
			('nama_penerima_barang', 1, 0, 'text', _('NAMA PENERIMA BARANG'), None), #CN
			('nama_pengangkut', 1, 0, 'text', _('NAMA PENGANGKUT'), None), #CO
			('nama_pengirim', 1, 0, 'text', _('NAMA PENGIRIM'), None), #CP
			('nama_ppjk', 1, 0, 'text', _('NAMA PPJK'), None), #CQ
			('nama_ttd', 1, 0, 'text', _('NAMA TTD'), None), #CR
			('ndpbm', 1, 0, 'text', _('NDPBM'), None), #CS
			('netto', 1, 0, 'text', _('NETTO'), None), #CT
			('nilai_incoterm', 1, 0, 'text', _('NILAI INCOTERM'), None), #CU
			('niper_penerima', 1, 0, 'text', _('NIPER PENERIMA'), None), #CV
			('nomor_api', 1, 0, 'text', _('NOMOR API'), None), #CW
			('nomor_bc11', 1, 0, 'text', _('NOMOR BC11'), None), #CX
			('nomor_billing', 1, 0, 'text', _('NOMOR BILLING'), None), #CY
			('nomor_daftar', 1, 0, 'text', _('NOMOR DAFTAR'), None), #CZ
			('nomor_ijin_bpk_pemasok', 1, 0, 'text', _('NOMOR IJIN BPK PEMASOK'), None), #DA
			('nomor_ijin_bpk_pengusaha', 1, 0, 'text', _('NOMOR IJIN BPK PENGUSAHA'), None), #DB
			('nomor_ijin_tpb', 1, 0, 'text', _('NOMOR IJIN TPB'), None), #DC
			('nomor_ijin_tpb_penerima', 1, 0, 'text', _('NOMOR IJIN TPB PENERIMA'), None), #DD
			('nomor_voyv_flight', 1, 0, 'text', _('NOMOR VOYV FLIGHT'), None), #DE
			('npwp_billing', 1, 0, 'text', _('NPWP BILLING'), None), #DF
			('pos_bc11', 1, 0, 'text', _('POS BC11'), None), #DG
			('seri', 1, 0, 'text', _('SERI'), None), #DH
			('subpos_bc11', 1, 0, 'text', _('SUBPOS BC11'), None), #DI
			('sub_subpos_bc11', 1, 0, 'text', _('SUB SUBPOS BC11'), None), #DJ
			('tanggal_bc11', 1, 0, 'text', _('TANGGAL BC11'), None), #DK
			('tanggal_berangkat', 1, 0, 'text', _('TANGGAL BERANGKAT'), None), #DL
			('tanggal_billing', 1, 0, 'text', _('TANGGAL BILLING'), None), #DM
			('tanggal_daftar', 1, 0, 'text', _('TANGGAL DAFTAR'), None), #DN
			('tanggal_ijin_bpk_pemasok', 1, 0, 'text', _('TANGGAL IJIN BPK PEMASOK'), None), #DO
			('tanggal_ijin_bpk_pengusaha', 1, 0, 'text', _('TANGGAL IJIN BPK PENGUSAHA'), None), #DP
			('tanggal_ijin_tpb', 1, 0, 'text', _('TANGGAL IJIN TPB'), None), #DQ
			('tanggal_npppjk', 1, 0, 'text', _('TANGGAL NPPPJK'), None), #DR
			('tanggal_tiba', 1, 0, 'text', _('TANGGAL TIBA'), None), #DS
			('tanggal_ttd', 1, 0, 'text', _('TANGGAL TTD'), None), #DT
			('tanggal_jatuh_tempo', 1, 0, 'text', _('TANGGAL JATUH TEMPO'), None), #DU
			('total_bayar', 1, 0, 'text', _('TOTAL BAYAR'), None), #DV
			('total_bebas', 1, 0, 'text', _('TOTAL BEBAS'), None), #DW
			('total_dilunasi', 1, 0, 'text', _('TOTAL DILUNASI'), None), #DX
			('total_jamin', 1, 0, 'text', _('TOTAL JAMIN'), None), #DY
			('total_sudah_dilunasi', 1, 0, 'text', _('TOTAL SUDAH DILUNASI'), None), #DZ
			('total_tangguh', 1, 0, 'text', _('TOTAL TANGGUH'), None), #EA
			('total_tanggung', 1, 0, 'text', _('TOTAL TANGGUNG'), None), #EB
			('total_tidak_dipungut', 1, 0, 'text', _('TOTAL TIDAK DIPUNGUT'), None), #EC
			('url_dokumen_pabean', 1, 0, 'text', _('URL DOKUMEN PABEAN'), None), #ED
			('versi_modul', 1, 0, 'text', _('VERSI MODUL'), None), #EE
			('volume', 1, 0, 'text', _('VOLUME'), None), #EF
			('waktu_bongkar', 1, 0, 'text', _('WAKTU BONGKAR'), None), #EG
			('waktu_stuffing', 1, 0, 'text', _('WAKTU STUFFING'), None), #EH
			('nomor_polisi', 1, 0, 'text', _('NOMOR POLISI'), None), #EI
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		n = 0
		for obj in objects:
			n+=1
			c_specs = [
				('nomor_aju', 1, 0, 'text', obj.name or '', None),
				('kode_kantor', 1, 0, 'text', obj.pabean_office_id.code or '', None),
				('nama_pengusaha', 1, 0, 'text', 'PT. BITRATEX INDUSTRIES', None),
				('nama_pemasok', 1, 0, 'text', obj.document_type=='41' and obj.dest_partner_id.name or '', None), #D
				('state', 1, 0, 'text', '00', None), #E
				('kode_dokumen_pabean', 1, 0, 'text', obj.document_type in ('27_in','27_out') and '27' or obj.document_type, None),
				('nppjk', 1, 0, 'text', '', None), #G
				('alamat_pemasok', 1, 0, 'text', obj.document_type=='41' and obj.dest_address or '', None), #H
				('alamat_pemilik', 1, 0, 'text', '', None), #I
				('alamat_penerima_barang', 1, 0, 'text', obj.document_type=='27_in' or obj.source_address or (obj.document_type=='27_out' and obj.dest_address or ''), None), #J
				('alamat_pengirim', 1, 0, 'text', obj.document_type=='40' and obj.source_address or '', None),
				('alamat_pengusaha', 1, 0, 'text', 'JALAN BRIGJEN S. SUDIARTO KM. 11, DESA PLAMONGANSARI, KECAMATAN PEDURUNGAN, SEMARANG, JAWA TENGAH', None),
				('alamat_ppjk', 1, 0, 'text', '', None), #M
				('api_pemilik', 1, 0, 'text', '', None), #N
				('api_penerima', 1, 0, 'text', '', None), #O
				('api_pengusaha', 1, 0, 'text', '', None), #P
				('asal_data', 1, 0, 'text', '', None), #Q
				('asuransi', 1, 0, 'text', '', None), #R
				('biaya_tambahan', 1, 0, 'text', '', None), #S
				('bruto', 1, 0, 'number', obj.gross_weight or 0.0, None),
				('cif', 1, 0, 'text', '', None), #U
				('cif_rupiah', 1, 0, 'number', 0, None), #V
				('diskon', 1, 0, 'text', '', None), #W
				('flag_pemilik', 1, 0, 'text', '', None), #X
				('url_dokumen_pabean', 1, 0, 'text', '', None), #Y
				('fob', 1, 0, 'text', '', None), #Z
				('freight', 1, 0, 'text', '', None), #AA
				('harga_barang_ldp', 1, 0, 'text', '', None), #AB
				('harga_invoice', 1, 0, 'text', '', None), #AC
				('harga_penyerahan', 1, 0, 'number', obj.amount_idr or 0.0, None),
				('harga_total', 1, 0, 'text', '', None), #AE
				('id_modul', 1, 0, 'text', '', None), #AF
				('id_pemasok', 1, 0, 'text', obj.document_type=='41' and obj.dest_partner_id.npwp and obj.dest_partner_id.npwp.replace('.','').replace('-','') or '', None),
				('id_pemilik', 1, 0, 'text', '', None), #AH
				('id_penerima_barang', 1, 0, 'text', obj.document_type=='27_in' and obj.source_partner_id.npwp and obj.source_partner_id.npwp.replace('.','').replace('-','') or  (obj.document_type=='27_out' and obj.dest_partner_id.npwp and obj.dest_partner_id.npwp.replace('.','').replace('-','') or ''), None),
				('id_pengirim', 1, 0, 'text', obj.document_type=='40' and obj.source_partner_id.npwp and obj.source_partner_id.npwp.replace('.','').replace('-','') or '', None),
				('id_pengusaha', 1, 0, 'text', obj.info_partner_id.npwp and obj.info_partner_id.npwp.replace('.','').replace('-','') or '', None),
				('id_ppjk', 1, 0, 'text', '', None), #AL
				('jabatan_ttd', 1, 0, 'text', 'KUASA DIREKSI', None),
				('jumlah_barang', 1, 0, 'number', len([x.id for x in obj.detail_packing_id]), None),
				('jumlah_kemasan', 1, 0, 'number', len(obj.beacukai_product_packages), None),
				('jumlah_kontainer', 1, 0, 'text', '', None), #AP
				('kesesuaian_dokumen', 1, 0, 'text', '', None), #AQ
				('keterangan', 1, 0, 'text', '', None), #AR
				('kode_asal_barang', 1, 0, 'text', '', None), #AS
				('kode_asuransi', 1, 0, 'text', '', None), #AT
				('kode_bendera', 1, 0, 'text', '', None), #AU
				('kode_cara_angkut', 1, 0, 'text', '', None),
				('kode_cara_bayar', 1, 0, 'text', '', None), #AW
				('kode_daerah_asal', 1, 0, 'text', '', None), #AX
				('kode_fasilitas', 1, 0, 'text', '', None), #AY
				('kode_ftz', 1, 0, 'text', '', None), #AZ
				('kode_harga', 1, 0, 'text', '', None), #BA
				('kode_id_pemasok', 1, 0, 'text', '', None), #BB
				('kode_id_pemilik', 1, 0, 'text', '', None), #BC
				('kode_id_penerima_barang', 1, 0, 'text', '', None), #BD
				('kode_id_pengirim', 1, 0, 'number', 1, None),
				('kode_id_pengusaha', 1, 0, 'number', 1, None),
				('kode_id_ppjk', 1, 0, 'text', '', None), #BG
				('kode_jenis_api', 1, 0, 'text', '', None), #BH
				('kode_jenis_api_pemilik', 1, 0, 'text', '', None), #BI
				('kode_jenis_api_penerima', 1, 0, 'text', '', None), #BJ
				('kode_jenis_api_pengusaha', 1, 0, 'text', '', None), #BK
				('kode_jenis_barang', 1, 0, 'text', '', None), #BL
				('kode_jenis_bc25', 1, 0, 'text', '', None), #BM
				('kode_jenis_nilai', 1, 0, 'text', '', None), #BN
				('kode_jenis_pemasukan01', 1, 0, 'text', '', None), #BO
				('kode_jenis_pemasukan02', 1, 0, 'text', '', None), #BP
				('kode_jenis_tpb', 1, 0, 'text', "1", None),
				('kode_kantor_bongkar', 1, 0, 'text', '', None), #BR
				('kode_kantor_tujuan', 1, 0, 'text', '', None), #BS
				('kode_loakasi_bayar', 1, 0, 'text', '', None), #BT
				('empty_column01', 1, 0, 'text', _(''), None), #BU
				('kode_negara_pemasok', 1, 0, 'text', '', None), #BV
				('kode_negara_pengirim', 1, 0, 'text', '', None), #BW
				('kode_negara_pemilik', 1, 0, 'text', '', None), #BX
				('kode_negara_tujuan', 1, 0, 'text', '', None), #BY
				('kode_pel_bongkar', 1, 0, 'text', '', None), #BZ
				('kode_pel_muat', 1, 0, 'text', '', None), #CA
				('kode_pel_transit', 1, 0, 'text', '', None), #CB
				('kode_pembayar', 1, 0, 'text', '', None), #CC
				('kode_status_pengusaha', 1, 0, 'text', '', None), #CD
				('status_perbaikan', 1, 0, 'text', '', None), #CE
				('kode_tps', 1, 0, 'text', '', None), #CF
				('kode_tujuan_pemasukan', 1, 0, 'text', '', None), #CG
				('kode_tujuan_pengiriman', 1, 0, 'text', "5", None), # Lainnya
				('kode_tujuan_tpb', 1, 0, 'text', '', None), #CI
				('kode_tutup_pu', 1, 0, 'text', '', None), #CJ
				('kode_valuta', 1, 0, 'text', '', None), #CK
				('kota_ttd', 1, 0, 'text', obj.place or '', None),
				('nama_pemilik', 1, 0, 'text', '', None), #CM
				('nama_penerima_barang', 1, 0, 'text', obj.document_type=='27_in' and obj.source_partner_id.name or (obj.document_type=='27_out' and obj.dest_partner_id.name or ''), None), #CN
				('nama_pengangkut', 1, 0, 'text', obj.sarana_pengangkutan or '', None), #CO
				('nama_pengirim', 1, 0, 'text', obj.document_type=='40' and obj.source_partner_id.name or '', None),
				('nama_ppjk', 1, 0, 'text', '', None), #CQ
				('nama_ttd', 1, 0, 'text', obj.signedby and obj.signedby.name or '', None),
				('ndpbm', 1, 0, 'text', '', None), #CS
				('netto', 1, 0, 'number', obj.nett_weight or 0.0, None),
				('nilai_incoterm', 1, 0, 'text', '', None), #CU
				('niper_penerima', 1, 0, 'text', '', None), #CV
				('nomor_api', 1, 0, 'text', '', None), #CW
				('nomor_bc11', 1, 0, 'text', '', None), #CX
				('nomor_billing', 1, 0, 'text', '', None), #CY
				('nomor_daftar', 1, 0, 'text', '', None), #CZ
				('nomor_ijin_bpk_pemasok', 1, 0, 'text', '', None), #DA
				('nomor_ijin_bpk_pengusaha', 1, 0, 'text', '', None), #DB
				('nomor_ijin_tpb', 1, 0, 'text', obj.tpb_certificate or '', None),
				('nomor_ijin_tpb_penerima', 1, 0, 'text', '', None), #DD
				('nomor_voyv_flight', 1, 0, 'text', '', None), #DE
				('npwp_billing', 1, 0, 'text', '', None), #DF
				('pos_bc11', 1, 0, 'text', '', None), #DG
				('seri', 1, 0, 'number', n, None), #DH
				('subpos_bc11', 1, 0, 'text', '', None), #DI
				('sub_subpos_bc11', 1, 0, 'text', '', None), #DJ
				('tanggal_bc11', 1, 0, 'text', '', None), #DK
				('tanggal_berangkat', 1, 0, 'text', '', None), #DL
				('tanggal_billing', 1, 0, 'text', '', None), #DM
				('tanggal_daftar', 1, 0, 'text', '', None), #DN
				('tanggal_ijin_bpk_pemasok', 1, 0, 'text', '', None), #DO
				('tanggal_ijin_bpk_pengusaha', 1, 0, 'text', '', None), #DP
				('tanggal_ijin_tpb', 1, 0, 'text', '', None), #DQ
				('tanggal_npppjk', 1, 0, 'text', '', None), #DR
				('tanggal_tiba', 1, 0, 'text', '', None), #DS
				('tanggal_ttd', 1, 0, 'text', obj.date!='False' and datetime.strptime(obj.date,'%Y-%m-%d').strftime('%d-%m-%Y') or datetime.strptime(obj.registration_date,'%Y-%m-%d').strftime('%d-%m-%Y'), None),
				('tanggal_jatuh_tempo', 1, 0, 'text', '', None), #DU
				('total_bayar', 1, 0, 'text', '', None), #DV
				('total_bebas', 1, 0, 'text', '', None), #DW
				('total_dilunasi', 1, 0, 'text', '', None), #DX
				('total_jamin', 1, 0, 'text', '', None), #DY
				('total_sudah_dilunasi', 1, 0, 'text', '', None), #DZ
				('total_tangguh', 1, 0, 'text', '', None), #EA
				('total_tanggung', 1, 0, 'text', '', None), #EB
				('total_tidak_dipungut', 1, 0, 'text', '', None), #EC
				('url_dokumen_pabean', 1, 0, 'text', '', None), #ED
				('versi_modul', 1, 0, 'text', '3.1.6', None), #EE
				('volume', 1, 0, 'number', obj.volume or 0.0, None),
				('waktu_bongkar', 1, 0, 'text', '', None), #EG
				('waktu_stuffing', 1, 0, 'text', '', None), #EH
				('nomor_polisi', 1, 0, 'text', obj.voyage_no or '', None),
			]
			row_data = self.xls_row_template(
				c_specs, [x[0] for x in c_specs])
			row_pos = self.xls_write_row(
				ws, row_pos, row_data, ll_cell_style)

		# Sheet Bahan Baku
		ws = wb.add_sheet("Bahan Baku")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('seri_bahan_baku', 1, 0, 'text', _('SERI BAHAN BAKU'), None), #C
			('cif', 1, 0, 'text', _('CIF'), None), #D
			('cif_rupiah', 1, 0, 'text', _('CIF RUPIAH'), None), #E
			('harga_penyerahan', 1, 0, 'text', _('HARGA_PENYERAHAN'), None), #F
			('harga_perolehan', 1, 0, 'text', _('HARGA PEROLEHAN'), None), #G
			('jenis_satuan', 1, 0, 'text', _('JENIS_SATUAN'), None), #H
			('jumlah_satuan', 1, 0, 'text', _('JUMLAH SATUAN'), None), #I
			('kode_asal_bahan_baku', 1, 0, 'text', _('KODE ASAL BAHAN BAKU'), None), #J
			('kode_barang', 1, 0, 'text', _('KODE BARANG'), None), #K
			('kode_fasilitas', 1, 0, 'text', _('KODE FASILITAS'), None), #L
			('kode_jenis_doc_asal', 1, 0, 'text', _('KOZDE JENIS DOK ASAL'), None), #M
			('kode_kantor', 1, 0, 'text', _('KODE KANTOR'), None), #N
			('kode_skema_tarif', 1, 0, 'text', _('KODE SKEMA TARIF'), None), #O
			('kode_status', 1, 0, 'text', _('STATUS'), None), #P
			('merk', 1, 0, 'text', _('MERK'), None), #Q
			('ndpbm', 1, 0, 'text', _('NDPBM'), None), #R
			('netto', 1, 0, 'text', _('NETTO'), None), #S
			('nomor_aju_dok_asal', 1, 0, 'text', _('NOMOR AJU DOKUMEN ASAL'), None), #T
			('nomor_daftar_dok_asal', 1, 0, 'text', _('NOMOR DAFTAR DOKUMEN ASAL'), None), #U
			('pos_tarif', 1, 0, 'text', _('POS TARIF'), None), #V
			('seri_barang_dok_asal', 1, 0, 'text', _('SERI BARANG DOKUMEN ASAL'), None), #W
			('spesifikasi_Lain', 1, 0, 'text', _('SPESIFIKASI LAIN'), None), #X
			('tanggal_daftar_dokumen_asal', 1, 0, 'text', _('TANGGAL DAFTAR DOKUMEN ASAL'), None), #Y
			('tipe', 1, 0, 'text', _('TIPE'), None), ##Z
			('ukuran', 1, 0, 'text', _('UKURAN'), None), #AA
			('uraian', 1, 0, 'text', _('URAIAN'), None), #AB
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		for obj in objects:
			n = 0
			for line in obj.konversi_ids:
				n+=1
				continue
				c_specs = [
					('nomor_aju', 1, 0, 'text', '', None), #A
					('seri_barang', 1, 0, 'number', n, None), #B
					('seri_bahan_baku', 1, 0, 'number', n, None), #C
					('cif', 1, 0, 'number', 0.0, None), #D
					('cif_rupiah', 1, 0, 'number', 0.0, None), #E
					('harga_penyerahan', 1, 0, 'number', 0.0, None), #F
					('harga_perolehan', 1, 0, 'number', 0.0, None), #G
					('jenis_satuan', 1, 0, 'text', '', None), #H
					('jumlah_satuan', 1, 0, 'number', 0.0, None), #I
					('kode_asal_bahan_baku', 1, 0, 'text', '0', None), #J
					('kode_barang', 1, 0, 'text', '', None), #K
					('kode_fasilitas', 1, 0, 'text', '', None), #L
					('kode_jenis_doc_asal', 1, 0, 'text', '', None), #M
					('kode_kantor', 1, 0, 'text', '', None), #N
					('kode_skema_tarif', 1, 0, 'text', '', None), #O
					('kode_status', 1, 0, 'text', '02', None), #P
					('merk', 1, 0, 'text', '', None), #Q
					('ndpbm', 1, 0, 'text', '', None), #R
					('netto', 1, 0, 'number', 0.0, None), #S
					('nomor_aju_dok_asal', 1, 0, 'text', '', None), #T
					('nomor_daftar_dok_asal', 1, 0, 'text', '', None), #U
					('pos_tarif', 1, 0, 'number', 0.0, None), #V
					('seri_barang_dok_asal', 1, 0, 'number', n, None), #W
					('spesifikasi_Lain', 1, 0, 'text', '', None), #X
					('tanggal_daftar_dokumen_asal', 1, 0, 'text', '', None), #Y
					('tipe', 1, 0, 'text', '', None), ##Z
					('ukuran', 1, 0, 'text', '', None), #AA
					('uraian', 1, 0, 'text', '', None), #AB
					]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)

		# Sheet Bahan Baku Tarif
		ws = wb.add_sheet("Bahan Baku Tarif")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('seri_bahan_baku', 1, 0, 'text', _('SERI BAHAN BAKU'), None), #C
			('jenis_tarif', 1, 0, 'text', _('JENIS TARIF'), None), #D
			('jumlah_satuan', 1, 0, 'text', _('JUMLAH SATUAN'), None), #E
			('kode_asal_bahan_baku', 1, 0, 'text', _('KODE ASAL BAHAN BAKU'), None), #F
			('kode_fasilitas', 1, 0, 'text', _('KODE FASILITAS'), None), #G
			('kode_komoditi_cukai', 1, 0, 'text', _('KODE KOMODITI CUKAI'), None), #H
			('kode_satuan', 1, 0, 'text', _('KODE SATUAN'), None), #I
			('kode_tarif', 1, 0, 'text', _('KODE TARIF'), None), #J
			('nilai_bayar', 1, 0, 'text', _('NILAI BAYAR'), None), #K
			('nilai_fasilitas', 1, 0, 'text', _('NILAI FASILITAS'), None), #L
			('nilai_sudah_lunas', 1, 0, 'text', _('NILAI SUDAH DILUNASI'), None), #M
			('tarif', 1, 0, 'text', _('TARIF'), None), #N
			('tarif_fasilitas', 1, 0, 'text', _('TARIF FASILITAS'), None), #O
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# Sheet BahanBakuDokumen
		ws = wb.add_sheet("BahanBakuDokumen")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('seri_bahan_baku', 1, 0, 'text', _('SERI BAHAN BAKU'), None), #C
			('seri_dokumen', 1, 0, 'text', _('SERI DOKUMEN'), None), #D
			('kode_asal_bahan_baku', 1, 0, 'text', _('KODE ASAL BAHAN BAKU'), None), #E
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# Sheet Barang
		ws = wb.add_sheet("Barang")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('asuransi', 1, 0, 'text', _('ASURANSI'), None), #C
			('cif', 1, 0, 'text', _('CIF'), None), #D
			('cif_rupiah', 1, 0, 'text', _('CIF RUPIAH'), None), #E
			('diskon', 1, 0, 'text', _('DISKON'), None), #F
			('flag_kendaraan', 1, 0, 'text', _('FLAG KENDARAAN'), None), #G
			('fob', 1, 0, 'text', _('FOB'), None), #H
			('freight', 1, 0, 'text', _('FREIGHT'), None), #I
			('barang_ldp', 1, 0, 'text', _('BARANG BARANG LDP'), None), #J
			('harga_invoice', 1, 0, 'text', _('HARGA INVOICE'), None), #K
			('harga_Penyerahan', 1, 0, 'text', _('HARGA PENYERAHAN'), None), #L
			('harga_satuan', 1, 0, 'text', _('HARGA SATUAN'), None), #M
			('jenis_kendaraan', 1, 0, 'text', _('JENIS KENDARAAN'), None), #N
			('jumlah_bahan_baku', 1, 0, 'text', _('JUMLAH BAHAN BAKU'), None), #O
			('jumlah_kemasan', 1, 0, 'text', _('JUMLAH KEMASAN'), None), #P
			('jumlah_satuan', 1, 0, 'text', _('JUMLAH SATUAN'), None), #Q
			('kapasitas_silinder', 1, 0, 'text', _('KAPASITAS SILINDER'), None), #R
			('kategori_barang', 1, 0, 'text', _('KATEGORI BARANG'), None), #S
			('kode_asal_barang', 1, 0, 'text', _('KODE_ASAL BARANG'), None), #T
			('kode_barang', 1, 0, 'text', _('KODE BARANG'), None), #U
			('kode_fasilitas', 1, 0, 'text', _('KODE FASILITAS'), None), #V
			('kode_guna', 1, 0, 'text', _('KODE GUNA'), None), #W
			('kode_jenis_nilai', 1, 0, 'text', _('KODE JENIS NILAI'), None), #X
			('kode_kemasan', 1, 0, 'text', _('KODE KEMASAN'), None), #Y
			('kode_lain', 1, 0, 'text', _('KODE LEBIH DARI 4 TAHUN'), None), #Z
			('kode_asal_negara', 1, 0, 'text', _('KODE NEGARA ASAL'), None), #AA
			('kode_satuan', 1, 0, 'text', _('KODE SATUAN'), None), #AB
			('kode_skema_tarif', 1, 0, 'text', _('KODE SKEMA TARIF'), None), #AC
			('kode_status_tarif', 1, 0, 'text', _('KODE STATUS'), None), #AD
			('kondisi_barang', 1, 0, 'text', _('KONDISI BARANG'), None), #AE
			('Merk', 1, 0, 'text', _('MERK'), None), #AF
			('netto', 1, 0, 'text', _('NETTO'), None), #AG
			('nilai_incoterm', 1, 0, 'text', _('NILAI INCOTERM'), None), #AH
			('nilai_pabean', 1, 0, 'text', _('NILAI PABEAN'), None), #AI
			('nomor_mesin', 1, 0, 'text', _('NOMOR MESIN'), None), #AJ
			('pos_tarif', 1, 0, 'text', _('POS TARIF'), None), #AK
			('seri_pos_tarif', 1, 0, 'text', _('SERI POS TARIF'), None), #AL
			('spesifikasi_lain', 1, 0, 'text', _('SPESIFIKASI LAIN'), None), #AM
			('tahun_pembuatan', 1, 0, 'text', _('TAHUN PEMBUATAN'), None), #AN
			('tipe', 1, 0, 'text', _('TIPE'), None), #AO
			('ukuran', 1, 0, 'text', _('UKURAN'), None), #AP
			('uraian', 1, 0, 'text', _('URAIAN'), None), #AQ
			('volume', 1, 0, 'text', _('VOLUME'), None), #AR
			('seri_ijin', 1, 0, 'text', _('SERI IJIN'), None), #AS
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		for obj in objects:
			n = 0
			for line in obj.detail_packing_id:
				n+=1
				c_specs = [
					('nomor_aju', 1, 0, 'text', obj.name or '', None),
					('seri_barang', 1, 0, 'number', n, None),
					('asuransi', 1, 0, 'number', 0, None), #C
					('cif', 1, 0, 'number', 0, None), #D
					('cif_rupiah', 1, 0, 'number', 0, None), #E
					('diskon', 1, 0, 'text', '', None), #F
					('flag_kendaraan', 1, 0, 'number', 0, None), #G
					('fob', 1, 0, 'number', 0, None), #H
					('freight', 1, 0, 'number', 0, None), #I
					('barang_ldp', 1, 0, 'text', '', None), #J
					('harga_invoice', 1, 0, 'number', 0, None), #K
					('harga_penyerahan', 1, 0, 'number', line.price_subtotal_idr or 0.0, None),
					('harga_satuan', 1, 0, 'number', 0, None), #M
					('jenis_kendaraan', 1, 0, 'text', '', None), #N
					('jumlah_bahan_baku', 1, 0, 'number', 0, None),
					('jumlah_kemasan', 1, 0, 'number', 0, None), #P
					('jumlah_satuan', 1, 0, 'number', line.product_qty_kgs or 0.0, None),
					('kapasitas_silinder', 1, 0, 'number', 0, None), #R
					('kategori_barang', 1, 0, 'text', '', None), #S
					('kode_asal_barang', 1, 0, 'text', '', None), #T
					('kode_barang', 1, 0, 'text', line.product_id.default_code or '', None),
					('kode_fasilitas', 1, 0, 'text', '', None), #V
					('kode_guna', 1, 0, 'text', '', None), #W
					('kode_jenis_nilai', 1, 0, 'text', '', None), #X
					('kode_kemasan', 1, 0, 'text', '', None), #Y
					('kode_lain', 1, 0, 'text', '', None), #Z
					('kode_asal_negara', 1, 0, 'text', '', None), #AA
					('kode_satuan', 1, 0, 'text', line.product_uom_kgs.ceisa_tpb_uom_alias or line.product_uom_kgs.name or '', None),
					('kode_skema_tarif', 1, 0, 'text', '', None), #AC
					('kode_status_tarif', 1, 0, 'text', '', None), #AD
					('kondisi_barang', 1, 0, 'text', '', None), #AE
					('Merk', 1, 0, 'text', '', None),
					('netto', 1, 0, 'number', line.net_weight or 0.0, None),
					('nilai_incoterm', 1, 0, 'number', 0, None), #AH
					('nilai_pabean', 1, 0, 'number', 0, None), #AI
					('nomor_mesin', 1, 0, 'text', '', None), #AJ
					('pos_tarif', 1, 0, 'number', 0, None), #AK
					('seri_pos_tarif', 1, 0, 'text', '', None), #AL
					('spesifikasi_lain', 1, 0, 'text', '', None),
					('tahun_pembuatan', 1, 0, 'text', '', None), #AN
					('Tipe', 1, 0, 'text', '', None),
					('Ukuran', 1, 0, 'text', '', None),
					('uraian', 1, 0, 'text', line.product_id.name or '', None),
					('volume', 1, 0, 'number', line.volume or 0.0, None),
					('seri_ijin', 1, 0, 'text', '', None), #AS
					]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)

		# Sheet BarangTarif
		ws = wb.add_sheet("BarangTarif")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('jenis_tarif', 1, 0, 'text', _('JENIS TARIF'), None), #C
			('jumlah_satuan', 1, 0, 'text', _('JUMLAH SATUAN'), None), #D
			('kode_fasilitas', 1, 0, 'text', _('KODE FASILITAS'), None), #E
			('kode_komoditi_cukai', 1, 0, 'text', _('KODE KOMODITI CUKAI'), None), #F
			('tarif_kode_satuan', 1, 0, 'text', _('TARIF KODE SATUAN'), None), #G
			('tarif_kode_tarif', 1, 0, 'text', _('TARIF KODE TARIF'), None), #H
			('tarif_nilai_bayar', 1, 0, 'text', _('TARIF NILAI BAYAR'), None), #I
			('tarif_nilai_fasilitas', 1, 0, 'text', _('TARIF NILAI FASILITAS'), None), #J
			('tarif_nilai_sudah_lunas', 1, 0, 'text', _('TARIF NILAI SUDAH DILUNASI'), None), #K
			('tarif', 1, 0, 'text', _('TARIF'), None), #L
			('tarif_fasilitas', 1, 0, 'text', _('TARIF FASILITAS'), None), #M
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# Sheet BarangDokumen
		ws = wb.add_sheet("BarangDokumen")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None), #A
			('seri_barang', 1, 0, 'text', _('SERI BARANG'), None), #B
			('seri_dokumen', 1, 0, 'text', _('SERI DOKUMEN'), None), #C
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# Sheet Dokumen
		ws = wb.add_sheet("Dokumen")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None),
			('seri_dokumen', 1, 0, 'text', _('SERI DOKUMEN'), None),
			('flag_url_dokumen', 1, 0, 'text', _('FLAG URL DOKUMEN'), None),
			('kode_Jenis_Dokumen', 1, 0, 'text', _('KODE JENIS DOKUMEN'), None),
			('nomor_Dokumen', 1, 0, 'text', _('NOMOR DOKUMEN'), None),
			('tanggal_Dokumen', 1, 0, 'text', _('TANGGAL DOKUMEN'), None),
			('tipe_dokumen', 1, 0, 'text', _('TIPE DOKUMEN'), None),
			('url_dokumen', 1, 0, 'text', _('URL DOKUMEN'), None),
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		for obj in objects:
			n = 0
			for line in obj.beacukai_additional_doc:
				n+=1
				c_specs = [
					('nomor_aju', 1, 0, 'text', obj.name or '', None),
					('seri_dokumen', 1, 0, 'number', n, None),
					('flag_url_dokumen', 1, 0, 'text', '', None),
					('kode_Jenis_Dokumen', 1, 0, 'text', line.doc_id and line.doc_id.code or '', None),
					('nomor_Dokumen', 1, 0, 'text', line.no_doc or '', None),
					('tanggal_Dokumen', 1, 0, 'text', line.tanggal_doc!='False' and datetime.strptime(line.tanggal_doc,'%Y-%m-%d').strftime('%d-%m-%Y') or '', None),
					('tipe_dokumen', 1, 0, 'text', '', None),
					('url_dokumen', 1, 0, 'text', '', None),
					]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)

		# Sheet Kemasan
		ws = wb.add_sheet("Kemasan")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None),
			('seri_kemasan', 1, 0, 'text', _('SERI KEMASAN'), None),
			('jumlah_kemasan', 1, 0, 'text', _('JUMLAH KEMASAN'), None),
			('kesesuaian_dokumen', 1, 0, 'text', _('KESESUAIAN DOKUMEN'), None),
			('keterangan', 1, 0, 'text', _('KETERANGAN'), None),
			('kode_jenis_kemasan', 1, 0, 'text', _('KODE JENIS KEMASAN'), None),
			('merk_kemasan', 1, 0, 'text', _('MEREK KEMASAN'), None),
			('nip_gate_in', 1, 0, 'text', _('NIP GATE IN'), None),
			('nip_gate_out', 1, 0, 'text', _('NIP GATE OUT'), None),
			('nomor_polisi', 1, 0, 'text', _('NOMOR POLISI'), None),
			('nomor_segel', 1, 0, 'text', _('NOMOR SEGEL'), None),
			('waktu_gate_in', 1, 0, 'text', _('WAKTU GATE IN'), None),
			('waktu_gate_out', 1, 0, 'text', _('WAKTU GATE OUT'), None),
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		for obj in objects:
			n = 0
			for line in obj.beacukai_product_packages:
				n+=1
				c_specs = [
					('nomor_aju', 1, 0, 'text', obj.name or '', None),
					('seri_kemasan', 1, 0, 'number', n, None),
					('jumlah_kemasan', 1, 0, 'number', line.jumlah or 0.0, None),
					('kesesuaian_dokumen', 1, 0, 'text', '', None),
					('keterangan', 1, 0, 'text', '', None),
					('kode_jenis_kemasan', 1, 0, 'text', line.package_id.ceisa_tpb_uom_alias or line.package_id.name, None),
					('merk_kemasan', 1, 0, 'text', line.merk or '', None),
					('nip_gate_in', 1, 0, 'text', '', None),
					('nip_gate_out', 1, 0, 'text', '', None),
					('nomor_polisi', 1, 0, 'text', '', None),
					('nomor_segel', 1, 0, 'text', '', None),
					('waktu_gate_in', 1, 0, 'text', '', None),
					('waktu_gate_out', 1, 0, 'text', '', None),
					]
				row_data = self.xls_row_template(
					c_specs, [x[0] for x in c_specs])
				row_pos = self.xls_write_row(
					ws, row_pos, row_data, ll_cell_style)
		# Sheet KONTAINER
		ws = wb.add_sheet("Kontainer")
		ws.panes_frozen = False
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

		# Header Table
		c_specs = [
			('nomor_aju', 1, 0, 'text', _('NOMOR AJU'), None),
			('seri_kontainer', 1, 0, 'text', _('SERI KONTAINER'), None),
			('kesesuaian_dokumen', 1, 0, 'text', _('KESESUAIAN DOKUMEN'), None),
			('keterangan', 1, 0, 'text', _('KETERANGAN'), None),
			('kode_stuffing', 1, 0, 'text', _('KODE STUFFING'), None),
			('kode_tipe_kontainer', 1, 0, 'text', _('KODE TIPE KONTAINER'), None),
			('kode_ukuran_kontainer', 1, 0, 'text', _('KODE UKURAN KONTAINER'), None),
			('flag_gate_in', 1, 0, 'text', _('FLAG GATE IN'), None),
			('flag_gate_out', 1, 0, 'text', _('FLAG GATE OUT'), None),
			('nomor_polisi', 1, 0, 'text', _('NOMOR POLISI'), None),
			('nomor_kontainer', 1, 0, 'text', _('NOMOR KONTAINER'), None),
			('nomor_segel', 1, 0, 'text', _('NOMOR SEGEL'), None),
			('waktu_gate_in', 1, 0, 'text', _('WAKTU GATE IN'), None),
			('waktu_gate_out', 1, 0, 'text', _('WAKTU GATE OUT'), None),
			]
		row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
		row_pos = self.xls_write_row(ws, row_pos, row_data)

		# ws.set_horz_split_pos(row_pos)

		ll_cell_format = xls_style['top']
		ll_cell_style = xlwt.easyxf(ll_cell_format)
		ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_style['center'])
		ll_cell_style_date = xlwt.easyxf(
			ll_cell_format + xls_style['left'],
			num_format_str=report_xls.date_format)
		ll_cell_style_decimal = xlwt.easyxf(
			ll_cell_format + xls_style['right'],
			num_format_str=report_xls.decimal_format)
		# for obj in objects:
		# 	n = 0
		# 	for line in obj.beacukai_product_packages:
		# 		n+=1
		# 		c_specs = [
		# 			('nomor_aju', 1, 0, 'text', obj.name or '', None),
		# 			('seri_kontainer', 1, 0, 'number', n, None),
		# 			('kesesuaian_dokumen', 1, 0, 'text', '', None),
		# 			('keterangan', 1, 0, 'text', '', None),
		# 			('kode_stuffing', 1, 0, 'text', '', None),
		# 			('kode_tipe_kontainer', 1, 0, 'text', '', None),
		# 			('kode_ukuran_kontainer', 1, 0, 'text', '', None),
		# 			('flag_gate_in', 1, 0, 'text', '', None),
		# 			('flag_gate_out', 1, 0, 'text', '', None),
		# 			('nomor_polisi', 1, 0, 'text', '', None),
		# 			('nomor_kontainer', 1, 0, 'text', '', None),
		# 			('nomor_segel', 1, 0, 'text', '', None),
		# 			('waktu_gate_in', 1, 0, 'text', '', None),
		# 			('waktu_gate_out', 1, 0, 'text', '', None),
		# 			]
		# 		row_data = self.xls_row_template(
		# 			c_specs, [x[0] for x in c_specs])
		# 		row_pos = self.xls_write_row(
		# 			ws, row_pos, row_data, ll_cell_style)
beacukai_doc_report_xls('report.beacukai.ceisa.tmpl.test','beacukai', parser=export_ceisa_template_parser, header=False)
