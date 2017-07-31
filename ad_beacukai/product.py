from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
import ast

class product_uom(osv.osv):
	"""docstring for Product UOM"""
	
	_inherit = "product.uom"
	_columns = {
		"ceisa_tpb_uom_alias" : fields.char('Alias for Ceisa TBP Beacukai', size=128),
	}


class product_product(osv.osv):
	_inherit = "product.product"
	_columns = {
		'bc_remarks' : fields.selection([('bc','BC'),('nonbc','Non BC')],'BC Remarks')
	}
	_defaults = {
		'bc_remarks' : 'bc',
	}