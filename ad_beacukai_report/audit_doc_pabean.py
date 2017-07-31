from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _

class audit_doc_pabean(osv.Model):
	_name = "audit.doc.pabean"
	
	_columns = {
		'name' : fields.char('Description', size=200, required=True),
	}