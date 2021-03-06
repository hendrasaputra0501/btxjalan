from openerp.osv import fields,osv

class account_voucher(osv.osv):
	_inherit = "account.voucher"

	def _get_invoice_number(self, cr, uid, ids, field_names, arg=None, context=None):
		if context is None:
			context = {}
		result = {}
		if not ids: return result
		for voucher in self.browse(cr,uid,ids):			
			invoices = []
			if voucher.type in ('sale','receipt'):
				for line in voucher.line_cr_ids:
					if line.move_line_id and line.move_line_id.invoice and line.move_line_id.invoice.number not in invoices:
						invoices.append(line.move_line_id.invoice.number)
			elif voucher.type in ('purchase','payment'):
				for line in voucher.line_dr_ids:
					if line.move_line_id and line.move_line_id.invoice and line.move_line_id.invoice.reference not in invoices:
						invoices.append(line.move_line_id.invoice.reference)

			result[voucher.id] = "; ".join([str(x) for x in invoices])
		return result

	_columns = {
		'invoice_name': fields.function(_get_invoice_number,type='char',size=200,string='Invoice',readonly=True,
			store={
				"account.voucher" : (lambda self, cr, uid, ids, c={}: ids,['line_ids','state','line_dr_ids','line_cr_ids'],10), 
			},method=True),
	}

	def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
		context = context or {}
		
		res = super(account_voucher,self).onchange_line_ids(cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=context)
		if not res['value']['writeoff_amount']:
			res['value'].update({'writeoff_lines':[],'extra_writeoff':False})
		if line_cr_ids:
			#[
			#[5, False, False], 
			#[0, False, {'date_due': '2015-03-13', 'name': 'BLI-115-0028', 'date_original': '2015-01-12', 'move_line_id': 281, 
			#'amount_original': 29973.74, 'currency_id': 3, 'amount': 0, 'ar_ap_tax': False, 'reconcile': False, 'type': 'cr', 'amount_unreconciled': 29973.74, 'account_id': 230}], [0, False, {'date_due': '2015-03-13', 'name': 'BLI-115-0028', 'date_original': '2015-01-12', 'move_line_id': 282, 'amount_original': 2997.38, 'currency_id': 13, 'amount': 0, 'ar_ap_tax': False, 'reconcile': False, 'type': 'cr', 'amount_unreconciled': 2997.38, 'account_id': 230}]]

			for linecr in line_cr_ids:
				if linecr[2]:
					mvl = self.pool.get('account.move.line').browse(cr,uid,linecr[2]['move_line_id'])
					linecr[2].update({'ar_ap_tax':mvl.ar_ap_tax})
		if line_dr_ids:
			for linedr in line_dr_ids:
				if linedr[2]:
					mvl = self.pool.get('account.move.line').browse(cr,uid,linedr[2]['move_line_id'])
					linedr[2].update({'ar_ap_tax':mvl.ar_ap_tax})
		res['value'].update({
			'line_dr_ids':line_dr_ids,
			'line_cr_ids':line_cr_ids
			})
		return res

	def cancel_voucher(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		move_lines = []
		# print "=================================",ids
		for voucher in self.browse(cr, uid, ids, context=context):
			# refresh to make sure you don't unlink an already removed move
			voucher.refresh()
			vmr=[]
			for line in voucher.move_ids:
				if line.reconcile_id:
					move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
					move_lines.remove(line.id)
					#reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
					vmr.append(line.reconcile_id.id)

			reconcile_pool.unlink(cr, uid, vmr)
			if len(move_lines) >= 2:
				#print "=========masuk=========",len(move_lines)
				move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
			if voucher.move_id:
				move_pool.button_cancel(cr, uid, [voucher.move_id.id])
				move_pool.unlink(cr, uid, [voucher.move_id.id])
		res = {
			'state':'cancel',
			'move_id':False,
		}
		self.write(cr, uid, ids, res)
		return True


	# def unlink(self, cr, uid, ids, context=None):
		
	# 	for move_rec in self.browse(cr, uid, ids, context=context):
	# 		print "------------------------",type(move_rec),getattr(move_rec, 'opening_reconciliation')
	# 		try:
	# 			if move_rec.opening_reconciliation:
	# 				raise osv.except_osv(_('Error!'), _('You cannot unreconcile journal items if they has been generated by the \
	# 														opening/closing fiscal year process.'))
	# 		except:
	# 			continue
	# 	return super(account_move_reconcile, self).unlink(cr, uid, ids, context=context)



class account_voucher_line(osv.Model):
	_inherit = "account.voucher.line"
	_columns = {
		"ar_ap_tax":fields.boolean("AR/AP Tax Info"),
	}