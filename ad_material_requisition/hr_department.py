from openerp.osv import fields,osv

class hr_department(osv.Model):
	_inherit = "hr.department"
	_columns = {
		"general_location_id" : fields.many2one('stock.location',"Department Stock Location"),
	}

class stock_location(osv.Model):
	_inherit = "stock.location"
	_columns = {
		"department_id" : fields.many2one('hr.department',"Department"),
	}	