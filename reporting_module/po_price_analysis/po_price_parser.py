import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class po_price_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context={}
		super(po_price_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
			'get_price_usd' : self._get_price_usd,
		})

	def _get_result(self, data, inventory_type):
		res = []
		start_date=data['start_date']
		end_date=data['end_date']
		query_issue = "\
			SELECT \
				rp.name as partner_name, coalesce(rp.partner_code,'') as partner_code, \
				pt.name as prod_name, coalesce(pp.default_code,'') as prod_code, \
				pu.name as uom, pol.product_qty as qty, \
				pol.price_unit as price_unit, rc.name as currency_name, \
				coalesce(po.name,po.name2) as po_name, to_char(po.date_order, 'DD/MM/YYYY') as po_date, \
				po.date_order as date_order ,\
				rcppr.id as po_id, \
				rcu.id as commpany_curr_id, \
				pol.price_unit-(pol.price_unit*(coalesce(disc_po.discount_amt,0)/100)) as price_after_discount \
			FROM \
				purchase_order_line pol \
				INNER JOIN purchase_order po ON pol.order_id=po.id \
				INNER JOIN product_product pp ON pol.product_id=pp.id \
				LEFT JOIN product_template pt ON pp.product_tmpl_id=pt.id \
				INNER JOIN product_uom pu ON pol.product_uom=pu.id \
				INNER JOIN product_pricelist ppr on ppr.id=po.pricelist_id \
				INNER JOIN res_currency rc on rc.id=ppr.currency_id \
				INNER JOIN res_partner rp on rp.id=po.partner_id \
				LEFT JOIN res_company rco on rco.id=po.company_id \
				LEFT JOIN res_currency rcu on rcu.id=rco.currency_id \
				LEFT JOIN res_currency rcppr on rcppr.id=ppr.currency_id \
				LEFT JOIN ( \
						select pdpol_rel.po_line_id,pd.discount_amt from price_discount_po_line_rel pdpol_rel \
						inner join price_discount pd on pdpol_rel.disc_id=pd.id \
				)disc_po on disc_po.po_line_id=pol.id \
				\
			WHERE po.date_order::date between '%s' and '%s' \
				and po.state in ('done','approved') \
				and pp.internal_type='%s' "
		query = query_issue%(start_date,end_date,inventory_type)
		if data['product_ids']:
			query += " and pp.id in ("+str(','.join([str(x) for x  in data['product_ids']]))+") "
		if data['partner_ids']:
			query += " and rp.id in ("+str(','.join([str(x) for x in data['partner_ids']]))+") "
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _get_price_usd(self,po_id,commpany_curr_id,price_unit,date_order):
		currency_pool=self.pool.get("res.currency")
		po_currency=po_id
		usd_price=0.0
		if po_currency:
			co_currency=commpany_curr_id
			price_unit=price_unit
			date_order=date_order
			usd_price=currency_pool.compute(self.cr,self.uid,po_currency,co_currency,(price_unit or 0.0), context={'date':date_order})
		return usd_price
report_sxw.report_sxw('report.po.price.analysis.report','po.price.wizard','reporting_module/po_price_analysis/po_price_report.mako', parser=po_price_parser, header=False)