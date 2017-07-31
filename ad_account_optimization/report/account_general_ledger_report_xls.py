# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from report_engine_xls import report_xls
#from account.report.account_general_ledger import general_ledger
from account.report.account_general_ledger import general_ledger
import cStringIO

class account_balance_report_xls(report_xls):
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
    
    def _display_filter(self, parser, data):
        filter_mode = parser._get_filter(data)
        filter_string = filter_mode
        if filter_mode == 'Date':
            filter_string = '%s -> %s' % (parser.formatLang(parser._get_start_date(data), date=True),
                                          parser.formatLang(parser._get_end_date(data), date=True))
        elif filter_mode == 'Periods':
            filter_string = '%s -> %s' % (parser.get_start_period(data),
                                 parser.get_end_period(data))

        moves_string = parser._get_target_move(data)
        display_acct_string = ''
        if data['form']['display_account'] == 'bal_all':
            display_acct_string = 'All'
        elif data['form']['display_account'] == 'bal_movement':
            display_acct_string = 'With movements'
        else:
            display_acct_string = 'With balance is not equal to 0'

        return 'Display Account: %s, Filter By: %s, Target Moves: %s' % (display_acct_string, filter_string, moves_string)

    def _display_fiscalyear(self, parser, data):
        k = parser._get_fiscalyear(data)
        if k:
            k = 'Fiscal Year: %s' % (k)
        return k
    
    def _sum_currency_amount(self, parser, cur):
        k = parser._sum_currency_amount_account(cur)
        if k:
            k = k
        return k
    
    def generate_xls_report(self, parser, data, obj, wb):
        #print data['form']
        print "test",parser
        
        c = parser.localcontext['company']
        ws = wb.add_sheet(('General Ledger')[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        judul = "GENERAL LEDGER"

        cols_specs = [
            # Headers data
            ('Title', 15, 0, 'text',
                lambda x, d, p: judul),
            ('Kosong', 15, 0, 'text',
                lambda x, d, p: ""),
            ('Fiscal Year', 13, 0, 'text',
                lambda x, d, p: self._display_fiscalyear(p, d)),
            ('Create Date', 2, 0, 'text',
                lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
            ('Filter', 15, 0, 'text',
                lambda x, d, p: self._display_filter(p, d)),

            # Line
            ('Date', 1, 65, 'text',
                lambda x, d, p: p.formatLang(x['ldate'],date=True)),
            ('Period', 1, 65, 'text',
                lambda x, d, p: x['period_code']),
            ('JNRL', 1, 28, 'text',
                lambda x, d, p: x['lcode']),
            ('Partner Name', 4, 0, 'text',
                lambda x, d, p: x['partner_name']),
            ('Ref.', 1, 60, 'text',
                lambda x, d, p: x['lref']),
            ('Move', 1, 60, 'text',
                lambda x, d, p: x['move']),
            ('Entry Label', 1, 175, 'text',
                lambda x, d, p: x['lname']),
            ('Debit', 1, 90, 'number',
                lambda x, d, p: x['debit']),
            ('Credit', 1, 90, 'number',
                lambda x, d, p: x['credit']),
            ('Balance', 1, 90, 'number',
                lambda x, d, p: x['progress']),
            ('Amount Currency', 1, 90, 'number',
                lambda x, d, p: x['amount_currency']),
            ('Currency', 1, 90, 'text',
                lambda x, d, p: x['currency_code']),
                      
           # Account Total
            ('Account Code', 1, 0, 'text',
                lambda x, d, p: x.code),
            ('Account Name', 9, 0, 'text',
                lambda x, d, p: x.name),
            ('Account Debit', 1, 0, 'number',
                lambda x, d, p: p._sum_debit_account(x)),
            ('Account Credit', 1, 0, 'number',
                lambda x, d, p: p._sum_credit_account(x)),
            ('Account Balance', 1, 0, 'number',
                lambda x, d, p: p._sum_balance_account(x)),
        ]
        
        row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
        row_hdr1 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr2 = self.xls_row_template(cols_specs, ['Fiscal Year', 'Create Date'])
        row_hdr3 = self.xls_row_template(cols_specs, ['Filter'])
        row_hdr4 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr5 = self.xls_row_template(cols_specs, ['Kosong'])
        hdr_line = ['Date', 'Period', 'JNRL', 'Partner Name', 'Ref.', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Amount Currency', 'Currency']
        hdr_account_total = ['Account Code', 'Account Name', 'Account Debit', 'Account Credit', 'Account Balance']

        row_line = self.xls_row_template(cols_specs, hdr_line)
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
        self.xls_write_row_header(ws, 5, row_account_total, row_hdr_style)
        self.xls_write_row_header(ws, 6, row_line, row_hdr_style, set_column_size=True)

        row_count = 7
        ws.horz_split_pos = row_count

        for a in parser.objects:
            for o in parser.get_children_accounts(a):
                r = ws.row(row_count)
                print "teeeest", r
                self.xls_write_row(ws, o, data, parser,
                                row_count, row_account_total, row_account_style)
                row_count += 1

                for l in parser.lines(o):
                    self.xls_write_row(ws, l, data, parser,
                                    row_count, row_line, row_style)
                    row_count += 1
                    print "print l",l
        pass

account_balance_report_xls(
        'report.account.general.ledger_landscape.xls',
        'account.account',
        'addons/account/report/account_general_ledger_landscape.rml',
        parser=general_ledger,
        header=False)

