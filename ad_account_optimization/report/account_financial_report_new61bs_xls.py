# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import xlwt
from report_engine_xls import report_xls
from ad_account_optimization.generic.account_financial_report import report_account_common
import cStringIO
from tools.translate import _

class account_financial_xls(report_xls):
    
    def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
        #print("START: "+time.strftime("%Y-%m-%d %H:%M:%S"))
 
        if not context:
            context = {}
        context = context.copy()
        rml_parser = self.parser(cr, uid, self.name2, context=context)
        objs = self.getObjects(cr, uid, ids, context=context)
        rml_parser.set_context(objs, data, ids, 'xls')
 
        n = cStringIO.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')
        self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
        wb.save(n)
        n.seek(0)
 
        #print("END: "+time.strftime("%Y-%m-%d %H:%M:%S"))
 
        return (n.read(), 'xls')
    
#    def _get_title(self, parser, data):
#        title_mode = parser._get_title(data)
#        print title_mode
#        return title_mode
        
    def _display_filter(self, parser, data):
        filter_mode = parser._get_filter(data)
        filter_string = filter_mode
        if filter_mode == 'Date':
            filter_string = '%s -> %s' % (parser.formatLang(parser._get_start_date(data), date=True),parser.formatLang(parser._get_end_date(data), date=True))
        elif filter_mode == 'Periods':
            filter_string = '%s -> %s' % (parser.get_start_period(data), parser.get_end_period(data))

        #moves_string = '13'#parser._get_target_move(data)
        display_acct_string = ''
#        if data['form']['display_account'] == 'bal_all':
#            display_acct_string = 'All'
#        elif data['form']['display_account'] == 'bal_movement':
#            display_acct_string = 'With movements'
#        else:
#            display_acct_string = 'With balance is not equal to 0'

        return 'Display Account: %s, Filter By: %s' % (display_acct_string, filter_string)

    def _display_fiscalyear(self, parser, data):
        k = parser._get_fiscalyear(data)
        if k:
            k = 'Fiscal Year: %s' % (k)
        return k
    
