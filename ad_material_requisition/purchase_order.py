import time
import netsvc
from openerp.tools.translate import _
from osv import fields,osv
from random import random,randint
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class purchase_order(osv.osv):
	_inherit = 'purchase.order'

	def generate_po_number(self,cr,uid,ids,context=None):
		for data in self.browse(cr,uid,ids):
			cd = {'date':datetime.strptime(data.date_order,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order') or '/'
			self.write(cr,uid,[data.id],{'name':name})
		return True

	def _get_picking_progress(self,cr,uid,ids,field,args, context=None):
		value = {}
		for data in self.browse(cr,uid,ids):
			total = 0.0
			total_all = 0.0
			for line in data.picking_ids:
				for d_line in line.move_lines:
					total += d_line.state == 'done' and d_line.product_qty or 0.0
			for line2 in data.order_line:
				total_all += line2.product_qty
			value[data.id] = (total_all!=0.0) and (total / total_all * 100) or 0.0
		return value
	
	def _get_invoicing_progress(self,cr,uid,ids,field,args, context=None):
		value = {}
		for data in self.browse(cr,uid,ids):
			total_paid = 0.0
			total_all = 0.0
			for line in data.invoice_ids:
				if line.state in ('draft','cancel'):continue
				total_paid += line.amount_total-line.residual
				total_all += line.amount_total
			#print "total_paid,total_all",total_paid,total_all
			value[data.id] = ((total_all>0.0) and ((total_paid/total_all)*100)) or 0.0
		return value

	_columns = {

				'name2'				: fields.char('RFQ Number', size=64, required=False, select=True, help="Unique number of the RFQ, computed automatically when the RFQ is created."),
				'tobe_purchased'	: fields.boolean('To Be Purchased'),
				'progress_picking'	: fields.function(_get_picking_progress,string="Shipment Progress",type="float"),
				'progress_invoicing': fields.function(_get_invoicing_progress,string="Invoice Progress",type="float"),
				"cancelled_order_ids": fields.one2many('purchase.order.line','old_order_id',"Un Purchased Item(s) from PR")
	}
	
	def button_confirm(self,cr,uid,ids, context=None):
		wf_service = netsvc.LocalService("workflow")
		for data in self.browse(cr,uid,ids):
			if data.tobe_purchased and data.requisition_id and data.requisition_id.state=='done_pr':
				wf_service.trg_validate(uid, 'purchase.order', data.id, 'purchase_confirm', cr)
				
		return True

	def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
		res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context)
		if order_line.pr_lines:
			if order_line.pr_lines[0].material_req_line_id:
				if order_line.pr_lines[0].material_req_line_id.location_id:
					res['location_dest_id'] = order_line.pr_lines[0].material_req_line_id.location_id.id
				elif order_line.pr_lines[0].material_req_line_id.requisition_id:
					res['location_dest_id'] = order_line.pr_lines[0].material_req_line_id.requisition_id.location_id.id
		return res
purchase_order()


class purchase_order_line(osv.osv):
	_inherit = 'purchase.order.line'
	_columns = {
		# "requisition_line_id"	: fields.many2one('purchase.requisition.line',"Requisition Line"),
		"requisition_id"		: fields.many2one("purchase.requisition","Requisition Number"),
		'pr_lines'				: fields.many2many('purchase.requisition.line','po_line_requisition_line_rel','po_line_id','req_line_id',"Requisition Line"),
		'old_order_id'			: fields.many2one('purchase.order',"Previous PO"),
		'order_id'				: fields.many2one('purchase.order', 'Order Reference', select=True, required=False, ondelete='cascade'),
		'machine_number'	: fields.char('Machine Number', size=200, required=False),	
		'part_number'		: fields.char(string='Part Number',size=300),
		'catalogue_id'		: fields.many2one('product.catalogue', 'Catalogue'),
		'catalogue_appears' : fields.boolean('Catalogue Appears', help="By unchecking the Catalogue Appears field you can not appear catalogue in report."),
	}

	_defaults = {
		'catalogue_appears': 1,
	}

	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
			partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
			name=False, price_unit=False, context=None):
		"""
		Here we can inherit anything related to onchange product_id
		"""
		res = super(purchase_order_line,self).onchange_product_id(cr,uid,ids,pricelist_id,product_id,qty,uom_id,partner_id,
			date_order=date_order,fiscal_position_id=fiscal_position_id,date_planned=date_planned,name=name,price_unit=price_unit,context=context)
		if product_id:
			prod = self.pool.get('product.product').browse(cr,uid,product_id)
			catalogue_id = False
			part_number = False
			if prod.catalogue_lines and prod.catalogue_lines[0]:
				catalogue_id = prod.catalogue_lines[0] and prod.catalogue_lines[0].catalogue.id or False
			if prod.catalogue_lines and prod.catalogue_lines[0] and prod.catalogue_lines[0].part_number:
				part_number = prod.catalogue_lines[0].part_number or False
			res['value']['part_number'] = part_number
			res['value']['catalogue_id'] = catalogue_id
		return res
purchase_order_line()