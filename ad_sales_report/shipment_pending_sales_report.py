

import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class report_shipment_pending_sales(osv.osv_memory):
    _name = "report.shipment.pending.sales.wizard"
    _columns = {
            "goods_type"        : fields.selection([('Finish','Finish Goods'),('Raw','Raw Material'),('Service','Services'),('Waste','Waste'),('Scrap','Scrap'),('Asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "locale_sale_type"  : fields.selection([('%','All'),('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
            "date_from"         : fields.date('From Date',required=True),
            "date_to"           : fields.date('To Date',required=True),
            "filter"            : fields.selection([('filter_no', 'No Filters'),('filter_cust', 'Customer'),('filter_prod', 'Product'),('filter_agent', 'Agent')],"Filter by",required=True),
            "partner_id"        : fields.many2many("res.partner",'partner_id_shipment_pending_sales_report_rel','partner_id','wizard_id','Customer'),
            "product_id"        : fields.many2many("product.product",'product_id_shipment_pending_sales_report_rel','product_id','wizard_id','Product'),
            "agent_id"          : fields.many2many("res.partner",'agent_id_shipment_pending_sales_report_rel','agent_id','wizard_id','Customer'),
            'agent'             : fields.boolean('Group By Agent'),
            "file_type"         : fields.selection([('pdf','PDF'),('excel','Excel')],"File type",required=True),
    } 

    _defaults ={
            "goods_type"        : 'Finish',
            "sale_type"         : 'export',
            "locale_sale_type"  : '%',
            "date_from"         : lambda *a:time.strftime("%Y-%m-01"),
            "date_to"           : lambda *a:time.strftime("%Y-%m-%d"),
            "filter"            : 'filter_no',
            "partner_id"        : False,
            "product_id"        : False,
            "agent_id"          : False,
            "file_type"         : lambda *a:'pdf'
            }

    def print_report(self, cr, uid, ids, context={}):
        form = self.read(cr, uid, ids)[0]
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'report.shipment.pending.sales.wizard',
             'form': self.read(cr, uid, ids)[0],
                 }
        # return {
        #         'type': 'ir.actions.report.xml',
        #         'report_name': 'shipment.pending.sales.report',
        #         'report_type': 'webkit',
        #         'datas': datas,
        #         }

        if form.get('file_type','pdf')=='pdf':
            # print "wawawawawawawawawawawawawawawa"
            if form.get('filter','filter_agent')=='filter_agent' or form.get('agent','True'):
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'shipment.pending.agent.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }
            else:
                return {
                    'type': 'ir.actions.report.xml',
                    'report_type': 'webkit',
                    'report_name': 'shipment.pending.sales.report',
                    'datas': datas,
                    }

        else:
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'xls.shipment.pending.sales.report',
                    'report_type': 'webkit',
                    'datas': datas,
                    }
            print "wewewewewewewewewewew"

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
            res['value'] = {'partner_id': False,'product_id': False,'agent_id': False}
        elif filter == 'filter_cust':
            res['value'] = {'partner_id': False}
        if filter == 'filter_prod':
            res['value'] = {'product_id': False}
        if filter =='filter_agent':
            res['value']={'agent_id': False}
        print res, "hahahahahahaha"
        return res

    def get_domain_partner_id(self, cr, uid, ids, sale_type='export', context=None):
        s = "select distinct partner_id from sale_order where sale_type = '" +sale_type+"'"
        cr.execute(s,)
        lids=cr.fetchall()
        return {'domain':{'partner_id':[('id','in',lids)]}}

    def get_domain_product_id(self, cr, uid, ids, goods_type='finish', context=None):
        return {'domain':{'product_id':[('internal_type','=',goods_type)]}}

    def get_domain_agent_id(self, cr, uid, ids, sale_type='export', context=None):
        s = "select distinct partner_id from sale_order where sale_type = '" +sale_type+"'"
        cr.execute(s,)
        lids=cr.fetchall()
        return {'domain':{'agent_id':[('id','in',lids)]}}




report_shipment_pending_sales()