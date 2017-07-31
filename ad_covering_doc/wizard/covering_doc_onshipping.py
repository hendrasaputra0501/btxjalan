from osv import osv, fields
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class covering_doc_onshipping(osv.osv_memory):

	_name = "covering.doc.onshipping"
	_description = "Covering Document Onshipping"

	_columns = {
		'group': fields.boolean("Group by Schedule Date"),
		'date': fields.date('Creation date'),
	}

	_defaults = {
		'group' : True,
	}

	def open_covering_doc(self, cr, uid, ids, context=None):
			if context is None:
				context = {}
			covering_ids = []
			data_pool = self.pool.get('ir.model.data')
			active_ids = context.get('active_ids', [])
			do_pool=self.pool.get('stock.picking')
			pickings=do_pool.browse(cr,uid,active_ids)
			invoice_ids=[x.invoice_id.id for x in pickings if x.invoice_id]
			if len(invoice_ids)< len(active_ids):
				raise osv.except_osv(_('Error!'), _('salah satu do belum ada invoice'))
			applicant_ids=[x.invoice_id.partner_id.id for x in pickings if x.invoice_id.partner_id.id]
			if len(set(applicant_ids))>1:
				raise osv.except_osv(_('Error!'), _('applicant harus sama'))
			res = self.create_covering_doc(cr, uid, ids, context=context)
			covering_ids += [res]
			action_model = False
			action = {}
			# if not covering_ids:
			# 	raise osv.except_osv(_('Error!'), _('Please create Cover.'))
			action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_covering_doc', "action_covering_doc")
			if action_model:
				action_pool = self.pool.get(action_model)
				action = action_pool.read(cr, uid, action_id, context=context)
				action['domain'] = "[('id','in', ["+','.join(map(str,covering_ids))+"])]"
			return action

	def create_covering_doc(self, cr, uid, ids, context=None):
		if context is None:
			context = {}

		covering_pool = self.pool.get('covering.doc')
		active_ids = context.get('active_ids', [])
		do_pool=self.pool.get('stock.picking')
		invoice_ids=[]
		for lines in active_ids:
			do=do_pool.browse(cr, uid,lines)
			invoice_id=do.invoice_id.id
			invoice_ids.append(invoice_id)
			consignee_id=do.invoice_id.partner_id.id
		res=covering_pool.create(cr,uid,{
			'date' : time.strftime("%Y-%m-%d"),
			'consignee_id' : consignee_id,
			'invoice_ids' : [(6,0,list(set(invoice_ids)))],
			},context=context)

		return res

covering_doc_onshipping()