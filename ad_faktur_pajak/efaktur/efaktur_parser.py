from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging
import json, ast

class EFakturParser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(EFakturParser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
		'get_invoice' : self._get_invoice,
		
		})

	def get_period(self,force_period):
		if force_period:
			return self.pool.get("account.period").browse(self.cr,self.uid,force_period)
		return False
	def get_reference(self,inv):
		reference=""
		n=0
		if inv.picking_ids:
			for pick in inv.picking_ids:
				if pick.state=='done':
					if n==0:
						reference+=pick.name
					else:
						reference+="*"+pick.name[-4:]
					n+=1
		if inv.currency_id.id != inv.company_id.tax_base_currency.id:
			reference="KMK Rate:"+str(self._get_rate_tax(inv))+"\n"+reference
		return reference[:255]
	def _get_invoice(self,data):
		cr=self.cr
		uid=self.uid
		# print "--------ddddddddddddd--------",data
		if data['filter_by']=='period':
			period = self.pool.get("account.period").browse(cr,uid,data["period_id"])
			date_start	= period.date_start
			date_end 	= period.date_stop
		elif data['filter_by']=='date_range':
			date_start	= data["date_start"]
			date_end 	= data["date_end"]
		# print "date=============>",date_start,date_end
		if data.get("invoice_ids",False):
			invoice_ids = data.get("invoice_ids",False)
		else:
			if data.get("sale_type",'local')=='local':
				invoice_ids = self.pool.get("account.invoice").search(cr,uid,[('date_invoice',">=",date_start),('date_invoice',"<=",date_end),("nomor_faktur_id","!=",False),('sale_type','=',data["sale_type"]),('goods_type','=',data["goods_type"]),("type",'=',data["type"]+"_invoice"),("state","not in",("draft","cancel"))])
			elif data.get("sale_type",'local')=='export':
				invoice_ids = self.pool.get("account.invoice").search(cr,uid,[('date_invoice',">=",date_start),('date_invoice',"<=",date_end),('sale_type','=',data["sale_type"]),('goods_type','=',data["goods_type"]),("type",'=',data["type"]+"_invoice"),("state","not in",("draft","cancel"))])

		# print "================",invoice_ids
		return self.pool.get("account.invoice").browse(cr,uid,invoice_ids)

	def _get_invoice_in(self,data):
		cr=self.cr
		uid=self.uid
		# print "--------ddddddddddddd--------",data
		if data['filter_by']=='period':
			period = self.pool.get("account.period").browse(cr,uid,data["period_id"])
			date_start	= period.date_start
			date_end 	= period.date_stop
		elif data['filter_by']=='date_range':
			date_start	= data["date_start"]
			date_end 	= data["date_end"]
		# print "date=============>",date_start,date_end
		if data.get("invoice_ids",False):
			efaktur_ids = self.pool.get("efaktur.head").search(cr,uid,[('related_invoice_id',"in",invoice_ids)])
		else:
			if not data['efaktur_heads_forced']:
				efaktur_ids1 = self.pool.get("efaktur.head").search(cr,uid,[('tanggalFaktur',">=",date_start),('tanggalFaktur',"<=",date_end),('nomorFaktur',"!=",False),('type',"=",'in')],order="tanggalFaktur asc")
				efaktur_ids2 = self.pool.get("efaktur.head").search(cr,uid,[("report_period",'=',False),('nomorFaktur',"!=",False),('type',"=",'in')],order="tanggalFaktur asc")
				efaktur_ids = efaktur_ids1+efaktur_ids2
			else:
				efaktur_ids = data['efaktur_heads_forced']
		efaktur_ids =  self.pool.get("efaktur.head").search(cr,uid,[('id','in',list(set(efaktur_ids))),('id','not in',data['efaktur_heads_exception'])],order="tanggalFaktur asc,nama_penjual asc")
		return self.pool.get("efaktur.head").browse(cr,uid,efaktur_ids)
		
	def _get_desc_line(self,inv_line):
		desc = ''
		if inv_line:
			desc += (inv_line.name and (inv_line.name + '\n') or '') 
			desc += (inv_line.quantity and (str(inv_line.quantity) + ' ') or '') 
			desc += (inv_line.uos_id and (inv_line.uos_id.name + ' ') or '') or ''
			desc += (inv_line.invoice_id and inv_line.invoice_id.currency_id and ('- ' + inv_line.invoice_id.currency_id.name + ' ') or '')
			desc += (inv_line.price_unit and (str(self._price_unit(inv_line)) + '\n') or '') 
			
			move_ids = self.pool.get('stock.move').search(self.cr,self.uid,[('invoice_line_id','=',inv_line.id),('product_id','=',inv_line.product_id.id)])
			if move_ids:
				move = self.pool.get('stock.move').browse(self.cr,self.uid,move_ids[0])
				desc += (move.picking_id and ('SJ No: ' + move.picking_id.name + ' ') or '')
				date_delivery = move.picking_id and move.picking_id.date_done!='False' and datetime.datetime.strptime(move.picking_id.date_done,'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y') or ''
				desc += (date_delivery and ('Date: ' + date_delivery + ' ') or '')
				desc += (move.picking_id and move.picking_id.sale_id and ('Ord.No: ' + move.picking_id.sale_id.name) or '')
		return desc.replace('\n','<br/>')

	def _get_rate_tax(self,inv):
		rate = 1.0
		cr = self.cr
		uid = self.uid
		# inv = self.pool.get('account.invoice').browse(self.cr,self.uid,data['id'])		
		if inv.currency_tax_id.name == 'IDR' and inv.currency_id.id==inv.company_id.currency_id.id:
			tax_date = inv.tax_date !='False' and inv.tax_date or inv.date_invoice
			tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',inv.currency_id.id),('name','<=',tax_date)])
			if tax_rate_ids:
				rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
		elif inv.currency_tax_id.name == 'IDR' and inv.currency_id.id != inv.company_id.currency_id.id and inv.currency_id.id != inv.company_id.tax_base_currency.id:
			tax_date = inv.tax_date !='False' and inv.tax_date or inv.date_invoice
			tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',inv.company_id.currency_id.id),('name','<=',tax_date)])
			if tax_rate_ids:
				rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
			# company_rate_ids = self.pool.get('res.currency.rate').search(cr, uid, [('currency_id','=',inv.company_id.currency_id.id),('name','<=',inv.date_invoice)])
			# company_rate=1.0
			# if company_rate_ids:
			# 	company_rate=company_rate_ids and self.pool.get('res.currency.rate').browse(cr,uid,company_rate_ids)[0].rate or 0.0
			# rate=rate*company_rate
		else:
			tax_date = inv.tax_date !='False' and inv.tax_date or inv.date_invoice
			tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',inv.currency_id.id),('name','<=',tax_date)])
			# print "================",tax_rate_ids
			if tax_rate_ids:
				rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
		return rate

	def get_dpp_total(self,invoice):
		tot_dpp=0.0
		cr = self.cr
		uid = self.uid
		for invoice_line in invoice.invoice_line:
			if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
				if invoice.currency_id.id == invoice.company_id.currency_id.id:
					tot_dpp+=round(invoice_line.price_subtotal*self._get_rate_tax(invoice),2)
				else:
					compute_amt = self.pool.get('res.currency').compute(cr,uid,invoice.currency_id.id,invoice.company_id.currency_id.id,invoice_line.price_subtotal,context={'date':invoice.date_invoice})
					tot_dpp+=round(compute_amt*self._get_rate_tax(invoice),2)
			else:
				tot_dpp+=round(invoice_line.price_subtotal,2)
		return int(tot_dpp)

	def get_ppn(self,invoice):
		tot_tax =0.0
		for invoice_line in invoice.invoice_line:
			if invoice_line.product_id.type != 'service':
				if invoice_line.invoice_line_tax_id:
					for t in invoice_line.invoice_line_tax_id:
						if t.type == 'percent':
							if not t.inside_berikat:
								if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
									# print "---------------",t.amount,invoice_line.price_subtotal,self._get_rate_tax(invoice),round(t.amount*invoice_line.price_subtotal*self._get_rate_tax(invoice),2)
									tot_tax+=round(t.amount*invoice_line.price_subtotal*self._get_rate_tax(invoice),2)
								else:
									tot_tax+=round(t.amount*invoice_line.price_subtotal,2)
							else:
								if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
									tot_tax+=round(t.tax_amount_kb*invoice_line.price_subtotal*self._get_rate_tax(invoice),2)
								else:
									tot_tax+=round(t.tax_amount_kb*invoice_line.price_subtotal,2)
						elif t.type == 'fixed':
							if not t.inside_berikat:
								tot_tax+=round(t.amount,2)
							else:
								tot_tax+=round(t.tax_amount_kb,2)
				else:
						tot_tax+=0

		# print "::::::::::::::::::::",tot_tax,self._get_rate_tax(invoice),invoice.amount_untaxed
		return int(round(tot_tax,0))
	
	def get_ppnbm(self,invoice):
		
		return 0.0

	def get_ppn_line(self,line):
		invoice=line.invoice_id
		tot_tax = 0.0
		for t in line.invoice_line_tax_id:
			if t.type == 'percent':
				if not t.inside_berikat:
					if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
						tot_tax+=round(t.amount*line.price_subtotal*self._get_rate_tax(invoice),2)
					else:
						tot_tax+=round(t.amount*line.price_subtotal,2)
				else:
					if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
						tot_tax+=round(t.tax_amount_kb*line.price_subtotal*self._get_rate_tax(invoice),2)
					else:
						tot_tax+=round(t.tax_amount_kb*line.price_subtotal,2)
			elif t.type == 'fixed':
				if not t.inside_berikat:
					tot_tax+=round(t.amount,2)
				else:
					tot_tax+=round(t.tax_amount_kb,2)
		return tot_tax

	def get_dpp_line(self,line):
		invoice = line.invoice_id
		dpp =0.0
		cr = self.cr
		uid = self.uid
		if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
			if invoice.currency_id.id == invoice.company_id.currency_id.id:
				dpp = round(line.price_subtotal * self._get_rate_tax(invoice),2)
			else:
				compute_amt = self.pool.get('res.currency').compute(cr,uid,invoice.currency_id.id,invoice.company_id.currency_id.id,invoice_line.price_subtotal,context={'date':invoice.date_invoice})
				dpp = round(compute_amt * self._get_rate_tax(invoice),2)
		else:
			dpp = round(line.price_subtotal,2)
		return dpp

	def get_price(self,line):
		invoice = line.invoice_id
		price =0.0
		if invoice.currency_id.id != invoice.company_id.tax_base_currency.id:
			price = line.price_subtotal * self._get_rate_tax(invoice)/line.quantity
		else:
			price = line.price_subtotal / line.quantity
		return price