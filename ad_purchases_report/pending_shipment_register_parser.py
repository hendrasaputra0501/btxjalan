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



class PendingShipmentRegister(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(PendingShipmentRegister, self).__init__(cr, uid, name, context=context)
		# print "=====================================zzzzzzzzzzzzzzzzzzzzzzz============================="
		self.localcontext.update({
			'time': time,
			# 'get_objects' : self._get_object,       
			# "get_difference": self._get_difference,
			'get_result':self._get_result,
			'get_rate':self._get_rate,
			'get_price_usd':self._get_price_usd,
		})
	# def _net_price
	def _get_price_usd(self, cury_po,company_curyid,date_order,price_unit):
		curr_obj = self.pool.get("res.currency")
		usd_amt = 0.0
		
		# company_curr = rfq.company_id and rfq.company_id.currency_id.id
		# cury_idco = curr_obj.browse(self.cr,self.uid, company_curyid)
		cury_idco = company_curyid
		# po_curr = rfq.pricelist_id and rfq.pricelist_id.currency_id and rfq.pricelist_id.currency_id.id
		# cury_id_po=curr_obj.browse(self.cr,self.uid,cury_po)
		cury_id_po=cury_po
		# ctx = {'date':sca_date!='False' and sca_date or time.strftime('%Y-%m-%d')}
		ctx={'date':date_order!='False' and date_order or time.strftime('%Y-%m-%d')}
		# usd_amt = currency_pool.compute(self.cr, self.uid, po_curr, company_curr, (price_unit or 0.0), context=ctx)
		usd_amt = curr_obj.compute(self.cr, self.uid, cury_id_po, cury_idco, (price_unit or 0.0), context=ctx)
		
		return usd_amt

	def _get_rate(self,cury_po,company_curyid,date_order):
		cr=self.cr
		uid=self.uid
		curr_obj = self.pool.get('res.currency')
		# print "============================lalalalalalalalalala---------------------------"
		ctx={'date':date_order!='False' and date_order or time.strftime('%Y-%m-%d')}
		# curry_id=company_curyid
		# cury_po=cury_po
		cury_idco = curr_obj.browse(cr, uid, company_curyid)
		cury_id_po=curr_obj.browse(cr, uid,cury_po)
		# for x in lines_po:
		# 	cury_id_po=x['currency_idpo']
		rate=curr_obj._get_conversion_rate(cr, uid,cury_id_po,cury_idco ,  context=ctx)
		# rate=curr_obj._get_conversion_rate(cr, uid,curry_id,cury_id2 ,  context=ctx)
		# print "============================lalalalalalalalalala---------------------------"
		return rate

	def _get_result(self, data):
		# print "====================wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww=========================="
		# date_start = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['date_start']
		# date_end = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['date_stop']
		date_start =data['form']['date_start']
		date_end =data['form']['date_stop']
		purchase_type = data['form']['purchase_type']
		# goods_type = data['form']['goods_type']
		if purchase_type =='all':
			purchase_type ="('local','import')"
		else:
			purchase_type = "('%s')" %purchase_type
		# print "====================xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=========================="
		# purchase_type = data['form']['purchase_type']
		# goods_type = data['form']['goods_type']
		# if purchase_type =='all':
		# 	purchase_type ="('local','import')"
		# else:
		# 	purchase_type = "('%s')" %purchase_type
		# force_picking_conditions = ""
		# if data['form']['force_picking_ids']:
		# 	force_picking_conditions = " AND b.id IN ("+','.join([str(x) for x in data['form']['force_picking_ids']])+")"
		query = "\
				select \
				pp.name_template as description\
				,pol.id as po_line_id \
				,po.name as po_number \
				,po.date_order as date_order\
				,coalesce(diskon_all.semua_diskon,'') as semua_diskon \
				,rco.currency_id as company_curry_id\
				,mrlx.name as indent_no \
				,prx.material_req_line_id \
				,prx.id \
				,pol.requisition_id \
				,rp.name as vendor \
				,rc.name as currency \
				,rc.id as currency_idpo\
				,pol.price_unit as price_unit \
				,pol.product_qty as product_qty\
				,po.payment_method as payment_method\
				,po.minimum_planned_date as etd_date\
				,po.date_approve as date_approve\
				,pol.remark as remark\
				,mrlx.dept_name as department \
				from purchase_order_line pol \
				inner join purchase_order po on pol.order_id=po.id \
				left outer join ( \
							select pr.id,prl.material_req_line_id,prl.product_id \
								from purchase_requisition pr \
								inner join purchase_requisition_line prl on pr.id=prl.requisition_id \
								where pr.state='done')prx \
									on pol.requisition_id=prx.id and pol.product_id=prx.product_id \
					\
				left outer join ( \
							select hd.name as dept_name,mrl.id,mrl.requisition_id,mrl.product_id,mr.name \
								from material_request_line mrl \
								inner join material_request mr on mrl.requisition_id=mr.id \
								left outer join hr_department hd on mr.department=hd.id \
								where mr.state='done')mrlx\
									on mrlx.id=prx.material_req_line_id and mrlx.product_id=prx.product_id \
					\
				left outer join res_partner rp on po.partner_id=rp.id \
				left outer join product_pricelist ppr on po.pricelist_id=ppr.id \
				left outer join product_product pp on pol.product_id=pp.id\
				left outer join res_currency rc on ppr.currency_id=rc.id\
				left outer join res_company rco on po.company_id=rco.id\
				left outer join ( \
							select poli.id,string_agg(diskon_table.diskon,'|') as semua_diskon \
								from purchase_order_line poli inner join ( \
									select puol.id, \
									'('''||pd.type||''','''||pd.discount_amt||''')' as diskon \
									from purchase_order_line puol \
									inner join price_discount_po_line_rel pdrel on puol.id=pdrel.po_line_id \
									inner join price_discount pd on pdrel.disc_id=pd.id \
						)diskon_table on poli.id=diskon_table.id \
						group by poli.id \
						)diskon_all on pol.id=diskon_all.id \
				where po.state='approved'  and to_char(po.date_order,'YYYY-MM-DD') >= substring('%s',1,10)\
				and to_char(po.date_order,'YYYY-MM-DD') <= substring('%s',1,10) and po.purchase_type in %s \
			"
		query = query%(date_start,date_end,purchase_type)
		print "=============",query

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res


report_sxw.report_sxw('report.pending.shipment.register.report','pending.shipment.register.wizard', 'addons/ad_purchases_report/pending_shipment_register_report.mako', parser=PendingShipmentRegister)
