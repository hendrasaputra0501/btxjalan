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

class payment_overdue_wizard(osv.osv_memory):
    _name = "payment.overdue.wizard"
    _columns = {
            "as_on"             : fields.date('As on',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "rounding"          : fields.integer("Number of digits(max.2)"),
            "goods_type"        : fields.selection([('finish','Finish Goods'),('finish_others','Finish Goods(Others)'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type', required=True),
            # "account_id"       : fields.many2one('account.account','Account Receivable',domain=[('type','=','receivable')],required=True),
            "journal_ids" : fields.many2many("account.journal","overdue_report_wizard_rel_journal","wizard_id","journal_id", "Filter Journals", domain=[('type','in',['sale','sale_refund','situation'])]),
            "account_ids" : fields.many2many("account.account","overdue_report_wizard_rel_account","wizard_id","account_id","Filter AR Accounts", required=True, domain=[('type','=','receivable')]),
            "adv_account_ids" : fields.many2many("account.account","overdue_report_wizard_rel_adv_account","wizard_id","account_id","Filter Advance Accounts", required=True, domain=[('type','=','receivable')]),
    }
    _defaults = {
        "as_on"     : lambda *a: time.strftime("%Y-%m-%d"),
        "sale_type" : lambda *a:"export",
        "goods_type" : lambda *a:"finish",
        "rounding" : lambda *a:2,
        # "journal_ids" : lambda self,cr,uid,context=None:self.pool.get('account.journal').search(cr,uid,[('type','in',['sale','sale_refund'])],context=None),
        # "account_ids" : lambda self,cr,uid,context=None:self.pool.get('account.account').search(cr,uid,[('type','=','receivable')],context=None),
    }
    def onchange_rounding(self,cr,uid,ids,rounding,context=None):
        val={'rounding':rounding}
        if rounding and (rounding > 2 or rounding < 0):
            val.update({'rounding':2})
        return {'value':val}
        
    def print_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'payment.overdue.wizard',
             'form': self.read(cr, uid, ids)[0],
             'date_entry' : time.strftime('%Y-%m-%d'),
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pay.overdue.report',
                'report_type': 'webkit',
                'datas': datas,
                }
payment_overdue_wizard()