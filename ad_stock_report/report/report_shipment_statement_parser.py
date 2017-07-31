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

class shipment_statement_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(shipment_statement_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_title' : self._get_title,
			'get_view' : self._get_view,
			'xdate' : self._xdate,
			#'get_result_ageing' : self._get_result_ageing,
		})

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

	def _get_title(self,data,sheet):
		if data['form']['sale_type'] == 'export':
			stitle = 'EXPORT '
		elif data['form']['sale_type'] == 'local':
			stitle = 'LOCAL '
		else:
			stitle = ''
		stitle = stitle + 'SHIPMENT STATEMENT - '
	        # if sheet == 'customer':
	        #     stitle = stitle + 'CUSTOMER WISE'
	        # elif sheet == 'product':
	        #     stitle = stitle + 'PRODUCT WISE'
	        # elif sheet == 'date':
	        #     stitle = stitle + 'DATE WISE'
		return stitle


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
						smp.lot_no \
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
						(select so.name as contract_no,sol.id as sol_id,sol.sequence_line as contractline_no,sol.product_id as sol_product_id,sol.order_id as sol_order_id,so.date_order \
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
						smp.lot_no\
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
						(select sol.id as sol_id,so.name as contract_no,sol.sequence_line as contractline_no,sol.product_id as sol_product_id,sol.order_id as sol_order_id,so.date_order \
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
						smp.lot_no,\
						smp.destination,\
						smp.truck_number,\
						smp.transporter_name\
						order by to_char(smp.date_done,'YYYY-MM-DD'),smp.name,smp.invoice_no,smp.container asc"%(data['sale_type'],data['date_from'],data['date_to'],data['sale_type']) 					

		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res


class shipment_statement_parser_xls(report_xls):
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
			if data['report_type']=='shipment':
				wr=wb.add_sheet(('Export Shipment Statement'))
			else:
				wr=wb.add_sheet(('OTIF -Export'))
		else:
			if data['report_type']=='shipment':
				wr=wb.add_sheet(('Local Shipment Statement'))
			else:
				wr=wb.add_sheet(('OTIF -Local'))

		delivery_moves = parser._get_view(data)
		# print "===========",delivery_moves
		#receipt_moves = parser._get_result_receipt(data)
		#res_last = parser._get_result_ageing(delivery_moves,data)
		
		hdr_style= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		title_style = xlwt.easyxf('font: name Calibri , colour_index black; align: vert centre, horiz center;')
		title_style1 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin;')
		title_style2 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: bottom thin;')
		title_style2_right = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz right; pattern: pattern solid, fore_color gray25; borders: bottom thin;')
		title_style3 = xlwt.easyxf('font: name Calibri, colour_index black; align: vert centre, horiz center; pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		header_style1 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz center;' "borders: top thin, bottom thin")
		locgroup_style = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz left;')
		subtotal_style1 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz center;' "borders: top dashed")
		subtotal_style2 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' "borders: top thin,bottom thin")
		subtotal_style3 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' "borders: top thin,bottom thin", num_format_str='#,##0.00;(#,##0.00)')
		subtotal_style4 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' "borders: top thin,bottom thin", num_format_str='#,##0.0000;(#,##0.0000)')
		style1 = xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' ,num_format_str='#,##0.00;(#,##0.00)') 
		style2= xlwt.easyxf('font : name Calibri, colour_index black; align: vert centre, horiz right;' ,num_format_str='#,##0.0000;(#,##0.0000)')
		# normal_bold_style_b = xlwt.easyxf('font: name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
		
		if data['sale_type']=='export':
			wr.write_merge(0,0,0,21, "PT. BITRATEX INDUSTRIES", title_style)
			wr.write_merge(1,1,0,21, parser._xdate(data['sale_type'].upper())+" SHIPMENT STATEMENT FOR THE PERIOD BETWEEN "+parser._xdate(data['date_from'])+ " AND " +parser._xdate(data['date_to']), title_style)
		else:
			wr.write_merge(0,0,0,16, "PT. BITRATEX INDUSTRIES", title_style)
			wr.write_merge(1,1,0,16, parser._xdate(data['sale_type'].upper())+" SHIPMENT STATEMENT FOR THE PERIOD BETWEEN "+parser._xdate(data['date_from'])+ " AND " +parser._xdate(data['date_to']), title_style)
		#wr.write_merge(2,2,6,8, "FROM:"+parser._xdate(data['date_from']), title_style)
		#wr.write_merge(2,2,9,11, "TO:"+parser._xdate(data['date_to']), title_style)
		wr.portrait = 0
		wr.fit_width_to_pages = 1
        #wr.fit_height_to_pages = 0
        #wr.fit_num_pages = 0
		wr.print_scaling = 48
		wr.write(3,0, "NO", title_style1)
		wr.write_merge(3,3,1,2, "CUSTOMER", title_style3)
		wr.write(3,3, "CONTRACT NO", title_style1)
		wr.write(3,4, "LC NO", title_style1)
		wr.write(3,5, "COUNT", title_style1)
		# wr.write(3,21, "LOT NO",title_style1)
		wr.write(3,6, "LOT NO",title_style1)
		wr.write_merge(3,3,7,8, "SURAT JALAN", title_style3)
		wr.write_merge(3,3,9,10, "INVOICE", title_style3)
		if data['sale_type']=='export':
			wr.write_merge(3,3,11,12, "BILL OF LADING", title_style3)
			wr.write_merge(3,3,13,14, "NEGOTIATION", title_style3)
			wr.write_merge(3,3,15,16, "SHIPMENT", title_style3)
			wr.write(3,17, "ETD", title_style1)
			wr.write(3,18, "ETA", title_style1)
			wr.write(3,19, "SHIPPING LINE", title_style1)
			wr.write(3,20, "CONTAINER NO.", title_style1)
			wr.write(3,21, "SIZE", title_style1)
			wr.write(4,0, "", title_style2)
			wr.write(4,1, "NAME", title_style2)
			wr.write(4,2, "DESTINATION", title_style2)
			wr.write(4,3, "", title_style2)
			wr.write(4,4, "", title_style2)
			wr.write(4,5, "", title_style2)
			wr.write(4,6, "", title_style2)
			wr.write(4,7, "NO.", title_style2)
			wr.write(4,8, "DATE", title_style2)
			wr.write(4,9, "NO.", title_style2)
			wr.write(4,10, "DATE.", title_style2)
			wr.write(4,11, "NO.", title_style2)
			wr.write(4,12, "DATE.", title_style2)
			wr.write(4,13, "DATE", title_style2)
			wr.write(4,14, "BANK", title_style2)
			wr.write(4,15, "K.G.", title_style2_right)
			wr.write(4,16, "US$", title_style2_right)
			wr.write(4,17, "", title_style2)
			wr.write(4,18, "", title_style2)
			wr.write(4,19, "", title_style2)
			wr.write(4,20, "", title_style2)
			wr.write(4,21, "", title_style2)
			if data['report_type']=='otif':
				wr.write_merge(3,3,22,23,"SC",title_style3)
				wr.write(4,22,"NO",title_style2)
				wr.write(4,23,"DATE",title_style2)
				wr.write(3,24,"LC/TT",title_style1)
				wr.write(4,24,"DATE",title_style2)
				wr.write(3,25,"REMARK",title_style1)
				wr.write(4,25,"",title_style2)
		else:
			
			wr.write_merge(3,3,11,12, "SHIPMENT", title_style3)
			wr.write(3,13, "AMOUNT", title_style1)
			
			wr.write(3,14, "TRANSPORTER NAME", title_style1)
			wr.write(3,15, "TRUCK NO.", title_style1)
			wr.write(3,16, "SIZE", title_style1)
			wr.write(4,0, "", title_style2)
			wr.write(4,1, "NAME", title_style2)
			wr.write(4,2, "DESTINATION", title_style2)
			wr.write(4,3, "", title_style2)
			wr.write(4,4, "", title_style2)
			wr.write(4,5, "", title_style2)
			wr.write(4,6, "", title_style2)
			wr.write(4,7, "NO.", title_style2)
			wr.write(4,8, "DATE", title_style2)
			wr.write(4,9, "NO.", title_style2)
			wr.write(4,10, "DATE.", title_style2)
		
			wr.write(4,11, "K.G.", title_style2_right)
			wr.write(4,12, "BALES", title_style2_right)
			wr.write(4,13, "", title_style2)
			wr.write(4,14, "", title_style2)
			wr.write(4,15, "", title_style2)
			wr.write(4,16, "", title_style2)
			if data['report_type']=='otif':
				wr.write_merge(3,3,17,18,"SC",title_style3)
				wr.write(4,17,"NO",title_style2)
				wr.write(4,18,"DATE",title_style2)
				wr.write(3,19,"LC/TT",title_style1)
				wr.write(4,19,"DATE",title_style2)
				wr.write(3,20,"REMARK",title_style1)
				wr.write(4,20,"",title_style2)
		

		# wr = wb.add_sheet(('Shipment Statement')) 
		wr.col(0).width = len("ABCDEFG")*160
		wr.col(1).width = (wr.col(0).width)*8
		wr.col(2).width = (wr.col(0).width)*3+300
		wr.col(3).width = (wr.col(0).width)*3+800
		wr.col(4).width = (wr.col(0).width)*4
		wr.col(5).width = (wr.col(0).width)*6
		wr.col(6).width = (wr.col(0).width)*2+300
		wr.col(7).width = (wr.col(0).width)*2+1200
		wr.col(8).width = (wr.col(0).width)*2+600
		wr.col(9).width = (wr.col(0).width)*3
		wr.col(10).width = (wr.col(0).width)*2+600
		wr.col(11).width = (wr.col(0).width)*3+1250
		wr.col(12).width = (wr.col(0).width)*2+600
		wr.col(13).width = (wr.col(0).width)*2+600
		wr.col(14).width = (wr.col(0).width)*3+800
		wr.col(15).width = (wr.col(0).width)*3+600
		wr.col(16).width = (wr.col(0).width)*3
		wr.col(17).width = (wr.col(0).width)*2+600
		wr.col(18).width = (wr.col(0).width)*2+600
		if data['sale_type']=='export':
			wr.col(19).width = (wr.col(0).width)*3+300
		else:
			wr.col(19).width = (wr.col(0).width)*3+1800
		wr.col(20).width =(wr.col(0).width)*4+600
		wr.col(21).width = (wr.col(0).width)*2+300


		res_grouped = {}
		rowcount=6
		total_qty_kg=0
		total_bale=0
		total_usd=0
		total_currency=0
		total_container_size=0
		sn=0
		for res in delivery_moves:
			key = res['id']
			if key not in res_grouped:
				res_grouped.update({key:[]})
			res_grouped[key].append(res)

		# for key in res_grouped.keys():
		# 	res_grouped2 = {}
		# 	for res in res_grouped[key]:
		# 		key1 = res['product_id']
		# 		if key1 not in res_grouped2:
		# 			res_grouped2.update({key1:[]})
		# 		res_grouped2[key1].append(res)
		# 	res_grouped[key] = res_grouped2
		# rowcount=5
		# total_qty2, total_kgs_qty, total_bale_qty = 0,0,0
		#for key in res_grouped:
			# subtotal_loc_qty2, subtotal_loc_kgs_qty, subtotal_loc_bale_qty = 0,0,0
			# wr.write_merge(rowcount,rowcount,0,5,key,locgroup_style)
			# rowcount+=1
			# for key1 in res_grouped[key]:
				# subtotal_qty2, subtotal_kgs_qty, subtotal_bale_qty = 0,0,0
			# for res in res_grouped[key][key1]:
			
			wr.write(rowcount,1,res['partner'])
			wr.write(rowcount,2,res['destination'])
			wr.write(rowcount,3,res['contractline_no'])
			wr.write(rowcount,4,res['lc_number'])
			wr.write(rowcount,5,res['count'])
			# wr.write(rowcount,6,res['lot_no'])
			wr.write(rowcount,6,','.join(list(set(res['lot_no'].split(',')))))
			# wr.write(rowcount,6,res['lot_no'])
			wr.write(rowcount,7,res['sj_name'])
			wr.write(rowcount,8,parser._xdate(res['sj_date']))
			wr.write(rowcount,9,res['invoice_no'])
			wr.write(rowcount,10,parser._xdate(res['invoice_date']))
			if data['sale_type']=='export':
				wr.write(rowcount,11,res['bl_number'])
				wr.write(rowcount,12,parser._xdate(res['bl_date'])) 
				wr.write(rowcount,13, parser._xdate(res['bank_negotiation_date']))
				wr.write(rowcount,14,res['nego_bank'])
				# wr.write(rowcount,14,round(res['shipment_kg'],2),style2)
				# wr.write(rowcount,15,round(res['shipment_usd'],2),style1)
				wr.write(rowcount,15,res['shipment_kg'],style2)
				wr.write(rowcount,16,res['shipment_usd'],style1)
				wr.write(rowcount,17,parser._xdate(res['etd']))
				wr.write(rowcount,18,parser._xdate(res['eta']))
				if data['sale_type']== 'export':
					wr.write(rowcount,19,res['shipping_line'])
				else:
					wr.write(rowcount,19,res['transporter_name'])
				# subtotal_qty2 += res['qty2']
				# wr.writroune(rowcount,3,res['uom'])
				if data['sale_type']== 'export':
					wr.write(rowcount,20,res['container_no'])
				elif data['sale_type']== 'local':
					wr.write(rowcount,20,res['truck_number'])
				# subtotal_kgs_qty += res['kgs_qty']
				# wr.write(rowcount,5,res['uop'])
				wr.write(rowcount,21,res['show_container_size'])
				# subtotal_bale_qty += res['bale_qty']
				# wr.write(rowcount,5,round(res['age'],2))
				total_qty_kg+=res['shipment_kg']
				total_usd+=res['shipment_usd']
				total_container_size+=res['container_size']
				if data['report_type']=='otif':
					wr.write(rowcount,22,res['contract_no'])
					wr.write(rowcount,23,res['date_order'])
					wr.write(rowcount,24,res['lctt_date'])
			else:
				# wr.write(rowcount,11,res['bl_number'])
				# wr.write(rowcount,12,parser._xdate(res['bl_date'])) 
				#wr.write(rowcount,13, parser._xdate(res['bank_negotiation_date']))
				#wr.write(rowcount,14,res['nego_bank'])
				# wr.write(rowcount,14,round(res['shipment_kg'],2),style2)
				# wr.write(rowcount,15,round(res['shipment_usd'],2),style1)
				wr.write(rowcount,11,res['shipment_kg'],style2)
				wr.write(rowcount,12,res['shipment_bales'],style2)
				# wr.write(rowcount,13,res['shipment_usd'],style1) 
				wr.write(rowcount,13,res['shipment_currency'],style1) 
				# wr.write(rowcount,18,parser._xdate(res['eta']))
				wr.write(rowcount,14,res['transporter_name'])
				# subtotal_qty2 += res['qty2']
				# wr.writroune(rowcount,3,res['uom'])
				wr.write(rowcount,15,res['truck_number'])
				# subtotal_kgs_qty += res['kgs_qty']
				# wr.write(rowcount,5,res['uop'])
				wr.write(rowcount,16,res['show_container_size'])
				# subtotal_bale_qty += res['bale_qty']
				# wr.write(rowcount,5,round(res['age'],2))
				total_bale+=res['shipment_bales']
				total_qty_kg+=res['shipment_kg']
				total_usd+=res['shipment_usd']
				total_currency+=res['shipment_currency']
				total_container_size+=res['container_size']
				if data['report_type']=='otif':
					wr.write(rowcount,17,res['contract_no'])
					wr.write(rowcount,18,res['date_order'])
					wr.write(rowcount,19,res['lctt_date'])
			sn+=1
			wr.write(rowcount,0,sn)
			rowcount+=1
		if data['sale_type']=='export':
			wr.write(rowcount,0,"",subtotal_style2)
			wr.write(rowcount,1,"",subtotal_style4)
			wr.write(rowcount,2,"",subtotal_style2)
			wr.write(rowcount,3,"",subtotal_style2)
			wr.write(rowcount,4,"",subtotal_style2)
			wr.write(rowcount,5,"",subtotal_style2)
			wr.write(rowcount,6,"",subtotal_style2)
			wr.write(rowcount,7,"",subtotal_style2)
			wr.write(rowcount,8,"",subtotal_style2)
			wr.write(rowcount,9,"",subtotal_style2)
			wr.write(rowcount,10,"",subtotal_style2)
			wr.write(rowcount,11,"",subtotal_style2)
			wr.write(rowcount,12,"",subtotal_style2)
			wr.write(rowcount,13,"",subtotal_style2)
			wr.write(rowcount,14,"Grand Total",subtotal_style2)
			wr.write(rowcount,15,total_qty_kg,subtotal_style4)
			wr.write(rowcount,16,total_usd,subtotal_style3)
			wr.write(rowcount,17,"",subtotal_style2)
			wr.write(rowcount,18,"",subtotal_style2)
			wr.write(rowcount,19,"",subtotal_style2)
			wr.write(rowcount,20,"",subtotal_style2)
			wr.write(rowcount,21,str(round(total_container_size,2))+ " x 40'",subtotal_style2)
			if data['report_type']=='otif':
				wr.write(rowcount,22,"",subtotal_style2)
				wr.write(rowcount,23,"",subtotal_style2)
				wr.write(rowcount,24,"",subtotal_style2)
				wr.write(rowcount,25,"",subtotal_style2)
		else:
			wr.write(rowcount,0,"",subtotal_style2)
			wr.write(rowcount,1,"",subtotal_style4)
			wr.write(rowcount,2,"",subtotal_style2)
			wr.write(rowcount,3,"",subtotal_style2)
			wr.write(rowcount,4,"",subtotal_style2)
			wr.write(rowcount,5,"",subtotal_style2)
			wr.write(rowcount,6,"",subtotal_style2)
			wr.write(rowcount,7,"",subtotal_style2)
			wr.write(rowcount,8,"",subtotal_style2)
			wr.write(rowcount,9,"",subtotal_style2)
			# wr.write(rowcount,10,"",subtotal_style2)
			# wr.write(rowcount,11,"",subtotal_style2)
			# wr.write(rowcount,12,"",subtotal_style2)
			# wr.write(rowcount,13,"",subtotal_style2)
			wr.write(rowcount,10,"Grand Total",subtotal_style2)
			wr.write(rowcount,11,total_qty_kg,subtotal_style4)
			wr.write(rowcount,12,total_bale,subtotal_style4)
			wr.write(rowcount,13,total_currency,subtotal_style3)
			wr.write(rowcount,14,"",subtotal_style2)
			wr.write(rowcount,15,"",subtotal_style2)
			# wr.write(rowcount,20,"",subtotal_style2)
			wr.write(rowcount,16,str(round(total_container_size,2))+ " x 40'",subtotal_style2)
			if data['report_type']=='otif':
				wr.write(rowcount,17,"",subtotal_style2)
				wr.write(rowcount,18,"",subtotal_style2)
				wr.write(rowcount,19,"",subtotal_style2)
				wr.write(rowcount,20,"",subtotal_style2)
		rowcount+=1
		pass


	

		# 		wr.write_merge(rowcount,rowcount,0,1,"Subtotal",subtotal_style1)
		# 		wr.write(rowcount,2,subtotal_qty2,subtotal_style2)
		# 		subtotal_loc_qty2 += subtotal_qty2
		# 		wr.write(rowcount,3,round(subtotal_kgs_qty,2),subtotal_style2)
		# 		subtotal_loc_kgs_qty += subtotal_kgs_qty
		# 		wr.write(rowcount,4,round(subtotal_bale_qty,2),subtotal_style2)
		# 		wr.write(rowcount,5,'',subtotal_style2)
		# 		subtotal_loc_bale_qty += subtotal_bale_qty
		# 		rowcount+=1
		# 	wr.write_merge(rowcount,rowcount,0,1,"Subtotal",subtotal_style1)
		# 	wr.write(rowcount,2,subtotal_loc_qty2,subtotal_style2)
		# 	total_qty2 += subtotal_loc_qty2
		# 	wr.write(rowcount,3,round(subtotal_loc_kgs_qty,2),subtotal_style2)
		# 	total_kgs_qty += subtotal_loc_kgs_qty
		# 	wr.write(rowcount,4,round(subtotal_loc_bale_qty,2),subtotal_style2)
		# 	total_bale_qty += subtotal_loc_bale_qty
		# 	wr.write(rowcount,5,'',subtotal_style2)
		# 	rowcount+=1
		# wr.write_merge(rowcount,rowcount,0,1,"Total",subtotal_style1)
		# wr.write(rowcount,2,total_qty2,subtotal_style2)
		# wr.write(rowcount,3,round(total_kgs_qty,2),subtotal_style2)
		# wr.write(rowcount,4,round(total_bale_qty,2),subtotal_style2)
		# wr.write(rowcount,5,'',subtotal_style2)
		# pass

report_sxw.report_sxw('report.shipment.statement.pdf','shipment.statement.wizard', 'addons/ad_stock_report/report/report_shipment_statement.mako',
						parser=shipment_statement_parser)
shipment_statement_parser_xls('report.shipment.statement.xls','stock.ageing.wizard', 'addons/ad_stock_report/report/report_shipment_statement.mako',
						parser=shipment_statement_parser)
