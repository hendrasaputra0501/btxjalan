from openerp.osv import fields,osv
import time

from tools.translate import _


class mrp_move(osv.Model):
	_name = "mrp.move"
	_columns = {
		'name':fields.char('MRP Move Number',size=128, required=True),
		"company_id":fields.many2one("res.company","Company"),
		"move_date":fields.date("Move Date",required=True,),
		"bom_id":fields.many2one("mrp.bom","Bill of Material",required=True, ),
		"product_id":fields.related("bom_id","product_id",string="Product to produce",type="many2one",relation="product.product"),
		"product_qty":fields.float("Produced Qty",required=True, ),
		"uom_id":fields.many2one('product.uom',"Unit of Measure",required=True, ),
		"mrp_location_id":fields.many2one('stock.location',"Production Site",required=True,),
		"location_dest_id":fields.many2one('stock.location',"Finished Goods Site",required=True,),
		"stock_journal_id":fields.many2one('account.journal',"Stock Journal",required=True),
		"cost_journal_id":fields.many2one("account.journal","Production Cost Journal",required=True),
		"mrp_move_line":fields.one2many("mrp.move.line","mrp_move_id","MRP Move Line"),
		"mrp_fg_move_line":fields.one2many("mrp.move.line","mrp_move_id","MRP Finished Move Line"),
		"mrp_cost_line":fields.one2many("mrp.cost.line","mrp_move_id","MRP Cost Line"),
		"picking_id":fields.many2one("stock.picking","Internal Move Created"),
		"stock_move_id":fields.many2one('account.move',"Stock Journal Entries",),
		"cost_move_id":fields.many2one('account.move',"Cost Journal Entries",),
		"state":fields.selection([('draft',"Draft"),('confirm',"Confirmed"),("production","In Production"),("done","Done"),('cancel',"Cancelled")],
			"State",required=True),
	}
	def _get_mrp_location(self,cr,uid,context=None):
		if not context:context={}
		users = self.pool.get("res.users").browse(cr,uid,uid,context)
		location_id = self.pool.get("stock.location").search(cr,uid,[("usage","=",'production')])
		if location_id:
			if isinstance(location_id,(tuple,list)):
				return location_id[0]
			else:
				return location_id
		return False

	def _get_fg_location(self,cr,uid,context=None):
		if not context:context={}
		users = self.pool.get("res.users").browse(cr,uid,uid,context)
		location_id = self.pool.get("stock.location").search(cr,uid,[('company_id',"=",users.company_id.id),("usage","=",'internal'),('chained_picking_type','=',False)])
		if location_id:
			if isinstance(location_id,(tuple,list)):
				return location_id[0]
			else:
				return location_id
		return False

	_defaults = {
		"company_id":lambda self,cr,uid,context: self.pool.get("res.users").browse(cr,uid,uid,context).company_id.id,
		'move_date': lambda *a: time.strftime('%Y-%m-%d'),
		'state':lambda *a : 'draft',
		'name':lambda *a : '/DRAFT',
		"mrp_location_id":_get_mrp_location,
		"location_dest_id":_get_fg_location,

	}

	def action_confirm(self,cr,uid,ids,context=None):
		if not context:context={}
		pick_pool =self.pool.get("stock.picking")
		for mrp_move in self.browse(cr,uid,ids,context):
			move_lines = []
			picking = {
			"name":'/Draft',
			"move_type":'direct',
			"company_id":mrp_move.company_id and mrp_move.company_id.id or False,
			"date":time.strftime('%Y-%m-%d'),
			"type":'internal',
			"move_lines":False,
			"state":"draft"
			}
			for line in mrp_move.mrp_move_line:
				lines = {
					"name"			: line.product_id and line.product_id.name or False,
					"product_id"	: line.product_id and line.product_id.id or False,
					"product_qty"	: line.product_id and line.product_qty or False,
					"product_uom"	: line.uom_id and line.uom_id.id or False,
					"date"			: time.strftime('%Y-%m-%d %H:%M:%S'),
					"date_expected" : time.strftime('%Y-%m-%d %H:%M:%S'),
					"partner_id"	: mrp_move.company_id and mrp_move.company_id.id or False,
					"location_id"	: line.source_location_id and line.source_location_id.id or False,
					"location_dest_id" : mrp_move.mrp_location_id and mrp_move.mrp_location_id.id or False, 
					}
				move_lines.append((0,0,lines))
			picking.update({"move_lines":move_lines})
			pick_id = pick_pool.create(cr,uid,picking,context)
			self.write(cr,uid,mrp_move.id,{"picking_id":pick_id},context)
		return True

	def onchange_bom_id(self,cr,uid,ids,bom_id,product_qty,context=None):
		value={
			'product_id':False,
			"product_qty":False,
			"uom_id":False,
			"mrp_move_line":False,
			"mrp_fg_move_line":False,
			}
		if not context:context={}
		if bom_id:
			bom = self.pool.get("mrp.bom").browse(cr,uid,bom_id,context)
			print "------------",bom.product_id.name,bom.product_id.id
			value.update({
				'product_id':(bom.product_id and bom.product_id.id,bom.product_id and bom.product_id.name) or False,
				"product_qty": product_qty and product_qty > 0.0 and product_qty or bom.product_qty or 0.0,
				"uom_id":bom.product_uom and bom.product_uom.id or False,
				"mrp_move_line":False,
				"mrp_fg_move_line":False,
				})
			mrp_move_line=[]
			mrp_fg_move_line=[]
			qty=0.0
			for item in bom.bom_lines:
				qty=((product_qty and product_qty > 0.0 and product_qty or bom.product_qty) * item.product_qty/bom.product_qty) or 0.0
				mrp_move_line.append({
					'name':item.product_id and item.product_id.name or '/',
					"product_id":item.product_id and item.product_id.id or False,
					'product_qty': qty,
					'uom_id':item.product_uom and item.product_uom.id or False,
					'unit_price':item.product_id.standard_price or 0.0,
					'subtotal':qty * item.product_id.standard_price or 0.0
					})
			qty1=0.0
			for item in bom.sub_products:
				qty1=((product_qty and product_qty > 0.0 and product_qty or bom.product_qty) * item.product_qty/bom.product_qty) or 0.0
				mrp_fg_move_line.append({
					'name':item.product_id and item.product_id.name or '/',
					"product_id":item.product_id and item.product_id.id or False,
					'product_qty': qty1,
					'uom_id':item.product_uom and item.product_uom.id or False,
					'unit_price':item.product_id.standard_price or 0.0,
					'subtotal':qty1 * item.product_id.standard_price or 0.0
					})
			value.update({'mrp_move_line':mrp_move_line,'mrp_fg_move_line':mrp_fg_move_line})
		return {'value':value}

