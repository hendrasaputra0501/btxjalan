from openerp.osv import fields,osv
from openerp.tools.translate import _

class account_move_line_distribution(osv.Model):
	_inherit = "account.analytic.line"
	_columns = {
		"invoice_related_id" : fields.many2one("account.invoice","Charge Related Invoice"),
	}

class account_move_line(osv.Model):
	_inherit = "account.move.line"
	_columns = {
		"analytic_distribution_line":fields.one2many('account.move.line.distribution','move_id',"Distributed Analytic")
	}

	def create_analytic_lines(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = super(account_move_line, self).create_analytic_lines(cr, uid, ids, context=context)
		analytic_line_obj = self.pool.get('account.analytic.line')
		for line in self.browse(cr, uid, ids, context=context):
			# toremove = analytic_line_obj.search(cr, uid, [('move_id','=',line.id)], context=context)
			# if toremove:
			# 	analytic_line_obj.unlink(cr, uid, toremove, context=context)
			if line.analytic_lines:
				analytic_line_obj.unlink(cr,uid,[obj.id for obj in line.analytic_lines])

			if line.analytic_account_id:
				if not line.journal_id.analytic_journal_id:
					raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal!") % (line.journal_id.name, ))
				vals_line = self._prepare_analytic_line(cr, uid, line, context=context)
				analytic_line_obj.create(cr, uid, vals_line)

			# if line.analytics_id:
			# 	if not line.journal_id.analytic_journal_id:
			# 		raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal.") % (line.journal_id.name,))
			# 	for line2 in line.analytics_id.account_ids:
			# 		val = (line.credit or  0.0) - (line.debit or 0.0)
			# 		amt=val * (line2.rate/100)
			# 		al_vals={
			# 			'name': line.name,
			# 			'date': line.date,
			# 			'account_id': line2.analytic_account_id.id,
			# 			'unit_amount': line.quantity,
			# 			'product_id': line.product_id and line.product_id.id or False,
			# 			'product_uom_id': line.product_uom_id and line.product_uom_id.id or False,
			# 			'amount': amt,
			# 			'general_account_id': line.account_id.id,
			# 			'move_id': line.id,
			# 			'journal_id': line.journal_id.analytic_journal_id.id,
			# 			'ref': line.ref,
			# 			'percentage': line2.rate
			# 		}
			# 		print "----------------------",al_vals
			# 		analytic_line_obj.create(cr, uid, al_vals, context=context)
			if line.analytic_distribution_line:
				if not line.journal_id.analytic_journal_id:
					raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal.") % (line.journal_id.name,))
				for line3 in line.analytic_distribution_line:
					al_vals={
						'invoice_related_id': line3.invoice_related_id.id,
						'name': line3.name,
						'date': line3.date,
						'account_id': line3.account_id.id,
						'unit_amount': line3.unit_amount,
						'product_id': line3.product_id and line3.product_id.id or False,
						'product_uom_id': line3.product_uom_id and line3.product_uom_id.id or False,
						'amount': line3.amount,
						'general_account_id': line3.account_id.id,
						'move_id': line.id,
						'journal_id': line3.journal_id.id,
						'ref': line3.ref,
						'percentage': line3.percentage
					}
					analytic_line_obj.create(cr, uid, al_vals, context=context)
		return res

class account_move_line_distribution(osv.Model):
	_name = "account.move.line.distribution"
	_columns = {
		"invoice_related_id" : fields.many2one("account.invoice","Charge Related Invoice"),
		"name"			: fields.char("Name",size=128,required=True),
		"date"			: fields.date("Date",required=True),
		"account_id"	: fields.many2one("account.analytic.account","Account"),
		"unit_amount"	: fields.float("Quantity"),
		"product_id"	: fields.many2one("product.product","Product"),
		"product_uom_id": fields.many2one("product.uom","UoM"),
		"amount"		: fields.float("Amount"),
		"general_acccount":fields.many2one("account.account","Account"),
		"move_id"		: fields.many2one("account.move.line","Journal Item"),
		"journal_id"	: fields.many2one("account.analytic.journal","Analytic Journal"),
		"ref"			: fields.char("Ref",size=128),
		"percentage"	: fields.float("Percentage")
	}

