from openerp.osv import fields,osv

class account_analytic_account(osv.Model):
	_inherit = "account.analytic.account"

	_columns = {
		"budget_expense":fields.many2one('account.account',"Budget Expense"),
		'department_id'	: fields.many2one('hr.department',"Department"),
	}

	def name_get(self, cr, uid, ids, context=None):
		res = []
		if not ids:
			return res
		if isinstance(ids, (int, long)):
			ids = [ids]
		for id in ids:
			elmt = self.browse(cr, uid, id, context=context)
			lv1=(elmt.code and ("["+ elmt.code +"] ") or "") +elmt.name
			lv2=elmt.parent_id and elmt.parent_id.name +"/" or ''
			name = lv2 + lv1
			res.append((id, name))
		return res

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, uid, [('name', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, uid, [('code', operator, name)]+ args, limit=limit, context=context)
		ids = list(set(ids))
		return self.name_get(cr, uid, ids, context)
	