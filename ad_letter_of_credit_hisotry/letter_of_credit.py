from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc

class loc(osv.osv):
	_inherit = "letterofcredit"
	
	_columns = {
		'lc_history_ids' : fields.one2many('letterofcredit.history','lc_id','Histories', readonly=True),
	}

class letter_of_credit_history_source(osv.Model):
	_name="letterofcredit.history.source"
	_columns = {
		'name': fields.char('Name', size=60, required=True),
		'model': fields.many2one('ir.model', 'Object', required=True),
	}

def _get_line_source_types(self, cr, uid, context=None):
	cr.execute('select m.model, s.name from letterofcredit_history_source s, ir_model m WHERE s.model = m.id order by s.name')
	return cr.fetchall()

class loc_history(osv.Model):

	def _get_source(self,cr,uid,ids,field_name,args,context=None):
		if not context:
			context={}
		res = {}
		for line in self.browse(cr, uid, ids, context):
			if line.value_source:
				if line.value_source._name=='ext.transaksi.line':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.ext_transaksi_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.ext_transaksi_id.ref or line.ref,
						'value_date' : line.value_source and line.value_source.ext_transaksi_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.ext_transaksi_id.date or line.date,
						'value_amount' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and (line.value_source.debit-line.value_source.credit) or line.amount,
						'value_currency' : line.value_source and line.value_source.ext_transaksi_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and \
									(line.value_source.ext_transaksi_id.currency_id and line.value_source.ext_transaksi_id.currency_id.id or line.value_source.ext_transaksi_id.journal_id.company_id.currency_id.id) or (line.currency_id and line.currency_id.id or False)
						}
					})
				elif line.value_source._name=='account.invoice.line':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.invoice_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.invoice_id.reference or line.ref,
						'value_date' : line.value_source and line.value_source.invoice_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.invoice_id.date_invoice or line.date,
						'value_amount' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.price_subtotal or line.amount,
						'value_currency' : line.value_source and line.value_source.invoice_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and \
									line.value_source.invoice_id.currency_id.id or (line.currency_id and line.currency_id.id or False),
						}
					})
				elif line.value_source._name=='account.invoice':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.reference or line.ref,
						'value_date' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.date_invoice or line.date,
						'value_amount' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.amount_total or line.amount,
						'value_currency' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and \
									line.value_source.currency_id.id or (line.currency_id and line.currency_id.id or False),
						}
					})
				elif line.value_source._name=='account.bank.loan':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.ref or line.ref,
						'value_date' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.effective_date or line.date,
						'value_amount' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.total_amount or line.amount,
						'value_currency' : line.value_source and line.value_source.journal_id and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and \
									(line.value_source.journal_id.currency and line.value_source.journal_id.currency.id or line.value_source.journal_id.company_id.currency_id.id) or (line.currency_id and line.currency_id.id or False),
						}
					})
				elif line.value_source._name=='account.bank.loan.interest':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.loan_id.name or line.ref,
						'value_date' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.payment_date or line.date,
						'value_amount' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.interest_amount or line.amount,
						'value_currency' : line.value_source and line.value_source.journal_id and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and \
									(line.value_source.journal_id.currency and line.value_source.journal_id.currency.id or line.value_source.journal_id.company_id.currency_id.id) or (line.currency_id and line.currency_id.id or False),
						}
					})
				elif line.value_source._name=='account.advance.payment':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.memo or line.ref,
						'value_date' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.effective_date or line.date,
						'value_amount' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and line.value_source.total_amount or line.amount,
						'value_currency' : line.value_source and line.value_source.lc_id and line.value_source.lc_id.id==line.lc_id.id and \
									line.value_source.currency_id.id or (line.currency_id and line.currency_id.id or False),
						}
					})
				elif line.value_source._name=='account.bank.loan.repayment':
					res.update({line.id : {
						'value_ref' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.loan_id.name or line.ref,
						'value_date' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.payment_date or line.date,
						'value_amount' : line.value_source and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and line.value_source.interest_amount or line.amount,
						'value_currency' : line.value_source and line.value_source.journal_id and line.value_source.loan_id and line.value_source.loan_id.lc_id and line.value_source.loan_id.lc_id.id==line.lc_id.id and \
									(line.value_source.journal_id.currency and line.value_source.journal_id.currency.id or line.value_source.journal_id.company_id.currency_id.id) or (line.currency_id and line.currency_id.id or False),
						}
					})
			else:
				res.update({line.id : {
					'value_ref' : line.ref,
					'value_date' : line.date,
					'value_amount' : line.amount,
					'value_currency' : (line.currency_id and line.currency_id.id or False),
					}
				})
		return res

	_name = "letterofcredit.history"
	_columns = {
		'lc_id' : fields.many2one('letterofcredit','LC'),
		'value_source'	: fields.reference('Source Document', selection=_get_line_source_types, size=200),
		'value_ref'		: fields.function(_get_source, type="char", size=128, string="Ref", method=True, multi="line_lc_history"),
		'value_date'	: fields.function(_get_source, type="date", string="Date", method=True, multi="line_lc_history"),
		'value_amount'	: fields.function(_get_source, type="float", string='Amount', digits_compute= dp.get_precision('Account'), method=True, multi="line_lc_history"),
		'value_currency'	: fields.function(_get_source, type="many2one", obj="res.currency", string="Currency", method=True, multi="line_lc_history"),
		
		'name' : fields.char('Name', size=200, required=True),
		'ref' : fields.char('Reference', size=200),
		'description' : fields.text('Description'),
		'amount' : fields.float('Amount', digits_compute= dp.get_precision('Account')),
		'currency_id' : fields.many2one('res.currency', 'Currency'),
		'date' : fields.date('Date'),
	}
