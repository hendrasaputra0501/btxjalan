# -*- coding: utf-8 -*-
# Copyright 2010 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import xlwt
from report_engine_xls import report_xls
from ad_account_optimization.generic.account_financial_report import report_account_common
#from ad_account_optimization.report.account_balance_sheet_new import account_balance_sheet_new
import cStringIO

class account_balance_report_new_xls(report_xls):
    
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
    
    def _display_balance(self, name, balance):
        #print "xxxx",name
        if name == 'Net Profit':
            bl = 0
        else:
            if balance > 0:
                bl = abs(balance)
            elif balance < 0:
                bl = balance
            else:
                bl = 0
        return bl
    
    def _display_code(self, code):
        if code == 'Net Profit':
            code = ''
        else:
            code = code
        return code
    
    def _display_net(self, net):
        if net > 0:
            net = 'Net Profit'
        elif net < 0:
            net = 'Net Loss'
        else:
            net = ''
        return net
    
    ## Modules Begin
    def _size_col(sheet, col):
        return sheet.col_width(col)
     
    def _size_row(sheet, row):
        return sheet.row_height(row)
        ## Modules End    
        
    def romawi_number(self, number):
        if number == 1:
            romawi_number = "I"
        elif number == 2:
            romawi_number = "II"
        elif number == 3:
            romawi_number = "III"
        elif number == 4:
            romawi_number = "IV"
        elif number == 5:
            romawi_number = "V"
        else:
            romawi_number = "Error Number"
        return romawi_number
    
    def generate_xls_report(self, parser, data, obj, wb):
        #print parser._sum_currency_amount_account(1)
        c = parser.localcontext['company']
        ws = wb.add_sheet(('Balance Sheet- %s - %s' % (c.partner_id.ref, c.currency_id.name))[:31])
        #ws.panes_frozen = True
        #ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.show_grid = 0
        ####A####
        ws.col(0).width     = len("AB")*256
        ####B####
        ws.col(1).width     = len("AB")*256
        ####C####
        ws.col(2).width     = len("AB")*256
        ####D####
        ws.col(3).width     = len("ABCDEFGHIJKL")*1024
        ####E####
        #ws.col(4).width     = len("ABC")*256
        ####F####
        #ws.col(5).width     = len("ABC")*
        ####G####
        ws.col(6).width     = len("AB")*256
        ####H####
        ws.col(7).width     = len("ABCDEFG")*1024
        ####I####
        ws.col(8).width     = len("AB")*256
        ####J####
        ws.col(9).width     = len("ABCDEFG")*1024
        ####K####
        ws.col(10).width    = len("AB")*len("AB")*256
        
        
        
        judul1      = "PT GUNUNG BARA UTAMA"
        judul2      = "Balance Sheet"
        tgl_judul   = "TANGGAL"
        judul4      = "(In Indonesian Rupiah)"
        #print "1111111111"
        cols_specs = [
                # Headers data
                
                ('Title', 11, 0, 'text',
                    lambda x, d, p: judul1),
                ('Title2', 11, 0, 'text',
                    lambda x, d, p: judul2),
                ('Title3', 11, 0, 'text',
                    lambda x, d, p: x['result_select_date_hdr']),
                ('Title4', 11, 0, 'text',
                    lambda x, d, p: judul4),
                ('Kosong', 11, 0, 'text',
                    lambda x, d, p: " "),
                ('Notes', 1, 0, 'text',
                    lambda x, d, p: 'Notes'),
                ('Select Date', 1, 0, 'text',
                    lambda x, d, p: x['select_date']),
                ('Initial Date', 1, 0, 'text',
                    lambda x, d, p: x['initial_date']),
                
                ('Rp', 1, 0, 'text',
                    lambda x, d, p: 'Rp.'),
                
                
                
                      
#                ('Fiscal Year', 4, 0, 'text',
#                    lambda x, d, p: self._display_fiscalyear(p, d)),
#                ('Create Date', 4, 0, 'text',
#                    lambda x, d, p: 'Create date: ' + p.formatLang(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),date_time = True)),
#                ('Filter', 8, 0, 'text',
#                    lambda x, d, p: self._display_filter(p, d)),
#                ('Currency', 8, 0, 'number',
#                    lambda x, d, p: 'Currency Rate IDR: ' + p.formatLang(self._sum_currency_amount(p, 1))),
#                # Balance column
#                ('Asset Code', 1, 67, 'text',
#                    lambda x, d, p: x['code1']),
#                ('Assets Account', 1, 270, 'text',
#                    lambda x, d, p: '  '*x['level1'] + x['name1']),
                
                ('Field Kosong', 1, 0, 'text',
                    lambda x, d, p: ''),
                   
                ('Assets Account Level 2', 2, 0, 'text',
                    lambda x, d, p: x['name']),
                ('Liability Account Level 2', 2, 0, 'text',
                    lambda x, d, p: 'LIABILITY & EQUITY'),
                      
                      
                      
                ('Total', 1, 0, 'text',
                    lambda x, d, p: 'Total'),
                      
                      
                      
                ('Level 3 Name', 1, 0, 'text',
                    lambda x, d, p: 'Total '+ lv3_name),
                      
                      
                      
                ('BalanceA', 1, 0, 'number',
                    lambda x, d, p: x['balance_tot1']),
                ('BalanceB', 1, 0, 'number',
                    lambda x, d, p: x['balance_tot2']),
                #########ASSET TOTAL###########
                ('Asset Total Label', 3, 0, 'text',
                    lambda x, d, p: 'TOTAL ASSET'),
                ('Asset TotalA', 1, 0, 'number',
                    lambda x, d, p: x['asset_tot1']),
                ('Asset TotalB', 1, 0, 'number',
                    lambda x, d, p: x['asset_tot2']),
                ##################################
                
                #########LIABILITY TOTAL###########
                ('Liability Total Label', 3, 0, 'text',
                    lambda x, d, p: 'TOTAL LIABILITY & EQUITY'),
                ('Liability TotalA', 1, 0, 'number',
                    lambda x, d, p: x['liability_tot1']),
                ('Liability TotalB', 1, 0, 'number',
                    lambda x, d, p: x['liability_tot2']),
                      
                      
                ('Net Loss Label', 3, 0, 'text',
                    lambda x, d, p: 'Current Year Surplus / (Deficit)'),
                ('Net Loss', 1, 0, 'number',
                    lambda x, d, p: x['net_loss']),
                ('Net Loss2', 1, 0, 'number',
                    lambda x, d, p: x['net_loss2']),
                ##################################
                
                ('NumberA', 1, 0, 'text',
                    lambda x, d, p: romawi_number),
                ('NameA', 1, 0, 'text',
                    lambda x, d, p: x['name']),
                
                ('Name1A', 1, 0, 'text',
                    lambda x, d, p: x['name']),
                      
                ('Balance1A', 1, 0, 'number',
                    lambda x, d, p: x['balance']),
                ('Balance1B', 1, 0, 'number',
                    lambda x, d, p: x['balance2']),
                
                ######Edit#######
                ('Balance1ALia', 1, 0, 'number',
                    lambda x, d, p: -(x['balance'])),
                ('Balance1BLia', 1, 0, 'number',
                    lambda x, d, p: -(x['balance2'])),
                ####################################
                
                
                ('Asset Balance', 1, 0, 'number',
                    lambda x, d, p: x['balance1']),
                      
                ('Asset Balance IDR', 1, 0, 'number',
                    lambda x, d, p: parser._sum_currency_amount_account(x['balance1'])),
                ('Liab. Code', 1, 0, 'text',
                    lambda x, d, p: self._display_code(x['code'])),
                ('Liabilities and Equities Account', 1, 0, 'text',
                    lambda x, d, p: '  '*x['level'] + self._display_code(x['name'])),
                ('Liab. Balance', 1, 0, 'number',
                    lambda x, d, p: self._display_balance(x['name'],x['balance'])),
                ('Liab. Balance IDR', 1, 0, 'number',
                    lambda x, d, p: parser._sum_currency_amount_account(self._display_balance(x['name'],x['balance']))),
                      
#                ('Footer1', 1, 270, 'number',
#                    lambda x, d, p: x['footer1']),
#                ('Footer2', 1, 270, 'text',
#                    lambda x, d, p: 'SUM(B4:B18)'),
#                ('Footer3', 1, 270, 'text',
#                    lambda x, d, p: 'xxxx3'),
                
                
        ]
        
        ##################TITLE TEMPLATE########################
        row_hdr0 = self.xls_row_template(cols_specs, ['Kosong'])
        row_hdr1 = self.xls_row_template(cols_specs, ['Title'])
        row_hdr2 = self.xls_row_template(cols_specs, ['Title2'])
        row_hdr3 = self.xls_row_template(cols_specs, ['Title3'])
        row_hdr4 = self.xls_row_template(cols_specs, ['Title4'])
        row_hdr5 = self.xls_row_template(cols_specs, ['Kosong'])
        
        row_hdr_date = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong','Field Kosong','Field Kosong','Field Kosong','Field Kosong','Select Date','Field Kosong','Initial Date'])
        row_hdr_notes = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong','Field Kosong','Field Kosong','Notes','Field Kosong','Rp','Field Kosong','Rp'])
        
        #row_hdr_date = self.xls_row_template(cols_specs, ['Notes'])
        #######################################################
        ##################ASSET TEMPLATE########################
        row_asset_level2 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Assets Account Level 2'])
        row_asset_level2_kosong = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong'])
        row_asset_total_level2 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Level 3 Name','Field Kosong','Field Kosong','Field Kosong','Field Kosong','BalanceA','Field Kosong', 'BalanceB'])
        row_asset_level3 = self.xls_row_template(cols_specs, ['NumberA','Field Kosong','NameA'])
        row_asset_level4 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong','Name1A','Field Kosong','Field Kosong','Field Kosong','Balance1A','Field Kosong', 'Balance1B'])
        row_asset_total = self.xls_row_template(cols_specs, ['Field Kosong','Asset Total Label'])
        #row_asset_total = self.xls_row_template(cols_specs, ['Field Kosong','Asset Total Label','Field Kosong','Field Kosong','Field Kosong','Asset TotalA','Field Kosong', 'Asset TotalB'])
        #######################################################
        
        ##################LIABILITY TEMPLATE########################
        row_liability_level2 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Liability Account Level 2'])
        row_liability_level2_kosong = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong'])
        row_liability_total_level2 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Level 3 Name','Field Kosong','Field Kosong','Field Kosong','Field Kosong','BalanceA','Field Kosong', 'BalanceB'])
        row_liability_level3 = self.xls_row_template(cols_specs, ['NumberA','Field Kosong','NameA'])
        ###Edit#####
        row_liability_level4 = self.xls_row_template(cols_specs, ['Field Kosong','Field Kosong','Field Kosong','Name1A','Field Kosong','Field Kosong','Field Kosong','Balance1ALia','Field Kosong', 'Balance1BLia'])
        ############
        row_liability_total = self.xls_row_template(cols_specs, ['Field Kosong','Liability Total Label'])
        
        row_net_loss = self.xls_row_template(cols_specs, ['Field Kosong','Net Loss Label','Field Kosong','Field Kosong','Field Kosong','Net Loss','Field Kosong', 'Net Loss2'])
        #######################################################
        
        ## Style variable Begin
        hdr_style = xlwt.easyxf('pattern: pattern solid, fore_color gray25;')
        row_normal_style=  xlwt.easyxf('font: height 200, name Times New Romance; align: wrap off;' ,num_format_str='#,##0;(#,##0)')
        row_bold_underline_style = xlwt.easyxf('font: height 200, name Times New Romance, underline on, bold on; align: wrap on, vert centre, horiz centre;',num_format_str='#,##0;(#,##0)')
        row_italic_style = xlwt.easyxf('font: height 200, name Times New Romance, italic on, bold off; align: wrap off,',num_format_str='#,##0;(#,##0)')
        row_bold_style = xlwt.easyxf('font: height 200, name Times New Romance, bold on; borders: bottom dotted;',num_format_str='#,##0;(#,##0)')
        row_bold_non_border_style = xlwt.easyxf('font: height 200, name Times New Romance, bold on;',num_format_str='#,##0;(#,##0)')
        row_bold_non_border_center_style = xlwt.easyxf('font: height 200, name Times New Romance, bold on; align: vert centre, horiz centre;',num_format_str='#,##0;(#,##0)')
        row_bold_center_style = xlwt.easyxf('font: height 200, name Times New Romance, bold on; align: wrap on, vert centre, horiz centre; borders: bottom double;',num_format_str='#,##0;(#,##0)')
        row_bold_right_style = xlwt.easyxf('font: height 200, name Times New Romance, bold on; borders: bottom double;',num_format_str='#,##0;(#,##0)')
        ############TITLE################
        tittle_style0 = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color white;')
        tittle_style1 = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold on; align: wrap on, vert centre, horiz centre;')
        tittle_style2 = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre;')
        tittle_style3 = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre;')
        tittle_style4 = xlwt.easyxf('font: height 200, name Times New Romance, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz centre;')
        tittle_style5 = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre;')
        
        tittle_date = xlwt.easyxf('font: height 200, name Times New Romance, colour_index black, bold on; align: wrap on, vert centre, horiz centre;')
        tittle_notes = xlwt.easyxf('font: height 200, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre; borders: bottom dotted;')
        ##################################
        
        row_bold_top_border_style = xlwt.easyxf('font: height 200, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz centre; borders: top dotted;')
        tittle_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold on; align: wrap on, vert centre, horiz centre; pattern: pattern solid, fore_color gray25;')
        subtittle_left_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color gray25;')
        subtittle_right_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index brown, bold on, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color gray25;')
        subtittle_top_and_bottom_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color gray25;')
        blank_style = xlwt.easyxf('font: height 650, name Times New Romance, colour_index brown, bold off; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color gray25;')
        normal_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index black, bold off; align: wrap on, vert centre, horiz left;')
        total_style = xlwt.easyxf('font: height 240, name Times New Romance, colour_index brown, bold on, italic on; align: wrap on, vert centre;', num_format_str='#,##0.00;(#,##0.00)')
        
        ## Style variable End

        # Write headers Title
        #c = parser.get_data(data)
        #print "---------------------------------------------", c
        result_select_date_hdr  = '2013-01-01'#c['result_select_date_hdr']
        select_date             = '2013-01-01'#c['result_select_date']
        initial_date            = '2013-01-01'#c['result_initial_date']
        
        self.xls_write_row(ws, None, data, parser, 0, row_hdr0, tittle_style0)
        self.xls_write_row(ws, None, data, parser, 1, row_hdr1, tittle_style1)
        self.xls_write_row(ws, None, data, parser, 2, row_hdr2, tittle_style2)
        self.xls_write_row(ws, {'result_select_date_hdr' : result_select_date_hdr}, data, parser, 3, row_hdr3, tittle_style3)
        self.xls_write_row(ws, None, data, parser, 4, row_hdr4, tittle_style4)
        self.xls_write_row(ws, None, data, parser, 5, row_hdr5, tittle_style5)
        
        self.xls_write_row(ws, {'select_date' : select_date, 'initial_date' : initial_date}, data, parser, 7, row_hdr_date, tittle_date)
        ###Remove Border###
        #self.xls_write_row(ws, None, data, parser, 8, row_hdr_notes, tittle_notes)
        ws.write(8, 5, 'Notes', tittle_notes)
        for i in [7,9]:
            ws.write(8, i, 'Rp', tittle_notes)
            #ws.write(8, 9, 'Rp', tittle_notes)
        
        
        #self.xls_write_row(ws, None, data, parser, 6, row_hdr6, blank_style)
