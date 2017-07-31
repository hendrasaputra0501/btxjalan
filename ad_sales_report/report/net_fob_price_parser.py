import re
import time
from datetime import datetime
import xlwt
from report import report_sxw
from report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
 
class net_fob_price_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(net_fob_price_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result_net_fob_price':self._get_result_net_fob_price,
			'get_result_target_fob':self._get_result_target_fob,
		})

	def _get_result_target_fob(self, data):
		res = []
		as_on = data['form']['as_on_date'].encode("utf-8")
		goods_type = data['form']['goods_type'].encode("utf-8")
		sale_type = data['form']['sale_type'].encode("utf-8")
		exception_agent_conditions = ""
		if data['form']['exception_agent_ids']:
			exception_agent_conditions = "WHERE ak.agent_id NOT IN ("+','.join([str(x) for x in data['form']['exception_agent_ids']])+") "
		
		query = "\
			SELECT DISTINCT\
				i.property_stock_prod_id as prodloc_id,\
				j.name as loc_name,\
				j.sequence as loc_sequence,\
				q.name as dept_loc_name,\
				q.sequence as dept_loc_seq,\
				h.currency_id as currency_id,\
				a.id as product_id,\
				p.name as blend,\
				a.count as count,\
				a.sd_type as sd_type,\
				a.wax as wax,\
				d.name as product_desc,\
				sol.sequence_line as number,\
				to_char(b.date_order,'DD/MM/YYYY') as date,\
				b.date_order as date2,\
				to_char(sol.est_delivery_date,'Mon-YYYY') as period,\
				c.name as customer,\
				(sol.product_uom_qty-coalesce(dum_smm.shipped_qty,0.0)) as qty,\
				coalesce(dum_smm.shipped_qty,0.0) as qty_shipped,\
				sol.product_uom as uom,\
				coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1)) as net_rate,\
				sol.price_unit as sale_rate,\
				(case e.type\
					when 'usance' then e.name\
					else 'Sight' end) as payment_term,\
				coalesce(g.name,'') as port,\
				coalesce(c.city,'') as city,\
				coalesce(c.street3,'') as street3,\
				coalesce(f.name,'') as country,\
				coalesce(f.zone,'') as mktzone,\
				(case b.sale_type when 'local' then coalesce(c.state_id,0) else 0 end) as state_dest_id,\
				coalesce(sol.efisiensi_rate,0.0) as rate,\
				coalesce(b.freight_rate_value,0.0) as freight_rate,\
				k.comm as comm,\
				(case b.sale_type\
					when 'export' then\
						(case e.type\
							when 'sight' then 0.0\
							when 'usance' then \
								(case \
									when coalesce(e.termdays,0.0)>30 then\
									(\
										((e.termdays-30)/360.0)\
										*(l.rate/100.0)\
										*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1)))\
									)\
								else 0.0 end)\
							else 0.0 end)\
					when 'local' then\
						(case\
							when e.termdays>14 then\
								(\
									(coalesce(e.termdays,0.0)/360.0)\
									* (l.rate/100.0)\
									*(coalesce(sol.price_unit,0.0)-(coalesce(sol.tax_amount,0.0)/coalesce(sol.product_uom_qty,1.0)))\
								)\
							else 0.0 end)\
					else 0.0 end) as term_rate,\
				(\
					(case b.sale_type when \
						'export' then coalesce(m.rate,0.0) when \
						'local' then coalesce(m.rate_domestik,0.0) else 0.0 \
					end)/100)\
					*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1))\
				) as insurance_rate,\
				(coalesce(k.comm,0.0)/100)*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1))-coalesce(b.freight_rate_value,0.0)) as comm_rate,\
				(case b.sale_type\
					when 'export' then\
						n.type\
					else 0 end) as container_type,\
				(case b.sale_type\
					when 'export' then\
						o.est_weight_per_container\
					else 0 end) as est_weight_per_container,\
				(case b.sale_type\
					when 'export' then\
						o.uom_id\
					else 0 end) as uom_est_weight,\
				m.incoterm_name as incoterm_name\
			FROM \
				sale_order_line sol\
				LEFT JOIN ( \
					SELECT \
						smm.sale_line_id,smm.product_id, \
						case when spm.type='out' then \
							sum(round((coalesce(smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
						else \
							sum(round((coalesce(-1*smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
						end as shipped_qty \
					FROM stock_move smm \
						LEFT JOIN sale_order_line solm ON smm.sale_line_id=solm.id \
						INNER JOIN stock_picking spm ON smm.picking_id=spm.id \
						INNER JOIN stock_location slm1 ON smm.location_id=slm1.id \
						INNER JOIN stock_location slm2 ON smm.location_dest_id=slm2.id \
						INNER JOIN product_uom pum1 ON solm.product_uom=pum1.id \
						INNER JOIN product_uom pum2 ON smm.product_uom=pum2.id \
					WHERE \
						smm.date::date<='"+as_on+"' \
						AND smm.state='done' \
						AND ((slm1.usage='internal' and slm2.usage='customer') or (slm1.usage='customer' and slm2.usage='internal')) \
					GROUP BY smm.sale_line_id,smm.product_id,spm.type \
					) dum_smm on sol.id=dum_smm.sale_line_id and sol.product_id=dum_smm.product_id \
				INNER JOIN product_product a on a.id=sol.product_id\
				INNER JOIN sale_order b on b.id=sol.order_id\
				LEFT JOIN res_partner c on c.id=b.partner_shipping_id\
				LEFT JOIN product_template d on d.id=a.product_tmpl_id\
				LEFT JOIN \
					(SELECT e1.id,e1.name,e1.type, sum(e2.days) as termdays\
					FROM account_payment_term e1\
					LEFT JOIN account_payment_term_line e2 ON e2.payment_id=e1.id\
					GROUP BY e1.id,e1.name,e1.type\
					) e on e.id=b.payment_term\
				LEFT JOIN res_country f on f.id=b.dest_country_id\
				LEFT JOIN res_port g on g.id=b.dest_port_id\
				LEFT JOIN product_pricelist h on h.id=b.pricelist_id\
				LEFT JOIN \
					(SELECT \
						cast(substring(ia.value_reference from 16 for (char_length(ia.value_reference)-15)) as integer) as property_stock_prod_id,\
						cast(substring(ia.res_id from 18 for (char_length(ia.res_id)-16)) as integer) as prod_tmpl_id \
					FROM ir_property ia \
					WHERE ia.name='property_stock_production') i on i.prod_tmpl_id=a.product_tmpl_id\
				LEFT JOIN stock_location j on j.id=i.property_stock_prod_id\
				LEFT JOIN \
					(SELECT ak.sale_line_id as sale_line_id,coalesce(avg(ak.commission_percentage),0) as comm \
					FROM sale_order_agent ak "+exception_agent_conditions+" \
					GROUP BY ak.sale_line_id) k on k.sale_line_id=sol.id\
				CROSS JOIN\
					(SELECT\
						coalesce(l1.rate,0) as rate\
					FROM \
						account_interest_rate l1\
						LEFT JOIN account_interest l2 ON l2.id=l1.interest_id\
					WHERE l2.type='global_rate' and l1.date_from<='"+as_on+" and l2.sale_type='"+sale_type+"'\
					ORDER BY l1.date_from DESC\
					LIMIT 1\
					) l\
				LEFT JOIN\
					(SELECT DISTINCT\
						(case m2.sale_type when 'export' then coalesce(m1.rate,0.0) else 0.0 end) as rate, coalesce(m4.rate,0.0) as rate_domestik, m2.sale_type,\
						coalesce(m3.id,0) as incoterm, coalesce(m3.code,' ') as incoterm_name, m1.name as date\
					FROM\
						insurance_rate m1\
						LEFT JOIN insurance_type m2 ON m2.id=m1.insurance_id\
						LEFT JOIN stock_incoterms m3 ON m3.id=m2.incoterms\
						CROSS JOIN \
							(SELECT DISTINCT \
								m41.rate\
							FROM insurance_rate m41 \
								LEFT JOIN insurance_type m42 ON m42.id=m41.insurance_id \
							WHERE m42.type='sale' and m42.sale_type='local') m4\
					WHERE m2.type='sale' and m2.sale_type='"+sale_type+"'\
					) m ON m.sale_type=b.sale_type and m.incoterm=coalesce(b.incoterm,0) and m.date<=b.date_order\
				LEFT JOIN container_size n ON n.id=sol.container_size\
				LEFT JOIN container_type o ON o.id=n.type\
				LEFT JOIN mrp_blend_code p ON p.id=a.blend_code\
				LEFT JOIN stock_location q ON q.id=sol.production_location\
			WHERE\
				b.state not in ('draft','cancel') \
				AND coalesce(sol.est_delivery_date,b.max_est_delivery_date,b.date_order)<='"+as_on+"' \
				AND ((b.date_done is null) or (b.date_done > '"+as_on+"')) \
				AND ((b.date_cancel is null) or (b.date_cancel > '"+as_on+"')) \
				AND ((sol.date_knock_off is null or sol.knock_off=false) or (sol.date_knock_off > '"+as_on+"')) \
				AND b.goods_type='"+goods_type+"' \
				AND b.sale_type='"+sale_type+"'\
			ORDER BY j.sequence,p.name,a.count,a.sd_type,sol.sequence_line ASC"


		self.cr.execute(query)

		res = self.cr.dictfetchall()
		res = self._get_freight_local(data, res)
		return res

	def _get_result_net_fob_price(self, data):
		res = []
		date_start = data['form']['start_date'].encode("utf-8")
		date_end = data['form']['end_date'].encode("utf-8")
		goods_type = data['form']['goods_type'].encode("utf-8")
		sale_type = data['form']['sale_type'].encode("utf-8")
		query = "\
			SELECT DISTINCT\
				i.property_stock_prod_id as prodloc_id,\
				j.name as loc_name,\
				j.sequence as loc_sequence,\
				h.currency_id as currency_id,\
				a.id as product_id,\
				p.name as blend,\
				a.count as count,\
				a.sd_type as sd_type,\
				a.wax as wax,\
				d.name as product_desc,\
				sol.sequence_line as number,\
				to_char(b.date_order,'DD/MM/YYYY') as date,\
				b.date_order as date2,\
				to_char(sol.est_delivery_date,'Mon-YYYY') as period,\
				c.name as customer,\
				sol.product_uom_qty as qty,\
				sol.product_uom as uom,\
				coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1)) as net_rate,\
				sol.price_unit as sale_rate,\
				(case e.type\
					when 'usance' then e.name\
					else 'Sight' end) as payment_term,\
				coalesce(g.name,'') as port,\
				coalesce(c.city,'') as city,\
				coalesce(c.street3,'') as street3,\
				coalesce(f.name,'') as country,\
				coalesce(f.zone,'') as mktzone,\
				(case b.sale_type when 'local' then coalesce(c.state_id,0) else 0 end) as state_dest_id,\
				coalesce(sol.efisiensi_rate,0.0) as rate,\
				coalesce(b.freight_rate_value,0.0) as freight_rate,\
				k.comm as comm,\
				(case b.sale_type\
					when 'export' then\
						(case e.type\
							when 'sight' then 0.0\
							when 'usance' then \
								(case \
									when coalesce(e.termdays,0.0)>30 then\
									(\
										((e.termdays-30)/360.0)\
										*(l.rate/100.0)\
										*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1)))\
									)\
								else 0.0 end)\
							else 0.0 end)\
					when 'local' then\
						(case\
							when e.termdays>14 then\
								(\
									(coalesce(e.termdays,0.0)/360.0)\
									* (l.rate/100.0)\
									*(coalesce(sol.price_unit,0.0)-(coalesce(sol.tax_amount,0.0)/coalesce(sol.product_uom_qty,1.0)))\
								)\
							else 0.0 end)\
					else 0.0 end) as term_rate,\
				(\
					(case b.sale_type when \
						'export' then coalesce(m.rate,0.0) when \
						'local' then coalesce(m.rate_domestik,0.0) else 0.0 \
					end)/100)\
					*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1))\
				) as insurance_rate,\
				(coalesce(k.comm,0.0)/100)*(coalesce(sol.price_unit,0)-(coalesce(sol.tax_amount,0)/coalesce(sol.product_uom_qty,1))-coalesce(b.freight_rate_value,0.0)) as comm_rate,\
				(case b.sale_type\
					when 'export' then\
						n.type\
					else 0 end) as container_type,\
				(case b.sale_type\
					when 'export' then\
						o.est_weight_per_container\
					else 0 end) as est_weight_per_container,\
				(case b.sale_type\
					when 'export' then\
						o.uom_id\
					else 0 end) as uom_est_weight,\
				m.incoterm_name as incoterm_name\
			FROM \
				sale_order_line sol\
				INNER JOIN product_product a on a.id=sol.product_id\
				INNER JOIN sale_order b on b.id=sol.order_id\
				LEFT JOIN res_partner c on c.id=b.partner_shipping_id\
				INNER JOIN product_template d on d.id=a.product_tmpl_id\
				LEFT JOIN \
					(SELECT e1.id,e1.name,e1.type, sum(e2.days) as termdays\
					FROM account_payment_term e1\
					LEFT JOIN account_payment_term_line e2 ON e2.payment_id=e1.id\
					GROUP BY e1.id,e1.name,e1.type\
					) e on e.id=b.payment_term\
				LEFT JOIN res_country f on f.id=b.dest_country_id\
				LEFT JOIN res_port g on g.id=b.dest_port_id\
				LEFT JOIN product_pricelist h on h.id=b.pricelist_id\
				LEFT JOIN \
					(SELECT \
						cast(substring(ia.value_reference from 16 for (char_length(ia.value_reference)-15)) as integer) as property_stock_prod_id,\
						cast(substring(ia.res_id from 18 for (char_length(ia.res_id)-16)) as integer) as prod_tmpl_id \
					FROM ir_property ia \
					WHERE ia.name='property_stock_production') i on i.prod_tmpl_id=a.product_tmpl_id\
				LEFT JOIN stock_location j on j.id=i.property_stock_prod_id\
				LEFT JOIN \
					(SELECT ak.sale_line_id as sale_line_id,coalesce(avg(ak.commission_percentage),0) as comm \
					FROM sale_order_agent ak \
					GROUP BY ak.sale_line_id) k on k.sale_line_id=sol.id \
				CROSS JOIN\
					(SELECT\
						coalesce(l1.rate,0) as rate\
					FROM \
						account_interest_rate l1\
						LEFT JOIN account_interest l2 ON l2.id=l1.interest_id\
					WHERE l2.type='global_rate' and l1.date_from<='"+date_end+"' and l2.sale_type='"+sale_type+"' \
					ORDER BY l1.date_from DESC\
					LIMIT 1\
					) l\
				LEFT JOIN\
					(SELECT DISTINCT\
						(case m2.sale_type when 'export' then coalesce(m1.rate,0.0) else 0.0 end) as rate, coalesce(m4.rate,0.0) as rate_domestik, m2.sale_type,\
						coalesce(m3.id,0) as incoterm, coalesce(m3.code,' ') as incoterm_name, m1.name as date\
					FROM\
						insurance_rate m1\
						LEFT JOIN insurance_type m2 ON m2.id=m1.insurance_id\
						LEFT JOIN stock_incoterms m3 ON m3.id=m2.incoterms\
						CROSS JOIN \
							(SELECT DISTINCT \
								m41.rate\
							FROM insurance_rate m41 \
								LEFT JOIN insurance_type m42 ON m42.id=m41.insurance_id \
							WHERE m42.type='sale' and m42.sale_type='local') m4\
					WHERE m2.type='sale' and m2.sale_type='"+sale_type+"'\
					) m ON m.sale_type=b.sale_type and m.incoterm=coalesce(b.incoterm,0) and m.date<=b.date_order\
				LEFT JOIN container_size n ON n.id=sol.container_size\
				LEFT JOIN container_type o ON o.id=n.type\
				LEFT JOIN mrp_blend_code p ON p.id=a.blend_code\
			WHERE\
				b.date_order>='"+date_start+"' AND b.date_order<='"+date_end+"' \
				and b.goods_type='"+goods_type+"' \
				AND b.sale_type='"+sale_type+"'\
				AND b.state not in ('draft')\
			ORDER BY j.sequence,p.name,a.count,a.sd_type,sol.sequence_line ASC"
		self.cr.execute(query)

		res = self.cr.dictfetchall()
		res = self._get_freight_local(data, res)
		return res

	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(self.cr, self.uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_freight_local(self, data, lines):
		cr = self.cr
		uid = self.uid
		transport_pool = self.pool.get('stock.transporter')
		trans_chg_pool = self.pool.get('stock.transporter.charge')
		date_end = data['form']['end_date'].decode("utf-8").encode("utf-8")
		sale_type = data['form']['sale_type'].decode("utf-8").encode("utf-8")
		trans_ids = transport_pool.search(cr, uid, [('type','=','trucking'),('charge_type','=','sale'),('sale_type','=',sale_type)])
		uom_kgs_id = self._get_uom_kgs()
		for line in lines:
			state_dest_id = line['state_dest_id']
			container_type = line['container_type']
			est_weight_per_container = line['est_weight_per_container']
			uom_est_weight = line['uom_est_weight']
			line.update({'freight_local_rate':0.0})
			if sale_type == 'export' and container_type and est_weight_per_container and uom_est_weight:
				est_weight_per_container = self._uom_to_base(data, est_weight_per_container, uom_est_weight, uom_to_id=(uom_kgs_id and uom_kgs_id or None))
				chg_ids = []
				for trans_id in (trans_ids or []):
					temp_chg_ids = trans_chg_pool.search(cr, uid, [('transporter_id','=',trans_id),('cost_type','=','type2'),('size_container','=',container_type),('is_lift_on_lift_off','!=',True),('date_from','<=',date_end)])
					if temp_chg_ids:
						chg_ids.append(temp_chg_ids[0])
				if chg_ids:
					total_freight = 0.0
					for chg in trans_chg_pool.browse(cr, uid, chg_ids):
						if chg.currency_id and chg.cost:
							total_freight += (self._get_amount_company_currency(chg.currency_id.id,(chg.cost),line['date2']))
					line['freight_local_rate'] = total_freight/len(chg_ids)/est_weight_per_container
				chg_ids2 = []
				for trans_id in (trans_ids or []):
					temp_chg_ids2 = trans_chg_pool.search(cr, uid, [('transporter_id','=',trans_id),('cost_type','=','type2'),('is_lift_on_lift_off','=',True),('size_container','=',container_type),('date_from','<=',date_end)])
					if temp_chg_ids2:
						chg_ids2.append(temp_chg_ids2[0])
				if chg_ids2:
					total_lolo = 0.0
					for chg2 in trans_chg_pool.browse(cr, uid, chg_ids2):
						if chg2.currency_id and chg2.cost:
							total_lolo += (self._get_amount_company_currency(chg2.currency_id.id,(chg2.cost),line['date2']))
					line['freight_local_rate'] += total_lolo/len(chg_ids2)/est_weight_per_container
			elif sale_type == 'local':
				# if state_dest_id != 0:
					# chg_ids = trans_chg_pool.search(cr, uid, [('transporter_id','in',trans_ids),('cost_type','=','type1'),('state_id','=',state_dest_id),('date_from','<=',date_end)])
				
				chg_ids = trans_chg_pool.search(cr, uid, [('transporter_id','in',trans_ids),('cost_type','=','type1'),('date_from','<=',date_end)],order="cost desc")
				if chg_ids:
					total_freight = 0.0
					for chg in trans_chg_pool.browse(cr, uid, chg_ids):
						frate = self._price_per_base(data, chg.cost, chg.uom_id.id)
						frate = self._get_amount_company_currency(chg.currency_id.id, frate, line['date2'])
						if total_freight < frate:
							total_freight = frate
					line['freight_local_rate'] = total_freight
		return lines

	def _get_uom_kgs(self):
		cr = self.cr
		uid = self.uid
		uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		return base and base[0] or False

	def _uom_to_base(self,data,qty,uom_source,uom_to_id=None):
		cr = self.cr
		uid = self.uid
		if data['form']['sale_type'] == 'export':
			uom_base = 'BALES'
		elif data['form']['sale_type'] == 'local':
			uom_base = 'BALES'
		else:
			uom_base = 'BALES'
		base = uom_to_id is not None and [uom_to_id] or self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		if base and base[0]==uom_source:
			return qty
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result


	def _price_per_base(self,data,price,uom_source,uom_to_id=None):
		cr = self.cr
		uid = self.uid
		if data['form']['sale_type'] == 'export':
		  uom_base = 'KGS'
		elif data['form']['sale_type'] == 'local':
		  uom_base = 'BALES'
		else:
		  uom_base = 'KGS'
		base = uom_to_id is not None and [uom_to_id] or self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		if base and base[0]==uom_source:
			return price
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=base and base[0] or False)
		if qty_result>0:
		  price_result = price*1000.0/qty_result 
		else:
		  price_result = price 
		return price_result

	def _get_mktzone(self):
		cr = self.cr
		uid = self.uid
		cr.execute("SELECT zone FROM res_country GROUP BY zone")
		return cr.dictfetchall()

class net_fob_price_xls(report_xls):
	def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
		if not context:
			context = {}
		context = context.copy()
		rml_parser = self.parser(cr, uid, self.name2, context=context)
		objs = []
		rml_parser.set_context(objs, data, ids, 'xls')
		n = cStringIO.StringIO()
		wb = xlwt.Workbook(encoding='utf-8')
		if data['form']['type'] == 'booked_order':
			self.generate_xls_report_1(rml_parser, data, rml_parser.localcontext['objects'], wb)
		else:
			self.generate_xls_report_2(rml_parser, data, rml_parser.localcontext['objects'], wb)
		wb.save(n)
		n.seek(0)
		return (n.read(), 'xls')

	def generate_xls_report_1(self, parser, data, obj, wb):
		ws = wb.add_sheet(('Net Fob Price'))
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 
		ws.preview_magn = 65
		ws.normal_magn = 65
		ws.print_scaling=65
		sale_type = data['form']['sale_type'].decode("utf-8").encode("utf-8")
		date_start = datetime.strptime(data['form']['start_date'],"%Y-%m-%d").strftime("%d/%m/%Y")
		date_end = datetime.strptime(data['form']['end_date'],"%Y-%m-%d").strftime("%d/%m/%Y")
		mktzone = sorted([x['zone'] for x in parser._get_mktzone() if x['zone']])

		title_style = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
		title_style1 = xlwt.easyxf('font: height 210, name Calibri, colour_index black; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		hdr_style_border_top = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin;')
		hdr_style_border_top_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin, bottom thin;')
		hdr_style_border_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: bottom thin;')
		normal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap off, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
		normal_right_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0;(#,##0)')
		normal_right_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
		normal_right_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')
		subtotal_label_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; borders: bottom dotted;')
		subtotal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.00;(#,##0.00)')
		subtotal_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0;(#,##0)')
		subtotal_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.0000;(#,##0.0000)')
		
		ws.write_merge(0,0,0,(sale_type == 'local' and 17 or 18+len(mktzone)),"PT. Bitratex Industries", title_style )
		ws.write_merge(1,1,0,(sale_type == 'local' and 17 or 18+len(mktzone)),"NET FOB PRICE OF "+data['form']['sale_type'].upper()+" ORDER - Booked During the Period", title_style )
		ws.write_merge(2,2,0,(sale_type == 'local' and 17 or 18+len(mktzone)),"From: "+date_start+" To "+date_end, title_style )
		ws.write_merge(3,3,0,(sale_type == 'local' and 17 or 18+len(mktzone)),"", title_style )
		
		ws.write_merge(4,5,0,0,"Product",hdr_style_border_top_bottom)
		ws.write_merge(4,4,1,2,"Sales Contract",hdr_style_border_top_bottom)
		ws.write(5,1,"No",hdr_style_border_bottom)
		ws.write(5,2,"Date",hdr_style_border_bottom)
		ws.write_merge(4,5,3,3,"Customer",hdr_style_border_top_bottom)
		ws.write_merge(4,5,4,4,"Qty in\n"+(sale_type=='local' and 'BALE' or 'BALE'),hdr_style_border_top_bottom)
		
		ws.write_merge(4,5,5,5,"Net Price\nUS$/"+(sale_type=='local' and 'BALE' or 'KG'),hdr_style_border_top_bottom)
		ws.write_merge(4,5,6,6,(sale_type=='local' and 'Sale Price\nUS$/BALE' or ''),hdr_style_border_top_bottom)
		ws.write_merge(4,5,7,7,"Value\nUS$",hdr_style_border_top_bottom)
		ws.write_merge(4,5,8,8,"Payment",hdr_style_border_top_bottom)
		
		ws.write_merge(4,5,9,9,"Destination",hdr_style_border_top_bottom)
		ws.write_merge(4,5,10,10,"Delivery\nPeriod",hdr_style_border_top_bottom)
		ws.write_merge(4,5,11,11,"Comm",hdr_style_border_top_bottom)
		ws.write_merge(4,5,12,12,"BKD",hdr_style_border_top_bottom)
		
		if sale_type == 'local':
			ws.write_merge(4,5,13,13,"Freight\nCost/BALE",hdr_style_border_top_bottom)
			ws.write_merge(4,5,14,14,"Usance\nCost/BALE",hdr_style_border_top_bottom)
			ws.write_merge(4,5,15,15,"Insurance\nCost/BALE",hdr_style_border_top_bottom)
			ws.write_merge(4,5,16,16,"F O B\nPrice/BALE",hdr_style_border_top_bottom)
			ws.write_merge(4,5,17,17,"EFN\nRate",hdr_style_border_top_bottom)
		else:
			ws.write_merge(4,5,13,13,"Freight\nCost/KG",hdr_style_border_top_bottom)
			ws.write_merge(4,5,14,14,"EMKL+LOLO\nCost/KG",hdr_style_border_top_bottom)
			ws.write_merge(4,5,15,15,"Usance\nCost/KG",hdr_style_border_top_bottom)
			ws.write_merge(4,5,16,16,"Insurance\nCost/KG",hdr_style_border_top_bottom)
			# tanpa marketzone
			ws.write_merge(4,5,17,17,"F O B\nPrice/KG",hdr_style_border_top_bottom)
			# marketzone
			ws.write_merge(4,4,18,18+len(mktzone)-1,"Market Zone",hdr_style_border_top_bottom)
			clm=18
			for zone in mktzone:
				ws.write(5,clm,zone,hdr_style_border_bottom)
				clm+=1
			ws.write_merge(4,5,19+len(mktzone)-1,19+len(mktzone)-1,"EFN\nRate",hdr_style_border_top_bottom)
		
		if data['form']['type'] == 'booked_order':
			result = parser._get_result_net_fob_price(data)
		else:
			result = parser._get_result_target_fob(data)
		# group disini
		result_grouped={}
		for res in result:
			key1=(res['prodloc_id'],res['loc_sequence'])
			if key1 not in result_grouped:
				result_grouped.update({key1:{}})
			key2=res['blend']
			if key2 not in result_grouped[key1]:
				result_grouped[key1].update({key2:{}})
			key3=res['count']
			if key3 not in result_grouped[key1][key2]:
				result_grouped[key1][key2].update({key3:{}})
			key4=res['sd_type']
			if key4 not in result_grouped[key1][key2][key3]:
				result_grouped[key1][key2][key3].update({key4:[]})
			
			result_grouped[key1][key2][key3][key4].append(res)

		uom_kgs_id = parser._get_uom_kgs()
		max_width_col_0 = 0
		max_width_col_1 = 0
		max_width_col_3 = 0
		max_width_col_8 = 0
		max_width_col_9 = 0
		rowcount = 6
		currency_usd = parser._get_company_currency()

		subtotal_wax = {1:0.0,2:0.0,3:0.0,4:0.0,5:0.0,6:0}
		subtotal_loc = subtotal_wax.copy()
		grand_total = subtotal_wax.copy()
		for parent_loc,loc_sequence in sorted(result_grouped.keys(),key=lambda k:k[1]):
			curr_loc = False
			for blend in sorted(result_grouped[parent_loc,loc_sequence].keys()):
				for count in sorted(result_grouped[parent_loc,loc_sequence][blend].keys()):
					for sd in sorted(result_grouped[parent_loc,loc_sequence][blend][count].keys()):
						for line in result_grouped[parent_loc,loc_sequence][blend][count][sd]:
							ws.write(rowcount,0,line['product_desc'], normal_style)
							if len(line['product_desc'] and line['product_desc'] or '')>max_width_col_0:
								max_width_col_0 = len(line['product_desc'])
							ws.write(rowcount,1,line['number'], normal_style)
							if len(line['number'] and line['number'] or '')>max_width_col_1:
								max_width_col_1 = len(line['number'])
							ws.write(rowcount,2,line['date'], normal_style)
							ws.write(rowcount,3,line['customer'], normal_style)
							if len(line['customer'] and line['customer'] or '')>max_width_col_3:
								max_width_col_3 = len(line['customer'])
							
							qty = line['qty']
							qty = parser._uom_to_base(data, qty, line['uom'])
							qty_kgs = parser._uom_to_base(data, line['qty'], line['uom'], uom_to_id=(uom_kgs_id and uom_kgs_id or None))
							ws.write(rowcount,4,qty, normal_right_style2)

							sale_rate = parser._price_per_base(data, line['sale_rate'], line['uom'])
							net_rate = parser._price_per_base(data, line['net_rate'], line['uom'])
							insurance_rate = parser._price_per_base(data, line['insurance_rate'], line['uom'])
							term_rate = parser._price_per_base(data, line['term_rate'], line['uom'])
							comm_rate = parser._price_per_base(data, line['comm_rate'], line['uom'])
							freight_rate = line['freight_rate']
							if line['currency_id']!=currency_usd.id:
								sale_rate = parser._get_amount_company_currency(line['currency_id'],sale_rate,line['date2'])
								net_rate = parser._get_amount_company_currency(line['currency_id'],net_rate,line['date2'])
								insurance_rate = parser._get_amount_company_currency(line['currency_id'],insurance_rate,line['date2'])
								term_rate = parser._get_amount_company_currency(line['currency_id'],term_rate,line['date2'])
								comm_rate = parser._get_amount_company_currency(line['currency_id'],comm_rate,line['date2'])
								freight_rate = parser._get_amount_company_currency(line['currency_id'],freight_rate,line['date2'])
							freight_local_rate = line['freight_local_rate']

							ws.write(rowcount,5,net_rate, sale_type=='local' and normal_right_style or normal_right_style1)
							ws.write(rowcount,6,sale_type=='local' and sale_rate or line['incoterm_name'], sale_type=='local' and normal_right_style or normal_style)
							ws.write(rowcount,7,(net_rate*(sale_type=='local' and qty or qty_kgs)), normal_right_style1)
							if len(line['payment_term'] and line['payment_term'] or '')>max_width_col_8:
								max_width_col_8 = len(line['payment_term'])
							ws.write(rowcount,8,line['payment_term'], normal_style)
							ws.write(rowcount,9,(sale_type=='local' and (line['city'] and line['city'] or line['street3'] or ' ') or "%s, %s"%(line['port'],line['country'])).upper(), normal_style)
							ws.write(rowcount,10, line['period'], normal_style)
							ws.write(rowcount,11,line['comm'], normal_right_style1)
							if len("%s,%s"%(line['port'],line['country']))>max_width_col_9:
								max_width_col_9 = len("%s,%s"%(line['port'],line['country']))
							if sale_type == 'local':
								ws.write(rowcount,13,freight_local_rate, normal_right_style1)
								ws.write(rowcount,14,term_rate, normal_right_style1)
								ws.write(rowcount,15,insurance_rate, normal_right_style1)
								fob_rate = net_rate - freight_local_rate - term_rate - insurance_rate - comm_rate
								ws.write(rowcount,16,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
								ws.write(rowcount,17,line['rate'], normal_right_style)
							else:
								ws.write(rowcount,13,freight_rate, normal_right_style1)
								ws.write(rowcount,14,freight_local_rate, normal_right_style1)
								ws.write(rowcount,15,term_rate, normal_right_style1)
								ws.write(rowcount,16,insurance_rate, normal_right_style1)
								fob_rate = net_rate - freight_rate - freight_local_rate - term_rate - insurance_rate - comm_rate
								ws.write(rowcount,17,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
								clm = 18
								for zone in mktzone:
									if zone==line['mktzone']:
										ws.write(rowcount,clm,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
									else:
										clm+=1

								ws.write(rowcount,19+len(mktzone)-1,line['rate'], normal_right_style)
							rowcount+=1
							subtotal_wax.update({
								1:subtotal_wax[1]+qty,
								2:subtotal_wax[2]+net_rate,
								3:subtotal_wax[3]+(net_rate*(sale_type=='local' and qty or qty_kgs)),
								4:subtotal_wax[4]+(fob_rate*qty),
								5:subtotal_wax[5]+(line['rate']*qty),
								6:subtotal_wax[6]+1,
							})
							curr_loc = line['loc_name']
						ws.write_merge(rowcount,rowcount,0,3, "Subtotal", subtotal_label_style)
						if sale_type == 'local':
							ws.write(rowcount,4, subtotal_wax[1], subtotal_style2)
							ws.write(rowcount,5, subtotal_wax[6] and subtotal_wax[2]/subtotal_wax[6] or 0.0, subtotal_style1)
							ws.write(rowcount,6, "", subtotal_label_style)
							ws.write(rowcount,7, subtotal_wax[3], subtotal_style)
							ws.write_merge(rowcount,rowcount,8,15, "", subtotal_label_style)
							ws.write(rowcount,16, subtotal_wax[1] and subtotal_wax[4]/subtotal_wax[1] or 0.0, subtotal_style1)
							ws.write(rowcount,17, subtotal_wax[5]/subtotal_wax[1], subtotal_style1)
						else:
							ws.write(rowcount,4, subtotal_wax[1], subtotal_style2)
							ws.write(rowcount,5, subtotal_wax[6] and subtotal_wax[2]/subtotal_wax[6] or 0.0, subtotal_style)
							ws.write(rowcount,6, "", subtotal_label_style)
							ws.write(rowcount,7, subtotal_wax[3], subtotal_style)
							ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
							ws.write(rowcount,17, subtotal_wax[1] and subtotal_wax[4]/subtotal_wax[1] or 0.0, subtotal_style)
							ws.write_merge(rowcount,rowcount,18,17+len(mktzone), "", subtotal_label_style)
							ws.write(rowcount,18+len(mktzone), subtotal_wax[5]/subtotal_wax[1], subtotal_style1)
						rowcount+=1

						subtotal_loc.update({
							1:subtotal_loc[1]+subtotal_wax[1],
							3:subtotal_loc[3]+subtotal_wax[3],
							5:subtotal_loc[5]+subtotal_wax[5],
							6:subtotal_loc[6]+1
						})
						for i in range(1,7):
							subtotal_wax[i]=0

			ws.write_merge(rowcount,rowcount,0,3, "Total "+(curr_loc and curr_loc or '') , subtotal_label_style)
			if sale_type == 'local':
				ws.write(rowcount,4, subtotal_loc[1], subtotal_style2)
				ws.write(rowcount,5, "", subtotal_style)
				ws.write(rowcount,6, "", subtotal_label_style)
				ws.write(rowcount,7, subtotal_loc[3], subtotal_style)
				ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
				ws.write(rowcount,17, subtotal_loc[5]/subtotal_loc[1], subtotal_style1)
			else:
				ws.write(rowcount,4, subtotal_loc[1], subtotal_style2)
				ws.write(rowcount,5, "", subtotal_style)
				ws.write(rowcount,6, "", subtotal_label_style)
				ws.write(rowcount,7, subtotal_loc[3], subtotal_style)
				ws.write_merge(rowcount,rowcount,8,17+len(mktzone), "", subtotal_label_style)
				ws.write(rowcount,18+len(mktzone), subtotal_loc[5]/subtotal_loc[1], subtotal_style1)
			rowcount+=1
			grand_total.update({
				1:grand_total[1]+subtotal_loc[1],
				3:grand_total[3]+subtotal_loc[3],
				5:grand_total[5]+subtotal_loc[5],
				6:grand_total[6]+1
			})
			for i in range(1,7):
				subtotal_loc[i]=0

		ws.write_merge(rowcount,rowcount,0,3, "Grand Total" , subtotal_label_style)
		if sale_type == 'local':
			ws.write(rowcount,4, grand_total[1], subtotal_style2)
			ws.write(rowcount,5, "", subtotal_style)
			ws.write(rowcount,6, "", subtotal_label_style)
			ws.write(rowcount,7, grand_total[3], subtotal_style)
			ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
			ws.write(rowcount,17, grand_total[5]/grand_total[1], subtotal_style1)
		else:
			ws.write(rowcount,4, grand_total[1], subtotal_style2)
			ws.write(rowcount,5, "", subtotal_style)
			ws.write(rowcount,6, "", subtotal_label_style)
			ws.write(rowcount,7, grand_total[3], subtotal_style)
			ws.write_merge(rowcount,rowcount,8,17+len(mktzone), "", subtotal_label_style)
			ws.write(rowcount,18+len(mktzone), grand_total[5]/grand_total[1], subtotal_style1)

		ws.col(0).width = 256 * int((max_width_col_0<20 and max_width_col_0 or 20)*1.4)
		ws.col(1).width = 256 * int(max_width_col_1*1.4)
		ws.col(3).width = 256 * int((max_width_col_3<20 and max_width_col_3 or 20)*1.4)
		ws.col(8).width = 256 * int(max_width_col_8*1.4)
		ws.col(9).width = 256 * int((max_width_col_9<20 and max_width_col_9 or 20)*1.4)

		ws.col(4).width = 256 * int(len(str(grand_total[1]))*1.4)
		ws.col(7).width = 256 * int(len(str(grand_total[3]))*1.4)
		ws.col(12).width = 0
		if sale_type=='local':
			# ws.col(14).width = 0
			ws.col(15).width = 0
		elif sale_type=='export':
			ws.col(6).width = 256 * int(5*1.4)
			ws.col(14).width = 0
			ws.col(15).width = 0
			ws.col(16).width = 0
		pass

	def generate_xls_report_2(self, parser, data, obj, wb):
		result_parser = parser._get_result_target_fob(data)
		uom_kgs_id = parser._get_uom_kgs()
		result_grouped_by_dept = {}
		for x in result_parser:
			key = (x['dept_loc_name'],x['dept_loc_seq'])
			if key not in result_grouped_by_dept:
				result_grouped_by_dept.update({key:[]})
			result_grouped_by_dept[key].append(x)
		for key_dept in sorted(result_grouped_by_dept.keys(), key=lambda x:x[1]): 
			ws = wb.add_sheet((key_dept[0]))
			ws.panes_frozen = True
			ws.remove_splits = True
			ws.portrait = 0 # Landscape
			ws.fit_width_to_pages = 1 
			ws.preview_magn = 65
			ws.normal_magn = 65
			ws.print_scaling=65
			sale_type = data['form']['sale_type'].decode("utf-8").encode("utf-8")
			date_start = datetime.strptime(data['form']['start_date'],"%Y-%m-%d").strftime("%d/%m/%Y")
			date_end = datetime.strptime(data['form']['end_date'],"%Y-%m-%d").strftime("%d/%m/%Y")
			as_on_date = datetime.strptime(data['form']['as_on_date'].encode("utf-8"),"%Y-%m-%d").strftime("%d/%m/%Y")
			mktzone = sorted([x['zone'] for x in parser._get_mktzone() if x['zone']])

			title_style = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
			title_style1 = xlwt.easyxf('font: height 210, name Calibri, colour_index black; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
			hdr_style_border_top = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin;')
			hdr_style_border_top_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: top thin, bottom thin;')
			hdr_style_border_bottom = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white; borders: bottom thin;')
			normal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap off, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
			normal_right_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0;(#,##0)')
			normal_right_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
			normal_right_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')
			subtotal_label_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; borders: bottom dotted;')
			subtotal_style = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.00;(#,##0.00)')
			subtotal_style1 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0;(#,##0)')
			subtotal_style2 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.0000;(#,##0.0000)')
			
			ws.write_merge(0,0,0,(sale_type == 'local' and 16 or 17+len(mktzone)),"PT. Bitratex Industries", title_style )
			ws.write_merge(1,1,0,(sale_type == 'local' and 16 or 17+len(mktzone)),"NET FOB PRICE OF "+data['form']['sale_type'].upper()+" ORDER - Target FOB", title_style )
			ws.write_merge(2,2,0,(sale_type == 'local' and 16 or 17+len(mktzone)),"As On: "+as_on_date, title_style )
			ws.write_merge(3,3,0,(sale_type == 'local' and 16 or 17+len(mktzone)),"", title_style )
			
			ws.write_merge(4,5,0,0,"Product",hdr_style_border_top_bottom)
			ws.write_merge(4,4,1,2,"Sales Contract",hdr_style_border_top_bottom)
			ws.write(5,1,"No",hdr_style_border_bottom)
			ws.write(5,2,"Date",hdr_style_border_bottom)
			ws.write_merge(4,5,3,3,"Customer",hdr_style_border_top_bottom)
			ws.write_merge(4,5,4,4,"Qty in\n"+(sale_type=='local' and 'BALE' or 'BALE'),hdr_style_border_top_bottom)
			
			ws.write_merge(4,5,5,5,"Net Price\nUS$/"+(sale_type=='local' and 'BALE' or 'KG'),hdr_style_border_top_bottom)
			ws.write_merge(4,5,6,6,(sale_type=='local' and 'Sale Price\nUS$/BALE' or ''),hdr_style_border_top_bottom)
			ws.write_merge(4,5,7,7,"Value\nUS$",hdr_style_border_top_bottom)
			ws.write_merge(4,5,8,8,"Payment",hdr_style_border_top_bottom)
			
			ws.write_merge(4,5,9,9,"Destination",hdr_style_border_top_bottom)
			ws.write_merge(4,5,10,10,"Delivery\nPeriod",hdr_style_border_top_bottom)
			ws.write_merge(4,5,11,11,"Comm",hdr_style_border_top_bottom)
			ws.write_merge(4,5,12,12,"BKD",hdr_style_border_top_bottom)
			
			if sale_type == 'local':
				ws.write_merge(4,5,13,13,"Freight\nCost/BALE",hdr_style_border_top_bottom)
				ws.write_merge(4,5,14,14,"Usance\nCost/BALE",hdr_style_border_top_bottom)
				ws.write_merge(4,5,15,15,"Insurance\nCost/BALE",hdr_style_border_top_bottom)
				ws.write_merge(4,5,16,16,"F O B\nPrice/BALE",hdr_style_border_top_bottom)
				# ws.write_merge(4,5,17,17,"EFN\nRate",hdr_style_border_top_bottom)
			else:
				ws.write_merge(4,5,13,13,"Freight\nCost/KG",hdr_style_border_top_bottom)
				ws.write_merge(4,5,14,14,"EMKL+LOLO\nCost/KG",hdr_style_border_top_bottom)
				ws.write_merge(4,5,15,15,"Usance\nCost/KG",hdr_style_border_top_bottom)
				ws.write_merge(4,5,16,16,"Insurance\nCost/KG",hdr_style_border_top_bottom)
				# tanpa marketzone
				ws.write_merge(4,5,17,17,"F O B\nPrice/KG",hdr_style_border_top_bottom)
				# marketzone
				ws.write_merge(4,4,18,18+len(mktzone)-1,"Market Zone",hdr_style_border_top_bottom)
				clm=18
				for zone in mktzone:
					ws.write(5,clm,zone,hdr_style_border_bottom)
					clm+=1
				# ws.write_merge(4,5,19+len(mktzone)-1,19+len(mktzone)-1,"EFN\nRate",hdr_style_border_top_bottom)
			result = result_grouped_by_dept[key_dept]
			# group disini
			result_grouped={}
			for res in result:
				qty = res['qty']
				qty = parser._uom_to_base(data, qty, res['uom'])
				qty_shipped = res['qty_shipped']
				if qty <= 5 and qty_shipped>0.0:
					continue
				key1=(res['prodloc_id'],res['loc_sequence'])
				if key1 not in result_grouped:
					result_grouped.update({key1:{}})
				key2=res['blend']
				if key2 not in result_grouped[key1]:
					result_grouped[key1].update({key2:{}})
				key3=res['count']
				if key3 not in result_grouped[key1][key2]:
					result_grouped[key1][key2].update({key3:{}})
				key4=res['sd_type']
				if key4 not in result_grouped[key1][key2][key3]:
					result_grouped[key1][key2][key3].update({key4:[]})
				
				result_grouped[key1][key2][key3][key4].append(res)

			max_width_col_0 = 0
			max_width_col_1 = 0
			max_width_col_3 = 0
			max_width_col_8 = 0
			max_width_col_9 = 0
			rowcount = 6
			currency_usd = parser._get_company_currency()

			subtotal_wax = {1:0.0,2:0.0,3:0.0,4:0.0,5:0.0,6:0}
			subtotal_loc = subtotal_wax.copy()
			grand_total = subtotal_wax.copy()
			for parent_loc,loc_sequence in sorted(result_grouped.keys(),key=lambda k:k[1]):
				curr_loc = False
				for blend in sorted(result_grouped[parent_loc,loc_sequence].keys()):
					for count in sorted(result_grouped[parent_loc,loc_sequence][blend].keys()):
						for sd in sorted(result_grouped[parent_loc,loc_sequence][blend][count].keys()):
							for line in result_grouped[parent_loc,loc_sequence][blend][count][sd]:
								qty = line['qty']
								qty = parser._uom_to_base(data, qty, line['uom'])
								qty_kgs = parser._uom_to_base(data, line['qty'], line['uom'], uom_to_id=(uom_kgs_id and uom_kgs_id or None))
								qty_shipped = line['qty_shipped']
								if qty <= 5 and qty_shipped>0.0:
									continue
								ws.write(rowcount,0,line['product_desc'], normal_style)
								if len(line['product_desc'] and line['product_desc'] or '')>max_width_col_0:
									max_width_col_0 = len(line['product_desc'])
								ws.write(rowcount,1,line['number'], normal_style)
								if len(line['number'] and line['number'] or '')>max_width_col_1:
									max_width_col_1 = len(line['number'])
								ws.write(rowcount,2,line['date'], normal_style)
								ws.write(rowcount,3,line['customer'], normal_style)
								if len(line['customer'] and line['customer'] or '')>max_width_col_3:
									max_width_col_3 = len(line['customer'])
								
								ws.write(rowcount,4,qty, normal_right_style2)

								sale_rate = parser._price_per_base(data, line['sale_rate'], line['uom'])
								net_rate = parser._price_per_base(data, line['net_rate'], line['uom'])
								insurance_rate = parser._price_per_base(data, line['insurance_rate'], line['uom'])
								term_rate = parser._price_per_base(data, line['term_rate'], line['uom'])
								comm_rate = parser._price_per_base(data, line['comm_rate'], line['uom'])
								freight_rate = line['freight_rate']
								if line['currency_id']!=currency_usd.id:
									sale_rate = parser._get_amount_company_currency(line['currency_id'],sale_rate,line['date2'])
									net_rate = parser._get_amount_company_currency(line['currency_id'],net_rate,line['date2'])
									insurance_rate = parser._get_amount_company_currency(line['currency_id'],insurance_rate,line['date2'])
									term_rate = parser._get_amount_company_currency(line['currency_id'],term_rate,line['date2'])
									comm_rate = parser._get_amount_company_currency(line['currency_id'],comm_rate,line['date2'])
									freight_rate = parser._get_amount_company_currency(line['currency_id'],freight_rate,line['date2'])
								freight_local_rate = line['freight_local_rate']

								ws.write(rowcount,5,net_rate, sale_type=='local' and normal_right_style or normal_right_style1)
								ws.write(rowcount,6,sale_type=='local' and sale_rate or line['incoterm_name'], sale_type=='local' and normal_right_style or normal_style)
								ws.write(rowcount,7,(net_rate*(sale_type=='local' and qty or qty_kgs)), normal_right_style1)
								if len(line['payment_term'] and line['payment_term'] or '')>max_width_col_8:
									max_width_col_8 = len(line['payment_term'])
								ws.write(rowcount,8,line['payment_term'], normal_style)
								ws.write(rowcount,9,(sale_type=='local' and (line['city'] and line['city'] or line['street3'] or ' ') or "%s, %s"%(line['port'],line['country'])).upper(), normal_style)
								ws.write(rowcount,10, line['period'], normal_style)
								ws.write(rowcount,11,line['comm'], normal_right_style1)
								if len("%s,%s"%(line['port'],line['country']))>max_width_col_9:
									max_width_col_9 = len("%s,%s"%(line['port'],line['country']))
								if sale_type == 'local':
									ws.write(rowcount,13,freight_local_rate, normal_right_style1)
									ws.write(rowcount,14,term_rate, normal_right_style1)
									ws.write(rowcount,15,insurance_rate, normal_right_style1)
									fob_rate = net_rate - freight_local_rate - term_rate - insurance_rate - comm_rate
									ws.write(rowcount,16,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
									# ws.write(rowcount,17,line['rate'], normal_right_style)
								else:
									ws.write(rowcount,13,freight_rate, normal_right_style1)
									ws.write(rowcount,14,freight_local_rate, normal_right_style1)
									ws.write(rowcount,15,term_rate, normal_right_style1)
									ws.write(rowcount,16,insurance_rate, normal_right_style1)
									fob_rate = net_rate - freight_rate - freight_local_rate - term_rate - insurance_rate - comm_rate
									ws.write(rowcount,17,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
									clm = 18
									for zone in mktzone:
										if zone==line['mktzone']:
											ws.write(rowcount,clm,fob_rate, sale_type=='local' and normal_right_style or normal_right_style1)
										else:
											clm+=1

									# ws.write(rowcount,19+len(mktzone)-1,line['rate'], normal_right_style)
								rowcount+=1
								subtotal_wax.update({
									1:subtotal_wax[1]+qty,
									2:subtotal_wax[2]+net_rate,
									3:subtotal_wax[3]+(net_rate*(sale_type=='local' and qty or qty_kgs)),
									4:subtotal_wax[4]+(fob_rate*qty),
									5:subtotal_wax[5]+(line['rate']*qty),
									6:subtotal_wax[6]+1,
								})
								curr_loc = line['loc_name']
							ws.write_merge(rowcount,rowcount,0,3, "Subtotal", subtotal_label_style)
							if sale_type == 'local':
								ws.write(rowcount,4, subtotal_wax[1], subtotal_style2)
								ws.write(rowcount,5, subtotal_wax[6] and subtotal_wax[2]/subtotal_wax[6] or 0.0, subtotal_style1)
								ws.write(rowcount,6, "", subtotal_label_style)
								ws.write(rowcount,7, subtotal_wax[3], subtotal_style)
								ws.write_merge(rowcount,rowcount,8,15, "", subtotal_label_style)
								ws.write(rowcount,16, subtotal_wax[1] and subtotal_wax[4]/subtotal_wax[1] or 0.0, subtotal_style1)
								# ws.write(rowcount,17, subtotal_wax[5]/subtotal_wax[1], subtotal_style1)
							else:
								ws.write(rowcount,4, subtotal_wax[1], subtotal_style2)
								ws.write(rowcount,5, subtotal_wax[6] and subtotal_wax[2]/subtotal_wax[6] or 0.0, subtotal_style)
								ws.write(rowcount,6, "", subtotal_label_style)
								ws.write(rowcount,7, subtotal_wax[3], subtotal_style)
								ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
								ws.write(rowcount,17, subtotal_wax[1] and subtotal_wax[4]/subtotal_wax[1] or 0.0, subtotal_style)
								ws.write_merge(rowcount,rowcount,18,17+len(mktzone), "", subtotal_label_style)
								# ws.write(rowcount,18+len(mktzone), subtotal_wax[5]/subtotal_wax[1], subtotal_style1)
							rowcount+=1

							subtotal_loc.update({
								1:subtotal_loc[1]+subtotal_wax[1],
								3:subtotal_loc[3]+subtotal_wax[3],
								5:subtotal_loc[5]+subtotal_wax[5],
								6:subtotal_loc[6]+1
							})
							for i in range(1,7):
								subtotal_wax[i]=0

				ws.write_merge(rowcount,rowcount,0,3, "Total "+(curr_loc and curr_loc or '') , subtotal_label_style)
				if sale_type == 'local':
					ws.write(rowcount,4, subtotal_loc[1], subtotal_style2)
					ws.write(rowcount,5, "", subtotal_style)
					ws.write(rowcount,6, "", subtotal_label_style)
					ws.write(rowcount,7, subtotal_loc[3], subtotal_style)
					ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
					# ws.write(rowcount,17, subtotal_loc[5]/subtotal_loc[1], subtotal_style1)
				else:
					ws.write(rowcount,4, subtotal_loc[1], subtotal_style2)
					ws.write(rowcount,5, "", subtotal_style)
					ws.write(rowcount,6, "", subtotal_label_style)
					ws.write(rowcount,7, subtotal_loc[3], subtotal_style)
					ws.write_merge(rowcount,rowcount,8,17+len(mktzone), "", subtotal_label_style)
					# ws.write(rowcount,18+len(mktzone), subtotal_loc[5]/subtotal_loc[1], subtotal_style1)
				rowcount+=1
				grand_total.update({
					1:grand_total[1]+subtotal_loc[1],
					3:grand_total[3]+subtotal_loc[3],
					5:grand_total[5]+subtotal_loc[5],
					6:grand_total[6]+1
				})
				for i in range(1,7):
					subtotal_loc[i]=0

			ws.write_merge(rowcount,rowcount,0,3, "Grand Total" , subtotal_label_style)
			if sale_type == 'local':
				ws.write(rowcount,4, grand_total[1], subtotal_style2)
				ws.write(rowcount,5, "", subtotal_style)
				ws.write(rowcount,6, "", subtotal_label_style)
				ws.write(rowcount,7, grand_total[3], subtotal_style)
				ws.write_merge(rowcount,rowcount,8,16, "", subtotal_label_style)
				# ws.write(rowcount,17, grand_total[5]/grand_total[1], subtotal_style1)
			else:
				ws.write(rowcount,4, grand_total[1], subtotal_style2)
				ws.write(rowcount,5, "", subtotal_style)
				ws.write(rowcount,6, "", subtotal_label_style)
				ws.write(rowcount,7, grand_total[3], subtotal_style)
				ws.write_merge(rowcount,rowcount,8,17+len(mktzone), "", subtotal_label_style)
				# ws.write(rowcount,18+len(mktzone), grand_total[5]/grand_total[1], subtotal_style1)

			ws.col(0).width = 256 * int((max_width_col_0<20 and max_width_col_0 or 20)*1.4)
			ws.col(1).width = 256 * int(max_width_col_1*1.4)
			ws.col(3).width = 256 * int((max_width_col_3<20 and max_width_col_3 or 20)*1.4)
			ws.col(8).width = 256 * int(max_width_col_8*1.4)
			ws.col(9).width = 256 * int((max_width_col_9<20 and max_width_col_9 or 20)*1.4)

			ws.col(4).width = 256 * int(len(str(grand_total[1]))*1.4)
			ws.col(7).width = 256 * int(len(str(grand_total[3]))*1.4)
			ws.col(12).width = 0
			if sale_type=='local':
				# ws.col(14).width = 0
				ws.col(15).width = 0
			elif sale_type=='export':
				ws.col(6).width = 256 * int(5*1.4)
				ws.col(14).width = 0
				ws.col(15).width = 0
				ws.col(16).width = 0
		pass
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																		
net_fob_price_xls('report.net.fob.price.report', 'net.fob.price.wizard', 'addons/ad_sales_report/report/pending_sales_report.mako', parser=net_fob_price_parser, header=False)
net_fob_price_xls('report.target.fob.report', 'net.fob.price.wizard', 'addons/ad_sales_report/report/pending_sales_report.mako', parser=net_fob_price_parser, header=False)
