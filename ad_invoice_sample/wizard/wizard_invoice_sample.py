from osv import osv, fields
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
import time


class wizard_invoice_sample(osv.osv_memory):
	_name = "wizard.invoice.sample"
	_description = "Wizard Invoice Sample"

	_columns = {
	# 	'group': fields.boolean("Group by Schedule Date"),
		'date': fields.date('Creation date'),
	}

	_defaults = {
	 	'date' : lambda *a:datetime.now().strftime("%Y-%m-%d"),
	 }

	def invoice_sample(self,cr,uid,ids, context=None):
		if context is None:
			context= {}
		invoice_ids=[]
		data_pool=self.pool.get('ir.model.data')
		# active_ids = context.get('active_ids', [])
		# do_pool=self.pool.get('stock.picking')
		# pickings=do_pool.browse(cr,uid,active_ids)
		res=self.create_invoice_sample(cr,uid,ids,context=context)
		# invoice_ids += res.values()
        
		# action_model = False
		# action = {}
		# if not invoice_ids:
		# 	raise osv.except_osv(_('Error!'), _('Please create Invoices.'))
		# action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_invoice_sample', "invoice_sample_form")
		# if action_model:
		# 	action_pool = self.pool.get(action_model)
		# 	action = action_pool.read(cr, uid, action_id, context=context)
		# 	action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
		# return action
		return res

	def create_invoice_sample(self,cr,uid,ids, context=None):
		if not context:context={}
		active_ids=context.get('active_ids',[])
		do_obj=self.pool.get('stock.picking')
		do_line_obj=self.pool.get('stock.move')
		inv_obj=self.pool.get('invoice.sample')
		inv_line_obj=self.pool.get('invoice.sample.line')
		onshipdata_obj = self.read(cr, uid, ids, ['date'])
		inv_ids=[]
		for id_picking in do_obj.browse(cr, uid,active_ids):
			print id_picking,"jajajajajajjajjajajaj"
			if  id_picking.invoice_state=="none":
				if context.get('new_picking', False):
					onshipdata_obj['id'] = onshipdata_obj.new_picking
					onshipdata_obj[ids] = onshipdata_obj.new_picking
				record ={ 
						'date_invoice':onshipdata_obj[0]['date'],
						'picking_ids':id_picking.id,
						'consignee_partner_id' : id_picking.partner_id.id,
						
				}

				inv_id=inv_obj.create(cr,uid,record)
				inv_ids.append(inv_id)

				for id_move_lines in id_picking.move_lines:
					inv_line_data={
							'invoice_id' :inv_id,
							'product_id' :id_move_lines.product_id.id,
							'name'  : id_move_lines.name,
							'quantity' : id_move_lines.product_qty,
							'uom_id' : id_move_lines.product_uom.id,
							'move_id' :id_move_lines.id,
					}
					inv_line_obj.create(cr,uid,inv_line_data)
			# 	id_picking.write({
			# 		"invoice_state":'invoiced',
			# 		})
			# else:
			# 	 raise osv.except_osv(_('Can not create new invoice document!'),_("Invoice Document has already created before!") )
		return inv_ids


wizard_invoice_sample()