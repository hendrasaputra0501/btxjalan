from openerp.osv import fields,osv

class res_partner(osv.Model):
	_inherit = "res.partner"

	_columns = {
		"government_tax_partner":fields.boolean("Government",help="Check this field if this partner is government (partner for tax payment)"),
	}

	_defaults = {

		"government_tax_partner":False,
	}