from openerp.osv import osv,fields

class account_payment_term(osv.Model):
	_inherit ="account.payment.term"
	_columns = {
		'alias': fields.char("Alias",size=5),
	}