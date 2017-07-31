from openerp.osv import osv,fields

class om_tally_wizard(osv.TransientModel):
	_name = "om.tally.wizard"
	_columns = {
		"period_id"			: fields.many2one("account.period","Period",required=True),
		"ar_account_ids"	: fields.many2many("account.account",'wiz_tally_ar_id','wiz_id','account_id','AR Account',domain="[('type','=','receivable')]"),
		"adv_account_ids"	: fields.many2many("account.account",'wiz_tally_adv_id','wiz_id','account_id','Advance Account',domain="[('type','=','receivable')]"),
		"journal_ids"		: fields.many2many("account.journal",'wiz_tally_journal_id','wiz_id','journal_id','ReClass Journal'),
	}
	_defaults = {
	"journal_ids"	:[209],
	"period_id"		:28,
	"ar_account_ids":[230,231,232],
	"adv_account_ids":[120],

	}
	def print_om_tally(self,cr,uid,ids,context=None):
		if not context:context={}
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'om.tally.wizard',
			 'form': self.read(cr, uid, ids)[0],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'om.tally.report',
				'report_type': 'webkit',
				'datas': datas,
				}		