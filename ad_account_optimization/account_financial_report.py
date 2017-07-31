import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter

import netsvc
import pooler
from osv import fields, osv
import decimal_precision as dp
from tools.translate import _

class account_financial_report(osv.osv):
    _inherit = "account.financial.report"
    _description = "Account Report"
    
    def _get_children_by_order(self, cr, uid, ids, context=None):
        res = []
        for id in ids:
            res.append(id)
            ids2 = self.search(cr, uid, [('parent_id', '=', id)], context=context)
            res += self._get_children_by_order(cr, uid, ids2, context=context)
        return res
    
    _columns = {
            
                }
account_financial_report()