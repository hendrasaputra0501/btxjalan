from openerp.osv import fields,osv

class account_invoice(osv.Model):
	_inherit="account.invoice"
	_columns = {
		"advances_detail":fields.one2many('voucher.split.advance.line','invoice_id',"Advances Detail"),
	}

class account_voucher_split_advances(osv.Model):
	_name = "account.voucher.split.advances"

	def _get_amount(self, cr, uid, ids, field, args, context=None):
		if context is None:
			context = {}
		res = {}
		for val in self.browse(cr, uid, ids, context=context):
			res[val.id]=0.0
			for line in val.lines:
				res[val.id]+=line.amount
		return res


	_columns = {
		"name" : fields.char("Description",size=64,required=True),
		"advance_id":fields.many2one('account.advance.payment',"Advance Document",ondelete="cascade"),
		"advance_date":fields.related('advance_id','date_payment',type='date',relation='account.advance.payment',string="Advance Date",readonly=True),
		"lines":fields.one2many('voucher.split.advance.line',"split_id","Details"),
		"voucher_id":fields.many2one("account.voucher","Voucher",required=True,ondelete="cascade"),
		"amount_alocated" : fields.function(_get_amount,type='float' ,string='Amount Alocated'),
	}

class voucher_split_advance_line(osv.Model):
	_name = "voucher.split.advance.line"
	_columns = {
		'name': fields.char("Description",size=64,required=True),
		"split_id": fields.many2one('account.voucher.split.advances',"Split ID",required=True,ondelete="cascade"),
		"invoice_id":fields.many2one("account.invoice","Invoice ID",required=True),
		'advance_id':fields.related('split_id','advance_id',type='many2one',relation="account.advance.payment",string="Advance Document"),
		"advance_date":fields.related('advance_id','date_payment',type='date',relation='account.advance.payment',string="Advance Date",readonly=True),
		"amount" : fields.float("Amount",required=True),
	} 

class account_voucher(osv.Model):
	_inherit = "account.voucher"

	def _check_advance(self,cr,uid,ids,field,args,context=None):
		if not context:context={}
		res ={}
		for voucher in self.browse(cr,uid,ids,context):
			val = False
			if voucher.type in ('sale','receipt'):
				for line in voucher.line_dr_ids:
					if line.move_line_id and line.amount>0.0:
						adv = self.pool.get('account.advance.payment').search(cr,uid,[('move_id','=',line.move_line_id.move_id.id)])
						if adv:
							val=True
			else:
				for line in voucher.line_cr_ids:
					if line.move_line_id and line.amount>0.0:
						adv = self.pool.get('account.advance.payment').search(cr,uid,[('move_id','=',line.move_line_id.move_id.id)])
						if adv:
							val=True
			res.update({voucher.id:val})
		return res

	_columns = {
		"any_advance_used":fields.function(_check_advance,type="boolean",string="Any Advance Used"),
		"advance_split_lines":fields.one2many('account.voucher.split.advances',"voucher_id","Advance Details"),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, required=True, states={'draft':[('readonly',False)]}),
	}

	def onchange_currency(self, cr, uid, ids, currency_id, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
		if context is None:
			context = {}
		if not currency_id or  not journal_id:
			return False
		vals = {'value':{} }
		currency_id = currency_id
		vals['value'].update({'currency_id': currency_id, 'payment_rate_currency_id': currency_id})
		#in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
		#without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
		#t0his common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
		if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
			vals['value']['amount'] = 0
			amount = 0
		if partner_id:
			res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
			for key in res.keys():
				vals[key].update(res[key])
		return vals

	def recompute_advances(self,cr,uid,ids,context=None):
		if not context:context={}
		voucher=self.browse(cr,uid,ids,context)[0]
		if voucher.advance_split_lines:
			self.pool.get('account.voucher.split.advances').unlink(cr,uid,[x.id for x in voucher.advance_split_lines])	
		if voucher.any_advance_used:
			mv = []
			line_split=[]
			container =[]
			if voucher.type in ('sale','receipt'):
				for line in voucher.line_dr_ids:
					if line.amount>0.0:
						mv.append(line.move_line_id.move_id.id)
				for inv in voucher.line_cr_ids:
					if inv.amount>0.0 and inv.move_line_id.invoice and inv.move_line_id.invoice.id:
						spl = {
							'name':inv.move_line_id.invoice.internal_number or '/',
							"invoice_id":inv.move_line_id.invoice.id,
							"amount" : 0.0,
							}
						if inv.move_line_id.invoice.id not in container:
							line_split.append((0,0,spl))
							container.append(inv.move_line_id.invoice.id)
			else:
				for line in voucher.line_cr_ids:
					if line.amount>0.0:
						mv.append(line.move_line_id.move_id.id)
				for inv in voucher.line_dr_ids:
					if inv.amount>0.0 and inv.move_line_id.invoice and inv.move_line_id.invoice.id:
						spl = {
							'name':inv.move_line_id.invoice.internal_number or '/',
							"invoice_id":inv.move_line_id.invoice.id,
							"amount" : 0.0,
							}
						if inv.move_line_id.invoice.id not in container:
							line_split.append((0,0,spl))
							container.append(inv.move_line_id.invoice.id)
			advance_ids = self.pool.get('account.advance.payment').search(cr,uid,[('move_id','in',mv)])
			if advance_ids:
				advances=self.pool.get('account.advance.payment').browse(cr,uid,advance_ids)
				spladv=[]
				for adv in advances:
					value = {
						"name" : adv.name,
						"advance_id":adv.id,
						"lines":line_split,
						#"voucher_id":voucher.id,
					}
					spladv.append((0,0,value))
				spl_value={'advance_split_lines':spladv}
				voucher.write(spl_value)

		return True