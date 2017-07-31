import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class advance_report_wizard(osv.osv_memory):
    _name = "advance.report.wizard"
    _columns = {
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "as_on_date"        : fields.date('As ON Date'),
            "start_date"        : fields.date('Start Date'),
            "end_date"          : fields.date('End Date'),
            "currency_id"       : fields.many2one('res.currency','Currency', required=True),
            "report_type"       : fields.selection([('adv_report','Detail Advances Report'),('adv_outs','Outstanding Advances Report'),('adv_adj','Adjustment Advances Report')], 'Report Type', required=True)
    }
    _defaults = {
        "sale_type" : "export",
        "report_type" : lambda *r:'adv_report',
        "as_on_date" : lambda *a:time.strftime("%Y-%m-%d"),
        "start_date": lambda *a:time.strftime("%Y-%m-01"),
        "end_date" : lambda *a:time.strftime("%Y-%m-%d"),
        "currency_id" : lambda self,cr,uid,context:self.pool.get('res.users').browse(cr,uid,uid,context).company_id.currency_id.id or False,
    }

    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'advance.report.wizard',
             'form': self.read(cr, uid, ids)[0],
            }
        if datas['form']['report_type'] == 'adv_report':
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'advance.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }
        elif datas['form']['report_type'] == 'adv_outs':
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'os.advance.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }
        elif datas['form']['report_type'] == 'adv_adj':
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'adj.advance.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }

advance_report_wizard()