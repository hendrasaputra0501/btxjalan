from openerp.osv import fields,osv
import urllib3
from lxml import etree
from tools.translate import _
import datetime
class efaktur_batch(osv.Model):
	_name="efaktur.batch"
	_rec_name="name"

	def _get_min_date(self,cr,uid,ids,field_name,arg,context=None):
		if not context:context={}
		res = {}
		for batch in self.browse(cr,uid,ids,context=context):
			xid = self.pool.get('efaktur.head').search(cr,uid,[("batch_id",'=',batch.id)],order="tanggalFaktur asc",limit=1)
			val = False
			if xid:
				xi = self.pool.get('efaktur.head').browse(cr,uid,xid,context=context)[0]
				val = xi.tanggalFaktur
			res.update({batch.id:val})
		return res

	def _get_max_date(self,cr,uid,ids,field_name,arg,context=None):
		if not context:context={}
		res = {}
		for batch in self.browse(cr,uid,ids,context=context):
			xid = self.pool.get('efaktur.head').search(cr,uid,[("batch_id",'=',batch.id)],order="tanggalFaktur desc",limit=1)
			val = False
			if xid:
				xi = self.pool.get('efaktur.head').browse(cr,uid,xid,context=context)[0]
				val = xi.tanggalFaktur
			res.update({batch.id:val})
		return res

	_columns = {
		"name"					: fields.char("Description"),
		"period_id"				: fields.many2one("account.period","Period for reporting"),
		"company_id"			: fields.many2one("res.company","Company"),
		"date_input"			: fields.date("Entry Date"),
		"qr_urls"				: fields.text("Efaktur URLs"),
		"date_min"				: fields.function(_get_min_date,type="date",string="Min.Date",store={
			'efaktur.batch' : (lambda self, cr,uid,ids,c: ids, ['qr_urls','batch_lines'], 10),
			}),
		"date_max"				: fields.function(_get_max_date,type="date",string="Max.Date",store={
			'efaktur.batch' : (lambda self, cr,uid,ids,c: ids, ['qr_urls','batch_lines'], 10),
			}),
		"batch_lines"			: fields.one2many("efaktur.head","batch_id","Batch Lines"),
	}
	_defaults = {
		"company_id": lambda self,cr,uid,context=None:self.pool.get("res.users").browse(cr,uid,uid).company_id.id,
		"date_input": lambda self,cr,uid,context:datetime.date.today().strftime("%Y-%m-%d")
	}
	def get_tax_data(self, cr, uid, ids, context=None):
		if not context:context={}
		ulib3 = urllib3.PoolManager()
		efaktur_head_pool = self.pool.get('efaktur.head')
		for batch in self.browse(cr, uid, ids, context=context):
			npwpcompany = batch.company_id.npwp.replace(".","").replace("-","")
			urls=batch.qr_urls
			urlspot=[]
			for url in urls.split("http://"):
				if url and url!='' and url not in ("\n","\t","\r"):
					href="http://"+url
					head_ids = efaktur_head_pool.search(cr, uid, [('url','=',href.strip())])
					if not head_ids:
						urlspot.append(href.strip())
					if head_ids:
						for efaktur in efaktur_head_pool.browse(cr, uid, head_ids):
							if efaktur.batch_id and efaktur.batch_id.id!=batch.id:
								raise osv.except_osv(_('Error Validation'), _("Factur no. %s is already reported with batch no. %s"%(efaktur.nomorFaktur, efaktur.batch_id.name)))
							else:
								efaktur_head_pool.write(cr, uid, efaktur.id, {'batch_id':batch.id})
			for link in list(set(urlspot)):
				try:
					res = ulib3.request('GET', link)
					if res.status==200 and res.data:
						tree = etree.fromstring(res.data)
						efaktur_head={}
						detailtrans = []
						for subtree1 in tree:
							# print "subtree1.tag===",subtree1.tag
							if subtree1.tag!='detailTransaksi':
								if subtree1.tag=="tanggalFaktur":
									dts=datetime.datetime.strptime(subtree1.text,"%d/%m/%Y").strftime('%Y-%m-%d')
									efaktur_head.update({subtree1.tag:dts})
								else:
									efaktur_head.update({subtree1.tag:subtree1.text})
							else:
								dumpy = {}
								for detail in subtree1.getchildren():
									dumpy.update({detail.tag:detail.text})
									if detail.tag=='ppnbm':
										detailtrans.append((0,0,dumpy))
										dumpy={}
						efaktur_head.update({
							'batch_id':batch.id,
							'company_id':batch.company_id.id,
							'url': link,
							'type': npwpcompany == efaktur_head.get('npwpPenjual',False) and 'out' or 'in',
							"efaktur_lines":detailtrans
							})
						self.pool.get('efaktur.head').create(cr,uid,efaktur_head,context=context)
						self.pool.get('efaktur.batch').write(cr,uid,batch.id,{'batch_lines':[]})
				except:
					raise osv.except_osv(_('Error Connecting to Server'), _("The connection to http://svc.efaktur.pajak.go.id/ can not be established."))
		return True

