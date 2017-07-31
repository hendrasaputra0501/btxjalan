
from openerp.osv import fields,osv

class function_pending_order(osv.osv):
	_name = "function.pending.order"

	def init(self, cr):
		cr.execute(" \
			CREATE OR REPLACE FUNCTION get_purchase_line(date_start date, date_end date, department_ids int[],location_dest_id int[])  \
			RETURNS TABLE (line_id int) AS $$  \
			DECLARE  \
			BEGIN \
			    RETURN QUERY \
				    with\
					indent as (\
						SELECT\
							mrl.id as mr_line_id, prl.id as pr_line_id, pr.id as pr_id,\
							mrl.product_id as prod_id, mrl.location_id as site_id\
						FROM\
							material_request_line mrl\
							INNER JOIN material_request mr ON mr.id=mrl.requisition_id\
							INNER JOIN hr_department hd ON hd.id=mr.department and hd.id=any(department_ids)\
							INNER JOIN purchase_requisition_line prl ON prl.id=mrl.pr_line_id\
							INNER JOIN purchase_requisition pr ON pr.id=prl.requisition_id\
					)\
					SELECT\
						pol.id as pol_id\
					FROM\
						purchase_order po\
						INNER JOIN purchase_order_line pol ON pol.order_id=po.id\
						INNER JOIN res_partner rp ON rp.id=po.partner_id\
						INNER JOIN product_product pp ON pp.id=pol.product_id\
						INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id\
						LEFT JOIN (select rel.po_line_id,\
							string_agg(pd.discount_amt::text||(case pd.type when 'percentage' then\
							'%' else '' end),'+') as diskon\
							from price_discount_po_line_rel rel inner join price_discount pd ON\
							pd.id=rel.disc_id\
							group by rel.po_line_id) disc ON disc.po_line_id=pol.id\
						LEFT JOIN (select rel.ord_id, string_agg(at.name,',') as taxes\
							from purchase_order_taxe rel inner join account_tax at ON at.id=rel.tax_id\
							group by rel.ord_id) tax ON tax.ord_id=pol.id\
						INNER JOIN (select * from indent) ind ON ind.prod_id=pol.product_id\
							and ind.pr_id=po.requisition_id\
						LEFT JOIN stock_location sl ON sl.id=ind.site_id\
					WHERE\
					po.date_order between date_start and date_end\
					and po.state in ('approved','done')\
					and sl.id=any(location_dest_id);\
			END;\
			$$ LANGUAGE plpgsql;  \
			")