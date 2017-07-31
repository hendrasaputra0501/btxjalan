from openerp.osv import fields,osv

class function_product_stock(osv.osv):
	_name = "function.product.stock"

	def init(self, cr):
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_opening(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date < date_limit
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_dest_id, product_id,product_uop,tracking_id 
					
					UNION ALL
					
					select location_id as loc_id,product_id,product_uop,-1*sum(qty_kg) as qty,-1*sum(product_uop_qty) as product_uop_qty,tracking_id
					from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date < date_limit
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy2
					group by location_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")

		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_opening_2(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uom_qty numeric) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				select dummy3.loc_id,product_id,sum(qty) as qty
					from (
					select location_dest_id as loc_id,product_id,sum(qty_kg) as qty
					from (select sm.location_dest_id, sm.product_id, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date < date_limit
					order by sm.location_dest_id,sm.product_id) sm_dummy 
					group by location_dest_id, product_id
					
					UNION ALL
					
					select location_id as loc_id,product_id,-1*sum(qty_kg) as qty
					from (select sm.location_id, sm.product_id,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date < date_limit
					order by sm.location_id,sm.product_id) sm_dummy2
					group by location_id, product_id 
				) dummy3
				group by dummy3.loc_id, product_id
				order by dummy3.loc_id, product_id
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")

		cr.execute(""" 
			CREATE OR REPLACE FUNCTION get_transfers(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_prod_ids int[],loc_supp_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uom_qty numeric) AS $$
			DECLARE
				prod RECORD;
				loc RECORD;
			BEGIN
				CREATE TEMP TABLE IF NOT EXISTS temp_transfers(
					tloc_id integer,
					tprod_id integer,
					tuom_qty numeric
					) ON COMMIT DROP;
				FOR loc IN (select id from stock_location where id=any(location_ids)) 
				LOOP
					FOR prod IN (select id from product_product where id=any(prod_ids)) 
					LOOP
						INSERT INTO temp_transfers(tloc_id,tprod_id,tuom_qty)
						select loc.id, prod.id, sum(qty) from (
							select 
								sl.name as dest_name, sl2.name as source, pp.name_template, 
								sm_dummy3.location_id as source, location_dest_id as dest_id, product_id, 
								sum(case 
									when sm_dummy3.location_id=loc.id then -1*qty_kg 
									else qty_kg 
								end) as qty 
							from 
								(
								select 
									sm.location_dest_id, sm.location_id, sm.product_id, 
									round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
								from stock_move sm left join product_product pp on sm.product_id = pp.id 
									left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id
									left join product_uom pu_pt on pt.uom_id = pu_pt.id  
									left join stock_picking sp on sm.picking_id=sp.id
								where  
									(sm.location_dest_id = loc.id 
									or sm.location_id = loc.id) 
									and sm.product_id=prod.id
									and sm.state in ('done') 
									and sm.date >= date_start 
									and sm.date <= date_end
									and sp.type='internal'
								order by sm.location_dest_id,sm.product_id) sm_dummy3 
								left join product_product pp on sm_dummy3.product_id = pp.id
								left join stock_location sl on sm_dummy3.location_dest_id = sl.id
								left join stock_location sl2 on sm_dummy3.location_id = sl2.id
							group by sm_dummy3.location_id,location_dest_id, product_id ,sl.name,sl2.name,pp.name_template) ds;
					END LOOP;
				END LOOP;
				RETURN QUERY 
					SELECT tloc_id, tprod_id, tuom_qty FROM temp_transfers ORDER BY tloc_id;
			END;
			$$ LANGUAGE plpgsql;
			""")

		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_incoming(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_prod_ids int[],loc_supp_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(location_ids) and sm.location_id = any(loc_prod_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_dest_id, product_id,product_uop,tracking_id 
					UNION ALL
					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(location_ids) and sm.location_id = any(loc_supp_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy2 
					group by location_dest_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_incoming_return(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_prod_ids int[],loc_supp_ids int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_prod_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_id, product_id,product_uop,tracking_id 
					UNION ALL
					select location_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_supp_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_fg(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_cust_ids int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_cust_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_id, product_id,product_uop,tracking_id 
					
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_fg_2(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_cust_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uom_qty numeric) AS $$
			DECLARE
			BEGIN

				RETURN QUERY 
				select dummy3.loc_id,product_id,sum(qty) as qty
					from (
					select location_id as loc_id,product_id,sum(qty_kg) as qty
						from (select sm.location_id, sm.product_id,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_cust_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_id,sm.product_id) sm_dummy 
					group by location_id, product_id
				) dummy3
				group by dummy3.loc_id, product_id 
				order by dummy3.loc_id, product_id 
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_fg_return(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_cust_ids int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(location_ids) and sm.location_id = any(loc_cust_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_dest_id, product_id,product_uop,tracking_id 
					
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_fg_return_2(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_cust_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uom_qty numeric) AS $$
			DECLARE
			BEGIN

				RETURN QUERY 
				select dummy3.loc_id,product_id,sum(qty) as qty
					from (
					select location_dest_id as loc_id,product_id,sum(qty_kg) as qty
						from (select sm.location_dest_id, sm.product_id,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(location_ids) and sm.location_id = any(loc_cust_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_dest_id,sm.product_id ) sm_dummy 
					group by location_dest_id, product_id 
					
				) dummy3
				group by dummy3.loc_id, product_id 
				order by dummy3.loc_id, product_id 
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_issue(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_issue int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_id as loc_id,product_id,product_uop,-1*sum(qty_kg) as qty,-1*sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_issue) and sm.location_dest_id not in (select id from stock_location where usage='production') and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_id, product_id,product_uop,tracking_id 

					UNION ALL

					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_issue) and sm.location_id not in (select id from stock_location where usage='production') and sm.location_dest_id = any(location_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy2 
					group by location_dest_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_opname_moves(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_issue int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				 RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_id as loc_id,product_id,product_uop,-1*sum(qty_kg) as qty,-1*sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(location_ids) and sm.location_dest_id = any(loc_issue) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end and sm.picking_id is NULL
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_id, product_id,product_uop,tracking_id 

					UNION ALL

					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
						from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_issue) and sm.location_dest_id = any(location_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end and sm.picking_id is NULL
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy2 
					group by location_dest_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_closing(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			BEGIN

				RETURN QUERY 
				select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (
					select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
					from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date <= date_limit
					order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
					group by location_dest_id, product_id,product_uop,tracking_id 
					
					UNION ALL
					
					select location_id as loc_id,product_id,product_uop,-1*sum(qty_kg) as qty,-1*sum(product_uop_qty) as product_uop_qty,tracking_id
					from (select sm.location_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
						sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date <= date_limit
					order by sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy2
					group by location_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				;
				
			END;
			$$ LANGUAGE plpgsql;
			"""
			)
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_closing_2(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uom_qty numeric) AS $$
			DECLARE
			BEGIN

				RETURN QUERY 
				select dummy3.loc_id,product_id,sum(qty) as qty
					from (
					select location_dest_id as loc_id,product_id,sum(qty_kg) as qty
					from (select sm.location_dest_id, sm.product_id, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_dest_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date <= date_limit
					order by sm.location_dest_id,sm.product_id ) sm_dummy 
					group by location_dest_id, product_id 
					
					UNION ALL
					
					select location_id as loc_id,product_id,-1*sum(qty_kg) as qty 
					from (select sm.location_id, sm.product_id,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg
						from stock_move sm left join product_product pp on sm.product_id = pp.id 
						left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
						left join product_uom pu_pt on pt.uom_id = pu_pt.id 
					where  sm.location_id = any(loc_dest_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date <= date_limit
					order by sm.location_id,sm.product_id ) sm_dummy2
					group by location_id, product_id 
				) dummy3
				group by dummy3.loc_id, product_id 
				order by dummy3.loc_id, product_id 
				;
				
			END;
			$$ LANGUAGE plpgsql;
			"""
			)
		cr.execute("""
			CREATE OR REPLACE FUNCTION get_rm_pm_used(date_start timestamp,date_end timestamp,prod_ids int[],location_ids int[],loc_prod_ids int[],loc_supp_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer,uop_id integer,uom_qty numeric,uop_qty numeric,track_id integer) AS $$
			DECLARE
			rec RECORD;
			BEGIN
			  CREATE TEMP TABLE IF NOT EXISTS temp_rm_pm_used 
			  (
				 loc_id integer,
				 product_id integer,
				 product_uop integer,
				 qty numeric,
				 product_uop_qty numeric,
				 tracking_id numeric
			  )
			  ON COMMIT DROP;

			FOR rec in
				(select dummy3.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
				from ( 
				select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
				from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
				sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
				left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
				left join product_uom pu_pt on pt.uom_id = pu_pt.id 
				where  sm.location_dest_id = any(location_ids) and sm.location_id = any(loc_prod_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
				order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummy 
				group by location_dest_id, product_id,product_uop,tracking_id 
				) dummy3
				group by dummy3.loc_id, product_id,product_uop,tracking_id 
				order by dummy3.loc_id, product_id,tracking_id, product_uop
				)

			LOOP 
				insert into temp_rm_pm_used (loc_id,product_id,product_uop,qty,product_uop_qty,tracking_id) 
				select rec.loc_id,mrp_bom.product_id,rec.product_uop,rec.qty*mb_line.comp_percentage/100.0,rec.product_uop_qty*mb_line.comp_percentage/100.0 
				from mrp_bom as mb_line left join mrp_bom mb_parent on mb_line.bom_id=mb_parent.id where mb_parent.product_id=rec.product_id;
			END LOOP;

			RETURN QUERY 
			select dummy4.loc_id,product_id,product_uop,sum(qty) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id
				from ( 
				select location_dest_id as loc_id,product_id,product_uop,sum(qty_kg) as qty,sum(product_uop_qty) as product_uop_qty,tracking_id 
				from (select sm.location_dest_id, sm.product_id, sm.product_uop,round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg,
				sm.product_uop_qty, coalesce(sm.tracking_id,0) as tracking_id from stock_move sm left join product_product pp on sm.product_id = pp.id 
				left join product_template pt on pp.product_tmpl_id = pt.id left join product_uom pu_sm on sm.product_uom = pu_sm.id 
				left join product_uom pu_pt on pt.uom_id = pu_pt.id 
				where  sm.location_dest_id = any(location_ids) and sm.location_dest_id = any(loc_prod_ids) and sm.product_id=any(prod_ids) and sm.state in ('done') and sm.date >= date_start and sm.date <= date_end
				order by sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop) sm_dummyx 
				group by location_dest_id, product_id,product_uop,tracking_id 
				UNION ALL
				select loc_id,product_id,product_uop,-1*sum(qty) as qty,-1*sum(product_uop_qty) as product_uop_qty,tracking_id
				from temp_rm_pm_used 
				group by loc_id, product_id,product_uop,tracking_id ) dummy4
			group by dummy4.loc_id, product_id,product_uop,tracking_id 
			order by dummy4.loc_id, product_id,tracking_id, product_uop;

			END;
			$$ LANGUAGE plpgsql;
			""")
		
		# query opening fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_opening_fifo(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT sub.loc_id, sub.product_id, sub.tracking_id, sub.uop_id, sub.uop_quantity, sub.uom_id, sub.qty, sub.amount::numeric(16,2) as amount FROM 
					(SELECT
						dummy.product_id, dummy.tracking_id, dummy.uop_id, dummy.uom_id, 
						sum(case coalesce(dummy.avg_uop,0.0) when 0.0 then 0.0 else round(coalesce(dummy.qty,0.0)::numeric(16,4)/coalesce(dummy.avg_uop,0.0)) end) as uop_quantity, 
						sum(coalesce(dummy.qty,0.0)) as qty, 
						sum(coalesce(dummy.amount,0.0)::numeric(16,4)) as amount,
						dummy.loc_id
					FROM 
						(SELECT
							sm.product_id, 
							coalesce(sm.tracking_id,0) as tracking_id, 
							sm.product_uop as uop_id, sm.product_uom as uom_id, 
							(case coalesce(sm.product_uop_qty,0.0) when 0.0 then 0.0 else round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)/coalesce(sm.product_uop_qty,0.0) end) as avg_uop,  
							(round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0)) as qty,
							((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit) as amount,
							sm.location_dest_id as loc_id
						FROM
							stock_move sm
							INNER JOIN product_product pp ON pp.id=sm.product_id
							INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
							INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
							INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
							LEFT JOIN (
								SELECT 
									sm1.id as move_in_id,
									sum(round(round(smm.qty::numeric(16,4)/pu_sm1.factor,4)*pu_pt.factor,4)) as qty,
									sm1.location_dest_id
								FROM
									stock_move_matching smm
									INNER JOIN stock_move sm1 ON sm1.id=smm.move_in_id
									INNER JOIN stock_move sm2 ON sm2.id=smm.move_out_id
									INNER JOIN product_product pp ON pp.id=sm2.product_id
									INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
									INNER JOIN product_uom pu_sm1 ON pu_sm1.id=sm1.product_uom
									INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
								WHERE 
								sm1.date < date_limit
								and sm2.date < date_limit
								and sm1.location_dest_id = any(loc_dest_ids) 
								and sm2.location_id = any(loc_dest_ids) 
								and sm1.product_id=any(prod_ids)
								and sm2.product_id=any(prod_ids) 
								and sm1.state in ('done')
								and sm2.state in ('done')
							GROUP BY sm1.id,sm1.location_dest_id) moveout ON moveout.move_in_id=sm.id
						WHERE 
							sm.date < date_limit
							and sm.location_dest_id = any(loc_dest_ids) 
							and sm.product_id=any(prod_ids) 
							and sm.state in ('done')) dummy
					GROUP BY dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.uop_id, dummy.uom_id) sub
				WHERE sub.qty > 0
				ORDER BY sub.loc_id, sub.product_id
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		# query incoming fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_incoming_fifo(date_start timestamp, date_end timestamp, prod_ids int[], location_ids int[], loc_prod_ids int[], loc_supp_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT
					dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.product_uop, sum(coalesce(dummy.product_uop_qty,0.0)) as uop_qty, dummy.product_uom, sum(dummy.qty) as qty, sum(dummy.amount::numeric(16,2)) as amount
				FROM
					(SELECT
						sm.location_dest_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						(sm.price_unit*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_id = any(loc_supp_ids) 
						and sm.location_dest_id = any(location_ids) 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					) dummy
				GROUP BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id
				ORDER BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id 
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		# query incoming return fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_incoming_return_fifo(date_start timestamp, date_end timestamp, prod_ids int[], location_ids int[], loc_prod_ids int[], loc_supp_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT
					dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.product_uop, sum(coalesce(dummy.product_uop_qty,0.0)) as uop_qty, dummy.product_uom, sum(dummy.qty) as qty, sum(dummy.amount::numeric(16,2)) as amount
				FROM
					(SELECT
						sm.location_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						(sm.price_unit*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_id = any(location_ids) 
						and sm.location_dest_id = any(loc_supp_ids) 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					) dummy
				GROUP BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id
				ORDER BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id 
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		# query outgoing fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_fifo(date_start timestamp, date_end timestamp, prod_ids int[], location_ids int[], loc_prod_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT
					dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.product_uop, sum(coalesce(dummy.product_uop_qty,0.0)) as uop_qty, dummy.product_uom, sum(dummy.qty) as qty, sum(dummy.amount::numeric(16,2)) as amount
				FROM
					(SELECT
						sm.location_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						coalesce(smm.amt,0.0) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
						INNER JOIN (select sum(round((qty*price_unit_out)::numeric,2)) as amt,move_out_id from stock_move_matching group by move_out_id) smm on smm.move_out_id=sm.id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_id = any(location_ids) 
						and sm.location_dest_id = any(loc_prod_ids) 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					) dummy
				GROUP BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id
				ORDER BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id 
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		# query outgoing return fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_outgoing_return_fifo(date_start timestamp, date_end timestamp, prod_ids int[], location_ids int[], loc_prod_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT
					dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.product_uop, sum(coalesce(dummy.product_uop_qty,0.0)) as uop_qty, dummy.product_uom, sum(dummy.qty) as qty, sum(dummy.amount::numeric(16,2)) as amount
				FROM
					(SELECT
						sm.location_dest_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						(sm.price_unit*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_id = any(loc_prod_ids) 
						and sm.location_dest_id = any(location_ids) 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					) dummy
				GROUP BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id
				ORDER BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id 
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		# query adjustment and transfer fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_adjustment_fifo(date_start timestamp, date_end timestamp, prod_ids int[], location_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT
					dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.product_uop, sum(coalesce(dummy.product_uop_qty,0.0)) as uop_qty, dummy.product_uom, sum(dummy.qty) as qty, sum(dummy.amount::numeric(16,2)) as amount
				FROM
					(SELECT
						sm.location_id as loc_id, sm.product_id, 
						sm.product_uop, (-1*sm.product_uop_qty) as product_uop_qty, 
						sm.product_uom, (-1*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as qty,
						(sm.price_unit*-1*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
						INNER JOIN stock_location sl ON sl.id=sm.location_dest_id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_id = any(location_ids) 
						and sl.usage='internal' 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					UNION ALL
					SELECT
						sm.location_dest_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						(sm.price_unit*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
						INNER JOIN stock_location sl ON sl.id=sm.location_id
					WHERE
						sm.date between date_start and date_end
						and sm.picking_id is not NULL
						and sm.location_dest_id = any(location_ids) 
						and sl.usage='internal' 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
					UNION ALL
					SELECT
						sm.location_id as loc_id, sm.product_id, 
						sm.product_uop, (-1*sm.product_uop_qty) as product_uop_qty, 
						sm.product_uom, (-1*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as qty,
						(sm.price_unit*-1*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
						INNER JOIN stock_location sl ON sl.id=sm.location_dest_id
					WHERE
						sm.date between date_start and date_end
						and sm.location_id = any(location_ids) 
						and sl.usage='inventory' 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
						and sm.picking_id is NULL
					UNION ALL
					SELECT
						sm.location_dest_id as loc_id, sm.product_id, 
						sm.product_uop, sm.product_uop_qty, 
						sm.product_uom, round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty,
						(sm.price_unit*round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)) as amount,
						coalesce(sm.tracking_id,0) as tracking_id
					FROM
						stock_move sm
						INNER JOIN product_product pp ON pp.id=sm.product_id
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
						INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
						INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
						INNER JOIN stock_location sl ON sl.id=sm.location_id
					WHERE
						sm.date between date_start and date_end
						and sm.location_dest_id = any(location_ids) 
						and sl.usage='inventory' 
						and sm.product_id=any(prod_ids) 
						and sm.state in ('done')
						and sm.picking_id is NULL
					) dummy
				GROUP BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id
				ORDER BY  dummy.loc_id, dummy.product_id, dummy.product_uop, dummy.product_uom, dummy.tracking_id 
				;
			END;
			$$ LANGUAGE plpgsql;
			""") 
		# query closing fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_closing_fifo(date_limit timestamp,prod_ids int[],loc_ids int[],loc_dest_ids int[]) 
			RETURNS TABLE (loc_id integer,prod_id integer, track_id integer, uop integer, uop_qty numeric, uom integer, uom_qty numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT sub.loc_id, sub.product_id, sub.tracking_id, sub.uop_id, sub.uop_quantity, sub.uom_id, sub.qty, sub.amount::numeric(16,2) as amount FROM 
					(SELECT
						dummy.product_id, dummy.tracking_id, dummy.uop_id, dummy.uom_id, 
						sum(case coalesce(dummy.avg_uop,0.0) when 0.0 then 0.0 else round(coalesce(dummy.qty,0.0)::numeric(16,4)/coalesce(dummy.avg_uop,0.0)) end) as uop_quantity, 
						sum(coalesce(dummy.qty,0.0)) as qty, 
						sum(coalesce(dummy.amount,0.0)::numeric(16,4)) as amount,
						dummy.loc_id
					FROM 
						(SELECT
							sm.product_id, 
							coalesce(sm.tracking_id,0) as tracking_id, 
							sm.product_uop as uop_id, sm.product_uom as uom_id, 
							(case coalesce(sm.product_uop_qty,0.0) when 0.0 then 0.0 else round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)/coalesce(sm.product_uop_qty,0.0) end) as avg_uop,  
							(round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0)) as qty,
							((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit) as amount,
							sm.location_dest_id as loc_id
						FROM
							stock_move sm
							INNER JOIN product_product pp ON pp.id=sm.product_id
							INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
							INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
							INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
							LEFT JOIN (
								SELECT 
									sm1.id as move_in_id,
									sum(round(round(smm.qty::numeric(16,4)/pu_sm1.factor,4)*pu_pt.factor,4)) as qty,
									sm1.location_dest_id
								FROM
									stock_move_matching smm
									INNER JOIN stock_move sm1 ON sm1.id=smm.move_in_id
									INNER JOIN stock_move sm2 ON sm2.id=smm.move_out_id
									INNER JOIN product_product pp ON pp.id=sm2.product_id
									INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
									INNER JOIN product_uom pu_sm1 ON pu_sm1.id=sm1.product_uom
									INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
								WHERE 
								sm1.date <= date_limit
								and sm2.date <= date_limit
								and sm1.location_dest_id = any(loc_dest_ids) 
								and sm2.location_id = any(loc_dest_ids) 
								and sm1.product_id=any(prod_ids)
								and sm2.product_id=any(prod_ids) 
								and sm1.state in ('done')
								and sm2.state in ('done')
							GROUP BY sm1.id,sm1.location_dest_id) moveout ON moveout.move_in_id=sm.id
						WHERE 
							sm.date <= date_limit
							and sm.location_dest_id = any(loc_dest_ids) 
							and sm.product_id=any(prod_ids) 
							and sm.state in ('done')) dummy
					GROUP BY dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.uop_id, dummy.uom_id) sub
				WHERE sub.qty > 0
				ORDER BY sub.loc_id, sub.product_id
				;
			END;
			$$ LANGUAGE plpgsql;
			""")

		# query ageing fifo
		cr.execute(
			"""
			CREATE OR REPLACE FUNCTION get_ageing_fifo(date_limit timestamp, prod_ids int[], loc_ids int[], loc_dest_ids int[], period_length integer) 
			RETURNS TABLE (loc_id integer, prod_id integer, track_id integer, uom integer, qty1 numeric, amount_value1 numeric(16,2), qty2 numeric, amount_value2 numeric(16,2), qty3 numeric, amount_value3 numeric(16,2), qty4 numeric, amount_value4 numeric(16,2), uom_quantity numeric, amount_value numeric(16,2)) AS $$
			DECLARE
			BEGIN
				RETURN QUERY 
				SELECT 
					sub.loc_id, sub.product_id, sub.tracking_id, sub.uom_id, 
					sub.age_1, 
					sub.amount_1,
					sub.age_2, 
					sub.amount_2,
					sub.age_3, 
					sub.amount_3,
					sub.age_4, 
					sub.amount_4,
					sub.qty,
					sub.amount_closing 
				FROM 
					(SELECT
						dummy.product_id, dummy.tracking_id, dummy.uom_id, 
						sum(dummy.age1) as age_1,
						sum(dummy.amount1::numeric(16,2)) as amount_1,
						sum(dummy.age2) as age_2,
						sum(dummy.amount2::numeric(16,2)) as amount_2,
						sum(dummy.age3) as age_3,
						sum(dummy.amount3::numeric(16,2)) as amount_3,
						sum(dummy.age4) as age_4,
						sum(dummy.amount4::numeric(16,2)) as amount_4,
						sum(dummy.qty) as qty,
						sum(dummy.amount::numeric(16,2)) as amount_closing,
						dummy.loc_id
					FROM 
						(SELECT
							sm.product_id, 
							coalesce(sm.tracking_id,0) as tracking_id, 
							sm.product_uom as uom_id, 
							(round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0)) as qty,
							((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit) as amount,
							(case when 
								(sm.date<=date_limit and sm.date>=(SELECT date_trunc('MONTH', date_limit))) 
									then (round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))
								else 0.0 
							end) as age1,
							(case when 
								(sm.date<=date_limit and sm.date>=(SELECT date_trunc('MONTH', date_limit)))
									then ((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit)
								else 0.0 
							end) as amount1,
							(case when 
								(sm.date<=(SELECT (date_trunc('MONTH', date_limit) - INTERVAL '1 day' + INTERVAL '23 hour 59 minute 59 second')) 
									and sm.date>=(SELECT date_trunc('YEAR', date_limit)))
									then (round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))
								else 0.0 
							end) as age2, 
							(case when 
								(sm.date<=(SELECT (date_trunc('MONTH', date_limit) - INTERVAL '1 day' + INTERVAL '23 hour 59 minute 59 second')) 
									and sm.date>=(SELECT date_trunc('YEAR', date_limit)))
									then ((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit)
								else 0.0 
							end) as amount2, 
							(case when 
								(sm.date<=(SELECT (date_trunc('YEAR', date_limit) - INTERVAL '1 day' + INTERVAL '23 hour 59 minute 59 second')) 
									and sm.date>=(SELECT date_trunc('YEAR', date_limit) - INTERVAL '1 YEAR'))
									then (round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))
								else 0.0
							end) as age3, 
							(case when 
								(sm.date<=(SELECT (date_trunc('YEAR', date_limit) - INTERVAL '1 day' + INTERVAL '23 hour 59 minute 59 second')) 
									and sm.date>=(SELECT date_trunc('YEAR', date_limit) - INTERVAL '1 YEAR')) 
									then ((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit)
								else 0.0
							end) as amount3, 
							(case when 
								(sm.date<=(SELECT (date_trunc('YEAR', date_limit) - INTERVAL '1 YEAR 1 day' + INTERVAL '23 hour 59 minute 59 second')))
									then (round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))
								else 0.0
							end) as age4,
							(case when 
								(sm.date<=(SELECT (date_trunc('YEAR', date_limit) - INTERVAL '1 YEAR 1 day' + INTERVAL '23 hour 59 minute 59 second')))
									then ((round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4)-coalesce(moveout.qty,0.0))*sm.price_unit)
								else 0.0
							end) as amount4,
							sm.location_dest_id as loc_id
						FROM
							stock_move sm
							INNER JOIN product_product pp ON pp.id=sm.product_id
							INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
							INNER JOIN product_uom pu_sm ON pu_sm.id=sm.product_uom
							INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
							LEFT JOIN (
								SELECT 
									sm1.id as move_in_id,
									sum(round(round(smm.qty::numeric(16,4)/pu_sm1.factor,4)*pu_pt.factor,4)) as qty,
									sm1.location_dest_id
								FROM
									stock_move_matching smm
									INNER JOIN stock_move sm1 ON sm1.id=smm.move_in_id
									INNER JOIN stock_move sm2 ON sm2.id=smm.move_out_id
									INNER JOIN product_product pp ON pp.id=sm2.product_id
									INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
									INNER JOIN product_uom pu_sm1 ON pu_sm1.id=sm1.product_uom
									INNER JOIN product_uom pu_pt ON pu_pt.id=pt.uom_id
								WHERE 
								sm1.date <= date_limit
								and sm2.date <= date_limit
								and sm1.location_dest_id = any(loc_dest_ids) 
								and sm2.location_id = any(loc_dest_ids) 
								and sm1.product_id=any(prod_ids)
								and sm2.product_id=any(prod_ids) 
								and sm1.state in ('done')
								and sm2.state in ('done')
							GROUP BY sm1.id,sm1.location_dest_id) moveout ON moveout.move_in_id=sm.id
						WHERE 
							sm.date <= date_limit
							and sm.location_dest_id = any(loc_dest_ids) 
							and sm.product_id=any(prod_ids) 
							and sm.state in ('done')) dummy
					GROUP BY dummy.loc_id, dummy.product_id, dummy.tracking_id, dummy.uom_id) sub
				WHERE sub.qty > 0
				ORDER BY sub.loc_id, sub.product_id
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
