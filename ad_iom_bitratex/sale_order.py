from openerp.osv import fields,osv

class sale_order_line(osv.osv):
	_inherit = "sale.order.line"
	_columns = {
		"iom_line_id": fields.many2one("iom.request.line","IOM Line")
	}