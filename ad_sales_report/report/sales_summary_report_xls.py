# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from ad_sales_report.report.sales_summary_report_parser import ReportSalesSummary

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class sales_summary_report_xls(report_xls):
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
        company_name = parser._get_company()[0] or ''
        sheets = ['customer', 'product', 'date', 'country']
        uom_base = parser._get_uom_base(data)
        price_base = parser._get_price_base(data)  
        base_currency = parser._get_base_currency()
        gt= data['form']['goods_type']
        checkgt_bales = (gt != 'finish_others') and (gt != 'waste') and (gt != 'asset') and True or False
        print "================================>",gt,checkgt_bales
        if data['form']['sale_type'] == 'local':
            opt_currency = parser._get_opt_currency(data)
        for base_curr in base_currency:
            amount_base = base_curr['currency_name'] or ''
            tax_amount_base = base_curr['tax_base_currency_name'] or ''
            if data['form']['sale_type'] == 'export':
                opt_currency = amount_base
            break
        
        ## Style variable Begin
        hdr_style                       = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        row_normal_style                = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        row_bold_style                  = xlwt.easyxf('font: bold on;',num_format_str='#,##0.00;(#,##0.00)')
        row_bold_top_style              = xlwt.easyxf('font: bold on;borders: top thin ;',num_format_str='#,##0.00;(#,##0.00)')
        row_bold_bottom_style           = xlwt.easyxf('font: bold on;borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        row_top_left_right_style        = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white;borders: left thin, top thin, right thin;')
        row_top_left_rigt_bot_style     = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white;borders: left thin, top thin, right thin, bottom thin;')
        tittle_style                    = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
        tittle_style1                   = xlwt.easyxf('font: height 210, name Calibri, colour_index black; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_left_style            = xlwt.easyxf('font: name Times New Roman, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz right; pattern: pattern solid, fore_color white;')
        subtittle_right_style           = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        blank_style                     = xlwt.easyxf('font: height 650, name Times New Roman, colour_index brown, bold off; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color gray25;')
        normal_style                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
        normal_right_style              = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')
        normal_right_style2             = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
        normal_right_style0             = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz right;',num_format_str='#,##0;(#,##0)')
        group_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on, italic on; align: wrap on, vert top, horiz left;')
        normal_bold_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert top, horiz left;',num_format_str='#,##0.0000;(#,##0.0000)')
        normal_bold_right_style         = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert top, horiz right;',num_format_str='#,##0.0000;(#,##0.0000)')
        normal_bold_right_style2        = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert top, horiz right;',num_format_str='#,##0.00;(#,##0.00)')
        subtotal_title_style            = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom dotted;')
        subtotal_style                  = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.0000;(#,##0.0000)')
        subtotal_style2                 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.00;(#,##0.00)')
        total_title_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        total_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
        total_style2                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        ## Style variable End

        for sheet in sheets:
            report_title1 = parser._get_title(data,sheet)
            report_title2 = 'FROM ' + parser._xdate(data['form']['date_from']) + ' TO ' + parser._xdate(data['form']['date_to'])

            dept_qty_bale_sum = {}
            dept_gross_amount_usd_sum = {}
            dept_net_amount_usd_sum = {}
            details = parser._get_view(data,sheet)
            for line in details:   
                if sheet == 'country':
                    dept_name = line['dest_country_name'] or ''
                else:
                    dept_name = line['dept_id'] or ''
                if dept_name in dept_qty_bale_sum.keys():
                    dept_qty_bale_sum[dept_name] += line['qty_bale'] or 0.0
                else:
                    dept_qty_bale_sum[dept_name] = line['qty_bale'] or 0.0
                if data['form']['sale_type'] == 'local':
                    if dept_name in dept_gross_amount_usd_sum.keys():
                        dept_gross_amount_usd_sum[dept_name] += line['gross_amount_cury'] or 0.0
                    else:
                        dept_gross_amount_usd_sum[dept_name] = line['gross_amount_cury'] or 0.0
                    if dept_name in dept_net_amount_usd_sum.keys():
                        dept_net_amount_usd_sum[dept_name] += line['net_amount_cury'] or 0.0
                    else:
                        dept_net_amount_usd_sum[dept_name] = line['net_amount_cury'] or 0.0
                else:
                    if dept_name in dept_gross_amount_usd_sum.keys():
                        dept_gross_amount_usd_sum[dept_name] += line['gross_amount'] or 0.0
                    else:
                        dept_gross_amount_usd_sum[dept_name] = line['gross_amount'] or 0.0
                    if dept_name in dept_net_amount_usd_sum.keys():
                        dept_net_amount_usd_sum[dept_name] += line['net_amount'] or 0.0
                    else:
                        dept_net_amount_usd_sum[dept_name] = line['net_amount'] or 0.0

            if sheet == 'customer':
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerCustomer',  2, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p: checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                            ('OtherUnit',  2, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Other Unit'),
                    ]
                else:
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerCustomer',  2, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p: checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                    ]
            elif sheet == 'product':
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    cols_specs = [
                            #title
                            ('Company', 13, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  13, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  13, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 13, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerProdCode',  3, 0, 'text', lambda x, d, p: 'Product Code'),
                            ('headerProdName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p:  checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                            ('OtherUnit',  2, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Other Unit'),
                            # ('Unit',  1, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Unit'),
                    ]
                else:
                    cols_specs = [
                            #title
                            ('Company', 13, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  13, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  13, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 13, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerProdCode',  3, 0, 'text', lambda x, d, p: 'Product Code'),
                            ('headerProdName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p:  checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                            # ('Other',  1, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Other'),
                            # ('Unit',  1, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Unit'),
                    ]

            elif sheet == 'country':
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerCustomer',  2, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p: checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                            ('OtherUnit',  2, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Other Unit'),
                    ]
                else:
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerCustomer',  2, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p: checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                    ]
            else:
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerDate',  2, 0, 'text', lambda x, d, p: 'Date'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p:  checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                            ('OtherUnit',  2, 0, 'text', lambda x, d, p: (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES')  and 'Other Unit'),
                    ]
                else:
                    cols_specs = [
                            #title
                            ('Company', 10, 0, 'text', lambda x, d, p: company_name),
                            ('Title1',  10, 0, 'text', lambda x, d, p: report_title1),
                            ('Title2',  10, 0, 'text', lambda x, d, p: report_title2),
                            ('Kosong', 10, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerDate',  2, 0, 'text', lambda x, d, p: 'Date'),
                            ('headerQtyBale',  1, 0, 'text', lambda x, d, p:  checkgt_bales and 'Qty (Bale)' or 'Qty (KGS)'),
                            ('headerGrossPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Gross Price ('+opt_currency+'/Bale)'),
                            ('headerNetPriceUSDBale',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/Bale)'),
                            ('headerGrossAmountUSD',  1, 0, 'text', lambda x, d, p: 'Gross Amount ('+opt_currency+')'),
                            ('headerNetAmountUSD',  1, 0, 'text', lambda x, d, p: 'Net Amount ('+opt_currency+')'),
                            ('headerNetPriceUSDKG',  1, 0, 'text', lambda x, d, p: 'Net Price ('+opt_currency+'/KG)'),
                            ('headerAnalysisQty',  1, 0, 'text', lambda x, d, p: 'Analysis % Quantity'),
                            ('headerAnalysisAmt',  1, 0, 'text', lambda x, d, p: 'Analysis % Amount'),
                    ]

            ##Penempatan untuk template rows
            row_Company             = self.xls_row_template(cols_specs, ['Company'])
            row_Title1              = self.xls_row_template(cols_specs, ['Title1'])
            row_Title2              = self.xls_row_template(cols_specs, ['Title2'])
            row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
            row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
            #============================================================================
            if sheet == 'customer':
                row_header              = self.xls_row_template(cols_specs, ['headerCustomer','headerQtyBale','headerGrossPriceUSDBale',
                                                                             'headerNetPriceUSDBale','headerGrossAmountUSD',
                                                                             'headerNetAmountUSD','headerNetPriceUSDKG',
                                                                             'headerAnalysisQty','headerAnalysisAmt','OtherUnit'])
            elif sheet == 'product':
                row_header              = self.xls_row_template(cols_specs, ['headerProdCode','headerProdName','headerQtyBale',
                                                                             'headerGrossPriceUSDBale',
                                                                             'headerNetPriceUSDBale','headerGrossAmountUSD',
                                                                             'headerNetAmountUSD','headerNetPriceUSDKG',
                                                                             'headerAnalysisQty','headerAnalysisAmt','OtherUnit'])
            elif sheet == 'country':
                row_header              = self.xls_row_template(cols_specs, ['headerCustomer','headerQtyBale','headerGrossPriceUSDBale',
                                                                             'headerNetPriceUSDBale','headerGrossAmountUSD',
                                                                             'headerNetAmountUSD','headerNetPriceUSDKG',
                                                                             'headerAnalysisQty','headerAnalysisAmt','OtherUnit'])
            else:
                row_header              = self.xls_row_template(cols_specs, ['headerDate','headerQtyBale','headerGrossPriceUSDBale',
                                                                             'headerNetPriceUSDBale','headerGrossAmountUSD',
                                                                             'headerNetAmountUSD','headerNetPriceUSDKG',
                                                                             'headerAnalysisQty','headerAnalysisAmt','OtherUnit'])

            if sheet == 'customer':
                wsa = wb.add_sheet(('Customer Wise'))    
            elif sheet == 'date':
                wsa = wb.add_sheet(('Date Wise'))    
            elif sheet == 'product':
                wsa = wb.add_sheet(('Product Wise'))    
            else:
                wsa = wb.add_sheet(('Country Wise'))    

            wsa.panes_frozen = True
            wsa.remove_splits = True
            #wsa.paper_size_code = 6 #Letter = 1 A4=6
            wsa.portrait = 0 # Landscape
            wsa.fit_width_to_pages = 1
            #wsa.fit_height_to_pages = 0
            #wsa.fit_num_pages = 0
            wsa.print_scaling = 80
            #wsa.print_centered_horz = 0
            #wsa.print_centered_vert = 1

            # set print header/footer
            wsa.header_str = ''
            wsa.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

            width01 = len("ABCDEFG")*128
            width02 = len("ABCDEFG")*512

            if sheet == 'customer':
                wsa.col(0).width = width01
                wsa.col(1).width = width02*2
                wsa.col(2).width = width02
                wsa.col(3).width = width02
                wsa.col(4).width = width02
                wsa.col(5).width = width02
                wsa.col(6).width = width02
                wsa.col(7).width = width02
                wsa.col(8).width = width02
                wsa.col(9).width = width02
                wsa.col(10).width = width02
                wsa.col(11).width = width02
                col_max = 11
            elif sheet == 'product':
                wsa.col(0).width = width01
                wsa.col(1).width = width01
                wsa.col(2).width = width02
                wsa.col(3).width = width02*2
                wsa.col(4).width = width02
                wsa.col(5).width = width02
                wsa.col(6).width = width02
                wsa.col(7).width = width02
                wsa.col(8).width = width02
                wsa.col(9).width = width02
                wsa.col(10).width = width02
                wsa.col(11).width = width02
                wsa.col(12).width = width02
                wsa.col(13).width = width02
                col_max = 13
            elif sheet == 'country':
                wsa.col(0).width = width01
                wsa.col(1).width = width02*2
                wsa.col(2).width = width02
                wsa.col(3).width = width02
                wsa.col(4).width = width02
                wsa.col(5).width = width02
                wsa.col(6).width = width02
                wsa.col(7).width = width02
                wsa.col(8).width = width02
                wsa.col(9).width = width02
                wsa.col(10).width = width02
                wsa.col(11).width = width02
                col_max = 11
            else:
                wsa.col(0).width = width01
                wsa.col(1).width = width02
                wsa.col(2).width = width02
                wsa.col(3).width = width02
                wsa.col(4).width = width02
                wsa.col(5).width = width02
                wsa.col(6).width = width02
                wsa.col(7).width = width02
                wsa.col(8).width = width02
                wsa.col(9).width = width02
                wsa.col(10).width = width02
                wsa.col(11).width = width02
                col_max = 11
            
            # Untuk Data Title
            self.xls_write_row(wsa, None, data, parser,0, row_Company, tittle_style)
            self.xls_write_row(wsa, None, data, parser,1, row_Title1, tittle_style)
            self.xls_write_row(wsa, None, data, parser,2, row_Title2, tittle_style)
            self.xls_write_row(wsa, None, data, parser,3, row_Kosong, tittle_style)
            
            # Untuk Data Header
            self.xls_write_row(wsa, None, data, parser,4, row_header, hdr_style)
            
            row_count = 5
            details = parser._get_view(data,sheet)
            dept_qty_bale = 0.0
            dept_qty_kg = 0.0
            dept_gross_amount_usd = 0.0
            dept_net_amount_usd = 0.0
            dept_items = 0
            group_qty_bale = 0.0
            group_qty_kg = 0.0
            group_gross_amount_usd = 0.0
            group_net_amount_usd = 0.0
            group_items = 0
            grand_qty_bale = 0.0
            grand_qty_kg = 0.0
            grand_gross_amount_usd = 0.0
            grand_net_amount_usd = 0.0
            grand_items = 0
            old_dept_name = 'None'
            old_group_name = 'None'

            for line in details:   
                if sheet == 'country':
                    dept_name = line['dest_country_name'] or ''
                else:
                    dept_name = line['dept_id'] or ''
                if sheet == 'product':
                    group_name = line['blend'] or ''
                else:
                    group_name = 'None'

                if (dept_name != old_dept_name) or (group_name != old_group_name):
                    if sheet == 'product':
                        if old_group_name != 'None':
                            wsa.write(row_count, 0, '', normal_style)
                            wsa.write_merge(row_count,row_count,1,3, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsa.write(row_count, 4, checkgt_bales and group_qty_bale or group_qty_kg , subtotal_style)
                            wsa.write_merge(row_count,row_count,5,6, '', subtotal_style)    
                            wsa.write(row_count, 7, group_gross_amount_usd, subtotal_style2)
                            wsa.write(row_count, 8, group_net_amount_usd, subtotal_style2)
                            wsa.write_merge(row_count,row_count,9,11, '', subtotal_style)    
                            row_count+=1    
                            #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                            #row_count+=1

                    if (dept_name != old_dept_name):
                        if sheet == 'customer':
                            if old_dept_name != 'None':
                                wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                                wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                                wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                                wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                                wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                                wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)    
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        elif sheet == 'product':
                            if old_dept_name != 'None':
                                wsa.write_merge(row_count,row_count,0,3, 'Total for ' + old_dept_name, subtotal_title_style)        
                                wsa.write(row_count, 4, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                                wsa.write_merge(row_count,row_count,5,6, '', subtotal_style)    
                                wsa.write(row_count, 7, dept_gross_amount_usd, subtotal_style2)
                                wsa.write(row_count, 8, dept_net_amount_usd, subtotal_style2)
                                wsa.write_merge(row_count,row_count,9,11, '', subtotal_style)    
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        elif sheet == 'country':
                            if old_dept_name != 'None':
                                wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                                wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                                wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                                wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                                wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                                wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)    
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        else:
                            if old_dept_name != 'None':
                                wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                                wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                                wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                                wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                                wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                                wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)    
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        wsa.write_merge(row_count,row_count,0,col_max, dept_name, group_style)
                        row_count+=1

                        old_dept_name = dept_name
                        dept_qty_bale = 0.0
                        dept_qty_kg = 0.0
                        dept_gross_amount_usd = 0.0
                        dept_net_amount_usd = 0.0
                        dept_items = 0
                        group_qty_bale = 0.0
                        group_qty_kg = 0.0
                        group_gross_amount_usd = 0.0
                        group_net_amount_usd = 0.0
                        group_items = 0

                    if group_name != old_group_name:
                        if sheet == 'product':
                            wsa.write(row_count,0, '', group_style)        
                            wsa.write_merge(row_count,row_count,1,col_max, group_name, group_style)
                            row_count+=1

                        old_group_name = group_name
                        group_qty_bale = 0.0
                        group_qty_kg = 0.0
                        group_gross_amount_usd = 0.0
                        group_net_amount_usd = 0.0
                        group_items = 0
                
                dept_qty_bale += line['qty_bale'] or 0.0
                dept_qty_kg += line['qty_kg'] or 0.0
                if data['form']['sale_type'] == 'local':
                    dept_gross_amount_usd += line['gross_amount_cury'] or 0.0
                    dept_net_amount_usd += line['net_amount_cury'] or 0.0
                else:
                    dept_gross_amount_usd += line['gross_amount'] or 0.0
                    dept_net_amount_usd += line['net_amount'] or 0.0
                dept_items += 1
                group_qty_bale += line['qty_bale'] or 0.0
                group_qty_kg += line['qty_kg'] or 0.0
                if data['form']['sale_type'] == 'local':
                    group_gross_amount_usd += line['gross_amount_cury'] or 0.0
                    group_net_amount_usd += line['net_amount_cury'] or 0.0
                else:
                    group_gross_amount_usd += line['gross_amount'] or 0.0
                    group_net_amount_usd += line['net_amount'] or 0.0
                group_items += 1
                grand_qty_bale += line['qty_bale'] or 0.0
                grand_qty_kg += line['qty_kg'] or 0.0
                if data['form']['sale_type'] == 'local':
                    grand_gross_amount_usd += line['gross_amount_cury'] or 0.0
                    grand_net_amount_usd += line['net_amount_cury'] or 0.0
                else:
                    grand_gross_amount_usd += line['gross_amount'] or 0.0
                    grand_net_amount_usd += line['net_amount'] or 0.0
                grand_items += 1

                if (line['qty_bale'] or 0.0) > 0.0:
                    gross_price_cury_bale = (line['gross_amount_cury'] or 0.0) / (line['qty_bale'] or 0.0)
                    net_price_cury_bale = (line['net_amount_cury'] or 0.0) / (line['qty_bale'] or 0.0)
                    gross_price_bale = (line['gross_amount'] or 0.0) / (line['qty_bale'] or 0.0)
                    net_price_bale = (line['net_amount'] or 0.0) / (line['qty_bale'] or 0.0)
                else:
                    gross_price_cury_bale = 0.0
                    net_price_cury_bale = 0.0
                    gross_price_bale = 0.0
                    net_price_bale = 0.0

                if (line['qty_kg'] or 0.0) > 0.0:
                    gross_price_cury_kg = (line['gross_amount_cury'] or 0.0) / (line['qty_kg'] or 0.0)
                    net_price_cury_kg = (line['net_amount_cury'] or 0.0) / (line['qty_kg'] or 0.0)
                    gross_price_kg = (line['gross_amount'] or 0.0) / (line['qty_kg'] or 0.0)
                    net_price_kg = (line['net_amount'] or 0.0) / (line['qty_kg'] or 0.0)
                else:
                    gross_price_cury_kg = 0.0
                    net_price_cury_kg = 0.0
                    gross_price_kg = 0.0
                    net_price_kg = 0.0

                if sheet == 'customer':
                    wsa.write(row_count, 0, '', normal_style)
                    wsa.write(row_count, 1, line['cust_name'] or '', normal_style)
                    wsa.write(row_count, 2, checkgt_bales and line['qty_bale'] or line['qty_kg'] or 0.0, normal_right_style)
                    wsa.write(row_count, 8, dept_qty_bale_sum[dept_name]!=0.0 and (line['qty_bale'] or 0.0)*100.0/dept_qty_bale_sum[dept_name] or 0.0, normal_right_style2)
                    wsa.write(row_count, 10, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['qty_unit'] or '', normal_right_style)
                    wsa.write(row_count, 11, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['uom'] or '', normal_right_style)
                    if data['form']['sale_type'] == 'local':
                        wsa.write(row_count, 3, gross_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_cury_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount_cury'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                    else:
                        wsa.write(row_count, 3, gross_price_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                elif sheet == 'product':
                    wsa.write(row_count, 0, '', normal_style)
                    wsa.write(row_count, 1, '', normal_style)
                    wsa.write(row_count, 2, line['prod_code'] or '', normal_style)
                    wsa.write(row_count, 3, line['prod_name'] or '', normal_style)
                    wsa.write(row_count, 4, checkgt_bales and line['qty_bale'] or line['qty_kg'] or 0.0, normal_right_style)
                    wsa.write(row_count, 10, dept_qty_bale_sum[dept_name]!=0.0 and (line['qty_bale'] or 0.0)*100.0/dept_qty_bale_sum[dept_name] or 0.0, normal_right_style2)
                    # wsa.write(row_count, 12, (checkgt_bales==False and gt=='asset') and (str(line['qty_unit']) or str(0.0)) +' hehehe', normal_right_style)
                    wsa.write(row_count, 12, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['qty_unit'] or '', normal_right_style)
                    wsa.write(row_count, 13, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['uom'] or '', normal_right_style)
                    if data['form']['sale_type'] == 'local':
                        wsa.write(row_count, 5, gross_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 6, net_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 7, line['gross_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 8, line['net_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 9, net_price_cury_kg, normal_right_style2)
                        wsa.write(row_count, 11, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount_cury'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                        # wsa.write(row_count, 12, 'texttttttttttt', normal_style)
                    else:
                        wsa.write(row_count, 5, gross_price_bale, normal_right_style2)
                        wsa.write(row_count, 6, net_price_bale, normal_right_style2)
                        wsa.write(row_count, 7, line['gross_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 8, line['net_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 9, net_price_kg, normal_right_style2)
                        wsa.write(row_count, 11, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                        # wsa.write(row_count, 12, 'texttttttttttt', normal_style)
                elif sheet == 'country':
                    wsa.write(row_count, 0, '', normal_style)
                    wsa.write(row_count, 1, line['cust_name'] or '', normal_style)
                    wsa.write(row_count, 2, checkgt_bales and line['qty_bale'] or line['qty_kg'] or 0.0, normal_right_style)
                    wsa.write(row_count, 8, dept_qty_bale_sum[dept_name]!=0.0 and (line['qty_bale'] or 0.0)*100.0/dept_qty_bale_sum[dept_name] or 0.0, normal_right_style2)
                    wsa.write(row_count, 10, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['qty_unit'] or '', normal_right_style)
                    wsa.write(row_count, 11, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['uom'] or '', normal_right_style)
                    if data['form']['sale_type'] == 'local':
                        wsa.write(row_count, 3, gross_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_cury_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount_cury'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                    else:
                        wsa.write(row_count, 3, gross_price_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                else:
                    wsa.write(row_count, 0, '', normal_style)
                    wsa.write(row_count, 1, line['do_date_dmy'] or '', normal_style)
                    wsa.write(row_count, 2, checkgt_bales and line['qty_bale'] or line['qty_kg'] or 0.0, normal_right_style)
                    wsa.write(row_count, 8, dept_qty_bale_sum[dept_name]!=0.0 and (line['qty_bale'] or 0.0)*100.0/dept_qty_bale_sum[dept_name] or 0.0, normal_right_style2)
                    wsa.write(row_count, 10, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['qty_unit'] or '', normal_right_style)
                    wsa.write(row_count, 11, (checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES') and line['uom'] or '', normal_right_style)
                    if data['form']['sale_type'] == 'local':
                        wsa.write(row_count, 3, gross_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_cury_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount_cury'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_cury_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount_cury'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                    else:
                        wsa.write(row_count, 3, gross_price_bale, normal_right_style2)
                        wsa.write(row_count, 4, net_price_bale, normal_right_style2)
                        wsa.write(row_count, 5, line['gross_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 6, line['net_amount'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 7, net_price_kg, normal_right_style2)
                        wsa.write(row_count, 9, dept_gross_amount_usd_sum[dept_name]!=0.0 and (line['gross_amount'] or 0.0)*100.0/dept_gross_amount_usd_sum[dept_name] or 0.0, normal_right_style2)
                row_count+=1
            
            if sheet == 'product':
                if old_group_name != 'None':
                    wsa.write(row_count, 0, '', normal_style)
                    wsa.write_merge(row_count,row_count,1,3, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsa.write(row_count, 4, checkgt_bales and group_qty_bale or group_qty_kg, subtotal_style)
                    wsa.write_merge(row_count,row_count,5,6, '', subtotal_style)    
                    wsa.write(row_count, 7, group_gross_amount_usd, subtotal_style2)
                    wsa.write(row_count, 8, group_net_amount_usd, subtotal_style2)
                    wsa.write_merge(row_count,row_count,9,11, '', subtotal_style)    
                    row_count+=1    

            if sheet == 'customer':
                if old_dept_name != 'None':
                    wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                    wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                    wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                    wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                    wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                    if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                        wsa.write_merge(row_count,row_count,7,11, '', subtotal_style)
                    else:
                        wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)
                    row_count+=1    
                wsa.write_merge(row_count,row_count,0,1, 'Grand Total', total_title_style)        
                wsa.write(row_count, 2, checkgt_bales and grand_qty_bale or grand_qty_kg, total_style)
                wsa.write_merge(row_count,row_count,3,4, '', total_style)    
                wsa.write(row_count, 5, grand_gross_amount_usd, total_style2)
                wsa.write(row_count, 6, grand_net_amount_usd, total_style2)
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    wsa.write_merge(row_count,row_count,7,11, '', total_style)
                else:
                    wsa.write_merge(row_count,row_count,7,9, '', total_style) 
            elif sheet == 'product':
                if old_dept_name != 'None':
                    wsa.write_merge(row_count,row_count,0,3, 'Total for ' + old_dept_name, subtotal_title_style)        
                    wsa.write(row_count, 4, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                    wsa.write_merge(row_count,row_count,5,6, '', subtotal_style)    
                    wsa.write(row_count, 7, dept_gross_amount_usd, subtotal_style2)
                    wsa.write(row_count, 8, dept_net_amount_usd, subtotal_style2)
                    if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                        wsa.write_merge(row_count,row_count,9,13, '', subtotal_style)
                    else:  
                        wsa.write_merge(row_count,row_count,9,11, '', subtotal_style)
                    row_count+=1    
                wsa.write_merge(row_count,row_count,0,3, 'Grand Total', total_title_style)        
                wsa.write(row_count, 4, checkgt_bales and grand_qty_bale or grand_qty_kg, total_style)
                wsa.write_merge(row_count,row_count,5,6, '', total_style)    
                wsa.write(row_count, 7, grand_gross_amount_usd, total_style2)
                wsa.write(row_count, 8, grand_net_amount_usd, total_style2)
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    wsa.write_merge(row_count,row_count,9,13, '', total_style)
                else:
                    wsa.write_merge(row_count,row_count,9,11, '', total_style)   
            elif sheet == 'country':
                if old_dept_name != 'None':
                    wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                    wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                    wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                    wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                    wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                    if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                        wsa.write_merge(row_count,row_count,7,11, '', subtotal_style)
                    else:
                        wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)
                    row_count+=1    
                wsa.write_merge(row_count,row_count,0,1, 'Grand Total', total_title_style)        
                wsa.write(row_count, 2, checkgt_bales and grand_qty_bale or grand_qty_kg, total_style)
                wsa.write_merge(row_count,row_count,3,4, '', total_style)    
                wsa.write(row_count, 5, grand_gross_amount_usd, total_style2)
                wsa.write(row_count, 6, grand_net_amount_usd, total_style2)
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    wsa.write_merge(row_count,row_count,7,11, '', total_style)
                else:
                    wsa.write_merge(row_count,row_count,7,9, '', total_style)
            else:
                if old_dept_name != 'None':
                    wsa.write_merge(row_count,row_count,0,1, 'Total for ' + old_dept_name, subtotal_title_style)        
                    wsa.write(row_count, 2, checkgt_bales and dept_qty_bale or dept_qty_kg, subtotal_style)
                    wsa.write_merge(row_count,row_count,3,4, '', subtotal_style)    
                    wsa.write(row_count, 5, dept_gross_amount_usd, subtotal_style2)
                    wsa.write(row_count, 6, dept_net_amount_usd, subtotal_style2)
                    if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                        wsa.write_merge(row_count,row_count,7,11, '', subtotal_style)
                    else:
                        wsa.write_merge(row_count,row_count,7,9, '', subtotal_style)
                    row_count+=1    
                wsa.write_merge(row_count,row_count,0,1, 'Grand Total', total_title_style)        
                wsa.write(row_count, 2, checkgt_bales and grand_qty_bale or grand_qty_kg, total_style)
                wsa.write_merge(row_count,row_count,3,4, '', total_style)    
                wsa.write(row_count, 5, grand_gross_amount_usd, total_style2)
                wsa.write(row_count, 6, grand_net_amount_usd, total_style2)
                if checkgt_bales==False and gt=='asset' and line['uom']!='KGS' and line['uom']!='BALES':
                    wsa.write_merge(row_count,row_count,7,11, '', total_style)   
                else:
                    wsa.write_merge(row_count,row_count,7,9, '', total_style) 
            
        pass

sales_summary_report_xls('report.sales.summary.report',
                 'report.sales.summary.wizard', 'addons/ad_sales_report/report/sales_summary_report.mako',
                 parser=ReportSalesSummary)