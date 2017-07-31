from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc

class loc(osv.osv):
	_inherit = 'letterofcredit'

	def _get_lc_product_lines(self, cr, uid, lines):
		res = []
		for line in lines:
			line_dict = {
				'sale_line_id' : line.sale_line_id and line.sale_line_id.id or False ,
				'product_id': line.product_id and line.product_id.id or False,
				'name': line.name,
				'price_unit': line.price_unit,
				'product_uom_qty': line.product_uom_qty,
				'application' : line.application,
				'other_description' : line.other_description,
				'cone_weight' : line.cone_weight,
				'count_number' : line.count_number,
				'bom_id' : line.bom_id and line.bom_id.id or False,
				'wax' : line.wax,
				'lc_dest' : line.lc_dest and line.lc_dest.id or False,
				'lc_dest_desc' : line.lc_dest_desc,
				'earliest_delivery_date' : line.earliest_delivery_date,
				'est_delivery_date' : line.est_delivery_date,
				'delivery_term_txt' : line.delivery_term_txt,
				'consignee' : line.consignee and line.consignee.id or False,
				'show_consignee_address' : line.show_consignee_address,
				'c_address_text' : line.c_address_text,
				'notify' : line.notify and line.notify.id or False,
				'show_notify_address' : line.show_notify_address,
				'n_address_text' : line.n_address_text,
				'knock_off' : line.knock_off,
				'date_knock_off' : line.date_knock_off,
				'move_lines':False,
			}
			res.append([0,0,line_dict])

		return res

	def action_deactivate(self,cr,uid,ids,context=None):
		if context is None:
			context={}

		if ids:
			original = self.browse(cr, uid, ids[0])
			parent = original.parent_id and original.parent_id or original
			childs = self.search(cr, uid, [('parent_id','=',parent.id)])
			
			next_rev_number = len(childs) + 1
			
			self.write(cr,uid,original.id,{'state':'nonactive'})

			default = {
				'state':'draft',
				'parent_id':parent.id,
				'name':parent and (parent.name + ' Rev. ' + str(next_rev_number)) or '/',
				'prev_revision_id':parent.id==original.id and False or original.id,
				'lc_product_lines':self._get_lc_product_lines(cr, uid, original.lc_product_lines)
			}
			
			cr.execute("SELECT picking_id FROM stock_picking_letterofcredit_rel WHERE lc_id='%s'"%(original.id))
			picking_ids = list(set([x[0] for x in cr.fetchall()]))
			new_lc_id=self.copy(cr,uid,ids[0],default,context)
			pickings = self.pool.get('stock.picking').browse(cr, uid, picking_ids, context=context)
			for picking in pickings:
				lc_ids_to = [new_lc_id]
				for lc in picking.lc_ids:
					if lc.id!=original.id:
						lc_ids_to.append(lc.id)
				self.pool.get('stock.picking').write(cr, uid, picking.id, {'lc_ids':[(6,0,lc_ids_to)]}, context=context)
			data_pool = self.pool.get('ir.model.data')
			action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_letter_of_credit', "action_letterofcredit_2")
			if action_model:
				action_pool = self.pool.get(action_model)
				action = action_pool.read(cr, uid, action_id, context=context)
				action['res_id'] = int(new_lc_id)
		
			return action
		return True

	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		default = default.copy()
		lc = self.browse(cr, uid, id, context=context)
		lines = []
		for line in lc.lc_product_lines:
			line_dic = self.pool.get('letterofcredit.product.line').copy_data(cr, uid, line.id)
			if line_dic.get('move_lines',{}):
				del line_dic['move_lines']
			if line_dic.get('lc_id',{}):
				del line_dic['lc_id']
			lines.append((0,0,line_dic))
		default.update({'lc_product_lines':lines})
		res = super(loc, self).copy(cr, uid, id, default=default, context=context)
		return res

class loc_product_lines(osv.osv):
	_inherit = "letterofcredit.product.line"
	_columns ={
		'move_lines':fields.one2many('stock.move','lc_product_line_id','Inventory Moves'),
	}

	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		default = default.copy()
		default.update({
		'move_lines': False,
		})
		res = super(loc_product_lines, self).copy(cr, uid, id, default=default, context=context)
		return res
		
loc_product_lines()