#    def _sum_currency_amount(self, parser, cur):
#        k = parser._sum_currency_amount_account(cur)
#        if k:
#            k = k
#        return k
    
    def generate_xls_report(self, parser, data, obj, wb):
        print data['form']
        #print "====",parser._get_account(data)
        c = parser.localcontext['company']
        ws = wb.add_sheet(('General Ledger')[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        judul = data['form']['account_report_id'][1]
        if data['form']['enable_filter']:
            cols_specs = [
                # Headers data
                ('Title', 13, 0, 'text',
                    lambda x, d, p: judul),
                ('Kosong', 13, 0, 'text',
                    lambda x, d, p: ""),
                ('Fiscal Year', 6, 0, 'text',
                    lambda x, d, p: self._display_fiscalyear(p, d)),
                ('Chart of Accounts', 3, 0, 'text',
                    lambda x, d, p: parser._get_account(data)),
                ('Create Date', 4, 0, 'text',
                    lambda x, d, p: p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
                ('Filter', 13, 0, 'text',
                    lambda x, d, p: self._display_filter(p, d)),
    
               # Account Total
                ('Account', 9, 0, 'text',
                    lambda x, d, p: '  '*x['level'] + x['name']),
                ('Balance', 2, 80, 'number',
                    lambda x, d, p: x['balance']),
                ('Balance Compare', 2, 80, 'number',
                    lambda x, d, p: x['balance_cmp']),
            ]
        elif data['form']['debit_credit']:
            cols_specs = [
                # Headers data
            ('Title', 15, 0, 'text',
                lambda x, d, p: judul),
            ('Kosong', 15, 0, 'text',
                lambda x, d, p: ""),
            ('Fiscal Year', 7, 0, 'text',
                lambda x, d, p: self._display_fiscalyear(p, d)),
            ('Chart of Accounts', 4, 0, 'text',
                lambda x, d, p: parser._get_account(data)),
            ('Create Date', 4, 0, 'text',
                lambda x, d, p: p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
            ('Filter', 15, 0, 'text',
                lambda x, d, p: self._display_filter(p, d)),
    
               # Account Total
                ('Account', 9, 0, 'text',
                    lambda x, d, p: '  '*x['level'] + x['name']),
                ('Debit', 2, 80, 'number',
                    lambda x, d, p: x['debit']),
                ('Credit', 2, 80, 'number',
                    lambda x, d, p: x['credit']),
                ('Balance', 2, 80, 'number',
                    lambda x, d, p: x['balance']),
            ]
        else:  
            cols_specs = [
                # Headers data
                ('Title', 11, 0, 'text',
                    lambda x, d, p: judul),
                ('Kosong', 11, 0, 'text',
                    lambda x, d, p: ""),
                ('Fiscal Year', 6, 0, 'text',
                    lambda x, d, p: self._display_fiscalyear(p, d)),
                ('Chart of Accounts', 3, 0, 'text',
                    lambda x, d, p: parser._get_account(data)),
                ('Create Date', 2, 0, 'text',
                    lambda x, d, p: p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
                ('Filter', 11, 0, 'text',
                    lambda x, d, p: self._display_filter(p, d)),
    
               # Account Total
                ('Account', 9, 0, 'text',
                    lambda x, d, p: '  '*x['level'] + x['name']),
                ('Balance', 2, 80, 'number',
                    lambda x, d, p: x['balance']),
            ]
        
        row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
        row_hdr1 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr2 = self.xls_row_template(cols_specs, ['Fiscal Year', 'Chart of Accounts', 'Create Date'])
        row_hdr3 = self.xls_row_template(cols_specs, ['Filter'])
        row_hdr4 = self.xls_row_template(cols_specs, ['Kosong'])
        #hdr_line = ['Account Name', 'Account Balance']
        if data['form']['enable_filter']:
            hdr_account_total = ['Account', 'Balance', 'Balance Compare']
        elif data['form']['debit_credit']:
            hdr_account_total = ['Account', 'Debit', 'Credit', 'Balance']
        else:
            hdr_account_total = ['Account', 'Balance']
        #row_line = self.xls_row_template(cols_specs, hdr_line)
        row_account_total = self.xls_row_template(cols_specs, hdr_account_total)

        # Style
        tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        row_hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
        row_account_style = xlwt.easyxf('font: bold on;borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        row_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        
        hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
        row_normal_style=  xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        row_bold_style = xlwt.easyxf('font: bold on;',num_format_str='#,##0.00;(#,##0.00)')
        
        tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_left_style = xlwt.easyxf('font: height 180, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_right_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_top_and_bottom_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        blank_style = xlwt.easyxf('font: height 650, name Arial, colour_index brown, bold off; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        normal_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off; align: wrap on, vert centre, horiz left;')
        total_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre;', num_format_str='#,##0.00;(#,##0.00)')
        
        self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style)
        self.xls_write_row(ws, None, data, parser, 1, row_hdr1, blank_style)
        self.xls_write_row(ws, None, data, parser, 2, row_hdr2, subtittle_left_style)
        self.xls_write_row(ws, None, data, parser, 3, row_hdr3, hdr_style)
        self.xls_write_row(ws, None, data, parser, 4, row_hdr4, blank_style)
        #self.xls_write_row_header(ws, 5, row_account_total, row_hdr_style)
        self.xls_write_row_header(ws, 5, row_account_total, row_hdr_style, set_column_size=True)

        row_count = 6
        ws.horz_split_pos = row_count
        for a in parser.objects:
            for o in parser.get_lines(data):
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", o
                if o['account_type'] == 'view' or o['account_type'] is False:
                    style = row_bold_style
                else:
                    style = row_normal_style
                r = ws.row(row_count)
                
                if o['account_type'] == 'view' or o['level'] == 3:
                    #####REVENUE#####
                    #if 
                    self.xls_write_row(ws, o, data, parser, row_count, row_account_total, style)
                    row_count += 1
        pass

account_financial_xls(
        'report.account.financial.report.new61bs.xls',
        'account.account',
        'addons/ad_account_optimization/report/account_financial_report.rml',
        parser=report_account_common,
        header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
