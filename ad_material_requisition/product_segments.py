from openerp.osv import fields,osv

class product_first_segment_code(osv.Model):
	_name = "product.first.segment.code"
	_columns = {
		"code":fields.char("Code",size=3,required=True),
		"name":fields.char('Description', size=128, required=True),
	}

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('code', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)
	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		return [(r['id'], (r['code'] and '[%s] %s' or '%s%s') % 
				(r['code'] or '' , r['name'] or '')) 
				for r in self.read(cr, uid, ids, ['code', 'name'], context, load='_classic_write') if type(r)==dict and r['id'] and r['id']!='']

class product_second_segment_code(osv.Model):
	_name = "product.second.segment.code"
	_columns = {
		"code":fields.char("Code",size=3,required=True),
		"name":fields.char('Description', size=128, required=True),
		'active': fields.boolean('Active', help="By unchecking the active field you can disable a segment code without deleting it."),
	}

	_defaults = {
        'active': 1,
    }

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		return [(r['id'], (r['code'] and '[%s] %s' or '%s%s') % 
				(r['code'] or '' , r['name'] or '')) 
				for r in self.read(cr, uid, ids, ['code', 'name'], context, load='_classic_write') if type(r)==dict and r['id'] and r['id']!='']

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('code', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)
	
class product_reason_code(osv.Model):
	_name = "product.reason.code"
	_columns = {
		"code":fields.char("Code",size=6,required=True),
		"name":fields.char('Description', size=128, required=True),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		return [(r['id'], (r['code'] and '[%s] %s' or '%s%s') % 
				(r['code'] or '' , r['name'] or '')) 
				for r in self.read(cr, uid, ids, ['code', 'name'], context, load='_classic_write') if type(r)==dict and r['id'] and r['id']!='']

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('code', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

class product_material_type(osv.osv):
	_name = "product.material.type"
	_columns = {
		"name":fields.char("Code",size=12,required=True),
		"description": fields.char("Description",size=64,required=True)
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		return [(r['id'], (r['name'] and '[%s] %s' or '%s%s') % 
				(r['name'] or '' , r['description'] or '')) 
				for r in self.read(cr, uid, ids, ['name', 'description'], context, load='_classic_write') if type(r)==dict and r['id'] and r['id']!='']

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('description', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)