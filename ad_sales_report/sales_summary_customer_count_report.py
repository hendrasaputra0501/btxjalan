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

class report_sales_summary_customer_count(osv.osv_memory):
    _name="report.sales.summary.customer.count.wizard"
    _columns={
        "report_type"	: 	fields.selection([('customer','Customer'),('product','Product')],'Report Type',required=True),
		"goods_type"	:	fields.selection([('finish','Finish Good'),('raw','Raw Material')], 'Goods Type', required=True),
		"sale_type"		:	fields.selection([('export','Export'),('local','Local'),('all','All')],'Sale Type', required=True),
		"period_id"     : 	fields.many2one('account.fiscalyear','Period Year'),
		"filter"        : 	fields.selection([('filter_no', 'No Filters'),('filter_cust', 'Customer'),('filter_prod', 'Product')],"Filter by",required=True),
        "partner_id"    : 	fields.many2many("res.partner",'partner_id_sales_summary_customercount_report_rel','partner_id','wizard_id','Customer'),
        "product_id"    : 	fields.many2many("product.product",'product_id_sales_summary_customercount_report_rel','product_id','wizard_id','Product'),
        "file_type"     : 	fields.selection([('pdf','PDF'),('excel','Excel')],"File type",required=True),
        "filter_date"   :   fields.selection([('period', 'Period'),('from_to','Date From-To')], "Filter Date", required=True),
        "date_from"     :   fields.date('Date From'),
        "date_to"       :   fields.date('Date To'),
        }

    _defaults ={
        "report_type"       : 'customer',
        "goods_type"        : 'finish',
        "sale_type"         : 'export',
        "filter"            : 'filter_no',
        "partner_id"        : False,
        "product_id"        : False,
        "file_type"         : lambda *a:'excel',
        "filter_date"       : 'period',
        }

    
    def print_report(self, cr, uid, ids, context={}):
        form = self.read(cr, uid, ids)[0]
        datas = {
            'ids': context.get('active_ids',[]),
            'model': 'report.sales.summary.customer.count.wizard',
            'form': self.read(cr, uid, ids)[0],
        }

        if form.get('file_type','pdf')=='pdf':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'sales.summary.customer.count.report',
                'report_type': 'webkit',
                'datas': datas,
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'xls.sales.summary.customer.count.report',
                'report_type': 'webkit',
                'datas': datas,
            }
            # print "wewewewewewewewewewew"


    def onchange_filter(self, cr, uid, ids, filter='filter_no', context=None):
        res = {'value': {}}
        # if filter == 'filter_no':
        #     res['value'] = {'partner_id': False,'product_id': False}
        # elif filter == 'filter_cust':
        #     res['value'] = {'product_id': False}
        # if filter == 'filter_prod':
        #     res['value'] = {'partner_id': False}
        # if filter =='filter_agent':
        #     res['value']={'agent_id': False}
        if filter == 'filter_no':
            res['value'] = {'partner_id': False,'product_id': False}
        elif filter == 'filter_cust':
            res['value'] = {'partner_id': False}
        if filter == 'filter_prod':
            res['value'] = {'product_id': False}
        # print res, "hahahahahahaha"
        return res

    def onchange_filter_date(self, cr, uid, ids, filter_date='period', context=None):
        res={'value': {}}
        if filter_date=='period':
            res['value'] = {'date_from': False, 'date_to': False}
        elif filter_date=='from_to':
            res['value']={'period_id':False}
        return res