# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from report import report_sxw
from ad_sales_report.report.pending_sales_report_parser import pending_sales_parser

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class pending_sales_report_xls(report_xls):
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
        if data['form']['report_type'] == 'customer':
            sheets = ['customer']
        elif data['form']['report_type'] == 'product':
            sheets = ['product']
        elif data['form']['report_type'] == 'contract':
            sheets = ['contract']
        else:
            sheets = ['customer', 'product', 'contract']
        uom_base = parser._get_uom_base(data)
        price_base = parser._get_price_base(data)        
        
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
        subtittle_left_style            = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_right_style           = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; pattern: pattern solid, fore_color white;')
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
        subtotal_style1                 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom dotted;',num_format_str='#,##0.00;(#,##0.00)')
        total_title_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
        total_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
        total_style1                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        ## Style variable End
        min_bale_bal_qty = 5.0

        for sheet in sheets:
            report_title = parser._get_title(sheet) + ' As On : ' + parser._xdate(data['form']['as_on'])
            if data['form']['sale_type'] == 'export':
                sale_type = 'Type : ' + 'Export'
            else:
                sale_type = 'Type : ' + 'Local'
            
            if sheet == 'customer':
                cols_specs = [
                        #title
                        ('Company',  21, 0, 'text', lambda x, d, p: company_name),
                        ('Title',  21, 0, 'text', lambda x, d, p: report_title),
                        ('Type',  21, 0, 'text', lambda x, d, p: sale_type),
                        ('Kosong', 21, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerProduct',  2, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerProductdescr',  1, 0, 'text', lambda x, d, p: 'Description'),
                        # ('headerBlendCount',  1, 0, 'text', lambda x, d, p: 'Blend-Count'),
                        ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                        ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                        ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Destination'),
                        ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                        ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                        ('headerUOMBaseName',  1, 0, 'text', lambda x, d, p: uom_base),
                        ('headerBalance',  1, 0, 'text', lambda x, d, p: 'Amt'),
                        ('headerLCQty',  1, 0, 'text', lambda x, d, p: 'LC Qty'),
                        ('headerPriceBase',  1, 0, 'text', lambda x, d, p: price_base),
                        ('headerIncoterm',  1, 0, 'text', lambda x, d, p: 'Delv Term'),
                        ('headerContainer',  1, 0, 'text', lambda x, d, p: 'CTR'),
                        ('headerComm',  1, 0, 'text', lambda x, d, p: '(%)'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay Term'),
                        ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Pay Recd Date'),
                        ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'Pay LSD'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title               = self.xls_row_template(cols_specs, ['Title'])
                row_Type                = self.xls_row_template(cols_specs, ['Type'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                row_header              = self.xls_row_template(cols_specs, ['headerProduct','headerProductdescr','headerContractNo',
                                                                             'headerContractDate','headerDestination',
                                                                             'headerLSD','headerLSDR','headerPackingType',
                                                                             'headerConeWidth','headerUOMBaseName','headerBalance','headerLCQty',
                                                                             'headerPriceBase','headerIncoterm','headerContainer','headerComm',
                                                                             'headerPayTerm','headerPayRecdDate','headerPayLSD',
                                                                             'headerRemarks'])

                wsa = wb.add_sheet(('Customer Wise'))    

                wsa.panes_frozen = True
                wsa.remove_splits = True
                wsa.portrait = 0 # Landscape
                wsa.fit_width_to_pages = 1

                # set print header/footer
                wsa.header_str = ''
                wsa.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

                wsa.col(0).width = len("ABCDEFG")*128
                wsa.col(1).width = len("ABCDEFG")*512
                
                # Untuk Data Title
                self.xls_write_row(wsa, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsa, None, data, parser,1, row_Title, tittle_style)
                self.xls_write_row(wsa, None, data, parser,2, row_Type, subtittle_left_style)
                self.xls_write_row(wsa, None, data, parser,3, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsa, None, data, parser,4, row_header, hdr_style)
                
                row_count = 5
                # print "=============",data,sheet
                details = parser._get_view(data,sheet)
                # print "::::::::::::::::::::::::", details
                group_product_uom_qty = 0.0
                group_bal_qty = 0.0
                grand_product_uom_qty = 0.0
                grand_bal_qty = 0.0
                old_group_name = False

                for line in details:   
                    base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    lc_qty = parser._uom_to_base(data,line['lc_qty'] or 0.0,line['product_uom'] or '')
                    bale_shipped_qty = parser._uom_to_base(data,line['shipped_qty'] or 0.0,line['product_uom'] or '')
                    if base_bal_qty <= min_bale_bal_qty and bale_shipped_qty>0.0:
                        continue
                    group_name = line['customer_name'] or ''
                    if group_name != old_group_name:
                        if old_group_name:
                            # wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            # wsa.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                            # wsa.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                            # wsa.write_merge(row_count,row_count,12,20, '', subtotal_style)    
                            # row_count+=1    
                            # wsa.write_merge(row_count,row_count,0,20, '', normal_style)
                            wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsa.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                            wsa.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                            wsa.write_merge(row_count,row_count,12,20, '', subtotal_style)    
                            row_count+=1    
                            wsa.write_merge(row_count,row_count,0,20, '', normal_style)
                            row_count+=1
                        wsa.write_merge(row_count,row_count,0,20, group_name, group_style)
                        row_count+=1
                        old_group_name = group_name
                        group_product_uom_qty = 0.0
                        group_bal_qty = 0.0
                    

                    group_product_uom_qty = group_product_uom_qty+base_product_uom_qty
                    group_bal_qty = group_bal_qty+base_bal_qty
                    grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty
                    grand_bal_qty = grand_bal_qty+base_bal_qty

                    # wsa.write(row_count, 1, line['product_name'] or '', normal_style)
                    # wsa.write(row_count, 2, (line['blend_count'] or '') , normal_style)
                    # wsa.write(row_count, 3, line['name'] or '', normal_style)
                    # wsa.write(row_count, 4, parser._xdate(line['date_order']), normal_style)
                    # wsa.write(row_count, 5, line['destination'] or '', normal_style)
                    # wsa.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    # wsa.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    # wsa.write(row_count, 8, line['packing_name'] or '', normal_style)
                    # wsa.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    # wsa.write(row_count, 10, "{:.4f}".format(base_product_uom_qty), normal_right_style)
                    # wsa.write(row_count, 11, "{:.4f}".format(base_bal_qty), normal_right_style)
                    # wsa.write(row_count, 12, "{:.4f}".format(lc_qty), normal_right_style)
                    # wsa.write(row_count, 13, "{:.4f}".format(parser._price_per_base(data,line['price_unit'] or 0.0,line['product_uom'] or '')), normal_right_style)
                    # wsa.write(row_count, 14, line['incoterm'] or '', normal_style)
                    # wsa.write(row_count, 15, line['container_size_name'] or '', normal_right_style)
                    # wsa.write(row_count, 16, "{:.2f}".format(line['commission_percentage'] or 0.0), normal_right_style2) 
                    # wsa.write(row_count, 17, line['payment_term_name'] or '', normal_right_style)
                    # wsa.write(row_count, 18, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    # wsa.write(row_count, 19, parser._xdate(line['lc_lsd']), normal_right_style)
                    # wsa.write(row_count, 20, line['remarks'] or '', normal_style)
                    wsa.write(row_count, 1, line['product_name'] or '', normal_style)
                    wsa.write(row_count,2,line['product_descr'] or '', normal_style)
                    # wsa.write(row_count, 2, (line['blend_count'] or '') , normal_style)
                    wsa.write(row_count, 3, line['name'] or '', normal_style)
                    wsa.write(row_count, 4, parser._xdate(line['date_order']), normal_style)
                    wsa.write(row_count, 5, line['destination'] or '', normal_style)
                    wsa.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    wsa.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    wsa.write(row_count, 8, line['packing_name'] or '', normal_style)
                    wsa.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    wsa.write(row_count, 10, "{:.4f}".format(base_product_uom_qty), normal_right_style)
                    wsa.write(row_count, 11, "{:.4f}".format(base_bal_qty), normal_right_style)
                    wsa.write(row_count, 12, "{:.4f}".format(lc_qty), normal_right_style)
                    wsa.write(row_count, 13, "{:.4f}".format(parser._price_per_base(data,line['price_unit'] or 0.0,line['product_uom'] or '')), normal_right_style)
                    wsa.write(row_count, 14, line['incoterm'] or '', normal_style)
                    wsa.write(row_count, 15, line['container_size_name'] or '', normal_right_style)
                    wsa.write(row_count, 16, "{:.2f}".format(line['commission_percentage'] or 0.0), normal_right_style2) 
                    wsa.write(row_count, 17, line['payment_term_name'] or '', normal_right_style)
                    wsa.write(row_count, 18, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    wsa.write(row_count, 19, parser._xdate(line['lc_lsd']), normal_right_style)
                    wsa.write(row_count, 20, line['remarks'] or '', normal_style)
                    row_count+=1
                
                if old_group_name:
                    # wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    # wsa.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                    # wsa.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                    # wsa.write_merge(row_count,row_count,12,20, '', subtotal_style)  
                    wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsa.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                    wsa.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                    wsa.write_merge(row_count,row_count,12,20, '', subtotal_style)          
                    row_count+=1 
                
                # wsa.write_merge(row_count,row_count,0,9, 'GRAND TOTAL', total_title_style)        
                # wsa.write(row_count, 10, "{:.4f}".format(grand_product_uom_qty), total_style)
                # wsa.write(row_count, 11, "{:.4f}".format(grand_bal_qty), total_style)
                # wsa.write_merge(row_count,row_count,12,20, '', total_style)   
                wsa.write_merge(row_count,row_count,0,9, 'GRAND TOTAL', total_title_style)        
                wsa.write(row_count, 10, "{:.4f}".format(grand_product_uom_qty), total_style)
                wsa.write(row_count, 11, "{:.4f}".format(grand_bal_qty), total_style)
                wsa.write_merge(row_count,row_count,12,20, '', total_style)     
            elif sheet == 'product':
                if data['form']['sale_type'] == 'export':
                    cols_specs = [
                            #title
                            ('Company',  27, 0, 'text', lambda x, d, p: company_name),
                            ('Title',  27, 0, 'text', lambda x, d, p: report_title),
                            ('Type',  27, 0, 'text', lambda x, d, p: sale_type),
                            ('Kosong', 27, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerBlend',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerBlendCount',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerSDType',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                            ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                            ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                            ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Dest.'),
                            ('headerPeriod',  1, 0, 'text', lambda x, d, p: 'Period'),
                            ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                            ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                            ('headerQty',  1, 0, 'text', lambda x, d, p: 'Bales'),
                            ('headerBalQty',  1, 0, 'text', lambda x, d, p: 'Balance'),
                            ('headerPriceBase',  1, 0, 'text', lambda x, d, p: 'Ccy'),
                            ('headerPriceKG',  1, 0, 'text', lambda x, d, p: 'US$/KG'),
                            ('headerDelvTerm',  1, 0, 'text', lambda x, d, p: 'Delv. Term'),
                            ('headerComm',  1, 0, 'text', lambda x, d, p: '(%)'),
                            ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay. Term'),
                            ('headerLCQty',  1, 0, 'text', lambda x, d, p: 'LC Qty'),
                            ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Recd. Date'),
                            ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                            ('headerExpiry',  1, 0, 'text', lambda x, d, p: 'Expiry'),
                            ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/C'),
                            ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                            ('headerStatus',  1, 0, 'text', lambda x, d, p: 'Status'),
                            ('headerRef',  1, 0, 'text', lambda x, d, p: 'Ref'),
                            ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                    ]

                ##Penempatan untuk template rows
                    row_Company             = self.xls_row_template(cols_specs, ['Company'])
                    row_Title               = self.xls_row_template(cols_specs, ['Title'])
                    row_Type                = self.xls_row_template(cols_specs, ['Type'])
                    row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                    row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                    #============================================================================
                    row_header              = self.xls_row_template(cols_specs, ['headerBlend','headerBlendCount','headerSDType',
                                                                                'headerProduct','headerContractNo',
                                                                                'headerContractDate','headerCustomer',
                                                                                'headerDestination','headerPeriod',
                                                                                'headerLSD','headerLSDR',
                                                                                'headerQty','headerBalQty',
                                                                                'headerPriceBase','headerPriceKG',
                                                                                'headerDelvTerm',
                                                                                'headerComm','headerPayTerm',
                                                                                'headerLCQty','headerPayRecdDate',
                                                                                'headerPayLSD','headerExpiry',
                                                                                'headerPackingType','headerConeWidth',
                                                                                'headerStatus',
                                                                                'headerRef','headerRemarks'])
                else:
                    cols_specs = [
                            #title
                            ('Company',  17, 0, 'text', lambda x, d, p: company_name),
                            ('Title',  17, 0, 'text', lambda x, d, p: report_title),
                            ('Type',  17, 0, 'text', lambda x, d, p: sale_type),
                            ('Kosong', 17, 0, 'text',lambda x, d, p: ' '),
                            ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                                  
                            #header
                            ('headerBlend',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerBlendCount',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerSDType',  1, 0, 'text', lambda x, d, p: ''),
                            ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                            ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                            ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                            ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                            ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Dest.'),
                            ('headerPeriod',  1, 0, 'text', lambda x, d, p: 'Period'),
                            ('headerQty',  1, 0, 'text', lambda x, d, p: 'Bales'),
                            ('headerBalQty',  1, 0, 'text', lambda x, d, p: 'Balance'),
                            ('headerPriceBase',  1, 0, 'text', lambda x, d, p: 'Ccy'),
                            ('headerPriceBale',  1, 0, 'text', lambda x, d, p: 'US$/BALES'),
                            ('headerComm',  1, 0, 'text', lambda x, d, p: '(%)'),
                            ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay. Term'),
                            ('headerRef',  1, 0, 'text', lambda x, d, p: 'Ref'),
                            ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                    ]

                ##Penempatan untuk template rows
                    row_Company             = self.xls_row_template(cols_specs, ['Company'])
                    row_Title               = self.xls_row_template(cols_specs, ['Title'])
                    row_Type                = self.xls_row_template(cols_specs, ['Type'])
                    row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                    row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                    #============================================================================
                    row_header              = self.xls_row_template(cols_specs, ['headerBlend','headerBlendCount','headerSDType',
                                                                                'headerProduct','headerContractNo',
                                                                                'headerContractDate','headerCustomer',
                                                                                'headerDestination','headerPeriod',
                                                                                'headerQty','headerBalQty',
                                                                                'headerPriceBase','headerPriceBale',
                                                                                'headerComm','headerPayTerm',
                                                                                'headerRef','headerRemarks'])

                wsb = wb.add_sheet(('Product Wise'))

                wsb.panes_frozen = True
                wsb.remove_splits = True
                wsb.portrait = 0 # Landscape
                wsb.fit_width_to_pages = 1

                # set print header/footer
                wsb.header_str = ''
                wsb.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

                width0 = len("ABCDEFG")*512
                
                if data['form']['sale_type'] == 'export':
                    wsb.col(0).width = width0/4
                    wsb.col(1).width = width0/4
                    wsb.col(2).width = width0/4
                    wsb.col(3).width = 5*width0/2
                    wsb.col(4).width = 2*width0
                    wsb.col(5).width = width0
                    wsb.col(6).width = 2*width0
                    wsb.col(7).width = width0
                    wsb.col(8).width = width0
                    wsb.col(9).width = width0
                    wsb.col(10).width = width0
                    wsb.col(11).width = width0
                    wsb.col(12).width = width0
                    wsb.col(13).width = width0
                    wsb.col(14).width = width0
                    wsb.col(15).width = width0
                    wsb.col(16).width = width0
                    wsb.col(17).width = width0
                    wsb.col(18).width = width0
                    wsb.col(19).width = width0
                    wsb.col(20).width = width0
                    wsb.col(21).width = width0
                    wsb.col(22).width = width0
                    wsb.col(23).width = width0
                    wsb.col(24).width = width0
                    wsb.col(25).width = 3*width0/2
                    wsb.col(26).width = 3*width0

                    row_count = 0
                    details = parser._get_view(data,sheet)
                    sub3_qty = 0.0
                    sub3_bal_qty = 0.0
                    sub3_lcqty = 0.0
                    sub2_qty = 0.0
                    sub2_bal_qty = 0.0
                    sub2_lcqty = 0.0
                    sub1_qty = 0.0
                    sub1_bal_qty = 0.0
                    sub1_lcqty = 0.0
                    group_qty = 0.0
                    group_bal_qty = 0.0
                    group_lcqty = 0.0
                    old_sub3_name = False
                    old_sub2_name = False
                    old_sub1_name = False
                    old_group_name = False

                    # Untuk Data Title
                    self.xls_write_row(wsb, None, data, parser,row_count, row_Company, tittle_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+1, row_Title, tittle_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+2, row_Type, subtittle_left_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+3, row_Kosong, tittle_style)
                    

                    # Untuk Data Header
                    self.xls_write_row(wsb, None, data, parser,row_count+4, row_header, hdr_style)

                    row_count+=5

                    for line in details:   
                        bal_qty = parser._uom_to_bales(line['bal_qty'] or 0.0,line['product_uom'] or '')
                        shipped_qty = parser._uom_to_bales(line['shipped_qty'] or 0.0,line['product_uom'] or '')
                        if bal_qty <= min_bale_bal_qty and shipped_qty>0.0:
                            continue
                        qty = parser._uom_to_bales(line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                        lcqty = parser._uom_to_bales(line['lc_qty'] or 0.0,line['product_uom'] or '')
                        
                        sub3_name = line['blend_count_sd'] or ''
                        sub2_name = line['blend_count'] or ''
                        sub1_name = line['blend'] or ''
                        group_name = line['loc_name'] or ''
                                                                                                
                        if (group_name != old_group_name) or (sub1_name != old_sub1_name) or (sub2_name != old_sub2_name) or (sub3_name != old_sub3_name):
                            if old_sub3_name:
                                wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                                wsb.write_merge(row_count,row_count,3,10, 'Sub Total for ' + old_sub3_name, subtotal_title_style)        
                                wsb.write(row_count, 11, "{:.2f}".format(sub3_qty), subtotal_style)
                                wsb.write(row_count, 12, "{:.2f}".format(sub3_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                                wsb.write(row_count, 18, "{:.2f}".format(sub3_lcqty), subtotal_style)
                                wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,26, '', normal_style)
                                #row_count+=1

                        if (group_name != old_group_name) or (sub1_name != old_sub1_name) or (sub2_name != old_sub2_name):
                            if old_sub2_name:
                                wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                                wsb.write_merge(row_count,row_count,2,10, 'Sub Total for ' + old_sub2_name, subtotal_title_style)        
                                wsb.write(row_count, 11, "{:.2f}".format(sub2_qty), subtotal_style)
                                wsb.write(row_count, 12, "{:.2f}".format(sub2_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                                wsb.write(row_count, 18, "{:.2f}".format(sub2_lcqty), subtotal_style)
                                wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,26, '', normal_style)
                                #row_count+=1

                        if (group_name != old_group_name) or (sub1_name != old_sub1_name):
                            if old_sub1_name:
                                wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                                wsb.write_merge(row_count,row_count,1,10, 'Sub Total for ' + old_sub1_name, subtotal_title_style)        
                                wsb.write(row_count, 11, "{:.2f}".format(sub1_qty), subtotal_style)
                                wsb.write(row_count, 12, "{:.2f}".format(sub1_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                                wsb.write(row_count, 18, "{:.2f}".format(sub1_lcqty), subtotal_style)
                                wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,26, '', normal_style)
                                #row_count+=1

                        if group_name != old_group_name:
                            if old_group_name:
                                wsb.write_merge(row_count,row_count,0,10, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsb.write(row_count, 11, "{:.2f}".format(group_qty), subtotal_style)
                                wsb.write(row_count, 12, "{:.2f}".format(group_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                                wsb.write(row_count, 18, "{:.2f}".format(group_lcqty), subtotal_style)
                                wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                                row_count+=1      
                                wsb.write_merge(row_count,row_count,0,26, '', normal_style)
                                row_count+=1
                            
                            wsb.write_merge(row_count,row_count,0,26, 'Unit : ' + group_name, group_style)
                            row_count+=1
                            #wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                            #wsb.write_merge(row_count,row_count,1,26, sub1_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,26, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,26, sub3_name, group_style)
                            #row_count+=1
                            group_qty = 0.0
                            group_bal_qty = 0.0
                            group_lcqty = 0.0
                            sub1_qty = 0.0
                            sub1_bal_qty = 0.0
                            sub1_lcqty = 0.0
                            sub2_qty = 0.0
                            sub2_bal_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_bal_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub1_name != old_sub1_name:
                            #wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                            #wsb.write_merge(row_count,row_count,1,26, sub1_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,26, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,26, sub3_name, group_style)
                            #row_count+=1
                            sub1_qty = 0.0
                            sub1_bal_qty = 0.0
                            sub1_lcqty = 0.0
                            sub2_qty = 0.0
                            sub2_bal_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_bal_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub2_name != old_sub2_name:
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,26, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,26, sub3_name, group_style)
                            #row_count+=1
                            sub2_qty = 0.0
                            sub2_bal_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_bal_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub3_name != old_sub3_name:
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,26, sub3_name, group_style)
                            #row_count+=1
                            sub3_qty = 0.0
                            sub3_bal_qty = 0.0
                            sub3_lcqty = 0.0

                        old_group_name = group_name
                        old_sub1_name = sub1_name
                        old_sub2_name = sub2_name
                        old_sub3_name = sub3_name

                        sub3_qty += qty
                        sub3_bal_qty += bal_qty                        
                        sub3_lcqty += lcqty
                        sub2_qty += qty
                        sub2_bal_qty += bal_qty                        
                        sub2_lcqty += lcqty
                        sub1_qty += qty
                        sub1_bal_qty += bal_qty                        
                        sub1_lcqty += lcqty
                        group_qty += qty
                        group_bal_qty += bal_qty                        
                        group_lcqty += lcqty

                        wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                        wsb.write(row_count, 3, line['product_descr'] or '', normal_style)
                        wsb.write(row_count, 4, line['name'] or '', normal_style)
                        wsb.write(row_count, 5, parser._xdate(line['date_order']), normal_style)
                        wsb.write(row_count, 6, line['customer_name'] or '', normal_style)
                        wsb.write(row_count, 7, line['destination'] or '', normal_style)
                        wsb.write(row_count, 8, line['sale_order_lsp'], normal_style)
                        wsb.write(row_count, 9, parser._xdate(line['sale_order_lsd']), normal_style)
                        wsb.write(row_count, 10, parser._xdate(line['sale_order_scd']), normal_style)
                        wsb.write(row_count, 11, "{:.2f}".format(qty), normal_right_style)
                        wsb.write(row_count, 12, "{:.2f}".format(bal_qty), normal_right_style)
                        if (line['cury_name'] or '') == 'USD':                            
                            wsb.write(row_count, 13, '', normal_right_style)
                        else:
                            wsb.write(row_count, 13, "{:.4f}".format(line['price_unit'] or 0.0), normal_right_style)
                        wsb.write(row_count, 14, "{:.4f}".format(parser._price_per_kgs(line['price_unit_usd'] or 0.0,line['product_uom'] or '')), normal_right_style)
                        wsb.write(row_count, 15, line['incoterm'] or '', normal_style)
                        wsb.write(row_count, 16, "{:.2f}".format(line['commission_percentage'] or 0.0), normal_right_style2) 
                        wsb.write(row_count, 17, line['payment_term_name'] or '', normal_right_style)
                        wsb.write(row_count, 18, "{:.2f}".format(lcqty), normal_right_style)
                        wsb.write(row_count, 19, parser._xdate(line['lc_recvd_date']), normal_right_style)
                        wsb.write(row_count, 20, parser._xdate(line['lc_lsd']), normal_right_style)
                        wsb.write(row_count, 21, parser._xdate(line['lc_expiry_date']), normal_right_style)
                        wsb.write(row_count, 22, line['packing_name'] or '', normal_style)
                        wsb.write(row_count, 23, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                        wsb.write(row_count, 24, line['order_state'] or '', normal_style)
                        wsb.write(row_count, 25, line['book_by'] or '', normal_style)
                        wsb.write(row_count, 26, line['other_description'] or '', normal_style)
                        row_count+=1
                    
                    if old_sub3_name:
                        wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                        wsb.write_merge(row_count,row_count,3,10, 'Sub Total for ' + old_sub3_name, subtotal_title_style)        
                        wsb.write(row_count, 11, "{:.2f}".format(sub3_qty), subtotal_style)
                        wsb.write(row_count, 12, "{:.2f}".format(sub3_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                        wsb.write(row_count, 18, "{:.2f}".format(sub3_lcqty), subtotal_style)
                        wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                        row_count+=1      

                    if old_sub2_name:
                        wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                        wsb.write_merge(row_count,row_count,2,10, 'Sub Total for ' + old_sub2_name, subtotal_title_style)        
                        wsb.write(row_count, 11, "{:.2f}".format(sub2_qty), subtotal_style)
                        wsb.write(row_count, 12, "{:.2f}".format(sub2_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                        wsb.write(row_count, 18, "{:.2f}".format(sub2_lcqty), subtotal_style)
                        wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                        row_count+=1      

                    if old_sub1_name:
                        wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                        wsb.write_merge(row_count,row_count,1,10, 'Sub Total for ' + old_sub1_name, subtotal_title_style)        
                        wsb.write(row_count, 11, "{:.2f}".format(sub1_qty), subtotal_style)
                        wsb.write(row_count, 12, "{:.2f}".format(sub1_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                        wsb.write(row_count, 18, "{:.2f}".format(sub1_lcqty), subtotal_style)
                        wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                        row_count+=1      

                    if old_group_name:
                        wsb.write_merge(row_count,row_count,0,10, 'Total for ' + old_group_name, subtotal_style)        
                        wsb.write(row_count, 11, "{:.2f}".format(group_qty), subtotal_style)
                        wsb.write(row_count, 12, "{:.2f}".format(group_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,13,17, '', subtotal_style)  
                        wsb.write(row_count, 18, "{:.2f}".format(group_lcqty), subtotal_style)
                        wsb.write_merge(row_count,row_count,19,26, '', subtotal_style)  
                        row_count+=1      
                else:
                    wsb.col(0).width = width0/4
                    wsb.col(1).width = width0/4
                    wsb.col(2).width = width0/4
                    wsb.col(3).width = 5*width0/2
                    wsb.col(4).width = 2*width0
                    wsb.col(5).width = width0
                    wsb.col(6).width = 2*width0
                    wsb.col(7).width = width0
                    wsb.col(8).width = width0
                    wsb.col(9).width = width0
                    wsb.col(10).width = width0
                    wsb.col(11).width = width0
                    wsb.col(12).width = width0
                    wsb.col(13).width = width0
                    wsb.col(14).width = width0
                    wsb.col(15).width = 3*width0/2
                    wsb.col(16).width = 3*width0

                    row_count = 0
                    details = parser._get_view(data,sheet)
                    sub3_qty = 0.0
                    sub3_bal_qty = 0.0
                    sub2_qty = 0.0
                    sub2_bal_qty = 0.0
                    sub1_qty = 0.0
                    sub1_bal_qty = 0.0
                    group_qty = 0.0
                    group_bal_qty = 0.0
                    old_sub3_name = False
                    old_sub2_name = False
                    old_sub1_name = False
                    old_group_name = False

                    # Untuk Data Title
                    self.xls_write_row(wsb, None, data, parser,row_count, row_Company, tittle_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+1, row_Title, tittle_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+2, row_Type, subtittle_left_style)
                    self.xls_write_row(wsb, None, data, parser,row_count+3, row_Kosong, tittle_style)
                    
                    # Untuk Data Header
                    self.xls_write_row(wsb, None, data, parser,row_count+4, row_header, hdr_style)
                    
                    row_count+=5

                    for line in details:   
                        bal_qty = parser._uom_to_bales(line['bal_qty'] or 0.0,line['product_uom'] or '')
                        shipped_qty = parser._uom_to_bales(line['shipped_qty'] or 0.0,line['product_uom'] or '')
                        if bal_qty <= min_bale_bal_qty and shipped_qty>0.0:
                            continue
                        qty = parser._uom_to_bales(line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                        
                        sub3_name = line['blend_count_sd'] or ''
                        
                        sub3_name = line['sd_type'] or ''
                        sub2_name = line['blend_count'] or ''
                        sub1_name = line['blend'] or ''
                        group_name = line['loc_name'] or ''
                                                                                                
                        if (group_name != old_group_name) or (sub1_name != old_sub1_name) or (sub2_name != old_sub2_name) or (sub3_name != old_sub3_name):
                            if old_sub3_name:
                                wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                                wsb.write_merge(row_count,row_count,3,8, 'Sub Total for ' + old_sub3_name, subtotal_title_style)        
                                wsb.write(row_count, 9, "{:.2f}".format(sub3_qty), subtotal_style)
                                wsb.write(row_count, 10, "{:.2f}".format(sub3_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,16, '', normal_style)
                                #row_count+=1

                        if (group_name != old_group_name) or (sub1_name != old_sub1_name) or (sub2_name != old_sub2_name):
                            if old_sub2_name:
                                wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                                wsb.write_merge(row_count,row_count,2,8, 'Sub Total for ' + old_sub2_name, subtotal_title_style)        
                                wsb.write(row_count, 9, "{:.2f}".format(sub2_qty), subtotal_style)
                                wsb.write(row_count, 10, "{:.2f}".format(sub2_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,16, '', normal_style)
                                #row_count+=1

                        if (group_name != old_group_name) or (sub1_name != old_sub1_name):
                            if old_sub2_name:
                                wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                                wsb.write_merge(row_count,row_count,1,8, 'Sub Total for ' + old_sub1_name, subtotal_title_style)        
                                wsb.write(row_count, 9, "{:.2f}".format(sub1_qty), subtotal_style)
                                wsb.write(row_count, 10, "{:.2f}".format(sub1_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                                row_count+=1      
                                #wsb.write_merge(row_count,row_count,0,16, '', normal_style)
                                #row_count+=1

                        if (group_name != old_group_name):
                            if old_sub2_name:
                                wsb.write_merge(row_count,row_count,0,8, 'Total for ' + old_group_name, subtotal_title_style)        
                                wsb.write(row_count, 9, "{:.2f}".format(group_qty), subtotal_style)
                                wsb.write(row_count, 10, "{:.2f}".format(group_bal_qty), subtotal_style)
                                wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                                row_count+=1      
                                wsb.write_merge(row_count,row_count,0,16, '', normal_style)
                                row_count+=1

                            wsb.write_merge(row_count,row_count,0,16, 'Unit : ' + group_name, group_style)
                            row_count+=1
                            #wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                            #wsb.write_merge(row_count,row_count,1,16, sub1_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,16, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,16, sub3_name, group_style)
                            #row_count+=1
                            group_qty = 0.0
                            group_lcqty = 0.0
                            sub1_qty = 0.0
                            sub1_lcqty = 0.0
                            sub2_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub1_name != old_sub1_name:
                            #wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                            #wsb.write_merge(row_count,row_count,1,16, sub1_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,16, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,16, sub3_name, group_style)
                            #row_count+=1
                            sub1_qty = 0.0
                            sub1_lcqty = 0.0
                            sub2_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub2_name != old_sub2_name:
                            #wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                            #wsb.write_merge(row_count,row_count,2,16, sub2_name, group_style)
                            #row_count+=1
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,16, sub3_name, group_style)
                            #row_count+=1
                            sub2_qty = 0.0
                            sub2_lcqty = 0.0
                            sub3_qty = 0.0
                            sub3_lcqty = 0.0

                        if sub3_name != old_sub3_name:
                            #wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                            #wsb.write_merge(row_count,row_count,3,16, sub3_name, group_style)
                            #row_count+=1
                            sub3_qty = 0.0
                            sub3_lcqty = 0.0

                        old_group_name = group_name
                        old_sub1_name = sub1_name
                        old_sub2_name = sub2_name
                        old_sub3_name = sub3_name

                        sub3_qty += qty
                        sub3_bal_qty += bal_qty                        
                        sub2_qty += qty
                        sub2_bal_qty += bal_qty                        
                        sub1_qty += qty
                        sub1_bal_qty += bal_qty                        
                        group_qty += qty
                        group_bal_qty += bal_qty                        

                        wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                        wsb.write(row_count, 3, line['product_descr'] or '', normal_style)
                        wsb.write(row_count, 4, line['name'] or '', normal_style)
                        wsb.write(row_count, 5, parser._xdate(line['date_order']), normal_style)
                        wsb.write(row_count, 6, line['customer_name'] or '', normal_style)
                        wsb.write(row_count, 7, line['destination'] or '', normal_style)
                        wsb.write(row_count, 8, line['sale_order_lsp'], normal_style)
                        wsb.write(row_count, 9, "{:.2f}".format(qty), normal_right_style)
                        wsb.write(row_count, 10, "{:.2f}".format(bal_qty), normal_right_style)
                        if (line['cury_name'] or '') == 'USD':                            
                            wsb.write(row_count, 11, '', normal_right_style)
                        else:
                            wsb.write(row_count, 11, "{:.4f}".format(line['price_unit'] or 0.0), normal_right_style)
                        wsb.write(row_count, 12, "{:.4f}".format(parser._price_per_bales(line['price_unit_usd'] or 0.0,line['product_uom'] or '')), normal_right_style)
                        wsb.write(row_count, 13, "{:.2f}".format(line['commission_percentage'] or 0.0), normal_right_style2) 
                        wsb.write(row_count, 14, line['payment_term_name'] or '', normal_right_style)
                        wsb.write(row_count, 15, line['book_by'] or '', normal_style)
                        wsb.write(row_count, 16, line['other_description'] or '', normal_style)
                        row_count+=1
                    
                    if old_sub3_name:
                        wsb.write_merge(row_count,row_count,0,2, '', normal_style)
                        wsb.write_merge(row_count,row_count,3,8, 'Sub Total for ' + old_sub3_name, subtotal_title_style)        
                        wsb.write(row_count, 9, "{:.2f}".format(sub3_qty), subtotal_style)
                        wsb.write(row_count, 10, "{:.2f}".format(sub3_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                        row_count+=1      

                    if old_sub2_name:
                        wsb.write_merge(row_count,row_count,0,1, '', normal_style)
                        wsb.write_merge(row_count,row_count,2,8, 'Sub Total for ' + old_sub2_name, subtotal_title_style)        
                        wsb.write(row_count, 9, "{:.2f}".format(sub2_qty), subtotal_style)
                        wsb.write(row_count, 10, "{:.2f}".format(sub2_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                        row_count+=1      

                    if old_sub1_name:
                        wsb.write_merge(row_count,row_count,0,0, '', normal_style)
                        wsb.write_merge(row_count,row_count,1,8, 'Sub Total for ' + old_sub1_name, subtotal_title_style)        
                        wsb.write(row_count, 9, "{:.2f}".format(sub1_qty), subtotal_style)
                        wsb.write(row_count, 10, "{:.2f}".format(sub1_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                        row_count+=1      

                    if old_group_name:
                        wsb.write_merge(row_count,row_count,0,8, 'Total for ' + old_group_name, subtotal_style)        
                        wsb.write(row_count, 9, "{:.2f}".format(group_qty), subtotal_style)
                        wsb.write(row_count, 10, "{:.2f}".format(group_bal_qty), subtotal_style)
                        wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                        row_count+=1      
            elif sheet == 'contract':
                cols_specs = [
                        #title
                        ('Company',  21, 0, 'text', lambda x, d, p: company_name),
                        ('Title',  21, 0, 'text', lambda x, d, p: report_title),
                        ('Type',  21, 0, 'text', lambda x, d, p: sale_type),
                        ('Kosong', 21, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerProduct',  2, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerProductdescr',  1, 0, 'text', lambda x, d, p: 'Description'),
                        # ('headerBlendCount',  1, 0, 'text', lambda x, d, p: 'Blend-Count'),
                        ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                        ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                        ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Destination'),
                        ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                        ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                        ('headerUOMBaseName',  1, 0, 'text', lambda x, d, p: uom_base),
                        ('headerBalance',  1, 0, 'text', lambda x, d, p: 'Amt'),
                        ('headerLCQty',  1, 0, 'text', lambda x, d, p: 'LC Qty'),
                        ('headerPriceBase',  1, 0, 'text', lambda x, d, p: price_base),
                        ('headerIncoterm',  1, 0, 'text', lambda x, d, p: 'Delv Term'),
                        ('headerContainer',  1, 0, 'text', lambda x, d, p: 'CTR'),
                        ('headerComm',  1, 0, 'text', lambda x, d, p: '(%)'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay Term'),
                        ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Pay Recd Date'),
                        ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'Pay LSD'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title               = self.xls_row_template(cols_specs, ['Title'])
                row_Type                = self.xls_row_template(cols_specs, ['Type'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                row_header              = self.xls_row_template(cols_specs, ['headerProduct','headerProductdescr',
                                                                             'headerContractDate','headerCustomer','headerDestination',
                                                                             'headerLSD','headerLSDR','headerPackingType',
                                                                             'headerConeWidth','headerUOMBaseName','headerBalance','headerLCQty',
                                                                             'headerPriceBase','headerIncoterm','headerContainer','headerComm',
                                                                             'headerPayTerm','headerPayRecdDate','headerPayLSD',
                                                                             'headerRemarks'])

                wsc = wb.add_sheet(('Contract Wise'))

                wsc.panes_frozen = True
                wsc.remove_splits = True
                wsc.portrait = 0 # Landscape
                wsc.fit_width_to_pages = 1

                # set print header/footer
                wsc.header_str = ''
                wsc.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

                wsc.col(0).width = len("ABCDEFG")*128
                
                
                # Untuk Data Title
                self.xls_write_row(wsc, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsc, None, data, parser,1, row_Title, tittle_style)
                self.xls_write_row(wsc, None, data, parser,2, row_Type, subtittle_left_style)
                self.xls_write_row(wsc, None, data, parser,3, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsc, None, data, parser,4, row_header, hdr_style)
                
                row_count = 5
                details = parser._get_view(data,sheet)
                group_product_uom_qty = 0.0
                group_bal_qty = 0.0
                grand_product_uom_qty = 0.0
                grand_bal_qty = 0.0
                old_group_name = False

                for line in details:
                    base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    bale_shipped_qty = parser._uom_to_base(data,line['shipped_qty'] or 0.0,line['product_uom'] or '')
                    lc_qty = parser._uom_to_base(data,line['lc_qty'] or 0.0,line['product_uom'] or '')
                    if base_bal_qty <= min_bale_bal_qty and bale_shipped_qty>0.0:
                        continue

                    group_name = line['name'] or ''
                    if group_name != old_group_name:
                        if old_group_name:
                            wsc.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsc.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                            wsc.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                            wsc.write_merge(row_count,row_count,12,20, '', subtotal_style)   
                            row_count+=1     
                            wsc.write_merge(row_count,row_count,0,20, '', normal_style)
                            row_count+=1
                        wsc.write_merge(row_count,row_count,0,20, group_name, group_style)
                        row_count+=1
                        old_group_name = group_name
                        group_product_uom_qty = 0.0
                        group_bal_qty = 0.0
                    
                    # base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    # base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    # base_product_uom_qty = line['product_uom_qty'] or 0.0
                    # base_bal_qty = line['bal_qty'] or 0.0

                    group_product_uom_qty = group_product_uom_qty+base_product_uom_qty
                    group_bal_qty = group_bal_qty+base_bal_qty
                    grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty
                    grand_bal_qty = grand_bal_qty+base_bal_qty

                    wsc.write(row_count, 1, line['product_name'] or '', normal_style)
                    wsc.write(row_count,2,line['product_descr'] or '', normal_style)
                    # wsc.write(row_count, 2, (line['blend_count'] or '') , normal_style)
                    wsc.write(row_count, 3, parser._xdate(line['date_order']), normal_style)
                    wsc.write(row_count, 4, line['customer_name'] or '', normal_style)
                    wsc.write(row_count, 5, line['destination'] or '', normal_style)
                    wsc.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    wsc.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    wsc.write(row_count, 8, line['packing_name'] or '', normal_style)
                    wsc.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    wsc.write(row_count, 10, "{:.4f}".format(base_product_uom_qty), normal_right_style)
                    wsc.write(row_count, 11, "{:.4f}".format(base_bal_qty), normal_right_style)
                    wsc.write(row_count, 12, "{:.4f}".format(lc_qty), normal_right_style)
                    wsc.write(row_count, 13, "{:.4f}".format(parser._price_per_base(data,line['price_unit'] or 0.0,line['product_uom'] or '')), normal_right_style)
                    wsc.write(row_count, 14, line['incoterm'] or '', normal_style)
                    wsc.write(row_count, 15, line['container_size_name'] or '', normal_right_style)
                    wsc.write(row_count, 16, "{:.2f}".format(line['commission_percentage'] or 0.0), normal_right_style2) 
                    wsc.write(row_count, 17, line['payment_term_name'] or '', normal_right_style)
                    wsc.write(row_count, 18, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    wsc.write(row_count, 19, parser._xdate(line['lc_lsd']), normal_right_style)
                    wsc.write(row_count, 20, line['remarks'] or '', normal_style)
                    row_count+=1
                
                if old_group_name:
                    wsc.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsc.write(row_count, 10, "{:.4f}".format(group_product_uom_qty), subtotal_style)
                    wsc.write(row_count, 11, "{:.4f}".format(group_bal_qty), subtotal_style)
                    wsc.write_merge(row_count,row_count,12,20, '', subtotal_style)      
                    row_count+=1

                wsc.write_merge(row_count,row_count,0,9, 'Grand Total', total_title_style)        
                wsc.write(row_count, 10, "{:.4f}".format(grand_product_uom_qty), total_style)
                wsc.write(row_count, 11, "{:.4f}".format(grand_bal_qty), total_style)
                wsc.write_merge(row_count,row_count,12,20, '', total_style)        
            
        pass
# from netsvc import Service
# del Service._services['report.Sales Report']
pending_sales_report_xls('report.excel.pending.sales.report', 'report.pending.sales.wizard', 'addons/ad_sales_report/report/pending_sales_report.mako',
                       parser=pending_sales_parser, header=False)
report_sxw.report_sxw('report.pending.sales.report', 'report.pending.sales.wizard', 'addons/ad_sales_report/report/pending_sales_report.mako', parser=pending_sales_parser,header=False) 