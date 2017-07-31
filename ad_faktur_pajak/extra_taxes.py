from openerp.osv import fields,osv
import datetime
import decimal_precision as dp
from tools.translate import _

class account_invoice(osv.Model):
	_inherit = "account.invoice"
	_columns = {
		'extra_taxes':fields.one2many('account.invoice.extra.taxes.line','doc_source_invoice',"Extra Taxes",readonly=True),
	}

class account_invoice_tax_reference(osv.Model):
	_name="account.invoice.tax.reference"
	_columns = {
		'name': fields.char('Name', size=60, required=True),
		'model': fields.many2one('ir.model', 'Object', required=True),
		'domain_eval': fields.text("Domain"),
	}

def _get_source_types(self, cr, uid, context=None):
	cr.execute('select m.model, s.name from account_invoice_tax_reference s, ir_model m WHERE s.model = m.id order by s.name')
	return cr.fetchall()


class account_invoice_extra_taxes(osv.Model):
	_name="account.invoice.extra.taxes"

	_columns = {
		"name"				: fields.char("Number",required=True,size=64),
		"journal_id"		: fields.many2one('account.journal',"Journal",required=True),
		"account_id"		: fields.many2one('account.account',"Account",required=True),
		"entry_date"		: fields.date("Entry Date",required=True),
		"partner_id"		: fields.many2one("res.partner","Partner",required=True),
		"effective_date"	: fields.date("Effective Date"),
		"period_id"			: fields.many2one('account.period',"Period",required=True),
		"rate_used"			: fields.selection([('bank',"Bank Indonesia"),('kmk',"KMK Rate")],"Rate Used",required=True),
		"line_ids"			: fields.one2many("account.invoice.extra.taxes.line",'extra_id',"Extra Tax"),
		'invoice_type'		: fields.selection([('out_invoice','Sale Charges'),('in_invoice','Purchase Charges')],"Charges Type",required=True),
		"company_id"		: fields.many2one('res.company',"Company",required=True),
		'parent_doc_source'	: fields.reference('Parent Source', required=True, selection=_get_source_types, size=128, help="User can choose the source document on which he wants to create documents"),
		"move_id"			: fields.many2one('account.move',"Journal Entries",readonly=True),
		'move_ids'			: fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True, states={'draft':[('readonly',False)]}),
		"state"				: fields.selection([('draft','Draft'),('posted','Posted'),('cancel','Cancelled')],"State",required=True),
	}

	_defaults = {
		'name'			: '/',
		'entry_date'	: lambda *a: datetime.date.today().strftime('%Y-%m-%d'),
		'rate_used'		: lambda *a:'kmk',
		"state"			: lambda *a:'draft',
		'invoice_type'	: lambda self,cr,uid,context:context.get('invoice_type','out_invoice'),
		'company_id'	: lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id
	}

	def onchange_journal_id(self,cr,uid,ids,journal_id,context=None):
		if not context:context={}
		val = {}
		if journal_id:
			journal = self.pool.get('account.journal').browse(cr,uid,journal_id,context)
			val.update({'account_id':journal.default_credit_account_id and journal.default_credit_account_id.id or False})
		return {'value':val}

	def onchange_parent_doc_source(self,cr,uid,ids,parent_doc_source,context=None):
		if not context:context={}
		domain =False
		ctx = {}
		if parent_doc_source:
			cr.execute("""select s.domain_eval from account_invoice_tax_reference s, ir_model m WHERE m.model = '%s' order by s.domain_eval"""%parent_doc_source.split(',')[0])
			domain_eval = cr.fetchall()
			domain_eval = eval(str(domain_eval[0][0]))
			domain = []
			for x in domain_eval:
				if isinstance(x,(tuple)):
					c=(x[0],x[1],eval(x[2]))
					domain.append(c)
				else:
					domain.append(x)
			# print "domain=================",domain
			ctx.update({'parent_doc_source':domain})
		return {'context':ctx}

	def action_post_tax(self,cr,uid,ids,context=None):
		if not context:context={}
		cur_obj = self.pool.get('res.currency')
		for ext_tax in self.browse(cr,uid,ids,context=context):
			lines =[]
			name = self.pool.get('ir.sequence').next_by_code(cr, uid, ext_tax.journal_id.sequence_id.code, context=None)
			move = {
				'name': "/",
				'line_id': lines,
				'journal_id': ext_tax.journal_id and ext_tax.journal_id.id or False,
				'date': ext_tax.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
				'narration': name or ext_tax.name or '/',
				'company_id': ext_tax.company_id and ext_tax.company_id.id,
				"period_id":ext_tax.period_id and ext_tax.period_id.id or False,
				}
			total_amt = 0.0
			total_cur = 0.0
			for line in ext_tax.line_ids:
				context.update({'date':ext_tax.effective_date or datetime.date.today().strftime("%Y-%m-%d")})
				sign = ext_tax.invoice_type =='out_invoice' and -1 or 1
				position = line.tax_amount >0 and 1 or -1
				tax_amount = position * cur_obj.compute(cr, uid, ext_tax.journal_id.currency and ext_tax.journal_id.currency.id or ext_tax.company_id.currency_id.id ,ext_tax.company_id.currency_id.id, abs(line.tax_amount), context=context)
				xline={
					'name': line.name or '/',
					'debit': sign *position > 0 and abs(tax_amount) or False,
					'credit': sign * position < 0 and abs(tax_amount) or False,
					'account_id': line.tax_id and line.tax_id.account_collected_id and line.tax_id.account_collected_id.id or False,
					'tax_code_id': line.tax_id and line.tax_id.id or False,
					'tax_amount': line.tax_amount or False,
					'ref':ext_tax.name or line.name,
					'date': ext_tax.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
					'currency_id': line.multicurrency and line.currency_id and line.currency_id.id or False,
					'amount_currency': sign * position * line.amount_currency or 0.0,
					'company_id': ext_tax.company_id and ext_tax.company_id.id or False,
					"period_id":ext_tax.period_id and ext_tax.period_id.id or False,
					}
				total_amt += tax_amount
				total_cur +=  sign * position * line.amount_currency or 0.0
				lines.append((0,0,xline))
			counter_sign = line.tax_amount >0 and 1 or -1
			xline={
					'name': line.name or '/',
					'debit': counter_sign > 0 and abs(total_amt) or False,
					'credit': counter_sign < 0 and abs(total_amt) or False,
					'account_id': ext_tax.account_id and ext_tax.account_id.id or False,
					'ref':name or ext_tax.name or '/',
					'date': ext_tax.effective_date or datetime.date.today().strftime("%Y-%m-%d"),
					'currency_id': line.multicurrency and line.currency_id and line.currency_id.id or False,
					'amount_currency': counter_sign >0 and abs(total_cur) or total_cur or 0.0,
					'company_id': ext_tax.company_id and ext_tax.company_id.id or False,
					"period_id":ext_tax.period_id and ext_tax.period_id.id or False,
					}
			lines.append((0,0,xline))
			move.update({'line_id':lines})
			print "move---------------",move
			move_id = self.pool.get('account.move').create(cr,uid,move,context)
			self.pool.get('account.move').post(cr,uid,[move_id],context)
			ext_tax.write({'move_id':move_id,'state':'posted'})
		return True

	def action_cancel(self,cr,uid,ids,context=None):
		if not context:context={}
		for ext_tax in self.browse(cr,uid,ids,context):
			if ext_tax.state == 'posted':
				self.pool.get('account.move').button_cancel(cr,uid,[ext_tax.move_id.id])
				self.pool.get('account.move').unlink(cr,uid,[ext_tax.move_id.id])
			ext_tax.write({'state':'cancel','move_id':False})
		return True

	def action_draft(self,cr,uid,ids,context=None):
		if not context:context={}
		for ext_tax in self.browse(cr,uid,ids,context):
			if ext_tax.state=='cancel':
				ext_tax.write({'state':'draft'})
		return True

