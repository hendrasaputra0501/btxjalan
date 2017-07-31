from openerp.osv import fields, osv

from tools.translate import _

class sale_order(osv.Model):
	_inherit = 'sale.order'
	_columns = {
	}

class sale_order_line(osv.Model):
	_inherit = 'sale.order.line'
	_columns = {
		'template_product_desc'	: fields.many2one('template.product.desc','Template Description'),
		'local_desc':fields.text("Product Local Description", ),
		'export_desc':fields.text("Product Export Description",),
		'use_template_on_print': fields.boolean("Use Template on SC Print?"),
		}
	_defaults = {
		"state":lambda *a:'draft',
				}
	def onchange_template_product_desc(self, cr, uid, ids, sale_type, application, product_id, temp, context=None):
		temp_pooler = self.pool.get('template.product.desc')
		temp_id = temp and temp_pooler.browse(cr,uid,temp,context) or False
		product_id = product_id and self.pool.get('product.product').browse(cr,uid,product_id)
		if product_id:
			code = product_id.default_code or ''
			name = product_id.name or ''
			app = ''
			if application:
				app = application=='knitting' and 'for knitting' or 'for weaving'

			if temp_id:
				if sale_type=='export':
					desc = (name + ' ' + app + '\n\n' + temp_id.desc).upper()
					return {'value':{'export_desc':desc,'local_desc':product_id.local_desc}}
				elif sale_type=='local':
					desc = (name + ' ' + app + '\n\n' + temp_id.desc).upper()
					return {'value':{'local_desc':desc,'export_desc':product_id.export_desc}}
				
		return True


class template_product_desc(osv.osv):
	_name = "template.product.desc"
	_columns = {
		"name" : fields.char('Number', size=128),
		"desc" : fields.text('Description', required=True),
		"product_id" : fields.many2one('product.product','Product', required=True)
	}
