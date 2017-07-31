from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class packing_product_detail(osv.osv):
	"""docstring for Container Detail on Shipping Instruction"""
	
	_name = "packing.product.detail"
	_columns = {
		"container_book_id" : fields.many2one('container.booking', 'Shipping Instruction', readonly=False),
		"product_id" : fields.many2one('product.product','Product'),
		
		"net_weight_per_cone" : fields.float('Net Weight Per Cone'),
		# "net_uom" : fields.many2one('product.uom', 'Net UoM'),
		"gross_weight_per_cone" : fields.float('Gross Weight Per Cone'),
		# "net_uom" : fields.many2one('product.uom', 'Gross UoM'),
		"total_cone" : fields.float('Number of Cones'),

		# "packing_type" : fields.many2one('packing.type','Packing',help='Packing Type on Negotiation'),
		"package_net_weight" : fields.float('Package Net Weight'),
		"package_gross_weight" : fields.float('Package Gross Weight'),
		"total_package" : fields.float('Package Total'),

		"pack_id" : fields.many2one('stock.tracking', 'Pack'),
		"product_uop" : fields.many2one('product.uom', 'Packing Standard'),
		
		'packing_type':fields.selection([
            ('bag','BAG'),
            ('pallet','PALLET'),
            ('carton','CARTON'),

        ],'Packing Type'),

	}
