

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

class report_pending_sales(osv.osv_memory):
    def _get_partner_type(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            typ = ''
            if rec.sale_type == 'export':
                typ = 'overseas'
            else:
                typ = 'local'
            res[rec.id] = typ
        return res

    _name = "report.pending.sales.wizard"
    _columns = {
            "report_type"       : fields.selection([('product','Product Wise'),('customer','Customer Wise'),('contract','Contract Wise')],'Report Type',required=True),
            "file_type"         : fields.selection([('pdf','PDF'),('excel','Excel')],"File type",required=True),
            "goods_type"        : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "as_on"             : fields.date('As On',required=True),
            "locale_sale_type"  : fields.selection([('%','All'),('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
            "filter"            : fields.selection([('filter_no', 'No Filters'), ('filter_cust', 'Customer'),('currency', 'Currency'),('product', 'Product')], "Filter by", required=True),
            "partner_id"        : fields.many2many("res.partner",'partner_id_pending_sales_report_rel','partner_id','wizard_id','Customer'),
            "partner_type"      : fields.function(_get_partner_type,string='Partner Type',method=True,type='char',size=10),
            "currency_ids"      : fields.many2many("res.currency",'curr_id_pending_sales_report_rel','currency_id','wizard_id','Currencies'),
            "product_id"        : fields.many2many("product.product",'product_id_pending_sales_report_rel','product_id','wizard_id','Product'),
    } 

    _defaults ={
            "report_type"       : lambda *a:'product',
            "file_type"         : lambda *a:'excel',
            "goods_type"        : lambda *a:'finish',
            "sale_type"         : lambda *a:'export',
            "as_on"             : lambda *a:time.strftime("%Y-%m-%d"),
            "locale_sale_type"  : lambda *a:'%',
            "filter"            : lambda *a:'filter_no',
            "partner_id"        : lambda *a:False,
            "currency_ids"      : lambda *a:False,
            "product_id"        : lambda *a:False,
            }

    def print_report(self, cr, uid, ids, context={}):
        form = self.read(cr, uid, ids)[0]
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'report.pending.sales.wizard',
             'form': form,
                 }
        print "---------------",form
        if form.get('file_type','pdf')=='pdf':
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'pending.sales.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }
        else:
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'excel.pending.sales.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }

    def onchange_filter(self, cr, uid, ids, filter='filter_no', context=None):
        res = {'value': {}}
        if filter == 'filter_no':
            res['value'] = {'partner_id': False}
            res['value'] = {'currency_ids': False}
            res['value'] = {'product_ids': False}
        return res

    def onchange_sale_type(self, cr, uid, ids, sale_type='export', context=None):
        res = {'value': {}}
        if sale_type == 'export':
            res = {'value': {'partner_type':'overseas'}}
        else:
            res = {'value': {'partner_type':'local'}}

        return res

    def get_domain_partner_id(self, cr, uid, ids, sale_type='export', context=None):
        s = "select distinct partner_id from sale_order where sale_type = '" +sale_type+"'"
        cr.execute(s,)
        lids=cr.fetchall()
        return {'domain':{'partner_id':[('id','in',lids)]}}

    def get_domain_product_id(self, cr, uid, ids, sale_type='export', context=None):
        s = "select distinct product_id from sale_order_line where sale_type = '" +sale_type+"'"
        cr.execute(s,)
        lids=cr.fetchall()
        return {'domain':{'product_id':[('id','in',lids)]}}

report_pending_sales()