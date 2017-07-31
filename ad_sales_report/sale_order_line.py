from openerp.osv import fields,osv

class sale_order_line(osv.Model):
	_inherit = "sale.order.line"

	def _get_sale_order(self, cr, uid, ids, context=None):
		if context is None:context={}
		res = []
		for so in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
			if so.order_line:
				for line in so.order_line:
					if line.id not in res:
						res.append(line.id)
		return res

	def _get_sale_order_agent(self, cr, uid, ids, context=None):
		if context is None:context={}
		res = []
		for soa in self.pool.get('sale.order.agent').browse(cr, uid, ids, context=context):
			if soa.sale_line_id and soa.sale_line_id.id not in res:
				res.append(soa.sale_line_id.id)
		return res

	def _get_net_fob_price(self, cr, uid, ids, field_names, args, context=None):
		if context is None:context={}
		
		# tax_obj = self.pool.get('account.tax')
		uom_obj = self.pool.get('product.uom')
		transport_pool = self.pool.get('stock.transporter')
		trans_chg_pool = self.pool.get('stock.transporter.charge')
		curr_obj = self.pool.get('res.currency')
		acc_interest_obj = self.pool.get('account.interest')
		acc_interest_rate_obj = self.pool.get('account.interest.rate')
		insurance_type_obj = self.pool.get('insurance.type')
		insurance_rate_obj = self.pool.get('insurance.rate')

		result = {}
		for sol in self.browse(cr, uid, ids):
			result[sol.id]={
				"actual_rate": 0.0,
				"term_rate": 0.0,
				"commission_rate": 0.0,
				"insurance_rate": 0.0,
				"freight_rate": 0.0,
				"net_fob_price": 0.0,
			}

			if not sol.order_id:
				continue
			
			company_curry = sol.order_id.company_id.currency_id
			current_curry = sol.order_id.pricelist_id.currency_id
			
			price_unit_company_curr = curr_obj.compute(cr, uid, current_curry.id, company_curry.id, (sol.price_unit-(sol.tax_amount/(sol.product_uom_qty or 1.0))), context={'date':sol.order_id.date_order}, round=False)
			term_rate = 0.0
			commission_rate = 0.0
			insurance_rate = 0.0
			freight_rate = 0.0

			########## FREIGHT CALCULATION
			if sol.sale_type == 'local' or sol.order_id.sale_type == 'local':
				trans_ids = transport_pool.search(cr, uid, [('type','=','trucking'),('charge_type','=','sale'),('sale_type','=',sol.sale_type or sol.order_id.sale_type)])
				chg_ids = trans_chg_pool.search(cr, uid, [('transporter_id','in',trans_ids),('cost_type','=','type1'),('date_from','<=',sol.order_id.date_order)],order="cost desc",limit=1)
				
				if chg_ids:
					chg = trans_chg_pool.browse(cr, uid, chg_ids[0])
					freight_rate = uom_obj._compute_price(cr, uid, chg.uom_id.id, chg.cost, to_uom_id=sol.product_uom.id)
					freight_rate = curr_obj.compute(cr, uid, chg.currency_id.id, company_curry.id, freight_rate, context={'date':sol.order_id.date_order})
			elif sol.sale_type == 'export' or sol.order_id.sale_type == 'export':
				freight_rate = curr_obj.compute(cr, uid, sol.order_id.freight_rate_currency and sol.order_id.freight_rate_currency.id or current_curry.id, company_curry.id, sol.order_id.freight_rate_value or 0.0,context={'date':sol.order_id.date_order})
			
			########## TERM RATE CALCULATION
			days = 0.0
			interest_global_id = acc_interest_obj.search(cr,uid,[('type','=','global_rate')])
			interest_line_id = acc_interest_rate_obj.search(cr,uid,[('interest_id','in',interest_global_id),('date_from','<=',sol.order_id.date_order)],order="date_from desc",limit=1)
			try:
				interest_line = acc_interest_rate_obj.browse(cr,uid,interest_line_id)[0]
			except:
				interest_line = acc_interest_rate_obj.browse(cr,uid,interest_line_id)

			payment_term = sol.order_id.payment_term or False
			if payment_term:
				for day in payment_term.line_ids:
					days+=day.days
			if sol.sale_type=='export' or sol.order_id.sale_type=='export':					
				if payment_term:
					if payment_term.type=="sight":
						term_rate = 0.0
					elif payment_term.type=="usance":
						term_rate = (days/360.0)*(interest_line.rate/100.0)*price_unit_company_curr
				else:
					term_rate = 0.0
			elif sol.sale_type=='local' or sol.order_id.sale_type=='local':
				if payment_term:
					if days>14:
						term_rate = (days/360.0)*(interest_line.rate/100.0)*price_unit_company_curr
					else:
						term_rate = 0.0
			
			########## COMMISSION RATE CALCULATION
			if sol.order_id.agent_ids:
				n = 0
				total_pct_comm = 0.0
				for agent in sol.order_id.agent_ids:
					if agent.sale_line_id and agent.sale_line_id.id==sol.id:
						n += 1
						total_pct_comm += agent.commission_percentage
				if n>=1:
					average_commission = total_pct_comm/n
					commission_rate = average_commission/100.0*price_unit_company_curr

			########## INSURANCE RATE CALCULATION
			domain_insurance_type = []
			if (sol.sale_type=='export' or sol.order_id.sale_type=='export') and sol.order_id.incoterm:
				domain_insurance_type = [('incoterms','=',sol.order_id.incoterm.id),('type','=','sale'),('sale_type','=',sol.sale_type or sol.order_id.sale_type)]
			elif sol.sale_type=='local' or sol.order_id.sale_type=='local':
				domain_insurance_type = [('type','=','sale'),('sale_type','=',sol.sale_type or sol.order_id.sale_type)]
			if domain_insurance_type:
				insurance_id = insurance_type_obj.search(cr, uid, domain_insurance_type)
				insurance_rate_id = insurance_rate_obj.search(cr, uid, [('insurance_id','in',insurance_id),('name','<=',sol.order_id.date_order)],order="name desc",limit=1)
				if insurance_rate_id:
					insurance_rate_data = insurance_rate_obj.browse(cr, uid, insurance_rate_id[0])
					insurance_rate = insurance_rate_data.rate*(price_unit_company_curr+(price_unit_company_curr*0.1))/100.0
					
			result[sol.id]['actual_rate']=price_unit_company_curr
			result[sol.id]['term_rate']=term_rate
			result[sol.id]['commission_rate']=commission_rate
			result[sol.id]['insurance_rate']=insurance_rate
			result[sol.id]['freight_rate']=freight_rate
			result[sol.id]['net_fob_price']=price_unit_company_curr-term_rate-commission_rate-freight_rate-insurance_rate
		return result

	_columns = {
		"actual_rate": fields.function(_get_net_fob_price, string="Actual Rate", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id'],10),
				'sale.order' : (_get_sale_order,['pricelist_id'],10), 
			}, multi="net_fob_price"),
		"term_rate": fields.function(_get_net_fob_price, string="Term Rate", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id','sale_type'],11),
				'sale.order' : (_get_sale_order,['pricelist_id','payment_term','sale_type'],11),
			}, multi="net_fob_price"),
		"commission_rate": fields.function(_get_net_fob_price, string="Commission Rate", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id'],11),
				'sale.order' : (_get_sale_order,['pricelist_id'],11), 
				'sale.order.agent' : (_get_sale_order_agent,['sale_line_id','commission_percentage'],10),
			}, multi="net_fob_price"),
		"insurance_rate": fields.function(_get_net_fob_price, string="Insurance Rate", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id','sale_type'],11),
				'sale.order' : (_get_sale_order,['pricelist_id','incoterm','sale_type'],11), 
			}, multi="net_fob_price"),
		"freight_rate": fields.function(_get_net_fob_price, string="Freight Rate", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id','sale_type'],11),
				'sale.order' : (_get_sale_order,['pricelist_id','incoterm','sale_type','freight_rate_value','freight_rate_currency'],11),
			}, multi="net_fob_price"),
		"net_fob_price": fields.function(_get_net_fob_price, string="Net FOB Price", type="float", group_operator="avg", digits=(16,4),
			store={
				'sale.order.line' : (lambda self,cr,uid,ids,context={}:ids,['price_unit','product_uom_qty','product_uom','tax_id','sale_type'],12),
				'sale.order' : (_get_sale_order,['pricelist_id','payment_term','incoterm','sale_type'],12), 
				'sale.order.agent' : (_get_sale_order_agent,['sale_line_id','commission_percentage'],11),
			}, multi="net_fob_price")
	}