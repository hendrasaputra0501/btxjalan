

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

class lc_tt_position_wizard(osv.osv_memory):
    _name = "lc.tt.position.wizard"
    _columns = {
            "goods_type"        : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "as_on"             : fields.date('As on',required=True),
            'lc_type'           : fields.selection([('tt','TT'),('in','LC')],"LC Type"),
    }
    _defaults = {
        "goods_type": "finish",
        "sale_type" : "export",
        "as_on"     : time.strftime("%Y-%m-%d"),
        "lc_type"   : "in",
    }

    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'lc.tt.position.wizard',
             'form': self.read(cr, uid, ids)[0],
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'lc.tt.position.report',
                'report_type': 'webkit',
                'datas': datas,
                }
lc_tt_position_wizard()