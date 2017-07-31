import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class stores_consumption_wizard(osv.osv_memory):
    _name = "stores.consumption.wizard"
    _columns = {
            "start_date"                : fields.date('Start Date',required=True),
            "end_date"                  : fields.date('End Date',required=True),
            "goods_type"                : fields.many2many("goods.type",'goods_type_stores_consumption_rel','type_id','wizard_id',"Goods Type", required=True),
            "location_force"            : fields.many2many("stock.location","location_stores_consumption_force_rel","location_id","wizard_id","Force Location"),
            "analytic_account_force"    : fields.many2many("account.analytic.account","analytic_account_stores_consumption_force_rel","analytic_account_id","wizard_id","Force Analytic Account"),
            # "department_id"             : fields.many2one('hr.department','Department',required=False),
    }
    _defaults = {
        "start_date": time.strftime("%Y-%m-01"),
        "end_date" : time.strftime("%Y-%m-%d"),
        'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','in',[5,7])],context=None),
    }

    def print_report(self, cr, uid, ids, context={}):
        if not context:context={}
        wizard = self.browse(cr,uid,ids,context)[0]
        datas = {
            'ids': context.get('active_ids',[]),
            'model': 'stores.consumption.wizard',
            'start_date' : wizard.start_date,
            'end_date' : wizard.end_date,
            'goods_type':[x.id for x in wizard.goods_type],
            'location_force':[lf.id for lf in wizard.location_force],
            'analytic_account_force':[aaf.id for aaf in wizard.analytic_account_force],
            # 'department_id':wizard.department_id and wizard.department_id.id or False,
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'stores.consumption.report',
                'report_type': 'webkit',
                'datas': datas,
                }
stores_consumption_wizard()