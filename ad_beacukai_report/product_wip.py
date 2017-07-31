from openerp.osv import fields,osv
from openerp import tools

class product_wip_usage(osv.osv):
	_name = "product.wip.usage"
	_auto = False
	_columns = {
		"effective_date": fields.date("Date"),
		"name"			: fields.char("Product",size=64),	
		"rm_categ_id"	: fields.many2one("product.rm.type.category","Product"),
		"uom_id"		: fields.many2one("product.uom","Unit of Measure"),
		"usage_qty"		: fields.float("Usage Qty"),
		"waste_qty"		: fields.float("Waste Qty"),
	}

	def init(self,cr):
		tools.drop_view_if_exists(cr, 'product_wip_usage')
		cr.execute("""
			CREATE OR REPLACE view product_wip_usage AS (
				select
					used_rm.date as effective_date,
					used_rm.rm_cat_name as name,
					used_rm.rm_type_cat_id as rm_categ_id,
					used_rm.uom_pt as uom_id,
					sum(used_rm.usage) as usage_qty,
					sum(used_rm.waste) as waste_qty
				from 
					(
					select 
						sm.date::date,
						sm.product_id,
						pp.name_template as product_name,
						sm.product_qty,
						pu1.name as uom_sm,
						pu2.factor/pu1.factor*sm.product_qty as qty_convert,
						pu2.name as uom_pt,
						prtc.id as rm_type_cat_id,
						prtc.name as rm_cat_name,
						coalesce(mbcl.percentage,0.0)/100.0*(pu2.factor/pu1.factor*sm.product_qty) as usage,
						coalesce(mbcl.waste_percentage,0.0)/100.0*(pu2.factor/pu1.factor*sm.product_qty) as waste
					from stock_move sm
						left join stock_location sl_prod on sm.location_id=sl_prod.id
						left join stock_location sl_fg on sm.location_dest_id=sl_fg.id
						left join product_product pp on sm.product_id=pp.id
						left join product_template pt on pp.product_tmpl_id=pt.id
						left join product_uom pu1 on sm.product_uom=pu1.id
						left join product_uom pu2 on pt.uom_id=pu2.id
						left join mrp_blend_code mbc on pp.blend_code=mbc.id
						right join mrp_blend_code_line mbcl on mbcl.blend_id=mbc.id
						left join product_rm_type prt on prt.id=mbcl.rm_type_id
						left join product_rm_type_category prtc on prtc.id=prt.category_id
					where 
						sm.location_id in (select slp.id from stock_location slp where slp.usage='production') and
						sm.location_dest_id in (select slp.id from stock_location slp where slp.usage='internal') and
						pp.internal_type='Finish' and
						sm.state='done'
						order by sm.date,prtc.id
					) used_rm
				group by used_rm.date,used_rm.rm_type_cat_id,used_rm.rm_cat_name,used_rm.uom_pt
				order by used_rm.date,used_rm.rm_cat_name
				)
		""")


class report_product_wip_stock(osv.osv):
	_name = "report.product.wip.stock"
	_auto = False
	_columns = {
		"effective_date": fields.date("Date"),
		"name"			: fields.char("Product",size=64),	
		"rm_categ_id"	: fields.many2one("product.rm.type.category","Product"),
		"uom_id"		: fields.many2one("product.uom","Unit of Measure"),
		"opening"		: fields.float("Opening Qty"),
		"incoming"		: fields.float("Incoming Qty"),
		"usage"			: fields.float("Usage Qty"),
		"waste"			: fields.float("Waste Qty"),
		"closing"		: fields.float("Closing Qty"),
		"adjustment"	: fields.float("Adjustment"),
	}
	_order="effective_date asc,name asc"

	def init(self,cr):
		tools.drop_view_if_exists(cr, 'report_product_wip_stock')
		cr.execute("""
			CREATE OR REPLACE view report_product_wip_stock AS (
					select 
					row_number() OVER () as id,
					a.effective_date::date as effective_date,
					c.code as name,
					a.id as rm_categ_id,
					c.uom_id,
					opening_wip_beacukai(a.effective_date::timestamp,a.id) as opening,
					incoming_wip_beacukai(a.effective_date::timestamp,a.id) as incoming,
					b.usage_qty as usage,
					b.waste_qty as waste,
					closing_wip_beacukai(a.effective_date::timestamp,a.id) as closing,
					adj_wip_beacukai(a.effective_date::timestamp,a.id) as adjustment
					from (
					select prtc.id,
					prtc.name, 
					generate_series((select min(date) from stock_move)::date, now()::date, '1 day'::interval) as effective_date
					from product_rm_type_category prtc) a
					left join product_wip_usage b on a.id=b.rm_categ_id and a.effective_date=b.effective_date
					left join product_rm_type_category c on a.id=c.id
					)
		""")