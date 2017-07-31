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
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class otif_parser(report_sxw.rml_parse):
	def __init__(self,cr,uid,name,context=None):
		super(otif_parser,self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'xdate' : self._xdate,
			'get_view' : self._get_view,
			'xdatetime' : self._xdatetime,
		})

	def _xdatetime(self,x):
		try:
			x1=x[:10]
		except:
			x1=''
		try:
			y=datetime.strftime(x1,'%Y-%m,%d').strptime('%Y,%m,%d')
		except:
			y=x1
		return y

	def _xdate(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
		except:
			y = x1
		return y

	def _get_view(self,data,context=None):
		if data['sale_type']=='export':
			query = " select smp.id,\
						smp.name as sj_name,\
						to_char(smp.date_done,'YYYY-MM-DD') as sj_date,\
						smp.container_number as container_no,\
						smp.shipping_line,\
						coalesce(cast(smp.container_size as decimal),0.0) as container_size, \
						smp.container as show_container_size,\
						smp.partner,\
						UPPER(smp.destination) as destination, \
						sor.contract_no as contract_no,\
						sor.contractline_no as contractline_no, \
						sor.date_order as date_order,\
						smp.invoice_no, \
						smp.invoice_date,\
						smp.bl_number, \
						smp.bl_date,\
						coalesce(round(sum(smp.qty_inv),2),0.00) as shipment_kg, \
						\
						coalesce(round(sum(smp.qty_bales_inv),2),0.00) as shipment_bales, \
						\
						coalesce(round(sum((smp.price_unit/smp.rate)*smp.qty_inv),2),0.00) as shipment_usd,  \
						coalesce(round(sum(smp.price_unit*smp.qty_inv),2),0.0000) as shipment_currency, \
						smp.etd, \
						smp.eta, \
						smp.name_template as count, \
						lclpl.nego_bank as nego_bank, \
						lclpl.lc_number, \
						lclpl.lctt_date,\
						smp.bank_negotiation_date as bank_negotiation_date,\
						\
						smp.lot_no, \
						sor.sol_lsd \
						from \
						( \
						\
						\
							select asp.id,smpu.name_template,smpu.sale_line_id,smpu.picking_id,\
							smpu.product_id, aiail.price_unit as price_unit, \
							asp.name,asp.date_done,asp.container_number ,asp.shipping_lines,b.name shipping_line, \
							asp.container_size,asp.container , \
							c.name as partner, rp.destination, \
							aiail.internal_number as invoice_no,  aiail.date_invoice as invoice_date,aiail.bl_number as bl_number, \
							aiail.bl_date as bl_date, smpu.lc_product_line_id, \
							asp.estimation_deliv_date as etd,asp.estimation_arriv_date as eta,aiail.bank_negotiation_date, asp.sale_type, \
							aiail.rate,sum(aiail.qty_inv) as qty_inv,\
							\
							sum(aiail.qty_bales_inv) as qty_bales_inv, \
							\
							string_agg(asp.lot_no,',') as lot_no\
							\
							from \
							(select pp.name_template,sm.sale_line_id,sm.picking_id,sm.product_id,sm.invoice_line_id,case when pu.name='LBS' \
								then coalesce(sm.price_unit,0.0)/2.2046 \
								when pu.name='BALES' then coalesce(sm.price_unit,0.0)*(400/2.2046) \
								else coalesce(sm.price_unit,0.0) \
								end as price_unit , \
								\
								sm.lc_product_line_id \
							from \
							(select distinct invoice_line_id,picking_id,product_id,sale_line_id,lc_product_line_id,product_uom,price_unit from stock_move group by invoice_line_id,picking_id,product_id,lc_product_line_id,sale_line_id,product_uom,price_unit) sm \
							inner join product_product pp on sm.product_id=pp.id \
							left outer join product_uom pu on sm.product_uom=pu.id \
							left outer join(select category_id,min(factor) as factor \
													   from product_uom \
													   where name = 'KGS' \
										group by category_id)pru on pru.category_id=pu.category_id \
							where coalesce(sm.sale_line_id,0) <> 0 \
							)smpu \
							left outer join (\
								select smo.product_id,stp.id,stp.name,smo.invoice_line_id, \
									spstmo.sequence_line,spstmo.container_size,spstmo.container,\
									stp.invoice_id,stp.shipping_lines,stp.partner_id,stp.forwading_charge,stp.container_book_id,\
									stp.date_done,stp.container_number,stp.estimation_deliv_date, \
									stp.estimation_arriv_date,stp.sale_type \
									\
									\
									,coalesce(stg.alias,stg.name) as lot_no \
									from stock_picking stp inner join stock_move smo on stp.id=smo.picking_id \
									left outer join stock_tracking stg on smo.tracking_id=stg.id \
									left outer join \
									\
										( \
										select sp.id,min(stmo.sequence_line) as sequence_line,min(sp.teus) as container_size,sp.name as container \
										from (select stp.id,cs.name,cs.teus from stock_picking stp \
										left outer join container_size cs on stp.container_size=cs.id) sp inner join stock_move stmo on stmo.picking_id=sp.id \
									\
										group by sp.id,sp.name \
										) spstmo on spstmo.id=stp.id and spstmo.sequence_line=smo.sequence_line  \
										\
										group by smo.product_id,stp.id,stp.name,smo.invoice_line_id, \
									spstmo.sequence_line,spstmo.container_size,spstmo.container, \
									stp.invoice_id,stp.shipping_lines,stp.partner_id,stp.forwading_charge,stp.container_book_id, \
									stp.date_done,stp.container_number,stp.estimation_deliv_date, \
									stp.estimation_arriv_date,stp.sale_type,\
									coalesce(stg.alias,stg.name) \
									\
											order by stp.name,spstmo.container_size asc) \
								asp on smpu.picking_id=asp.id and smpu.product_id=asp.product_id and smpu.invoice_line_id=asp.invoice_line_id \
							inner join \
								(select ail.id as invoice_line_id,aicr.id,aicr.internal_number,aicr.date_invoice,aicr.bl_number,aicr.bl_date,aicr.bank_negotiation_date, \
									ail.product_id,(ail.quantity/pu.factor)*pru.factor as qty_inv, \
									\
									(ail.quantity/pu.factor)*pu_bales.factor as qty_bales_inv,\
									\
									\
									(ail.price_unit*pu.factor)*pru.factor as price_unit ,aicr.rate \
									from \
										(\
										select ai.currency_id,rcrcr.name,rcrcr.rate,rcrcr.name,ai.id,ai.internal_number,ai.bl_number,ai.bl_date,ai.bank_negotiation_date,ai.date_invoice from account_invoice ai left join ( \
							select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
							from account_invoice inv \
								inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
							where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
							and inv.type='out_invoice' and inv.goods_type='finish' \
							and inv.sale_type = '%s' \
							group by inv.id,rcrinv.currency_id \
							) rcrai on rcrai.id = ai.id \
						left join res_currency_rate rcrcr on rcrcr.currency_id = ai.currency_id and rcrai.curr_date = rcrcr.name \
						where ai.type='out_invoice' and ai.goods_type='finish'\
						group by ai.id,rcrcr.name,rcrcr.rate,rcrcr.name,ai.id,ai.internal_number \
						order by ai.internal_number) \
										 aicr inner join account_invoice_line ail on aicr.id=ail.invoice_id \
									left outer join product_uom pu on ail.uos_id=pu.id \
									left outer join(select category_id,min(factor) as factor \
											from product_uom where name = 'KGS' \
											group by category_id)pru on pru.category_id=pu.category_id \
						\
						left outer join(select category_id,min(factor) as factor \
										from product_uom where name = 'BALES' \
										group by category_id)pu_bales on pu_bales.category_id=pu.category_id \
						\
								) aiail \
									on asp.invoice_id=aiail.id and asp.product_id=aiail.product_id and aiail.invoice_line_id=asp.invoice_line_id \
							left outer join stock_transporter b on asp.shipping_lines=b.id  \
							left outer join res_partner c on asp.partner_id=c.id \
							left outer join \
							(select stc.id,stc.port_id,rpt.name as destination from stock_transporter_charge stc \
								left outer join res_port rpt on stc.port_id=rpt.id) rp on asp.forwading_charge=rp.id \
							inner join \
							container_booking cb  on asp.container_book_id=cb.id\
							\
							\
							group by name_template,asp.id,smpu.name_template,smpu.sale_line_id,smpu.picking_id,smpu.product_id, \
							asp.name,asp.date_done,asp.container_number ,asp.shipping_lines,b.name ,shipping_line, \
							c.name, rp.destination, asp.container_size, asp.container, \
							aiail.internal_number,  aiail.date_invoice, aiail.bl_number, aiail.bl_date, aiail.price_unit, \
							asp.estimation_deliv_date,asp.estimation_arriv_date,aiail.bank_negotiation_date, asp.sale_type,smpu.lc_product_line_id,  \
							aiail.rate \
							\
							\
							 \
							\
						)smp inner join \
						(select so.name as contract_no,sol.id as sol_id,sol.sequence_line as contractline_no,sol.product_id as sol_product_id,sol.order_id as sol_order_id,so.date_order, sol.est_delivery_date as sol_lsd \
					from sale_order_line sol inner join sale_order so on sol.order_id=so.id )sor on \
					 smp.sale_line_id=sor.sol_id and smp.product_id=sor.sol_product_id \
					 left outer join (select lcr.lc_id as order_id,lcpb.lc_number,lcpb.name as nego_bank,lpl.id,lpl.product_id,lpl.est_delivery_date as lctt_date \
										from sale_order_letterofcredit_rel lcr \
										inner join \
											(select lc.id,rb.name,lc.lc_number,lc.negotiate_bank,lc.state from letterofcredit lc \
												left outer join res_bank rb on lc.negotiate_bank=rb.id \
											)lcpb on lcr.order_id=lcpb.id \
												inner join letterofcredit_product_line lpl on lcpb.id = lpl.lc_id \
												where lcpb.state not in ('nonactive') \
									)lclpl on lclpl.order_id=sor.sol_order_id and lclpl.product_id=sor.sol_product_id  and lclpl.id= smp.lc_product_line_id \
						\
					where  to_char(smp.date_done,'YYYY-MM-DD') >= substring('%s',1,10) \
					and to_char(smp.date_done,'YYYY-MM-DD') <= substring('%s',1,10) \
					and smp.sale_type='%s' \
					 group by smp.invoice_no,\
						smp.name,\
						smp.id,\
						smp.date_done,\
						smp.container_number,\
						smp.shipping_line,\
						smp.container_size,\
						smp.container,\
						smp.partner,\
						smp.destination,\
						sor.contract_no,\
						sor.contractline_no,\
						sor.date_order,\
						smp.invoice_no,\
						smp.invoice_date, \
						smp.bl_number, \
						smp.bl_date, \
						 \
						smp.etd,\
						smp.eta,\
						smp.name_template, \
						lclpl.nego_bank, \
						lclpl.lc_number, \
						lclpl.lctt_date, \
						smp.bank_negotiation_date,\
						\
						smp.lot_no,sor.sol_lsd\
						order by to_char(smp.date_done,'YYYY-MM-DD'),smp.name,smp.invoice_no,smp.container asc"%(data['sale_type'],data['date_from'],data['date_to'],data['sale_type']) 
		else:
			query = " select smp.id,\
						smp.name as sj_name,\
						to_char(smp.date_done,'YYYY-MM-DD') as sj_date,\
						smp.container_number as container_no,\
						smp.shipping_line,\
						coalesce(cast(smp.container_size as decimal),0.0) as container_size, \
						smp.container as show_container_size,\
						smp.partner,\
						sor.contract_no as contract_no,\
						sor.contractline_no as contractline_no, \
						sor.date_order as date_order, \
						smp.invoice_no, \
						smp.invoice_date,\
						smp.bl_number, \
						smp.bl_date,\
						coalesce(round(sum(smp.qty_inv),2),0.0000) as shipment_kg, \
						\
						coalesce(round(sum(smp.qty_bales_inv),2),0.00) as shipment_bales, \
						\
						coalesce(round(sum((smp.price_unit/smp.rate)*smp.qty_inv),2),0.0000) as shipment_usd,  \
						coalesce(round(sum(smp.qty_inv/181.44),2),0.00) as shipment_bales,\
						coalesce(round(sum(smp.price_unit*smp.qty_inv),2),0.00) as shipment_currency, \
						smp.etd, \
						smp.eta, \
						smp.name_template as count, \
						lclpl.nego_bank as nego_bank, \
						lclpl.lc_number, \
						lclpl.lctt_date, \
						smp.bank_negotiation_date as bank_negotiation_date,\
						\
						smp.lot_no, \
						sor.sol_lsd, \
						smp.destination, \
						smp.truck_number,\
						smp.transporter_name\
						from \
						( \
						\
						\
							select asp.id,smpu.name_template,smpu.sale_line_id,smpu.picking_id,\
							smpu.product_id, aiail.price_unit as price_unit, \
							asp.name,asp.date_done,asp.container_number ,asp.shipping_lines,b.name shipping_line, \
							asp.container_size,asp.container , \
							c.name as partner, \
							aiail.internal_number as invoice_no,  aiail.date_invoice as invoice_date,aiail.bl_number as bl_number, \
							aiail.bl_date as bl_date, smpu.lc_product_line_id, \
							asp.estimation_deliv_date as etd,asp.estimation_arriv_date as eta,aiail.bank_negotiation_date, asp.sale_type, \
							aiail.rate,sum(aiail.qty_inv) as qty_inv,\
							\
							sum(aiail.qty_bales_inv) as qty_bales_inv, \
							\
							string_agg(asp.lot_no,',') as lot_no,\
							asp.destination, \
							asp.truck_number,asp.transporter_name\
							from \
							(select pp.name_template,sm.sale_line_id,sm.picking_id,sm.product_id,sm.invoice_line_id,case when pu.name='LBS' \
								then coalesce(sm.price_unit,0.0)/2.2046 \
								when pu.name='BALES' then coalesce(sm.price_unit,0.0)*(400/2.2046) \
								else coalesce(sm.price_unit,0.0) \
								end as price_unit , \
								\
								sm.lc_product_line_id \
							from \
							(select distinct invoice_line_id,picking_id,product_id,sale_line_id,lc_product_line_id,product_uom,price_unit from stock_move group by invoice_line_id,picking_id,product_id,lc_product_line_id,sale_line_id,product_uom,price_unit) sm \
							inner join product_product pp on sm.product_id=pp.id \
							left outer join product_uom pu on sm.product_uom=pu.id \
							left outer join(select category_id,min(factor) as factor \
													   from product_uom \
													   where name = 'KGS' \
										group by category_id)pru on pru.category_id=pu.category_id \
							where coalesce(sm.sale_line_id,0) <> 0 \
							)smpu \
							left outer join ( \
								select smo.product_id,stp.id,stp.name,smo.invoice_line_id, \
									spstmo.sequence_line,spstmo.container_size,spstmo.container,\
									stp.invoice_id,stp.shipping_lines,stp.partner_id,stp.forwading_charge,stp.container_book_id, \
									stp.date_done,stp.container_number,stp.estimation_deliv_date, \
									stp.estimation_arriv_date,stp.sale_type \
									\
									\
									,coalesce(stg.alias,stg.name) as lot_no \
									\
									,stc.name as destination \
									 ,stp.truck_number\
									 ,rpa.name as transporter_name\
									from stock_picking stp inner join stock_move smo on stp.id=smo.picking_id \
									left outer join stock_tracking stg on smo.tracking_id=stg.id \
									left outer join \
									\
										( \
										select sp.id,min(stmo.sequence_line) as sequence_line,min(sp.teus) as container_size,sp.name as container \
										from (select stp.id,cs.name,cs.teus from stock_picking stp \
										left outer join container_size cs on stp.container_size=cs.id) sp inner join stock_move stmo on stmo.picking_id=sp.id \
										\
										group by sp.id,sp.name \
										) spstmo on spstmo.id=stp.id and spstmo.sequence_line=smo.sequence_line \
										left outer join stock_transporter_charge stc on stp.trucking_charge=stc.id \
										left outer join stock_transporter sttr  on stp.trucking_company=sttr.id\
										left outer join res_partner rpa on sttr.partner_id=rpa.id\
										where stp.goods_type='finish' \
										\
										group by smo.product_id,stp.id,stp.name,smo.invoice_line_id, \
									spstmo.sequence_line,spstmo.container_size,spstmo.container, \
									stp.invoice_id,stp.shipping_lines,stp.partner_id,stp.forwading_charge,stp.container_book_id, \
									stp.date_done,stp.container_number,stp.estimation_deliv_date, \
									stp.estimation_arriv_date,stp.sale_type, \
									coalesce(stg.alias,stg.name),stc.name,stp.truck_number,rpa.name \
									\
											order by stp.name,spstmo.container_size asc) \
								asp on smpu.picking_id=asp.id and smpu.product_id=asp.product_id and smpu.invoice_line_id=asp.invoice_line_id \
							inner join \
								(select ail.id as invoice_line_id,aicr.id,aicr.internal_number,aicr.date_invoice,aicr.bl_number,aicr.bl_date,aicr.bank_negotiation_date, \
									ail.product_id,(ail.quantity/pu.factor)*pru.factor as qty_inv, \
									\
									(ail.quantity/pu.factor)*pu_bales.factor as qty_bales_inv,\
									\
									\
									(ail.price_unit*pu.factor)*pru.factor as price_unit ,aicr.rate \
									from \
										(\
										select ai.currency_id,rcrcr.name,rcrcr.rate,rcrcr.name,ai.id,ai.internal_number,ai.bl_number,ai.bl_date,ai.bank_negotiation_date,ai.date_invoice from account_invoice ai left join ( \
							select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
							from account_invoice inv \
								inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
							where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
							and inv.type='out_invoice' and inv.goods_type='finish' \
							and inv.sale_type = '%s' \
							group by inv.id,rcrinv.currency_id \
							) rcrai on rcrai.id = ai.id \
						left join res_currency_rate rcrcr on rcrcr.currency_id = ai.currency_id and rcrai.curr_date = rcrcr.name \
						where ai.type='out_invoice' and ai.goods_type='finish' \
						group by ai.id,rcrcr.name,rcrcr.rate,rcrcr.name,ai.id,ai.internal_number \
						order by ai.internal_number) \
										 aicr inner join account_invoice_line ail on aicr.id=ail.invoice_id \
									left outer join product_uom pu on ail.uos_id=pu.id \
									left outer join(select category_id,min(factor) as factor \
											from product_uom where name = 'KGS' \
											group by category_id)pru on pru.category_id=pu.category_id \
							\
									left outer join(select category_id,min(factor) as factor \
										from product_uom where name = 'BALES' \
										group by category_id)pu_bales on pu_bales.category_id=pu.category_id \
							\
								) aiail \
									on asp.invoice_id=aiail.id and asp.product_id=aiail.product_id and aiail.invoice_line_id=asp.invoice_line_id \
							left outer join stock_transporter b on asp.shipping_lines=b.id  \
							left outer join res_partner c on asp.partner_id=c.id \
							\
							\
							group by name_template,asp.id,smpu.name_template,smpu.sale_line_id,smpu.picking_id,smpu.product_id, \
							asp.name,asp.date_done,asp.container_number ,asp.shipping_lines,b.name ,shipping_line, \
							c.name,   asp.container_size, asp.container, \
							aiail.internal_number,  aiail.date_invoice, aiail.bl_number, aiail.bl_date, aiail.price_unit, \
							asp.estimation_deliv_date,asp.estimation_arriv_date,aiail.bank_negotiation_date, asp.sale_type,smpu.lc_product_line_id,  \
							aiail.rate ,asp.destination,asp.truck_number,asp.transporter_name \
							\
							\
							 \
							\
						)smp inner join \
						(select sol.id as sol_id,so.name as contract_no,sol.sequence_line as contractline_no,sol.product_id as sol_product_id,sol.order_id as sol_order_id,so.date_order, sol.est_delivery_date as sol_lsd \
					from sale_order_line sol inner join sale_order so on sol.order_id=so.id )sor on \
					 smp.sale_line_id=sor.sol_id and smp.product_id=sor.sol_product_id \
					 left outer join (select lcr.lc_id as order_id,lcpb.lc_number,lcpb.name as nego_bank,lpl.id,lpl.product_id ,lpl.est_delivery_date as lctt_date \
										from sale_order_letterofcredit_rel lcr \
										inner join \
											(select lc.id,rb.name,lc.lc_number,lc.negotiate_bank,lc.state from letterofcredit lc \
												left outer join res_bank rb on lc.negotiate_bank=rb.id \
											)lcpb on lcr.order_id=lcpb.id \
												inner join letterofcredit_product_line lpl on lcpb.id = lpl.lc_id \
												where lcpb.state not in ('nonactive') \
									)lclpl on lclpl.order_id=sor.sol_order_id and lclpl.product_id=sor.sol_product_id  and lclpl.id= smp.lc_product_line_id \
						\
					where  to_char(smp.date_done,'YYYY-MM-DD') >= substring('%s',1,10) \
					and to_char(smp.date_done,'YYYY-MM-DD') <= substring('%s',1,10) \
					and smp.sale_type='%s' \
					 group by smp.invoice_no,\
						smp.name,\
						smp.id,\
						smp.date_done,\
						smp.container_number,\
						smp.shipping_line,\
						smp.container_size,\
						smp.container,\
						smp.partner,\
						sor.contract_no,\
						sor.contractline_no,\
						sor.date_order, \
						smp.invoice_no,\
						smp.invoice_date, \
						smp.bl_number, \
						smp.bl_date, \
						 \
						smp.etd,\
						smp.eta,\
						smp.name_template, \
						lclpl.nego_bank, \
						lclpl.lc_number, \
						lclpl.lctt_date, \
						smp.bank_negotiation_date,\
						\
						smp.lot_no,sor.sol_lsd\
						smp.destination,\
						smp.truck_number,\
						smp.transporter_name\
						order by to_char(smp.date_done,'YYYY-MM-DD'),smp.name,smp.invoice_no,smp.container asc"%(data['sale_type'],data['date_from'],data['date_to'],data['sale_type']) 					

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		# print res,"dadadadadaddad"
		return res

