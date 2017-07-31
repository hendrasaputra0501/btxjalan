from openerp.osv import fields,osv

class ir_attachment(osv.Model):
	_inherit = "ir.attachment"
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		if not vals.get('res_model', False) and context.get('default_res_model', False):
			vals.get['res_model'] = context.get('default_res_model', False)		
		# print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",vals
		if not vals.get('parent_id', False):
			parent_ids = self.pool.get('document.directory').search(cr, uid, [('ressource_type_id','=',vals.get('res_model'))])
			# print "xxxxxxxxxx",parent_ids
			parent_id=[]
			if parent_ids and len(parent_ids)>1:
				for parent in self.pool.get('document.directory').browse(cr,uid,parent_ids):
					if parent.domain:
						# print "================",parent.domain,type(parent.domain),vals.get("res_id",False)
						res_list = self.pool.get(vals.get('res_model')).search(cr,uid,eval(parent.domain))
						# print "res----------------",res_list
						if vals.get('res_id',False):
							if vals['res_id'] in res_list:
								parent_id.append(parent.id)
					else:
						continue
			# print "parent_id========",parent_id
			if not parent_id and parent_ids:
				parent_id = parent_ids
			if parent_id and parent_id[0]:
			   vals['parent_id'] = parent_id[0]
			else:
				vals['parent_id'] = False
		
		return super(ir_attachment, self).create(cr, uid, vals, context)
ir_attachment()