# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from report_engine_xls import report_xls
from account.report.account_partner_ledger import third_party_ledger
import cStringIO

class account_balance_report_xls(report_xls):
    def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):

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
        display_partner_string = parser._get_partners()

        return 'Display Partner: %s, Filter By: %s, Target Moves: %s' % (display_partner_string, filter_string, moves_string)

    def _display_fiscalyear(self, parser, data):
        k = parser._get_fiscalyear(data)
        if k:
            k = 'Fiscal Year: %s' % (k)
        return k

    def generate_xls_report(self, parser, data, obj, wb):
        c = parser.localcontext['company']
        ws = wb.add_sheet(('Partner Ledger')[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        judul = "PARTNER LEDGER"

        cols_specs = [
            # Headers data
            ('Title', 7, 0, 'text',
                    lambda x, d, p: judul),
            ('Kosong', 7, 0, 'text',
                    lambda x, d, p: ""),
            ('Fiscal Year', 5, 0, 'text',
                lambda x, d, p: self._display_fiscalyear(p, d)),
            ('Create Date', 2, 0, 'text',
                lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
            ('Filter', 7, 0, 'text',
                lambda x, d, p: self._display_filter(p, d)),

           # Line
            ('Date', 1, 65, 'text',
                lambda x, d, p: p.formatLang(x['date'],date=True)),
            ('JNRL', 1, 28, 'text',
                lambda x, d, p: x['code']),
            ('Ref.', 1, 45, 'text',
                lambda x, d, p: x['ref']),
            ('Entry Label', 1, 175, 'text',
                lambda x, d, p: x['name']),
            ('Debit', 1, 77, 'number',
                lambda x, d, p: x['debit']),
            ('Credit', 1, 75, 'number',
                lambda x, d, p: x['credit']),
            ('Balance', 1, 75, 'number',
                lambda x, d, p: x['progress']),

            # Partner Total
            ('Initial Balance', 4, 0, 'text',
                lambda x, d, p: 'Initial Balance'),
            ('Initial Balance Debit', 1, 0, 'number',
                lambda x, d, p: p._get_intial_balance(x)[0][0]),
            ('Initial Balance Credit', 1, 0, 'number',
                lambda x, d, p: p._get_intial_balance(x)[0][1]),
            ('Initial Balance Balance', 1, 0, 'number',
                lambda x, d, p: p._get_intial_balance(x)[0][2]),

            # Partner Line
            ('Partner Name', 4, 0, 'text',
                lambda x, d, p: '%s%s' % (x.ref and ('%s - ' % (x.ref)) or '', x.name)),
            ('Partner Debit', 1, 0, 'number',
                lambda x, d, p: p._sum_debit_partner(x)),
            ('Partner Credit', 1, 0, 'number',
                lambda x, d, p: p._sum_credit_partner(x)),
            ('Partner Balance', 1, 0, 'number',
                lambda x, d, p: (p._sum_debit_partner(x) - p._sum_credit_partner(x)) or 0.0),
        ]
        row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
        row_hdr5 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr1 = self.xls_row_template(cols_specs, ['Fiscal Year', 'Create Date'])
        row_hdr2 = self.xls_row_template(cols_specs, ['Filter'])
        row_hdr6 = self.xls_row_template(cols_specs, ['Kosong'])
        hdr_line = ['Date', 'JNRL', 'Ref.', 'Entry Label', 'Debit', 'Credit', 'Balance']
        hdr_partner_total = ['Partner Name', 'Partner Debit', 'Partner Credit', 'Partner Balance']
        hdr_initial_total = [ 'Initial Balance', 'Initial Balance Debit', 'Initial Balance Credit', 'Initial Balance Balance']

        row_line = self.xls_row_template(cols_specs, hdr_line)
        tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        subtittle_left_style = xlwt.easyxf('font: height 180, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
        hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;',num_format_str='#,##0.00;(#,##0.00)')
        row_partner_total = self.xls_row_template(cols_specs, hdr_partner_total)
        row_initial_total = self.xls_row_template(cols_specs, hdr_initial_total)

        # Style
        row_hdr_style = xlwt.easyxf( 'pattern: pattern solid, fore_color white;',num_format_str='#,##0.00;(#,##0.00)')
        row_partner_style = xlwt.easyxf('font: bold on;' 'borders: bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
        row_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')

        self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style)
        self.xls_write_row(ws, None, data, parser, 1, row_hdr5, hdr_style)
        self.xls_write_row(ws, None, data, parser, 2, row_hdr1, subtittle_left_style)
        self.xls_write_row(ws, None, data, parser, 3, row_hdr2, row_hdr_style)
        self.xls_write_row(ws, None, data, parser, 4, row_hdr6, hdr_style)
        self.xls_write_row_header(ws, 5, row_partner_total, row_hdr_style)
        self.xls_write_row_header(ws, 6, row_line, row_hdr_style, set_column_size=True)
        #self.xls_write_row_header(ws, 4, row_forward_total, row_hdr_style)

        row_count = 7
        ws.horz_split_pos = row_count

        for p in parser.objects:
            r = ws.row(row_count)
            self.xls_write_row(ws, p, data, parser,
                            row_count, row_partner_total, row_partner_style)
            row_count += 1
            if parser.initial_balance:
                self.xls_write_row(ws, p, data, parser,
                                    row_count, row_initial_total, row_style)
                row_count += 1

            for l in parser.lines(p):
                self.xls_write_row(ws, l, data, parser,
                                row_count, row_line, row_style)
                row_count += 1
        pass

account_balance_report_xls(
        'report.account.third_party_ledger.xls',
        'account.account',
        'addons/account/report/account_partner_ledger.rml',
        parser=third_party_ledger,
        header=False)


