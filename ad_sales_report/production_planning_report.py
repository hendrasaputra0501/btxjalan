

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

class report_production_planning(osv.osv_memory):
    _name = "report.production.planning.wizard"
    _columns = {
            "report_type"       : fields.selection([('product','Product Wise'),('customer','Customer Wise'),('contract','Contract Wise')],'Report Type',required=True),
            "goods_type"        : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "as_on"             : fields.date('As On',required=True),
            "locale_sale_type"  : fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
    } 
    _defaults ={
            'report_type'   : 'product',
            'goods_type'    : 'finish',
            'sale_type'     : 'export',
            'as_on'         : lambda *a:time.strftime("%Y-%m-%d"),
            }
    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'report.production.planning.wizard',
             'form': self.read(cr, uid, ids)[0],
                 }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'production.planning.report',
                'report_type': 'webkit',
                'datas': datas,
                }
report_production_planning()