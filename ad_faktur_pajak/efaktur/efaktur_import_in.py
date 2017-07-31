import time
import datetime
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from report_engine_xls import report_xls
from ad_faktur_pajak.efaktur.efaktur_parser import EFakturParser

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class efaktur_import_in(report_xls):
	no_ind = 0
	def get_no_index(self):
		self.set_no_index()
		return self.no_ind
	def set_no_index(self):
		self.no_ind += 1
		return True

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
		c = parser.localcontext['company']
		##Penempatan untuk template rows
		title_style 					= xlwt.easyxf('font: height 220, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='###0.00;-###0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='###0.00;-###0.00')
		normal_style_no_format 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;')
		normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='###0.00;-###0.00')
		normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom dotted;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='###0;-###0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='###0.00;-###0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='###0.0000;(###0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='###0.00;(###0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')

		ws = wb.add_sheet('Tax - %s'%data['type'],cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 65
		ws.normal_magn = 65
		ws.print_scaling=65
		ws.page_preview = False
		ws.set_fit_width_to_pages(1)

		rowcount = 0
		ws.write(rowcount,0,"FM",normal_style)
		ws.write(rowcount,1,"KD_JENIS_TRANSAKSI",normal_style)
		ws.write(rowcount,2,"FG_PENGGANTI",normal_style)
		ws.write(rowcount,3,"NOMOR_FAKTUR",normal_style)
		ws.write(rowcount,4,"MASA_PAJAK",normal_style)
		ws.write(rowcount,5,"TAHUN_PAJAK",normal_style)
		ws.write(rowcount,6,"TANGGAL_FAKTUR",normal_style)
		ws.write(rowcount,7,"NPWP",normal_style)
		ws.write(rowcount,8,"NAMA",normal_style)
		ws.write(rowcount,9,"ALAMAT_LENGKAP",normal_style)
		ws.write(rowcount,10,"JUMLAH_DPP",normal_style)
		ws.write(rowcount,11,"JUMLAH_PPN",normal_style)
		ws.write(rowcount,12,"JUMLAH_PPNBM",normal_style)
		ws.write(rowcount,13,"IS_CREDITABLE",normal_style)
		rowcount+=1
		force_period = data["use_force_period"] and data["force_period"] or False
		masa_pajak = False
		if force_period:
			period=parser.get_period(force_period)
			masa_pajak = datetime.datetime.strptime(period.date_start,"%Y-%m-%d").strftime("%-m")

		for inv in parser._get_invoice_in(data):
			td_string = inv.tanggalFaktur and datetime.datetime.strptime(inv.tanggalFaktur,"%Y-%m-%d").strftime("%-m") or False
			ty_string = inv.tanggalFaktur and datetime.datetime.strptime(inv.tanggalFaktur,"%Y-%m-%d").strftime("%Y") or False
			td_complete = inv.tanggalFaktur and datetime.datetime.strptime(inv.tanggalFaktur,"%Y-%m-%d").strftime("%d/%m/%Y") or False
			tax_date = td_string and int(td_string) or ""
			tax_year = ty_string and int(ty_string) or ""
			
			ws.write(rowcount,0,"FM",normal_style)
			ws.write(rowcount,1,str(inv.kode_jenis_transaksi and inv.kode_jenis_transaksi[0:2]) or "",normal_style)
			ws.write(rowcount,2,inv.fgPengganti and inv.fgPengganti[0:1] or "",normal_style)
			ws.write(rowcount,3,inv.nomorFaktur,normal_style)
			ws.write(rowcount,4,masa_pajak or tax_date ,normal_style_no_format)
			ws.write(rowcount,5,tax_year,normal_style_no_format)
			ws.write(rowcount,6,td_complete,normal_style)
			ws.write(rowcount,7,inv.npwpPenjual.replace(".","").replace("-","") or "000000000000000",normal_style)
			ws.write(rowcount,8,inv.namaPenjual,normal_style)
			ws.write(rowcount,9,inv.alamatPenjual[:255],normal_style)
			ws.write(rowcount,10,inv.jumlahDpp,normal_style_no_format)
			ws.write(rowcount,11,inv.jumlahPpn,normal_style_no_format)
			ws.write(rowcount,12,inv.jumlahPpnBm,normal_style_no_format)
			ws.write(rowcount,13,inv.kdJenisTransaksi and inv.kdJenisTransaksi[0:2]=='01' and 1 or 0,normal_style_no_format)
			rowcount+=1			
		pass
#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
efaktur_import_in('report.efaktur.wizard.import.in','stock.report.bitratex.wizard', 'addons/ad_faktur_pajak/efaktur/efaktur.mako',
						parser=EFakturParser)