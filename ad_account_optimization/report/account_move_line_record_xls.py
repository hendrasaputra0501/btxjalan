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
import string
import time
import xlwt
from report_engine_xls import report_xls
from ad_account_optimization.generic.account_move_line_record import journal_print
from tools.translate import _
from sys import *
import random
import datetime

header_line = []
ws = []

class account_move_line_xls(report_xls):

    """def _get_start_date(self, data):
        # ok
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        return ''
    
    def _get_end_date(self, data):
        # ok
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        return ''

    def get_start_period(self, data):
        if data.get('form', False) and data['form'].get('period_from', False):
            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr,self.uid,data['form']['period_from']).name
        return ''

    def get_end_period(self, data):
        if data.get('form', False) and data['form'].get('period_to', False):
            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr, self.uid, data['form']['period_to']).name
        return ''
    
    def _get_target_move(self, data):
        if data.get('form', False) and data['form'].get('target_move', False):
            if data['form']['target_move'] == 'By date':
                return _('All Entries')
            return _('All Posted Entries')
        return ''
    
    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return _('Date')
            elif data['form']['filter'] == 'filter_period':
                return _('Periods')
        return _('No Filter')
    
    def _display_filter(self, parser, data):
        filter_mode = self._get_filter(data)
        filter_string = filter_mode
        if filter_mode == 'Date':
            filter_string = '%s -> %s' % (parser.formatLang(self._get_start_date(data), date=True),
                                          parser.formatLang(self._get_end_date(data), date=True))
        elif filter_mode == 'Periods':
            filter_string = '%s -> %s' % (self.get_start_period(data),
                                 self.get_end_period(data))

        moves_string = self._get_target_move(data)
        display_acct_string = ''
        if data['form']['sort_selection'] == 'date':
            display_acct_string = 'By date'
        elif data['form']['sort_selection'] == 'to_number(name,"999999999")':
            display_acct_string = 'By entry number'
        else:
            display_acct_string = 'By reference number'
        
        #fiscal_year_str = parser.get_fiscalyear_text(data['form'])
        #period_date_str = parser.get_periods_and_date_text(data['form'])
        print "######>>>>>>>>>>>",data['form']
        return data['form'] #'Fiscal Year: %s, Period & Date By: %s' % (fiscal_year_str, period_date_str)"

    def _display_fiscalyear(self, parser, data):
         k = parser.get_fiscalyear_text(data)
         if k:
            k = 'Fiscal Year: %s' % (k)
         k = "############^^^^^^^^^^^^############"
         print "--------------------------->>>>>>",k
         return k"""
#===============================================================================
#    def _get_start_date(self, data):
#        # ok
#        if data.get('form', False) and data['form'].get('date_from', False):
#            return data['form']['date_from']
#        return ''
#    
#    def _get_end_date(self, data):
#        # ok
#        if data.get('form', False) and data['form'].get('date_to', False):
#            return data['form']['date_to']
#        return ''
# 
#    def get_start_period(self, data):
#        if data.get('form', False) and data['form'].get('period_from', False):
#            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr,self.uid,data['form']['period_from']).name
#        return ''
# 
#    def get_end_period(self, data):
#        if data.get('form', False) and data['form'].get('period_to', False):
#            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr, self.uid, data['form']['period_to']).name
#        return ''
#    
#    def _get_target_move(self, data):
#        if data.get('form', False) and data['form'].get('target_move', False):
#            if data['form']['target_move'] == 'all':
#                return _('All Entries')
#            return _('All Posted Entries')
#        return ''
#    
#    def _get_filter(self, data):
#        if data.get('form', False) and data['form'].get('filter', False):
#            if data['form']['filter'] == 'filter_date':
#                return _('Date')
#            elif data['form']['filter'] == 'filter_period':
#                return _('Periods')
#        return _('No Filter')
#===============================================================================
    
