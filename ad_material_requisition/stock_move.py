from openerp.osv import fields,osv

class stock_move(osv.Model):
	_inherit = "stock.move"
	_columns = {
		"reason_code"			: fields.many2one('product.reason.code',"Reason Code",required=False),
		"material_type"			: fields.many2one('product.material.type',"Material Type"),
	}
	_order = 'id'
