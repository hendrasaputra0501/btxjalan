import re
import time
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime

class faktur_pajak_reconciliation_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(faktur_pajak_reconciliation_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_faktur_pajak_reported':self._get_faktur_pajak_reported,
			'get_faktur_pajak_only_invoiced':self._get_faktur_pajak_only_invoiced,
			'get_pending_moves':self._get_pending_moves,
		})
	
	def _get_faktur_pajak_reported(self, data):
		# all faktur pajak which has already scanned and reported yet
		res = []
		cr = self.cr
		uid = self.uid
		efaktur_head_pool = self.pool.get('efaktur.head')

		data=data['form']
		query = "SELECT \
					eh.id \
				FROM \
					efaktur_head eh \
					inner join efaktur_batch eb ON eb.id=eh.batch_id \
				WHERE eb.period_id=%s \
				ORDER BY eh.tanggal_faktur ASC"%(data['period_id'][0])
				# WHERE eb.date_min>='%s' and eb.date_max<='%s'"%(data['start_date'],data['end_date'])
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		ef_ids = [x['id'] for x in res]
		
		return efaktur_head_pool.browse(cr, uid, ef_ids)

	def _get_faktur_pajak_only_invoiced(self, data):
		# all faktur pajak which has already scanned but not reported yet
		res = []
		cr = self.cr
		uid = self.uid
		efaktur_head_pool = self.pool.get('efaktur.head')

		data=data['form']
		query = "SELECT ehh.id FROM \
					(SELECT id FROM (\
						(SELECT \
							eh.id \
						FROM \
							efaktur_head eh \
							inner join account_invoice ai on ai.id=eh.related_invoice_id and ai.move_id is not NULL\
						WHERE eh.batch_id is NULL and eh.related_ext_transaksi_id is NULL ) \
						UNION ALL \
						(SELECT \
							eh.id \
						FROM \
							efaktur_head eh \
							inner join ext_transaksi ex on ex.id=eh.related_ext_transaksi_id and ex.move_id is not NULL \
						WHERE eh.batch_id is NULL and eh.related_invoice_id is NULL)) efaktur \
					GROUP BY id ) dummy \
					INNER JOIN efaktur_head ehh on ehh.id=dummy.id \
				ORDER BY ehh.tanggal_faktur ASC"
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		ef_ids = [x['id'] for x in res]
		
		return efaktur_head_pool.browse(cr, uid, ef_ids)
		
	def _get_pending_moves(self, data):
		invoice_pool = self.pool.get('account.invoice')
		ext_trans_pool = self.pool.get('ext.transaksi')
		res = []
		cr = self.cr
		uid = self.uid
		# vatin_account_ids = data.get('vatin_account_ids',[])
		vatin_account_ids = [153,154,285,346]
		# get move_id that related to invoice and its invoice doesnt have scan faktur pajak
		query1 = "SELECT ai.id FROM\
					account_move_line aml \
					INNER JOIN account_invoice ai ON ai.move_id=aml.move_id \
				WHERE aml.account_id in %s and ai.id not in (select related_invoice_id from efaktur_head where related_invoice_id is not NULL) \
					and aml.date>='2017-01-01' \
				GROUP BY ai.id \
				"%(str(tuple(vatin_account_ids)))
		self.cr.execute(query1)
		qresult1 = self.cr.dictfetchall()
		inv_ids = [x['id'] for x in qresult1]
		for inv in invoice_pool.browse(cr, uid, inv_ids):
			res.append({'move_id':inv.move_id,'related_invoice_id':inv,'related_ext_transaksi_id':False})
		
		# get move_id that related to ext.transaksi and its transaction doesnt have scan faktur pajak
		query2 = "SELECT et.id FROM\
					account_move_line aml \
					INNER JOIN ext_transaksi et ON et.move_id=aml.move_id or et.tax_move_id=aml.move_id \
				WHERE aml.account_id in %s and et.id not in (select related_ext_transaksi_id from efaktur_head where related_ext_transaksi_id is not NULL) \
					and aml.date>='2017-01-01' \
				GROUP BY et.id \
				"%(str(tuple(vatin_account_ids)))
		self.cr.execute(query2)
		qresult2 = self.cr.dictfetchall()
		ext_trans_ids = [x['id'] for x in qresult2]
		for ext_trans in ext_trans_pool.browse(cr, uid, ext_trans_ids):
			move_id = False
			if ext_trans.tax_move_id and ext_trans.move_id and ext_trans.move_id.id==ext_trans.tax_move_id.id:
				move_id = ext_trans.move_id
			elif ext_trans.tax_move_id and ext_trans.move_id and ext_trans.move_id.id!=ext_trans.tax_move_id.id:
				move_id = ext_trans.tax_move_id
			elif ext_trans.tax_move_id and not ext_trans.move_id:
				move_id = ext_trans.tax_move_id
			elif ext_trans.move_id and not ext_trans.tax_move_id:
				move_id = ext_trans.move_id
			if ext_trans.type_transaction=='payment':
				date_payment = move_id.date
			res.append({'move_id':move_id,'related_invoice_id':False,'related_ext_transaksi_id':ext_trans})
		return res

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id.id
		from_curr = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.tax_base_currency.id
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, currency_usd, amount, context={'date':date})

	def _get_rate_conversion(self, from_curr, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		from_curr = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.tax_base_currency
		return self.pool.get('res.currency')._get_conversion_rate(self.cr, self.uid, currency_usd, from_curr, context={'date':date})
	# def _get_date_range(self,data):
	# 	date_start = data['start_date']
	# 	date_stop = data['end_date']
	# 	if date_start and not date_stop:
	# 		da = datetime.strptime(date_start,"%Y-%m-%d")
	# 		return "From : %s"%da.strftime("%d/%m/%Y")
	# 	elif date_stop and not date_start:
	# 		db = datetime.strptime(date_stop,"%Y-%m-%d")
	# 		return "Until : %s"%db.strftime("%d/%m/%Y")
	# 	elif date_stop and date_start:
	# 		da = datetime.strptime(date_start,"%Y-%m-%d")
	# 		db = datetime.strptime(date_stop,"%Y-%m-%d")
	# 		return "Range : %s - %s"%(da.strftime("%d/%m/%Y"),db.strftime("%d/%m/%Y"))
	# 	else:
	# 		return "Wholetime"

class faktur_pajak_reconciliation_xls(report_xls):
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
		# style
		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz center; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: top thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: top thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		
		ws = wb.add_sheet('Vat In Recon',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		
		# max_width_col={0:12,1:8,2:12,3:5,4:10,5:12,6:8,7:8,8:6}
		subtotal={6:0.0,7:0.0}
		rowcount = start_row = 0
		
		# Header Title
		ws.write_merge(rowcount, rowcount, 0, 6, "SPN PPN", th_top_style)
		ws.write_merge(rowcount, rowcount, 7, 9, "General Ledger", th_top_style)
		ws.write_merge(rowcount, rowcount, 10, 13, "Scan Information", th_top_style)
		ws.write_merge(rowcount, rowcount, 14, 15, "Remarks", th_top_style)
		ws.write(rowcount, 16, "Payment", th_top_style)
		rowcount +=1
		ws.write(rowcount, 0, "Masa", th_bottom_style)
		ws.write(rowcount, 1, "Customer", th_bottom_style)
		ws.write(rowcount, 2, "No. Faktur Pajak", th_bottom_style)
		ws.write(rowcount, 3, "Date Faktur Pajak", th_bottom_style)
		ws.write(rowcount, 4, "Month", th_bottom_style)
		ws.write(rowcount, 5, "DPP", th_bottom_style)
		ws.write(rowcount, 6, "PPN", th_bottom_style)
		ws.write(rowcount, 7, "No. Entry", th_bottom_style)
		ws.write(rowcount, 8, "Date Effective", th_bottom_style)
		ws.write(rowcount, 9, "PPN", th_bottom_style)
		ws.write(rowcount, 10, "No. Faktur Pajak", th_bottom_style)
		ws.write(rowcount, 11, "Date Scan", th_bottom_style)
		ws.write(rowcount, 12, "DPP", th_bottom_style)
		ws.write(rowcount, 13, "PPN", th_bottom_style)
		ws.write(rowcount, 14, "Faktur", th_bottom_style)
		ws.write(rowcount, 15, "Without Faktur", th_bottom_style)
		ws.write(rowcount, 16, "Date Payment", th_bottom_style)
		rowcount+=1
		# vatin_account_ids = data.get('vatin_account_ids',[])
		vatin_account_ids = [153,154,285,346]
		### Note : Scanned Faktur Pajak and already reported
		for fp in sorted(parser._get_faktur_pajak_reported(data), key=lambda x:x.batch_id.period_id.id):
			if not fp.nomorFaktur:
				continue
			ws.write(rowcount,0, fp.batch_id.period_id.name, normal_style)
			ws.write(rowcount,1, fp.namaPenjual, normal_style)
			ws.write(rowcount,2, "%s%s.%s-%s.%s"%(fp.kdJenisTransaksi or '00',fp.fgPengganti or '0',fp.nomorFaktur[:3],fp.nomorFaktur[3:5],fp.nomorFaktur[5:]), normal_style)
			ws.write(rowcount,3, fp.tanggalFaktur, normal_style)
			ws.write(rowcount,4, datetime.strptime(fp.tanggalFaktur,'%Y-%m-%d').strftime('%b'), normal_style)
			ws.write(rowcount,5, fp.jumlahDpp or 0.0, normal_style_float)
			ws.write(rowcount,6, fp.jumlahPpn or 0.0, normal_style_float)
			move_ppn_total = 0.0
			date_payment = False
			move_id = fp.related_invoice_id and fp.related_invoice_id.state in ('open','paid') and fp.related_invoice_id.move_id or False
			# payment date taken from account.invoice in field payment_date if there is related invoice
			if move_id:
				date_payment = fp.related_invoice_id.payment_date
			if not move_id:
				if fp.related_ext_transaksi_id:

					if fp.related_ext_transaksi_id.tax_move_id and fp.related_ext_transaksi_id.move_id and fp.related_ext_transaksi_id.move_id.id==fp.related_ext_transaksi_id.tax_move_id.id:
						move_id = fp.related_ext_transaksi_id.move_id
					elif fp.related_ext_transaksi_id.tax_move_id and fp.related_ext_transaksi_id.move_id and fp.related_ext_transaksi_id.move_id.id!=fp.related_ext_transaksi_id.tax_move_id.id:
						move_id = fp.related_ext_transaksi_id.tax_move_id
					elif fp.related_ext_transaksi_id.tax_move_id and not fp.related_ext_transaksi_id.move_id:
						move_id = fp.related_ext_transaksi_id.tax_move_id
					elif fp.related_ext_transaksi_id.move_id and not fp.related_ext_transaksi_id.tax_move_id:
						move_id = fp.related_ext_transaksi_id.move_id
					if fp.related_ext_transaksi_id.type_transaction=='payment':
						date_payment = move_id.date
			if move_id:
				move_ppn_total = sum([line.amount_currency for line in move_id.line_id if line.account_id.id in vatin_account_ids])
			ws.write(rowcount,7, move_id and move_id.name or '', normal_style)
			ws.write(rowcount,8, move_id and move_id.date or '', normal_style)
			ws.write(rowcount,9, abs(move_ppn_total) or 0.0, normal_style_float)
			ws.write(rowcount,10, move_id and "%s%s.%s-%s.%s"%(fp.kdJenisTransaksi or '00',fp.fgPengganti or '0',fp.nomorFaktur[:3],fp.nomorFaktur[3:5],fp.nomorFaktur[5:]) or "", normal_style)
			# ws.write(rowcount,11, fp.date_scan or '', normal_style)
			ws.write(rowcount,12, move_id and fp.jumlahDpp or 0.0, normal_style_float)
			ws.write(rowcount,13, move_id and fp.jumlahPpn or 0.0, normal_style_float)
			ws.write(rowcount,14, move_id and 'True' or '', normal_style)
			ws.write(rowcount,15, '', normal_style)
			ws.write(rowcount,16, date_payment or '', normal_style)
			rowcount += 1
		
		### Note : Scanned Faktur Pajak but not yet reported
		for fp in sorted(parser._get_faktur_pajak_only_invoiced(data), key=lambda x:(x.related_invoice_id and x.related_invoice_id.move_id.period_id.id or x.related_ext_transaksi_id.force_period.id)):
			if not fp.nomorFaktur:
				continue			
			ws.write(rowcount,0, 'Not Reported', normal_style)
			ws.write(rowcount,1, fp.namaPenjual, normal_style)
			ws.write(rowcount,2, "%s%s.%s-%s.%s"%(fp.kdJenisTransaksi or '00',fp.fgPengganti or '0',fp.nomorFaktur[:3],fp.nomorFaktur[3:5],fp.nomorFaktur[5:]), normal_style)
			ws.write(rowcount,3, fp.tanggalFaktur, normal_style)
			ws.write(rowcount,4, datetime.strptime(fp.tanggalFaktur,'%Y-%m-%d').strftime('%b'), normal_style)
			ws.write(rowcount,5, fp.jumlahDpp or 0.0, normal_style_float)
			ws.write(rowcount,6, fp.jumlahPpn or 0.0, normal_style_float)
			move_ppn_total = 0.0
			date_payment = False
			move_id = fp.related_invoice_id and fp.related_invoice_id.state in ('open','paid') and fp.related_invoice_id.move_id or False
			# payment date taken from account.invoice in field payment_date if there is related invoice
			if move_id:
				date_payment = fp.related_invoice_id.payment_date
			if not move_id:
				if fp.related_ext_transaksi_id:

					if fp.related_ext_transaksi_id.tax_move_id and fp.related_ext_transaksi_id.move_id and fp.related_ext_transaksi_id.move_id.id==fp.related_ext_transaksi_id.tax_move_id.id:
						move_id = fp.related_ext_transaksi_id.move_id
					elif fp.related_ext_transaksi_id.tax_move_id and fp.related_ext_transaksi_id.move_id and fp.related_ext_transaksi_id.move_id.id!=fp.related_ext_transaksi_id.tax_move_id.id:
						move_id = fp.related_ext_transaksi_id.tax_move_id
					elif fp.related_ext_transaksi_id.tax_move_id and not fp.related_ext_transaksi_id.move_id:
						move_id = fp.related_ext_transaksi_id.tax_move_id
					elif fp.related_ext_transaksi_id.move_id and not fp.related_ext_transaksi_id.tax_move_id:
						move_id = fp.related_ext_transaksi_id.move_id
					if fp.related_ext_transaksi_id.type_transaction=='payment':
						date_payment = move_id.date
			if move_id:
				move_ppn_total = sum([line.amount_currency for line in move_id.line_id if line.account_id.id in vatin_account_ids])
			ws.write(rowcount,7, move_id and move_id.name or '', normal_style)
			ws.write(rowcount,8, move_id and move_id.date or '', normal_style)
			ws.write(rowcount,9, abs(move_ppn_total) or 0.0, normal_style_float)
			ws.write(rowcount,10, "%s%s.%s-%s.%s"%(fp.kdJenisTransaksi or '00',fp.fgPengganti or '0',fp.nomorFaktur[:3],fp.nomorFaktur[3:5],fp.nomorFaktur[5:]), normal_style)
			# ws.write(rowcount,11, fp.date_scan or '', normal_style)
			ws.write(rowcount,12, fp.jumlahDpp or 0.0, normal_style_float)
			ws.write(rowcount,13, fp.jumlahPpn or 0.0, normal_style_float)
			ws.write(rowcount,14, 'True', normal_style)
			ws.write(rowcount,15, '', normal_style)
			ws.write(rowcount,16, date_payment or '', normal_style)
			rowcount += 1

		### Note : GL Taxes without Scanned Faktur
		for line in sorted(parser._get_pending_moves(data), key=lambda x:(x['move_id'].period_id.id,x['move_id'].date)):
			ws.write(rowcount,0, '', normal_style)
			ws.write(rowcount,1, '', normal_style)
			ws.write(rowcount,2, '', normal_style)
			ws.write(rowcount,3, '', normal_style)
			ws.write(rowcount,4, '', normal_style)
			ws.write(rowcount,5, '', normal_style_float)
			ws.write(rowcount,6, '', normal_style_float)
			move_ppn_total = 0.0
			date_payment = False
			move_id = line['move_id']
			# payment date taken from account.invoice in field payment_date if there is related invoice
			if line.get('related_invoice_id',False):
				date_payment = line['related_invoice_id'].payment_date
			if line.get('related_ext_transaksi_id',False) and line['related_ext_transaksi_id'].type_transaction=='payment':
				date_payment = move_id.date
			
			if move_id:
				move_ppn_total = sum([line.amount_currency for line in move_id.line_id if line.account_id.id in vatin_account_ids])
			
			ws.write(rowcount,7, move_id and move_id.name or '', normal_style)
			ws.write(rowcount,8, move_id and move_id.date or '', normal_style)
			ws.write(rowcount,9, abs(move_ppn_total) or 0.0, normal_style_float)
			ws.write(rowcount,10, '', normal_style)
			ws.write(rowcount,11, '', normal_style)
			ws.write(rowcount,12, '', normal_style_float)
			ws.write(rowcount,13, '', normal_style_float)
			ws.write(rowcount,14, '', normal_style)
			ws.write(rowcount,15, '', normal_style)
			ws.write(rowcount,16, date_payment or '', normal_style)
			rowcount += 1

		# ws.write(rowcount,0, "", subtotal_style2)
		# ws.write(rowcount,1, "", subtotal_style2)
		# ws.write(rowcount,2, "", subtotal_style2)
		# ws.write(rowcount,3, "", subtotal_style2)
		# ws.write(rowcount,4, "", subtotal_style2)
		# ws.write(rowcount,5, "", subtotal_style2)
		# # ws.write(rowcount,6, subtotal[6], subtotal_style2)
		# ws.write(rowcount,6, xlwt.Formula("SUM($G$%s:$G$%s)"%(str(start_row),str(rowcount))), subtotal_style2)
		# # ws.write(rowcount,7, subtotal[7], subtotal_style2)
		# ws.write(rowcount,7, xlwt.Formula("SUM($H$%s:$H$%s)"%(str(start_row),str(rowcount))), subtotal_style2)
		# ws.write(rowcount,8, "", subtotal_style2)
		# ws.write(rowcount,9, "", subtotal_style2)
		# ws.write(rowcount,10, "", subtotal_style2)
		# rowcount += 1
		pass

faktur_pajak_reconciliation_xls('report.faktur.pajak.reconciliation','faktur.pajak.reconciliation.wizard','addons/ad_faktur_pajak/report/faktur_pajak.mako', parser=faktur_pajak_reconciliation_parser, header=False)