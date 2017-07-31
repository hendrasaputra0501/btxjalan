import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class issue_history_wizard(osv.osv_memory):
    _name = "item.history.wizard"
    _columns = {
            "start_date"        : fields.date('Start Date',required=True),
            "end_date"          : fields.date('End Date',required=True),
            "product_id"        : fields.many2one('product.product','Product',required=True),
            "location_force"    : fields.many2many("stock.location","location_item_history_force_rel","location_id","wizard_id","Force Location"),
    }
    _defaults = {
        "start_date": time.strftime("%Y-%m-01"),
        "end_date" : time.strftime("%Y-%m-%d"),
    }

    def print_report(self, cr, uid, ids, context={}):
        if not context:context={}
        wizard = self.browse(cr,uid,ids,context)[0]
        datas = {
            'ids': context.get('active_ids',[]),
            'model': 'item.history.wizard',
            'start_date' : wizard.start_date,
            'end_date' : wizard.end_date,
            'product_id':wizard.product_id and wizard.product_id.id or False,
            'location_force':[lf.id for lf in wizard.location_force],
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'item.history',
                'report_type': 'webkit',
                'datas': datas,
                }
issue_history_wizard()