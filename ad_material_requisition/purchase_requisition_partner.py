
import time
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _
from random import random,randint

class purchase_requisition_partner(osv.osv_memory):
	_inherit = "purchase.requisition.partner"
	_columns = {
		'partner_id': fields.many2one('res.partner','Supplier', required=False),
		'partner_ids': fields.many2many('res.partner', 'pr_partner_rel', 'pr_id', 'partner_id', 'Supplier', required=False),
		'group_product': fields.boolean("Group Products"),
	}
	_defaults = {
		"group_product": lambda *a : True,
	}

	def create_order(self, cr, uid, ids, context=None):
		active_ids = context and context.get('active_ids', [])
		
		purchase_order_line = self.pool.get('purchase.order.line')
		purchase_order_sca = self.pool.get('purchase.order.sca')
		res_partner = self.pool.get('res.partner')
		purchase_order = self.pool.get('purchase.order')
		fiscal_position = self.pool.get('account.fiscal.position')
		requisition = self.pool.get('purchase.requisition').browse(cr,uid,active_ids)[0]
		i=1
		for wiz in self.browse(cr,uid,ids,context=context):
			partners = wiz.partner_ids
			for partner in partners:
				supplier_pricelist = partner.property_product_pricelist_purchase or False
				supplier = partner
				res = {}
				### group  pr by location ID ###
	#			 for requisition in wiz.pr_ids:
					# if partner.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
					#	 raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
				location_id = requisition.warehouse_id.lot_input_id.id
				counter = len(str(requisition.counter_rfq + i)) == 1 and '00%s'%str(requisition.counter_rfq +i) or \
				len(str(requisition.counter_rfq+i)) == 2 and '0%s'%str(requisition.counter_rfq+i) or \
				len(str(requisition.counter_rfq+i)) >= 3 and '%s'%str(requisition.counter_rfq+i)
				name_rfq = 'RFQ/%s/%s'%(requisition.name, counter)
				self.pool.get('purchase.requisition').write(cr,uid,requisition.id,{'counter_rfq': requisition.counter_rfq + 1})
				name_po = '/Draft-%s'% randint(1,10000)
				i+=1
				purchase_id = purchase_order.create(cr, uid, {
							'origin': requisition.name,
							'goods_type': requisition.goods_type or 'stores',
							'partner_id': supplier.id,
							'pricelist_id': supplier_pricelist.id,
							'location_id': location_id,
							'company_id': requisition.company_id.id,
							'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
							'requisition_id':requisition.id,
							'notes':requisition.description,
							'warehouse_id':requisition.warehouse_id.id ,
							'name2': name_rfq,
							'name': name_po,
							'invoice_method':'picking',
							'purchase_type': supplier.partner_type =='local' and 'local' or 'import',
				})
				res[requisition.id] = purchase_id
				dump = {}
				if wiz.group_product:
					for line in requisition.line_ids:
						product = line.product_id
						seller_price, qty, default_uom_po_id, date_planned = self.pool.get('purchase.requisition')._seller_details(cr, uid, line, supplier, context=context)
						taxes_ids = product.supplier_taxes_id
						taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
						if product.id not in dump.keys():
							pr_line = [line.id]
							dump.update({
								product.id:{
											'pr_id_temporary' : line.id,
											'order_id': purchase_id,
											'name': product.partner_ref,
											'product_qty': qty,
											'product_id': product.id,
											'product_uom': default_uom_po_id,
											# 'account_analytic_id':line.account_analytic_id and line.account_analytic_id.id or False,
											'price_unit': seller_price,
											'date_planned': date_planned,
											# 'taxes_id': [(6, 0, taxes)],
											"requisition_id":requisition.id,
											"machine_number":line.machine_number or False,
											"part_number":line.part_number or False,
											"catalogue_id":line.catalogue_id and line.catalogue_id.id or False,
											'pr_lines': [(6,0,pr_line)],
											}
								})
						else:
							temp = dump.get(product.id,False)
							pr_line = temp.get('pr_lines',False) and temp.get('pr_lines',False)[0][2] or False
							pr_line.append(line.id)
							temp.update({
								'product_qty': temp.get('product_qty',0.0)+qty,
								'account_analytic_id':False,
								'pr_lines': [(6,0,pr_line)],
								})
					for dx in sorted(dump.values(), key=lambda x:x['pr_id_temporary']):
						del dx['pr_id_temporary'] 
						po_line_id = purchase_order_line.create(cr,uid,dx)
						dd=dx
						purchase_order_sca.create(cr, uid, {
							'tobe_purchased': False,
							'requisition_id': requisition.id,
							'po_line_id': po_line_id,
							'pr_lines':dd.get('pr_lines',False),
							"po_id":purchase_id,
							"partner_id":supplier.id,
							"product_id":dd.get('product_id',False),
							"name":dd.get('name',False),
							"product_qty":dd.get('product_qty',False),
							"pro_qty": dd.get('product_qty',False),
							"product_uom":dd.get('product_uom',False),
							"price_unit":dd.get('price_unit',False),
						}, context=context)
				else:
					for line in requisition.line_ids:
						product = line.product_id
						seller_price, qty, default_uom_po_id, date_planned = self.pool.get('purchase.requisition')._seller_details(cr, uid, line, supplier, context=context)
						taxes_ids = product.supplier_taxes_id
						taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
						pr_line = [line.id]
						dump.update({
							line.id:{
									'order_id': purchase_id,
									'name': product.partner_ref,
									'product_qty': qty,
									'product_id': product.id,
									'product_uom': default_uom_po_id,
									#'account_analytic_id':line.account_analytic_id and line.account_analytic_id.id or False,
									'price_unit': seller_price,
									'date_planned': date_planned,
									# 'taxes_id': [(6, 0, taxes)],
									"requisition_id":requisition.id,
									"machine_number":line.machine_number or False,
									"part_number":line.part_number or False,
									"catalogue_id":line.catalogue_id and line.catalogue_id.id or False,
									'pr_lines': [(6,0,pr_line)],
									}
							})
					for dx in sorted(dump.keys()):
						po_line_id = purchase_order_line.create(cr,uid,dump.get(dx,False))
						dd=False
						dd=dump.get(dx,False)
						purchase_order_sca.create(cr, uid, {
							'tobe_purchased': False,
							'requisition_id': requisition.id,
							'po_line_id': po_line_id,
							'pr_lines':dd.get('pr_lines',False),
							"po_id":purchase_id,
							"partner_id":supplier.id,
							"product_id":dd.get('product_id',False),
							"name":dd.get('name',False),
							"product_qty":dd.get('product_qty',False),
							"pro_qty": dd.get('product_qty',False),
							"product_uom":dd.get('product_uom',False),
							"price_unit":dd.get('price_unit',False),
						}, context=context)
		return {'type': 'ir.actions.act_window_close'}
purchase_requisition_partner()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
