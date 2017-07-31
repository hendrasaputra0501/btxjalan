from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from datetime import datetime

class pabean_office(osv.Model):
	_name = "pabean.office"
	_columns = {
		'name' : fields.char('Name', size=64, required=True),
		'code' : fields.char('Code', size=6, required=True),
		'description' : fields.text('Description'),
	}

	def name_get(self, cr, uid, ids, context=None):
		res = []
		for pabean in self.browse(cr, uid, ids, context=context):
			res.append((pabean.id, "%s - %s"%(pabean.code,pabean.name)))
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, ['|',('name', operator, name),('code', operator, name)] + args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

pabean_office()

class res_company(osv.Model):
	_inherit = "res.company"
	_columns = {
		"code_module_ceisa_tpb"	: fields.char("ID MODUL TPB", size=4),	
		"skep_number"			: fields.char("No. SKEP", size=20),
		"skep_date"				: fields.date("Tanggal SKEP"),
		"pabean_office_id"		: fields.many2one('pabean.office', 'Pabean Office'),	
	}
res_company()

class beacukai(osv.Model):
	_name = "beacukai"

	def _get_picking_related(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		
		for line in self.browse(cr,uid,ids):
			result[line.id] = ''
			for picking in line.picking_ids2:
				result[line.id]+=picking.name+'; '
		return result

	_columns = {
		"shipment_type"		: fields.selection([('in',"Incoming"),('out',"Outgoing")],"Shipment Type",required=True),
		"transaction_type"	: fields.selection([('local',"Local"),('overseas',"Overseas")],"Transaction Type",required=False),
		"berikat_type"		: fields.selection([('inside',"Inside Kawasan Berikat"),('outside',"Outside Kawasan Berikat")],"Coverage Area",required=False),
		"document_type"		: fields.selection([('23',"BC 2.3"),
												('27_in', "BC 2.7 Masukan"),
												('27_out', "BC 2.7 Keluaran"),
												('30', "BC 3.0"),
												('40', "BC 4.0"),
												('41','BC 4.1')],"Document Type",required=True),
		"purpose"			: fields.selection([('subcont',"Subcontracted"),('lent',"Lent"),('repair',"Repair"),('exhibit',"Exhibition"),('other',"Other")],\
								"Shipment Purpose",required=False),
		"invoice_ids"		: fields.one2many("account.invoice",'bc_id',"Invoice(s)"),
		"invoice_id"		: fields.many2one("account.invoice","Invoice"),
		"shipper_id"		: fields.many2one("container.booking","Shipper"),
		"picking_ids"		: fields.one2many('stock.picking','bc_id',"Picking(s)"), #shipper jika in , 
		"picking_id"		: fields.many2one('stock.picking',"Picking",help='Khusus BC 4.0, jika shipment type=out maka data ini adalah data SHIPPER,selain itu adalh data MRR'), #shipper jika in , 
		"picking_ids2"	  : fields.many2many('stock.picking','beacukai_stock_picking_rel','beacukai_id','stock_picking_id',string='Delivery/Incoming Document'),
		'picking_related_number' : fields.function(_get_picking_related, type='char', size=500, 
			store={
				'beacukai'	: (lambda self, cr, uid, ids, c={}: ids,['picking_ids2','invoice_id'],10),
			}, string='Shipment Doc'
			),
		"sale_ids"	  	: fields.many2many('sale.order','beacukai_sale_order_rel','beacukai_id','sale_order_id',string='Contract'),
		"purchase_ids"	  : fields.many2many('purchase.order','beacukai_purchase_order_rel','beacukai_id','purchase_order_id',string='Contract'),

		'detail_packing_id'	: fields.one2many('beacukai.product.line','beacukai_id',"Detail Packing"),

		"source_partner_id"	: fields.many2one("res.partner","Source Partner",required=False),
		"source_address"	: fields.char("Source Address",required=False,size=600),
		"source_npwp"		: fields.char("Sender NPWP",required=False,size=30),
		"dest_partner_id"	: fields.many2one("res.partner","Destination Partner",required=False),
		"dest_address"		: fields.char("Destination Address",required=False,size=600),
		"dest_npwp"			: fields.char("Receiver NPWP",required=False,size=30),
		"info_partner_id"	: fields.many2one("res.partner","Info Partner",required=True),
		"info_address"		: fields.char("Info Address",required=False,size=600),
		"info_npwp"			: fields.char("Info NPWP",required=False,size=30),
		"ppjk_no"			: fields.char("PPJK No.",required=False,size=30),
		"ppjk_date"			: fields.date("PPJK Date.",required=False),
		#"transporter_id"	: fields.many2one('stock.transporter',"Transporter",required=False),
		'sarana_pengangkutan': fields.char("Sarana Pengangkutan.",required=False,size=30),
		"voyage_no"			: fields.char("Voyage/Flight No.",required=False,size=30),
		"stuffing_loc"		: fields.char("Stuffing Location",required=False,size=100),
		"unstuffing_loc"	: fields.char("Unstuffing Location",required=False,size=100),

		"cara_pengangkutan"	: fields.selection([('laut',"Laut"),('kereta',"Kereta Api"),('jalan',"Jalan Raya"),('udara',"Udara"),('other',"Other")],\
								"Cara Pengangkutan",required=False),


		"sale_id"			: fields.many2one("sale.order","Contract No."),
		
		"purchase_id"		: fields.many2one('purchase.order',"Contract No.",),
		"sale_id"			: fields.many2one('sale.order',"Contract No.",),
		"contract_date"		: fields.date("Contract Date",required=False),
		
		"volume"			: fields.float("Volume"),
		"volume_uom"		: fields.many2one("product.uom","Volume UoM"),
		"gross_weight"		: fields.float("Gross Weight"),
		"volume_uom"		: fields.many2one("product.uom","Gross UoM"),
		"nett_weight"		: fields.float("Nett Weight"),
		"nett_uom"			: fields.many2one("product.uom","Nett UoM"),
		
		"original_amount"	: fields.float("Nilai Pabean"),
		"original_currency"	: fields.many2one("res.currency","Currency"),
		"amount_idr"		: fields.float("Nilai Pabean IDR"),
		"currency_idr"		: fields.many2one("res.currency","Currency"),

		"packing"			: fields.char("Packing",required=False,size=100),
		"brand"				: fields.char("Brand",required=False,size=100),
		"container_no"		: fields.char("Container No.",required=False,size=100),
		"packing_qty"		: fields.float("Packing Qty"),
		



		"packing"			: fields.char("Packing",required=False,size=100),
		"brand"				: fields.char("Brand",required=False,size=100),
		"container_no"		: fields.char("Container No.",required=False,size=100),
		"packing_qty"		: fields.float("Packing Qty"),
		
		"name"				: fields.char("No.",size=100),
		"pabean_office_code": fields.char("Pabean Office Code",size=12),
		"pabean_partner_id"	: fields.many2one("res.partner","Pabean Office"),
		"pabean_address"	: fields.text("Pabean Office"),
		"pabean_office_id"	: fields.many2one('pabean.office', 'Pabean Office'),
		"tpb_type"			: fields.selection([('berikat_wh','Gudang Berikat'),
							('berikat_area','Kawasan Berikat'),('berikat_exh','Tempat Penyelenggaraan Pameran Berikat'),
							('free_cost_shop','Toko Bebas Bea'),('berikat_auction','Tempat Lelang Berikat'),('berikat_refurbish','Kawasan Daur Ulang Berikat')
							],"TPB Type"),
		"tpb_certificate"	: fields.char("TPB No."),	
		"code_module_ceisa_tpb"	: fields.char("Code Ceisa TPB Module"),	
		"registration_no"	: fields.char("Registration No.",size=64),
		"registration_date"	: fields.date("Registration Date",),
	#start by bahrul 
		#header 2 
		"merk_kemasan"			: fields.char("Merk Kemasan",size=32),
		"no_kemasan"			: fields.char("No. Kemasan/No. Peti kemas",size=10),
		"qty_kemasan"			: fields.char("Jumlah Kemasan",size=10),
		"Jenis_kemasan"			: fields.char("Jenis Kemasan",size=10),
		"no_segel"				: fields.char("No.segel",size=10),
		"jenis_segel"			: fields.char("No.segel",size=10),
		"keterangan_header_2"	: fields.char("keterangan",size=32),
		#uraian barang hasil
		"uraian_barang"			: fields.char("Uraian Barang",size=64),
		"kode"					: fields.char("Kode",size=10),
		"jumlah_satuan"			: fields.char("Jumlah satuan",size=10),
		"keterangan_hasil"		: fields.char("Keterangan",size=10),
		#Place and date
		"place"					: fields.char("Place",size=10),
		"date"					: fields.date("Date"),
		"signedby"				: fields.many2one("res.partner","Sign By"),
		#Diisi oleh bea dan cukai
		"no_pendaftaran"					: fields.char("No. Pendaftaran",size=15),
		"tgl_pendaftaran"					: fields.date("Tgl. Pendaftaran"),

		#header 3
		#Data Perhitungan jaminan dan jenis pungutan
		"cury_bm"					: fields.float("Cury BM"),
		"jumlah_bm"					: fields.float("Jumlah BM"),
		"cury_cukai"				: fields.float("Cury cukai"),
		"jumlah_cukai"				: fields.float("Jumlah Cukai"),
		"cury_ppn"					: fields.float("Cury PPN"),
		"jumlah_ppn"				: fields.float("Jumlah PPN"),
		"cury_ppnbm"				: fields.float("Cury PPnBM"),
		"jumlah_ppnbm"				: fields.float("Jumlah PPnBM"),
		"cury_pph"					: fields.float("Cury PPh"),
		"jumlah_pph"				: fields.float("Jumlah PPh"),
		"cury_total"				: fields.float("Cury Total"),
		"jumlah_total"				: fields.float("Jumlah Total"),
		#Data Jaminan
		"jenis_jaminan"				: fields.char("Jenis Jaminan",size=32),
		"no_jaminan"				: fields.char("No.Jaminan",size=32),
		"date_jaminan"				: fields.date("Tgl.Jaminan"),
		"cury_jaminan"				: fields.float("Jaminan Cury"),
		"nilai_jaminan"				: fields.float("Nilai Jaminan"),
		"tgl_jatuh_tempo"			: fields.date("Tgl. Jatuh Tempo"),
		"penjamin"					: fields.char("Penjamin",size=32),
		"bukti_penerimaan"			: fields.char("Bukti Penerimaan",size=32),
		"tgl_bukti_penerimaan"			: fields.date("Tgl. Bukti Penerimaan"),
		
		'beacukai_product_packages': fields.one2many('beacukai.product.package', 'beacukai_id'),
		# 'beacukai_container_ids': fields.one2many('beacukai.container', 'beacukai_id'),
		'beacukai_additional_doc': fields.one2many('beacukai.additional.doc', 'beacukai_id', string='Beacukai additional Doc'),
		'konversi_ids'				: fields.one2many('beacukai.product.konversi','beacukai_id','Konversi Product')
	#end by bahrul
	}

	_defaults = {
		# "currency_idr"		: lambda self,cr,uid,context:self.pool.get('res.currency').browse(cr, uid, pool.get('res.currency').search(cr,uid,[('name','=','IDR')])[0]).id or False,
		"shipment_type"		: lambda self,cr,uid,context:context.get('shipment_type','out'),
		"transaction_type"	: lambda *a:'overseas',
		"berikat_type"		: lambda *a:'inside',
		"document_type"		: lambda self,cr,uid,context:context.get('document_type','40'),
		'sarana_pengangkutan' : lambda *a:'Truk',
		'cara_pengangkutan' : lambda *a:'jalan',
		'pabean_address'	: lambda * a : 'KPPBC Semarang',
		'pabean_office_code': lambda *a :'060800',
		'pabean_office_id' : lambda self,cr,uid,context: self.pool.get('res.users').browse(cr, uid, uid).company_id.pabean_office_id.id,
		'code_module_ceisa_tpb': lambda self,cr,uid,context: self.pool.get('res.users').browse(cr, uid, uid).company_id.code_module_ceisa_tpb,
		'name' : lambda *r : '/',
		'tpb_certificate' : lambda self,cr,uid,context: self.pool.get('res.users').browse(cr, uid, uid).company_id.skep_number,
	}

	def onchange_shipper(self,cr,uid,ids,shipper_id,context=None):
		res={}
		data=self.pool.get('container.booking').browse(cr,uid,shipper_id)
		res={
				'source_partner_id':data.shipper and data.shipper.id or False,
				'source_address':data.shipper.street or "",
				'source_npwp':data.shipper.partner_id.npwp or "",
			}
		return {'value':res}

	def onchange_shipment_type(self,cr,uid,ids,shipment_type,context=None):
		res={}
		res={
				'picking_id':[('type','=',shipment_type),('state','=','done')],
				'picking_ids2':[('type','=',shipment_type),('state','=','done')]
			}
		return {'domain':res,'value':{'picking_id':False}}

	def onchange_invoice_id(self,cr,uid,ids,invoice_id,context=None):
		if context is None:
			context = {}
		res={}
		picking_ids = self.pool.get('stock.picking').search(cr, uid, [('invoice_id','=',invoice_id)], context=context)
		if picking_ids:
			res.update({'picking_ids2':[(6,0,picking_ids)]})
		return {'value':res}

	def _get_price_unit(self, cr, uid, ids, sale_line_id=False, purchase_line_id=False):
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		if not sale_line_id and not purchase_line_id:
			return 0
		elif sale_line_id:
			if sale_line_id.tax_id:
				taxes = self.pool.get('account.tax').compute_all(cr, uid, sale_line_id.tax_id, sale_line_id.price_unit, sale_line_id.product_uom_qty, product=sale_line_id.product_id, partner=sale_line_id.order_id.partner_id)
				return round(taxes['total']/sale_line_id.product_uom_qty,4)
			else:
				return sale_line_id.price_unit
		elif purchase_line_id:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in purchase_line_id.discount_ids], purchase_line_id.price_unit, purchase_line_id.product_qty, context={})
			price_after = disc.get('price_after',purchase_line_id.price_unit)
			
			taxes = tax_obj.compute_all(cr, uid, purchase_line_id.taxes_id, price_after, purchase_line_id.product_qty, purchase_line_id.product_id, purchase_line_id.order_id.partner_id)
			order_id = purchase_line_id.order_id or purchase_line_id.old_order_id
			cur = order_id.pricelist_id.currency_id
			amount_sub = cur_obj.round(cr, uid, cur, taxes['total'])
			return round(amount_sub/purchase_line_id.product_qty,4)
			
	def _get_price_subtotal(self, cr, uid, ids, product_qty=0, sale_line_id=False, purchase_line_id=False):
		cur_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		product_qty = product_qty or 0.0
		if not sale_line_id and not purchase_line_id:
			return 0
		elif sale_line_id:
			taxes = self.pool.get('account.tax').compute_all(cr, uid, sale_line_id.tax_id, sale_line_id.price_unit, product_qty, product=sale_line_id.product_id, partner=sale_line_id.order_id.partner_id)
			return taxes['total']
		elif purchase_line_id:
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in purchase_line_id.discount_ids], purchase_line_id.price_unit, product_qty, context={})
			price_after = disc.get('price_after',purchase_line_id.price_unit)
			taxes = tax_obj.compute_all(cr, uid, purchase_line_id.taxes_id, price_after, product_qty, purchase_line_id.product_id, purchase_line_id.order_id.partner_id)
			order_id = purchase_line_id.order_id or purchase_line_id.old_order_id
			cur = order_id.pricelist_id.currency_id
			amount_sub = cur_obj.round(cr, uid, cur, taxes['total'])
			return amount_sub
		

	def onchange_picking_id(self,cr,uid,ids,picking_ids,shipment_type,document_type,context=None):
		res={
			'source_partner_id':False,
			'source_address':'',
			'source_npwp':'',
				
			'dest_partner_id':False,
			'dest_address':'',
			'dest_npwp':'',

			'info_partner_id':False,
			'info_address':'',
			'info_npwp':'',
				
			'purchase_ids':[(6,0,[])],
			'sale_ids':[(6,0,[])],
			'contract_date' : False,
			'gross_weight':0.0,
			'amount_idr':0.0,
			'currency_idr':False,
			'stuffing_loc':'',
			'unstuffing_loc':'KWS BRKT, PT. BITRATEX,IND',
			'pabean_office_code':'060800',

			'detail_packing_id':[],
			'konversi_ids':[],
		}
		if not picking_ids or not picking_ids[0][2]:
			return {'value':res}	

		res = {}
		curr_obj=self.pool.get('res.currency')
		uom_obj=self.pool.get('product.uom')
		tax_obj = self.pool.get('account.tax')
		datasssss=self.pool.get('stock.picking').browse(cr,uid,picking_ids[0][2])
		move_lines = []
		konversi_lines = []
		purchase_ids = []
		sale_ids = []
		to_curr=curr_obj.search(cr,uid,[('name','=','IDR')])[0]
		uom_kgs=uom_obj.search(cr,uid,[('name','=','KGS')])[0]
		

		total_price_subtotal_idr=0.0
		total_berat_kotor=0.0
		total_berat_bersih=0.0
		registration_date = False
		for data in datasssss:
			if shipment_type == 'in' :
				registration_date = data.date_done!='False' and data.date_done or False
				for mv in data.move_lines:
					if mv.purchase_line_id and mv.purchase_line_id.order_id and mv.purchase_line_id.order_id.pricelist_id and mv.purchase_line_id.order_id.pricelist_id.id:
						from_curr=mv.purchase_line_id.order_id.pricelist_id.currency_id.id 
						# price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, round((mv.price_unit or mv.purchase_line_id.price_unit)*mv.product_qty,2), context={'date':mv.picking_id.date_done})

						price_unit = self._get_price_unit(cr, uid, ids, purchase_line_id = (mv.purchase_line_id and mv.purchase_line_id or False))
						amount_sub = self._get_price_subtotal(cr, uid, ids, product_qty=mv.product_qty, purchase_line_id = (mv.purchase_line_id and mv.purchase_line_id or False))
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, amount_sub, context={'date':mv.picking_id.date_done})

						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						except:
							qty_kgs = mv.product_qty
						try:
							qty_kg = uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
							default_uom = uom_kgs
						except:
							default_uom=mv.product_uom.id
						move_lines.append({
										"move_id":mv.id,
										"product_id": mv.product_id.id,
										"product_qty": mv.product_qty,
										"product_uom": mv.product_uom.id,
										"product_qty_kgs": qty_kgs or 0.0,
										"product_uom_kgs": default_uom,
										"price_unit" : price_unit,
										"price_subtotal": amount_sub,
										"price_subtotal_idr": price_subtotal_idr,
										"net_weight" : mv.net_weight or 0.0,
							})
					elif mv.sale_line_id and mv.sale_line_id.order_id and mv.sale_line_id.order_id.pricelist_id and mv.sale_line_id.order_id.pricelist_id.id:
						from_curr=mv.sale_line_id.order_id.pricelist_id.currency_id.id 
						# price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, round((mv.price_unit or mv.purchase_line_id.price_unit)*mv.product_qty,2), context={'date':mv.picking_id.date_done})
						
						price_unit = self._get_price_unit(cr, uid, ids, sale_line_id = (mv.sale_line_id and mv.sale_line_id or False))
						amount_sub = self._get_price_subtotal(cr, uid, ids, product_qty=mv.product_qty, sale_line_id = (mv.sale_line_id and mv.sale_line_id or False))
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, amount_sub, context={'date':mv.picking_id.date_done})
						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						except:
							qty_kgs = mv.product_qty
						try:
							qty_kg = uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
							default_uom = uom_kgs
						except:
							default_uom=mv.product_uom.id
						move_lines.append({
										"move_id":mv.id,
										"product_id": mv.product_id.id,
										"product_qty": mv.product_qty,
										"product_uom": mv.product_uom.id,
										"product_qty_kgs": qty_kgs or 0.0,
										"product_uom_kgs": default_uom,
										"price_unit" : price_unit,
										"price_subtotal":amount_sub,
										"price_subtotal_idr":price_subtotal_idr,
										"net_weight" : mv.net_weight or 0.0,
							})
					else:
						from_curr=mv.price_currency_id and mv.price_currency_id.id or mv.picking_id.company_id.currency_id.id 
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, round((mv.price_unit or 0.0)*mv.product_qty,2), context={'date':mv.picking_id.date_done})
						# qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						except:
							qty_kgs = mv.product_qty
						try:
							qty_kg = uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
							default_uom = uom_kgs
						except:
							default_uom=mv.product_uom.id
						move_lines.append({
										"move_id":mv.id,
										"product_id": mv.product_id.id,
										"product_qty": mv.product_qty,
										"product_uom": mv.product_uom.id,
										"product_qty_kgs": qty_kgs or 0.0,
										"product_uom_kgs": default_uom,
										"price_unit" : (mv.price_unit or 0.0),
										"price_subtotal":mv.price_unit*mv.product_qty,
										"price_subtotal_idr":price_subtotal_idr,
										"net_weight" : mv.net_weight or 0.0,
							})
					# total_berat_kotor+=mv.product_qty
					total_berat_kotor+=mv.gross_weight
					total_berat_bersih+=float(qty_kgs) or mv.product_qty or 0.0
					total_price_subtotal_idr += price_subtotal_idr
					if mv.product_id and mv.product_id.internal_type in ('Finish','Finish_others') and document_type!='30':
						konversi = {
							'product_id':mv.product_id.id,
							"product_qty": mv.product_qty,
							"product_uom": mv.product_uom.id,
							"product_qty_kgs": mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs) or 0.0,
							"product_uom_kgs": uom_kgs,
							}
						if mv.product_id and mv.product_id.blend_code and mv.product_id.blend_code.blend_lines:
							komponen_lines = []
							for komp in mv.product_id.blend_code.blend_lines:
								komponen_lines.append((0,0,{
									'product_id':False,
									'rm_category_id':komp.rm_type_id and komp.rm_type_id.category_id and komp.rm_type_id.category_id.id or False,
									'product_qty':mv.product_qty*(komp.percentage/100),
									'product_uom':mv.product_uom and mv.product_uom.id or False,
									"product_qty_kgs": mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty*(komp.percentage/100), uom_kgs) or 0.0,
									"product_uom_kgs": uom_kgs,
									}))

							konversi.update({
								'komponen_ids':komponen_lines,
								})
						konversi_lines.append(konversi)

				if data.purchase_id and data.purchase_id.id not in purchase_ids:
					purchase_ids.append(data.purchase_id.id)
					
				if res:
					res.update({
						'purchase_ids':[(6,0,purchase_ids)],
						'contract_date' : data.purchase_id and data.purchase_id.date_order or False,
						'gross_weight':total_berat_kotor,
						'nett_weight':total_berat_bersih,
						'amount_idr':total_price_subtotal_idr,
						'stuffing_loc':data.partner_id.city,
						'detail_packing_id':move_lines,
						'konversi_ids': konversi_lines,
					})
				else:
					res={
						'source_partner_id':data.partner_id.id and data.partner_id.id or False,
						'source_address':data.partner_id.street,
						'source_npwp':data.partner_id.npwp,
							
						'dest_partner_id':data.company_id.partner_id.id,
						'dest_address':data.company_id.partner_id.street,
						'dest_npwp':data.company_id.partner_id.npwp,

						'info_partner_id':data.company_id.partner_id.id,
						'info_address':data.company_id.partner_id.street,
						'info_npwp':data.company_id.partner_id.npwp,
						
						'registration_date' : registration_date,

						# 'purchase_id':data.purchase_id and data.purchase_id.id or False,
						'purchase_ids':[(6,0,purchase_ids)],
						'contract_date' : data.purchase_id and data.purchase_id.date_order or False,
						'gross_weight':total_berat_kotor,
						'nett_weight':total_berat_bersih,
						'amount_idr':total_price_subtotal_idr,
						'currency_idr':to_curr or False,
						'stuffing_loc':data.partner_id.city,
						'unstuffing_loc':'KWS BRKT, PT. BITRATEX,IND',
						'pabean_office_code':'060800',

						'detail_packing_id':move_lines,
						'konversi_ids':konversi_lines,
					}
			elif shipment_type == 'out' :
				registration_date = data.date_done!='False' and data.date_done or False
				for mv in data.move_lines:
					if mv.sale_line_id and mv.sale_line_id.order_id and mv.sale_line_id.order_id.pricelist_id and mv.sale_line_id.order_id.pricelist_id.id:
						from_curr = mv.sale_line_id and mv.sale_line_id.order_id and mv.sale_line_id.order_id.pricelist_id and mv.sale_line_id.order_id.pricelist_id.currency_id and mv.sale_line_id.order_id.pricelist_id.currency_id.id or mv.picking_id.company_id.currency_id.id
					
						price_unit = self._get_price_unit(cr, uid, ids, sale_line_id = (mv.sale_line_id and mv.sale_line_id or False))
						amount_sub = self._get_price_subtotal(cr, uid, ids, product_qty=mv.product_qty, sale_line_id = (mv.sale_line_id and mv.sale_line_id or False))
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, amount_sub, context={'date':mv.picking_id.date_done})
						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						except:
							qty_kgs = mv.product_qty
						total_price_subtotal_idr += price_subtotal_idr
						move_lines.append({
							"move_id":mv.id,
							"product_id": mv.product_id.id,
							"product_qty": mv.product_qty,
							"product_uom": mv.product_uom.id,
							"product_qty_kgs": qty_kgs or 0.0,
							"product_uom_kgs": uom_kgs,
							"price_unit" : price_unit or mv.price_unit or 0.0,
							"price_subtotal":amount_sub or (price_unit or mv.price_unit or 0.0)*mv.product_qty or 0.0,
							"price_subtotal_idr":price_subtotal_idr,
						})
					elif mv.purchase_line_id and mv.purchase_line_id.order_id and mv.purchase_line_id.order_id.pricelist_id and mv.purchase_line_id.order_id.pricelist_id.id:
						from_curr = mv.purchase_line_id and mv.purchase_line_id.order_id and mv.purchase_line_id.order_id.pricelist_id and mv.purchase_line_id.order_id.pricelist_id.currency_id and mv.purchase_line_id.order_id.pricelist_id.currency_id.id or mv.purchase_line_id.company_id.currency_id.id
					
						price_unit = self._get_price_unit(cr, uid, ids, purchase_line_id = (mv.purchase_line_id and mv.purchase_line_id or False))
						amount_sub = self._get_price_subtotal(cr, uid, ids, product_qty=mv.product_qty, purchase_line_id = (mv.purchase_line_id and mv.purchase_line_id or False))
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, amount_sub or (mv.price_unit*mv.product_qty), context={'date':mv.picking_id.date_done})
						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
							default_uom = uom_kgs
						except:
							default_uom=mv.product_uom.id
							qty_kgs = mv.product_qty
						total_price_subtotal_idr += price_subtotal_idr
						move_lines.append({
							"move_id":mv.id,
							"product_id": mv.product_id.id,
							"product_qty": mv.product_qty,
							"product_uom": mv.product_uom.id,
							"product_qty_kgs": qty_kgs or 0.0,
							"product_uom_kgs": default_uom,
							"price_unit" : price_unit or mv.price_unit or 0.0,
							"price_subtotal":(price_unit or mv.price_unit or 0.0)*mv.product_qty or 0.0,
							"price_subtotal_idr":price_subtotal_idr,
						})
					else:
						from_curr=mv.price_currency_id and mv.price_currency_id.id or mv.picking_id.company_id.currency_id.id 
						price_subtotal_idr = curr_obj.computerate(cr, uid, from_curr, to_curr, round((mv.price_unit or 0.0)*mv.product_qty,2), context={'date':mv.picking_id.date_done})
						# qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						try:
							qty_kgs = mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
						except:
							qty_kgs = mv.product_qty
						try:
							qty_kg = uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs)
							default_uom = uom_kgs
						except:
							default_uom=mv.product_uom.id
						move_lines.append({
										"move_id":mv.id,
										"product_id": mv.product_id.id,
										"product_qty": mv.product_qty,
										"product_uom": mv.product_uom.id,
										"product_qty_kgs": qty_kgs or 0.0,
										"product_uom_kgs": default_uom,
										"price_unit" : (mv.price_unit or 0.0),
										"price_subtotal":mv.price_unit*mv.product_qty,
										"price_subtotal_idr":price_subtotal_idr,
							})
					total_berat_bersih+=float(qty_kgs) or mv.product_qty or 0.0
					total_berat_kotor+=mv.product_uop and mv.product_uop.gross_weight*mv.product_uop_qty or total_berat_bersih
					if mv.product_id and mv.product_id.internal_type in ('Finish','Finish_others') and document_type!='30':
						
						konversi = {
							'product_id':mv.product_id.id,
							"product_qty": mv.product_qty,
							"product_uom": mv.product_uom.id,
							"product_qty_kgs": mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, uom_kgs) or 0.0,
							"product_uom_kgs": uom_kgs,
							}
						if mv.product_id and mv.product_id.blend_code and mv.product_id.blend_code.blend_lines:
							komponen_lines = []
							for komp in mv.product_id.blend_code.blend_lines:
								komponen_lines.append((0,0,{
									'product_id':False,
									'rm_category_id':komp.rm_type_id and komp.rm_type_id.category_id and komp.rm_type_id.category_id.id or False,
									'product_qty':mv.product_qty*(komp.percentage/100),
									'product_uom':mv.product_uom and mv.product_uom.id or False,
									"product_qty_kgs": mv.product_uom.id == uom_kgs and mv.product_qty or uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty*(komp.percentage/100), uom_kgs) or 0.0,
									"product_uom_kgs": uom_kgs,
									}))

							konversi.update({
								'komponen_ids':komponen_lines,
								})
						konversi_lines.append(konversi)
				if data.sale_id and data.sale_id.id not in sale_ids:
					sale_ids.append(data.sale_id.id)

				if res:
					res.update({
						'sale_ids':[(6,0,sale_ids)],
						'detail_packing_id':move_lines,
						'nett_weight':total_berat_bersih,
						'gross_weight':total_berat_kotor,
						'amount_idr':total_price_subtotal_idr,
						'konversi_ids':konversi_lines,
					})
				else:
					res={
						'source_partner_id':data.company_id.partner_id.id,
						'source_address':data.company_id.partner_id.street,
						'source_npwp':data.company_id.partner_id.npwp,

						'dest_partner_id':data.partner_id.id and data.partner_id.id or False,
						'dest_address':data.partner_id.street,
						'dest_npwp':data.partner_id.npwp,
						
						'info_partner_id':data.company_id.partner_id.id,
						'info_address':data.company_id.partner_id.street,
						'info_npwp':data.company_id.partner_id.npwp,

						'registration_date':registration_date,
						
						'sale_ids':[(6,0,sale_ids)],
						'contract_date' : data.sale_id and data.sale_id.date_order or False,
						'gross_weight':total_berat_kotor,
						'nett_weight':total_berat_bersih,
						'amount_idr':total_price_subtotal_idr,
						'currency_idr':to_curr or False,
						'detail_packing_id':move_lines,
						'konversi_ids':konversi_lines,
					}
		return {'value':res}

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		if vals.get('name','/')=='/' and vals.get('document_type',False) \
			and vals.get('registration_date',False) and vals.get('pabean_office_id',False) \
			and vals.get('code_module_ceisa_tpb',False):
			name = ""
			if vals.get('document_type',False) in ('27_out','40','41'):
				seq_name = '%s.%s'%(self._name,str(vals['document_type']))
				
				try:
					name = self.pool.get('ir.sequence').get(cr, uid, seq_name)
				except:
					raise osv.except_osv(_('Error'),_("Can not generate Nomor Pengajuan!"))
				if not name:
					name ='/'
				pabean_office = self.pool.get('pabean.office').browse(cr, uid, vals['pabean_office_id'])
				try:
					date = datetime.strptime(vals['registration_date'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')
				except:
					date = datetime.strptime(vals['registration_date'],'%Y-%m-%d').strftime('%Y%m%d')
				name = "%s%s00%s%s%s"%(pabean_office.code[:4], (vals['document_type']=='27_out' and '27' or vals['document_type']), vals['code_module_ceisa_tpb'], date, name)
			else:
				seq_name = self._name
				try:
					date = datetime.strptime(vals['registration_date'],'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
				except:
					date = datetime.strptime(vals['registration_date'],'%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
				name = self.pool.get('ir.sequence').get(cr, uid, seq_name, context={'date':date})
			
			vals.update({'name': name})
		return super(beacukai, self).create(cr, uid, vals, context)

beacukai()

class beacukai_product_sourcebc_line(osv.Model):
	_name = "beacukai.product.sourcebc.line"
	_columns = {
		"line_id" : fields.many2one('beacukai.product.line', 'Line Reference', ondelete="cascade"),
		"source_bc_id" : fields.many2one('beacukai',"Beacukai",required=True),
		"source_bc_name" : fields.char('No. Pengajuan', required=True),
		"source_bc_registration_no" : fields.char('No. BC', required=True),
		"source_bc_registration_date" : fields.date('Tanggal Pengajuan', required=True),
		"soucre_bc_pabean_office_id" : fields.many2one('pabean.office','KPPBC Dok', required=True),
		"product_id" : fields.many2one('product.product', 'Product'),
		"product_uom" : fields.many2one('product.uom', 'UoM'),
		"price_subtotal" : fields.float('Price Unit', digits_compute=dp.get_precision('Product Price'), required=True),
	}
beacukai_product_sourcebc_line()

class beacukai_product_line(osv.Model):
	_name = "beacukai.product.line"
	_rec_name="product_id"
	_columns = {
		"beacukai_id":fields.many2one('beacukai',"Beacukai",required=False,ondelete="cascade"),
		"move_id":fields.many2one('stock.move',"Move ID", required=False),
		"product_id": fields.many2one("product.product","Product",required=True),
		"product_qty": fields.float("Quantity",digits_compute= dp.get_precision('Product Unit of Measure'),required=True),
		"product_uom": fields.many2one("product.uom","UoM",required=True),
		"product_qty_kgs": fields.float("Quantity KGS",digits_compute= dp.get_precision('Product Unit of Measure'),required=False),
		"product_uom_kgs": fields.many2one("product.uom","UoM KGS",required=False),
		"price_unit" : fields.float("Price Unit",digits_compute= dp.get_precision('Product Price'),required=True,),
		"price_subtotal":fields.float("Subtotal",required=True),
		"price_subtotal_idr":fields.float("Harga(IDR)",required=True),
		"merk" : fields.char("Merk", size=64), 
		"tipe" : fields.char("Tipe", size=64), 
		"ukuran" : fields.char("Ukuran", size=64), 
		"net_weight" : fields.float("Netto", digits_compute= dp.get_precision('Product Price'), required=True),
		"volume" : fields.float("Volume", digits_compute= dp.get_precision('Product Price'), required=True),
		"product_source_lines" : fields.one2many('beacukai.product.sourcebc.line', 'line_id', 'Data Bahan Baku'),
	}
	_defaults = {
		'net_weight' : 0.0,
		'volume' : 0.0,
	}

	def onchange_product(self,cr,uid,ids,product_id,context=None):
		res={}
		data=self.pool.get('product.product').browse(cr,uid,product_id)
		res={
				'product_uom_kgs':data.uom_id and  data.uom_id.id or False,
				'product_uom':data.uom_id and data.uom_id.id or False,
			}
		return {'value':res}

beacukai_product_line()

class beacukai_document_attached(osv.Model):
	_name = "beacukai.document.attached"
	_columns = {
		'code' : fields.char("Kode", size=20, required=True),
		'name' : fields.char("Uraian", size=64, required=True),
	}
beacukai_document_attached()

class beacukai_additional_doc(osv.Model):
	_name = "beacukai.additional.doc"
	_rec_name="no_doc"
	_columns = {
		'beacukai_id':fields.many2one('beacukai',"Beacukai", required=True, ondelete="cascade"),
		'jenis_doc': fields.char("Jenis Document"),
		'doc_id': fields.many2one('beacukai.document.attached',"Jenis Document"),
		'no_doc': fields.char("No. Document", size=64),
		'tanggal_doc': fields.date("Tanggal"),
	}
beacukai_additional_doc()

class beacukai_product_package(osv.Model):
	_name = "beacukai.product.package"
	_columns = {
		'beacukai_id':fields.many2one('beacukai',"Beacukai", required=True, ondelete="cascade"),
		'jumlah': fields.float("Jumlah", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
		'package_id': fields.many2one('product.uom',"Jenis Package", required=True),
		'merk': fields.char("Merk", size=64),
	}
beacukai_product_package()

# class beacukai_container(osv.Model):
# 	_name = "beacukai.container"
# 	_columns = {
# 		'beacukai_id':fields.many2one('beacukai',"Beacukai", required=True, ondelete="cascade"),
# 		'jumlah': fields.float("Jumlah", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
# 		'package_id': fields.many2one('product.uom',"Jenis Package"),
# 		'merk': fields.char("Merk", size=64),
# 	}
# beacukai_container()

class beacukai_product_konversi(osv.Model):
	_name = "beacukai.product.konversi"
	_rec_name="product_id"
	_columns = {
		'beacukai_id':fields.many2one('beacukai',"Beacukai",required=True,ondelete="cascade"),
		"product_id": fields.many2one("product.product","Product",required=True),
		"product_qty": fields.float("Quantity",digits_compute= dp.get_precision('Product Unit of Measure'),required=True),
		"product_uom": fields.many2one("product.uom","UoM",required=True),
		"product_qty_kgs": fields.float("Quantity KGS",digits_compute= dp.get_precision('Product Unit of Measure'),required=False),
		"product_uom_kgs": fields.many2one("product.uom","UoM KGS",required=False),
		"komponen_ids":fields.one2many('beacukai.product.komponen','product_konversi_id','Komponen'),
	}
beacukai_product_konversi()

class beacukai_product_komponen(osv.Model):
	_name = "beacukai.product.komponen"
	_rec_name="product_id"
	_columns = {
		'product_konversi_id':fields.many2one('beacukai.product.konversi',"Referense",required=True,ondelete="cascade"),
		"product_id": fields.many2one("product.product","Product",required=False),
		"rm_category_id": fields.many2one("product.rm.type.category","RM Categ",required=False),
		"product_qty": fields.float("Quantity",digits_compute= dp.get_precision('Product Unit of Measure'),required=True),
		"product_uom": fields.many2one("product.uom","UoM",required=True),
		"product_qty_kgs": fields.float("Quantity KGS",digits_compute= dp.get_precision('Product Unit of Measure'),required=False),
		"product_uom_kgs": fields.many2one("product.uom","UoM KGS",required=False),
		"source_bc_type" : fields.selection([('27_in', "BC 2.7 Masukan"), ('40', "BC 4.0")],"Document Type"),
		'source_bc_ids' : fields.many2one('beacukai.product.komponen.doc', 'line_id','Source BCs'),
	}
beacukai_product_komponen()

class beacukai_product_komponen_doc(osv.Model):
	_name = "beacukai.product.komponen.doc"
	_columns = {
		'line_id' : fields.many2one('beacukai.product.komponen', 'Reference', required=True),
		'sequence_ref' : fields.integer('Nomor Urut', required=True),
		'source_beacukai_id' : fields.many2one('beacukai','Source BC', required=True),
		'source_bc_type' : fields.related('line_id',type='selection', selection=[('27_in', "BC 2.7 Masukan"), ('40', "BC 4.0")], string="Document Type"),
		'product_qty' : fields.float("Quantity", digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
	}