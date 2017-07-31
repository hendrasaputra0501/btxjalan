# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from ad_sales_report.report.sales_report_parser import ReportSalesOrder

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class sales_report_xls(report_xls):
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
        sheets = ['customer', 'product', 'date', 'invoice', 'country']
        uom_base = parser._get_uom_base(data)
        price_base = parser._get_price_base(data)  
        base_currency = parser._get_base_currency()
        for base_curr in base_currency:
            amount_base = base_curr['currency_name'] or ''
            tax_amount_base = base_curr['tax_base_currency_name'] or ''
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
            # if sheet!=data['form']['report_type']:
            #     continue
            report_title1 = parser._get_title(data,sheet)
            report_title2 = 'FROM ' + parser._xdate(data['form']['date_from']) + ' TO ' + parser._xdate(data['form']['date_to'])

            if data['form']['sale_type'] == 'local':
                # asseeeeeeeeettt
                if data['form']['goods_type']=='asset':
                    if sheet == 'invoice':
                        cols_specs = [
                                #title
                                ('Company', 23, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  23, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  23, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 23, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  2, 0, 'text', lambda x, d, p: 'Surat Jalan No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'Surat Jalan Date'),
                                ('headerTaxInvc',  1, 0, 'text', lambda x, d, p: 'Tax Invc.'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerUOMQty',  1, 0, 'text', lambda x, d, p: 'Qty (' + uom_base + ')'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerNetPrice',  1, 0, 'text', lambda x, d, p: 'Net Price (/' + uom_base + ')'),
                                ('headerTax',  1, 0, 'text', lambda x, d, p: 'Tax'),
                                ('headerSellPrice',  1, 0, 'text', lambda x, d, p: 'Sell Price (/' + uom_base + ')'),
                                ('headerNetAmount',  1, 0, 'text', lambda x, d, p: 'Net Amount'),
                                ('headerTaxAmount',  1, 0, 'text', lambda x, d, p: 'Tax Amount'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Total Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Total Amount (RP)'),
                                ('headerDPPNPET',  1, 0, 'text', lambda x, d, p: 'DPP N-PET'),
                                ('headerDPPPET',  1, 0, 'text', lambda x, d, p: 'DPP PET'),
                                ('headerTaxNPET',  1, 0, 'text', lambda x, d, p: 'Tax N-PET '),
                                ('headerTaxPET',  1, 0, 'text', lambda x, d, p: 'Tax PET'),
                                ('OtherUnit',  2, 0, 'text', lambda x, d, p: 'Other Unit'),
                        ]
                    else:
                        cols_specs = [
                                #title
                                ('Company', 24, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  24, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  24, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 24, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'Surat Jalan No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'Surat Jalan Date'),
                                ('headerTaxInvc',  1, 0, 'text', lambda x, d, p: 'Tax Invc.'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerUOMQty',  1, 0, 'text', lambda x, d, p: 'Qty (' + uom_base + ')'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerNetPrice',  1, 0, 'text', lambda x, d, p: 'Net Price (/' + uom_base + ')'),
                                ('headerTax',  1, 0, 'text', lambda x, d, p: 'Tax'),
                                ('headerSellPrice',  1, 0, 'text', lambda x, d, p: 'Sell Price (/' + uom_base + ')'),
                                ('headerNetAmount',  1, 0, 'text', lambda x, d, p: 'Net Amount'),
                                ('headerTaxAmount',  1, 0, 'text', lambda x, d, p: 'Tax Amount'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Total Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Total Amount (RP)'),
                                ('headerDPPNPET',  1, 0, 'text', lambda x, d, p: 'DPP N-PET'),
                                ('headerDPPPET',  1, 0, 'text', lambda x, d, p: 'DPP PET'),
                                ('headerTaxNPET',  1, 0, 'text', lambda x, d, p: 'Tax N-PET '),
                                ('headerTaxPET',  1, 0, 'text', lambda x, d, p: 'Tax PET'),
                                ('OtherUnit',  2, 0, 'text', lambda x, d, p: 'Other Unit'),
                        ]
                else:
                    #non asseeeeeettttttttttttttt
                    if sheet == 'invoice':
                        cols_specs = [
                                #title
                                ('Company', 23, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  23, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  23, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 23, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  2, 0, 'text', lambda x, d, p: 'Surat Jalan No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'Surat Jalan Date'),
                                ('headerTaxInvc',  1, 0, 'text', lambda x, d, p: 'Tax Invc.'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerUOMQty',  1, 0, 'text', lambda x, d, p: 'Qty (' + uom_base + ')'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerNetPrice',  1, 0, 'text', lambda x, d, p: 'Net Price (/' + uom_base + ')'),
                                ('headerTax',  1, 0, 'text', lambda x, d, p: 'Tax'),
                                ('headerSellPrice',  1, 0, 'text', lambda x, d, p: 'Sell Price (/' + uom_base + ')'),
                                ('headerNetAmount',  1, 0, 'text', lambda x, d, p: 'Net Amount'),
                                ('headerTaxAmount',  1, 0, 'text', lambda x, d, p: 'Tax Amount'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Total Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Total Amount (RP)'),
                                ('headerDPPNPET',  1, 0, 'text', lambda x, d, p: 'DPP N-PET'),
                                ('headerDPPPET',  1, 0, 'text', lambda x, d, p: 'DPP PET'),
                                ('headerTaxNPET',  1, 0, 'text', lambda x, d, p: 'Tax N-PET '),
                                ('headerTaxPET',  1, 0, 'text', lambda x, d, p: 'Tax PET'),
                        ]
                    else:
                        cols_specs = [
                                #title
                                ('Company', 24, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  24, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  24, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 24, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'Surat Jalan No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'Surat Jalan Date'),
                                ('headerTaxInvc',  1, 0, 'text', lambda x, d, p: 'Tax Invc.'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerUOMQty',  1, 0, 'text', lambda x, d, p: 'Qty (' + uom_base + ')'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerNetPrice',  1, 0, 'text', lambda x, d, p: 'Net Price (/' + uom_base + ')'),
                                ('headerTax',  1, 0, 'text', lambda x, d, p: 'Tax'),
                                ('headerSellPrice',  1, 0, 'text', lambda x, d, p: 'Sell Price (/' + uom_base + ')'),
                                ('headerNetAmount',  1, 0, 'text', lambda x, d, p: 'Net Amount'),
                                ('headerTaxAmount',  1, 0, 'text', lambda x, d, p: 'Tax Amount'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Total Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Total Amount (RP)'),
                                ('headerDPPNPET',  1, 0, 'text', lambda x, d, p: 'DPP N-PET'),
                                ('headerDPPPET',  1, 0, 'text', lambda x, d, p: 'DPP PET'),
                                ('headerTaxNPET',  1, 0, 'text', lambda x, d, p: 'Tax N-PET '),
                                ('headerTaxPET',  1, 0, 'text', lambda x, d, p: 'Tax PET'),
                        ]
            #exportttttttttttttttttt
            else:
                #assseeeettttt
                if data['form']['goods_type']=='asset':
                    if sheet == 'date':
                        cols_specs = [
                                #title
                                ('Company', 20, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  20, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  20, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 20, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerInvoiceNo',  1, 0, 'text', lambda x, d, p: 'Invoice No'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                                ('OtherUnit',  2, 0, 'text', lambda x, d, p: 'Other Unit'),
                        ]
                    elif sheet == 'invoice':
                        cols_specs = [
                                #title
                                ('Company', 18, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  18, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  18, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 18, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  2, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                                ('OtherUnit',  2, 0, 'text', lambda x, d, p: 'Other Unit'),
                        ]
                    else:
                        cols_specs = [
                                #title
                                ('Company', 19, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  19, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  19, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 19, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerInvoiceNo',  1, 0, 'text', lambda x, d, p: 'Invoice No'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                                ('OtherUnit',  2, 0, 'text', lambda x, d, p: 'Other Unit'),
                        ]
                else:
                    # export non assseeeettttt
                    if sheet == 'date':
                        cols_specs = [
                                #title
                                ('Company', 20, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  20, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  20, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 20, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerInvoiceNo',  1, 0, 'text', lambda x, d, p: 'Invoice No'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                        ]
                    elif sheet == 'invoice':
                        cols_specs = [
                                #title
                                ('Company', 18, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  18, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  18, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 18, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  2, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerKMKRate',  1, 0, 'text', lambda x, d, p: 'KMK Rate'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                        ]
                    else:
                        cols_specs = [
                                #title
                                ('Company', 19, 0, 'text', lambda x, d, p: company_name),
                                ('Title1',  19, 0, 'text', lambda x, d, p: report_title1),
                                ('Title2',  19, 0, 'text', lambda x, d, p: report_title2),
                                ('Kosong', 19, 0, 'text',lambda x, d, p: ' '),
                                ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                      
                                #header
                                ('headerSJNo',  3, 0, 'text', lambda x, d, p: 'SJ No'),
                                ('headerSJDate',  1, 0, 'text', lambda x, d, p: 'SJ Date'),
                                ('headerInvoiceNo',  1, 0, 'text', lambda x, d, p: 'Invoice No'),
                                ('headerCustomerCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                                ('headerProductCode',  1, 0, 'text', lambda x, d, p: 'Code'),
                                ('headerProductName',  1, 0, 'text', lambda x, d, p: 'Product Name'),
                                ('headerProductLotNo',  1, 0, 'text', lambda x, d, p: 'Lot No'),
                                ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                                ('headerQtyBales',  1, 0, 'text', lambda x, d, p: 'Qty (BALES)'),
                                ('headerQtyKgs',  1, 0, 'text', lambda x, d, p: 'Qty (KGS)'),
                                ('headerCuryId',  1, 0, 'text', lambda x, d, p: 'Cury Id'),
                                ('headerSellPriceIDR',  1, 0, 'text', lambda x, d, p: 'Sell Price (RP/BALE)'),
                                ('headerSellPriceUSD',  1, 0, 'text', lambda x, d, p: 'Sell Price (US$/KG)'),
                                ('headerTerms',  1, 0, 'text', lambda x, d, p: 'Terms'),
                                ('headerSalesAmtUSD',  1, 0, 'text', lambda x, d, p: 'Sales Amount (US$)'),
                                ('headerSalesAmtIDR',  1, 0, 'text', lambda x, d, p: 'Sales Amount (RP)'),
                        ]


            ##Penempatan untuk template rows
            row_Company             = self.xls_row_template(cols_specs, ['Company'])
            row_Title1              = self.xls_row_template(cols_specs, ['Title1'])
            row_Title2              = self.xls_row_template(cols_specs, ['Title2'])
            row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
            row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
            #============================================================================
            if data['form']['sale_type'] == 'local':
                if data['form']['goods_type']=='asset':
                    row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerTaxInvc',
                                                                                 'headerCustomerCode','headerCustomer','headerProduct','headerContractNo',
                                                                                 'headerUOMQty','headerCuryId','headerNetPrice','headerTax',
                                                                                 'headerSellPrice','headerNetAmount','headerTaxAmount',
                                                                                 'headerTerms','headerKMKRate','headerSalesAmtUSD','headerSalesAmtIDR',
                                                                                 'headerDPPNPET','headerDPPPET','headerTaxNPET','headerTaxPET','OtherUnit'])
                else:
                    row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerTaxInvc',
                                                                                 'headerCustomerCode','headerCustomer','headerProduct','headerContractNo',
                                                                                 'headerUOMQty','headerCuryId','headerNetPrice','headerTax',
                                                                                 'headerSellPrice','headerNetAmount','headerTaxAmount',
                                                                                 'headerTerms','headerKMKRate','headerSalesAmtUSD','headerSalesAmtIDR',
                                                                                 'headerDPPNPET','headerDPPPET','headerTaxNPET','headerTaxPET'])
            #exporttttttt                                                                     
            else:
                #asseetttttttttttttttttttt
                if data['form']['goods_type']=='asset':
                    if sheet == 'date':
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerInvoiceNo',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerKMKRate',
                                                                                     'headerSalesAmtUSD','headerSalesAmtIDR','OtherUnit'])
                    elif sheet == 'invoice':
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerKMKRate',
                                                                                     'headerSalesAmtUSD','headerSalesAmtIDR','OtherUnit'])
                    else:
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerInvoiceNo',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerSalesAmtUSD',
                                                                                   'headerSalesAmtIDR','OtherUnit'])
                        # non asseeeettt
                else:
                    if sheet == 'date':
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerInvoiceNo',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerKMKRate',
                                                                                     'headerSalesAmtUSD','headerSalesAmtIDR'])
                    elif sheet == 'invoice':
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerKMKRate',
                                                                                     'headerSalesAmtUSD','headerSalesAmtIDR'])
                    else:
                        row_header              = self.xls_row_template(cols_specs, ['headerSJNo','headerSJDate','headerInvoiceNo',
                                                                                     'headerCustomerCode','headerCustomer','headerProductCode','headerProductName',
                                                                                     'headerProductLotNo','headerContractNo','headerQtyBales',
                                                                                     'headerQtyKgs','headerCuryId','headerSellPriceIDR',
                                                                                     'headerSellPriceUSD','headerTerms','headerSalesAmtUSD',
                                                                                     'headerSalesAmtIDR'])

            if sheet == 'customer':
                wsa = wb.add_sheet(('Customer Wise'))    
            elif sheet == 'date':
                wsa = wb.add_sheet(('Date Wise'))    
            elif sheet == 'invoice':
                wsa = wb.add_sheet(('Invoice Wise'))    
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
            wsa.print_scaling = 50
            #wsa.print_centered_horz = 0
            #wsa.print_centered_vert = 1

            # set print header/footer
            wsa.header_str = ''
            wsa.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

            width01 = len("ABCDEFG")*128
            width02 = len("ABCDEFG")*512

            if data['form']['sale_type'] == 'local':
                if sheet == 'invoice':
                    wsa.col(0).width = width01
                    wsa.col(1).width = width02
                    wsa.col(2).width = (width02*4)/5
                    wsa.col(3).width = (width02*4)/5
                    wsa.col(4).width = width02
                    wsa.col(5).width = width02*2
                    wsa.col(6).width = (width02*4)/5
                    wsa.col(7).width = width02*6/5
                    wsa.col(8).width = (width02*4)/5
                    wsa.col(9).width = (width02*4)/5
                    wsa.col(10).width = (width02*4)/5
                    wsa.col(11).width = width02/2
                    wsa.col(12).width = (width02*4)/5
                    wsa.col(13).width = (width02*3)/2
                    wsa.col(14).width = width02
                    wsa.col(15).width = width02
                    wsa.col(16).width = width02
                    wsa.col(17).width = width02
                    wsa.col(18).width = (width02*3)/2
                    wsa.col(19).width = (width02*3)/2
                    wsa.col(20).width = (width02*3)/2
                    wsa.col(21).width = (width02*3)/2
                    wsa.col(22).width = width02/2
                    x=22
                    if data['form']['goods_type']=='asset':
                        wsa.col(23).width = width02/2
                        wsa.col(24).width = width02/2
                        x=24
                    col_max = x  
                else:
                    wsa.col(0).width = width01
                    wsa.col(1).width = width01
                    wsa.col(2).width = width02
                    wsa.col(3).width = (width02*4)/5
                    wsa.col(4).width = width02
                    wsa.col(5).width = (width02*4)/5
                    wsa.col(6).width = width02*2
                    wsa.col(7).width = (width02*4)/5
                    wsa.col(8).width = width02*6/5
                    wsa.col(9).width = (width02*4)/5
                    wsa.col(10).width = (width02*4)/5
                    wsa.col(11).width = (width02*4)/5
                    wsa.col(12).width = width02/2
                    wsa.col(13).width = (width02*4)/5
                    wsa.col(14).width = (width02*3)/2
                    wsa.col(15).width = width02
                    wsa.col(16).width = width02
                    wsa.col(17).width = width02
                    wsa.col(18).width = width02
                    wsa.col(19).width = (width02*3)/2
                    wsa.col(20).width = (width02*3)/2
                    wsa.col(21).width = (width02*3)/2
                    wsa.col(22).width = (width02*3)/2
                    wsa.col(23).width = width02/2
                    x=23
                    if data['form']['goods_type']=='asset':
                        wsa.col(24).width = width02/2
                        wsa.col(25).width = width02/2
                        x=25
                    col_max = x  
            else:
                if sheet == 'invoice':
                    wsa.col(0).width = width01
                    wsa.col(1).width = width02
                    wsa.col(2).width = (width02*4)/5
                    wsa.col(3).width = width02
                    wsa.col(4).width = width02*2
                    wsa.col(5).width = (width02*4)/5
                    wsa.col(6).width = width02*2
                    wsa.col(7).width = (width02*3)/5
                    wsa.col(8).width = width02*6/5
                    wsa.col(9).width = (width02*4)/5
                    wsa.col(10).width = width02
                    wsa.col(11).width = width02/2
                    wsa.col(12).width = (width02*4)/5
                    wsa.col(13).width = (width02*4)/5
                    wsa.col(14).width = width02
                    wsa.col(15).width = width02
                    wsa.col(16).width = width02
                    wsa.col(17).width = (width02*3)/2
                    x=17
                    if data['form']['goods_type']=='asset':
                        wsa.col(18).width = (width02*3)/2
                        wsa.col(19).width = (width02*3)/2
                        x=19
                    col_max =x  
                else:
                    wsa.col(0).width = width01
                    wsa.col(1).width = width01
                    wsa.col(2).width = width02
                    wsa.col(3).width = (width02*4)/5
                    wsa.col(4).width = width02
                    wsa.col(5).width = width02
                    wsa.col(6).width = width02*2
                    wsa.col(7).width = (width02*4)/5
                    wsa.col(8).width = width02*2
                    wsa.col(9).width = (width02*3)/5
                    wsa.col(10).width = width02*6/5
                    wsa.col(11).width = (width02*4)/5
                    wsa.col(12).width = width02
                    wsa.col(13).width = width02/2
                    wsa.col(14).width = (width02*4)/5
                    wsa.col(15).width = (width02*4)/5
                    wsa.col(16).width = width02
                    if sheet == 'date':
                        wsa.col(17).width = width02
                        wsa.col(18).width = width02
                        wsa.col(19).width = (width02*3)/2
                        x = 19  
                        if data['form']['goods_type']=='asset':
                            wsa.col(20).width = (width02*3)/2
                            wsa.col(21).width = (width02*3)/2
                            x=21
                    else:
                        wsa.col(17).width = width02
                        wsa.col(18).width = (width02*3)/2
                        x = 18
                        if data['form']['goods_type']=='asset':
                            wsa.col(19).width = (width02*3)/2
                            wsa.col(20).width = (width02*3)/2
                            x=20
                    col_max=x
            
            # Untuk Data Title
            self.xls_write_row(wsa, None, data, parser,0, row_Company, tittle_style)
            self.xls_write_row(wsa, None, data, parser,1, row_Title1, tittle_style)
            self.xls_write_row(wsa, None, data, parser,2, row_Title2, tittle_style)
            self.xls_write_row(wsa, None, data, parser,3, row_Kosong, tittle_style)
            
            # Untuk Data Header
            self.xls_write_row(wsa, None, data, parser,4, row_header, hdr_style)
            
            row_count = 5
            details = parser._get_view(data,sheet)
            loc_kmk_rate = 0.0
            loc_uom_qty = 0.0
            loc_qty_bales = 0.0
            loc_qty_kgs = 0.0
            loc_net_amount = 0.0
            loc_tax_amount = 0.0
            loc_tot_amount = 0.0
            loc_cury_net_amount = 0.0
            loc_cury_tax_amount = 0.0
            loc_cury_tot_amount = 0.0
            loc_tot_amount_idr = 0.0
            loc_tot_amount_usd = 0.0
            loc_dpp_npet = 0.0
            loc_dpp_pet = 0.0
            loc_tax_npet = 0.0
            loc_tax_pet = 0.0
            loc_items = 0
            group_uom_qty = 0.0
            group_qty_bales = 0.0
            group_qty_kgs = 0.0
            group_net_amount = 0.0
            group_tax_amount = 0.0
            group_tot_amount = 0.0
            group_cury_net_amount = 0.0
            group_cury_tax_amount = 0.0
            group_cury_tot_amount = 0.0
            group_tot_amount_idr = 0.0
            group_tot_amount_usd = 0.0
            group_dpp_npet = 0.0
            group_dpp_pet = 0.0
            group_tax_npet = 0.0
            group_tax_pet = 0.0
            group_items = 0
            group_kmk_rate = 0.0
            grand_uom_qty = 0.0
            grand_qty_bales = 0.0
            grand_qty_kgs = 0.0
            grand_net_amount = 0.0
            grand_tax_amount = 0.0
            grand_tot_amount = 0.0
            grand_cury_net_amount = 0.0
            grand_cury_tax_amount = 0.0
            grand_cury_tot_amount = 0.0
            grand_tot_amount_idr = 0.0
            grand_tot_amount_usd = 0.0
            grand_dpp_npet = 0.0
            grand_dpp_pet = 0.0
            grand_tax_npet = 0.0
            grand_tax_pet = 0.0
            grand_items = 0
            old_loc_name = 'None'
            old_group_name = 'None'
            peb_name = ''

            for line in details:   
                if sheet == 'invoice':
                    loc_name = line['invoice_no'] or ''
                    peb_name = line['peb_no'] or ''
                elif sheet == 'country':
                    loc_name = line['dest_country_name'] or ''
                else:
                    loc_name = line['loc_name'] or ''
                if sheet == 'customer':
                    group_name = line['cust_name'] or ''
                elif sheet == 'date':
                    group_name = line['do_date_dmy'] or ''
                elif sheet == 'invoice':
                    group_name = 'None'
                elif sheet == 'country':
                    group_name = line['cust_name'] or ''
                else:
                    group_name = line['blend'] or ''

                if (loc_name != old_loc_name) or (group_name != old_group_name):
                    if data['form']['sale_type'] == 'local':
                        if old_group_name != 'None':
                            if sheet == 'invoice':
                                wsa.write(row_count,0, '', normal_style)        
                                wsa.write_merge(row_count,row_count,1,7, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsa.write(row_count, 8, group_uom_qty, subtotal_style)
                                wsa.write_merge(row_count,row_count,9,12, '', subtotal_style)    
                                wsa.write(row_count, 13, group_cury_net_amount, subtotal_style2)
                                wsa.write(row_count, 14, group_cury_tax_amount, subtotal_style2)
                                wsa.write_merge(row_count,row_count,15,16, '', subtotal_style)    
                                wsa.write(row_count, 17, group_tot_amount_usd, subtotal_style2)
                                wsa.write(row_count, 18, group_tot_amount_idr, subtotal_style2)
                                wsa.write(row_count, 19, group_dpp_npet, subtotal_style2)
                                wsa.write(row_count, 20, group_dpp_pet, subtotal_style2)
                                wsa.write(row_count, 21, group_tax_npet, subtotal_style2)
                                wsa.write(row_count, 22, group_tax_pet, subtotal_style2)
                            else:
                                wsa.write(row_count,0, '', normal_style)        
                                wsa.write_merge(row_count,row_count,1,8, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsa.write(row_count, 9, group_uom_qty, subtotal_style)
                                wsa.write_merge(row_count,row_count,10,13, '', subtotal_style)    
                                wsa.write(row_count, 14, group_cury_net_amount, subtotal_style2)
                                wsa.write(row_count, 15, group_cury_tax_amount, subtotal_style2)
                                wsa.write_merge(row_count,row_count,16,17, '', subtotal_style)    
                                wsa.write(row_count, 18, group_tot_amount_usd, subtotal_style2)
                                wsa.write(row_count, 19, group_tot_amount_idr, subtotal_style2)
                                wsa.write(row_count, 20, group_dpp_npet, subtotal_style2)
                                wsa.write(row_count, 21, group_dpp_pet, subtotal_style2)
                                wsa.write(row_count, 22, group_tax_npet, subtotal_style2)
                                wsa.write(row_count, 23, group_tax_pet, subtotal_style2)
                            row_count+=1    
                            #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                            #row_count+=1
                    else:
                        if old_group_name != 'None':
                            if sheet == 'invoice':
                                wsa.write(row_count,0, '', normal_style)        
                                wsa.write_merge(row_count,row_count,1,8, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsa.write(row_count, 9, group_qty_bales, subtotal_style)
                                wsa.write(row_count, 10, group_qty_kgs, subtotal_style)
                                wsa.write_merge(row_count,row_count,11,15, '', subtotal_style)
                                wsa.write(row_count, 16, group_tot_amount_usd, subtotal_style2)
                                wsa.write(row_count, 17, group_tot_amount_idr, subtotal_style2)
                            else:
                                wsa.write(row_count,0, '', normal_style)        
                                wsa.write_merge(row_count,row_count,1,10, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsa.write(row_count, 11, group_qty_bales, subtotal_style)
                                wsa.write(row_count, 12, group_qty_kgs, subtotal_style)
                                if sheet == 'date':
                                    wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)
                                    if group_items > 0:    
                                        wsa.write(row_count, 17, group_kmk_rate/group_items, subtotal_style2)
                                    else:
                                        wsa.write(row_count, 17, '', subtotal_style2)
                                    wsa.write(row_count, 18, group_tot_amount_usd, subtotal_style2)
                                    wsa.write(row_count, 19, group_tot_amount_idr, subtotal_style2)
                                else:
                                    wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)    
                                    wsa.write(row_count, 17, group_tot_amount_usd, subtotal_style2)
                                    wsa.write(row_count, 18, group_tot_amount_idr, subtotal_style2)
                            row_count+=1    
                            #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                            #row_count+=1

                    if (loc_name != old_loc_name):
                        if data['form']['sale_type'] == 'local':
                            if old_loc_name != 'None':
                                if sheet == 'invoice':
                                    wsa.write_merge(row_count,row_count,0,7, 'Total for ' + old_loc_name, subtotal_title_style)        
                                    wsa.write(row_count, 8, loc_uom_qty, subtotal_style)
                                    wsa.write_merge(row_count,row_count,9,12, '', subtotal_style)    
                                    wsa.write(row_count, 13, loc_cury_net_amount, subtotal_style2)
                                    wsa.write(row_count, 14, loc_cury_tax_amount, subtotal_style2)
                                    wsa.write_merge(row_count,row_count,15,16, '', subtotal_style)    
                                    wsa.write(row_count, 17, loc_tot_amount_usd, subtotal_style2)
                                    wsa.write(row_count, 18, loc_tot_amount_idr, subtotal_style2)
                                    wsa.write(row_count, 19, loc_dpp_npet, subtotal_style2)
                                    wsa.write(row_count, 20, loc_dpp_pet, subtotal_style2)
                                    wsa.write(row_count, 21, loc_tax_npet, subtotal_style2)
                                    wsa.write(row_count, 22, loc_tax_pet, subtotal_style2)
                                else:
                                    wsa.write_merge(row_count,row_count,0,8, 'Total for ' + old_loc_name, subtotal_title_style)        
                                    wsa.write(row_count, 9, loc_uom_qty, subtotal_style)
                                    wsa.write_merge(row_count,row_count,10,13, '', subtotal_style)    
                                    wsa.write(row_count, 14, loc_cury_net_amount, subtotal_style2)
                                    wsa.write(row_count, 15, loc_cury_tax_amount, subtotal_style2)
                                    wsa.write_merge(row_count,row_count,16,17, '', subtotal_style)    
                                    wsa.write(row_count, 18, loc_tot_amount_usd, subtotal_style2)
                                    wsa.write(row_count, 19, loc_tot_amount_idr, subtotal_style2)
                                    wsa.write(row_count, 20, loc_dpp_npet, subtotal_style2)
                                    wsa.write(row_count, 21, loc_dpp_pet, subtotal_style2)
                                    wsa.write(row_count, 22, loc_tax_npet, subtotal_style2)
                                    wsa.write(row_count, 23, loc_tax_pet, subtotal_style2)
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        else:
                            if old_loc_name != 'None':
                                if sheet == 'invoice':
                                    wsa.write_merge(row_count,row_count,0,8, 'Total for ' + old_loc_name, subtotal_title_style)        
                                    wsa.write(row_count, 9, loc_qty_bales, subtotal_style)
                                    wsa.write(row_count, 10, loc_qty_kgs, subtotal_style)
                                    wsa.write_merge(row_count,row_count,11,14, '', subtotal_style)    
                                    if loc_items > 0:    
                                        wsa.write(row_count, 15, loc_kmk_rate/loc_items, subtotal_style2)
                                    else:
                                        wsa.write(row_count, 15, '', subtotal_style2)
                                    wsa.write(row_count, 16, loc_tot_amount_usd, subtotal_style2)
                                    wsa.write(row_count, 17, loc_tot_amount_idr, subtotal_style2)
                                else:
                                    wsa.write_merge(row_count,row_count,0,10, 'Total for ' + old_loc_name, subtotal_title_style)        
                                    wsa.write(row_count, 11, loc_qty_bales, subtotal_style)
                                    wsa.write(row_count, 12, loc_qty_kgs, subtotal_style)
                                    if sheet == 'date':
                                        wsa.write_merge(row_count,row_count,13,17, '', subtotal_style)    
                                        wsa.write(row_count, 18, loc_tot_amount_usd, subtotal_style2)
                                        wsa.write(row_count, 19, loc_tot_amount_idr, subtotal_style2)
                                    else:
                                        wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)    
                                        wsa.write(row_count, 17, loc_tot_amount_usd, subtotal_style2)
                                        wsa.write(row_count, 18, loc_tot_amount_idr, subtotal_style2)
                                row_count+=1    
                                wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                                row_count+=1
                        if sheet == 'invoice' and peb_name:
                            wsa.write_merge(row_count,row_count,0,1, loc_name, group_style)
                            wsa.write(row_count,2, 'PEB Number : ', group_style)
                            wsa.write_merge(row_count,row_count,3,col_max, peb_name, group_style)
                        else:
                            wsa.write_merge(row_count,row_count,0,col_max, loc_name, group_style)
                        row_count+=1

                        old_loc_name = loc_name
                        loc_kmk_rate = 0.0
                        loc_uom_qty = 0.0
                        loc_qty_bales = 0.0
                        loc_qty_kgs = 0.0
                        loc_net_amount = 0.0
                        loc_tax_amount = 0.0
                        loc_tot_amount = 0.0
                        loc_cury_net_amount = 0.0
                        loc_cury_tax_amount = 0.0
                        loc_cury_tot_amount = 0.0
                        loc_tot_amount_idr = 0.0
                        loc_tot_amount_usd = 0.0
                        loc_dpp_npet = 0.0
                        loc_dpp_pet = 0.0
                        loc_tax_npet = 0.0
                        loc_tax_pet = 0.0
                        loc_items = 0
                        group_uom_qty = 0.0
                        group_qty_bales = 0.0
                        group_qty_kgs = 0.0
                        group_net_amount = 0.0
                        group_tax_amount = 0.0
                        group_tot_amount = 0.0
                        group_cury_net_amount = 0.0
                        group_cury_tax_amount = 0.0
                        group_cury_tot_amount = 0.0
                        group_tot_amount_idr = 0.0
                        group_tot_amount_usd = 0.0
                        group_dpp_npet = 0.0
                        group_dpp_pet = 0.0
                        group_tax_npet = 0.0
                        group_tax_pet = 0.0
                        group_items = 0
                        group_kmk_rate = 0.0

                    if group_name != old_group_name:
                        wsa.write(row_count,0, '', group_style)        
                        wsa.write_merge(row_count,row_count,1,col_max, group_name, group_style)
                        row_count+=1

                        old_group_name = group_name
                        group_uom_qty = 0.0
                        group_qty_bales = 0.0
                        group_qty_kgs = 0.0
                        group_net_amount = 0.0
                        group_tax_amount = 0.0
                        group_tot_amount = 0.0
                        group_cury_net_amount = 0.0
                        group_cury_tax_amount = 0.0
                        group_cury_tot_amount = 0.0
                        group_tot_amount_idr = 0.0
                        group_tot_amount_usd = 0.0
                        group_dpp_npet = 0.0
                        group_dpp_pet = 0.0
                        group_tax_npet = 0.0
                        group_tax_pet = 0.0
                        group_items = 0
                        group_kmk_rate = 0.0
                
                #print "****************",line
                base_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                qty_bales = parser._uom_to_bales(line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                qty_kgs = parser._uom_to_kgs(line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                base_net_price = parser._price_per_base(data,line['net_price'] or 0.0,line['product_uom'] or '')
                base_sell_price = parser._price_per_base(data,line['sell_price'] or 0.0,line['product_uom'] or '')
                if qty_bales>0.0:
                    sell_price_idr_bales = round((line['tot_amount_idr'] or 0.0)/qty_bales,2)
                else:
                    sell_price_idr_bales = 0.0
                sell_price_usd_kgs = parser._price_per_kgs(line['sell_price_usd'] or 0.0,line['product_uom'] or '')
                cury_net_price = parser._price_per_base(data,line['cury_net_price'] or 0.0,line['product_uom'] or '')
                cury_sell_price = parser._price_per_base(data,line['cury_sell_price'] or 0.0,line['product_uom'] or '')
                net_amount = line['net_amount'] or 0.0
                tax_amount = line['tax_amount'] or 0.0
                tot_amount = line['tot_amount'] or 0.0
                cury_net_amount = line['cury_net_amount'] or 0.0
                cury_tax_amount = line['cury_tax_amount'] or 0.0
                cury_tot_amount = line['cury_tot_amount'] or 0.0
                kmk_rate = line['kmk_rate'] or 0.0
                # tot_amount_idr = line['tot_amount_idr'] or 0.0
                tot_amount_idr=(line['tot_amount_usd'] or 0.0)*(line['kmk_rate'] or 0.0)
                tot_amount_usd = line['tot_amount_usd'] or 0.0
                dpp_npet = line['dpp_npet'] or 0.0
                dpp_pet = line['dpp_pet'] or 0.0
                tax_npet = line['tax_npet'] or 0.0
                tax_pet = line['tax_pet'] or 0.0

                loc_kmk_rate += kmk_rate
                loc_uom_qty += base_uom_qty
                loc_qty_bales += qty_bales
                loc_qty_kgs += qty_kgs
                loc_net_amount += net_amount
                loc_tax_amount += tax_amount
                loc_tot_amount += tot_amount
                loc_cury_net_amount += cury_net_amount
                loc_cury_tax_amount += cury_tax_amount
                loc_cury_tot_amount += cury_tot_amount
                loc_tot_amount_idr += tot_amount_idr
                loc_tot_amount_usd += tot_amount_usd
                loc_dpp_npet += dpp_npet
                loc_dpp_pet += dpp_pet
                loc_tax_npet += tax_npet
                loc_tax_pet += tax_pet
                loc_items += 1
                group_uom_qty += base_uom_qty
                group_qty_bales += qty_bales
                group_qty_kgs += qty_kgs
                group_net_amount += net_amount
                group_tax_amount += tax_amount
                group_tot_amount += tot_amount
                group_cury_net_amount += cury_net_amount
                group_cury_tax_amount += cury_tax_amount
                group_cury_tot_amount += cury_tot_amount
                group_tot_amount_idr += tot_amount_idr
                group_tot_amount_usd += tot_amount_usd
                group_dpp_npet += dpp_npet
                group_dpp_pet += dpp_pet
                group_tax_npet += tax_npet
                group_tax_pet += tax_pet
                group_items += 1
                group_kmk_rate += kmk_rate
                grand_uom_qty += base_uom_qty
                grand_qty_bales += qty_bales
                grand_qty_kgs += qty_kgs
                grand_net_amount += net_amount
                grand_tax_amount += tax_amount
                grand_tot_amount += tot_amount
                grand_cury_net_amount += cury_net_amount
                grand_cury_tax_amount += cury_tax_amount
                grand_cury_tot_amount += cury_tot_amount
                grand_tot_amount_idr += tot_amount_idr
                grand_tot_amount_usd += tot_amount_usd
                grand_dpp_npet += dpp_npet
                grand_dpp_pet += dpp_pet
                grand_tax_npet += tax_npet
                grand_tax_pet += tax_pet
                grand_items += 1

                if data['form']['sale_type'] == 'local':
                    if sheet == 'invoice':
                        wsa.write(row_count, 0, '', normal_style)
                        wsa.write(row_count, 1, line['do_name'] or '', normal_style)
                        wsa.write(row_count, 2, line['do_date'] or '', normal_style)
                        wsa.write(row_count, 3, line['tax_invc'] or '', normal_style)
                        wsa.write(row_count, 4, line['cust_code'] or '', normal_style)
                        wsa.write(row_count, 5, line['cust_name'] or '', normal_style)
                        wsa.write(row_count, 6, line['prod_code'] or '', normal_style)
                        wsa.write(row_count, 7, line['contract_no'] or '', normal_style)
                        wsa.write(row_count, 8, base_uom_qty or '', normal_right_style)
                        wsa.write(row_count, 9, line['curr_name'] or '', normal_style)
                        wsa.write(row_count, 10, cury_net_price, normal_right_style2)
                        wsa.write(row_count, 11, line['tax_percent'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 12, cury_sell_price, normal_right_style2)
                        wsa.write(row_count, 13, cury_net_amount, normal_right_style2)
                        wsa.write(row_count, 14, cury_tax_amount, normal_right_style2)
                        wsa.write(row_count, 15, line['payment_term_name'] or '', normal_style)
                        wsa.write(row_count, 16, kmk_rate, normal_right_style2)
                        #wsa.write(row_count, 16, '', normal_style)
                        wsa.write(row_count, 17, tot_amount_usd, normal_right_style2)
                        # wsa.write(row_count, 18, tot_amount_idr, normal_right_style2)
                        wsa.write(row_count, 18, tot_amount_usd*kmk_rate, normal_right_style2)                        
                        wsa.write(row_count, 19, dpp_npet, normal_right_style2)
                        wsa.write(row_count, 20, dpp_pet, normal_right_style2)
                        wsa.write(row_count, 21, tax_npet, normal_right_style2)
                        wsa.write(row_count, 22, tax_pet, normal_right_style2)
                        if data['form']['goods_type']=='asset':
                            wsa.write(row_count, 23, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['product_uom_qty'] or '', normal_right_style2)
                            wsa.write(row_count, 24, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['uom'] or '', normal_right_style2)
                    else:
                        wsa.write(row_count, 0, '', normal_style)
                        wsa.write(row_count, 1, '', normal_style)
                        wsa.write(row_count, 2, line['do_name'] or '', normal_style)
                        wsa.write(row_count, 3, line['do_date'] or '', normal_style)
                        wsa.write(row_count, 4, line['tax_invc'] or '', normal_style)
                        wsa.write(row_count, 5, line['cust_code'] or '', normal_style)
                        wsa.write(row_count, 6, line['cust_name'] or '', normal_style)
                        wsa.write(row_count, 7, line['prod_code'] or '', normal_style)
                        wsa.write(row_count, 8, line['contract_no'] or '', normal_style)
                        wsa.write(row_count, 9, base_uom_qty or '', normal_right_style)
                        wsa.write(row_count, 10, line['curr_name'] or '', normal_style)
                        wsa.write(row_count, 11, cury_net_price, normal_right_style2)
                        wsa.write(row_count, 12, line['tax_percent'] or 0.0, normal_right_style2)
                        wsa.write(row_count, 13, cury_sell_price, normal_right_style2)
                        wsa.write(row_count, 14, cury_net_amount, normal_right_style2)
                        wsa.write(row_count, 15, cury_tax_amount, normal_right_style2)
                        wsa.write(row_count, 16, line['payment_term_name'] or '', normal_style)
                        wsa.write(row_count, 17, kmk_rate, normal_right_style2)
                        #wsa.write(row_count, 17, '', normal_style)
                        wsa.write(row_count, 18, tot_amount_usd, normal_right_style2)
                        # wsa.write(row_count, 19, tot_amount_idr, normal_right_style2)
                        wsa.write(row_count, 19, tot_amount_usd*kmk_rate, normal_right_style2)
                        wsa.write(row_count, 20, dpp_npet, normal_right_style2)
                        wsa.write(row_count, 21, dpp_pet, normal_right_style2)
                        wsa.write(row_count, 22, tax_npet, normal_right_style2)
                        wsa.write(row_count, 23, tax_pet, normal_right_style2)
                        if data['form']['goods_type']=='asset':
                            wsa.write(row_count, 24, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['product_uom_qty'] or '', normal_right_style2)
                            wsa.write(row_count, 25, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['uom'] or '', normal_right_style2)

                else:
                    if sheet == 'invoice':
                        wsa.write(row_count, 0, '', normal_style)
                        wsa.write(row_count, 1, line['do_name'] or '', normal_style)
                        wsa.write(row_count, 2, parser._xdate(line['do_date']), normal_style)
                        wsa.write(row_count, 3, line['cust_code'] or '', normal_style)
                        wsa.write(row_count, 4, line['cust_name'] or '', normal_style)
                        wsa.write(row_count, 5, line['prod_code'] or '', normal_style)
                        wsa.write(row_count, 6, line['prod_name'] or '', normal_style)
                        wsa.write(row_count, 7, line['tracking_name'] or '', normal_style)
                        wsa.write(row_count, 8, line['contract_no'] or '', normal_style)
                        wsa.write(row_count, 9, qty_bales, normal_right_style)
                        wsa.write(row_count, 10, qty_kgs, normal_right_style)
                        wsa.write(row_count, 11, line['curr_name'] or '', normal_style)
                        wsa.write(row_count, 12, sell_price_idr_bales, normal_right_style2)
                        wsa.write(row_count, 13, sell_price_usd_kgs, normal_right_style2)
                        wsa.write(row_count, 14, line['payment_term_name'] or '', normal_style)
                        #wsa.write(row_count, 15, kmk_rate, normal_right_style2)
                        wsa.write(row_count, 15, '', normal_style)
                        wsa.write(row_count, 16, tot_amount_usd, normal_right_style2)
                        # wsa.write(row_count, 17, tot_amount_idr, normal_right_style2)
                        wsa.write(row_count, 17, tot_amount_usd*kmk_rate, normal_right_style2)
                        if data['form']['goods_type']=='asset':
                            wsa.write(row_count, 18, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['product_uom_qty'] or '', normal_right_style2)
                            wsa.write(row_count, 19, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['uom'] or '', normal_right_style2)
                    else:
                        wsa.write(row_count, 0, '', normal_style)
                        wsa.write(row_count, 1, '', normal_style)
                        wsa.write(row_count, 2, line['do_name'] or '', normal_style)
                        wsa.write(row_count, 3, parser._xdate(line['do_date']), normal_style)
                        wsa.write(row_count, 4, line['invoice_no'] or '', normal_style)
                        wsa.write(row_count, 5, line['cust_code'] or '', normal_style)
                        wsa.write(row_count, 6, line['cust_name'] or '', normal_style)
                        wsa.write(row_count, 7, line['prod_code'] or '', normal_style)
                        wsa.write(row_count, 8, line['prod_name'] or '', normal_style)
                        wsa.write(row_count, 9, line['tracking_name'] or '', normal_style)
                        wsa.write(row_count, 10, line['contract_no'] or '', normal_style)
                        wsa.write(row_count, 11, qty_bales, normal_right_style)
                        wsa.write(row_count, 12, qty_kgs, normal_right_style)
                        wsa.write(row_count, 13, line['curr_name'] or '', normal_style)
                        wsa.write(row_count, 14, sell_price_idr_bales, normal_right_style2)
                        wsa.write(row_count, 15, sell_price_usd_kgs, normal_right_style2)
                        wsa.write(row_count, 16, line['payment_term_name'] or '', normal_style)
                        if sheet == 'date':
                            #wsa.write(row_count, 17, kmk_rate, normal_right_style2)
                            wsa.write(row_count, 17, '', normal_style)
                            wsa.write(row_count, 18, tot_amount_usd, normal_right_style2)
                            # wsa.write(row_count, 19, tot_amount_idr, normal_right_style2)
                            wsa.write(row_count, 19, tot_amount_usd*kmk_rate, normal_right_style2)
                            if data['form']['goods_type']=='asset':
                                wsa.write(row_count, 20, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['product_uom_qty'] or '', normal_right_style2)
                                wsa.write(row_count, 21, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['uom'] or '', normal_right_style2)
                        else:
                            wsa.write(row_count, 17, tot_amount_usd, normal_right_style2)
                            # wsa.write(row_count, 18, tot_amount_idr, normal_right_style2)
                            wsa.write(row_count, 18, tot_amount_usd*kmk_rate, normal_right_style2)
                            if data['form']['goods_type']=='asset':
                                wsa.write(row_count, 19, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['product_uom_qty'] or '', normal_right_style2)
                                wsa.write(row_count, 20, (line['uom'] !='BALES' and line['uom'] !='KGS') and line['uom'] or '', normal_right_style2)
                row_count+=1
            
            if data['form']['sale_type'] == 'local':
                if old_group_name != 'None':
                    if sheet == 'invoice':
                        wsa.write(row_count,0, '', normal_style)        
                        wsa.write_merge(row_count,row_count,1,7, 'Total for ' + old_group_name, subtotal_title_style)        
                        wsa.write(row_count, 8, group_uom_qty, subtotal_style)
                        wsa.write_merge(row_count,row_count,9,12, '', subtotal_style)    
                        wsa.write(row_count, 13, group_cury_net_amount, subtotal_style2)
                        wsa.write(row_count, 14, group_cury_tax_amount, subtotal_style2)
                        wsa.write_merge(row_count,row_count,15,16, '', subtotal_style)    
                        wsa.write(row_count, 17, group_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 18, group_tot_amount_idr, subtotal_style2)
                        wsa.write(row_count, 19, group_dpp_npet, subtotal_style2)
                        wsa.write(row_count, 20, group_dpp_pet, subtotal_style2)
                        wsa.write(row_count, 21, group_tax_npet, subtotal_style2)
                        wsa.write(row_count, 22, group_tax_pet, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
                    else:
                        wsa.write(row_count,0, '', normal_style)        
                        wsa.write_merge(row_count,row_count,1,8, 'Total for ' + old_group_name, subtotal_title_style)        
                        wsa.write(row_count, 9, group_uom_qty, subtotal_style)
                        wsa.write_merge(row_count,row_count,10,13, '', subtotal_style)    
                        wsa.write(row_count, 14, group_cury_net_amount, subtotal_style2)
                        wsa.write(row_count, 15, group_cury_tax_amount, subtotal_style2)
                        wsa.write_merge(row_count,row_count,16,17, '', subtotal_style)    
                        wsa.write(row_count, 18, group_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 19, group_tot_amount_idr, subtotal_style2)
                        wsa.write(row_count, 20, group_dpp_npet, subtotal_style2)
                        wsa.write(row_count, 21, group_dpp_pet, subtotal_style2)
                        wsa.write(row_count, 22, group_tax_npet, subtotal_style2)
                        wsa.write(row_count, 23, group_tax_pet, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
            else:
                if old_group_name != 'None':
                    wsa.write(row_count,0, '', normal_style)        
                    wsa.write_merge(row_count,row_count,1,10, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsa.write(row_count, 11, group_qty_bales, subtotal_style)
                    wsa.write(row_count, 12, group_qty_kgs, subtotal_style)
                    if sheet == 'date':
                        wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)
                        if group_items > 0:    
                            wsa.write(row_count, 17, group_kmk_rate/group_items, subtotal_style2)
                        else:
                            wsa.write(row_count, 17, '', subtotal_style2)
                        wsa.write(row_count, 18, group_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 19, group_tot_amount_idr, subtotal_style2)
                    else:
                        wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)    
                        wsa.write(row_count, 17, group_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 18, group_tot_amount_idr, subtotal_style2)
                    row_count+=1    
                    #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                    #row_count+=1

            if data['form']['sale_type'] == 'local':
                if sheet == 'invoice':
                    if old_loc_name != 'None':
                        wsa.write_merge(row_count,row_count,0,7, 'Total for ' + old_loc_name, subtotal_title_style)        
                        wsa.write(row_count, 8, loc_uom_qty, subtotal_style)
                        wsa.write_merge(row_count,row_count,9,12, '', subtotal_style)    
                        wsa.write(row_count, 13, loc_cury_net_amount, subtotal_style2)
                        wsa.write(row_count, 14, loc_cury_tax_amount, subtotal_style2)
                        wsa.write_merge(row_count,row_count,15,16, '', subtotal_style)    
                        wsa.write(row_count, 17, loc_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 18, loc_tot_amount_idr, subtotal_style2)
                        wsa.write(row_count, 19, loc_dpp_npet, subtotal_style2)
                        wsa.write(row_count, 20, loc_dpp_pet, subtotal_style2)
                        wsa.write(row_count, 21, loc_tax_npet, subtotal_style2)
                        wsa.write(row_count, 22, loc_tax_pet, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
                    wsa.write_merge(row_count,row_count,0,7, 'GRAND TOTAL', total_title_style)        
                    wsa.write(row_count, 8, grand_uom_qty, total_style)
                    wsa.write_merge(row_count,row_count,9,12, '', total_style)    
                    wsa.write(row_count, 13, grand_cury_net_amount, total_style2)
                    wsa.write(row_count, 14, grand_cury_tax_amount, total_style2)
                    wsa.write_merge(row_count,row_count,15,16, '', total_style)    
                    wsa.write(row_count, 17, grand_tot_amount_usd, total_style2)
                    wsa.write(row_count, 18, grand_tot_amount_idr, total_style2)
                    wsa.write(row_count, 19, grand_dpp_npet, total_style2)
                    wsa.write(row_count, 20, grand_dpp_pet, total_style2)
                    wsa.write(row_count, 21, grand_tax_npet, total_style2)
                    wsa.write(row_count, 22, grand_tax_pet, total_style2)
                    if data['form']['goods_type']=='asset':
                        wsa.write(row_count, 23, '', total_style2)
                        wsa.write(row_count, 24, '', total_style2)
                else:
                    if old_loc_name != 'None':
                        wsa.write_merge(row_count,row_count,0,8, 'Total for ' + old_loc_name, subtotal_title_style)        
                        wsa.write(row_count, 9, loc_uom_qty, subtotal_style)
                        wsa.write_merge(row_count,row_count,10,13, '', subtotal_style)    
                        wsa.write(row_count, 14, loc_cury_net_amount, subtotal_style2)
                        wsa.write(row_count, 15, loc_cury_tax_amount, subtotal_style2)
                        wsa.write_merge(row_count,row_count,16,17, '', subtotal_style)    
                        wsa.write(row_count, 18, loc_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 19, loc_tot_amount_idr, subtotal_style2)
                        wsa.write(row_count, 20, loc_dpp_npet, subtotal_style2)
                        wsa.write(row_count, 21, loc_dpp_pet, subtotal_style2)
                        wsa.write(row_count, 22, loc_tax_npet, subtotal_style2)
                        wsa.write(row_count, 23, loc_tax_pet, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
                    wsa.write_merge(row_count,row_count,0,8, 'GRAND TOTAL', total_title_style)        
                    wsa.write(row_count, 9, grand_uom_qty, total_style)
                    wsa.write_merge(row_count,row_count,10,13, '', total_style)    
                    wsa.write(row_count, 14, grand_cury_net_amount, total_style2)
                    wsa.write(row_count, 15, grand_cury_tax_amount, total_style2)
                    wsa.write_merge(row_count,row_count,16,17, '', total_style)    
                    wsa.write(row_count, 18, grand_tot_amount_usd, total_style2)
                    wsa.write(row_count, 19, grand_tot_amount_idr, total_style2)
                    wsa.write(row_count, 20, grand_dpp_npet, total_style2)
                    wsa.write(row_count, 21, grand_dpp_pet, total_style2)
                    wsa.write(row_count, 22, grand_tax_npet, total_style2)
                    wsa.write(row_count, 23, grand_tax_pet, total_style2)
                    if data['form']['goods_type']=='asset':
                        wsa.write(row_count, 24, '', total_style2)
                        wsa.write(row_count, 25, '', total_style2)
            else:
                if sheet == 'invoice':
                    if old_loc_name != 'None':
                        wsa.write_merge(row_count,row_count,0,8, 'Total for ' + old_loc_name, subtotal_title_style)        
                        wsa.write(row_count, 9, loc_qty_bales, subtotal_style)
                        wsa.write(row_count, 10, loc_qty_kgs, subtotal_style)
                        wsa.write_merge(row_count,row_count,11,14, '', subtotal_style)    
                        if loc_items > 0:    
                            wsa.write(row_count, 15, loc_kmk_rate/loc_items, subtotal_style2)
                        else:
                            wsa.write(row_count, 15, '', subtotal_style2)
                        wsa.write(row_count, 16, loc_tot_amount_usd, subtotal_style2)
                        wsa.write(row_count, 17, loc_tot_amount_idr, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
                    wsa.write_merge(row_count,row_count,0,8, 'GRAND TOTAL', total_title_style)        
                    wsa.write(row_count, 9, grand_qty_bales, total_style)
                    wsa.write(row_count, 10, grand_qty_kgs, total_style)
                    wsa.write_merge(row_count,row_count,11,15, '', total_style)    
                    wsa.write(row_count, 16, grand_tot_amount_usd, total_style2)
                    wsa.write(row_count, 17, grand_tot_amount_idr, total_style2)
                    if data['form']['goods_type']=='asset':
                        wsa.write(row_count, 18, '', total_style2)
                        wsa.write(row_count, 19, '', total_style2)
                else:
                    if old_loc_name != 'None':
                        wsa.write_merge(row_count,row_count,0,10, 'Total for ' + old_loc_name, subtotal_title_style)        
                        wsa.write(row_count, 11, loc_qty_bales, subtotal_style)
                        wsa.write(row_count, 12, loc_qty_kgs, subtotal_style)
                        if sheet == 'date':
                            wsa.write_merge(row_count,row_count,13,17, '', subtotal_style)    
                            wsa.write(row_count, 18, loc_tot_amount_usd, subtotal_style2)
                            wsa.write(row_count, 19, loc_tot_amount_idr, subtotal_style2)
                        else:
                            wsa.write_merge(row_count,row_count,13,16, '', subtotal_style)    
                            wsa.write(row_count, 17, loc_tot_amount_usd, subtotal_style2)
                            wsa.write(row_count, 18, loc_tot_amount_idr, subtotal_style2)
                        row_count+=1    
                        #wsa.write_merge(row_count,row_count,0,col_max, '', normal_style)
                        #row_count+=1
                    wsa.write_merge(row_count,row_count,0,10, 'GRAND TOTAL', total_title_style)        
                    wsa.write(row_count, 11, grand_qty_bales, total_style)
                    wsa.write(row_count, 12, grand_qty_kgs, total_style)
                    if sheet == 'date':
                        wsa.write_merge(row_count,row_count,13,17, '', total_style)    
                        wsa.write(row_count, 18, grand_tot_amount_usd, total_style2)
                        wsa.write(row_count, 19, grand_tot_amount_idr, total_style2)
                        if data['form']['goods_type']=='asset':
                            wsa.write(row_count, 23, '', total_style2)
                            wsa.write(row_count, 24, '', total_style2)
                    else:
                        wsa.write_merge(row_count,row_count,13,16, '', total_style)    
                        wsa.write(row_count, 17, grand_tot_amount_usd, total_style2)
                        wsa.write(row_count, 18, grand_tot_amount_idr, total_style2)
                        if data['form']['goods_type']=='asset':
                            wsa.write(row_count, 23, '', total_style2)
                            wsa.write(row_count, 24, '', total_style2)
            
        pass

# from netsvc import Service
# del Service._services['report.Sales Report']
sales_report_xls('report.sales.report',
                 'report.sales.wizard', 'addons/ad_sales_report/report/sales_report.mako',
                 parser=ReportSalesOrder)