class otif_parser_xls(report_xls):
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
		if data['sale_type']=='export':
			wr=wb.add_sheet(('OTIF - Export'))
		else:
			wr=wb.add_sheet(('OTIF -Local'))

		otif_data = parser._get_view(data)
		title_style = xlwt.easyxf('font: name Calibri , colour_index black; align: vert centre, horiz center;')
		titletop_style = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin;')
		titletop_border_btm_style = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		titlebottom_style = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: bottom thin;')
		subtotal_style = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' "borders: top thin,bottom thin; pattern: pattern solid, fore_color gray25;", num_format_str='#,##0.0000;(#,##0.0000)')
		float_style = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;', num_format_str='#,##0.0000;(#,##0.0000)')
		normal_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;')

		wr.write_merge(0,0,0,12, "PT. BITRATEX INDUSTRIES", title_style)
		wr.write_merge(1,1,0,12, parser._xdate(data['sale_type'].upper())+" OTIF REPORT "+parser._xdate(data['date_from'])+ " AND " +parser._xdate(data['date_to']), title_style)
		
		wr.write(2,0, "NO.", titletop_style)
		wr.write_merge(2,2,1,2,"CUSTOMER", titletop_border_btm_style)
		wr.write(2,3,"CONTRACT NO",titletop_style)
		wr.write(2,4,"SC DATE",titletop_style)
		wr.write(2,5,"COUNT",titletop_style)
		wr.write(2,6,"QTY BALES",titletop_style)
		wr.write(2,7,"LSD SC",titletop_style)
		wr.write(2,8,"LC/TT",titletop_style)
		wr.write_merge(2,2,9,10,"DISPACT DETAILS",titletop_border_btm_style)
		wr.write(2,11,"DIFFERENCE",titletop_style)
		# wr.write(2,6,"ETD",titletop_style)
		# wr.write(2,7,"ETA",titletop_style)
		# wr.write_merge(2,2,8,9,"SC",titletop_border_btm_style)
		# wr.write(2,10,"LC/TT",titletop_style)
		wr.write(2,12,"REMARK",titletop_style)

		wr.write(3,0, "", titlebottom_style)
		wr.write(3,1, "NAME", titlebottom_style)
		wr.write(3,2, "POD", titlebottom_style)
		wr.write(3,3, "", titlebottom_style)
		wr.write(3,4, "", titlebottom_style)
		wr.write(3,5, "", titlebottom_style)
		wr.write(3,6, "", titlebottom_style)
		wr.write(3,7, "", titlebottom_style)
		wr.write(3,8, "DATE", titlebottom_style)
		wr.write(3,9, "ETD", titlebottom_style)
		wr.write(3,10, "ETA", titlebottom_style)
		wr.write(3,11, "ETD - LSD LC/TT", titlebottom_style)
		wr.write(3,12, "", titlebottom_style)

		# wr.col(0).width = len("ABCDEFG")*160
		# wr.col(1).width = (wr.col(0).width)*50
		# wr.col(2).width = (wr.col(0).width)*3+300
		# wr.col(3).width = (wr.col(0).width)*3+800
		max_widt_col0=len('No.')
		max_widt_col1=len('name')
		max_widt_col2=len('Destination')
		max_widt_col3=len('CONTRACT NO.')
		max_widt_col5=len('COUNT')
		max_widt_col4=len('SC DATE')
		max_widt_col8=len('LC/TT')
		max_widt_col11=len('ETD - LSD LC/TT')



		sn=0
		rowcount=4
		totbales_qty=0
		for x in otif_data:
			# print x['etd'],"lalalalalallalaalalallalaal"
			# print x['lctt_date'],"jajajajajjajaja"
			# print datetime.strptime(x['etd'],'%Y-%m-%d %H:%M:%S'),"zazazazazazaza"
			# strptime(x1,'%Y-%m-%d')
			# if x['lctt_date']:
			# 	print datetime.strptime(x['lctt_date'] ,'%Y-%m-%d'),"mamamamamamaamama"
			# 	print datetime.strptime(x['etd'],'%Y-%m-%d %H:%M:%S')-datetime.strptime(x['lctt_date'] ,'%Y-%m-%d'),"nanananananana"
			# print parser._xdate(x['lctt_date']),"blalablalla"
			# print 
			content_diffdate="-"
			etd_date=datetime.strptime(x['etd'],'%Y-%m-%d %H:%M:%S')
			if x['lctt_date']:
				lctt_date=datetime.strptime(x['lctt_date'] ,'%Y-%m-%d')
				diff_date=etd_date-lctt_date
				# print diff_date.days,"kakakakaka"
				content_diffdate=diff_date.days
			# print content_diffdate,"xaxaxaxaxaxaxa"
			wr.write(rowcount,1, x['partner'])
			if len(x['partner'])>max_widt_col1:
				max_widt_col1=len(x['partner'])
			wr.write(rowcount,2,x['destination'])
			if len(x['destination']or '')>max_widt_col2:
				max_widt_col2=len(x['destination'])
			wr.write(rowcount,3,x['contractline_no'])
			if len(x['contractline_no'])>max_widt_col3:
				max_widt_col3=len(x['contractline_no'])
			wr.write(rowcount,4,parser._xdate(x['date_order']))

				
			wr.write(rowcount,5,x['count'])
			if len(x['count'])>max_widt_col5:
				max_widt_col5=len(x['count'])
			wr.write(rowcount,6,x['shipment_bales'],float_style)
			wr.write(rowcount,7,parser._xdate(x['sol_lsd']))
			wr.write(rowcount,8,parser._xdate(x['lctt_date']))
			wr.write(rowcount,9,parser._xdate(x['etd']))
			wr.write(rowcount,10,parser._xdate(x['eta']))
			wr.write(rowcount,11,content_diffdate,normal_style)
			# if len(x['shipment_bales'])>max_widt_col5:
			# 	max_widt_col5=len(x['shipment_bales'])
			# if len(x['etd'])>max_widt_col6:
			# 	max_widt_col3=len(x['etd'])
			# if len(x['eta'])>max_widt_col7:
			# 	max_widt_col7=len(x['eta'])
			# wr.write(rowcount,8,x['contract_no'])
			# if len(x['contract_no'])>max_widt_col8:
			# 	max_widt_col8=len(x['contract_no'])
			totbales_qty+=x['shipment_bales']

			sn+=1
			wr.write(rowcount,0,sn)
			rowcount=rowcount+1
		wr.write_merge(rowcount,rowcount,0,5,"GRAND TOTAL : ",subtotal_style)
		wr.write(rowcount,6,totbales_qty,subtotal_style)
		wr.write_merge(rowcount,rowcount,7,12,"",subtotal_style)
		rowcount=rowcount+1
		wr.col(0).width=256 * int(max_widt_col0*2.1)
		wr.col(1).width=256 * int(max_widt_col1*1)
		wr.col(2).width=256 * int(max_widt_col2*1)
		wr.col(3).width=256 * int(max_widt_col3*1.1)
		wr.col(4).width=256 * int(max_widt_col4*1.5)
		wr.col(5).width=256 * int(max_widt_col5*1.2)
		wr.col(8).width=256 * int(max_widt_col8*2)
		wr.col(11).width=256* int(max_widt_col11*1)

report_sxw.report_sxw('report.otif.pdf','otif.wizard','addons/reporting_module/otif_report/otif_report.mako',parser=otif_parser)
otif_parser_xls('report.otif.xls','otif.wizard','addons/reporting_module/otif_report/otif_report.mako',parser=otif_parser)