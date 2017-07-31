from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging
import cStringIO
import xlwt
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from ad_account_optimization.report.report_engine_xls import report_xls

class sales_summary_customer_count_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(sales_summary_customer_count_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_view'  : self._get_view,
        })

    def _get_view(self,data,context=None):
    	report_type = 	data['form']['report_type']
        # print data['form']['period_id'][1],"cacacacacacacacacacaca"
        goods_type	=	data['form']['goods_type']
        sale_type	=	data['form']['sale_type']
        # period_id    = 	data['form']['period_id'][1]
        filter_date = data['form']['filter_date']
        print filter_date,"mamamamamamamamamamamama"
        if filter_date=='period':
            period_id    =  data['form']['period_id'][1]
            s1=" and to_char(sp.date_done,'YYYY') =substring('%s',1,4)"
            # date_type=data['form']['period_id'][1]
        elif filter_date=='from_to':
            date_from=data['form']['date_from']
            date_to=data['form']['date_to']
            s1=" and to_char(sp.date_done,'YYYY-MM-DD') >=substring('%s',1,10) and to_char(sp.date_done,'YYYY-MM-DD') <=substring('%s',1,10)"
            print date_from,"zazazazazazazazazazazazazazazazazazaz"
            # date_type= date_from +" TO " + date_to
        if sale_type=='all':
            sale="('local','export')"
        else:
            sale="('"+sale_type+"')"
        # print period_id,"jajajajajajajjajjajajajjajjajja"
        # "filter"        : 	fields.selection([('filter_no', 'No Filters'),('filter_cust', 'Customer'),('filter_prod', 'Product')],"Filter by",required=True),
        #       "partner_id"    : 	fields.many2many("res.partner",'partner_id_sales_summary_customercount_report_rel','partner_id','wizard_id','Customer'),
        #       "product_id"    : 	fields.many2many("product.product",'product_id_sales_summary_customercount_report_rel','product_id','wizard_id','Product'),
        #       "file_type"     : 	fields.selection([('pdf','PDF'),('excel','Excel')],"File type",required=True),
        s="select sp.sale_type as sale_type,\
        substring(rp.name,1,25) as customer, \
        rp.id as customer_id,\
        stcrc.country_name, \
        rc.name as country ,\
        sp.destination_country, \
        pp.name_template , \
        to_char(sp.date_done,'mm') as month, \
        pp.id as product_id, \
        sm.partner_id as partner_id, \
        product_qty, \
        pu.name as uom, \
        sm.id as stockmove_id, \
        case when pu.name='BALES' and sp.type='out' \
        then coalesce(sm.product_qty,0.00) \
        when pu.name='KGS'and sp.type='out' \
        then coalesce(sm.product_qty/181.44000,0.0,0.00) \
        when pu.name='LBS' and sp.type='out' \
        then coalesce(sm.product_qty/400,00) \
        \
        when pu.name='BALES' and sp.type='in' \
        then -coalesce(sm.product_qty,0.00) \
        when pu.name='KGS'and sp.type='in' \
        then -coalesce(sm.product_qty/181.44000,0.0,0.00) \
        when pu.name='LBS' and sp.type='in' \
        then -coalesce(sm.product_qty/400,00) \
        end as qty_bales \
        from stock_picking sp \
        inner join stock_move sm on sp.id=sm.picking_id \
        left join res_partner rp on sp.partner_id=rp.id \
        left join product_product pp on sm.product_id=pp.id \
        left join product_uom pu on sm.product_uom=pu.id \
        left join res_country rc on rp.country_id=rc.id \
        left join(select rc.name as country_name,stc.id as stc_id from stock_transporter_charge stc \
        left join res_country rc on stc.country_id=rc.id) stcrc on sp.forwading_charge=stcrc.stc_id \
        where sp.state='done' and sm.state='done' \
        and coalesce(sp.sale_id,0) <> 0 \
        and sp.goods_type = lower('%s') \
        and sp.sale_type in %s \
        "
        # and sm.partner_id='10038' \
        # and sm.product_id in (2217,1782)\
        # and to_char(sp.date_done,'mm')='01'\

        # s="select distinct pp.name_template , \
        # sm.product_id as product_id,\
        # rp.name as customer \
        # from stock_picking sp \
        # inner join stock_move sm on sp.id=sm.picking_id \
        # left join res_partner rp on sp.partner_id=rp.id \
        # left join product_product pp on sm.product_id=pp.id \
        # left outer join product_uom pu on sm.product_uom=pu.id \
        # where sp.state='done' and sm.state='done' \
        # and to_char(sp.date_done,'YYYY') =substring('%s',1,4) \
        # and coalesce(sp.sale_id,0) <> 0 \
        # and sp.goods_type = lower('%s') \
        # and sp.sale_type = '%s' \
        # "
        spartner = ''
        if data['form']['filter'] == 'filter_cust':
            for pid in data['form']['partner_id']:
                if spartner == '':
                    spartner = str(pid)
                else:
                    spartner += ','+str(pid)

        sproduct=''
        if data['form']['filter']=='filter_prod':
            for pid in data['form']['product_id']:
                if sproduct=='':
                    sproduct=str(pid)
                else:
                    sproduct+=','+str(pid)

        if data['form']['filter'] == 'filter_cust':
            s +=s1+" and sp.partner_id in("+spartner+") \
                 "
        if data['form']['filter'] == 'filter_prod':
            s+=s1+"and sm.product_id in("+sproduct+") \
        "
        if data['form']['filter']=='filter_no':
            s+=s1+"order by substring(rp.name,1,25),pp.name_template"
        else:
            s+="order by substring(rp.name,1,25),pp.name_template"

        print spartner,"xaxaxaxaxxzzaaaaaa"
                # query = s%(period_id,goods_type,sale_type)
        if data['form']['filter_date']=='period': 
            query = s%(goods_type,sale,period_id)
        elif data['form']['filter_date']=='from_to':
            query = s%(goods_type,sale,date_from,date_to)
        self.cr.execute(query)
        res = self.cr.dictfetchall()
        # for x in res:
            # print x,"glalalalalalalalalalalalalala"
        return res

