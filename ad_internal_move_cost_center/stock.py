from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp.tools import float_compare

class stock_location(osv.Model):
	_inherit = "stock.location"
	_columns = {
		"analytic_account_id":fields.many2one('account.analytic.account',"Analytic Account"),
	}

class stock_move(osv.Model):
	_inherit = "stock.move"
	_columns = {
		"analytic_account_id":fields.many2one('account.analytic.account',"Analytic Account"),
		"cost_method":fields.related('product_id','cost_method',type='selection',selection=[
			('standard','Standard'),
			('average','Average'),
			('fifo','FIFO'),
			('lifo','LIFO'),
			],string="Cost Method"),
		"location_id_usage":fields.related('location_id','usage',type='selection',selection=[
			('view','View'),
			('supplier','Supplier'),
			('customer','Customer'),
			('internal','Internal'),
			('inventory','Inventory'),
			('production','Production'),
			('procurement','Procurement'),
			('transit','Transit'),
			],string="Source Usage"),
		"location_dest_id_usage":fields.related('location_dest_id','usage',type='selection',selection=[
			('view','View'),
			('supplier','Supplier'),
			('customer','Customer'),
			('internal','Internal'),
			('inventory','Inventory'),
			('production','Production'),
			('procurement','Procurement'),
			('transit','Transit'),
			],string="Destination Usage"),
	}
	def price_calculation(self, cr, uid, ids, context=None):
		'''
		This method puts the right price on the stock move, 
		adapts the price on the product when necessary
		and creates the necessary stock move matchings
		
		It returns a list of tuples with (move_id, match_id) 
		which is used for generating the accounting entries when FIFO/LIFO
		'''
		product_obj = self.pool.get('product.product')
		currency_obj = self.pool.get('res.currency')
		matching_obj = self.pool.get('stock.move.matching')
		uom_obj = self.pool.get('product.uom')
		
		product_avail = {}
		res = {}
		for move in self.browse(cr, uid, ids, context=context):
			# Initialize variables
			res[move.id] = []
			move_qty = move.product_qty
			move_uom = move.product_uom.id
			company_id = move.company_id.id
			ctx = context.copy()
			user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
			date_move = move.picking_id and move.picking_id.date_done!=False and move.picking_id.date_done or move.date
			ctx['force_company'] = move.company_id.id
			ctx['to_date']=date_move
			ctx['move_out_id']=move.id
			product = product_obj.browse(cr, uid, move.product_id.id, context=ctx)
			cost_method = product.cost_method
			product_uom_qty = uom_obj._compute_qty(cr, uid, move_uom, move_qty, product.uom_id.id, round=False)
			tuples = []
			if not product.id in product_avail:
				product_avail[product.id] = product.qty_available
			
			# Check if out -> do stock move matchings and if fifo/lifo -> update price
			# only update the cost price on the product form on stock moves of type == 'out' because if a valuation has to be made without PO, 
			# for inventories for example we want to use the last value used for an outgoing move
			# if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
			if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
				fifo = (cost_method != 'lifo')
				
				ctx.update({'location_dest_id':move.location_id.id, 'tracking_id':(move.tracking_id and move.tracking_id.id or False), 'date':(move.picking_id.date_done!='False' and move.picking_id.date_done or move.date)})
				tuples = product_obj.get_stock_matchings_fifolifo(cr, uid, [product.id], move_qty, fifo, 
																  move_uom, move.company_id.currency_id.id, context=ctx) #TODO Would be better to use price_currency_id for migration?
				price_amount = 0.0
				amount = 0.0
				#Write stock matchings
				for match in tuples: 
					matchvals = {'move_in_id': match[0], 'qty': match[1], 
								 'move_out_id': move.id}
					match_id = matching_obj.create(cr, uid, matchvals, context=context)
					res[move.id].append(match_id)
					price_amount += match[1] * match[2]
					amount += match[1]
				#Write price on out move
				# if (move.product_id.internal_type=='Raw Material' or float_compare(product_avail[product.id], product_uom_qty, precision_digits=4) in (1,0)) and product.cost_method in ['fifo', 'lifo']:
				if float_compare(product_avail[product.id], product_uom_qty, precision_digits=4) in (1,0) and product.cost_method in ['fifo', 'lifo']:
					if amount > 0:
						self.write(cr, uid, move.id, {'price_unit': round(price_amount / amount,4)}, context=context)
						product_obj.write(cr, uid, product.id, {'standard_price': round(price_amount / product_uom_qty,4)}, context=ctx)
					else:
						# self.write(cr, uid, move.id, {'price_unit': 0.0}, context=context)
						# product_obj.write(cr, uid, product.id, {'standard_price': 0.0}, context=ctx)
						raise osv.except_osv(_('Error'), _("Something went wrong finding stock moves for Product Code "+product.default_code+" on move id: "+str(move.id)))
				elif product_avail[product.id] < product_uom_qty and product.cost_method in ['fifo', 'lifo']:
					raise osv.except_osv(_('Error : Stock is not available yet for Product '+product.default_code), _("Current Available stock is only "+str(product_avail[product.id])+" while you want to transfer "+str(product_uom_qty)+" on move id: "+str(move.id)))
				else:
					new_price = uom_obj._compute_price(cr, uid, product.uom_id.id, product.standard_price, move_uom)
					self.write(cr, uid, move.id, {'price_unit': new_price}, context=ctx)
				#Adjust product_avail when not average and move returned from
				if (not move.move_returned_from or product.cost_method != 'average'):
					product_avail[product.id] -= product_uom_qty
			
			# for internal moves
			if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
				fifo = (cost_method != 'lifo')
				ctx.update({'location_dest_id':move.location_id.id, 'tracking_id':(move.tracking_id and move.tracking_id.id or False), 'date':(move.picking_id.date_done!='False' and move.picking_id.date_done or move.date)})
				tuples = product_obj.get_stock_matchings_fifolifo(cr, uid, [product.id], move_qty, fifo, 
																  move_uom, move.company_id.currency_id.id, context=ctx) #TODO Would be better to use price_currency_id for migration?
				price_amount = 0.0
				amount = 0.0
				#Write stock matchings
				for match in tuples: 
					matchvals = {'move_in_id': match[0], 'qty': match[1], 
								 'move_out_id': move.id}
					match_id = matching_obj.create(cr, uid, matchvals, context=context)
					res[move.id].append(match_id)
					price_amount += match[1] * match[2]
					amount += match[1]
				#Write price on out move
				# if product.cost_method in ['fifo', 'lifo']:
				# if (move.product_id.internal_type=='Raw Material' or float_compare(product_avail[product.id], product_uom_qty, precision_digits=4) in (1,0)) and product.cost_method in ['fifo', 'lifo']:
				if float_compare(product_avail[product.id], product_uom_qty, precision_digits=4) in (1,0) and product.cost_method in ['fifo', 'lifo']:
					if amount > 0:
						self.write(cr, uid, move.id, {'price_unit': round(price_amount / amount,4)}, context=context)
					else:
						raise osv.except_osv(_('Error'), _("Something went wrong finding stock moves for Product Code "+product.default_code))
				elif product_avail[product.id] < product_uom_qty and product.cost_method in ['fifo', 'lifo']:
					raise osv.except_osv(_('Error : Stock is not available yet for Product '+product.default_code), _("Current Available stock is only "+str(product_avail[product.id])+" while you want to transfer "+str(product_uom_qty)+" on move id: "+str(move.id)))
				else:
					new_price = uom_obj._compute_price(cr, uid, product.uom_id.id, product.standard_price, move_uom)
					self.write(cr, uid, move.id, {'price_unit': new_price}, context=ctx)
				#Adjust product_avail when not average and move returned from
				if (not move.move_returned_from or product.cost_method != 'average'):
					product_avail[product.id] -= product_uom_qty

			#Check if in => if price 0.0, take standard price / Update price when average price and price on move != standard price
			if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
				# if move.price_unit == 0.0:
					# new_price = uom_obj._compute_price(cr, uid, product.uom_id.id, product.standard_price, move_uom)
					# self.write(cr, uid, move.id, {'price_unit': new_price}, context=ctx)
				if product.cost_method == 'average':
				# elif product.cost_method == 'average':
					# move_product_price = uom_obj._compute_price(cr, uid, move_uom, move.price_unit, product.uom_id.id)
					if product_avail[product.id] > 0.0:
						amount_unit = product.standard_price
						new_std_price = ((amount_unit * product_avail[product.id])\
								+ (move_product_price * product_uom_qty))/(product_avail[product.id] + product_uom_qty)
					else:
						new_std_price = move_product_price
					product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price}, context=ctx)
				# Should create the stock move matchings for previous outs for the negative stock that can be matched with is in
				if product_avail[product.id] < 0.0:
					resneg = self._generate_negative_stock_matchings(cr, uid, [move.id], product, context=ctx)
					res[move.id] += resneg
				product_avail[product.id] += product_uom_qty
			#The return of average products at average price (could be made optional)
			if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal' and cost_method == 'average' and move.move_returned_from:
				move_orig = move.move_returned_from
				new_price = uom_obj._compute_price(cr, uid, move_orig.product_uom, move_orig.price_unit, product.uom_id.id)
				if (product_avail[product.id]- product_uom_qty) >= 0.0:
					amount_unit = product.standard_price
					new_std_price = ((amount_unit * product_avail[product.id])\
									 - (new_price * product_uom_qty))/(product_avail[product.id] - product_uom_qty)
					self.write(cr, uid, [move.id],{'price_unit': move_orig.price_unit,})
					product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price}, context=ctx)
				product_avail[product.id] -= product_uom_qty

			# print "==================analytic_line===================="
			resource = {}
			resource2 = {}
			if ((move.location_id.usage == 'internal' and move.location_dest_id.usage == 'inventory') or (move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal')) and move.product_id.internal_type in ('Stores','Fixed') and move.picking_id:
				if move.id not in resource:
					resource[move.id]=[]
				context.update({'tuples':tuples})
				# resource,analytic_line1=self._prepare_analytic_line(cr, uid, move, cost_method,resource,  ttype='credit',context=context)
				# x1=self.pool.get('account.analytic.line').create(cr,uid,analytic_line1)
				resource,analytic_line2=self._prepare_analytic_line(cr, uid, move, cost_method,resource,  ttype='debit', context=ctx)
				x2=self.pool.get('account.analytic.line').create(cr,uid,analytic_line2)
		return res

	def _prepare_analytic_line(self, cr, uid, obj_line,cost_method,res={},  ttype='credit',context=None):
		"""
		Prepare the values given at the create() of account.analytic.line upon the validation of a journal item having
		an analytic account. This method is intended to be extended in other modules.

		:param obj_line: browse record of the account.move.line that triggered the analytic line creation
		"""
		journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, obj_line, context=context)
		#analytic_journal_id = self.pool.get('account.analytic.journal').search(cr,uid,[('name','in',('Production','production'))])
		journal_id = 1
		uom_obj = self.pool.get('product.uom')
		product_obj = self.pool.get('product.product')
		matching_obj = self.pool.get('stock.move.matching')
		#print "-==-----------",obj_line.product_id.name, obj_line.location_id.analytic_account_id.name
		if ttype=='debit':
			account_id = (obj_line.analytic_account_id and obj_line.analytic_account_id.id) or (obj_line.location_dest_id.analytic_account_id and obj_line.location_dest_id.analytic_account_id.id) or False
		else:
			account_id = (obj_line.analytic_account_id and obj_line.analytic_account_id.id) or (obj_line.location_id.analytic_account_id and obj_line.location_id.analytic_account_id.id) or False
		if not account_id:
			if ttype=='credit':
				raise osv.except_osv(_('Error'), _('Please define analytic account for source location') % ())
			elif ttype=='debit':
				raise osv.except_osv(_('Error'), _('Please define analytic account for destination location or define analytic account on the line') % ())
		if cost_method in ('fifo','lifo'):
			fifo = (cost_method != 'lifo')
			context.update({'lot_ids':obj_line.prodlot_id and [obj_line.prodlot_id.id] or False})
			context.update({'location_dest_id':obj_line.location_id.id})
			price_amount = 0.0
			amount = 0.0
			tuples = context.get('tuples',[])
			#Write stock matchings
			for match in tuples: 
				matchvals = {'move_in_id': match[0], 'qty': match[1], 
							 'move_out_id': obj_line.id}
				# match_id = matching_obj.create(cr, uid, matchvals, context=context)

				price_amount += match[1] * match[2]
				amount += match[1]


			# if amount>0.0:
			# 	self.write(cr, uid, obj_line.id, {'price_unit': price_amount / amount}, context=context)
			#product_obj.write(cr, uid, product.id, {'standard_price': price_amount / product_uom_qty}, context=ctx)
			return res,{'name': obj_line.name or obj_line.product_id.name or '',
					'date': obj_line.date,
					'account_id': account_id,
					'unit_amount': obj_line.product_qty,
					'product_id': obj_line.product_id and obj_line.product_id.id or False,
					'product_uom_id': obj_line.product_uom and obj_line.product_uom.id or False,
					'amount': ttype=='debit' and price_amount or (-1*price_amount),
					'general_account_id': ttype=='debit' and acc_dest or acc_src,
					'journal_id': journal_id,
					'ref': obj_line.picking_id.name,
					'user_id': uid,
				   }
		else:
			amount = obj_line.product_qty * uom_obj._compute_price(cr, uid, obj_line.product_uom.id, obj_line.product_id.standard_price, obj_line.product_uom.id)
			return res,{'name': obj_line.name or obj_line.product_id.name or '',
					'date': obj_line.date,
					'account_id': account_id,
					'unit_amount': obj_line.product_qty,
					'product_id': obj_line.product_id and obj_line.product_id.id or False,
					'product_uom_id': obj_line.product_uom and obj_line.product_uom.id or False,
					'amount': ttype=='debit' and amount or (-1*amount),
					'general_account_id': ttype=='debit' and acc_dest or acc_src,
					'journal_id': journal_id,
					'ref': obj_line.picking_id.name,
					'user_id': uid,
				   }

	# def _create_cost_center_internal_move(self, cr, uid, move, matches, src_account_id, dest_account_id, reference_amount, reference_currency_id, type='', context=None):
	# 	"""
	# 	Generate the account.analytic.line values to post to track the stock valuation difference due to the
	# 	processing of the given stock move.
	# 	"""
	# 	move_list = []
	# 	# Consists of access rights 
	# 	# TODO Check if amount_currency is not needed
	# 	match_obj = self.pool.get("stock.move.matching")
	# 	if type == 'out' and move.product_id.cost_method in ['fifo', 'lifo']:
	# 		for match in match_obj.browse(cr, uid, matches, context=context):
	# 			move_list += [(match.qty, match.qty * match.price_unit_out)]
	# 	elif type == 'in' and move.product_id.cost_method in ['fifo', 'lifo']:
	# 		move_list = [(move.product_qty, reference_amount)]
	# 	else:
	# 		move_list = [(move.product_qty, reference_amount)]

	# 	res = []
	# 	for item in move_list:
	# 		# prepare default values considering that the destination accounts have the reference_currency_id as their main currency
	# 		partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
	# 		debit_line_vals = {
	# 					'name': move.name,
	# 					'product_id': move.product_id and move.product_id.id or False,
	# 					'quantity': item[0],
	# 					'product_uom_id': move.product_uom.id, 
	# 					'ref': move.picking_id and move.picking_id.name or False,
	# 					'date': time.strftime('%Y-%m-%d'),
	# 					'partner_id': partner_id,
	# 					'debit': item[1],
	# 					'account_id': dest_account_id,
	# 		}
	# 		credit_line_vals = {
	# 					'name': move.name,
	# 					'product_id': move.product_id and move.product_id.id or False,
	# 					'quantity': item[0],
	# 					'product_uom_id': move.product_uom.id, 
	# 					'ref': move.picking_id and move.picking_id.name or False,
	# 					'date': time.strftime('%Y-%m-%d'),
	# 					'partner_id': partner_id,
	# 					'credit': item[1],
	# 					'account_id': src_account_id,
	# 		}
	# 		res += [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
	# 	return res
