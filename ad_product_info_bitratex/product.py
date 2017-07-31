from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
import ast

class product_origin(osv.Model):
	_name = "product.origin"
	_columns = {
		"name":fields.char("Origin Name",size=128,required=True, ),
		"country":fields.many2one('res.country','Country',),
	}

class product_specification(osv.Model):
	_name = "product.specification"
	_columns = {
		"name":fields.char("Specification Name",size=128,required=True, ),
		"description":fields.text('Description'),
	}

class product_product(osv.Model):
	_inherit = "product.product"

	def get_product_available(self, cr, uid, ids, context=None):
		""" Finds whether product is available or not in particular warehouse.
		@return: Dictionary of values
		"""
		if context is None:
			context = {}

		location_obj = self.pool.get('stock.location')
		warehouse_obj = self.pool.get('stock.warehouse')
		shop_obj = self.pool.get('sale.shop')
		
		states = context.get('states',[])
		what = context.get('what',())
		if not ids:
			ids = self.search(cr, uid, [])
		res = {}.fromkeys(ids, 0.0)
		if not ids:
			return res

		if context.get('shop', False):
			warehouse_id = shop_obj.read(cr, uid, int(context['shop']), ['warehouse_id'])['warehouse_id'][0]
			if warehouse_id:
				context['warehouse'] = warehouse_id

		if context.get('warehouse', False):
			lot_id = warehouse_obj.read(cr, uid, int(context['warehouse']), ['lot_stock_id'])['lot_stock_id'][0]
			if lot_id:
				context['location'] = lot_id

		if context.get('location', False):
			if type(context['location']) == type(1):
				location_ids = [context['location']]
			elif type(context['location']) in (type(''), type(u'')):
				location_ids = location_obj.search(cr, uid, [('name','ilike',context['location'])], context=context)
			else:
				location_ids = context['location']
		else:
			location_ids = []
			wids = warehouse_obj.search(cr, uid, [], context=context)
			if not wids:
				return res
			for w in warehouse_obj.browse(cr, uid, wids, context=context):
				location_ids.append(w.lot_stock_id.id)

		# build the list of ids of children of the location given by id
		if context.get('compute_child',True):
			child_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', location_ids)])
			location_ids = child_location_ids or location_ids
		
		# this will be a dictionary of the product UoM by product id
		product2uom = {}
		uom_ids = []

		if 'in' in what or 'out' in what:
			for product in self.read(cr, uid, ids, ['uom_id'], context=context):
				product2uom[product['id']] = product['uom_id'][0]
				uom_ids.append(product['uom_id'][0])
			# this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id
		if 'uop_enter' in what or 'uop_exit' in what:
			for product in self.read(cr, uid, ids, ['uop_id'], context=context):
				product2uom[product['id']] = product['uop_id'][0]
				uom_ids.append(product['uop_id'][0])
			# this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id


		uoms_o = {}
		for uom in self.pool.get('product.uom').browse(cr, uid, uom_ids, context=context):
			uoms_o[uom.id] = uom

		results = []
		results2 = []

		from_date = context.get('from_date',False)
		to_date = context.get('to_date',False)
		date_str = False
		date_values = False
		where = [tuple(location_ids),tuple(location_ids),tuple(ids),tuple(states)]
		if from_date and to_date:
			date_str = "date>=%s and date<=%s"
			where.append(tuple([from_date]))
			where.append(tuple([to_date]))
		elif from_date:
			date_str = "date>=%s"
			date_values = [from_date]
		elif to_date:
			date_str = "date<=%s"
			date_values = [to_date]
		if date_values:
			where.append(tuple(date_values))

		prodlot_id = context.get('prodlot_id', False)
		prodlot_clause = ''
		if prodlot_id:
			prodlot_clause = ' and prodlot_id = %s '
			where += [prodlot_id]

		# TODO: perhaps merge in one query.
		if 'in' in what:
			# all moves from a location out of the set to a location in the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id NOT IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where))
			results = cr.fetchall()
		if 'out' in what:
			# all moves from a location in the set to a location out of the set
			cr.execute(
				'select sum(product_qty), product_id, product_uom '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id NOT IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uom',tuple(where))
			results2 = cr.fetchall()
		
		if 'uop_enter' in what:
			cr.execute(
				'select sum(product_uop_qty), product_id, product_uop '\
				'from stock_move '\
				'where location_id NOT IN %s '\
				'and location_dest_id IN %s '\
				'and product_id IN %s '\
				'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
				+ prodlot_clause + 
				'group by product_id,product_uop',tuple(where))
			results3 = cr.fetchall()
		if 'uop_exit' in what:
			cr.execute(
				'select sum(product_uop_qty), product_id, product_uop '\
				'from stock_move '\
				'where location_id IN %s '\
				'and location_dest_id NOT IN %s '\
				'and product_id  IN %s '\
				'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
				+ prodlot_clause + 
				'group by product_id,product_uop',tuple(where))
			results4 = cr.fetchall()

		# Get the missing UoM resources
		uom_obj = self.pool.get('product.uom')
		if 'in' in what or 'out' in what:
			uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2)
			if context.get('uom', False):
				uoms += [context['uom']]
			uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
			if uoms:
				uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
				for o in uoms:
					uoms_o[o.id] = o
		
		if 'uop_enter' in what or 'uop_exit' in what:
			uoms = map(lambda x: x[2], results3) + map(lambda x: x[2], results4)
			#print "---------",results3
			if context.get('uom', False):
				uoms += [context['uom']]
			uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
			if uoms:
				uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
				for o in uoms:
					uoms_o[o.id] = o

		#TOCHECK: before change uom of product, stock move line are in old uom.
		context.update({'raise-exception': False})
		# Count the incoming quantities
		if 'in' in what or 'out' in what:
			for amount, prod_id, prod_uom in results:
				amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
						 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
				res[prod_id] += amount
			# Count the outgoing quantities
			for amount, prod_id, prod_uom in results2:
				amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
						uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
				res[prod_id] -= amount
		if 'uop_enter' in what or 'uop_exit' in what:
			for amount, prod_id, prod_uom in results3:
				amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
						 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
				res[prod_id] += amount
			# Count the outgoing quantities
			for amount, prod_id, prod_uom in results4:
				amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
						uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
				res[prod_id] -= amount
		return res

	def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
		""" Finds the incoming and outgoing quantity of product.
		@return: Dictionary of values
		"""
		if not field_names:
			field_names = []
		if context is None:
			context = {}
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0.0)
		for f in field_names:
			c = context.copy()
			if f == 'qty_available':
				c.update({ 'states': ('done',), 'what': ('in', 'out') })
			if f == 'virtual_available':
				c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
			if f == 'incoming_qty':
				c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
			if f == 'outgoing_qty':
				c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
			if f == 'qty_uop_available':
				c.update({ 'states': ('done',), 'what': ('uop_enter', 'uop_exit') })
			if f == 'virtual_uop_available':
				c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('uop_enter', 'uop_exit') })
			stock = self.get_product_available(cr, uid, ids, context=c)
			for id in ids:
				res[id][f] = stock.get(id, 0.0)
		return res
	def _get_id_record(self, cr, uid, ids, field_names=None, arg=False, context=None):
		res={}
		for xid in self.browse(cr,uid,ids,context):
			res[xid.id]=xid.id
		return res
	_columns = {
		"edit_state" :fields.selection([('writeable','Writeable'),('unwriteable','Unwriteable')],"Editable State",required=True),
		"old_code"	: fields.char("Old Code",size=128),
		"nomenclature":fields.char("Nomenclature",size=50),
		"function_id":fields.function(_get_id_record,type="integer"),
		"local_desc":fields.text("Local Description"),
		"export_desc":fields.text("Export Description"),
		"product_group":fields.many2one('product.product',"Product Group",),
		"internal_type":fields.selection([
			('Finish',"Finished Goods"),
			('Finish_others',"Finished Good Others"),
			('Raw Material',"Raw Material"),
			('Stores',"Stores"),
			('Waste',"Waste"),
			('Scrap',"Scrap"),
			('Fixed','Fixed Assets'),
			('Packing','Packing Material'),
			],
			"Internal Type",required=False),
		"rm_class_id": fields.many2one('product.rm.type.category',"Raw Material Type"),
		"indentable"	: fields.boolean("Indentable"),
		"use_min_stock"	: fields.boolean("Use minimum stock"),
		"count":fields.float("Count",),
		"blend_code" : fields.many2one('mrp.blend.code','Blend Code'),
		"blend_id":fields.many2one("mrp.bom","Blend (BoM)"),
		"wax":fields.selection([('none','None'),('waxed',"Waxed"),('unwaxed',"Unwaxed")],"Wax",help="Select wax if this product is using wax"),
		"blend_lines":fields.related("blend_id","bom_lines",string="Components",type='one2many', relation='mrp.bom'),
		"application":fields.selection([('knitting',"Knitting"),('weaving',"Weaving")],"Application Purpose"),
		"sd_type":fields.selection([('1','Single'),('2','Double'),('3','Triple')],"Single/Double"),
		"specification": fields.many2one("product.specification","Product Specification"),
		"origin": fields.many2one("product.origin","Origin"),
		# "manufacturer_pcatalogue":fields.char("Manufacture Catalogue Number",size=64),
		"uop_id":fields.many2one("product.uom","Unit of Picking",required=True, ),
		"uop_coeff":fields.float("Unit of Picking Coeff.",required=True, ),
		'qty_available': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Quantity On Hand',
			help="Current quantity of products.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods stored at this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods stored in the Stock Location of this Warehouse, or any "
				 "of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "stored in the Stock Location of the Warehouse of this Shop, "
				 "or any of its children.\n"
				 "Otherwise, this includes goods stored in any Stock Location "
				 "with 'internal' type."),
		'virtual_available': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Forecasted Quantity',
			help="Forecast quantity (computed as Quantity On Hand "
				 "- Outgoing + Incoming)\n"
				 "In a context with a single Stock Location, this includes "
				 "goods stored in this location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods stored in the Stock Location of this Warehouse, or any "
				 "of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "stored in the Stock Location of the Warehouse of this Shop, "
				 "or any of its children.\n"
				 "Otherwise, this includes goods stored in any Stock Location "
				 "with 'internal' type."),
		'incoming_qty': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Incoming',
			help="Quantity of products that are planned to arrive.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods arriving to this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods arriving to the Stock Location of this Warehouse, or "
				 "any of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "arriving to the Stock Location of the Warehouse of this "
				 "Shop, or any of its children.\n"
				 "Otherwise, this includes goods arriving to any Stock "
				 "Location with 'internal' type."),
		'outgoing_qty': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Outgoing',
			help="Quantity of products that are planned to leave.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods leaving this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods leaving the Stock Location of this Warehouse, or "
				 "any of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "leaving the Stock Location of the Warehouse of this "
				 "Shop, or any of its children.\n"
				 "Otherwise, this includes goods leaving any Stock "
				 "Location with 'internal' type."),
		"qty_uop_available": fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Quantity on Hand (UoP)'),
		"virtual_uop_available":fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Forecasted Quantity (UoP)'),
		"specification_lines": fields.one2many("product.product.spec","product_id","Product Specifications"),
		}

	def _get_uom_id(self, cr, uid, *args):
		cr.execute("select id from product_uom where name='KGS' order by id limit 1")
		res = cr.fetchone()
		return res and res[0] or False

	_defaults = {
		'edit_state':'writeable',
		# 'internal_type': lambda *a:'Stores',
		'uop_id': _get_uom_id,
		'uop_coeff':lambda *a:1.0,
		'function_id':0,
		'nomenclature':lambda *a:'Ne',
		'uom_id':_get_uom_id,
		'uom_po_id':_get_uom_id,
	}
	
	def set_writeable(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'edit_state':'writeable'})

	def set_unwriteable(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'edit_state':'unwriteable'})

	def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):
		res = super(product_product, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

		
		if view_type == 'form':
			# Set all fields read only when state is close.
			doc = etree.XML(res['arch'])
			for node in doc.xpath("//field"):
				attrs_original = eval(node.get('attrs',str(False)))
				attrs_readonly = attrs_original and attrs_original.get('readonly',False) or False
				if (attrs_original and not attrs_readonly) or not attrs_original:
					attrs_readonly = []
					attrs_readonly.append(('edit_state', '=', 'unwriteable'))
				else:
					attrs_readonly.append("|")
					attrs_readonly.append(('edit_state', '=', 'unwriteable'))
					attrs_readonly=attrs_readonly
				if not attrs_original:
					attrs_original={}
				attrs_original.update({'readonly':attrs_readonly})
				node.set('attrs', str(attrs_original))
				node_name = node.get('name')
				setup_modifiers(node, res['fields'][node_name])
			res['arch'] = etree.tostring(doc)

		return res

	def write(self, cr, uid, ids, vals, context={}):
		if not context:context={}
		try:
			product=self.browse(cr,uid,ids,context=context)[0]
		except:
			product=self.browse(cr,uid,ids,context=context)
		if product.edit_state=='writeable':
			vals.update({'edit_state':'unwriteable'})
		res=super(product_product, self).write(cr, uid, ids, vals, context)
		return res

	def onchange_blend_id(self,cr,uid,ids,blend_id,context=None):
		if not context:context={}
		value={}
		if not blend_id:
			value.update({'blend_lines':False})
		else:
			blend = self.pool.get('mrp.bom').browse(cr,uid,blend_id,context)
			blend_lines = [(1,bline.id,{'product_id':bline.product_id.id or False,'sequence':bline.sequence or False,'name':bline.name or False,'product_qty':bline.product_qty or 0.0,'product_uom':bline.product_uom.id or False,'code':bline.code or False,'type':bline.type or False,'method':bline.method or False,'routing_id':bline.routing_id.id or False,'date_start':bline.date_start or False,'date_stop':bline.date_stop or False}) for bline in blend.bom_lines]
			value.update({'blend_lines':blend_lines})
		return{'value':value}

	def onchange_set_desc(self,cr,uid,ids,default_code,name,internal_type,application,sd_type,count,wax,blend_code_id,blend_id,context=None):
		if not context:
			context={}
		local_desc=''
		export_desc=''
		code=''
		blend_code=''
		count_code=''
		sd_type_code=''
		wax_code=''
		domain=[]
		blend_desc = ''

		if not name:
			name=''
		if internal_type=='Finish':
			if count:
				#local_desc = local_desc + str(count)
				#export_desc = export_desc + str(count)
				count_code=str(count)
			if sd_type=='1':
				#local_desc+='/1 '
				#export_desc+='/1 '
				sd_type_code='1'
			elif sd_type=='2':
				#local_desc+='/2 '
				#export_desc+='/2 '
				sd_type_code='2'
			elif sd_type=='3':
				#local_desc+='/2 '
				#export_desc+='/2 '
				sd_type_code='3'

			if blend_code_id:
				blend_code_obj=self.pool.get('mrp.blend.code').browse(cr,uid,blend_code_id)
				blend_code=blend_code_obj.name
				blend_desc = blend_code_obj.desc or ''
				local_desc = local_desc+blend_desc
				export_desc = export_desc+blend_desc
			# if blend_id:
			# 	blend=self.pool.get('mrp.bom').browse(cr,uid,blend_id)
			# 	local_desc+=blend_code+' '
			# 	for line in blend.bom_lines:
			# 		export_desc = export_desc + ' '+ line.product_id.name + '('
			# 		if line.comp_percentage:
			# 			export_desc = export_desc + str(line.comp_percentage) + ' %) '
			# 		else:
			# 			export_desc = export_desc + '0 %) '
			if wax=='waxed':
				# local_desc = local_desc + ' waxed '
				# export_desc = export_desc+ ' waxed '
				wax_code='W'
			elif wax=='unwaxed':
				# local_desc = local_desc + ' unwaxed '
				# export_desc = export_desc + ' unwaxed '
				wax_code='U'
			elif wax=='none':
				# local_desc = local_desc + ' '
				# export_desc = export_desc + ' '
				wax_code=''

			if application=='knitting':
				local_desc = local_desc + 'to knitting'
				export_desc = export_desc + 'to knitting'
			elif application=='weaving':
				local_desc = local_desc + 'to weaving'
				export_desc = export_desc + 'to weaving'

			code=blend_code+count_code+sd_type_code+wax_code
		else:
			if default_code:
				# local_desc+='['+(default_code or '')+'] '+name
				# export_desc+='['+(default_code or '')+'] '+name
				local_desc+=name
				export_desc+=name
				code=default_code
			else:
				local_desc+=name
				export_desc+=name
		res = {'local_desc':local_desc.upper(),'export_desc':export_desc.upper(),'default_code':code}
		if internal_type in ('Stores', 'Packing', 'Raw Material'):
			res.update({'cost_method':'fifo'})
			res.update({'valuation':'real_time'})
		else:
			res.update({'cost_method':'standard'})
			res.update({'valuation':'manual_periodic'})
		
		return {'value':res}

class product_packing_type(osv.osv):
	_name = "product.packing.type"
	_columns = {
		'name':fields.char('Name',required=True),
	}


class product_uom(osv.osv):
	"""docstring for Product UOM"""
	
	_inherit = "product.uom"
	_columns = {
		"uom_alias" : fields.char('Alias', size=128, help="This is can be use for reporting purpose"),
		"net_weight" : fields.float('Net Weight',digits=(1, 3)),
		"gross_weight" : fields.float('Gross Weight Sigle',digits=(1, 3)),
		"gross_weight_double" : fields.float('Gross Weight Double',digits=(1, 3)),
		"cone_weight" : fields.float('Cone Weight',digits=(1, 3)),
		"cones" : fields.integer('Cones'),
		"conicity" : fields.char('Conicity', size=128),
		"dimension" : fields.char('Dimension/Size', size=128),
		"width"	: fields.char('Width',size=128),
		"height" : fields.char('Height',size=128),
		"length" : fields.char('Length',size=128),
		"is_package_unit" : fields.boolean('Is Package Unit?'),
		'packing_type' : fields.many2one('product.packing.type','Packing',help='Packing Type on Negotiation'),
		# 'packing_type' : fields.selection([('bag','BAGS'),('pallet','PALLETS'),('carton','CARTONS')],string="Packing Type"),
		'dimension_uom': fields.many2one('product.uom','Dimension Uom',help='Dimension Uom'),
	}

	def name_get(self, cr, uid, ids, context=None):
		if isinstance(ids, (list, tuple)) and not len(ids):
			return []
		if isinstance(ids, (long, int)):
			ids = [ids]
		reads = self.read(cr, uid, ids, ['name','is_package_unit','net_weight','cone_weight','cones','length','height','width'], context=context)
		res = []
		for record in reads:
			name = record['name']
			if record['is_package_unit']:
				name+='/'+str(record['net_weight'] or 'none')+'/'+str(record['cone_weight'] or 'none')+'/'+str(record['cones'] or '')+'/'+((record['length'] and record['length']+'L' or '') or 'none')+'x'+((record['width'] and record['width']+'W' or '') or 'none')+'x'+((record['height'] and record['height']+'H' or '') or 'none')
			res.append((record['id'], name))
		return res

class product_product_spec(osv.Model):
	_name = "product.product.spec"
	_columns  = {
		"product_id": fields.many2one("product.product","Product ID",required=True),
		"spec_id"	: fields.many2one("product.specifications","Specification"),
		"name"		: fields.char("Specification Name",required=True),
		"sequence"	: fields.integer("Sequence",required=True),
	}
	_order="sequence asc"

	def onchange_spec_id(self,cr,uid,ids,spec_id,context=None):
		if not context:context={}
		value={'sequence':False}
		if spec_id:
			specs = self.pool.get('product.specifications').browse(cr,uid,spec_id)
			value.update({
				"sequence":specs.sequence
				})
		return {'value':value}
		
class product_specifications(osv.Model):
	_name="product.specifications"
	_columns = {
		"name"			: fields.char("Specification",required=True),
		"description"	: fields.text("Description"),
		"sequence"		: fields.integer("Sequence",required=True),
	}
	def get_sequence(self,cr,uid,context=None):
		if not context:context={}
		max_ids = self.pool.get("product.specifications").search(cr,uid,[],order="sequence desc",limit=1)
		next=1
		if max_ids:
			max_ids = self.pool.get("product.specifications").browse(cr,uid,max_ids)
			try:
				next=max_ids.sequence+1
			except:
				next=max_ids[0].sequence+1
		return next

	_defaults = {
		"sequence": get_sequence
	}
	_order="sequence desc"