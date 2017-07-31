from openerp.osv import fields,osv

class function_pending_order(osv.osv):
	_name = "function.pending.order"

	def init(self, cr):
		cr.execute(" \
			CREATE OR REPLACE FUNCTION lc_shipment_sol(as_on_date timestamp,gtype text, stype text)  \
			RETURNS TABLE (shipped_sol_qty numeric,shipped_lc_qty numeric,lc_qty numeric,sol_id integer,lc_prod_line_id integer,lc_id integer,prod_id integer,lc_rcvd_smg date,lc_lsd date,schd_date date) AS $$  \
			DECLARE  \
			BEGIN  \
			    RETURN QUERY  \
				select  \
					dum_smm.shipped_qty as shipped_sol_qty,  \
					dum_sml.shipped_qty as shipped_lc_qty,  \
					dum_sml.product_uom_qty,  \
					sol.id as sol_id,  \
					lpl.id,  \
					dum_sml.id as lc_id,  \
					sol.product_id,  \
					lc.rcvd_smg,  \
					lpl.est_delivery_date as est_delivery_date,  \
					sm2.date_expected as schd_date  \
				\
				from sale_order_line sol\
					left join stock_move sm on sm.sale_line_id=sol.id  \
					inner join product_uom pusol1 on sol.product_uom=pusol1.id  \
					left join product_uom pusol2 on sm.product_uom=pusol2.id  \
					left join stock_picking sp on sm.picking_id=sp.id  \
					left join (\
						select sale_line_id,min(date_expected::date)::date as date_expected \
						from stock_move where state='draft' and sale_line_id is not NULL group by sale_line_id) sm2 on sm2.sale_line_id=sol.id  \
					left join stock_location sl1 on sm.location_id=sl1.id  \
					left join stock_location sl2 on sm.location_dest_id=sl2.id  \
					left join letterofcredit_product_line lpl on (lpl.id=sm.lc_product_line_id or sol.id=lpl.sale_line_id)  \
					inner join letterofcredit lc on lc.id = lpl.lc_id and lc.state <> 'nonactive'  \
					left join (  \
						select  \
							solm.id as sale_line_id,solm.product_id, \
							case when spm.type='out' then  \
								sum(round((coalesce(smm.product_qty,0.0)/coalesce(pum2.factor,1.0))*coalesce(pum1.factor,0.0),4))  \
							else  \
								sum(round((coalesce(-1*smm.product_qty,0.0)/coalesce(pum2.factor,1.0))*coalesce(pum1.factor,0.0),4))  \
							end as shipped_qty  \
							\
						from  sale_order_line solm\
							left join (\
								select smx1.*\
								from stock_move smx1\
									inner join stock_picking spmx1 on smx1.picking_id=spmx1.id\
									inner join stock_location slmx1 on smx1.location_id=slmx1.id  \
									inner join stock_location slmx2 on smx1.location_dest_id=slmx2.id  \
								where\
									smx1.date::date<=as_on_date::date and smx1.state='done'\
									and ((slmx1.usage='internal' and slmx2.usage='customer') or (slmx1.usage='customer' and slmx2.usage='internal'))  \
									and spmx1.goods_type=gtype and spmx1.sale_type=stype\
								) smm on (smm.sale_line_id=solm.id )\
							left join product_uom pum1 on solm.product_uom=pum1.id\
							left join stock_picking spm on smm.picking_id=spm.id  \
							left join stock_location slm1 on smm.location_id=slm1.id  \
							left join stock_location slm2 on smm.location_dest_id=slm2.id  \
							left join product_uom pum2 on smm.product_uom=pum2.id  \
						group by solm.id,solm.product_id,spm.type \
						) dum_smm on sol.id=dum_smm.sale_line_id and sol.product_id=dum_smm.product_id  \
					left join (  \
						select  \
							lpl_l.id,  \
							sol_l.product_id,  \
							lpl_l.lc_id,  \
							lpl_l.product_uom_qty,  \
							case when sml.spx_type='out' then  \
								sum(round((coalesce(sml.product_qty,0.0)/coalesce(pul2.factor,1.0))*coalesce(pul1.factor,0.0),4))  \
							else  \
								sum(round((coalesce(-1*sml.product_qty,0.0)/coalesce(pul2.factor,1.0))*coalesce(pul1.factor,0.0),4))  \
							end as shipped_qty,  \
							min(lpl_l.est_delivery_date) as lc_lsd_min  \
						from letterofcredit_product_line lpl_l  \
							left join (  \
								select smx.*,spx.type as spx_type  \
								from stock_move smx  \
								left join stock_location slx1 on smx.location_id=slx1.id  \
								left join stock_location slx2 on smx.location_dest_id=slx2.id  \
								left join stock_picking spx on smx.picking_id=spx.id  \
								where smx.date::date<=as_on_date::date and smx.state='done'  \
								and ((slx1.usage='internal' and slx2.usage='customer') or (slx1.usage='customer' and slx2.usage='internal'))	  \
								and spx.goods_type=gtype and spx.sale_type=stype  \
							) sml  \
								on sml.lc_product_line_id=lpl_l.id  \
							inner join (select id,state from letterofcredit where state<>'nonactive') lc_l  \
								on lc_l.id=lpl_l.lc_id  \
							left join stock_picking spl on sml.picking_id=spl.id  \
							left join stock_location sll1 on sml.location_id=sll1.id  \
							left join stock_location sll2 on sml.location_dest_id=sll2.id  \
							left join sale_order_line sol_l on sol_l.id=lpl_l.sale_line_id  \
							left join product_uom pul1 on sol_l.product_uom=pul1.id  \
							left join product_uom pul2 on sml.product_uom=pul2.id  \
						where (lpl_l.knock_off <> True or lpl_l.date_knock_off::date<=as_on_date::date or lpl_l.date_knock_off is NULL ) \
						and lc_l.state!='nonactive'  \
						group by lpl_l.id,sol_l.product_id,sml.spx_type  \
						) dum_sml on lpl.id=dum_sml.id and dum_sml.product_id=sol.product_id  \
				group by sol.id,dum_sml.shipped_qty,dum_smm.shipped_qty,dum_sml.product_uom_qty,  \
				dum_sml.id,  \
				lpl.id,  \
				dum_sml.lc_id,sol.product_id,lc.rcvd_smg,  \
				lpl.est_delivery_date,sm2.date_expected \
				;  \
			END;  \
			$$ LANGUAGE plpgsql;  \
			")

		