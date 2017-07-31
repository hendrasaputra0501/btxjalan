from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
from datetime import datetime

class stock_move_composition(osv.Model):
	_name = "stock.move.composition"
	_columns = {
		"move_id" : fields.many2one("stock.move","Move ID", readonly=True, states={'draft':[('readonly',False)]}),
		"date"	: fields.datetime("Date", required=True, readonly=True, states={'draft':[('readonly',False)]}),
		# "rm_type_id" : fields.many2one("product.rm.type","Raw Material",required=True),
		"rm_category_id": fields.many2one("product.rm.type.category","RM Category", required=True, readonly=True, states={'draft':[('readonly',False)]}),
		"product_uom" : fields.many2one("product.uom", "Unit of Measure", required=True, readonly=True, states={'draft':[('readonly',False)]}),
		"product_qty" : fields.float("Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
		"location_id" : fields.many2one("stock.location","Source Location",required=True, domain="[('usage','!=','view')]", readonly=True, states={'draft':[('readonly',False)]}),
		"location_dest_id" : fields.many2one("stock.location","Destination Location",required=True, domain="[('usage','!=','view')]", readonly=True, states={'draft':[('readonly',False)]}),
		"state"	: fields.selection([('draft','Draft'),('done','Done')], "Status", required=True),
	}

	_defaults = {
		"state" : lambda *s: 'draft',
		"date" : lambda *d: datetime.now().strftime('%Y-%m-%d 12:00:00'),
	}

	_order = "date desc, id asc"

	# def onchange_rm_type(self, cr, uid, ids, rm_type_id, context=None):
	# 	res = {
	# 		'rm_category_id' : False,
	# 		'product_uom' : False,
	# 	}
	# 	if rm_type_id:
	# 		rm_type = self.pool.get('product.rm.type').browse(cr, uid, rm_type_id)
	# 		res['rm_category_id'] = rm_type.category_id and rm_type.category_id.id or False
	# 		res['product_uom'] = rm_type.category_id and rm_type.category_id.uom_id and rm_type.category_id.uom_id.id or False
	# 	return {'value':res}