#        self.xls_write_row_header(ws, 6, row_balance, hdr_style, set_column_size=True)
#
        level3_no     = 0
        lv3_name    = ""
        lv3_total    = 0.0
        lv3_total2    = 0.0
        total_asset = 0.0
        total_asset2 = 0.0
        row_count = 11
        #ws.horz_split_pos = row_count
        
        total = {
                     'tot_asset':0,
                     'tot_lia':0,
                     'tot_income':0,
                     'tot_expenses':0,
                     'tot_income2':0,
                     'tot_expenses2':0,
                     }
#        for a in parser.get_lines():                   
#            
#            if a['level1'] <> 2:
#                style = row_normal_style
#            else:
#                #style = row_bold_style
#                style = row_normal_style
#                total['tot_asset'] += a['balance1']
#                
#            if a['level'] <> 2:
#                style = row_normal_style
#            else:
#                #style = row_bold_style
#                style = row_normal_style
#                total['tot_lia'] += a['balance']
#            
#            self.xls_write_row(ws, a, data, parser, row_count, row_balance, style)
#            row_count += 1          
        #-------------------------------
        for w in parser.get_lines('income'):
            if w['type'] <> 'view': 
                style = row_normal_style   
                total['tot_income'] += w['balance']
                total['tot_income2'] += w['balance2']
            else:
                style = row_bold_style
        for e in parser.get_lines('expense'):
            if e['type'] <> 'view':
                style = row_normal_style
                total['tot_expenses'] += e['balance']
                total['tot_expenses2'] += e['balance2']
            else:
                style = row_bold_style
        #print "yyyyyyyyy",total['tot_income']+total['tot_expenses']
        #-------------------------------
        total['tot_net'] = abs(total['tot_income'])-abs(total['tot_expenses'])
        total['tot_net2'] = abs(total['tot_income2'])-abs(total['tot_expenses2'])
        
        print "total['tot_net']--------------------------------->>", total['tot_income'],'VS',total['tot_expenses'], '-------', total['tot_net']
        
        for a in parser.get_lines('asset'):
            print "BBBBBBBBBBBBBBBBB"
            if a['level'] == 2:
                style = row_bold_underline_style
            elif a['level'] == 3:
                style = row_italic_style
            else:
                style = row_normal_style
            if a['type'] == 'view' and a['level'] == 2:
                self.xls_write_row(ws, a, data, parser, row_count, row_asset_level2, style)
                row_count += 1
                self.xls_write_row(ws, a, data, parser, row_count, row_asset_level2_kosong, style)
                row_count += 1
                
            if a['type'] == 'view' and a['level'] == 3:
                level3_no+=1
                romawi_number = self.romawi_number(level3_no)
                
                total_asset += lv3_total
                total_asset2 += lv3_total2
                if lv3_name <> "":
                    print "level",level3_no,total_asset,total_asset2
                    ###Remove Border###
                    ws.write(row_count, 7, None, row_bold_top_border_style)
                    ws.write(row_count, 9, None, row_bold_top_border_style)
                    row_count += 1
