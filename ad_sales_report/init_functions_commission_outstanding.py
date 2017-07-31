from openerp.osv import fields,osv

class function_detail_commission_outstanding(osv.Model):
	_name = "function.detail.commission.outstanding"

	def init(self,cr):
		cr.execute("\
			CREATE OR REPLACE FUNCTION commission_detail_outstanding(start_date date,end_date date,stype text) \
			RETURNS TABLE (production_unit varchar,inv_no varchar,inv_id int,inv_date date,lc_batch varchar,sj_no varchar, \
				sj_date date,contract varchar,party varchar,product_id int,prod_name varchar, price_subtotal numeric,agent_name varchar,agent_db_id integer, \
				comm_percent numeric,comm_amt numeric,freight numeric,insurance numeric,fob numeric,comm_amt_fob numeric,incoterm varchar,paid_amt_usd numeric) AS $$ \
			DECLARE \
			BEGIN \
				RETURN QUERY \
				with \
					comm_detail as ( \
						select * from commission_detail(start_date,end_date,stype) \
						), \
					ai_knock_off as ( \
						select invoice_id,knock_off,date_knock_off,date_done \
						from account_invoice_commission aic \
						where invoice_id in (select xcd.inv_id from comm_detail xcd group by xcd.inv_id) \
					), \
					bpa_line as (\
						select abpl.id as line_id, abpl.invoice_id, abpl.invoice_line_id\
						from account_bill_passing_line abpl \
							inner join account_bill_passing abp on abp.id=abpl.bill_id \
						where abpl.comm_provision_id is NULL and abpl.invoice_id is not NULL and abpl.invoice_line_id is not NULL \
							and abp.date_effective<=end_date and abp.state='approved'\
					),\
					ai_pay as ( \
						select dumpaipay.com_int_nbr,dumpaipay.original_inv,dumpaipay.comm_inv_id,dumpaipay.comm_move_id, \
							dumpaipay.invoice_related_id,sum(dumpaipay.paid_amt_usd) as paid_amt_usd,dumpaipay.comm_state \
						from ( \
							select \
								aipay.internal_number as com_int_nbr, \
								(case when round((ailpay.price_subtotal/aipay.amount_untaxed)*sum(credit),2)>0 then aipay.state else '' end) as comm_state, \
								aiori.internal_number as original_inv, \
								aipay.id as comm_inv_id, \
								ampay.id as comm_move_id,ailpay.invoice_related_id, \
								round((ailpay.price_subtotal/aipay.amount_untaxed)*sum(credit),2) as paid_amt_usd \
							from account_invoice_line ailpay \
								left join account_invoice aipay on ailpay.invoice_id=aipay.id \
								left join account_move ampay on ampay.id=aipay.move_id \
								left join account_move_line amlpay on amlpay.account_id=aipay.account_id \
									and amlpay.date<=end_date \
									and (amlpay.reconcile_id is not NULL or amlpay.reconcile_partial_id is not NULL) \
									and amlpay.move_id=ampay.id \
								left join account_invoice aiori on ailpay.invoice_related_id=aiori.id \
							where aipay.type='in_invoice' \
								and aipay.charge_type='sale' \
								and ailpay.invoice_related_id in (select xcd2.inv_id from comm_detail xcd2 group by xcd2.inv_id) \
								and (ailpay.type_of_charge=(select id from charge_type where name='Sales Commission' \
									and trans_type='sale' limit 1) or ailpay.type_of_charge is NULL) \
								and aipay.id in (select invoice_id from bpa_line) \
								and ailpay.id in (select invoice_line_id from bpa_line) \
								and aipay.state != 'cancel' \
							group by ailpay.price_subtotal,aipay.internal_number,aiori.internal_number,aipay.id,ampay.id,ailpay.invoice_related_id,aipay.state \
							order by aiori.internal_number \
						) dumpaipay \
					group by dumpaipay.com_int_nbr,dumpaipay.original_inv,dumpaipay.comm_inv_id,dumpaipay.comm_move_id,dumpaipay.invoice_related_id, \
						comm_state \
					), \
					ai_pay2 as ( \
						select \
							abpl.invoice_related_id, coalesce(abpl.partner_id,aic.agent_id) as partner_id, \
							(case when coalesce(aic.bill_prov_id,0)<>0 then round((1/coalesce(rcr_prov.rate,1))*abpl_prov.amount,2) \
							else round((1/coalesce(rcr.rate,1))*abpl.amount,2) end)as paid_amt_usd2, \
							aic.amount_paid as paid_amt_usd\
						from \
							account_bill_passing_line abpl \
							inner join account_bill_passing abp on abp.id=abpl.bill_id and abp.date_effective<=end_date\
							inner join account_invoice_line ail on ail.id=abpl.invoice_line_id \
							inner join account_invoice ai on ai.id=ail.invoice_id \
							inner join account_invoice_commission aic on aic.id=abpl.comm_id \
							inner join ( \
								select rate_abp.id, rate_abp.currency_id, max(rate_rcr.name::date) as date_rate\
								from \
									account_bill_passing rate_abp \
									inner join res_currency_rate rate_rcr on rate_rcr.currency_id=rate_abp.currency_id and rate_rcr.name::date<=rate_abp.date_effective::date \
								group by rate_abp.id, rate_abp.currency_id) abp_date_rate on abp_date_rate.id=abpl.bill_id \
							inner join res_currency_rate rcr on rcr.name::date=abp_date_rate.date_rate::date and rcr.currency_id=abp_date_rate.currency_id\
							left join account_bill_passing_line abpl_prov on abpl_prov.id=aic.bill_prov_id \
							left join ( \
								select rate_abp.id, rate_abp.currency_id, max(rate_rcr.name::date) as date_rate\
								from \
									account_bill_passing rate_abp \
									inner join res_currency_rate rate_rcr on rate_rcr.currency_id=rate_abp.currency_id and rate_rcr.name::date<=rate_abp.date_effective::date \
								group by rate_abp.id, rate_abp.currency_id) abp_prov_date_rate on abp_date_rate.id=abpl_prov.bill_id \
							left join res_currency_rate rcr_prov on rcr_prov.name::date=abp_prov_date_rate.date_rate::date and rcr_prov.currency_id=abp_prov_date_rate.currency_id\
						where \
							abpl.comm_provision_id is NULL and ai.move_id is not NULL) \
					select cd.*, \
						case \
							when coalesce(gr_cd.total_comm_fob,0.00)=0.0 then 0.00 \
							else \
								round((cd.comm_amt_fob/gr_cd.total_comm_fob)* coalesce(ai_pay2.paid_amt_usd,0.00),2) \
						end as paid_amt_usd \
					from comm_detail as cd \
						left join (select xcd3.inv_id,sum(xcd3.comm_amt_fob) as total_comm_fob \
							from comm_detail xcd3 group by xcd3.inv_id) gr_cd on gr_cd.inv_id=cd.inv_id \
						left join ai_pay2 on ai_pay2.invoice_related_id=cd.inv_id and cd.agent_db_id=ai_pay2.partner_id\
						left join ai_knock_off on ai_knock_off.invoice_id=cd.inv_id \
					where \
						(ai_knock_off.date_done is NULL or ai_knock_off.date_done>end_date) \
						and (coalesce(ai_knock_off.knock_off,false) = false \
							or coalesce(ai_knock_off.date_knock_off,'2215-12-31') > end_date) \
					order by cd.production_unit,cd.inv_no asc,cd.sj_no,cd.contract; \
					END; \
			$$ LANGUAGE plpgsql; \
			")