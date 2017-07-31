from openerp.osv import fields, osv

from tools.translate import _

class mrp_bom(osv.Model):
	_inherit = "mrp.bom"
	_columns = {
		"wax" : fields.boolean("Wax",help="Check this field if BoM will use wax in production")
	}