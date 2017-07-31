from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from tools.translate import _
import cStringIO
from datetime import datetime
import netsvc
import tools
import decimal_precision as dp
import logging
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class ReportDelayShipment(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ReportDelayShipment, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_objects' : self._get_object,       
            "get_difference": self._get_difference,
        })

    def _get_object(self,data):
        # obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
        # print "---------",data
        date_start = data['form']['start_date']
        date_end = data['form']['end_date']
        sale_type = data['form']['sale_type']

        # self.cr.execute("select sm.id from stock_move sm \
        #     left join sale_order_line sol on sm.sale_line_id=sol.id \
        #     left join stock_picking sp on sp.id=sm.picking_id \
        #     left join sale_order so on sp.sale_id=sp.id \
        #     where  sp.type='out' and sp.sale_type='"+sale_type+"' and (sm.date>sol.est_delivery_date or sp.date_done > so.max_est_delivery_date) \
        #     and sp.state='done' and ((sm.date>='"+date_start+"' and sm.date<='"+date_end+"') \
        #     or (sp.date_done>='"+date_start+"' and sp.date_done<='"+date_end+"')) order by sm.date,so.id,so.partner_id,sol.id")
        # move_ids = [x[0] for x in self.cr.fetchall()]
        # print "move_ids============",move_ids
        # if move_ids:
        #     obj_data=self.pool.get('stock.move').browse(self.cr,self.uid,move_ids)
        #     return obj_data
        # return []
        self.cr.execute("select max(sm.id) from stock_move sm \
            left join sale_order_line sol on sm.sale_line_id=sol.id \
            left join stock_picking sp on sp.id=sm.picking_id \
            left join sale_order so on sp.sale_id=sp.id \
            where  sp.type='out' and sp.sale_type='"+sale_type+"' and (sm.date>sol.est_delivery_date or sp.date_done > so.max_est_delivery_date) \
            and sp.state='done' and ((sm.date>='"+date_start+"' and sm.date<='"+date_end+"') \
            or (sp.date_done>='"+date_start+"' and sp.date_done<='"+date_end+"')) group by sm.sequence_line,sm.date,so.id,so.partner_id,sol.id \
            order by sm.date,so.id,so.partner_id,sol.id")
        move_ids = [x[0] for x in self.cr.fetchall()]
        # print "move_ids============",move_ids
        if move_ids:
            obj_data=self.pool.get('stock.move').browse(self.cr,self.uid,move_ids)
            return obj_data
        return []
    
    def _get_difference(self,date_start,date_end):
        if date_start and date_end:
            try:
                date_start=datetime.strptime(date_start,'%Y-%m-%d')
            except:
                date_start=datetime.strptime(date_start,'%Y-%m-%d %H:%M:%S')
            try:
                date_end=datetime.strptime(date_end,'%Y-%m-%d')
            except:
                date_end=datetime.strptime(date_end,'%Y-%m-%d %H:%M:%S')
            date_difference=date_end-date_start
            return date_difference.days>0 and date_difference.days or ''
        return ""
report_sxw.report_sxw('report.delay.shipment.report','delay.shipment.wizard', 'addons/reporting_module/delay_shipment/delay_shipment.mako', parser=ReportDelayShipment)



