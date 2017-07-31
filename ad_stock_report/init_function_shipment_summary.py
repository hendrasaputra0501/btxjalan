from openerp.osv import fields,osv

class function_shipment_summary(osv.Model):
	_name = "function.shipment.summary"

	def init(self,cr):
		cr.execute("\
			CREATE OR REPLACE FUNCTION shipment_summary(daily date,start_mth date,end_mth date,start_year date,end_year date,stype text) \
			RETURNS TABLE (loc_name varchar,blend varchar,qty_daily numeric,qty_bale_daily numeric,cont_daily numeric,subtotal_daily numeric, \
				qty_monthly numeric,qty_bale_monthly numeric,cont_monthly numeric,subtotal_monthly numeric, \
				qty_annual numeric,qty_bale_annual numeric,cont_annual numeric,subtotal_annual numeric) AS $$ \
			DECLARE \
			BEGIN \
				RETURN QUERY \
					with sm_daily as \
						( \
						select \
							sl3.id as loc_id, \
							sl3.name as loc_name, \
							mbc.id as blend_id, \
							mbc.name as blend, \
							sum(round(sm.product_qty/pusm.factor*pupt.factor,4)) as qty_kg, \
							sum(cont_grp.total_container::numeric*cs.teus::numeric) as cont, \
							sum(round(1.0/rcrinv.rate*ail.price_subtotal,2)) as price_subtotal_usd \
						from stock_move sm \
							left join product_product pp on sm.product_id=pp.id \
							left join product_template pt on pp.product_tmpl_id=pt.id \
							left join product_uom pupt on pt.uom_id=pupt.id \
							left join product_uom pusm on sm.product_uom=pusm.id \
							left join mrp_blend_code mbc on pp.blend_code=mbc.id \
							left join stock_location sl1 on sm.location_id=sl1.id \
							left join stock_location sl2 on sm.location_dest_id=sl2.id \
							left join \
								(select split_part(value_reference,',',2)::int as location_id,split_part(res_id,',',2)::int as product_tmpl_id \
								from ir_property \
								where name='property_stock_production' and value_reference is not NULL and res_id is not NULL \
								) ip on ip.product_tmpl_id = pt.id \
							left join stock_location sl3 on ip.location_id=sl3.id \
							left join stock_location sl4 on sl3.location_id=sl3.id \
							left join stock_picking sp on sm.picking_id=sp.id \
							left join container_size cs on sp.container_size=cs.id \
							left join container_type ct on cs.type=ct.id \
							left join sale_order_line sol on sm.sale_line_id=sol.id \
							left join sale_order so on sol.order_id=so.id \
							left join account_invoice_line ail on sm.invoice_line_id=ail.id \
							left join account_invoice ai on ail.invoice_id=ai.id \
							left join ( \
								select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
								from account_invoice inv \
									inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
								where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
								and inv.type='out_invoice' and inv.goods_type='finish' \
								and inv.sale_type =stype \
								group by inv.id,rcrinv.currency_id \
								) rcrai on rcrai.id = ai.id \
							left join res_currency_rate rcrinv on rcrinv.currency_id = ai.currency_id and rcrai.curr_date = rcrinv.name \
							left join ( \
								select sp1.id,cs1.total_container,min(sm1.id) as move_id \
								from stock_move sm1 \
									left join stock_picking sp1 on sm1.picking_id=sp1.id \
									left join container_size cs1 on sp1.container_size=cs1.id \
									left join container_type ct1 on cs1.type=ct1.id \
								group by sp1.id,cs1.total_container \
								) cont_grp on cont_grp.move_id=sm.id \
						where \
							sm.date::date=daily \
							and sl1.usage='internal' and sl2.usage='customer' \
							and sp.type='out' \
							and so.sale_type=stype \
							and pp.internal_type='Finish' \
							and sm.state='done' \
						group by sl3.id,sl3.name,mbc.id,mbc.name \
						order by sl3.name,mbc.name \
						), \
					sm_monthly as \
						( \
						select \
							sl3.id as loc_id, \
							sl3.name as loc_name, \
							mbc.id as blend_id, \
							mbc.name as blend, \
							sum(round(sm.product_qty/pusm.factor*pupt.factor,4)) as qty_kg, \
							sum(cont_grp.total_container::numeric*cs.teus::numeric) as cont, \
							sum(round(1.0/rcrinv.rate*ail.price_subtotal,2)) as price_subtotal_usd \
						from stock_move sm \
							left join product_product pp on sm.product_id=pp.id \
							left join product_template pt on pp.product_tmpl_id=pt.id \
							left join product_uom pupt on pt.uom_id=pupt.id \
							left join product_uom pusm on sm.product_uom=pusm.id \
							left join mrp_blend_code mbc on pp.blend_code=mbc.id \
							left join stock_location sl1 on sm.location_id=sl1.id \
							left join stock_location sl2 on sm.location_dest_id=sl2.id \
							left join \
								(select split_part(value_reference,',',2)::int as location_id,split_part(res_id,',',2)::int as product_tmpl_id \
								from ir_property \
								where name='property_stock_production' and value_reference is not NULL and res_id is not NULL \
								) ip on ip.product_tmpl_id = pt.id \
							left join stock_location sl3 on ip.location_id=sl3.id \
							left join stock_location sl4 on sl3.location_id=sl3.id \
							left join stock_picking sp on sm.picking_id=sp.id \
							left join container_size cs on sp.container_size=cs.id \
							left join container_type ct on cs.type=ct.id \
							left join sale_order_line sol on sm.sale_line_id=sol.id \
							left join sale_order so on sol.order_id=so.id \
							left join account_invoice_line ail on sm.invoice_line_id=ail.id \
							left join account_invoice ai on ail.invoice_id=ai.id \
							left join ( \
								select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
								from account_invoice inv \
									inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
								where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
								and inv.type='out_invoice' and inv.goods_type='finish' \
								and inv.sale_type =stype \
								group by inv.id,rcrinv.currency_id \
								) rcrai on rcrai.id = ai.id \
							left join res_currency_rate rcrinv on rcrinv.currency_id = ai.currency_id and rcrai.curr_date = rcrinv.name \
							left join ( \
								select sp1.id,cs1.total_container,min(sm1.id) as move_id \
								from stock_move sm1 \
									left join stock_picking sp1 on sm1.picking_id=sp1.id \
									left join container_size cs1 on sp1.container_size=cs1.id \
									left join container_type ct1 on cs1.type=ct1.id \
								group by sp1.id,cs1.total_container \
								) cont_grp on cont_grp.move_id=sm.id \
						where \
							sm.date::date>=start_mth \
							and sm.date::date<=end_mth \
							and sl1.usage='internal' and sl2.usage='customer' \
							and sp.type='out' \
							and so.sale_type=stype \
							and pp.internal_type='Finish' \
							and sm.state='done' \
						group by sl3.id,sl3.name,mbc.id,mbc.name \
						order by sl3.name,mbc.name \
						), \
					sm_year as \
						( \
						select \
							sl3.id as loc_id, \
							sl3.name as loc_name, \
							mbc.id as blend_id, \
							mbc.name as blend, \
							sum(round(sm.product_qty/pusm.factor*pupt.factor,4)) as qty_kg, \
							sum(cont_grp.total_container::numeric*cs.teus::numeric) as cont, \
							sum(round(1.0/rcrinv.rate*ail.price_subtotal,2)) as price_subtotal_usd \
						from stock_move sm \
							left join product_product pp on sm.product_id=pp.id \
							left join product_template pt on pp.product_tmpl_id=pt.id \
							left join product_uom pupt on pt.uom_id=pupt.id \
							left join product_uom pusm on sm.product_uom=pusm.id \
							left join mrp_blend_code mbc on pp.blend_code=mbc.id \
							left join stock_location sl1 on sm.location_id=sl1.id \
							left join stock_location sl2 on sm.location_dest_id=sl2.id \
							left join \
								(select split_part(value_reference,',',2)::int as location_id,split_part(res_id,',',2)::int as product_tmpl_id \
								from ir_property \
								where name='property_stock_production' and value_reference is not NULL and res_id is not NULL \
								) ip on ip.product_tmpl_id = pt.id \
							left join stock_location sl3 on ip.location_id=sl3.id \
							left join stock_location sl4 on sl3.location_id=sl3.id \
							left join stock_picking sp on sm.picking_id=sp.id \
							left join container_size cs on sp.container_size=cs.id \
							left join container_type ct on cs.type=ct.id \
							left join sale_order_line sol on sm.sale_line_id=sol.id \
							left join sale_order so on sol.order_id=so.id \
							left join account_invoice_line ail on sm.invoice_line_id=ail.id \
							left join account_invoice ai on ail.invoice_id=ai.id \
							left join ( \
								select inv.id, inv.currency_id, max(rcrinv.name) as curr_date \
								from account_invoice inv \
									inner join res_currency_rate rcrinv on inv.currency_id = rcrinv.currency_id \
								where to_char(rcrinv.name,'YYYY-MM-DD') <= to_char(inv.date_invoice,'YYYY-MM-DD') \
								and inv.type='out_invoice' and inv.goods_type='finish' \
								and inv.sale_type =stype \
								group by inv.id,rcrinv.currency_id \
								) rcrai on rcrai.id = ai.id \
							left join res_currency_rate rcrinv on rcrinv.currency_id = ai.currency_id and rcrai.curr_date = rcrinv.name \
							left join ( \
								select sp1.id,cs1.total_container,min(sm1.id) as move_id \
								from stock_move sm1 \
									left join stock_picking sp1 on sm1.picking_id=sp1.id \
									left join container_size cs1 on sp1.container_size=cs1.id \
									left join container_type ct1 on cs1.type=ct1.id \
								group by sp1.id,cs1.total_container \
								) cont_grp on cont_grp.move_id=sm.id \
						where \
							sm.date::date>=start_year \
							and sm.date::date<=end_year \
							and sl1.usage='internal' and sl2.usage='customer' \
							and sp.type='out' \
							and so.sale_type=stype \
							and pp.internal_type='Finish' \
							and sm.state='done' \
						group by sl3.id,sl3.name,mbc.id,mbc.name \
						order by sl3.name,mbc.name \
						) \
				select \
					coalesce(s3.loc_name,s2.loc_name,s1.loc_name) as loc_name, \
					coalesce(s3.blend,s2.blend,s1.blend) as blend, \
					s1.qty_kg as qty_daily, \
					round(s1.qty_kg/181.44,2) as qty_bale_daily, \
					s1.cont as cont_daily, \
					s1.price_subtotal_usd as subtotal_daily, \
					s2.qty_kg as qty_monthly, \
					round(s2.qty_kg/181.44,2) as qty_bale_monthly, \
					s2.cont as cont_monthly, \
					s2.price_subtotal_usd as subtotal_monthly, \
					s3.qty_kg as qty_annual, \
					round(s3.qty_kg/181.44,2) as qty_bale_annual, \
					s3.cont as cont_annual, \
					s3.price_subtotal_usd as subtotal_annual \
				from sm_daily s1 \
					full outer join sm_monthly s2 on s1.loc_id=s2.loc_id and s1.blend_id=s2.blend_id \
					full outer join sm_year s3 on s2.loc_id=s3.loc_id and s2.blend_id=s3.blend_id \
				order by s3.loc_name,s3.blend,s2.loc_name,s2.blend,s1.blend,s1.loc_name; \
				END; \
			$$ LANGUAGE plpgsql; \
			")