report_sxw.report_sxw('report.sales.summary.customer.count.report','report.sales.summary.customer.count.wizard', 'addons/ad_purchases_report/pending_purchase_order_report.mako',parser=sales_summary_customer_count_parser)

class sales_summary_customer_count_xls(report_xls):
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

    def get_totqty_customer_count_per_month(self,stockmove_id,customer_id,product_id,month):
        cr=self.cr
        uid=self.uid
        context=None
        qty_tot=0.00
        stock_move_obj=self.pool.get('stock.move')
        stock_move_ids

    def generate_xls_report(self, parser, data, obj, wb):
        c = parser.localcontext['company']
        i=0
        ws = wb.add_sheet('Sales Summary Customer Count',cell_overwrite_ok=True)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.preview_magn = 60
        ws.normal_magn = 60
        ws.print_scaling=60
        ws.page_preview = False
        ws.set_fit_width_to_pages(1)
        pending_purchase_data = parser._get_view(data)

        title_style  = xlwt.easyxf('font: height 280, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
        normal_style = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
        normal_style_float = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz center ;',num_format_str='#,##0.00;-#,##0.00')
        # normal_style_float_r = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz right ;',num_format_str='#,##0.00;-#,##0.00')
        normal_style_float_r = xlwt.easyxf('font: height 200, name Calibri, colour_index black; align: wrap on, vert centre, horiz right ;',num_format_str='#,##0;-#,##0')
        # normal_bold_float_r = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right ;',num_format_str='#,##0.00;-#,##0.00')
        normal_bold_float_r = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right ;',num_format_str='#,##0;-#,##0')
        normal_style_float_bold_border_top = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center;border:top thick;' ,num_format_str='#,##0.00;-#,##0.00')
        normal_style_float_bold_border_bottom = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center;border:bottom thick;' ,num_format_str='#,##0.00;-#,##0.00')
        normal_bold_style_cen = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        normal_bold_style_right = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right; pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        normal_bold_style_a = xlwt.easyxf('font: height 200, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
        normal_bold_style_b = xlwt.easyxf('font: height 200, name Calibri, colour_index white, bold on;pattern: pattern solid, pattern_back_colour black; align: wrap on, vert centre, horiz right; ')
        th_top_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
        th_both_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
        th_bottom_style = xlwt.easyxf('font: height 220, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
        group_style  = xlwt.easyxf('font: name Calibri, colour_index black, bold on, italic on; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
        group_style_grand=xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
        # group_style_cen_grand=xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
        group_style_cen_grand=xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
        # group_style_right  = xlwt.easyxf('font: name Calibri, colour_index black, bold on, italic on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
        group_style_right  = xlwt.easyxf('font: name Calibri, colour_index black, bold on, italic on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0;(#,##0)')
        # group_style_right_grand=xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        group_style_right_grand=xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern:pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0;(#,##0)')
        # number_style= xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        number_style= xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz centre;')
        group_style_white  =  xlwt.easyxf('font: name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
        # title_style  = xlwt.easyxf(colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
        # period_id     =   data['form']['period_id'][1]
        if data['form']['period_id']:
            date_type=data['form']['period_id'][1]
        else:
            date_from=data['form']['date_from']
            date_to=data['form']['date_to']
            date_type= date_from +" TO " + date_to

        ws.write_merge(0,0,0,15, "PT. BITRATEX INDUSTRIES", title_style)
        sale_type   =   data['form']['sale_type']
        if sale_type=="all":
            ws.write_merge(1,1,0,15, "SHIPMENT STATUS - COUNT WISE - " +period_id , title_style)
        else:
            ws.write_merge(1,1,0,15, sale_type.upper() +" SHIPMENT STATUS - COUNT WISE - " +date_type , title_style)
        ws.write(2,15,"(in Bales)",normal_bold_style_right)
        ws.write(3,0,"No.",normal_bold_style_cen)
        ws.write(3,1,"Customer Name",normal_bold_style_cen)
        ws.write(3,2,"Country",normal_bold_style_cen)        

        ws.write(3,3,"Jan",normal_bold_style_right)
        ws.write(3,4,"Peb",normal_bold_style_right)
        ws.write(3,5,"Mar",normal_bold_style_right)
        ws.write(3,6,"Apr",normal_bold_style_right)
        ws.write(3,7,"Mei",normal_bold_style_right)
        ws.write(3,8,"Jun",normal_bold_style_right)
        ws.write(3,9,"Jul",normal_bold_style_right)
        ws.write(3,10,"Ags",normal_bold_style_right)
        ws.write(3,11,"Sept",normal_bold_style_right)
        ws.write(3,12,"Okt",normal_bold_style_right)
        ws.write(3,13,"Nop",normal_bold_style_right)
        ws.write(3,14,"Des",normal_bold_style_right)
        ws.write(3,15,"Total",normal_bold_style_right)

        max_widt_col0=len('No.')
        max_widt_col1=len('Customer Name')
        max_widt_col2=len('Country')

        row_count=4
        number=1
        result_grouped={}
        for o in pending_purchase_data:
            if data['form']['report_type']=='customer':
                key0_sale_type=(o['sale_type'])
                if key0_sale_type not in result_grouped:
                    result_grouped.update({key0_sale_type:{}})
                key1_cust_or_prod=(o['customer_id'],o['customer'])
                if key1_cust_or_prod not in result_grouped[key0_sale_type]:
                    result_grouped[key0_sale_type].update({key1_cust_or_prod:{}})
                key2_prod_or_cust=(o['product_id'],o['name_template'])
                if key2_prod_or_cust not in result_grouped[key0_sale_type][key1_cust_or_prod]:
                    result_grouped[key0_sale_type][key1_cust_or_prod].update({key2_prod_or_cust:{}})
                key2b_dest=o['country_name']
                if key2b_dest not in result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust]:
                    result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust].update({key2b_dest:{}})
                key3_month=o['month']
                if key3_month not in result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest]:
                    result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest].update({key3_month:[]})
                result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest][key3_month].append(o)
            elif data['form']['report_type']=='product':
                key0_sale_type=(o['sale_type'])
                if key0_sale_type not in result_grouped:
                    result_grouped.update({key0_sale_type:{}})
                key1_cust_or_prod=(o['product_id'],o['name_template'])
                if key1_cust_or_prod not in result_grouped[key0_sale_type]:
                    result_grouped[key0_sale_type].update({key1_cust_or_prod:{}})
                key2_prod_or_cust=(o['customer_id'],o['customer'])
                if key2_prod_or_cust not in result_grouped[key0_sale_type][key1_cust_or_prod]:
                    result_grouped[key0_sale_type][key1_cust_or_prod].update({key2_prod_or_cust:{}})
                key2b_dest=o['country_name']
                if key2b_dest not in result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust]:
                    result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust].update({key2b_dest:{}})
                key3_month=o['month']
                if key3_month not in result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest]:
                    result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest].update({key3_month:[]})
                result_grouped[key0_sale_type][key1_cust_or_prod][key2_prod_or_cust][key2b_dest][key3_month].append(o)

        for key_sale_type in sorted(result_grouped.keys(), key=lambda l:key0_sale_type):
            ws.write_merge(row_count,row_count,0,1, "  " + key_sale_type.upper() or '', group_style_white)
            row_count=row_count+1
            qtygrand_jan=0
            qtygrand_peb=0
            qtygrand_mar=0
            qtygrand_apr=0
            qtygrand_may=0
            qtygrand_jun=0
            qtygrand_jul=0
            qtygrand_ags=0
            qtygrand_sep=0
            qtygrand_okt=0
            qtygrand_nop=0
            qtygrand_dec=0
            for key_1 in sorted(result_grouped[key_sale_type].keys(), key=lambda l:l[1]):
                # print key_1[1],key_1[0],"mamamamamamamamamamamamamamamam"
                ws.write(row_count,0,number,number_style)
                ws.write_merge(row_count,row_count,1,15,  str(key_1[1]) or '',group_style)
                row_count=row_count+1
                number=number+1
                qtysubtot_jan=0
                qtysubtot_peb=0
                qtysubtot_mar=0
                qtysubtot_apr=0
                qtysubtot_may=0
                qtysubtot_jun=0
                qtysubtot_jul=0
                qtysubtot_ags=0
                qtysubtot_sep=0
                qtysubtot_okt=0
                qtysubtot_nop=0
                qtysubtot_dec=0
                for key_2 in sorted(result_grouped[key_sale_type][key_1].keys(), key=lambda l:l[1]):
                    ws.write(row_count,1,key_2[1],normal_style)
                    if len(key_2[1])>max_widt_col1:
                        max_widt_col1=len(key_2[1])
                    for key_dest in sorted(result_grouped[key_sale_type][key_1][key_2].keys(), key=lambda l:key2b_dest):
                        ws.write(row_count,2,key_dest,normal_style)
                        if len(key_dest or '')>max_widt_col2:
                            max_widt_col2=len(key_dest)
                        qtytot01=0
                        qtytot02=0
                        qtytot03=0
                        qtytot04=0
                        qtytot05=0
                        qtytot06=0
                        qtytot07=0
                        qtytot08=0
                        qtytot09=0
                        qtytot10=0
                        qtytot11=0
                        qtytot12=0
                        qtytot13=0
                        for key_month in sorted(result_grouped[key_sale_type][key_1][key_2][key_dest].keys(),key=lambda l:key3_month):
                            lines=sorted(result_grouped[key_sale_type][key_1][key_2][key_dest][key_month],key=lambda x:x['month'])
                            for line in lines:
                                if line['month']=="01":
                                    # qty01=line['qty_bales']
                                    qtytot01+=line['qty_bales']
                                if line['month']=="02":
                                    # qty02=line['qty_bales']
                                    qtytot02+=line['qty_bales']
                                if line['month']=="03":
                                    # qty03=line['qty_bales']
                                    qtytot03+=line['qty_bales']
                                if line['month']=="04":
                                    # qty04=line['qty_bales']
                                    qtytot04+=line['qty_bales']
                                if line['month']=="05":
                                    # qty05=line['qty_bales']
                                    qtytot05+=line['qty_bales']
                                if line['month']=="06":
                                    # qty06=line['qty_bales']
                                    qtytot06+=line['qty_bales']
                                if line['month']=="07":
                                    # qty07=line['qty_bales']
                                    qtytot07+=line['qty_bales']
                                if line['month']=="08":
                                    # qty08=line['qty_bales']
                                    qtytot08+=line['qty_bales']
                                if line['month']=="09":
                                    # qty09=line['qty_bales']
                                    qtytot09+=line['qty_bales']
                                if line['month']=="10":
                                    # qty10=line['qty_bales']
                                    qtytot10+=line['qty_bales']
                                if line['month']=="11":
                                    # qty11=line['qty_bales']
                                    qtytot11+=line['qty_bales']
                                if line['month']=="12":
                                    # qty12=line['qty_bales']
                                    qtytot12+=line['qty_bales']
                            ws.write(row_count,3,qtytot01,normal_style_float_r)
                            ws.write(row_count,4,qtytot02,normal_style_float_r)
                            ws.write(row_count,5,qtytot03,normal_style_float_r)
                            ws.write(row_count,6,qtytot04,normal_style_float_r)
                            ws.write(row_count,7,qtytot05,normal_style_float_r)
                            ws.write(row_count,8,qtytot06,normal_style_float_r)
                            ws.write(row_count,9,qtytot07,normal_style_float_r)
                            ws.write(row_count,10,qtytot08,normal_style_float_r)
                            ws.write(row_count,11,qtytot09,normal_style_float_r)
                            ws.write(row_count,12,qtytot10,normal_style_float_r)
                            ws.write(row_count,13,qtytot11,normal_style_float_r)
                            ws.write(row_count,14,qtytot12,normal_style_float_r)
                            qtytot13=qtytot01+qtytot02+qtytot03+qtytot04+qtytot05+qtytot06+qtytot07+qtytot08+qtytot09+qtytot10+qtytot11+qtytot12
                            ws.write(row_count,15,qtytot13,normal_bold_float_r)
                            if line['month']=="01":
                                qtysubtot_jan+=qtytot01
                            if line['month']=="02":
                                qtysubtot_peb+=qtytot02
                            if line['month']=="03":
                                qtysubtot_mar+=qtytot03
                            if line['month']=="04":
                                qtysubtot_apr+=qtytot04
                            if line['month']=="05":
                                qtysubtot_may+=qtytot05
                            if line['month']=="06":
                                qtysubtot_jun+=qtytot06
                            if line['month']=="07":
                                qtysubtot_jul+=qtytot07
                            if line['month']=="08":
                                qtysubtot_ags+=qtytot08
                            if line['month']=="09":
                                qtysubtot_sep+=qtytot09
                            if line['month']=="10":
                                qtysubtot_okt+=qtytot10
                            if line['month']=="11":
                                qtysubtot_nop+=qtytot11
                            if line['month']=="12":
                                qtysubtot_dec+=qtytot12
                            qtysubtot_13=qtysubtot_jan+qtysubtot_peb+qtysubtot_mar+qtysubtot_apr+qtysubtot_may+qtysubtot_jun+qtysubtot_jul+qtysubtot_ags+qtysubtot_sep+qtysubtot_okt+qtysubtot_nop+qtysubtot_dec
                        row_count=row_count+1
                ws.write_merge(row_count,row_count,0,2,"Sub Total of "+ str(key_1[1]) or '',group_style_right)
                ws.write(row_count,3,qtysubtot_jan,group_style_right)
                ws.write(row_count,4,qtysubtot_peb,group_style_right)
                ws.write(row_count,5,qtysubtot_mar,group_style_right)
                ws.write(row_count,6,qtysubtot_apr,group_style_right)
                ws.write(row_count,7,qtysubtot_may,group_style_right)
                ws.write(row_count,8,qtysubtot_jun,group_style_right)
                ws.write(row_count,9,qtysubtot_jul,group_style_right)
                ws.write(row_count,10,qtysubtot_ags,group_style_right)
                ws.write(row_count,11,qtysubtot_sep,group_style_right)
                ws.write(row_count,12,qtysubtot_okt,group_style_right)
                ws.write(row_count,13,qtysubtot_nop,group_style_right)
                ws.write(row_count,14,qtysubtot_dec,group_style_right)
                ws.write(row_count,15,qtysubtot_13,group_style_right)
                qtygrand_jan+=qtysubtot_jan
                qtygrand_peb+=qtysubtot_peb
                qtygrand_mar+=qtysubtot_mar
                qtygrand_apr+=qtysubtot_apr
                qtygrand_may+=qtysubtot_may
                qtygrand_jun+=qtysubtot_jun
                qtygrand_jul+=qtysubtot_jul
                qtygrand_ags+=qtysubtot_ags
                qtygrand_sep+=qtysubtot_sep
                qtygrand_okt+=qtysubtot_okt
                qtygrand_nop+=qtysubtot_nop
                qtygrand_dec+=qtysubtot_dec
                qtygrand_13=qtygrand_jan+qtygrand_peb+qtygrand_mar+qtygrand_apr+qtygrand_may+qtygrand_jun+qtygrand_jul+qtygrand_ags+qtygrand_sep+qtygrand_okt+qtygrand_nop+qtygrand_dec
                row_count=row_count+1
            # ws.write(row_count,0,"",group_style_grand)
            # ws.write(row_count,1,"",group_style_grand)
            ws.write_merge(row_count,row_count,0,2,"Grand Total",group_style_cen_grand)

            ws.write(row_count,3,qtygrand_jan,group_style_right_grand)
            ws.write(row_count,4,qtygrand_peb,group_style_right_grand)
            ws.write(row_count,5,qtygrand_mar,group_style_right_grand)
            ws.write(row_count,6,qtygrand_apr,group_style_right_grand)
            ws.write(row_count,7,qtygrand_may,group_style_right_grand)
            ws.write(row_count,8,qtygrand_jun,group_style_right_grand)
            ws.write(row_count,9,qtygrand_jul,group_style_right_grand)
            ws.write(row_count,10,qtygrand_ags,group_style_right_grand)
            ws.write(row_count,11,qtygrand_sep,group_style_right_grand)
            ws.write(row_count,12,qtygrand_okt,group_style_right_grand)
            ws.write(row_count,13,qtygrand_nop,group_style_right_grand)
            ws.write(row_count,14,qtygrand_dec,group_style_right_grand)
            ws.write(row_count,15,qtygrand_13,group_style_right_grand)


            ws.col(0).width=256 * int(max_widt_col0*2.1)
            ws.col(1).width =256 * int(max_widt_col1*1.5)
            ws.col(2).width=256 * int(max_widt_col2*1.5)
            row_count=row_count+1
            

sales_summary_customer_count_xls('report.xls.sales.summary.customer.count.report','report.sales.summary.customer.count.wizard','addons/ad_sales_report/report/sales_summary_customer_count.mako', parser=sales_summary_customer_count_parser,header=False)