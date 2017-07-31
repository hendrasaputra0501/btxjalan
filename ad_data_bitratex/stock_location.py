from openerp.osv import fields,osv

class stock_location(osv.osv):
	_inherit = "stock.location"
	_defaults = {
	'scrap_location':False,
	}