class delay_shipment_xls(report_xls):
    no_ind = 0
    def get_no_index(self):
        self.set_no_index()
        return self.no_ind
    def set_no_index(self):
        self.no_ind += 1
        return True

    def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context = {}
        context = context.copy()
        rml_parser = self.parser(cr, uid, self.name2, context=context)
        objs = []
        rml_parser.set_context(objs, data, ids, 'xls')
        n = cStringIO.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')
        self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
        wb.save(n)
        n.seek(0)
        return (n.read(), 'xls')
        
    def generate_xls_report(self, parser, data, obj, wb):
        c = parser.localcontext['company']
        i=0
        ws = wb.add_sheet('Delayed Shipment',cell_overwrite_ok=True)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.preview_magn = 60
        ws.normal_magn = 60
        ws.print_scaling=60
        ws.page_preview = False
        ws.set_fit_width_to_pages(1)

        title_style  = xlwt.easyxf('font: height 280, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
        normal_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
        normal_style_float = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz center ;',num_format_str='#,##0.00;-#,##0.00')
        normal_style_float_bold = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center',num_format_str='#,##0.00;-#,##0.00')
        normal_bold_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
        normal_bold_style_a = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
        normal_bold_style_b = xlwt.easyxf('font: height 200, name Calibri, colour_index white, bold on;pattern: pattern solid, pattern_back_colour black; align: wrap on, vert centre, horiz right; ')
        th_top_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
        th_both_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
        th_bottom_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
        group_style  = xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
        normal_style_round_null = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz center ;',num_format_str='#,##0;-#,##0')

        date_start = datetime.strptime(data['form']['start_date'],"%Y-%m-%d").strftime("%d/%m/%Y")
        date_end = datetime.strptime(data['form']['end_date'],"%Y-%m-%d").strftime("%d/%m/%Y")

        ws.write_merge(0,0,0,11, "PT. BITRATEX INDUSTRIES", title_style)
        ws.write_merge(1,1,0,11, " DELAYED SHIPMENT FROM " +date_start+ " TO " +date_end, title_style)
        ws.write_merge(3,4,0,1, "ITEM CODE", normal_style_float_bold)
        ws.write_merge(3,4,2,2, "DESCRIPTION", normal_style)
        ws.write(3,3, "CONTRACT", normal_bold_style)
        ws.write(4,3, "NO.", normal_bold_style)
        ws.write_merge(3,4,4,4, "CUSTOMER", normal_style_float_bold)
        ws.write_merge(3,3,5,6, "L/C", normal_style_float_bold)
        ws.write(4,5, "BATCH", normal_style_float_bold)
        ws.write(4,6, "NO.", normal_style_float_bold)
        ws.write_merge(3,3,7,9, "DELIVERY DATES AS PER", normal_style_float_bold)
        ws.write(4,7, "CONTRACT", normal_style_float_bold)
        ws.write(4,8, "L/C", normal_style_float_bold)
        ws.write(4,9, "SHIPPED", normal_style_float_bold)
        ws.write_merge(3,3,10,11, "DELAY AS PER", normal_style_float_bold)
        ws.write(4,10, "CONTRACT", normal_style_float_bold)
        ws.write(4,11, "L/C", normal_style_float_bold)
        ws.write_merge(3,4,12,12, "Reason", normal_style_float_bold)
        # ws.write_merge(3,4,13,13, "REASON CODE", normal_style_float_bold)
        # ws.write_merge(3,4,14,15, "REMARKS", normal_style_float_bold)






        max_widht_col_0 = len('UNIT')
        max_widht_col_1 =  len('ITEM CODE')
        max_widht_col_2 = len('DESCRIPTION')
        max_widht_col_3 = len('CONTRACT')
        max_widht_col_4 = len('CONTRACT')
        max_widht_col_5 = len('BATCH')
        max_widht_col_6 = len('BATCH')
        max_widht_col_7 = len('CONTRACT')
        max_widht_col_9 = len('SHIPPED')
        max_widht_col_9 = len('CONTRACT')
        rowcount=5
        # for o in parser._get_object(data):
        #     diff_contract=parser._get_difference(o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date,o.date or o.picking_id.date_done)
        #     diff_lc=parser._get_difference (o.lc_product_line_id.est_delivery_date,o.date or o.picking_id.date_done)
        #     print "****************",diff_lc
        #     if not diff_lc and data['form']['sale_type']=='export':
        #         continue
        #     date_shipped=datetime.strptime(o.date or o.picking_id.date_done, '%Y-%m-%d %H:%M:%S')
        #     date_shipped=datetime.strftime(date_shipped, '%d/%m/%Y')
        #     date_contract=datetime.strptime(o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date, '%Y-%m-%d')
        #     date_contract=datetime.strftime(date_contract, '%d/%m/%Y')
        #     ws.write(rowcount,0,o.product_id.default_code or '',normal_style)
        #     ws.write(rowcount,1,o.product_id.name or '',normal_style)
        #     if len(o.product_id.name or '')>max_widht_col_1:
        #         max_widht_col_1 = len(o.product_id.name)
        #     ws.write(rowcount,2,o.sale_line_id.order_id.name or '',normal_style)
        #     if len(o.sale_line_id.order_id.name or '')>max_widht_col_2:
        #         max_widht_col_2 = len(o.sale_line_id.order_id.name)
        #     ws.write(rowcount,3,o.sale_line_id.order_id.partner_id.name  or '',normal_style)
        #     if len(o.sale_line_id.order_id.partner_id.name or '')>max_widht_col_3:
        #         max_widht_col_3 = len(o.sale_line_id.order_id.partner_id.name)
        #     ws.write(rowcount,4,o.lc_product_line_id and o.lc_product_line_id.lc_id and o.lc_product_line_id.lc_id.name or '',normal_style)
        #     ws.write(rowcount,5,o.lc_product_line_id and o.lc_product_line_id.lc_id and o.lc_product_line_id.lc_id.lc_number or '',normal_style)
        #     ws.write(rowcount,6,date_contract,normal_style)
        #     if len(date_contract)>max_widht_col_6:
        #         max_widht_col_6 = len(date_contract)
        #     ws.write(rowcount,7,o.lc_product_line_id.est_delivery_date or '',normal_style)
        #     ws.write(rowcount,8,date_shipped, normal_style)
        #     if len(date_shipped)>max_widht_col_8:
        #         max_widht_col_8 = len(date_shipped)
        #     ws.write(rowcount,9, diff_contract,normal_style_float)
        #     ws.write(rowcount,10,diff_lc ,normal_style_float)
        #     ws.write(rowcount,11,'',normal_style)
        #     # ws.write(rowcount,12,'',normal_style)
        #     # ws.write(rowcount,13,'',normal_style)
        #     rowcount+=1
        result_grouped={}
        for o in parser._get_object(data):
            # diff_contract=parser._get_difference(o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date,o.date or o.picking_id.date_done)
            # diff_lc=parser._get_difference (o.lc_product_line_id.est_delivery_date,o.date or o.picking_id.date_done)
            # # print "****************",diff_lc
            # if not diff_lc and data['form']['sale_type']=='export':
            #     continue
            # date_shipped=datetime.strptime(o.date or o.picking_id.date_done, '%Y-%m-%d %H:%M:%S')
            # date_shipped=datetime.strftime(date_shipped, '%d/%m/%Y')
            # date_contract=datetime.strptime(o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date, '%Y-%m-%d')
            # date_contract=datetime.strftime(date_contract, '%d/%m/%Y')

            key1_loc=o.product_id.property_stock_production.name
            # print key1_loc,"hahahahahhahahahahaha"
            if key1_loc not in result_grouped:
                result_grouped.update({key1_loc:[]})
            result_grouped[key1_loc].append(o)

        for key_loc in sorted(result_grouped.keys(),key=lambda l:l):
            ws.write_merge(rowcount,rowcount,0,12,key_loc or '',group_style)
            if len(key_loc or '')>max_widht_col_0:
                max_widht_col_0=len(key_loc)
            rowcount+=1
            lines=sorted(result_grouped[key_loc],key=lambda x:x.id)
            for line in lines:
                diff_contract=parser._get_difference(line.sale_line_id.est_delivery_date or line.sale_line_id.order_id.max_est_delivery_date,line.date or line.picking_id.date_done)
                diff_lc=parser._get_difference (line.lc_product_line_id.est_delivery_date,line.date or line.picking_id.date_done)
                
                # print "****************",diff_lc
                if not diff_lc and data['form']['sale_type']=='export':
                    continue
                date_shipped=datetime.strptime(line.date or line.picking_id.date_done, '%Y-%m-%d %H:%M:%S')
                date_shipped=datetime.strftime(date_shipped, '%d/%m/%Y')
                date_contract=datetime.strptime(line.sale_line_id.est_delivery_date or line.sale_line_id.order_id.max_est_delivery_date, '%Y-%m-%d')
                date_contract=datetime.strftime(date_contract, '%d/%m/%Y')
                delivery_date=datetime.strptime(line.lc_product_line_id.est_delivery_date,"%Y-%m-%d").strftime("%d/%m/%Y")
                # delivery_date=datetime.strftime(line.lc_product_line_id.est_delivery_date or '', '%d/%m/%Y')

                ws.write(rowcount,1,line.product_id.default_code or '',normal_style)
                ws.write(rowcount,2,line.product_id.name or '',normal_style)
                if len(line.product_id.name or '')>max_widht_col_2:
                    max_widht_col_2 = len(line.product_id.name)
                # ws.write(rowcount,3,line.sale_line_id.order_id.name or '',normal_style)
                # if len(line.sale_line_id.order_id.name or '')>max_widht_col_3:
                ws.write(rowcount,3,line.sale_line_id.sequence_line or '',normal_style)
                if len(line.sale_line_id.sequence_line or '')>max_widht_col_3:
                    max_widht_col_3 = len(line.sale_line_id.sequence_line)
                ws.write(rowcount,4,line.sale_line_id.order_id.partner_id.name  or '',normal_style)
                if len(line.sale_line_id.order_id.partner_id.name or '')>max_widht_col_4:
                    max_widht_col_4 = len(line.sale_line_id.order_id.partner_id.name)
                ws.write(rowcount,5,line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.name or '',normal_style)
                if len(line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.name or '')>max_widht_col_5:
                    max_widht_col_5 =len(line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.name)
                ws.write(rowcount,6,line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.lc_number or '',normal_style)
                if len(line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.lc_number or '')>max_widht_col_6:
                    max_widht_col_6 =len(line.lc_product_line_id and line.lc_product_line_id.lc_id and line.lc_product_line_id.lc_id.lc_number)
                ws.write(rowcount,7,date_contract,normal_style)
                if len(date_contract)>max_widht_col_7:
                    max_widht_col_7 = len(date_contract)
                ws.write(rowcount,8,delivery_date,normal_style)
                ws.write(rowcount,9,date_shipped, normal_style)
                if len(date_shipped)>max_widht_col_9:
                    max_widht_col_9 = len(date_shipped)
                ws.write(rowcount,10, diff_contract,normal_style_round_null)
                ws.write(rowcount,11, diff_lc ,normal_style_round_null)
                ws.write(rowcount,12,'',normal_style)
                ws.write(rowcount,13,'',normal_style)
                ws.write(rowcount,14,'',normal_style)
                rowcount+=1

        ws.col(0).width = 256 * int(max_widht_col_0*1.4)
        ws.col(1).width = 256 * int(max_widht_col_1*1.4)
        ws.col(2).width = 256 * int(max_widht_col_2*1.4)
        ws.col(3).width = 256 * int(max_widht_col_3*1.4)
        ws.col(4).width = 256 * int(max_widht_col_4*1.4)
        ws.col(5).width = 256 * int(max_widht_col_5*1.4)
        ws.col(6).width = 256 * int(max_widht_col_6*1.4)
        ws.col(7).width = 256 * int(max_widht_col_7*1.4)
        ws.col(9).width = 256 * int(max_widht_col_9*1.4)
        # ws.col(9).width = 256 * int(max_widht_col_9*1.4)

        pass
#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
delay_shipment_xls('report.xls.delay.shipment.report','delay.shipment.wizard', 'addons/reporting_module/delay_shipment/delay_shipment.mako',
                        parser=ReportDelayShipment)