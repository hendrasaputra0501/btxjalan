from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from tools.translate import _
import cStringIO
import netsvc
import tools
import decimal_precision as dp
import logging
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from collections import OrderedDict
from openerp.tools import float_compare,float_round

class DetailOutstandingFreightCost(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(DetailOutstandingFreightCost, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
		"get_result": self._get_result,
		"get_date_range":self._get_date_range,
		"aggregate_lc":self.aggregate_lc,
		"get_freight_from_invoice":self._get_freight_from_invoice,
		"get_fob_from_invoice":self._get_fob_from_invoice,
		"get_invoice_balance_outstanding":self._get_invoice_balance_outstanding
		})

	def get_currencies(self,data):
		cr = self.cr
		uid = self.uid
		currency = []
		currencies = data['form']['currency_filters']
		if currencies:
			currency = self.pool.get("res.currency").browse(cr,uid,currencies)
		else:
			user = self.pool.get("res.users").browse(cr,uid,uid)
			currency = [user.company_id.currency_id]
		return currency
	
	def _get_date_range(self,data):
		cr = self.cr
		uid = self.uid
		if data['form']['filter_by']=='dt':
			return [data['form']['date_start'],data['form']['date_stop']]
		else:
			try:
				period = self.pool.get('account.period').browse(cr,uid,data['form']['period_id'][0])
				return [period.date_start,period.date_stop]
			except:
				period = self.pool.get('account.period').browse(cr,uid,data['form']['period_id'][0])[0]
				return [period.date_start,period.date_stop]

	def aggregate_lc(self,lc_ids):
		lcs = ""
		if lc_ids:
			for lc in lc_ids:
				lcs += lc.name+", "
			lcs =lcs[:-2]
		return lcs

	def _get_result(self, data,currency_id):		
		date_range = self._get_date_range(data)
		date_start = date_range[0]
		date_end = date_range[1]
		cr = self.cr
		uid = self.uid
		if data['form']['outstanding']:
			picking_ids = self.pool.get('stock.picking').search(cr,uid,[("type",'=','out'),('sale_type','=','export'),('date_done','<=',date_end),('state','=','done')],order="name asc")
		else:
			picking_ids = self.pool.get('stock.picking').search(cr,uid,[("type",'=','out'),('sale_type','=','export'),('date_done','>=',date_start),('date_done','<=',date_end),('state','=','done')],order="name asc")
		res = False
		return_values = []
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		if picking_ids:
			res = self.pool.get('stock.picking').browse(cr,uid,picking_ids)
			for pick in res:
				found = False
				if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
					for charge in pick.invoice_id.charge_invoice_ids:
						if charge.type_of_charge.id == charge_type_id:
							if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type in ('freight','fob') and currency_id == charge.currency_id.id:
								found = True
				else:
					if pick.forwading and pick.forwading.id:
						charge = pick.forwading_charge
						if charge.currency_id.id == currency_id:
							found=True
					else:
						found = False
				# if pick.name=='BES-116-0175':
				# 	print ">>>>>>>>>>>>>>>>>>>>>>>>>>>", found
				if found:
					return_values.append(pick)

		return return_values

	def _get_invoice_balance_outstanding(self,invoice,last_pay_date,with_tax=True,computerate=False):
		#return invoice balance using invoice currency
		total_paid = 0.0
		cr = self.cr
		uid = self.uid
		total_payment = 0.0
		total_invoice = 0.0
		balance_compute = 0.0
		balance=0.0
		if invoice and invoice.payment_ids:
			total_invoice = sum([x.credit for x in invoice.move_id.line_id if x.account_id.type=='payable'] )
			for payment in invoice.payment_ids:
				if datetime.strptime(payment.date,'%Y-%m-%d')<=datetime.strptime(last_pay_date,'%Y-%m-%d'):
					total_payment += payment.debit>0.0 and payment.debit or -payment.credit
		
		balance_compute = (total_invoice - total_payment) >=0.0 and (total_invoice - total_payment) or 0.0
		
		if total_payment>total_invoice:
			balance_compute = 0.0
		
		if not computerate:
			balance=self.pool.get("res.currency").compute(cr,uid,invoice.company_id.currency_id.id,invoice.currency_id.id,balance_compute,context={'date':invoice.date_invoice})
		else:
			balance=self.pool.get("res.currency").computerate(cr,uid,invoice.company_id.currency_id.id,invoice.currency_id.id,balance_compute,context={'date':invoice.date_invoice,'reverse':False})
		if invoice.id == 5036:
			print "------------------>",balance,balance_compute,total_payment,total_invoice,"===",((balance_compute==total_invoice) and with_tax and invoice.amount_total) or ((balance_compute==total_invoice) and not with_tax and invoice.amount_untaxed) or balance

		return ((balance_compute==total_invoice) and with_tax and invoice.amount_total) or ((balance_compute==total_invoice) and not with_tax and invoice.amount_untaxed) or balance

	def _get_freight_from_invoice(self,pick,last_pay_date,currency_id):
		cr = self.cr
		uid = self.uid
		total_charge_usd = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		
		no_inv = True
		if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
			for charge in pick.invoice_id.charge_invoice_ids:
				if charge.type_of_charge.id == charge_type_id:
					if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type=='freight':
						no_inv =False
						# cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						cost = self.pool.get('account.tax').compute_all(cr, uid, [tax for tax in charge.invoice_line_tax_id if tax.tax_sign>0], charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						if charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and charge.currency_id.id == charge.company_id.tax_base_currency.id:
							ctx={'date':pick.invoice_id.date_invoice or False}
							ch = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,cost['total_included'],context=ctx)
							# print "=================",charge.id,pick.invoice_id.id
							inv_price = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,charge.invoice_id.amount_total,context=ctx)
							inv_bal = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date),context=ctx)
							total_charge_usd += ch/inv_price*(charge.invoice_id.state not in ('open','paid') and inv_price or inv_bal ) or 0.0
						elif charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and (charge.currency_id.id != charge.company_id.tax_base_currency.id) and (charge.currency_id.id != charge.company_id.currency_id.id):
							ctx={'date':pick.invoice_id.date_invoice or False}
							ch = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,cost['total_included'],context=ctx)
							inv_price = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,charge.invoice_id.amount_total,context=ctx)
							inv_bal = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date),context=ctx)
							total_charge_usd += ch/inv_price*(charge.invoice_id.state not in ('open','paid') and inv_price or inv_bal) or 0.0
						else:
							total_charge_usd += cost['total_included']/charge.invoice_id.amount_total*((charge.invoice_id.state not in ('open','paid') and charge.invoice_id.amount_total) or self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date) or 0.0)
		
		return (total_charge_usd > 0.0 and total_charge_usd) or (total_charge_usd == 0.0 and no_inv and "") or (total_charge_usd == 0.0 and not no_inv and "Paid")

	def _get_fob_from_invoice(self,pick,last_pay_date,currency_id):
		cr = self.cr
		uid = self.uid
		total_charge_usd = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		
		no_inv = True
		if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
			for charge in pick.invoice_id.charge_invoice_ids:
				if charge.type_of_charge.id == charge_type_id:
					if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type=='fob':
						no_inv =False
						# cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						cost = self.pool.get('account.tax').compute_all(cr, uid, [tax for tax in charge.invoice_line_tax_id if tax.tax_sign>0], charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						if charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and charge.currency_id.id == charge.company_id.tax_base_currency.id:
							ctx={'date':pick.invoice_id.date_invoice or False}
							ch = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,cost['total_included'],context=ctx)
							# print "=================",charge.id,pick.invoice_id.id
							inv_price = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,charge.invoice_id.amount_total,context=ctx)
							inv_bal = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date),context=ctx)
							total_charge_usd += ch/inv_price*(charge.invoice_id.state not in ('open','paid') and inv_price or inv_bal ) or 0.0
						elif charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and (charge.currency_id.id != charge.company_id.tax_base_currency.id) and (charge.currency_id.id != charge.company_id.currency_id.id):
							ctx={'date':pick.invoice_id.date_invoice or False}
							ch = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,cost['total_included'],context=ctx)
							inv_price = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,charge.invoice_id.amount_total,context=ctx)
							inv_bal = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date),context=ctx)
							total_charge_usd += ch/inv_price*(charge.invoice_id.state not in ('open','paid') and inv_price or inv_bal) or 0.0
						else:
							total_charge_usd += cost['total_included']/charge.invoice_id.amount_total*((charge.invoice_id.state not in ('open','paid') and charge.invoice_id.amount_total) or self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date) or 0.0)
		
		return (total_charge_usd > 0.0 and total_charge_usd) or (total_charge_usd == 0.0 and no_inv and "") or (total_charge_usd == 0.0 and not no_inv and "Paid")

	def _get_emkl_from_invoice(self,pick,last_pay_date):
		cr = self.cr
		uid = self.uid
		total_charge_idr = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','EMKL')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		no_inv = True
		if pick and pick.invoice_id and pick.trucking_invoice_id and pick.trucking_invoice_id.invoice_line:
			for charge in pick.trucking_invoice_id.invoice_line:
				if charge.type_of_charge.id == charge_type_id or charge.report_charge_type=='emkl':
					if charge.picking_related_id and charge.picking_related_id.id == pick.id :
						no_inv =False
						cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						if charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and charge.currency_id.id != charge.company_id.tax_base_currency.id:
							ctx={'date':pick.invoice_id.date_invoice or False}
							ch = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,charge.company_id.tax_base_currency.id,cost['total'],context=ctx)
							inv_price = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,charge.company_id.tax_base_currency.id,charge.invoice_id.amount_untaxed,context=ctx)
							inv_bal = self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,charge.company_id.tax_base_currency.id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=False),context=ctx)
							total_charge_idr += ch/inv_price*(charge.invoice_id.state not in ('open','paid') and inv_price or inv_bal) or 0.0
							# if pick.invoice_id.id==2:
							# 	print "---------EMKL 1----------",ch,inv_price,inv_bal,"=====",total_charge_idr
						else:
							total_charge_idr += cost['total']/charge.invoice_id.amount_untaxed*((charge.invoice_id.state not in ('open','paid') and charge.invoice_id.amount_untaxed) or self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=False) or 0.0)
							# if pick.invoice_id.id==2:
							# 	print "\n=======================invoice-balance================="
							# 	print "\n",self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=False)
							# 	print "\n=======================================================\n"
							# 	print "---------EMKL 2----------",cost['total'],charge.invoice_id.amount_untaxed,"=====>>>",total_charge_idr
							# 	print "\n======================end emkl2=================================\n"
		else:
			total_charge_idr = pick.trucking_charge and pick.trucking_charge.cost
		return (total_charge_idr > 0.0 and total_charge_idr) or (total_charge_idr == 0.0 and no_inv and "") or (total_charge_idr == 0.0 and not no_inv and "Paid")

	def _get_lifton_bpa(self,pick,currency_id,last_pay_date):
		cr = self.cr
		uid = self.uid
		total_charge = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Lift On Lift Off')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		found = False
		for charge in pick.lifton_bpa_id:
			for line in charge.ext_line:
				if line.ext_transaksi_id and line.picking_related_id and (line.picking_related_id.id == pick.id) and line.type_of_charge and (line.type_of_charge.id==charge_type_id):
					if charge.currency_id.id == currency_id and charge.state=='draft':
						total_charge+=line.debit and line.debit>0.0 and line.debit or (-1*line.credit) or 0.0
					elif charge.currency_id.id == currency_id and charge.state=='posted' and (line.ext_transaksi_id.date and datetime.strptime(line.ext_transaksi_id.date,'%Y-%m-%d')<=datetime.strptime(last_pay_date,'%Y-%m-%d')):
						found =True
					elif charge.currency_id.id == currency_id and charge.state=='posted' and (line.ext_transaksi_id.date and datetime.strptime(line.ext_transaksi_id.date,'%Y-%m-%d')>datetime.strptime(last_pay_date,'%Y-%m-%d')):
						total_charge+=line.debit and line.debit>0.0 and line.debit or (-1*line.credit) or 0.0
						found =True
		return (total_charge >0.0 and total_charge) or (total_charge==0.0 and found and "Paid") or (total_charge==0.0 and not found and  "")

	def _get_other_cost_from_invoice(self,pick,currency_id,last_pay_date):
		cr = self.cr
		uid = self.uid
		total_charge = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		found =False
		if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
			for charge in pick.invoice_id.charge_invoice_ids:
				if charge.type_of_charge.id == charge_type_id:
					if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type=='ocost':
						# cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						cost = self.pool.get('account.tax').compute_all(cr, uid, [tax for tax in charge.invoice_line_tax_id if tax.tax_sign>0], charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						
						if charge.currency_id.id != currency_id and charge.currency_id.id not in (charge.company_id.currency_id.id,charge.company_id.tax_base_currency.id):
							ctx={'date':pick.invoice_id.date_invoice or False,'reverse':False}
							ch = self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,currency_id,cost['total_included'],context=ctx)
							inv_price = self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,currency_id,charge.invoice_id.amount_total,context=ctx)
							inv_bal = self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,currency_id,self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=True),context=ctx)
							total_charge += ch/inv_price*(charge.invoice_id.state in ('open','paid') and inv_bal or inv_price) or 0.0
							if pick.invoice_id.id==4991:
								print "===========1==========",ch,"/",inv_price,"*",inv_bal,"|",charge.invoice_id.state,"=",total_charge
							found =True
						elif charge.currency_id.id == currency_id and charge.currency_id.id in (charge.company_id.currency_id.id,charge.company_id.tax_base_currency.id):
						 	# bals = self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=True)
						 	inv_bal = (charge.invoice_id.state not in ('open','paid') and  charge.invoice_id.amount_total or self._get_invoice_balance_outstanding(charge.invoice_id,last_pay_date,with_tax=True)) or 0.0
						 	total_charge += cost['total_included']/charge.invoice_id.amount_total*inv_bal
							found = True
							if pick.invoice_id.id==4991:
								print "===========2==========",charge.invoice_id.id,"***",cost['total_included'],'/',charge.invoice_id.amount_total,'*',inv_bal,"|",charge.invoice_id.state,"=",total_charge
						else:
							continue
		if pick.invoice_id.id ==4991:
			print "========LAST COST=====",total_charge,found
		return (total_charge >0.0 and total_charge) or (total_charge == 0.0 and found and "Paid") or (total_charge == 0.0 and not found and "") 

	def _convert_rate(self,amount,date_convert,pick):
		cr=self.cr
		uid=self.uid
		if type(amount)==float:
			ctx = {'date':date_convert or (pick.invoice_id and pick.invoice_id.tax_date or pick.invoice_id.date_invoice) or False}
			charge= self.pool.get('res.currency').compute(cr,uid,pick.company_id.tax_base_currency.id,pick.company_id.currency_id.id,amount,context=ctx)
			return charge or 0.0
		else:
			return 0.0
# report_sxw.report_sxw('report.detail.freight.cost.report','detail.freight.cost', 'addons/reporting_module/detail_freight_cost/detail_freight_cost.mako', parser=DetailFreightCost)
