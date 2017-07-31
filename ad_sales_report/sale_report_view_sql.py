from openerp.osv import fields,osv
from openerp import tools


class sale_report_view_sql(osv.osv):
	_name = "sale.report.view.sql"
	_auto = False
	_rec_name = "product_id"
	_columns = {
		"blend_id"				: fields.many2one("mrp.blend.code","Blend",required=True),
		"product_id"			: fields.many2one("product.product","Product",required=True),
		"location_id"			: fields.many2one("stock.location","Source Location",required=True),
		"parent_location_id"	: fields.many2one("stock.location","Parent Location",required=True),
		"sale_type"				: fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"locale_sale_type"		: fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Local Sale Type",required=True),
		'goods_type' 			: fields.selection([('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],
			'Goods Type',required=True),
		"partner_id"			: fields.many2one("res.partner","Partner",required=True),
		"delivery_date"			: fields.date("Delivery Date",required=True),
		"currency_id"			: fields.many2one("res.currency","Currency",required=True),
		"sm_qty_kgs"			: fields.float("Qty(KGS)",group_operator="sum"),
		"net_price_unit_kgs"	: fields.float("Net Price Unit(KGS)",group_operator="sum"),
		"net_amount_kgs"		: fields.float("Net Amount(KGS)",group_operator="sum"),
		"gross_price_unit_kgs"	: fields.float("Gross Price(KGS)",group_operator="sum"),
		"gross_amount_kgs"		: fields.float("Gross Amount(KGS)",group_operator="sum"),

		"sm_qty_bales"			: fields.float("Qty(BALES)",group_operator="sum"),
		"net_price_unit_bales"	: fields.float("Net Price Unit(BALES)",group_operator="sum"),
		"net_amount_bales"		: fields.float("Net Amount(BALES)",group_operator="sum"),
		"gross_price_unit_bales": fields.float("Gross Price(BALES)",group_operator="sum"),
		"gross_amount_bales"	: fields.float("Gross Amount(BALES)",group_operator="sum"),

		}

	def init(self,cr):
		tools.drop_view_if_exists(cr, 'sale_report_view_sql')
		cr.execute(""" 
			create or replace view sale_report_view_sql as (
				select sm.id as id,
				sl.id as location_id,
				sl3.id as parent_location_id,
				sp.partner_id,
				sm.date::date as delivery_date,
				sm.product_id,
				pp.blend_code as blend_id,
				--sm.product_qty,
				ail.quantity as ail_quantity,
				round((sm.product_qty*pu3.factor/pu1.factor),4) as sm_qty_kgs,
				round((sm.product_qty*pu4.factor/pu1.factor),4) as sm_qty_bales,
				--round((ail.quantity*pu5.factor/pu2.factor),4) as ail_qty_kgs,
				--round((ail.quantity*pu6.factor/pu2.factor),4) as ail_qty_bales,
				sp.sale_type,
				sp.goods_type,
				so.locale_sale_type,
				ai.currency_id,
				round((sm.product_qty*pu3.factor/pu1.factor)/(ail.quantity*pu5.factor/pu2.factor)*(ail.price_subtotal+ail.tax_amount),2) as gross_amount_kgs,
				round((sm.product_qty*pu3.factor/pu1.factor)/(ail.quantity*pu5.factor/pu2.factor)*(ail.price_subtotal),2) as net_amount_kgs,
				round(((ail.price_subtotal+ail.tax_amount)/ail.quantity*pu2.factor/pu5.factor),2) as gross_price_unit_kgs,
				round((ail.price_subtotal/ail.quantity*pu2.factor/pu5.factor),2) as net_price_unit_kgs,
				round((sm.product_qty*pu4.factor/pu1.factor)/(ail.quantity*pu6.factor/pu2.factor)*(ail.price_subtotal+ail.tax_amount),2) as gross_amount_bales,
				round((sm.product_qty*pu4.factor/pu1.factor)/(ail.quantity*pu6.factor/pu2.factor)*(ail.price_subtotal),2) as net_amount_bales,
				round(((ail.price_subtotal+ail.tax_amount)/ail.quantity*pu2.factor/pu6.factor),2) as gross_price_unit_bales,
				round((ail.price_subtotal/ail.quantity*pu2.factor/pu6.factor),2) as net_price_unit_bales
				from stock_move sm
				left join stock_picking sp on sm.picking_id=sp.id
				left join stock_location sl on sm.location_id=sl.id
				left join stock_location sl2 on sl.location_id=sl2.id
				left join stock_location sl3 on sl2.location_id=sl3.id
				left join sale_order so on sp.sale_id=so.id
				left join account_invoice_line ail on sm.invoice_line_id=ail.id or (sm.product_id=ail.product_id and sp.invoice_id=ail.invoice_id)
				left join account_invoice ai on sp.invoice_id=ai.id
				left join product_uom pu1 on sm.product_uom=pu1.id
				left join product_uom pu2 on ail.uos_id=pu2.id
				left join product_product pp on pp.id=sm.product_id
				left join mrp_blend_code mbc on mbc.id=pp.blend_code
				left join (select puv.factor,puv.category_id from product_uom puv where name='KGS') pu3 on pu3.category_id=pu1.category_id
				left join (select puw.factor,puw.category_id from product_uom puw where name='BALES') pu4 on pu4.category_id=pu1.category_id
				left join (select pux.factor,pux.category_id from product_uom pux where name='KGS') pu5 on pu5.category_id=pu2.category_id
				left join (select puy.factor,puy.category_id from product_uom puy where name='BALES') pu6 on pu6.category_id=pu2.category_id

				where
				sp.type='out' and sp.state='done' and sm.state='done' and sp.invoice_state='invoiced' 
				order by sl.id,sm.product_id,ail.id
				)
			""")