class mrp_move_line(osv.Model):
	_name = 'mrp.move.line'

	def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
		res = dict.fromkeys(ids, 0.0)
		for line in self.browse(cr, uid, ids, context=context):
			res[line.id] = (line.product_qty*line.unit_price) or 0.0
		return res

	_columns = {
		"name":fields.char('Description',size=128, required=True),
		"mrp_move_id":fields.many2one("mrp.move","MRP Move",ondelete="cascade",required=True),
		"product_id":fields.many2one("product.product","Product",required=True),
		"source_location_id":fields.many2one("stock.location","Source Location",required=True),
		"product_qty":fields.float("Qty",required=True, ),
		"uom_id":fields.many2one('product.uom',"Unit of Measure",required=True, ),
		"second_product_qty":fields.float("2nd Qty (2nd Uom)",required=True, ),
		"second_uom_id":fields.many2one('product.uom',"Unit of Measure (2nd Uom)",required=True, ),
		"unit_price":fields.float("Unit Price",required=True, ),
		"subtotal":fields.function(_get_subtotal,type="float",string="Subtotal"),
	}

class mrp_cost_line(osv.Model):
	_name="mrp.cost.line"
	_columns = {
	    "name":fields.char("Description",size=128, required=True, ),
	    "mrp_move_id":fields.many2one("mrp.move","MRP Move",ondelete="cascade",required=True),
	    "account_id":fields.many2one("account.account","Account",required=True,),
	    "amount":fields.float("Amount"),
	}