class efaktur_head(osv.Model):

	def _get_info_faktur(self,cr,uid,ids,field_names,args,context=None):
		if not context:context={}
		res = {}
		for head in self.browse(cr,uid,ids,context=context):
			val = {
				"kode_jenis_transaksi": head.kdJenisTransaksi,
				"fg_pengganti": head.fgPengganti,
				"nomor_faktur": head.nomorFaktur,
				"tanggal_faktur": head.tanggalFaktur,
				"npwp_penjual": head.npwpPenjual,
				"nama_penjual": head.namaPenjual,
				"alamat_penjual": head.alamatPenjual,
				"npwp_lawan_transaksi": head.npwpLawanTransaksi,
				"nama_lawan_transaksi": head.namaLawanTransaksi,
				"alamat_lawan_transaksi": head.alamatLawanTransaksi,
				"jumlah_dpp": head.jumlahDpp,
				"jumlah_ppn": head.jumlahPpn,
				"jumlah_ppnbm": head.jumlah_ppnbm,
				"status_approval": head.statusApproval,
				"status_faktur": head.statusFaktur,
				}
			res.update({head.id:val})
		return res

	_name="efaktur.head"
	_rec_name = "nomorFaktur"
	_columns ={
		"batch_id"				: fields.many2one("efaktur.batch","Batch ID"),
		"company_id"			: fields.many2one("res.company","Company"),
		"url"					: fields.text("URL"),
		"type"					: fields.selection([('in',"Masukan"),('out','Keluaran')],"Type Faktur"),
		"kdJenisTransaksi"		: fields.char("Kode Jenis Transaksi",size=128),
		"fgPengganti"			: fields.char("Faktur Pengganti",size=128),
		"nomorFaktur"			: fields.char("Nomor Faktur",size=128),
		"tanggalFaktur"			: fields.date("Tgl. Faktur",select=True),
		"npwpPenjual"			: fields.char("NPWP Penjual",size=128),
		"namaPenjual"			: fields.char("Penjual", size=128),
		"alamatPenjual"			: fields.text("Alamat Penjual"),
		"npwpLawanTransaksi"	: fields.char("NPWP Partner Transaksi"),
		"namaLawanTransaksi"	: fields.char("Partner Transaksi",size=128),
		"alamatLawanTransaksi"	: fields.text("Alamat Partner Transaksi"),
		"jumlahDpp"				: fields.float("Total DPP",digits=(16,0)),
		"jumlahPpn"				: fields.float("Total PPn",digits=(16,0)),
		"jumlahPpnBm"			: fields.float("Total PPnBM",digits=(16,0)),
		"statusApproval"		: fields.char("Status Approval",size=256),
		"statusFaktur"			: fields.char("Status Faktur",size=256),
		"efaktur_lines"			: fields.one2many("efaktur.lines","head_id","Efaktur Lines"),
		"related_invoice_id"	: fields.many2one("account.invoice","Related Invoice"),
		"report_period"			: fields.many2one("account.period","Period Pelaporan"),	
		
		"kode_jenis_transaksi"	: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="Kode Transaksi(F)", store=True, help="this is use only for sorting purposes"),
		"fg_pengganti"			: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="NPWP Vendor(F)", store=True, help="this is use only for sorting purposes"),
		"nomor_faktur"			: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="No Faktur(F)", store=True, help="this is use only for sorting purposes"),
		"tanggal_faktur"		: fields.function(_get_info_faktur, type="date", multi="get_info", string="Tgl Faktur(F)", store=True, help="this is use only for sorting purposes"),
		"npwp_penjual"			: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="NPWP Vendor(F)", store=True, help="this is use only for sorting purposes"),
		"nama_penjual"			: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="Vendor(F)", store=True, help="this is use only for sorting purposes"),
		"alamat_penjual"		: fields.function(_get_info_faktur, type="text", multi="get_info", string="Vendor Addrs(F)", store=True, help="this is use only for sorting purposes"),
		"npwp_lawan_transaksi"	: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="NPWP Lawan Transaksi(F)", store=True, help="this is use only for sorting purposes"),
		"nama_lawan_transaksi"	: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="Lawan Trans.(F)", store=True, help="this is use only for sorting purposes"),
		"alamat_lawan_transaksi": fields.function(_get_info_faktur, type="text", multi="get_info", string="Lawan Trans Addrs(F)", store=True, help="this is use only for sorting purposes"),
		"jumlah_dpp"			: fields.function(_get_info_faktur, type="float", multi="get_info", digits=(16,0), string="DPP Amt(F)", store=True, help="this is use only for sorting purposes"),
		"jumlah_ppn"			: fields.function(_get_info_faktur, type="float", multi="get_info", digits=(16,0), string="PPN Amt(F)", store=True, help="this is use only for sorting purposes"),
		"jumlah_ppnbm"			: fields.function(_get_info_faktur, type="float", multi="get_info", digits=(16,0), string="PPnBM Amt(F)", store=True, help="this is use only for sorting purposes"),
		"status_approval"		: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="Status Approval(F)", store=True, help="this is use only for sorting purposes"),
		"status_faktur"			: fields.function(_get_info_faktur, type="char", multi="get_info", size=128, string="Status Faktur(F)", store=True, help="this is use only for sorting purposes"),

	}
	_defaults = {
		"company_id": lambda self,cr,uid,context=None:self.pool.get("res.users").browse(cr,uid,uid).company_id.id
	}
	_order = 'tanggal_faktur asc, nama_penjual asc'

class efaktur_lines(osv.Model):
	_name="efaktur.lines"
	_rec_name = "nama"
	_columns ={
		"head_id"				: fields.many2one("efaktur.head","Efaktur",ondelete="cascade"),
		"nama"					: fields.char("Nama Barang",size=256),
		"hargaSatuan"			: fields.float("Price Unit"),
		"jumlahBarang"			: fields.float("Qty"),
		"hargaTotal"			: fields.float("Subtotal"),
		"diskon"				: fields.float("Discount"),
		"dpp"					: fields.float("DPP"),
		"ppn"					: fields.float("PPn"),
		"tarifPpnbm"			: fields.float("Tarif PPnBM"),
		"ppnbm"					: fields.float("PPnBM"),
	}