from openerp.osv import fields,osv

class om_tally_function(osv.Model):
	_name = "om.tally.function"
	
	def init(self, cr):
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_om_tally(period int,ar_account integer[],adv_account integer[],adv_journal integer[],opening_dt date,closing_dt date) 
			RETURNS TABLE (partner_id integer,code varchar(64),cust varchar(128),sale varchar,curr varchar,op numeric,cl numeric,cn numeric,dn numeric,dpp numeric,tax numeric,pa numeric,pp numeric) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				with 
				ar_sales_dpp as 
					(
					select rp.id,rp.partner_code,rp.name as customer,
					case when rc.name<>'IDR' then 'USD'
					else rc.name
					end as currency,
					coalesce(am_inv.sale_type,
						case when rp.partner_type='local' then rp.partner_type else 'export' end ) as sale_type,
					sum(case when rc.name='IDR' then coalesce(abs(aml.amount_currency),0.0) else coalesce(aml.debit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					inner join (select move_id,goods_type,currency_id,sale_type from account_invoice where type='out_invoice' and state in ('open','paid')) am_inv on am.id=am_inv.move_id
					left join res_currency rc on am_inv.currency_id = rc.id
					where aml.ar_ap_tax = false 
					and aml.period_id=period
					and aml.account_id = any(ar_account)
					group by rp.id,rp.partner_code,rp.name,rc.name,am_inv.goods_type,am_inv.sale_type
					order by rp.id
					),
				ar_sales_tax as (
					select rp.id,rp.partner_code,rp.name as customer,
					case when rc.name<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then coalesce(abs(aml.amount_currency),0.0) else aml.debit end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					inner join (select move_id,goods_type,currency_id from account_invoice where type='out_invoice' and state in ('open','paid')) am_inv on am.id=am_inv.move_id
					left join res_currency rc on am_inv.currency_id = rc.id
					where aml.ar_ap_tax = true 
					and aml.period_id=period
					and aml.account_id = any(ar_account)
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
					),
				payment_dp as(
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					-1*sum(case when rc.name='IDR' then abs(aml.amount_currency) else  coalesce(aml.debit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					left join (select id from account_journal where type in ('cash','bank')) aj on aml.journal_id=aj.id
					where aml.period_id=period
					and aml.account_id = any(adv_account)
					and (aml.reconcile_id is not NULL or aml.reconcile_partial_id is not NULL)
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				),
				payment_ar as(
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then abs(aml.amount_currency) else  coalesce(aml.credit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					left join (select id from account_journal where type in ('cash','bank')) aj on aml.journal_id=aj.id
					where aml.period_id=period
					and aml.account_id = any(ar_account)
					and (aml.reconcile_id is not NULL or aml.reconcile_partial_id is not NULL)
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				),
				prepayment as(
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then abs(aml.amount_currency) else coalesce(aml.credit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					where aml.period_id=period
					and aml.account_id = any(adv_account)
					and aml.journal_id = any(adv_journal)
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				),
				cn as(
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then abs(aml.amount_currency) else  coalesce(aml.credit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					left join (select id from account_journal where type not in ('cash','bank')) aj on aml.journal_id=aj.id
					where aml.period_id=period
					and aml.account_id = any(ar_account)
					and (aml.reconcile_id is NULL and aml.reconcile_partial_id is NULL)
					and aml.credit>0.0 and aml.debit=0.0
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				), 
				dn as(
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then abs(aml.amount_currency) else coalesce(aml.debit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					inner join (select id from account_journal where type not in ('cash','bank','sale')) aj on aml.journal_id=aj.id
					where aml.period_id=period
					and (aml.account_id = any(ar_account) or aml.account_id = any(adv_account))
					and aml.debit>0.0 and aml.credit=0.0
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				),
				opening as (
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then aml.amount_currency else coalesce(aml.debit-aml.credit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					where aml.date<=opening_dt::date
					and (aml.account_id = any(ar_account) or aml.account_id = any(adv_account))
					and aper.special='f'
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				),
				closing as (
					select rp.id,rp.partner_code,rp.name as customer,
					case when coalesce(rc.name,'USD')<>'IDR' then 'USD'
					else rc.name
					end as currency,
					case when rp.partner_type='local' then rp.partner_type else 'export' end as sale_type,
					sum(case when rc.name='IDR' then aml.amount_currency else coalesce(aml.debit-aml.credit,0.0) end) as amount
					from account_move_line aml
					inner join res_partner rp on aml.partner_id=rp.id
					inner join account_move am on aml.move_id=am.id
					left join account_period aper on aml.period_id=aper.id
					left join account_fiscalyear afy on aper.fiscalyear_id=afy.id
					left join res_currency rc on aml.currency_id = rc.id
					where aml.date<=closing_dt::date
					and (aml.account_id = any(ar_account) or aml.account_id = any(adv_account))
					and aper.special='f'
					group by rp.id,rp.partner_code,rp.name,rc.name
					order by rp.id
				)
				select id,partner_code,customer,sale_type,currency,sum(open) as opening_amt,sum(close) as closing_amt,sum(credit_note) as credit_note,sum(debit_note) as debit_note,sum(ar_dpp) as ar_dpp,sum(ar_tax) as ar_tax,sum(paid) as paid,sum(prepaid) as prepaid
				from (
					select id,partner_code,customer,sale_type,currency,amount as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,0.0 as paid,0.0 as prepaid from opening
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,amount as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,0.0 as paid,0.0 as prepaid from cn
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,amount as debit_note,0.0 as ar_dpp,0.0 as ar_tax,0.0 as paid,0.0 as prepaid from dn
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,amount as ar_dpp,0.0 as ar_tax,0.0 as paid,0.0 as prepaid from ar_sales_dpp
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,amount as ar_tax,0.0 as paid,0.0 as prepaid from ar_sales_tax
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,amount as paid,0.0 as prepaid from payment_dp
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,amount as paid,0.0 as prepaid from payment_ar
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,0.0 as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,0.0 as paid,amount as prepaid from prepayment
					UNION
					select id,partner_code,customer,sale_type,currency,0.0 as open,amount as close,0.0 as credit_note,0.0 as debit_note,0.0 as ar_dpp,0.0 as ar_tax,0.0 as paid,0.0 as prepaid from closing
					) as dummy
				group by id,partner_code,customer,sale_type,currency
				order by partner_code
				;
			END;
			$$ LANGUAGE plpgsql;
			""")