from openerp.osv import fields,osv

class function_detail_commission(osv.Model):
	_name = "function.detail.commission"

	def init(self,cr):
		cr.execute("\
			CREATE OR REPLACE FUNCTION commission_detail(start_date date,end_date date,stype text) \
			RETURNS TABLE (production_unit varchar,inv_no varchar,inv_id int,inv_date date,lc_batch varchar,sj_no varchar, \
				sj_date date,contract varchar,party varchar,product_id int,prod_name varchar, price_subtotal numeric,agent_name varchar,agent_db_id integer, \
				comm_percent numeric,comm_amt numeric,freight numeric,insurance numeric,fob numeric,comm_amt_fob numeric,incoterm varchar) AS $$ \
			DECLARE \
			BEGIN \
				RETURN QUERY \
					with ail as ( \
						select ail1.id,ail1.invoice_id,ai1.internal_number,ai1.currency_id,ail1.product_id, \
						ail1.uos_id,ail1.quantity,ail1.price_unit,ail1.price_subtotal,ai1.amount_total,rcrinv_out.rate, \
						round(1.0/rcrinv_out.rate*ail1.price_subtotal,2) as price_subtotal_usd,round(1.0/rcrinv_out.rate*ai1.amount_total,2) as amount_total_usd, \
						ai1.amount_insurance,round(1.0/rcrinv_out.rate*ai1.amount_insurance,2) as amount_insurance_usd,ai1.date_invoice \
						from account_invoice ai1 \
							right join account_invoice_line ail1 on ail1.invoice_id=ai1.id \
							left join ( \
								select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
								from account_invoice inv \
									inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
								where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
								and inv.type='out_invoice' and inv.goods_type='finish' \
								and inv.sale_type =stype \
								group by inv.id,rcrinv.currency_id \
								) rcrai1 on rcrai1.id = ai1.id \
							left join res_currency_rate rcrinv_out on rcrinv_out.currency_id = ai1.currency_id and rcrai1.curr_date = rcrinv_out.name \
						where ai1.state <> 'cancel' \
							and ai1.sale_type =stype \
							and ai1.goods_type='finish' \
							and ai1.type='out_invoice' \
							and ai1.date_invoice >=start_date \
							and ai1.date_invoice<=end_date \
						order by ai1.internal_number asc \
						), \
					sp_ids as ( \
						select id,trucking_invoice_id from stock_picking where invoice_id in (select invoice_id from ail group by invoice_id) \
						), \
					sm_ids as ( \
						select sm.picking_id,sum(round(sm.product_qty/pu1.factor*pu2.factor,4)) as total_qty_do \
						from stock_move sm \
						left join product_product pp on sm.product_id=pp.id \
						left join product_template pt on pp.product_tmpl_id=pt.id \
						left join product_uom pu1 on sm.product_uom=pu1.id \
						left join product_uom pu2 on pt.uom_id=pu2.id \
						where sm.invoice_line_id in (select id from ail) \
						group by picking_id \
						), \
					sm_ids2 as ( \
						select sp.invoice_id,sum(round(sm.product_qty/pu1.factor*pu2.factor,4)) as total_qty_do \
						from stock_move sm \
						left join stock_picking sp on sm.picking_id=sp.id \
						left join product_product pp on sm.product_id=pp.id \
						left join product_template pt on pp.product_tmpl_id=pt.id \
						left join product_uom pu1 on sm.product_uom=pu1.id \
						left join product_uom pu2 on pt.uom_id=pu2.id \
						where sm.invoice_line_id in (select id from ail) \
						group by invoice_id \
						), \
					chg1 as ( \
						select picking_related_id,invoice_related_id,currency_id, \
						sum(chg1_subtotal) as chg1_subtotal, \
						sum(tax_amount) as tax_amount, \
						sum(chg1_amount_total) as chg1_amount_total, \
						chg1_rate,sum(chg1_subtotal_usd) as chg1_subtotal_usd, \
						sum(chg1_subtotal_tax_usd) as chg1_subtotal_tax_usd, \
						sum(chg1_subtotal_vat_usd) as chg1_subtotal_vat_usd, \
						sum(chg1_amount_total_usd) as chg1_amount_total_usd \
						from ( \
							select ail2.id,ail2.invoice_id,ail2.picking_related_id,ail2.invoice_related_id,ai2.currency_id, \
							ail2.price_subtotal as chg1_subtotal,ail2.tax_amount, \
							ai2.amount_total as chg1_amount_total,coalesce(rcrinv_in1.rate,1) as chg1_rate, \
							round((1/coalesce(rcrinv_in1.rate,1))*ail2.price_subtotal,2) as chg1_subtotal_usd, \
							round((1/coalesce(rcrinv_in1.rate,1))*(ail2.price_subtotal+ail2.tax_amount),2) as chg1_subtotal_tax_usd, \
							round((1/coalesce(rcrinv_in1.rate,1))*(ail2.price_subtotal+ail2.vat_non_pph_amt),2) as chg1_subtotal_vat_usd, \
							round((1/coalesce(rcrinv_in1.rate,1))*ai2.amount_total,2) as chg1_amount_total_usd \
							from account_invoice_line ail2 \
							left join account_invoice ai2 on ail2.invoice_id=ai2.id \
							left join ( \
								select inv_line.invoice_related_id,max(rcrinv.name) as curr_date \
								from account_invoice_line inv_line \
									inner join account_invoice inv on inv_line.invoice_id=inv.id \
									left join account_invoice inv2 on inv_line.invoice_related_id=inv2.id \
									inner join res_currency_rate rcrinv on inv.currency_id=rcrinv.currency_id \
								where rcrinv.name::date<=inv2.date_invoice::date \
								group by inv_line.invoice_related_id \
								) rcrai1 on rcrai1.invoice_related_id = ail2.invoice_related_id \
							left join res_currency_rate rcrinv_in1 on rcrinv_in1.currency_id = ai2.currency_id and rcrai1.curr_date = rcrinv_in1.name \
							 \
							where ai2.type='in_invoice' and ail2.report_charge_type='freight' \
							and ail2.type_of_charge=(select id from charge_type where name='Freight' and trans_type='sale' limit 1) \
							and ail2.invoice_related_id in (select invoice_id from ail group by ail.invoice_id) \
							and ail2.picking_related_id in (select id from sp_ids ) \
							) dumchg1 \
						group by picking_related_id,invoice_related_id,currency_id,chg1_rate \
						), \
					chg2 as ( \
						select ail2.id,ail2.invoice_id,ail2.picking_related_id,ail2.invoice_related_id,ai2.currency_id,ail2.price_subtotal as chg2_subtotal,ail2.tax_amount, \
						ai2.amount_total as chg2_amount_total,coalesce(rcrinv_in1.rate,1) as chg2_rate, \
						round((1/coalesce(rcrinv_in1.rate,1))*ail2.price_subtotal,2) as chg2_subtotal_usd, \
						round((1/coalesce(rcrinv_in1.rate,1))*(ail2.price_subtotal+ail2.tax_amount),2) as chg2_subtotal_tax_usd, \
						round((1/coalesce(rcrinv_in1.rate,1))*ai2.amount_total,2) as chg2_amount_total_usd \
						from account_invoice_line ail2 \
						left join account_invoice ai2 on ail2.invoice_id=ai2.id \
						left join ( \
							select inv_line.invoice_related_id,max(rcrinv.name) as curr_date \
							from account_invoice_line inv_line \
								inner join account_invoice inv on inv_line.invoice_id=inv.id \
								left join account_invoice inv2 on inv_line.invoice_related_id=inv2.id \
								inner join res_currency_rate rcrinv on inv.currency_id=rcrinv.currency_id \
							where rcrinv.name::date<=inv2.date_invoice::date \
							group by inv_line.invoice_related_id \
							) rcrai1 on rcrai1.invoice_related_id = ail2.invoice_related_id \
						left join res_currency_rate rcrinv_in1 on rcrinv_in1.currency_id = ai2.currency_id and rcrai1.curr_date = rcrinv_in1.name \
						where ai2.type='in_invoice' \
						and ail2.type_of_charge=(select id from charge_type where name='EMKL' and trans_type='sale' limit 1) \
						and ail2.invoice_related_id in (select invoice_id from ail group by ail.invoice_id) \
						and ail2.picking_related_id in (select id from sp_ids ) \
						and ai2.id in (select trucking_invoice_id from sp_ids ) \
						), \
					chg3 as ( \
						select dum_chg3.picking_related_id,dum_chg3.invoice_related_id,sum(dum_chg3.chg3_subtotal) as chg3_subtotal,sum(dum_chg3.chg3_subtotal_usd) as chg3_subtotal_usd \
						from ( \
							select etl.id,etl.ext_transaksi_id,etl.picking_related_id,etl.invoice_related_id,et.currency_id, \
							case when coalesce(etl.debit,0.0)>0 then debit else -1*etl.credit end as chg3_subtotal,rcret1_in1.rate as chg3_rate, \
							round((1/rcret1_in1.rate)*case when coalesce(etl.debit,0.0)>0 then debit else -1*etl.credit end,2) as chg3_subtotal_usd \
							from ext_transaksi_line etl \
							left join ext_transaksi et on etl.ext_transaksi_id=et.id \
							left join ( \
								select etl_chg.invoice_related_id,max(rcrinv.name) as curr_date \
								from ext_transaksi_line etl_chg \
									inner join ext_transaksi et_chg on etl_chg.ext_transaksi_id=et_chg.id \
									left join account_invoice inv2 on etl_chg.invoice_related_id=inv2.id \
									inner join res_currency_rate rcrinv on et_chg.currency_id=rcrinv.currency_id \
								where rcrinv.name::date<=inv2.date_invoice::date \
								group by etl_chg.invoice_related_id \
								) rcrai1 on rcrai1.invoice_related_id = etl.invoice_related_id \
							left join res_currency_rate rcret1_in1 on rcret1_in1.currency_id = et.currency_id and rcrai1.curr_date = rcret1_in1.name \
							where et.type_transaction='payment' \
							and etl.type_of_charge=(select id from charge_type where name='Lift On Lift Off' and trans_type='sale' limit 1) \
							and etl.invoice_related_id in (select invoice_id from ail group by ail.invoice_id) \
							and etl.picking_related_id in (select id from sp_ids ) \
							) dum_chg3 \
						group by dum_chg3.picking_related_id,dum_chg3.invoice_related_id \
						), \
					chg4 as ( \
						select ail2.report_charge_type,ail2.id,ail2.invoice_id,ail2.picking_related_id,ail2.invoice_related_id,ai2.currency_id,ail2.price_subtotal as chg4_subtotal,ail2.tax_amount, \
						ai2.amount_total as chg4_amount_total,coalesce(rcrinv_in1.rate,1) as chg4_rate, \
						round((1/coalesce(rcrinv_in1.rate,1))*ail2.price_unit,2) as chg4_subtotal_usd, \
						round((1/coalesce(rcrinv_in1.rate,1))*(ail2.price_subtotal+ail2.tax_amount),2) as chg4_subtotal_tax_usd, \
						round((1/coalesce(rcrinv_in1.rate,1))*ai2.amount_total,2) as chg4_amount_total_usd \
						from account_invoice_line ail2 \
						left join account_invoice ai2 on ail2.invoice_id=ai2.id \
						left join ( \
							select inv_line.invoice_related_id,max(rcrinv.name) as curr_date \
							from account_invoice_line inv_line \
								inner join account_invoice inv on inv_line.invoice_id=inv.id \
								left join account_invoice inv2 on inv_line.invoice_related_id=inv2.id \
								inner join res_currency_rate rcrinv on inv.currency_id=rcrinv.currency_id \
							where rcrinv.name::date<=inv2.date_invoice::date \
							group by inv_line.invoice_related_id \
							) rcrai1 on rcrai1.invoice_related_id = ail2.invoice_related_id \
						left join res_currency_rate rcrinv_in1 on rcrinv_in1.currency_id = ai2.currency_id and rcrai1.curr_date = rcrinv_in1.name \
						where ai2.type='in_invoice' \
						and ail2.report_charge_type='ocost' \
						and ail2.invoice_related_id in (select invoice_id from ail group by ail.invoice_id) \
						and ail2.picking_related_id in (select id from sp_ids ) \
						) \
					select site_id as production_unit, \
						internal_number as inv_no, \
						invoice_id as inv_id, \
						date_invoice as inv_date, \
						lc_batch_no as lc_batch, \
						do_no, \
						do_date, \
						sequence_line as contract, \
						partner_alias as party, \
						prod_id, \
						product_name as prod_name, \
						sum(price_subtotal_usd) as price_subtotal, \
						agent, \
						agent_id, \
						commission_percentage as comm_percent, \
						sum(amt_comm) as comm_amt, \
						sum(freight_total) as freight, \
						sum(amt_insurance_usd) as insurance, \
						sum(amount_fob) as fob, \
						sum(comm_fob) as comm_amt_fob, \
						inco \
					from ( \
						select \
							slprod2.name as site_id, \
							ail.internal_number,ail.invoice_id, \
							ail.date_invoice,coalesce(lc.name,'-') as lc_batch_no,sp.name as do_no,sp.date_done::date as do_date, \
							sol.sequence_line, \
							coalesce(rp.partner_alias,rp.name) as partner_alias,pp.id as prod_id,pp.name_template as product_name,ail.price_subtotal_usd,coalesce(rp_soa.partner_alias,rp_soa.name) as agent, rp_soa.id as agent_id, \
							coalesce(soa.commission_percentage,0.0) as commission_percentage, \
							round((coalesce(soa.commission_percentage,0.0)/100.0)*ail.price_subtotal_usd,2) as amt_comm, \
							( \
							coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg1.chg1_subtotal_vat_usd,2),0.0)+ \
							coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg4.chg4_subtotal_usd,2),0.0)) \
							as freight_total, \
							round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids2.total_qty_do)*ail.amount_insurance_usd,2) as amt_insurance_usd, \
							( \
							ail.price_subtotal_usd- \
							( \
							coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg1.chg1_subtotal_vat_usd,2),0.0)+ \
							coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg4.chg4_subtotal_usd,2),0.0)) \
							) as amount_fob, \
							round((coalesce(soa.commission_percentage,0.0)/100.0)*( \
								ail.price_subtotal_usd- \
										( \
										coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg1.chg1_subtotal_vat_usd,2),0.0)+ \
										coalesce(round((round(sm.product_qty/pu1.factor*pu2.factor,4)/sm_ids.total_qty_do)*chg4.chg4_subtotal_usd,2),0.0)) \
								),2) as comm_fob, \
							inco.code as inco \
						from stock_move sm \
							left join sale_order_line sol on sm.sale_line_id=sol.id \
							left join sale_order so on sol.order_id=so.id \
							left join stock_picking sp on sm.picking_id=sp.id \
							left join product_product pp on sm.product_id=pp.id \
							left join product_template pt on pp.product_tmpl_id=pt.id \
							left join product_uom pu1 on sm.product_uom=pu1.id \
							left join product_uom pu2 on pt.uom_id=pu2.id \
							left join ail on sm.invoice_line_id = ail.id and sm.product_id=ail.product_id \
							left join account_invoice ai5 on ai5.id=ail.invoice_id \
							left join res_partner rp on ai5.partner_id=rp.id \
							left join letterofcredit_product_line lpl on sm.lc_product_line_id=lpl.id \
							left join letterofcredit lc on lpl.lc_id=lc.id \
							left join sm_ids on sm_ids.picking_id=sm.picking_id \
							left join sm_ids2 on sm_ids2.invoice_id =sp.invoice_id \
							left join chg1 on chg1.picking_related_id = sp.id and chg1.invoice_related_id = ail.invoice_id \
							left join chg2 on chg2.picking_related_id = sp.id and chg2.invoice_related_id = ail.invoice_id \
							left join chg3 on chg3.picking_related_id = sp.id and chg3.invoice_related_id = ail.invoice_id \
							left join chg4 on chg4.picking_related_id = sp.id and chg4.invoice_related_id = ail.invoice_id \
							left join sale_order_agent soa on soa.sale_line_id=sol.id \
							left join res_partner rp_soa on soa.agent_id=rp_soa.id \
							inner join stock_incoterms inco on so.incoterm=inco.id \
							left join \
								(select split_part(value_reference,',',2)::int as location_id,split_part(res_id,',',2)::int as product_tmpl_id \
								from ir_property \
								where name='property_stock_production' and value_reference is not NULL and res_id is not NULL \
								) ip on ip.product_tmpl_id = pt.id \
							inner join stock_location slprod on ip.location_id=slprod.id \
							left join stock_location slprod2 on slprod.location_id=slprod2.id \
							left join stock_location slprod3 on slprod2.location_id=slprod3.id \
						where sp.type='out' and sp.state='done' \
							and sp.sale_type=stype and sp.goods_type='finish' \
							and sp.date_done::date >=start_date \
							and sp.date_done::date <=end_date \
						group by slprod2.name,ail.invoice_id,ail.internal_number,ail.date_invoice,lc.name,sp.name,sp.date_done::date,sol.sequence_line,coalesce(rp.partner_alias,rp.name), \
							pp.id,pp.name_template,ail.price_subtotal_usd,sm.product_qty,pu1.factor,pu2.factor,sm_ids.total_qty_do,chg1.chg1_subtotal_tax_usd,chg1.chg1_subtotal_vat_usd, \
							chg2.chg2_subtotal_usd,chg3.chg3_subtotal_usd,chg4.chg4_subtotal_usd,coalesce(rp_soa.partner_alias,rp_soa.name),rp_soa.id,soa.commission_percentage,inco.code, \
							sm_ids2.total_qty_do,ail.amount_insurance,ail.amount_insurance_usd,sm.invoice_line_id \
						order by slprod2.name,ail.internal_number asc,sp.name,sol.sequence_line \
					) grouper \
					group by site_id,invoice_id,internal_number,date_invoice,lc_batch_no,do_no,do_date, \
						sequence_line,partner_alias,prod_id,product_name, \
						agent,agent_id,commission_percentage,inco \
					order by site_id,internal_number,do_no,sequence_line; \
				END;		 \
			$$ LANGUAGE plpgsql; \
			")