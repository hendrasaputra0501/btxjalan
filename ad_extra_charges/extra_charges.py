from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp

class extra_charges(osv.osv):
	_name = "extra.charges"
	_columns = {
		'type' : fields.selection([
			('in','In'),
			('out','Out')], 'Type'),
		'invoice_id' : fields.many2one('account.voucher','Invoice'),
		'po_id' : fields.many2one('purchase.order','Purchases Order'),
		'sale_id' : fields.many2one('sale.order','Sales Order'),
		'date_charge' : fields.date('Date Charge'),
		'effective_date' : fields.date('Effective Date'),
		'account_id' : fields.many2one('account.account','Account'),
		'journal_id' : fields.many2one('account.journal','Journal'),
		'purpose_id' : fields.many2one('extra.charge.purpose','Purpose'),
		'charge_ids' : fields.one2many('extra.charges.line','charge_id','Charge'),
		'pick_ids' : fields.many2many('stock.picking','charge_pick_rel','pick_id','charge_id','Picking'),
	}
	_defaults = {
		'type' : lambda self,cr,uid,context:context.get('type','out')
	}
extra_charges()

class extra_charge_purpose(osv.osv):
	_name = "extra.charge.purpose"
	_columns = {
		'name' : fields.char('Name',size=50),
		'desc' : fields.text('Description'),
	}
extra_charge_purpose()

class extra_charges_line(osv.osv):
	_name = "extra.charges.line"
	_columns = {
		'charge_id' : fields.many2one('extra.charges','Charge'),
		'name' : fields.char('Description',size=50),
		'account_id' : fields.many2one('account.account','Account'),
		'analytic_id' : fields.many2one('account.analytic.account','Analytic Account'),
		'type_line' : fields.selection([
			('charge','Charge'),
			('tax','Tax')],'Type'),
		'amount' : fields.float("Amount",required=True, digits_compute= dp.get_precision('amount')),
		'amount_currency' : fields.float("Amount Currency",required=True, digits_compute= dp.get_precision('amount_currency')),
		'currency_id' : fields.many2one('res.currency','Currency'),
	}
extra_charges_line()