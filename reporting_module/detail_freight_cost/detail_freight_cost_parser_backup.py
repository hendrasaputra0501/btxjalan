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

class DetailFreightCost(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(DetailFreightCost, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
		"get_result": self._get_result,
		"get_date_range":self._get_date_range,
		"aggregate_lc":self.aggregate_lc,
		"get_freight_from_invoice":self._get_freight_from_invoice,
		})


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

	def _get_result(self, data):
		date_range = self._get_date_range(data)
		date_start = date_range[0]
		date_end = date_range[1]
		cr = self.cr
		uid = self.uid
		picking_ids = self.pool.get('stock.picking').search(cr,uid,[("type",'=','out'),('sale_type','=','export'),('date_done','>=',date_start),('date_done','<=',date_end),('state','=','done')],order="name asc")
		res = False
		if picking_ids:
			res = self.pool.get('stock.picking').browse(cr,uid,picking_ids)
		return res

	def _get_freight_from_invoice(self,pick):
		cr = self.cr
		uid = self.uid
		total_charge_usd = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
			for charge in pick.invoice_id.charge_invoice_ids:
				if charge.type_of_charge.id == charge_type_id:

					if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type=='freight':
						cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						if charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and charge.currency_id.id == charge.company_id.tax_base_currency.id:
							#ctx = {'reverse':True,'date':pick.invoice_id and pick.invoice_id.tax_date or pick.invoice_id.date_invoice or False}
							#total_charge_usd += self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,charge.company_id.currency_id.id,charge.price_subtotal,context=ctx)
							ctx={'date':pick.invoice_id.date_invoice or False}
							total_charge_usd += self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,charge.company_id.currency_id.id,cost['total_included'],context=ctx)
						elif charge.currency_id and charge.company_id and charge.company_id.tax_base_currency and (charge.currency_id.id != charge.company_id.tax_base_currency.id) and (charge.currency_id.id != charge.company_id.currency_id.id):
							ctx={'date':pick.invoice_id.date_invoice or False}
							total_charge_usd += self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,charge.company_id.currency_id.id,cost['total_included'],context=ctx)
						else:
							if pick.invoice_id.id==5318:
								print "=======freight invoice========",charge.invoice_id.id,cost
							total_charge_usd += cost['total_included']
						
		return total_charge_usd	

	def _get_lifton_bpa(self,pick,currency_id):
		# print "=================",currency_id,pick.id
		cr = self.cr
		uid = self.uid
		total_charge = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Lift On Lift Off')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id
		for charge in pick.lifton_bpa_id:
			for line in charge.ext_line:
				if line.picking_related_id and (line.picking_related_id.id == pick.id) and line.type_of_charge and (line.type_of_charge.id==charge_type_id):
					if charge.currency_id.id == currency_id:
						total_charge+=line.debit and line.debit>0.0 and line.debit or (-1*line.credit) or 0.0
						# print "------------1",total_charge
					# else:
					# 	ctx={'date':charge.date or pick.invoice_id.date_invoice or False}
					# 	total_charge += self.pool.get('res.currency').compute(cr,uid,charge.currency_id.id,currency_id,(line.debit and line.debit>0.0 and line.debit or (-1*line.credit) or 0.0) ,context=ctx)	
						# print "------------2",total_charge
		# print "------------3",total_charge
		return total_charge

	def _get_other_cost_from_invoice(self,pick,currency_id):
		cr = self.cr
		uid = self.uid
		total_charge = 0.0
		charge_type_id = self.pool.get('charge.type').search(cr,uid,[('name','=','Freight')])
		try:
			charge_type_id = charge_type_id[0]
		except:
			charge_type_id = charge_type_id

		if pick and pick.invoice_id and pick.invoice_id.charge_invoice_ids:
			for charge in pick.invoice_id.charge_invoice_ids:
				if charge.type_of_charge.id == charge_type_id:
					#####################
					# check difference between freight and other cost
					#####################
					if charge.picking_related_id and charge.picking_related_id.id == pick.id and charge.report_charge_type=='ocost':
						cost = self.pool.get('account.tax').compute_all(cr, uid, charge.invoice_line_tax_id, charge.price_unit, charge.quantity, product=None, partner=None, force_excluded=False)
						if charge.currency_id and charge.currency_id.id == currency_id:
							total_charge += cost['total_included']
						elif charge.currency_id and (charge.currency_id.id != currency_id) and (charge.currency_id.id in (charge.company_id.currency_id.id,charge.company_id.tax_base_currency.id)):
							# ctx = {'reverse':True,'date':pick.invoice_id and pick.invoice_id.tax_date or pick.invoice_id.date_invoice or False}
							# total_charge += self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,charge.company_id.currency_id.id,charge.price_subtotal,context=ctx)
							continue
						elif charge.currency_id and (charge.currency_id.id != currency_id) and (currency_id==charge.company_id.currency_id.id) and (charge.currency_id.id not in (charge.company_id.currency_id.id,charge.company_id.tax_base_currency.id)):
							ctx={'date':pick.invoice_id.date_invoice or False}
							total_charge += self.pool.get('res.currency').computerate(cr,uid,charge.currency_id.id,charge.company_id.currency_id.id,cost['total_included'],context=ctx)
		return total_charge	

	def _convert_rate(self,amount,date_convert,pick):
		cr=self.cr
		uid=self.uid
		ctx = {'date':date_convert or (pick.invoice_id and pick.invoice_id.tax_date or pick.invoice_id.date_invoice) or False}
		# print "------------------------",pick.name,amount
		charge= self.pool.get('res.currency').compute(cr,uid,pick.company_id.tax_base_currency.id,pick.company_id.currency_id.id,amount,context=ctx)
		return charge or 0.0

# report_sxw.report_sxw('report.detail.freight.cost.report','detail.freight.cost', 'addons/reporting_module/detail_freight_cost/detail_freight_cost.mako', parser=DetailFreightCost)
