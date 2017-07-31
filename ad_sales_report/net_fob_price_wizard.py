

import time
import netsvc
# from report import report_sxw
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
# from report import report_sxw
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class net_fob_price_wizard(osv.osv_memory):
    _name = "net.fob.price.wizard"
    _columns = {
            "goods_type"        : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "start_date"        : fields.date('Start Date',required=True),
            "end_date"          : fields.date('End Date',required=True),
            "as_on_date"        : fields.date('As On Date',required=True),
            "type"              : fields.selection([('booked_order','Booked Order Net FOB Price'),('target_fob','Target FOB Price')],'Report Type',required=True),
            "exception_agent_ids" : fields.many2many("res.partner","fob_wizard_rel_partner","wizard_id","partner_id","Agent Exceptions",domain=[('agent','=',True)]),
    }
    _defaults = {
        "goods_type": lambda *g:"finish",
        "sale_type" : lambda *s:"export",
        "start_date": lambda *s:time.strftime("%Y-%m-01"),
        "end_date" : lambda *e:time.strftime("%Y-%m-%d"),
        "as_on_date" : lambda *a:time.strftime("%Y-%m-%d"),
        "type":lambda *t:'booked_order',
    }

    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'net.fob.price.wizard',
             'form': self.read(cr, uid, ids)[0],
            }
        if datas['form']['type'] == 'booked_order':
            report_name = 'net.fob.price.report'
        else:
            report_name = 'target.fob.report'
        
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'report_type': 'webkit',
                'datas': datas,
                }
net_fob_price_wizard()