#===============================================================================
#    def _display_filter(self, parser, data):
#        filter_mode = self._get_filter(data)
#        filter_string = filter_mode
#        if filter_mode == 'Date':
#            filter_string = '%s -> %s' % (parser.formatLang(self._get_start_date(data), date=True),
#                                          parser.formatLang(self._get_end_date(data), date=True))
#        elif filter_mode == 'Periods':
#            filter_string = '%s -> %s' % (self.get_start_period(data),
#                                 self.get_end_period(data))
# 
#        moves_string = self._get_target_move(data)
#        display_acct_string = ''
#        if data['form']['display_account'] == 'bal_all':
#            display_acct_string = 'All'
#        elif data['form']['display_account'] == 'bal_movement':
#            display_acct_string = 'With movements'
#        else:
#            display_acct_string = 'With balance is not equal to 0'
#        
#        fiscal_year_str = parser.get_fiscalyear_text(data['form'])
#        period_date_str = parser.get_periods_and_date_text(data['form'])
# 
#        return 'Fiscal Year: %s, Period & Date By: %s' % (fiscal_year_str, period_date_str)
#===============================================================================

    #===========================================================================
    # def _display_fiscalyear(self, parser, data):
    #    """k = parser.get_fiscalyear_text(data)
    #    if k:
    #        k = 'Fiscal Year: %s' % (k)"""
    #    k = "asdfasdfasdfasdf"
    #    return k   
    #===========================================================================
    ## Modules Begin
    def _size_col(sheet, col):
        return sheet.col_width(col)
     
    def _size_row(sheet, row):
        return sheet.row_height(row)
        
    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
    
    """def create_header(self, xxx):
        
        print "==================xxx=",xxx
        judul = "Judul judulan"
        return {'judul':judul}"""
    
    def generate_xls_report(self, parser, data, obj, wb):
        
        
        for a in parser.objects:
            if a.company_id.name in header_line:
                a.company_id.name = ''
            else:
                header_line.append(a.company_id.name)

            if len(a.company_id.name) != 0:
                c = parser.localcontext['company']
                ws = wb.add_sheet(('JOURNAL LEDGER %s - %s - %s ' % (self.id_generator(), c.partner_id.ref, c.currency_id.name))[:31])
                ws.panes_frozen = True
                ws.remove_splits = True
                ws.portrait = 0 # Landscape
                ws.fit_width_to_pages = 1
                judul = "JOURNAL LEDGER REPORT"
        
                cols_specs = [
                        # Headers data
                        ('Title',  8, 0, 'text',
                            lambda x, d, p: judul),
                        ('Kosong', 8, 0, 'text',
                            lambda x, d, p: ""),
                       ('Create Date', 8, 0, 'text',
                            lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
                        # Balance column
                        ('Entry'           , 1, 67, 'text',
                            lambda x, d, p: x['name_split']),
                        ('Date'           , 1, 67, 'text',
                            lambda x, d, p: p.formatLang(x['date'],date=True)),
                        ('Period'   , 1, 80, 'text',
                            lambda x, d, p: x.period_id['name']),
                        ('Journal'        , 1, 200, 'text',
                            lambda x, d, p: x.journal_id['code']),
                        ('Partner'        , 1, 200, 'text',
                            lambda x, d, p: x.partner_id['name']),
                        ('Reference'        , 1, 200, 'text',
                            lambda x, d, p: x['ref']),
                        ('Debit'       , 1, 80, 'number',
                            lambda x, d, p: abs(x['amount'])),
                        ('Credit'      , 1, 80, 'number',
                            lambda x, d, p: abs(x['amount'])),
                              

                       # Account Total
                        ('Blank', 3, 0, 'text',
                            lambda x, d, p: ""),
                        ('Account', 1, 0, 'text',
                            lambda x, d, p: x.account_id['code']),
                        ('Account Name', 1, 0, 'text',
                            lambda x, d, p: x.account_id['name']),
                        ('Description', 1, 0, 'text',
                            lambda x, d, p: x['name']),                              
                        ('Account Debit', 1, 0, 'number',
                            lambda x, d, p: x['debit']),
                        ('Account Credit', 1, 0, 'number',
                            lambda x, d, p: x['credit']),

        
                ]
        
                row_hdr0 = self.xls_row_template(cols_specs, ['Title'])
                row_hdr1 = self.xls_row_template(cols_specs, ['Kosong'])
                row_hdr2 = self.xls_row_template(cols_specs, ['Create Date'])
                row_hdr4 = self.xls_row_template(cols_specs, ['Kosong'])

                row_balance = self.xls_row_template(cols_specs,[
                                                                'Entry',
                                                                'Date',
                                                                'Period',
                                                                'Journal',
                                                                'Partner',
                                                                'Reference',
                                                                'Debit',
                                                                'Credit'
                                                                ])
                hdr_account_total = self.xls_row_template(cols_specs,['Blank', 'Account', 'Account Name',  'Description', 'Account Debit', 'Account Credit'])
        
                ## Style variable Begin
                hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color white;')
                row_normal_style=  xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                row_bold_style = xlwt.easyxf('font: bold on;')
        
                tittle_style = xlwt.easyxf('font: height 240, name Arial Black, colour_index black, bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color white;')
                subtittle_left_style = xlwt.easyxf('font: name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
                subtittle_right_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
                subtittle_top_and_bottom_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
                blank_style = xlwt.easyxf('font: height 650, name Arial, colour_index brown, bold off; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')
                normal_style = xlwt.easyxf('font: height 240, name Arial, colour_index black, bold off; align: wrap on, vert centre, horiz left;')
                total_style = xlwt.easyxf('font: height 240, name Arial, colour_index brown, bold on, italic on; align: wrap on, vert centre;', num_format_str='#,##0.00;(#,##0.00)')
                ## Style variable End
        
                # Write headers
                self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style)
                self.xls_write_row(ws, None, data, parser, 1, row_hdr1, blank_style)
                self.xls_write_row(ws, None, data, parser, 2, row_hdr2, subtittle_left_style)
                #self.xls_write_row(ws, None, data, parser, 3, row_hdr3, hdr_style)
                self.xls_write_row(ws, None, data, parser, 3, row_hdr1, blank_style)
                self.xls_write_row_header(ws, 4, row_balance, hdr_style, set_column_size=True)
                self.xls_write_row_header(ws, 5, hdr_account_total, hdr_style)
        
                row_count = 6
                ws.horz_split_pos = row_count
                
                for b in parser.objects:
                    r = ws.row(row_count)
                    self.xls_write_row(ws, b, data, parser, row_count, row_balance, row_bold_style)
                    row_count += 1 
                    
                    for c in b.line_id:
                    
                        self.xls_write_row(ws, c, data, parser, row_count, hdr_account_total, row_normal_style)
                        row_count += 1 

        pass

account_move_line_xls(
        'report.account.move.line.xls',
        'account.journal.period',
        #'account.move',
        'addons/ad_account_optimization/report/account_move_line_record_h.rml',
        parser=journal_print,
        header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
