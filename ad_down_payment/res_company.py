from osv import osv
from osv import fields
import os
import tools
from tools.translate import _
from tools.safe_eval import safe_eval as eval


class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'downpayment_account_id': fields.many2one('account.account', 'Downpayment Account'),
        'retention_account_id': fields.many2one('account.account', 'Retention Account'),
    }
    
res_company()