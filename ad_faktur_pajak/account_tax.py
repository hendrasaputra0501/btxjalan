from openerp.osv import fields,osv

class account_tax(osv.Model):
	_inherit = "account.tax"
	_columns = {
		"inside_berikat"		: fields.boolean("Tax for Kawasan Berikat"),
		"reported_unreturned"	: fields.boolean("Reported but not returned",help="Check this fields if this tax is not returned, but will be reported on tax return"),
		"tax_amount_kb"			: fields.float("Tax KB Percentage",),
	}