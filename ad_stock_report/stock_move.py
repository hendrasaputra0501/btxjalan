from openerp.osv import fields,osv

class stock_move(osv.Model):
	_inherit = "stock.move"

	def _get_rate_valuation(self, cr, uid, ids, field_names, args, context=None):
		if not context:context={}
		tax_obj = self.pool.get('account.tax')
		uom_obj = self.pool.get('product.uom')
		curr_obj = self.pool.get('res.currency')
		transport_pool = self.pool.get('stock.transporter')
		trans_chg_pool = self.pool.get('stock.transporter.charge')
		result = {}
		for x in ids:
			result[x]={
				"actual_rate": 0.0,
				"term_rate": 0.0,
				"commission_rate": 0.0,
				"insurance_rate": 0.0,
				"freight_rate": 0.0,
				"fob_rate": 0.0,
			}
		for sm in self.browse(cr,uid,ids):
			price_unit_usd = 0.0
			term_rate = 0.0
			commission_rate = 0.0
			insurance_rate = 0.0
			freight_rate = 0.0
			inv_price_unit_kg_usd = 0.0
			if sm.picking_id and sm.picking_id.type=='out' and sm.location_id.usage=='internal' and sm.location_dest_id.usage=='customer' and sm.state=='done':
				days =0.0
				date_invoice = (sm.invoice_line_id and sm.invoice_line_id.invoice_id and sm.invoice_line_id.invoice_id.date_invoice) or (sm.picking_id and sm.picking_id.date_done)
				company_id_browse = (sm.invoice_line_id and sm.invoice_line_id.invoice_id and sm.invoice_line_id.invoice_id.company_id) or (sm.picking_id and sm.picking_id.company_id)
				###############################compute actual rate in usd/kg###################################
				invoice_line = False
				if sm.invoice_line_id:
					inv_price_unit = sm.invoice_line_id and (sm.invoice_line_id.price_subtotal/sm.invoice_line_id.quantity) or 0.0
					tax_unit = sm.invoice_line_id and (sm.invoice_line_id.tax_amount/sm.invoice_line_id.quantity) or 0.0
					inv_price_unit_kg = uom_obj._compute_price(cr, uid, sm.invoice_line_id.uos_id.id, inv_price_unit, to_uom_id=sm.product_id.uom_id.id)
					
					tax_unit_kg = uom_obj._compute_price(cr, uid, sm.invoice_line_id.uos_id.id, tax_unit, to_uom_id=sm.product_id.uom_id.id)
					if not sm.invoice_line_id.invoice_id.use_kmk_ar_ap:
						inv_price_unit_kg_usd = curr_obj.compute(cr,uid,sm.invoice_line_id.invoice_id.currency_id.id,company_id_browse.currency_id.id,inv_price_unit_kg,context={'date':date_invoice})
					else:
						inv_price_unit_kg_usd = curr_obj.computerate(cr,uid,sm.invoice_line_id.invoice_id.currency_id.id,company_id_browse.currency_id.id,inv_price_unit_kg,context={'date':date_invoice,'reverse':True})

					if sm.invoice_line_id.invoice_id.currency_tax_id.id==company_id_browse.tax_base_currency.id:
						tax_amount_usd = curr_obj.computerate(cr,uid,sm.invoice_line_id.invoice_id.currency_id.id,company_id_browse.currency_id.id,tax_unit_kg,context={'date':date_invoice,'reverse':True})
					else:
						tax_amount_usd = curr_obj.compute(cr,uid,sm.invoice_line_id.invoice_id.currency_id.id,company_id_browse.currency_id.id,tax_unit_kg,context={'date':date_invoice})
					price_unit_usd = inv_price_unit_kg_usd+tax_amount_usd
				elif not sm.invoice_line_id and sm.picking_id.invoice_id and sm.picking_id.invoice_id.id:
					invoice_line_id = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',sm.picking_id.invoice_id.id),('product_id','=',sm.product_id.id),('uos_id','=',sm.sale_line_id.product_uom.id)],order="price_unit desc",limit=1)
					try:
						invoice_line = self.pool.get('account.invoice.line').browse(cr,uid,invoice_line_id)[0]
					except:
						invoice_line = self.pool.get('account.invoice.line').browse(cr,uid,invoice_line_id)
					inv_price_unit = (invoice_line.price_subtotal/invoice_line.quantity) or 0.0
				
					tax_unit = (invoice_line.tax_amount/invoice_line.quantity) or 0.0
					inv_price_unit_kg = uom_obj._compute_price(cr, uid, invoice_line.uos_id.id, inv_price_unit, to_uom_id=sm.product_id.uom_id.id)
					tax_unit_kg = uom_obj._compute_price(cr, uid, invoice_line.uos_id.id, tax_unit, to_uom_id=sm.product_id.uom_id.id)
					if not invoice_line.invoice_id.use_kmk_ar_ap:
						inv_price_unit_kg_usd = curr_obj.compute(cr,uid,invoice_line.invoice_id.currency_id.id,company_id_browse.currency_id.id,inv_price_unit_kg,context={'date':date_invoice})
					else:
						inv_price_unit_kg_usd = curr_obj.computerate(cr,uid,invoice_line.invoice_id.currency_id.id,company_id_browse.currency_id.id,inv_price_unit_kg,context={'date':date_invoice,'reverse':True})

					if invoice_line.invoice_id.currency_tax_id.id==company_id_browse.tax_base_currency.id:
						tax_amount_usd = curr_obj.computerate(cr,uid,invoice_line.invoice_id.currency_id.id,company_id_browse.currency_id.id,tax_unit_kg,context={'date':date_invoice,'reverse':True})
					else:
						tax_amount_usd = curr_obj.compute(cr,uid,invoice_line.invoice_id.currency_id.id,company_id_browse.currency_id.id,tax_unit_kg,context={'date':date_invoice})
					price_unit_usd = inv_price_unit_kg_usd+tax_amount_usd
				

				###############################compute freight rate in usd/kg###################################
				if sm.sale_type == 'local':
					if sm.picking_id and sm.picking_id.trucking_charge and sm.picking_id.trucking_charge.id:
						freight_kg = uom_obj._compute_price(cr, uid, sm.picking_id.trucking_charge.uom_id.id, sm.picking_id.trucking_charge.cost, to_uom_id=sm.product_id.uom_id.id)
						freight_kg_usd = curr_obj.compute(cr,uid,sm.picking_id.trucking_charge.currency_id.id,company_id_browse.currency_id.id,freight_kg,context={'date':date_invoice})
						freight_rate = freight_kg_usd
				elif sm.sale_type == 'export':
					total_weight=0.0
					sm_weight=uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, to_uom_id=sm.product_id.uom_id.id)
					for smp in sm.picking_id.move_lines:
						smp_weight=uom_obj._compute_qty(cr, uid, smp.product_uom.id, smp.product_qty, to_uom_id=smp.product_id.uom_id.id)
						total_weight+=smp_weight
					######freight########
					sm_fr_rate_kg_usd = 0.0
					if sm.picking_id and sm.picking_id.forwading_charge and sm.picking_id.forwading_charge.id:
						sm_fr_rate_kg = sm.picking_id.forwading_charge.cost/total_weight
						sm_fr_rate_kg_usd = curr_obj.compute(cr,uid,sm.picking_id.forwading_charge.currency_id.id,company_id_browse.currency_id.id,sm_fr_rate_kg,context={'date':date_invoice})
					######freight########
					sm_emkl_rate_kg_usd = 0.0
					if sm.picking_id and sm.picking_id.trucking_charge and sm.picking_id.trucking_charge.id:
						sm_emkl_rate_kg = sm.picking_id.trucking_charge.cost/total_weight
						sm_emkl_rate_kg_usd = curr_obj.compute(cr,uid,sm.picking_id.trucking_charge.currency_id.id,company_id_browse.currency_id.id,sm_emkl_rate_kg,context={'date':date_invoice})
					freight_rate = sm_fr_rate_kg_usd + sm_emkl_rate_kg_usd
				###############################compute term rate in usd/kg###################################

				payment_term = (sm.invoice_line_id.invoice_id and sm.invoice_line_id.invoice_id.payment_term) or (invoice_line and invoice_line.invoice_id and invoice_line.invoice_id.payment_term) or False
				if payment_term:
					for day in payment_term.line_ids:
						days+=day.days
				interest_global_id = self.pool.get('account.interest').search(cr,uid,[('type','=','global_rate')])
				interest_line_id = self.pool.get('account.interest.rate').search(cr,uid,[('interest_id','in',interest_global_id),('date_from','<=',date_invoice)],order="date_from desc",limit=1)
				try:
					interest_line = self.pool.get('account.interest.rate').browse(cr,uid,interest_line_id)[0]
				except:
					interest_line = self.pool.get('account.interest.rate').browse(cr,uid,interest_line_id)
				if sm.picking_id.sale_type=='export':					
					if payment_term:
						if payment_term.type=="sight":
							term_rate = 0.0
						elif payment_term.type=="usance":
							term_rate = (days/360.0)*(interest_line.rate/100.0)*inv_price_unit_kg_usd
					else:
						term_rate = 0.0
				elif sm.picking_id.sale_type=='local':
					if payment_term:
						if days>14:
							term_rate = (days/360.0)*(interest_line.rate/100.0)*inv_price_unit_kg_usd
						else:
							term_rate = 0.0
				###############################compute commission in usd/kg###################################
				if sm.sale_line_id and sm.invoice_line_id and sm.invoice_line_id.invoice_id and sm.invoice_line_id.invoice_id.commission_ids:
					n=0
					total_pct_comm = 0.0
					# for com in sm.invoice_line_id.invoice_id.commission_ids:
					# 	total_pct_comm += com.commission_percentage
					# 	n+=1
					# average_commission = total_pct_comm/n
					# commission_rate = average_commission/100.0*(inv_price_unit_kg_usd-sm_fr_rate_kg_usd) or 0.0

					for com in sm.invoice_line_id.invoice_id.commission_ids:
						for line in com.commission_lines:
							if line.sale_order_agent_id and line.sale_order_agent_id.sale_line_id and line.sale_order_agent_id.sale_line_id.id==sm.sale_line_id.id:
								total_pct_comm += line.commission_percentage
						n+=1
					average_commission = total_pct_comm/n
					commission_rate = average_commission/100.0*(inv_price_unit_kg_usd-sm_fr_rate_kg_usd) or 0.0


				###############################compute insurance in usd/kg###################################
				if sm.invoice_line_id and sm.invoice_line_id.invoice_id:
					domain_insurance_type = []
					if sm.picking_id.sale_type=='export' and sm.invoice_line_id.invoice_id.incoterms:
						incoterm = sm.invoice_line_id.invoice_id.incoterms.id
						domain_insurance_type = [('incoterms','=',incoterm),('type','=','sale'),('sale_type','=',sm.sale_type)]
					elif sm.picking_id.sale_type=='local':
						domain_insurance_type = [('type','=','sale'),('sale_type','=',sm.sale_type)]
					
					if domain_insurance_type:
						insurance_id = self.pool.get('insurance.type').search(cr, uid, domain_insurance_type)
						insurance_rate_id = self.pool.get('insurance.rate').search(cr,uid,[('insurance_id','in',insurance_id),('name','<=',date_invoice)],order="name desc",limit=1)
						try:
							insurance_rate_data = self.pool.get('insurance.rate').browse(cr,uid,insurance_rate_id)[0]
						except:
							insurance_rate_data = self.pool.get('insurance.rate').browse(cr,uid,insurance_rate_id)
						insurance_rate = insurance_rate_data.rate*(inv_price_unit_kg_usd+(inv_price_unit_kg_usd*0.1))/100.0

				result[sm.id]['actual_rate']=inv_price_unit_kg_usd
				result[sm.id]['term_rate']=term_rate
				result[sm.id]['commission_rate']=commission_rate
				result[sm.id]['insurance_rate']=insurance_rate
				result[sm.id]['freight_rate']=freight_rate
				result[sm.id]['fob_rate']=inv_price_unit_kg_usd-term_rate-commission_rate-freight_rate-insurance_rate
			elif sm.picking_id and sm.picking_id.type=='in' and sm.state=='done' and sm.location_id.usage=='customer' and sm.location_dest_id.usage=='internal':
				date_invoice = (sm.invoice_line_id and sm.invoice_line_id.invoice_id and sm.invoice_line_id.invoice_id.date_invoice) or (sm.picking_id and sm.picking_id.date_done)
				if sm.return_ref_id and sm.return_ref_id.id:
					ret_sm = self._get_rate_valuation(cr,uid,[sm.return_ref_id.id],field_names,args)
					result[sm.id]['actual_rate']=ret_sm.get(sm.return_ref_id.id,False).get('actual_rate',0.0) or 0.0
					result[sm.id]['term_rate']=ret_sm.get(sm.return_ref_id.id,False).get('term_rate',0.0) or 0.0
					result[sm.id]['commission_rate']=ret_sm.get(sm.return_ref_id.id,False).get('commission_rate',0.0) or 0.0
					result[sm.id]['insurance_rate']=ret_sm.get(sm.return_ref_id.id,False).get('insurance_rate',0.0) or 0.0
					result[sm.id]['freight_rate']=ret_sm.get(sm.return_ref_id.id,False).get('freight_rate',0.0) or 0.0
					result[sm.id]['fob_rate']=ret_sm.get(sm.return_ref_id.id,False).get('fob_rate',0.0) or 0.0
					# if sm.id == 3983:
					# 	print "smmmmmmmmmmmmmmmm------------>1 : ",sm
				else:
					price_kg = uom_obj._compute_price(cr, uid, sm.product_uom.id, sm.price_unit, to_uom_id=sm.product_id.uom_id.id)
					price_kg_usd = curr_obj.compute(cr,uid,sm.price_currency_id.id,sm.picking_id.company_id.currency_id.id,price_kg,context={'date':date_invoice})
					result[sm.id]['actual_rate']= price_kg_usd or 0.0
					result[sm.id]['term_rate']=  0.0
					result[sm.id]['commission_rate']= 0.0 
					result[sm.id]['insurance_rate']= 0.0 
					result[sm.id]['freight_rate']= 0.0 
					result[sm.id]['fob_rate']= price_kg_usd or 0.0
					# if sm.id == 3983:
					# 	print "smmmmmmmmmmmmmmmm------------>2 : ",sm
		return result
		
	_columns = {
		"actual_rate": fields.function(_get_rate_valuation,string="Actual Rate",multi="rate",group_operator="avg",digits=(16,4)),
		"term_rate": fields.function(_get_rate_valuation,string="Term Rate",multi="rate",group_operator="avg",digits=(16,4)),
		"commission_rate": fields.function(_get_rate_valuation,string="Commission Rate",multi="rate",group_operator="avg",digits=(16,4)),
		"insurance_rate": fields.function(_get_rate_valuation,string="Insurance Rate",multi="rate",group_operator="avg",digits=(16,4)),
		"freight_rate": fields.function(_get_rate_valuation,string="Freight Rate",multi="rate",group_operator="avg",digits=(16,4)),
		"fob_rate": fields.function(_get_rate_valuation,string="FOB Rate",multi="rate",group_operator="avg",digits=(16,4))
	}