#                    self.xls_write_row(ws, a, data, parser, row_count, row_asset_level2_kosong, style)
#                    row_count += 1
                    ###Remove Border###
                    ws.write(row_count, 2, 'Total ' + lv3_name, row_bold_non_border_style)
                    ws.write(row_count, 7, lv3_total, row_bold_style)
                    ws.write(row_count, 9, lv3_total2, row_bold_style)
                    row_count += 1
                    #self.xls_write_row(ws, {'balance_tot1': lv3_total, 'balance_tot2': lv3_total2}, data, parser, row_count, row_asset_total_level2, row_bold_style)
                    row_count += 1
                    self.xls_write_row(ws, None, data, parser, row_count, row_asset_level2_kosong, style)
                    row_count += 1
                    
                self.xls_write_row(ws, a, data, parser, row_count, row_asset_level3, style)
                row_count += 2
                lv3_name =  a['name']
                lv3_total =  a['balance']
                lv3_total2 =  a['balance2']
                
            if a['type'] == 'view' and a['level'] == 4:
                self.xls_write_row(ws, a, data, parser, row_count, row_asset_level4, style)
                row_count += 1
        
        total_asset += lv3_total
        total_asset2 += lv3_total2
        self.xls_write_row(ws, a, data, parser, row_count, row_asset_level2_kosong, style)
        row_count += 1
        
        ws.write(row_count, 2, 'Total ' + lv3_name, row_bold_non_border_style)
        ws.write(row_count, 7, lv3_total, row_bold_style)
        ws.write(row_count, 9, lv3_total2, row_bold_style)
        row_count += 3
        ###Remove Border###
        #self.xls_write_row(ws, {'balance_tot1': lv3_total, 'balance_tot2': lv3_total2}, data, parser, row_count, row_asset_total_level2, row_bold_style)
        #row_count += 3
        
        #ws.write(row_count, 2, 'Total ASSET', row_bold_non_border_center_style)
        self.xls_write_row(ws, None, data, parser, row_count, row_asset_total, row_bold_non_border_center_style)
        ws.write(row_count, 7, total_asset, row_bold_right_style)
        ws.write(row_count, 9, total_asset2, row_bold_right_style)
        row_count += 5
        ###REmove Border###
        #self.xls_write_row(ws, {'asset_tot1': total_asset, 'asset_tot2': total_asset2}, data, parser, row_count, row_asset_total, row_bold_center_style)
        #row_count += 5
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        lv3_name    = ""
        lv3_total    = 0.0
        total_liability = 0.0
        lv3_total2    = 0.0
        total_liability2 = 0.0
        
        self.xls_write_row(ws, None, data, parser, row_count, row_liability_level2, row_bold_underline_style)
        row_count += 2
        
        for a in parser.get_lines('liability'):
            if a['level'] == 3:
                style = row_italic_style
            else:
                style = row_normal_style
            if a['type'] == 'view' and a['level'] == 3:
                #print "AAA"
                level3_no+=1
                romawi_number = self.romawi_number(level3_no)
                total_liability += lv3_total
                total_liability2 += lv3_total2
                if lv3_name <> "":
                    
                    ws.write(row_count, 7, None, row_bold_top_border_style)
                    ws.write(row_count, 9, None, row_bold_top_border_style)
                    row_count += 1
                    ###Remove###
