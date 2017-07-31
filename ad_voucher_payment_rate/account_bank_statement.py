from openerp.osv import fields,osv
from openerp.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from datetime import datetime

class account_bank_statement(osv.Model):
	def _get_move_line_selected(self, cr, uid, ids, field_names, arg=None, context=None):
		res = {}
		for statement in self.browse(cr, uid, ids, context=context):
			move_line_ids = []
			for line in statement.line_ids:
				if line.move_line_id and line.move_line_id.id not in move_line_ids:
					move_line_ids.append(line.move_line_id.id)
			
			res[statement.id]=move_line_ids
		return res

	_inherit = "account.bank.statement"
	_columns = {
		"company_bank_id" : fields.many2one('res.partner.bank','Company Bank Account'),
		"attention" : fields.char('Attn.', size=128),
		"cc" : fields.char('CC.', size=128),
		"header_note" : fields.text('Header'),
		"note" : fields.text('Notes'),
		"document_date":fields.date("Doc.Date"),
		'journal_type':fields.selection([('bank','Bank'),('cash','Cash')],string="Journal type",select=True,required=True),
		'journal_baru_id' : fields.many2one('account.journal','Journal'),
		'current_move_line_selected' : fields.function(_get_move_line_selected, type="many2many", string="Move Line Selected (Text)", obj="account.move.line"),
	}

	_defaults = {
		"document_date":fields.date.context_today,	
		"journal_type":lambda self,cr,uid,context:context.get('journal_type','bank'),
	}

	def check_status_condition(self, cr, uid, state, journal_type='bank'):
		return state in ('draft','open')

	def button_dummy(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		for statement in self.browse(cr, uid, ids, context=context):
			balance_end_est = statement.balance_start
			for line in statement.line_ids:
				balance_end_est+=line.amount
			self.write(cr, uid, [statement.id], {'balance_end_real':balance_end_est}, context=context)
		return True

	def button_create_voucher(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		obj_seq = self.pool.get('ir.sequence')
		voucher_obj = self.pool.get('account.voucher')
		voucher_line_obj = self.pool.get('account.voucher.line')
		line_obj = self.pool.get('account.move.line')
		for statement in self.browse(cr, uid, ids, context=context):
			if statement.name == '/':
				if statement.journal_id.sequence_id:
					st_number = obj_seq.next_by_id(cr, uid, statement.journal_id.sequence_id.id, context={'date':datetime.strptime(statement.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
				else:
					st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement', context={'date':datetime.strptime(statement.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
				self.write(cr, uid, [statement.id], {'name':st_number})
			else:
				st_number = statement.name
			for line in statement.line_ids:
				if not line.move_line_id or line.voucher_id:
					continue

				if line.account_id.type not in ('receivable','payable'):
					continue

				amount = line.amount or 0.0
				ttype = amount < 0 and 'payment' or 'receipt'
				sign = 1 if ttype == 'receipt' else -1
				if line.move_line_id.journal_id.type in ('sale', 'sale_refund'):
					type = 'customer'
					ttype = 'receipt'
					sign = 1
				elif line.move_line_id.journal_id.type in ('purchase', 'purchase_refund'):
					type = 'supplier'
					ttype = 'payment'
					sign = -1

				context.update({'st_move_line_id': line.move_line_id.id, 'line_type': line.type})
				next_number = self.get_next_st_line_number(cr, uid, st_number, line, context)
				result = voucher_obj.onchange_partner_id(cr, uid, [], partner_id=line.partner_id.id, journal_id=statement.journal_id.id, amount=sign*amount, currency_id= statement.currency.id, ttype=ttype, date=statement.date, context=context)
				voucher_res = { 'type': ttype,
					'number': next_number,
					'name': line.name,
					'partner_id': line.partner_id.id,
					'journal_id': statement.journal_id.id,
					'account_id': result['value'].get('account_id', statement.journal_id.default_credit_account_id.id),
					'company_id': statement.company_id.id,
					'currency_id': statement.currency.id,
					'date': statement.date,
					'amount': sign*amount,
					'payment_rate': result['value']['payment_rate'],
					'payment_rate_currency_id': result['value']['payment_rate_currency_id'],
					'period_id':statement.period_id.id}
				voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)

				voucher_line_dict =  {}
				for line_dict in result['value']['line_cr_ids'] + result['value']['line_dr_ids']:
					move_line = line_obj.browse(cr, uid, line_dict['move_line_id'], context)
					if line.move_line_id.move_id.id == move_line.move_id.id:
						voucher_line_dict = line_dict

				if voucher_line_dict:
					voucher_line_dict.update({'voucher_id': voucher_id})
					voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)

				line.write({'voucher_id':voucher_id})
		return True

class account_bank_statement_line(osv.Model):
	_inherit = "account.bank.statement.line"
	_columns = {
		"move_line_id" : fields.many2one('account.move.line','Move Line ID'),
		"partner_bank_id" : fields.many2one('res.partner.bank','Partner Bank Account'),
	}