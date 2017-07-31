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

class transport_container(osv.osv):
	"""docstring for transport_container"""
	_name = "stock.transporter"
	_columns = {
		"name" : fields.char('Name',size=200, required=True),
		"account_id" : fields.many2one('account.account', 'Expense Account', required=False),
		"partner_id" : fields.many2one('res.partner','Transport Company', required=True),
		"note" : fields.text('Additional Information'),
		"type" : fields.selection([('trucking','Trucking'),('container','Container')],'Transporter Type', required=True),
		"charge_ids" : fields.one2many('stock.transporter.charge','transporter_id','Fee Charge'),
		"charge_type" : fields.selection([('sale','Sale'),('purchase','Purchase'),('internal','Internal Move')],'Internal Type'),
		"sale_type" : fields.selection([('local','Local'),('export','Export')],'Sale Type'),
		"purchase_type" : fields.selection([('local','Local'),('import','Import')],'Purchase Type'),
		"truck_ids" : fields.one2many('stock.transporter.truck','transporter_id','Truck Type(s)'),
	}

transport_container()

class transport_charge(osv.osv):
	"""docstring for transport_charge"""
	_name = "stock.transporter.charge"
	_columns = {
		"transporter_id" : fields.many2one('stock.transporter','Transport Company'),
		"name" : fields.char('Code',size=200, required=True),
		"country_id" : fields.many2one('res.country','Destination Country',required=True),
		"port_id" : fields.many2one('res.port','Destination Port'),
		"state_id" : fields.many2one('res.country.state','Destination State/City'),
		"cost_type" : fields.selection([('type1','Per Weight'),('type2','Per Delivery')],'Cost Type'),
		# "size" : fields.selection([("20'","20'"),("40'","40'"),("40' HC","40' HC"),("LCL","LCL")], string='Size Container', required=False),
		"size_container" : fields.many2one('container.type','Size'),
		"uom_id" : fields.many2one('product.uom','UoM', required=False),
		"currency_id" : fields.many2one('res.currency','Currency',required=True),
		"cost" : fields.float('Cost',required=True, digits_compute= dp.get_precision('Account')),
		"incoterm" : fields.many2one('stock.incoterms','Incoterm'),
		"date_from" : fields.date("Valid from"),
		"date_to" : fields.date("Valid to"),
		"is_lift_on_lift_off" : fields.boolean("Is Lift on Lift Off?"),
		"use_minimum_qty_rule" : fields.boolean("Use Minimum Quantity Rule"),
		"min_uom_qty" : fields.float('Minimum Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
		"dispensation_cost" : fields.float('Dispensation Cost', digits_compute=dp.get_precision('Account')),
	}

	_defaults = {
		'cost_type' : lambda *a: 'type2',
		'transporter_id' : lambda self,cr,uid,context=None:context.get('transporter_id',False)
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['name','date_from','date_to'], context)
		res = []
		for record in reads:
			charge_code = record['name']
			charge_date_valid_from = record.get('date_from',False)
			charge_date_valid_to = record.get('date_to',False)
			name = charge_date_valid_from and charge_code + " (" + datetime.strptime(charge_date_valid_from,"%Y-%m-%d").strftime("%d/%m/%Y") or charge_code
			name = charge_date_valid_to and name + " - " + datetime.strptime(charge_date_valid_to,"%Y-%m-%d").strftime("%d/%m/%Y") + ")" or name + ")"
			res.append((record['id'], name))
		return res

transport_charge()

class container_size(osv.osv):
	_name = "container.size"
	_columns = {
		"name" : fields.char('Size', size=128, required=True),
		"desc" : fields.text('Description'),
		'teus' : fields.float('TEUS.', help="Container Type Code Bitratex"),
		# "size" : fields.selection([("20'","20'"),("40'","40'"),("40' HC","40' HC"),("LCL","LCL")], string='Size Container', required=True),
		"type" : fields.many2one('container.type','Size Container'),
		"total_container" : fields.integer('Total', required=True),
		"alias": fields.char("Alias",size=6),
	}
	_defaults = {
		# "size" : "40'",
		"total_container" : 1,
	}
container_size()

class container_type(osv.osv):
	_name = "container.type"
	_columns = {
		"name" : fields.selection([("20'","20'"),("40'","40'"),("40' HC","40' HC"),("LCL","LCL")], string='Size Container', required=True),
		"est_weight_per_container" : fields.float('Estimated Weight', required=True),
		"uom_id" : fields.many2one('product.uom','UoM Weight', required=True),
	}
	_defaults = {
		"name" : "40'",
		"est_weight_per_container" : 0.0,
	}
container_type()

class driver(osv.osv):
	_name = "driver"
	_columns = {
		"name" : fields.char('Driver', size=320, required=True),
		"id_card" : fields.char('ID Card', size=320, required=True),
	}
driver()

class stock_transporter_truck(osv.osv):
	_name = "stock.transporter.truck"
	_columns = {
		"transporter_id" : fields.many2one('stock.transporter','Transport Vendor'),
		"name" : fields.char('Type Truck', size=320, required=True),
		"min_uom_qty" : fields.float('Minimum Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),required=True),
		"uom_id" : fields.many2one('product.uom','UoM', required=True),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['name','min_uom_qty','uom_id'], context)
		res = []
		for record in reads:
			name = record['name']
			if record.get('uom_id',False):
				min_uom_qty = record.get('min_uom_qty',0.0)
				uom = self.pool.get('product.uom').browse(cr, uid, record.get('uom_id',False)[0])
				uom_name = uom and uom.name or ' '
				name = name + '( Min. Qty ' + str(min_uom_qty) + ' ' + uom_name + ')'
			res.append((record['id'], name))
		return res
stock_transporter_truck()

class stock_porters(osv.osv):
	_name = "stock.porters"
	_columns = {
		"name" : fields.many2one('res.partner','Porters Company', required=True),
		"account_id" : fields.many2one('account.account', 'Expense Account', required=False),
		"note" : fields.text('Additional Information'),
		"charge_ids" : fields.one2many('stock.porters.charge','porters_id','Fee Charge'), 
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['name'], context)
		res = []
		for record in reads:
			partner_id = record['name'][0]
			name = self.pool.get('res.partner').browse(cr, uid, partner_id).name
			res.append((record['id'], name))
		return res

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		args = args or []
		ids = []
		if name:
			ids = self.search(cr, uid, [('name.name', '=', name)] + args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, uid, [('name.name', operator, name)] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)

stock_porters()

class stock_porters_charge(osv.osv):
	_name = "stock.porters.charge"
	_columns = {
		"porters_id" : fields.many2one('stock.porters','Porters'),
		"name" : fields.char('Code',size=200, required=True),
		# "country_id" : fields.many2one('res.country','Destination Country',required=True),
		# "port_id" : fields.many2one('res.port','Destination Port'),
		# "state_id" : fields.many2one('res.country.state','Destination State/City'),
		# "size" : fields.char('Size',size=20, required=True),
		"quantity" : fields.float('Quantity',required=True, digits_compute= dp.get_precision('Account')),
		"uom_id" : fields.many2one('product.uom','UoP',required=True),
		"cost" : fields.float('Cost',required=True, digits_compute= dp.get_precision('Account')),
		"currency_id" : fields.many2one('res.currency','Currency',required=True),
		"date_from" : fields.date("Valid from"),
		"date_to" : fields.date("Valid to"),
	}

	_defaults = {
		'porters_id' : lambda self,cr,uid,context=None:context.get('porters_id',False)
	}

stock_porters_charge()