#                    self.xls_write_row(ws, a, data, parser, row_count, row_liability_level2_kosong, style)
#                    row_count += 1
                    ws.write(row_count, 2, 'Total ' + lv3_name, row_bold_non_border_style)
                    ws.write(row_count, 7, lv3_total, row_bold_style)
                    ws.write(row_count, 9, lv3_total2, row_bold_style)
                    row_count += 1
                    #self.xls_write_row(ws, {'balance_tot1': lv3_total, 'balance_tot2': lv3_total2}, data, parser, row_count, row_liability_total_level2, row_bold_style)
                    #row_count += 1
                    self.xls_write_row(ws, None, data, parser, row_count, row_liability_level2_kosong, style)
                    row_count += 1
                    
                self.xls_write_row(ws, a, data, parser, row_count, row_liability_level3, style)
                row_count += 2
                lv3_name =  a['name']
                ####Edit####
                lv3_total =  -(a['balance'])
                lv3_total2 =  -(a['balance2'])
                ########
                
            if a['type'] == 'view' and a['level'] == 4:
                self.xls_write_row(ws, a, data, parser, row_count, row_liability_level4, row_normal_style)
                row_count += 1
        
        total_liability += lv3_total
        total_liability2 += lv3_total2
        
        ####################
        total_liability += total['tot_net']
        total_liability2 += total['tot_net2']
        ####################
        self.xls_write_row(ws, a, data, parser, row_count, row_liability_level2_kosong, style)
        row_count += 1
        
        ws.write(row_count, 2, 'Total ' + lv3_name, row_bold_non_border_style)
        ws.write(row_count, 7, lv3_total, row_bold_style)
        ws.write(row_count, 9, lv3_total2, row_bold_style)
        row_count += 3
        ###Remove Border###
        #self.xls_write_row(ws, {'balance_tot1': lv3_total, 'balance_tot2': lv3_total2}, data, parser, row_count, row_liability_total_level2, row_bold_style)
        #row_count += 3
        
        ws.write(row_count, 2, 'Current Year Surplus / (Deficit)', row_bold_non_border_style)
        ws.write(row_count, 7, total['tot_net'], row_bold_style)
        ws.write(row_count, 9, total['tot_net2'], row_bold_style)
        row_count += 2
        ###Remove Border###
        #self.xls_write_row(ws, {'net_loss': total['tot_net'], 'net_loss2': total['tot_net2']}, data, parser, row_count, row_net_loss, style)
        #row_count += 2
        
        self.xls_write_row(ws, None, data, parser, row_count, row_liability_total, row_bold_non_border_center_style)
        ws.write(row_count, 7, total_liability, row_bold_right_style)
        ws.write(row_count, 9, total_liability2, row_bold_right_style)
        row_count += 5
        
        ###Remove Border###
        #self.xls_write_row(ws, {'liability_tot1': total_liability, 'liability_tot2': total_liability2}, data, parser, row_count, row_liability_total, row_bold_center_style)
        #row_count += 1
        
        
