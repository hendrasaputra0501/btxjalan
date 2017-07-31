import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class issue_report_wizard(osv.osv_memory):
    _name = "issue.report.wizard"
    _columns = {
            # "sale_type"               : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "start_date"                : fields.date('Start Date',required=True),
            "end_date"                  : fields.date('End Date',required=True),
            "goods_type"                : fields.many2many("goods.type",'goods_type_issue_report_rel','type_id','wizard_id',"Goods Type", required=True),
            "location_force"            : fields.many2many("stock.location","location_issue_report_force_rel","location_id","wizard_id","Force Location"),
            "analytic_account_force"    : fields.many2many("account.analytic.account","analytic_account_issue_report_force_rel","analytic_account_id","wizard_id","Force Analytic Account"),
            "header_group_by"           : fields.selection([('site_wise','Site Wise'),('code_wise','Product First Segment Code Wise'),('analytic_account_wise','Analytic Account Wise'),('material_type','Material Type Wise'),('department_wise','Department Wise')], 'Header Group By', required=False),
            "department_id"             : fields.many2one('hr.department','Department',required=False),
            "department_force"          : fields.many2many("hr.department","hr_department_issue_report_force_rel","hr_department_id","wizard_id","Force Department"),
            "product_force"             : fields.many2many("product.product","product_product_report_force_rel","product_id","wizard_id","Force Product"),
    }
    _defaults = {
        # "sale_type" : "export",
        "start_date": time.strftime("%Y-%m-01"),
        "end_date" : time.strftime("%Y-%m-%d"),
        "header_group_by" : lambda *h:'site_wise',
        #local stores
        # 'location_force':lambda self,cr,uid,context=None:self.pool.get('stock.location').search(cr,uid,[('id','in',[4408,4381,4386,4387,4388,4391,4392,4342,4343,4347,4348,4349,4353,4354,4359,4360,4365,4366,4367,4371,4372,4377,4378,4393,4399,4410,4416,4421,4422,4425,4426,4427,4428,4429,4430,4431,4438,4439,4446,4449,4471,4453,4454,4463,4464,4468,4469,4474,4478,4479,4483,4484,4458,4459,4440,4411,4495,4496,4498,4513,4514,4516,4519,4531,4532,4534,4548,4549,4551,4559,4560,4561,4565,4566,4567,4577,4578,4580,4412,4413])],context=None),
        #import stores
        # 'location_force':lambda self,cr,uid,context=None:self.pool.get('stock.location').search(cr,uid,[('id','in',[4407,4409,4382,4383,4384,4385,4389,4390,4340,4341,4345,4346,4351,4352,4357,4358,4356,4362,4363,4364,4369,4370,4374,4375,4376,4435,4436,4437,4432,4433,4434,4451,4452,4461,4462,4466,4467,4472,4473,4476,4477,4481,4482,4456,4457,4441,4442,4490,4491,4492,4493,4494,4508,4509,4510,4511,4512,4526,4527,4528,4529,4530,4544,4545,4546,4547,4556,4558,4562,4563,4564,4573,4574,4575,4576,4414])],context=None),
        # 'analytic_account_force':lambda self,cr,uid,context=None:self.pool.get('account.analytic.account').search(cr,uid,[('parent_id','in',[123,129,135,118]),('name','not ilike','PANTRY'),('name','not ilike','STATIONERY')],context=None),
        # 'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',5)],context=None),
    }

    def print_report(self, cr, uid, ids, context={}):
        if not context:context={}
        wizard = self.browse(cr,uid,ids,context)[0]
        datas = {
            'ids': context.get('active_ids',[]),
            'model': 'issue.report.wizard',
            'start_date' : wizard.start_date,
            'end_date' : wizard.end_date,
            'goods_type':[x.id for x in wizard.goods_type],
            'location_force':[lf.id for lf in wizard.location_force],
            'analytic_account_force':[aaf.id for aaf in wizard.analytic_account_force],
            'header_group_by':wizard.header_group_by,
            'department_id':wizard.department_id and wizard.department_id.id or False,
            'department_force':[df.id for df in wizard.department_force],
            'product_force':[pf.id for pf in wizard.product_force],
            }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'issue.report',
                'report_type': 'webkit',
                'datas': datas,
                }
issue_report_wizard()