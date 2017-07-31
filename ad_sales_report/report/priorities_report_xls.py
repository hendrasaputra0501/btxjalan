# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from ad_sales_report.report.priorities_report_parser import ReportPriorities

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
import datetime

class priorities_report_xls(report_xls):
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
        normal_style2                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold off; align: wrap on, vert top, horiz left;')
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

        details = parser._get_view(data)

        old_group_name = 'None'
        for line in details:   
            group_name = line['loc_name1'] or 'undefined'
            lsd_str=line['sale_order_lsd']
            print lsd_str,"ssssssssssssssssssssssssss"
            lsd=datetime.datetime.strptime(lsd_str,'%Y-%m-%d')
            print lsd,"zzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            date_5=datetime.timedelta(days=5)
            date5=lsd-date_5
            lsd_5=datetime.datetime.strftime(date5,'%d/%m/%Y')
            if group_name != old_group_name:
                old_group_name = group_name
                ## Style variable End
                report_title1 = parser._get_title(data,group_name)
                report_title2 = 'AS ON ' + parser._xdate(data['form']['as_on'])
                cols_specs = [
                        #title
                        ('Company', 19, 0, 'text', lambda x, d, p: company_name),
                        ('Title1',  19, 0, 'text', lambda x, d, p: report_title1),
                        ('Title2',  19, 0, 'text', lambda x, d, p: report_title2),
                        ('Kosong', 19, 0, 'text',lambda x, d, p: ' '),
                        ('Spasi', 1, 0, 'text',lambda x, d, p: ' '),
                              
                        #header
                        ('headerCount',  1, 0, 'text', lambda x, d, p: 'Count'),
                        ('headerProduct',  1, 0, 'text', lambda x, d, p: 'Product'),
                        ('headerBlend',  1, 0, 'text', lambda x, d, p: 'Blend'),
                        ('headerWaxed',  1, 0, 'text', lambda x, d, p: 'Waxed'),
                        ('headerSCNo',  1, 0, 'text', lambda x, d, p: 'SC No'),
                        ('headerSCDate',  1, 0, 'text', lambda x, d, p: 'SC Date'),
                        ('headerCustomer',  1, 0, 'text', lambda x, d, p: 'Customer'),
                        ('headerQty',  1, 0, 'text', lambda x, d, p: 'Bales'),
                        ('headerPackingType',  1, 0, 'text', lambda x, d, p: 'P/T'),
                        ('headerConeWidth',  1, 0, 'text', lambda x, d, p: 'Cn Wt'),
                        ('headerLSDSC',  1, 0, 'text', lambda x, d, p: 'LSD (SC)'),
                        ('headerLSDLC',  1, 0, 'text', lambda x, d, p: 'LSD LC'),
                        ('headerLSD5',  1, 0, 'text', lambda x, d, p: 'LSD-5 days'),
                        ('headerPayTerm',  1, 0, 'text', lambda x, d, p: 'TT/LC'),
                        ('headerPriority',  1, 0, 'text', lambda x, d, p: 'Priority'),
                        ('headerReadyBy',  1, 0, 'text', lambda x, d, p: 'Ready By'),
                        ('headerShipped',  1, 0, 'text', lambda x, d, p: 'Shipped'),
                        ('headerRemarks',  1, 0, 'text', lambda x, d, p: 'Remarks'),
                        ('headerCountry',  1, 0, 'text', lambda x, d, p: 'Country'),
                        ('headerPort',  1, 0, 'text', lambda x, d, p: 'Port'),
                ]

                ##Penempatan untuk template rows
                row_Company             = self.xls_row_template(cols_specs, ['Company'])
                row_Title1              = self.xls_row_template(cols_specs, ['Title1'])
                row_Title2              = self.xls_row_template(cols_specs, ['Title2'])
                row_Kosong              = self.xls_row_template(cols_specs, ['Kosong'])
                row_Spasi               = self.xls_row_template(cols_specs, ['Spasi'])
                #============================================================================
                row_header              = self.xls_row_template(cols_specs, ['headerCount','headerProduct','headerBlend',
                                                                             'headerWaxed','headerSCNo','headerSCDate',
                                                                             'headerCustomer','headerQty','headerPackingType',
                                                                             'headerConeWidth','headerLSDSC','headerLSDLC','headerLSD5',
                                                                             'headerPayTerm','headerPriority','headerReadyBy',
                                                                             'headerShipped','headerRemarks','headerCountry',
                                                                             'headerPort'])
                wsa = wb.add_sheet(group_name)    

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

                wsa.col(0).width = width02/2
                wsa.col(1).width = width02*2
                wsa.col(2).width = width02/2
                wsa.col(3).width = width02/2
                wsa.col(4).width = width02
                wsa.col(5).width = (width02*7)/10
                wsa.col(6).width = (width02*5)/2
                wsa.col(7).width = (width02*3)/5
                wsa.col(8).width = (width02*3)/10
                wsa.col(9).width = width02/2
                wsa.col(10).width = (width02*7)/10
                wsa.col(11).width = (width02*7)/10
                wsa.col(12).width = (width02*7)/10
                wsa.col(13).width = width02
                wsa.col(14).width = width02
                wsa.col(15).width = width02
                wsa.col(16).width = width02
                wsa.col(17).width = width02
                wsa.col(18).width = (width02*3)/5
                wsa.col(19).width = (width02*3)/5
                    
                # Untuk Data Title
                self.xls_write_row(wsa, None, data, parser,0, row_Company, tittle_style)
                self.xls_write_row(wsa, None, data, parser,1, row_Title1, tittle_style)
                self.xls_write_row(wsa, None, data, parser,2, row_Title2, tittle_style)
                self.xls_write_row(wsa, None, data, parser,3, row_Kosong, tittle_style)
                
                # Untuk Data Header
                self.xls_write_row(wsa, None, data, parser,4, row_header, hdr_style)
        
                row_count = 5           

            # base_uom_qty = parser._uom_to_bales(line['product_uom_qty'] or 0.0,line['product_uom'] or '')
            base_uom_qty = parser._uom_to_bales(line['bal_qty'] or 0.0,line['product_uom'] or '')
            bale_shipped_qty = parser._uom_to_bales(line['shipped_qty'] or 0.0,line['product_uom'] or False)
            if (base_uom_qty >= 5.0) or (bale_shipped_qty == 0.0):
                wsa.write(row_count, 0, line['count_descr'] or '', normal_style2)
                wsa.write(row_count, 1, line['product_descr'] or '', normal_style)
                wsa.write(row_count, 2, line['blend'] or '', normal_style)
                wsa.write(row_count, 3, line['wax'] or '', normal_style)
                wsa.write(row_count, 4, line['name'] or '', normal_style)
                wsa.write(row_count, 5, parser._xdate(line['date_order']), normal_style)
                wsa.write(row_count, 6, line['customer_name'] or '', normal_style)
                wsa.write(row_count, 7, round(base_uom_qty,2), normal_right_style2)
                wsa.write(row_count, 8, line['packing_name'] or '', normal_style)
                wsa.write(row_count, 9, "{:.2f}".format(line['cone_weight'] or 0.0), normal_right_style2)
                wsa.write(row_count, 10, parser._xdate(line['sale_order_lsd']), normal_style)
                wsa.write(row_count, 11, parser._xdate(line['lc_lsd']), normal_style)
                wsa.write(row_count, 12, parser._xdate(lsd_5), normal_style)
                wsa.write(row_count, 13, line['payment_term_name'] or '', normal_style)
                wsa.write(row_count, 14, '', normal_style)
                wsa.write(row_count, 15, '', normal_style)
                wsa.write(row_count, 16, '', normal_style)
                wsa.write(row_count, 17, line['internal_remarks'] or '', normal_style)
                wsa.write(row_count, 18, line['country'] or '', normal_style)
                wsa.write(row_count, 19, line['port'] or '', normal_style)
                row_count+=1
            else:
                continue
        pass

priorities_report_xls('report.priorities.report',
                 'report.priorities.wizard', 'addons/ad_sales_report/report/priorities_report.mako',
                 parser=ReportPriorities)