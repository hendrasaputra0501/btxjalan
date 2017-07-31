

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

class report_sales_summary(osv.osv_memory):
    _name = "report.sales.summary.wizard"
    _columns = {
            "report_type"       : fields.selection([('product','Product Wise'),('customer','Customer Wise'),('date','Date Wise'),('country','Country Wise')],'Report Type',required=True),
            "goods_type"        : fields.selection([('finish','Finish Goods'),('finish_others','Finish Goods Other'),('raw','Raw Material'),('service','Services'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type',required=True),
            "sale_type"         : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
            "locale_sale_type"  : fields.selection([('%','All'),('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type",required=False),
            "usage"             : fields.selection([('customer',"Delivery"),('internal',"Return")],"Document Type",required=True),
            "date_from"         : fields.date('Date From',required=True),
            "date_to"           : fields.date('Date To',required=True),
            "week_detail"       : fields.boolean('With Week Detail'),
            "def_uom"           : fields.many2one('product.uom','Reference UOM'),
            "currency_id"       : fields.many2one('res.currency','Currency')
    } 
    
    def get_default_uom(self,cr,uid,context=None):
        if not context:context={}
        uom_categ_id = self.pool.get("product.uom.categ").search(cr,uid,[('name','=','Bitratex Weight')],context=context)
        uom_id =False
        if uom_categ_id:
            try:
                uom_categ_id = uom_categ_id[0]
            except:
                uom_categ_id = uom_categ_id
            if uom_categ_id:
                uom_id = self.pool.get("product.uom").search(cr,uid,[('name','=','BALES'),('category_id','=',uom_categ_id)],context=context)

        return uom_id
    _defaults ={
                'report_type'       : 'customer',
                'goods_type'        : 'finish',
                'sale_type'         : 'export',
                'date_from'         : lambda *a:time.strftime("%Y-%m-01"),
                'date_to'           : lambda *a:time.strftime("%Y-%m-%d"),
                'def_uom'           : 473,
                'locale_sale_type'  : '%',
                'currency_id'       : '3',
                'usage'             : lambda *a:'customer',
                }
    def compute_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'report.sales.summary.wizard',
             'form': self.read(cr, uid, ids)[0],
                 }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'sales.summary.report',
                'report_type': 'webkit',
                'datas': datas,
                }
report_sales_summary()