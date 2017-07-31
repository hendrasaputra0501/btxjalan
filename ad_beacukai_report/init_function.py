from openerp.osv import fields,osv

class stock_wip_functions(osv.osv):
	_name = "stock.wip.functions"

	def init(self,cr):
		cr.execute("""
			CREATE OR REPLACE FUNCTION opening_wip_beacukai(date_start timestamp,class_id int)
			RETURNS TABLE (qty numeric) AS $$
			DECLARE
			BEGIN
			RETURN QUERY
			select sum(op_wip.qty) from 
				(
				select sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date<date_start and sm.location_dest_id in (select id from stock_location where usage='internal') 
				and sm.location_id not in (select id from stock_location where usage='internal')
				and sm.state='done' 
				UNION
				select -1*sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date<date_start and sm.location_dest_id not in (select id from stock_location where usage='internal') 
				and sm.location_id in (select id from stock_location where usage='internal')
				and sm.state='done' 
				) op_wip
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute("""
			CREATE OR REPLACE FUNCTION incoming_wip_beacukai(date_start timestamp,class_id int)
			RETURNS TABLE (qty numeric) AS $$
			DECLARE
			BEGIN
			RETURN QUERY

			select sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
			from stock_move sm 
			left join product_product pp on sm.product_id=pp.id
			left join product_template pt on pp.product_tmpl_id=pt.id
			left join product_uom pu1 on sm.product_uom=pu1.id
			left join product_uom pu2 on pt.uom_id=pu2.id
			where 
			sm.product_id in (select id from product_product where rm_class_id=class_id) and
			sm.date=date_start and sm.location_dest_id in (select id from stock_location where usage='internal') 
			and sm.location_id not in (select id from stock_location where usage='supplier')
			and sm.state='done' 
			;
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute("""
			CREATE OR REPLACE FUNCTION closing_wip_beacukai(date_start timestamp,class_id int)
			RETURNS TABLE (qty numeric) AS $$
			DECLARE
			BEGIN
			RETURN QUERY

			select sum(op_wip.qty) from 
				(
				select sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date<=date_start and sm.location_dest_id in (select id from stock_location where usage='internal') 
				and sm.location_id not in (select id from stock_location where usage='internal')
				and sm.state='done' 
				UNION
				select -1*sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date<=date_start and sm.location_dest_id not in (select id from stock_location where usage='internal') 
				and sm.location_id in (select id from stock_location where usage='internal')
				and sm.state='done' 
				) op_wip
				;
			END;
			$$ LANGUAGE plpgsql;
			""")
		cr.execute("""
			CREATE OR REPLACE FUNCTION adj_wip_beacukai(date_start timestamp,class_id int)
			RETURNS TABLE (qty numeric) AS $$
			DECLARE
			BEGIN
			RETURN QUERY

			select sum(op_wip.qty) from 
				(
				select sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date=date_start and sm.location_dest_id in (select id from stock_location where usage='internal') 
				and sm.location_id not in (select id from stock_location where usage='inventory')
				and sm.state='done' 
				UNION
				select -1*sum(pu2.factor/pu1.factor*sm.product_qty) as qty 
				from stock_move sm 
				left join product_product pp on sm.product_id=pp.id
				left join product_template pt on pp.product_tmpl_id=pt.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on pt.uom_id=pu2.id
				where 
				sm.product_id in (select id from product_product where rm_class_id=class_id) and
				sm.date=date_start and sm.location_dest_id not in (select id from stock_location where usage='inventory') 
				and sm.location_id in (select id from stock_location where usage='internal')
				and sm.state='done' 
				) op_wip
				;
			END;
			$$ LANGUAGE plpgsql;
			""")