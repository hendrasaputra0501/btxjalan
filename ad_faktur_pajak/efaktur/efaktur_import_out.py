import time
import datetime
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from report_engine_xls import report_xls
from ad_faktur_pajak.efaktur.efaktur_parser import EFakturParser

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class efaktur_import_out(report_xls):
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
		normal_style_4dp				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='###0.0000;-###0.0000')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='###0.00;-###0.00')
		normal_style_no_format 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;')
		normal_style_date_format 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='dd/mm/yyyy')
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
		# print "==================",data.get('type'),data.get('sale_type')
		if data.get('type','out')=='out' and data.get('sale_type','local')=='local':

			ws.write(rowcount,0,"FK",normal_style)
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
			ws.write(rowcount,13,"ID_KETERANGAN_TAMBAHAN",normal_style)
			ws.write(rowcount,14,"FG_UANG_MUKA",normal_style)
			ws.write(rowcount,15,"UANG_MUKA_DPP",normal_style)
			ws.write(rowcount,16,"UANG_MUKA_PPN",normal_style)
			ws.write(rowcount,17,"UANG_MUKA_PPNBM",normal_style)
			ws.write(rowcount,18,"REFERENSI",normal_style)
			rowcount+=1
			ws.write(rowcount,0,"LT",normal_style)
			ws.write(rowcount,1,"NPWP",normal_style)
			ws.write(rowcount,2,"NAMA",normal_style)
			ws.write(rowcount,3,"JALAN",normal_style)
			ws.write(rowcount,4,"BLOK",normal_style)
			ws.write(rowcount,5,"NOMOR",normal_style)
			ws.write(rowcount,6,"RT",normal_style)
			ws.write(rowcount,7,"RW",normal_style)
			ws.write(rowcount,8,"KECAMATAN",normal_style)
			ws.write(rowcount,9,"KELURAHAN",normal_style)
			ws.write(rowcount,10,"KABUPATEN",normal_style)
			ws.write(rowcount,11,"PROPINSI",normal_style)
			ws.write(rowcount,12,"KODE_POS",normal_style)
			ws.write(rowcount,13,"NOMOR_TELEPON",normal_style)
			rowcount+=1
			ws.write(rowcount,0,"OF",normal_style)
			ws.write(rowcount,1,"KODE_OBJEK",normal_style)
			ws.write(rowcount,2,"NAMA",normal_style)
			ws.write(rowcount,3,"HARGA_SATUAN",normal_style)
			ws.write(rowcount,4,"JUMLAH_BARANG",normal_style)
			ws.write(rowcount,5,"HARGA_TOTAL",normal_style)
			ws.write(rowcount,6,"DISKON",normal_style)
			ws.write(rowcount,7,"DPP",normal_style)
			ws.write(rowcount,8,"PPN",normal_style)
			ws.write(rowcount,9,"TARIF_PPNBM",normal_style)
			ws.write(rowcount,10,"PPNBM",normal_style)
			rowcount+=1
			
			for inv in parser._get_invoice(data):
				td_string = inv.tax_date and datetime.datetime.strptime(inv.tax_date,"%Y-%m-%d").strftime("%-m") or datetime.datetime.strptime(inv.date_invoice,"%Y-%m-%d").strftime("%-m") or False
				ty_string = inv.tax_date and datetime.datetime.strptime(inv.tax_date,"%Y-%m-%d").strftime("%Y") or datetime.datetime.strptime(inv.date_invoice,"%Y-%m-%d").strftime("%Y") or False
				td_complete = inv.tax_date and datetime.datetime.strptime(inv.tax_date,"%Y-%m-%d").strftime("%d/%m/%Y") or datetime.datetime.strptime(inv.date_invoice,"%Y-%m-%d").strftime("%d/%m/%Y") or False
				tax_date = td_string and int(td_string) or ""
				tax_year = ty_string and int(ty_string) or ""
				partner_addr = (inv.partner_id and inv.partner_id.street or "") + " " + (inv.partner_id and inv.partner_id.street2 or "") + " " + (inv.partner_id and inv.partner_id.street3 or "")
				total_dpp0=parser.get_dpp_total(inv)
				total_ppn0=parser.get_ppn(inv)
				
				ws.write(rowcount,0,"FK",normal_style)
				ws.write(rowcount,1,inv.kode_transaksi_faktur_pajak and inv.kode_transaksi_faktur_pajak[0:2] or "",normal_style)
				ws.write(rowcount,2,(inv.fp_harga_jual and "0") or (inv.fp_penggantian and "1") or "0",normal_style)
				ws.write(rowcount,3,"%s%s%s"%(inv.nomor_faktur_id.nomor_perusahaan,inv.nomor_faktur_id.tahun_penerbit,inv.nomor_faktur_id.nomor_urut),normal_style)
				ws.write(rowcount,4,tax_date ,normal_style_no_format)
				ws.write(rowcount,5,tax_year,normal_style_no_format)
				ws.write(rowcount,6,td_complete,normal_style)
				ws.write(rowcount,7,inv.partner_id.npwp and inv.partner_id.npwp.replace(".","").replace("-","") or "000000000000000",normal_style)
				ws.write(rowcount,8,inv.partner_id.name,normal_style)
				ws.write(rowcount,9,partner_addr[:255],normal_style)
				ws.write(rowcount,10,total_dpp0,normal_style_no_format)
				ws.write(rowcount,11,total_ppn0,normal_style_no_format)
				ws.write(rowcount,12,parser.get_ppnbm(inv),normal_style_no_format)
				ws.write(rowcount,13,2,normal_style_no_format)
				ws.write(rowcount,14,0,normal_style_no_format)
				ws.write(rowcount,15,0,normal_style_no_format)
				ws.write(rowcount,16,0,normal_style_no_format)
				ws.write(rowcount,17,0,normal_style_no_format)
				ws.write(rowcount,18,parser.get_reference(inv),normal_style_no_format)
				lt_npwp = inv.partner_id.npwp and inv.partner_id.npwp.replace(".","").replace("-","") or "000000000000000" 
				if lt_npwp != "000000000000000":
					rowcount+=1
					ws.write(rowcount,0,"LT",normal_style)
					ws.write(rowcount,1,inv.partner_id.npwp and inv.partner_id.npwp.replace(".","").replace("-","") or "000000000000000",normal_style)
					ws.write(rowcount,2,inv.partner_id.name,normal_style)
					ws.write(rowcount,3,partner_addr,normal_style)
					ws.write(rowcount,4,"-",normal_style)
					ws.write(rowcount,5,"-",normal_style)
					ws.write(rowcount,6,"-",normal_style)
					ws.write(rowcount,7,"-",normal_style)
					ws.write(rowcount,8,"-",normal_style)
					ws.write(rowcount,9,"-",normal_style)
					ws.write(rowcount,10,"-",normal_style)
					ws.write(rowcount,11,"-",normal_style)
					ws.write(rowcount,12,"-",normal_style)
					ws.write(rowcount,13,inv.partner_id.phone,normal_style)
				rowcount+=1
				total_line=0
				for line in inv.invoice_line:
					total_line+=1
				nline=0
				total_dpp=0
				total_ppn=0
				for line in inv.invoice_line:
					nline+=1
					if nline<total_line:
						line_dpp=int(parser.get_dpp_line(line))
						line_ppn=int(round(parser.get_ppn_line(line),0))
					else:
						line_dpp=total_dpp0-total_dpp
						line_ppn=total_ppn0-total_ppn
					total_dpp += line_dpp
					total_ppn += line_ppn
					ws.write(rowcount,0,"OF",normal_style_no_format)
					ws.write(rowcount,1,line.product_id.default_code,normal_style)
					ws.write(rowcount,2,line.name,normal_style)
					ws.write(rowcount,3,parser.get_price(line),normal_style_no_format)
					ws.write(rowcount,4,line.quantity,normal_style_4dp)
					ws.write(rowcount,5,line_dpp,normal_style_no_format)
					ws.write(rowcount,6,0,normal_style_no_format)
					ws.write(rowcount,7,line_dpp,normal_style_no_format)
					ws.write(rowcount,8,line_ppn,normal_style_no_format)
					ws.write(rowcount,9,0,normal_style_no_format)
					ws.write(rowcount,10,0,normal_style_no_format)
					rowcount+=1
		elif data.get('type','out')=='out' and data.get('sale_type','local')=='export':
			
			ws.write(rowcount,0,"DK",normal_style)
			ws.write(rowcount,1,"JENIS_TRANSAKSI",normal_style)
			ws.write(rowcount,2,"JENIS_DOKUMEN",normal_style)
			ws.write(rowcount,3,"KD_JNS_TRANSAKSI",normal_style)
			ws.write(rowcount,4,"FG_PENGGANTI",normal_style)
			ws.write(rowcount,5,"NOMOR_DOK_LAIN_GANTI",normal_style)
			ws.write(rowcount,6,"NOMOR_DOK_LAIN",normal_style)
			ws.write(rowcount,7,"TANGGAL_DOK_LAIN",normal_style)
			ws.write(rowcount,8,"MASA_PAJAK",normal_style)
			ws.write(rowcount,9,"TAHUN_PAJAK",normal_style)
			ws.write(rowcount,10,"NPWP",normal_style)
			ws.write(rowcount,11,"NAMA",normal_style)
			ws.write(rowcount,12,"ALAMAT_LENGKAP",normal_style)
			ws.write(rowcount,13,"JUMLAH_DPP",normal_style)
			ws.write(rowcount,14,"JUMLAH_PPN",normal_style)
			ws.write(rowcount,15,"JUMLAH_PPNBM",normal_style)
			ws.write(rowcount,16,"KETERANGAN",normal_style)
			rowcount+=1
			for inv in parser._get_invoice(data):
				pebd_string = inv.peb_date and datetime.datetime.strptime(inv.peb_date,"%Y-%m-%d").strftime("%-m") or ""
				pebd_datetime = inv.peb_date and datetime.datetime.strptime(inv.peb_date,"%Y-%m-%d")
				peby_string = inv.peb_date and datetime.datetime.strptime(inv.peb_date,"%Y-%m-%d").strftime("%Y") or ""
				peby_string2 = inv.peb_date and datetime.datetime.strptime(inv.peb_date,"%Y-%m-%d").strftime("%y") or ""
				pebd_complete = inv.peb_date and datetime.datetime.strptime(inv.peb_date,"%Y-%m-%d").strftime("%d/%m/%Y") or ""
				peb_date = pebd_string and int(pebd_string) or ""
				peb_year = peby_string and int(peby_string) or ""
				peb_year2 = peby_string2 and int(peby_string2) or ""
				partner_addr = (inv.partner_id and inv.partner_id.street or "") + " " + (inv.partner_id and inv.partner_id.street2 or "") + " " + (inv.partner_id and inv.partner_id.street3 or "")
				
				ws.write(rowcount,0,"DK",normal_style_no_format)
				ws.write(rowcount,1,"4",normal_style_no_format)
				ws.write(rowcount,2,"6",normal_style_no_format)
				ws.write(rowcount,3,"13",normal_style_no_format)
				ws.write(rowcount,4,"0",normal_style_no_format)
				ws.write(rowcount,5,"-",normal_style_no_format)
				ws.write(rowcount,6,inv.peb_number and "PEB%s%s"%(peb_year2,inv.peb_number) or "",normal_style_no_format)
				ws.write(rowcount,7,pebd_complete,normal_style_no_format)
				ws.write(rowcount,8,pebd_string,normal_style_date_format)
				ws.write(rowcount,9,peb_year,normal_style_no_format)
				ws.write(rowcount,10,"",normal_style_no_format)
				ws.write(rowcount,11,inv.partner_id.name,normal_style_no_format)
				ws.write(rowcount,12,partner_addr[:255],normal_style_no_format)
				ws.write(rowcount,13,parser.get_dpp_total(inv),normal_style_no_format)
				ws.write(rowcount,14,round(0.1*parser.get_dpp_total(inv),0),normal_style_no_format)
				ws.write(rowcount,15,0,normal_style_no_format)
				ws.write(rowcount,16,parser.get_reference(inv),normal_style_no_format)
				rowcount+=1
		pass
#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
efaktur_import_out('report.efaktur.wizard.import.out','stock.report.bitratex.wizard', 'addons/ad_faktur_pajak/efaktur/efaktur.mako',
						parser=EFakturParser)