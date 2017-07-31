from openerp.osv import fields,osv

class stock_picking(osv.Model):
	_inherit = "stock.picking"
	_columns = {
	    'bc_id': fields.many2one('beacukai', 'BC Form', ),
	}

class stock_picking_in(osv.Model):
	_inherit = "stock.picking.in"
	_columns = {
	    'bc_id': fields.many2one('beacukai', 'BC Form', ),
	}

class stock_picking_out(osv.Model):
	_inherit = "stock.picking.out"
	_columns = {
	    'bc_id': fields.many2one('beacukai', 'BC Form', ),
	}