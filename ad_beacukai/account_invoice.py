from openerp.osv import fields,osv

class account_invoice(osv.Model):
	_inherit = "account.invoice"

	_columns = {
		"bc_id"	: fields.many2one("beacukai","Beacukai"),
	}