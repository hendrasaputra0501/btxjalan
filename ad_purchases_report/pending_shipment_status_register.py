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



class PendingShipmentStatusRegister(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(PendingShipmentStatusRegister, self).__init__(cr, uid, name, context=context)
		# print "=====================================zzzzzzzzzzzzzzzzzzzzzzz============================="
		self.localcontext.update({
			'time': time,
			# 'get_objects' : self._get_object,       
			# "get_difference": self._get_difference,
			'get_result':self._get_result,
			# 'get_rate':self._get_rate,
			'get_price_usd':self._get_price_usd,
		})
	# def _net_price

	def _get_result(self, data):
		# print "====================wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww=========================="
		# date_start = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['date_start']
		# date_end = data['form']['filter_date']=='as_of' and data['form']['as_of_date'] or data['form']['to_date']
		# from_date =data['form']['from_date']
		# to_date =data['form']['to_date']
		# purchase_type = data['form']['purchase_type']
		filter_by=data['form']['filter_by']
		# # if purchase_type:
		# if filter_by=='po_date':
		# 	purchase_type=purchase_type[2:-2]
		# po_number=data['form']['po_number']
		# goods_type = data['form']['goods_type']
		# if purchase_type =='all':
		# 	purchase_type ="('local','import')"
		# else:
		# 	purchase_type = "('%s')" %purchase_type
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
		if filter_by=='po_date':
			from_date =data['form']['from_date']
			to_date =data['form']['to_date']
			purchase_type = data['form']['purchase_type']
			if purchase_type:
				purchase_type=purchase_type[2:-2]
			# po_number=data['form']['po_number']
			query = "\
					select \
					po.id as po_id,\
					po.name as name,\
					po.date_order as date_order, \
					po.payment_date as payment_date, \
					po.last_shipment_date as lsd, \
					po.actual_shipment_date as actual_date, \
					po.transit_shipment_date as transit_date, \
					po.document_ref as document_ref, \
					hd.name as department, \
					rp.name as vendor, \
					rp.partner_alias as partner_alias, \
					rc.name as currency, \
					rc.id as currency_idpo, \
					rco.currency_id as company_curry_id, \
					po.amount_total as amount, \
					po.pending_itemdesc as pending_itemdesc, \
					po.divy_by as divy_by, \
					po.payment_method as payment_method, \
					po.shipment_etd_dt as shipment_etd_dt, \
					po.arrival_harbour as arrival_harbour, \
					po.arrival_factory as arrival_factory, \
					po.shipment_remarks as shipment_remarks \
					from purchase_order po \
					inner join \
						( \
							\
							select po.name from purchase_order po \
							inner join ( \
										select po.name,pol.order_id,pol.id,pol.product_id,pol.product_qty,sm.product_qty,sm.picking_id,sm.location_id, COALESCE(sm.product_qty,0.0000) as qty_receipt,COALESCE(pol.product_qty,0.0000) as qty_po \
										from purchase_order_line pol \
										inner join purchase_order po on pol.order_id=po.id \
										left join \
										(select purchase_id,product_id,location_id,sum(product_qty) as product_qty,picking_id,state from stock_move \
										where location_id=8 and \
										state='done' \
										group by purchase_id,product_id,location_id,picking_id,state) \
										sm on pol.order_id=sm.purchase_id and pol.product_id=sm.product_id \
										where po.goods_type='stores' and pol.product_id is not null and pol.product_id not in(23808,23809,24838,24575)\
										\
										and ((pol.knock_off is null or pol.knock_off='f') and (to_char(pol.date_knock_off,'YYYY-MM-DD')<=substring('2016-11-30',1,10)or to_char(pol.date_knock_off,'YYYY-MM-DD') is null)) \
										\
										order by po.name \
						    			) incoming on incoming.name=po.name \
							left join \
										(		\
										select sm.purchase_Line_id,sp.name,sm.product_id,COALESCE(sm.product_qty,0.0000) as qty_return from purchase_order_line pol \
										inner join purchase_order po on pol.order_id=po.id \
										inner join \
										(select purchase_id,product_id,location_id,sum(product_qty) as product_qty,picking_id,state,purchase_Line_id from stock_move \
										where location_id<>8 and \
										state='done' \
										group by purchase_id,product_id,location_id,picking_id,state,purchase_Line_id)sm  \
										on pol.order_id=sm.purchase_id and pol.product_id=sm.product_id \
										left outer join stock_picking sp on sm.picking_id=sp.id \
										where po.goods_type='stores' and pol.product_id is not null and pol.product_id not in(23808,23809,24838,24575)\
										) smr on incoming.id=smr.purchase_Line_id and incoming.product_id=smr.product_id \
										group by po.name having sum(coalesce(incoming.qty_po,0.0000)-coalesce(incoming.qty_receipt,0.0000)-coalesce(smr.qty_return,0.0000))>0 \
						)pending_po on pending_po.name=po.name \
					left outer join res_partner rp on po.partner_id=rp.id \
					left outer join product_pricelist ppr on po.pricelist_id=ppr.id \
					left outer join res_currency rc on ppr.currency_id=rc.id \
					left outer join res_company rco on po.company_id=rco.id \
					left outer join hr_department hd on hd.id=po.department \
					\
					where po.state='approved' and po.goods_type='stores' and to_char(po.date_order,'YYYY-MM-DD') >= substring('%s',1,10)\
					and to_char(po.date_order,'YYYY-MM-DD') <= substring('%s',1,10) and po.purchase_type in ('%s') \
				"
			query = query%(from_date,to_date,purchase_type)
			print "=============",query
		else:
			po_number=data['form']['po_number']
			query = "\
					select \
					po.id as po_id,\
					po.name as name,\
					po.date_order as date_order,\
					po.payment_date as payment_date,\
					po.last_shipment_date as lsd,\
					po.actual_shipment_date as actual_date,\
					po.transit_shipment_date as transit_date,\
					po.document_ref as document_ref,\
					hd.name as department,\
					rp.name as vendor, \
					rp.partner_alias as partner_alias,\
					rc.name as currency,\
					rc.id as currency_idpo,\
					rco.currency_id as company_curry_id,\
					po.amount_total as amount,\
					po.pending_itemdesc as pending_itemdesc,\
					po.divy_by as divy_by,\
					po.payment_method as payment_method,\
					po.shipment_etd_dt as shipment_etd_dt,\
					po.arrival_harbour as arrival_harbour,\
					po.arrival_factory as arrival_factory,\
					po.shipment_remarks as shipment_remarks\
					from purchase_order po\
					left outer join res_partner rp on po.partner_id=rp.id\
					left outer join product_pricelist ppr on po.pricelist_id=ppr.id \
					left outer join res_currency rc on ppr.currency_id=rc.id\
					left outer join res_company rco on po.company_id=rco.id\
					left outer join hr_department hd on hd.id=po.department\
					\
					where po.state='approved' and po.goods_type='stores' and po.name in('%s') \
				"
			query = query%(po_number)
			print "=============",query

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		# res1=sorted(res,key=lambda m:m['po_id'])
		return res




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

	


report_sxw.report_sxw('report.pending.shipment.status.register.report','wizard.pending.shipment.status.register', 'addons/ad_purchases_report/pending_shipment_status_register.mako', parser=PendingShipmentStatusRegister)
