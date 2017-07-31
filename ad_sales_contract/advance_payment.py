from openerp.osv import fields, osv

from tools.translate import _

class advance_payment(osv.Model):
	_inherit = 'account.advance.payment'
	_columns = {
		"sale_ids"			: fields.many2many('sale.order','sale_order_advance_rel','order_id','adv_id',"Sales Order(s)"),
	}