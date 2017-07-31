import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class commision_detail_wizard(osv.osv_memory):
    _name = "commision.detail.wizard"
    _columns = {
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "start_date"        : fields.date('Start Date',required=True),
            "end_date"          : fields.date('End Date',required=True),
            "fiscalyear_id"     : fields.many2one('account.fiscalyear','Fiscal Year'),
            "company_id"        : fields.many2one('res.company','Company'),
    }
    _defaults = {
        "sale_type" : "export",
        "start_date": time.strftime("%Y-%m-01"),
        "end_date" : time.strftime("%Y-%m-%d"),
        "company_id" : lambda self, cr, uid, context : self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
        # "start_date": lambda *a:'2015-08-01',
        # "end_date": lambda *a:'2015-08-31',
    }

    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'commision.detail.wizard',
             'form': self.read(cr, uid, ids)[0],
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'commision.detail.report',
                'report_type': 'webkit',
                'datas': datas,
                }
commision_detail_wizard()