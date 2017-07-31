# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from report_engine_xls import report_xls
#from account_v6_reports_backport.report.account_partner_balance import partner_balance
from account_partner_balance import partner_balance_i

class account_balance_report_xls(report_xls):
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
        display_partner_string = parser._get_partners()

        return 'Display Partner: %s, Filter By: %s, Target Moves: %s' % (display_partner_string, filter_string, moves_string)

    def _display_fiscalyear(self, parser, data):
        k = parser._get_fiscalyear(data)
        if k:
            k = 'Fiscal Year: %s' % (k)
        return k

    def _display_journals(self, parser, data):
        return u'Journals: %s' % (', '.join([ lt or '' for lt in parser._get_journal(data) ]))

    def generate_xls_report(self, parser, data, obj, wb):
        c = parser.localcontext['company']
        ws = wb.add_sheet(('Account Balance - %s - %s' % (c.partner_id.ref, c.currency_id.name))[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        judul = "PARTNER BALANCE"	

        cols_specs = [
                # Headers data
                ('Title', 6, 0, 'text',
                    lambda x, d, p: judul),
                ('Kosong', 6, 0, 'text',
                    lambda x, d, p: ""),
                ('Fiscal Year', 4, 0, 'text',
                    lambda x, d, p: self._display_fiscalyear(p, d)),
                ('Create Date', 2, 0, 'text',
                    lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
                ('Filter', 6, 0, 'text',
                    lambda x, d, p: self._display_filter(p, d)),
                ('Journals', 6, 0, 'text',
                    lambda x, d, p: self._display_journals(p, d)),
                # Balance column
                ('Code', 1, 67, 'text',
                    lambda x, d, p: ('%s %s' % (x['ref'] or '', x['type'] == 3 and x['code'] or ''))),
                ('(Account/Partner) Name', 1, 270, 'text',
                    lambda x, d, p: x['name']),
                ('Debit', 1, 70, 'number',
                    lambda x, d, p: x['debit']),
                ('Credit', 1, 70, 'number',
                    lambda x, d, p: x['credit']),
                ('Balance', 1, 80, 'number',
                    lambda x, d, p: x['balance']),
                ('In Dispute', 1, 70, 'number',
                    lambda x, d, p: x['enlitige']),
        ]
	
        row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
        row_hdr5 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr1 = self.xls_row_template(cols_specs, ['Fiscal Year', 'Create Date'])
        row_hdr2 = self.xls_row_template(cols_specs, ['Filter'])
        row_hdr3 = self.xls_row_template(cols_specs, ['Journals'])
        row_hdr6 = self.xls_row_template(cols_specs, ['Kosong'])
        row_balance = self.xls_row_template(cols_specs,
                ['Code','(Account/Partner) Name','Debit','Credit','Balance', 'In Dispute'])
	
        tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_left_style = xlwt.easyxf('font: height 180, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
        row_normal_style=  xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        row_bold_style = xlwt.easyxf('font: bold on;',num_format_str='#,##0.00;(#,##0.00)')

        # Write headers
        self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style)
        self.xls_write_row(ws, None, data, parser, 1, row_hdr5, hdr_style)
        self.xls_write_row(ws, None, data, parser, 2, row_hdr1, subtittle_left_style)
        self.xls_write_row(ws, None, data, parser, 3, row_hdr2, hdr_style)
        self.xls_write_row(ws, None, data, parser, 4, row_hdr3, hdr_style)
        self.xls_write_row(ws, None, data, parser, 5, row_hdr6, hdr_style)
        self.xls_write_row_header(ws, 6, row_balance, hdr_style, set_column_size=True)

        row_count = 7
        ws.horz_split_pos = row_count

        for l in parser.lines():
            if l['type'] != 3:
                style = row_normal_style
            else:
                style = row_bold_style

            self.xls_write_row(ws, l, data, parser,
                        row_count, row_balance, style)
            row_count += 1

        pass

account_balance_report_xls(
        'report.account.partner.balance.xls',
        'res.partner',
        'addons/account/report/account_partner_balance.rml',
        parser=partner_balance_i,
        header=False)