#        c = parser.get_data(data)
#        total = {
#                 'tot_asset':0,
#                 'tot_lia':0,
#                 'tot_asset_idr':0,
#                 'tot_lia_idr':0,
#                 }
#        for a in parser.get_lines():
#            if a['level1'] <> 2:
#                style = row_normal_style
#            else:
#                #style = row_bold_style
#                style = row_normal_style
#                total['tot_asset'] += a['balance1']
#                total['tot_asset_idr'] += parser._sum_currency_amount_account(a['balance1'])
#                
#            if a['level'] <> 2:
#                style = row_normal_style
#            else:
#                #style = row_bold_style
#                style = row_normal_style
#                total['tot_lia'] += a['balance']
#                total['tot_lia_idr'] += parser._sum_currency_amount_account(a['balance'])
#            
#            self.xls_write_row(ws, a, data, parser, row_count, row_balance, style)
#            row_count += 1          
#        
#
#        cols_specs = [
#                ('Label_Asset_Total', 2, 67, 'text',
#                    lambda x, d, p: 'BALANCE ASSET'),
#                ('Label_Liabilities_Total', 2, 67, 'text',
#                    lambda x, d, p: 'BALANCE LIABILITY AND EQUITY'),
#                # Row Total
#                ('Asset Total', 1, 67, 'number',
#                    lambda x, d, p: x['tot_asset']),
#                ('Asset Total IDR', 1, 80, 'number',
#                    lambda x, d, p: x['tot_asset_idr']),
#                ('Liabilities and Equities Total', 1, 67, 'number',
#                    lambda x, d, p: x['tot_lia']),
#                ('Liabilities and Equities Total IDR', 1, 80, 'number',
#                    lambda x, d, p: x['tot_lia_idr']),
#        ]
#        row_ftr1 = self.xls_row_template(cols_specs, ['Label_Asset_Total','Asset Total','Asset Total IDR','Label_Liabilities_Total', 'Liabilities and Equities Total', 'Liabilities and Equities Total IDR'])
#
#        row_count += 1
#        self.xls_write_row(ws, total, data, parser, row_count, row_ftr1, total_style)                  
#        row_count += 1
        
#        self.xls_write_row(ws, {'footer1' : level3_no}, data, parser, row_count, row_footer, total_style)
#        row_count += 1
        
        #ws = wb.add_sheet('countif')
        #ws.write(row_count, 0, xlwt.Formula('SUM(A1:F1)'),total_style) 
        
        pass

account_balance_report_new_xls(
        'report.account.balancesheet.new.xls',
        'account.account',
        'addons/account/report/account_financial_report.rml',
        parser=report_account_common,
        header=False)