class account_invoice_extra_taxes_line(osv.Model):
	_name="account.invoice.extra.taxes.line"

	def _get_doc_source_inv(self, cr, uid, ids, field_name, arg, context):
		result = {}
		for line in self.browse(cr, uid, ids, context=context):
			# print "===========1==========",line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='account.invoice' and line.doc_source.id or False
			if line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='account.invoice':
				result[line.id] = line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='account.invoice' and line.doc_source.id or False
			elif line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='account.invoice.line':
				invoice_line = line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='account.invoice.line' and line.doc_source.id
				invline =self.pool.get('account.invoice.line').browse(cr,uid,invoice_line)
				result[line.id] =  invline and invline.invoice_id and invline.invoice_id.id or False
		return result

	def _get_doc_source_ext(self, cr, uid, ids, field_name, arg, context):
		result = {}
		for line in self.browse(cr, uid, ids, context=context):
			# print "==========2===========",line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='extra.transaksi.line' and line.id or False
			result[line.id] = line and line.doc_source and str(line.doc_source).split(",")[0].split("(")[1]=='extra.transaksi.line' and line.id or False
		return result

	_columns = {
		"name"				: fields.char("Description",size=128),
		"extra_id"			: fields.many2one("account.invoice.extra.taxes","Extra Tax",ondelete="cascade",required=True),
		"tax_id"			: fields.many2one("account.tax","Tax",required=True),
		"multicurrency"		: fields.boolean("Multi Currency",help="Check this box if the faktur pajak received using multicurrency, if not checked, it will be assumed that you entry in Base Currency"),
		"currency_id"		: fields.many2one("res.currency","2nd Currency"),
		"faktur_pajak_no"	: fields.char("No.Faktur",size=20),
		"kmk_rate_id"		: fields.many2one("res.currency.tax.rate","KMK Rate"),
		"bank_rate_id"		: fields.many2one("res.currency.rate","Bank Rate"),
		"base_amount"		: fields.float("Base Amount",digits_compute= dp.get_precision('Account'), required=True),
		"tax_amount"		: fields.float("Tax Amount",digits_compute= dp.get_precision('Account'), required=True),
		"amount_currency"	: fields.float("Tax Amount (2nd Currency)",digits_compute= dp.get_precision('Account'), required=True),

		'doc_source'		: fields.reference('Source Document', required=True, selection=_get_source_types, size=128, help="User can choose the source document on which he wants to create documents"),
		'doc_source_invoice': fields.function(_get_doc_source_inv,type="many2one",relation="account.invoice",string="Invoice",store=True),
		'doc_source_ext' 	: fields.function(_get_doc_source_ext,type="many2one",relation="ext.transaksi.line",string="Extra Transaction"),
	}
	_defaults = {
	}


