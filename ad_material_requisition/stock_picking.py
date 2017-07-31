from openerp.osv import fields,osv

class stock_picking(osv.Model):
	_inherit = "stock.picking"
	_columns = {
		"req_employee"		: fields.many2one('hr.employee',"Employee Request"),
		"material_req_id"	: fields.many2one('material.request',"Material Request"),
		"mr_description"	: fields.text("Material Request Description"),

		"issue_state"		: fields.selection([('draft_department','Department Draft'),('approved_department','Approved by Department')],'Issue State'),
		'goods_type' : fields.selection([('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],
			'Goods Type'),
		"manual_issue"		: fields.boolean("Manual Issue"),
	}

	_defaults = {
		'issue_state' : lambda self, cr, uid, context : context.get('issue_state',False), 
		'manual_issue' : 0,
	}

	def action_approve_dept(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'issue_state':'approved_department'})

	def set_draft_dept_approved(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'issue_state':'draft_department'})


		
