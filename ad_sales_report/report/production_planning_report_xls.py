# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from ad_sales_report.report.production_planning_report_parser import production_planning_parser

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class production_planning_report_xls(report_xls):
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
            report_title = parser._get_title(sheet) + ' As On : ' + parser._xdate(data['form']['as_on'])
            if sheet == 'customer':
                cols_specs = [
                        #title
                        ('Company',  17, 0, 'text', lambda x, d, p: company_name),
                        ('Title',  17, 0, 'text', lambda x, d, p: report_title),
                        ('Kosong', 17, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerProduct',  2, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerBlendCount',  1, 0, 'text', lambda x, d, p: 'Blend-Count'),
                        ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                        ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                        ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Destination'),
                        ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                        ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                        ('headerUOMBaseName',  1, 0, 'text', lambda x, d, p: uom_base),
                        ('headerIncoterm',  1, 0, 'text', lambda x, d, p: 'Incoterm'),
                        ('headerContainer',  1, 0, 'text', lambda x, d, p: 'Container'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay Term'),
                        ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Pay Recd Date'),
                        ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'Pay LSD'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title              = self.xls_row_template(cols_specs, ['Title'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                #============================================================================
                row_header              = self.xls_row_template(cols_specs, ['headerProduct','headerBlendCount','headerContractNo',
                                                                             'headerContractDate','headerDestination',
                                                                             'headerLSD','headerLSDR','headerPackingType',
                                                                             'headerConeWidth','headerUOMBaseName',
                                                                             'headerIncoterm','headerContainer',
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
                wsa.col(2).width = wsa.col(1).width
                wsa.col(3).width = wsa.col(1).width
                wsa.col(4).width = wsa.col(1).width
                wsa.col(5).width = wsa.col(1).width
                wsa.col(6).width = wsa.col(1).width
                wsa.col(7).width = wsa.col(1).width
                wsa.col(8).width = wsa.col(1).width
                wsa.col(9).width = wsa.col(1).width
                wsa.col(10).width = wsa.col(1).width
                wsa.col(11).width = wsa.col(1).width
                wsa.col(12).width = wsa.col(1).width
                wsa.col(13).width = wsa.col(1).width
                wsa.col(14).width = wsa.col(1).width
                wsa.col(15).width = wsa.col(1).width
                wsa.col(16).width = wsa.col(1).width
                
                # Untuk Data Title
                self.xls_write_row(wsa, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsa, None, data, parser,1, row_Title, tittle_style)
                self.xls_write_row(wsa, None, data, parser,2, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsa, None, data, parser,3, row_header, hdr_style)
                
                row_count = 4
                details = parser._get_view(data,sheet)
                group_product_uom_qty = 0.0
                group_bal_qty = 0.0
                grand_product_uom_qty = 0.0
                grand_bal_qty = 0.0
                old_group_name = False

                for line in details:   
                    group_name = line['customer_name'] or ''
                    if group_name != old_group_name:
                        if old_group_name:
                            wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsa.write(row_count, 10, group_product_uom_qty, subtotal_style)
                            wsa.write_merge(row_count,row_count,11,16, '', subtotal_style)    
                            row_count+=1    
                            wsa.write_merge(row_count,row_count,0,16, '', normal_style)
                            row_count+=1
                        wsa.write_merge(row_count,row_count,0,16, group_name, group_style)
                        row_count+=1
                        old_group_name = group_name
                        group_product_uom_qty = 0.0
                        group_bal_qty = 0.0
                    
                    base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    group_product_uom_qty = group_product_uom_qty+base_product_uom_qty
                    group_bal_qty = group_bal_qty+base_bal_qty
                    grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty
                    grand_bal_qty = grand_bal_qty+base_bal_qty

                    wsa.write(row_count, 1, line['product_name'] or '', normal_style)
                    wsa.write(row_count, 2, (line['blend_count'] or '') , normal_style)
                    wsa.write(row_count, 3, line['name'] or '', normal_style)
                    wsa.write(row_count, 4, parser._xdate(line['date_order']), normal_style)
                    wsa.write(row_count, 5, line['destination'] or '', normal_style)
                    wsa.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    wsa.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    wsa.write(row_count, 8, line['packing_name'] or '', normal_style)
                    wsa.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    wsa.write(row_count, 10, base_product_uom_qty, normal_right_style)
                    wsa.write(row_count, 11, line['incoterm'] or '', normal_style)
                    wsa.write(row_count, 12, line['container_size_name'] or '', normal_right_style)
                    wsa.write(row_count, 13, line['payment_term_name'] or '', normal_right_style)
                    wsa.write(row_count, 14, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    wsa.write(row_count, 15, parser._xdate(line['lc_lsd']), normal_right_style)
                    wsa.write(row_count, 16, line['remarks'] or '', normal_style)
                    row_count+=1
                
                if old_group_name:
                    wsa.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsa.write(row_count, 10, group_product_uom_qty, subtotal_style)
                    wsa.write_merge(row_count,row_count,11,16, '', subtotal_style)       
                    row_count+=1 
                
                wsa.write_merge(row_count,row_count,0,9, 'GRAND TOTAL', total_title_style)        
                wsa.write(row_count, 10, grand_product_uom_qty, total_style)
                wsa.write_merge(row_count,row_count,11,16, '', total_style)        
            elif sheet == 'product':
                cols_specs = [
                        #title
                        ('Company',  17, 0, 'text', lambda x, d, p: company_name),
                        ('Title',  17, 0, 'text', lambda x, d, p: report_title),
                        ('Kosong', 17, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerProduct',  2, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerContractNo',  1, 0, 'text', lambda x, d, p: 'Contract No'),
                        ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                        ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                        ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Destination'),
                        ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                        ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                        ('headerUOMBaseName',  1, 0, 'text', lambda x, d, p: uom_base),
                        ('headerIncoterm',  1, 0, 'text', lambda x, d, p: 'Incoterm'),
                        ('headerContainer',  1, 0, 'text', lambda x, d, p: 'Container'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay Term'),
                        ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Pay Recd Date'),
                        ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'Pay LSD'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title              = self.xls_row_template(cols_specs, ['Title'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                #============================================================================
                row_header              = self.xls_row_template(cols_specs, ['headerProduct','headerContractNo',
                                                                             'headerContractDate','headerCustomer','headerDestination',
                                                                             'headerLSD','headerLSDR','headerPackingType',
                                                                             'headerConeWidth','headerUOMBaseName',
                                                                             'headerIncoterm','headerContainer',
                                                                             'headerPayTerm','headerPayRecdDate','headerPayLSD',
                                                                             'headerRemarks'])

                wsb = wb.add_sheet(('Blend Count Wise'))

                wsb.panes_frozen = True
                wsb.remove_splits = True
                wsb.portrait = 0 # Landscape
                wsb.fit_width_to_pages = 1

                # set print header/footer
                wsb.header_str = ''
                wsb.footer_str = '&L&10&I&"Times New Roman"' + parser._get_print_user_time() + '&R&10&I&"Times New Roman"Page &P of &N'

                wsb.col(0).width = len("ABCDEFG")*128
                wsb.col(1).width = len("ABCDEFG")*512
                wsb.col(2).width = wsb.col(1).width
                wsb.col(3).width = wsb.col(1).width
                wsb.col(4).width = wsb.col(1).width
                wsb.col(5).width = wsb.col(1).width
                wsb.col(6).width = wsb.col(1).width
                wsb.col(7).width = wsb.col(1).width
                wsb.col(8).width = wsb.col(1).width
                wsb.col(9).width = wsb.col(1).width
                wsb.col(10).width = wsb.col(1).width
                wsb.col(11).width = wsb.col(1).width
                wsb.col(12).width = wsb.col(1).width
                wsb.col(13).width = wsb.col(1).width
                wsb.col(14).width = wsb.col(1).width
                wsb.col(15).width = wsb.col(1).width
                wsb.col(16).width = wsb.col(1).width
                
                # Untuk Data Title
                self.xls_write_row(wsb, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsb, None, data, parser,1, row_Title, tittle_style)
                self.xls_write_row(wsb, None, data, parser,2, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsb, None, data, parser,3, row_header, hdr_style)
                
                row_count = 4
                details = parser._get_view(data,sheet)
                group_product_uom_qty = 0.0
                group_bal_qty = 0.0
                grand_product_uom_qty = 0.0
                grand_bal_qty = 0.0
                old_group_name = False

                for line in details:   
                    group_name = line['blend_count'] or ''
                    if group_name != old_group_name:
                        if old_group_name:
                            wsb.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsb.write(row_count, 10, group_product_uom_qty, subtotal_style)
                            wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                            row_count+=1      
                            wsb.write_merge(row_count,row_count,0,16, '', normal_style)
                            row_count+=1
                        wsb.write_merge(row_count,row_count,0,16, group_name, group_style)
                        row_count+=1
                        old_group_name = group_name
                        group_product_uom_qty = 0.0
                        group_bal_qty = 0.0
                    
                    base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    group_product_uom_qty = group_product_uom_qty+base_product_uom_qty
                    group_bal_qty = group_bal_qty+base_bal_qty
                    grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty
                    grand_bal_qty = grand_bal_qty+base_bal_qty

                    wsb.write(row_count, 1, line['product_name'] or '', normal_style)
                    wsb.write(row_count, 2, line['name'] or '', normal_style)
                    wsb.write(row_count, 3, parser._xdate(line['date_order']), normal_style)
                    wsb.write(row_count, 4, line['customer_name'] or '', normal_style)
                    wsb.write(row_count, 5, line['destination'] or '', normal_style)
                    wsb.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    wsb.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    wsb.write(row_count, 8, line['packing_name'] or '', normal_style)
                    wsb.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    wsb.write(row_count, 10, base_product_uom_qty, normal_right_style)
                    wsb.write(row_count, 11, line['incoterm'] or '', normal_style)
                    wsb.write(row_count, 12, line['container_size_name'] or '', normal_right_style)
                    wsb.write(row_count, 13, line['payment_term_name'] or '', normal_right_style)
                    wsb.write(row_count, 14, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    wsb.write(row_count, 15, parser._xdate(line['lc_lsd']), normal_right_style)
                    wsb.write(row_count, 16, line['remarks'] or '', normal_style)
                    row_count+=1
                
                if old_group_name:
                    wsb.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsb.write(row_count, 10, group_product_uom_qty, subtotal_style)
                    wsb.write_merge(row_count,row_count,11,16, '', subtotal_style)  
                    row_count+=1      

                wsb.write_merge(row_count,row_count,0,9, 'GRAND TOTAL', total_title_style)        
                wsb.write(row_count, 10, grand_product_uom_qty, total_style)
                wsb.write_merge(row_count,row_count,11,16, '', total_style)        
            elif sheet == 'contract':
                cols_specs = [
                        #title
                        ('Company',  17, 0, 'text', lambda x, d, p: company_name),
                        ('Title',  17, 0, 'text', lambda x, d, p: report_title),
                        ('Kosong', 17, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerProduct',  2, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerBlendCount',  1, 0, 'text', lambda x, d, p: 'Blend-Count'),
                        ('headerContractDate',  1, 0, 'text', lambda x, d, p: 'Contract Date'),
                        ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                        ('headerDestination',  1, 0, 'text', lambda x, d, p: 'Destination'),
                        ('headerLSD',  1, 0, 'text', lambda x, d, p: 'LSD'),
                        ('headerLSDR',  1, 0, 'text', lambda x, d, p: 'LSD (R)'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'C/W'),
                        ('headerUOMBaseName',  1, 0, 'text', lambda x, d, p: uom_base),
                        ('headerIncoterm',  1, 0, 'text', lambda x, d, p: 'Incoterm'),
                        ('headerContainer',  1, 0, 'text', lambda x, d, p: 'Container'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'Pay Term'),
                        ('headerPayRecdDate',  1, 0, 'text', lambda x, d, p: 'Pay Recd Date'),
                        ('headerPayLSD',  1, 0, 'text', lambda x, d, p: 'Pay LSD'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title              = self.xls_row_template(cols_specs, ['Title'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                #============================================================================
                row_header              = self.xls_row_template(cols_specs, ['headerProduct','headerBlendCount',
                                                                             'headerContractDate','headerCustomer','headerDestination',
                                                                             'headerLSD','headerLSDR','headerPackingType',
                                                                             'headerConeWidth','headerUOMBaseName',
                                                                             'headerIncoterm','headerContainer',
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
                wsc.col(1).width = len("ABCDEFG")*512
                wsc.col(2).width = wsc.col(1).width
                wsc.col(3).width = wsc.col(1).width
                wsc.col(4).width = wsc.col(1).width
                wsc.col(5).width = wsc.col(1).width
                wsc.col(6).width = wsc.col(1).width
                wsc.col(7).width = wsc.col(1).width
                wsc.col(8).width = wsc.col(1).width
                wsc.col(9).width = wsc.col(1).width
                wsc.col(10).width = wsc.col(1).width
                wsc.col(11).width = wsc.col(1).width
                wsc.col(12).width = wsc.col(1).width
                wsc.col(13).width = wsc.col(1).width
                wsc.col(14).width = wsc.col(1).width
                wsc.col(15).width = wsc.col(1).width
                wsc.col(16).width = wsc.col(1).width
                
                # Untuk Data Title
                self.xls_write_row(wsc, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsc, None, data, parser,1, row_Title, tittle_style)
                self.xls_write_row(wsc, None, data, parser,2, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsc, None, data, parser,3, row_header, hdr_style)
                
                row_count = 4
                details = parser._get_view(data,sheet)
                group_product_uom_qty = 0.0
                group_bal_qty = 0.0
                grand_product_uom_qty = 0.0
                grand_bal_qty = 0.0
                old_group_name = False

                for line in details:   
                    group_name = line['name'] or ''
                    if group_name != old_group_name:
                        if old_group_name:
                            wsc.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                            wsc.write(row_count, 10, group_product_uom_qty, subtotal_style)
                            wsc.write_merge(row_count,row_count,11,16, '', subtotal_style)   
                            row_count+=1     
                            wsc.write_merge(row_count,row_count,0,16, '', normal_style)
                            row_count+=1
                        wsc.write_merge(row_count,row_count,0,16, group_name, group_style)
                        row_count+=1
                        old_group_name = group_name
                        group_product_uom_qty = 0.0
                        group_bal_qty = 0.0
                    
                    base_product_uom_qty = parser._uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'] or '')
                    base_bal_qty = parser._uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'] or '')
                    group_product_uom_qty = group_product_uom_qty+base_product_uom_qty
                    group_bal_qty = group_bal_qty+base_bal_qty
                    grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty
                    grand_bal_qty = grand_bal_qty+base_bal_qty

                    wsc.write(row_count, 1, line['product_name'] or '', normal_style)
                    wsc.write(row_count, 2, (line['blend_count'] or '') , normal_style)
                    wsc.write(row_count, 3, parser._xdate(line['date_order']), normal_style)
                    wsc.write(row_count, 4, line['customer_name'] or '', normal_style)
                    wsc.write(row_count, 5, line['destination'] or '', normal_style)
                    wsc.write(row_count, 6, parser._xdate(line['sale_order_lsd']), normal_style)
                    wsc.write(row_count, 7, parser._xdate(line['sale_order_scd']), normal_style)
                    wsc.write(row_count, 8, line['packing_name'] or '', normal_style)
                    wsc.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                    wsc.write(row_count, 10, base_product_uom_qty, normal_right_style)
                    wsc.write(row_count, 11, line['incoterm'] or '', normal_style)
                    wsc.write(row_count, 12, line['container_size_name'] or '', normal_right_style)
                    wsc.write(row_count, 13, line['payment_term_name'] or '', normal_right_style)
                    wsc.write(row_count, 14, parser._xdate(line['lc_recvd_date']), normal_right_style)
                    wsc.write(row_count, 15, parser._xdate(line['lc_lsd']), normal_right_style)
                    wsc.write(row_count, 16, line['remarks'] or '', normal_style)
                    row_count+=1
                
                if old_group_name:
                    wsc.write_merge(row_count,row_count,0,9, 'Total for ' + old_group_name, subtotal_title_style)        
                    wsc.write(row_count, 10, group_product_uom_qty, subtotal_style)
                    wsc.write_merge(row_count,row_count,11,16, '', subtotal_style)      
                    row_count+=1  

                wsc.write_merge(row_count,row_count,0,9, 'Grand Total', total_title_style)        
                wsc.write(row_count, 10, grand_product_uom_qty, total_style)
                wsc.write_merge(row_count,row_count,11,16, '', total_style)        
            
        pass
# from netsvc import Service
# del Service._services['report.Sales Report']
#production_planning_report_xls('report.production.planning.report', 'report.production.planning.wizard', 'addons/ad_sales_report/report/production_planning_report.mako',
#                        parser=production_planning_parser, header=False)