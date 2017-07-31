from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _
from datetime import datetime
import time

class wizard_company_profile(osv.osv_memory):
	_name = "wizard.company.profile"
	_description = "Open Company Profile"
	_columns = {
		"company_id" : fields.many2one('res.company','Company', readonly=True),
	}

	_defaults = {
		'company_id' : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.id or False,
	}

	def action_open_window(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		wizard = self.read(cr, uid, ids, ['company_id'], context=context)
		if wizard:
			company = self.pool.get('res.company').browse(cr, uid, wizard[0]['company_id'][0])
			url = company.website
			return {
				'name'     : 'Go to website',
				'res_model': 'ir.actions.act_url',
				'type'     : 'ir.actions.act_url',
				'target'   : 'self',
				'url'      : "http://%s"%url,
			}

wizard_company_profile()
