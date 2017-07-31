from openerp.osv import fields, osv
import re
from tools.translate import _
from operator import itemgetter
from lxml import etree
from openerp.osv.orm import setup_modifiers

class company_type(osv.osv):
	_name = "company.type"
	_columns = {
		"name" : fields.char('Name',size=10,required=True),
		"affix" : fields.selection([('prefix','Prefix'),('suffix','Suffix')],'Affix Type',required=True),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		type_affix={'prefix':'Prefix','suffix':'Suffix'}		
		reads = self.read(cr, uid, ids, ['name','affix'], context=context)
		res = []
		for record in reads:
			name = record['name'] + '(' + type_affix[record['affix']] + ')'
			res.append((record['id'], name))
		return res

class res_partner(osv.osv):
	_inherit = "res.partner"
	
	def _credit_debit_overdue_get(self, cr, uid, ids, field_names, arg, context=None):
		query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
		cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
					  FROM account_move_line l
					  LEFT JOIN account_account a ON (l.account_id=a.id)
					  WHERE a.type IN ('receivable','payable')
					  AND l.partner_id IN %s
					  AND l.reconcile_id IS NULL
					  AND l.date_maturity <= CURRENT_DATE 
					  AND """ + query + """
					  GROUP BY l.partner_id, a.type
					  """,
				   (tuple(ids),))
		maps = {'receivable':'credit_overdue', 'payable':'debit_overdue' }
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0)
		for pid,type,val in cr.fetchall():
			if val is None: val=0
			res[pid][maps[type]] = (type=='receivable') and val or -val
		return res

	def _asset_difference_due_search(self, cr, uid, obj, name, type, args, context=None):
		if not args:
			return []
		having_values = tuple(map(itemgetter(2), args))
		where = ' AND '.join(
			map(lambda x: '(SUM(bal2) %(operator)s %%s)' % {
								'operator':x[1]},args))
		query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
		cr.execute(('SELECT pid AS partner_id, SUM(bal2) FROM ' \
					'(SELECT CASE WHEN bal IS NOT NULL THEN bal ' \
					'ELSE 0.0 END AS bal2, p.id as pid FROM ' \
					'(SELECT (debit-credit) AS bal, partner_id ' \
					'FROM account_move_line l ' \
					'WHERE account_id IN ' \
							'(SELECT id FROM account_account '\
							'WHERE type=%s AND active) ' \
					'AND reconcile_id IS NULL AND date_maturity<= CURRENT_DATE ' \
					'AND '+query+') AS l ' \
					'RIGHT JOIN res_partner p ' \
					'ON p.id = partner_id ) AS pl ' \
					'GROUP BY pid HAVING ' + where), 
					(type,) + having_values)
		res = cr.fetchall()
		if not res:
			return [('id','=','0')]
		return [('id','in',map(itemgetter(0), res))]

	def _credit_overdue_search(self, cr, uid, obj, name, args, context=None):
		return self._asset_difference_due_search(cr, uid, obj, name, 'receivable', args, context=context)
	
	_columns = {
		"edit_state" :fields.selection([('writeable','Writeable'),('unwriteable','Unwriteable')],"Editable State",required=True),
		"street3" : fields.char('Street 3',size=128),
		"partner_alias" : fields.char('Alias', size=128, help="This is can be use for reporting purpose"),
		"type_of_companies":fields.many2one('company.type','Type of Companies'),
		"partner_code":fields.char('Partner Code', size=64,required=False,select=True),
		'group_id':fields.many2one('res.partner',"Company Group"),
		"agent_ids":fields.many2many('res.partner',"partner_partner_rel","partner_id","agent_id","Agents"),
		"agent":fields.boolean("Agent"),
		"spec_terms":fields.text('Specific Terms'),
		'type': fields.selection([('default', 'Default'), ('invoice', 'Invoice'),
								   ('delivery', 'Shipping'), ('contact', 'Contact'),('service',"Service Centre"),
								   ('other', 'Other')], 'Address Type',
			help="Used to select automatically the right address according to the context in sales and purchases documents."),
		'credit_overdue': fields.function(_credit_debit_overdue_get,
			fnct_search=_credit_overdue_search, string='Total Overdue Receivable', multi='dco', help="Total amount this customer owes you and have been overdue."),
		'debit_overdue': fields.function(_credit_debit_overdue_get,
			fnct_search=_credit_overdue_search, string='Total Overdue Payable', multi='dco', help="Total amount this supplier you owes and have been overdue."),
		'credit_overdue_limit': fields.float('Receivable Overdue Limit'),
		'credit_overdue_limit_group': fields.float('Company Group AR Overdue Limit'),
		'credit_limit_group': fields.float('Company Group Receivable Limit'),
		'shipment_local_area_id' : fields.many2one('res.country.state','Local Shipment Area', help="This will be use for local shipment costing purpose")
	}
	_defaults = {
		"edit_state":'writeable',
	}
	def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):
		res = super(res_partner, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

		
		if view_type == 'form':
			# Set all fields read only when state is close.
			doc = etree.XML(res['arch'])
			for node in doc.xpath("//field"):
				attrs_original = eval(node.get('attrs',str(False)))
				attrs_readonly = attrs_original and attrs_original.get('readonly',False) or False
				if (attrs_original and not attrs_readonly) or not attrs_original:
					attrs_readonly = []
					attrs_readonly.append(('edit_state', '=', 'unwriteable'))
				else:
					attrs_readonly.append("|")
					attrs_readonly.append(('edit_state', '=', 'unwriteable'))
					attrs_readonly=attrs_readonly
				if not attrs_original:
					attrs_original={}
				attrs_original.update({'readonly':attrs_readonly})
				node.set('attrs', str(attrs_original))
				node_name = node.get('name')
				setup_modifiers(node, res['fields'][node_name])
			res['arch'] = etree.tostring(doc)

		return res
	
	def write(self, cr, uid, ids, vals, context={}):
		if not context:context={}
		for partner in self.browse(cr,uid,ids,context=context):
			if partner.edit_state =='writeable':
				vals.update({'edit_state':"unwriteable"})
		res=super(res_partner, self).write(cr, uid, ids, vals, context)
		return res

	def set_writeable(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'edit_state':'writeable'})

	def set_unwriteable(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'edit_state':'unwriteable'})

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		return [(r['id'], (r['partner_code'] and '[%s] %s' or '%s%s') % (r['partner_code'] or '' , r['name'] or '')) for r in self.read(cr, uid, ids, ['partner_code', 'name'], context, load='_classic_write') if type(r)==dict and r['id'] and r['id']!='']
		
	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('name','ilike',name)]+ args, limit=limit, context=context)
			if not ids:
				self.search(cr, user, [('partner_code','ilike',name)]+ args, limit=limit, context=context)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('partner_code','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		
		result = self.name_get(cr, user, ids, context=context)
		return result
