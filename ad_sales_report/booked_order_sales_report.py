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

class report_booked_order_sales(osv.osv_memory):
    _name = "report.booked.order.sales.wizard"
    _columns = {
            "report_type"       : fields.selection([('product','Product Wise'),('customer','Customer Wise'),('date','Date Wise')],'Report Type',required=True),
            "goods_type"        : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "locale_sale_type"  : fields.selection([('%','All'),('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
            "date_from"         : fields.date('Date From',required=True),
            "date_to"           : fields.date('Date To',required=True),
            "currency_id"       : fields.many2one('res.currency','Currency'),
            "filter"            : fields.selection([('filter_no', 'No Filters'), ('filter_cust', 'Customer')], "Filter by", required=True),
            "partner_id"        : fields.many2many("res.partner",'partner_id_booked_sales_report_rel','partner_id','wizard_id','Customer'),
    }     
    _defaults ={
                'report_type'       : 'customer',
                'goods_type'        : 'finish',
                'sale_type'         : 'export',
                'date_from'         : lambda *a:time.strftime("%Y-%m-01"),
                'date_to'           : lambda *a:time.strftime("%Y-%m-%d"),
                'locale_sale_type'  : '%',
                'currency_id'       : '3',
                "filter"            : 'filter_no',
                "partner_id"        : False,
                }
    def compute_report(self, cr, uid, ids, context={}):
        datas = {
                'ids': context.get('active_ids',[]),
                'model': 'report.booked.order.sales.wizard',
                'form': self.read(cr, uid, ids)[0],
                }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'booked.order.sales.report',
                'report_type': 'webkit',
                'datas': datas,
                }
    def onchange_filter(self, cr, uid, ids, filter='filter_no', context=None):
        res = {'value': {}}
        if filter == 'filter_no':
            res['value'] = {'partner_id': False}

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

report_booked_order_sales()