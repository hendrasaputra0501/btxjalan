# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
import re
import pooler
from report import report_sxw
from account.report import account_profit_loss
from common_report_header import common_report_header
from tools.translate import _
import math
import datetime
import datetime, dateutil.parser
from dateutil.relativedelta import relativedelta


class report_balancesheet_horizontal_new(report_sxw.rml_parse, common_report_header):
    print "PPPPPPPPPPPPPPPPPPPPP"
    def __init__(self, cr, uid, name, context=None):
        super(report_balancesheet_horizontal_new, self).__init__(cr, uid, name, context=context)
        self.obj_pl = account_profit_loss.report_pl_account_horizontal(cr, uid, name, context=context)
        self.result_sum_dr = 0.000000000
        self.result_sum_cr = 0.000000000
        self.res_pl = {}
        self.result_sum_dr_currency = 0.000000000
        self.result = {}
        self.res_bl = {}
        self.res_bl_currency = {}
        self.result_temp = []
        self.localcontext.update({
            'time': time,
            'get_lines': self.get_lines,
            'get_lines_another': self.get_lines_another,
            'get_lines_another_total': self.get_lines_another_total,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
            'sum_dr': self.sum_dr,
            'sum_cr': self.sum_cr,
            'sum_dr_currency': self.sum_dr_currency,
            'sum_all': self.sum_all,
            'get_data':self.get_data,
            'get_pl_balance':self.get_pl_balance,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_sortby': self._get_sortby,
            'get_filter': self._get_filter,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_company':self._get_company,
            'get_target_move': self._get_target_move,
            'sum_currency_amount_account': self._sum_currency_amount_account,
            'digit':self.digit,
            'FormatWithCommas':self.FormatWithCommas,
            'commafy':self.commafy,
            'final_result': self.final_result,
        })
        self.context = context
        self.re_digits_nondigits = re.compile(r'\d+|\D+')
        
    def digit(self, price, decimal):
        af='%.'+str(decimal)+'f'
        #value = self.FormatWithCommas(af, price)
        value=af %price
        #print "*********VALUE ",value
        if str(value)[0:1]=='-':
            value=float(str(value)[1:len(str(value))])*(-1)*0.000000001
        else:
            value=float(value)*0.000000001
        return value
    
    def FormatWithCommas(self, format, value):
        parts = self.re_digits_nondigits.findall(format % (value,))
        for i in xrange(len(parts)):
            s = parts[i]
            if s.isdigit():
                parts[i] = self.commafy(s)
                break
        return ''.join(parts)
        
    def commafy(self, s):
        r = []
        for i, c in enumerate(reversed(s)):
            if i and (not (i % 3)):
                r.insert(0, ',')
            r.insert(0, c)
        return ''.join(r)
    
    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
            lang_dict = self.pool.get('res.users').read(self.cr,self.uid,self.uid,['context_lang'])
            data['lang'] = lang_dict.get('context_lang') or False
        return super(report_balancesheet_horizontal_new, self).set_context(objects, data, new_ids, report_type=report_type)
    
    def final_result(self):
        return self.res_pl
    
    def sum_dr(self):
        """print "dddddddddd",self.result_sum_dr
        if self.res_bl['type'] == _('Net Profit'):
            self.result_sum_dr += self.res_bl['balance']*-1"""
        return self.result_sum_dr

    def sum_cr(self):
        """if self.res_bl['type'] == _('Net Loss'):
            self.result_sum_cr += self.res_bl['balance']"""
        return self.result_sum_cr
    
    def sum_all(self):
        total = self.result_sum_cr - self.result_sum_dr
        return total
    
    def sum_dr_currency(self):
        """if self.res_bl['type'] == _('Net Profit'):
            self.result_sum_dr_currency += self.res_bl['balance']*-1"""
        return self.result_sum_dr_currency
    
    def get_pl_balance(self):
        return self.res_bl

    def get_data(self,data):
        #print "DATA-------------------------->>", data
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)

        #Getting Profit or Loss Balance from profit and Loss report
        self.obj_pl.get_data(data)
        self.res_bl = self.obj_pl.final_result()

        account_pool = db_pool.get('account.account')
        currency_pool = db_pool.get('res.currency')

        types = [
            'liability',
            'asset',
            'expense','income'
        ]

        ctx = self.context.copy()
        ctx['fiscalyear'] = data['form'].get('fiscalyear_id', False)

        if data['form']['filter'] == 'filter_period':
            #ctx['periods'] = data['form'].get('periods', False)
            ctx['period_from'] =  data['form'].get('period_from', False)
            ctx['period_to'] =  data['form'].get('period_to', False)
            #initial_date = (datetime.datetime.today()-datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        elif data['form']['filter'] == 'filter_date':
            ctx['date_from'] = data['form'].get('date_from', False)
            ctx['date_to'] =  data['form'].get('date_to', False)
            print "#####################################", ctx['date_from']
            
            result_select_date_hdr = dateutil.parser.parse(ctx['date_to'])
            result_select_date_hdr = result_select_date_hdr.strftime('%B %Y')
            
            result_select_date = dateutil.parser.parse(ctx['date_to'])
            result_select_date = result_select_date.strftime('%d-%b-%y')
            
            #result_initial_date = datetime.datetime.strptime(ctx['date_to'],"%d-%b-%y")
            
            #print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", result_initial_date
#            
#            result_initial_date = dateutil.parser.parse(ctx['date_to'])
#            result_initial_date = result_initial_date.strftime('%Y-%m-%d')
#            print "_______------------------------", result_initial_date
#            result_initial_date = (result_initial_date.strptime('%Y-%m-%d'))-(datetime.timedelta(days=30)).strftime('%Y-%m-%d')
#            print "_______------------------------1234", result_initial_date
#            
            initial_date = (datetime.datetime.strptime(ctx['date_to'],"%Y-%m-%d")-relativedelta(months=1))
            print "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", initial_date
        else:
            #datetime.datetime.today().strftime('%Y-%m-%d'),
            result_select_date_hdr = datetime.datetime.today().strftime('%B %Y')
            result_select_date = datetime.datetime.today().strftime('%d-%b-%y')
            result_initial_date = (datetime.datetime.today()-relativedelta(months=1))
            initial_date = (datetime.datetime.today()-relativedelta(months=1))
        print "*******************************************", initial_date
        
        period_search = self.pool.get('account.period').search(self.cr, self.uid, [('date_stop','>=',initial_date),('date_start','<=',initial_date)])
        period_browse = self.pool.get('account.period').browse(self.cr, self.uid, period_search)
        for period in period_browse:
            #period_search = self.pool.get('account.fiscalyear').search(self.cr, self.uid, [('date_stop','>=',initial_date),('date_start','<=',initial_date)])
            period_browse = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, [period.fiscalyear_id.id])
            for fiscal in period_browse:
                fiscal_date_start = fiscal.date_start 
            date_from2  = fiscal_date_start
            date_to2    = period.date_stop
            print "period.name---------------------------->>>", period.name, 'FROM :',date_from2 ,'TO :',date_to2
        #result_initial_date = datetime.datetime.strptime(date_to2,"%d-%b-%y")
        ctx['state'] = data['form'].get('target_move', 'all')
        
        #############################################################
        ctx2 = self.context.copy()
        ctx2['fiscalyear'] = data['form'].get('fiscalyear_id', False)

        ctx2['date_from']   = date_from2
        ctx2['date_to']     = date_to2
        ctx2['state'] = data['form'].get('target_move', 'all')
        
        #############################################################
        
        cal_list = {}
        pl_dict = {}
        account_dict = {}
        account_id = data['form'].get('chart_account_id', False)
        account_ids = account_pool._get_children_and_consol(cr, uid, account_id, context=ctx)
        accounts = account_pool.browse(cr, uid, account_ids, context=ctx)
        
        ##########################
        accounts2 = account_pool.browse(cr, uid, account_ids, context=ctx2)
        ##########################
        
        
        #print "accounts-------------------->>", accounts
        
        #print "CONTEXT2", ctx2
        
        if not self.res_bl:
            self.res_bl['type'] = _('Net Profit')
            self.res_bl['balance'] = 0.0

        if self.res_bl['type'] == _('Net Profit'):
            self.res_bl['type'] = _('Net Profit')
        else:
            self.res_bl['type'] = _('Net Loss')
            
        pl_dict  = {
            'code': '',
            'name': '',
            'type': '',
            'level': False,
            'balance': False,
        }
        for typ in types:
            #print "types---------------------------------------->>", types
            accounts_temp = []
            
#            for account2 in accounts2:
#                if (account2.user_type.report_type) and (account2.user_type.report_type == typ):
#                    account2.name,"+++++++++++++",account2.balance
            
            for account in accounts:
                if (account.user_type.report_type) and (account.user_type.report_type == typ):
                    account_dict = {
                        'id': account.id,
                        'code': account.code,
                        'name': account.name,
                        'type': account.type,
                        'level': account.level,
                        'balance': account.balance,
                        'balance2': 99999999,
                    }
                    #print "ACC=========",account_dict
                    ######################################
                    for account2 in accounts2:
                        if account2.id == account.id:
                            account_dict = {
                            'id': account.id,
                            'code': account.code,
                            'name': account.name,
                            'type': account.type,
                            'level': account.level,
                            'balance': account.balance,
                            'balance2': account2.balance,
                        }
                    #######################################
                    
                    currency = account.currency_id and account.currency_id or account.company_id.currency_id
                    if typ == 'liability' and account.type <> 'view' and (account.debit <> account.credit):
                        self.result_sum_dr += account.balance
                        self.result_sum_dr_currency += account.balance
                    if typ == 'asset' and account.type <> 'view' and (account.debit <> account.credit):
                        self.result_sum_cr += account.balance
                    
                    if data['form']['display_account'] == 'bal_movement':
                        if (not currency_pool.is_zero(self.cr, self.uid, currency, account.credit)) or (not currency_pool.is_zero(self.cr, self.uid, currency, account.debit)) or (not currency_pool.is_zero(self.cr, self.uid, currency, account.balance)):
                            accounts_temp.append(account_dict)
                    elif data['form']['display_account'] == 'bal_solde':
                        if not currency_pool.is_zero(self.cr, self.uid, currency, account.balance):
                            accounts_temp.append(account_dict)
                    else:
                        #print "DDDDDDDDDDDDDDDDDDDDD"
                        accounts_temp.append(account_dict)
                    if account.id == data['form']['reserve_account_id']:
                        #print "CCCCCCCCCCCCCCCC", account.name
                        pl_dict['level'] = account['level'] + 1
                        accounts_temp.append(pl_dict)
           
            self.result[typ] = accounts_temp
            cal_list[typ]=self.result[typ]
        
        #print "cal_list----------------------------------------", cal_list
        if cal_list:
            temp = {}
            for i in range(0,max(len(cal_list['liability']),len(cal_list['asset']))):
                if i < len(cal_list['liability']) and i < len(cal_list['asset']):
                    temp={
                          'code': cal_list['liability'][i]['code'],
                          'name': cal_list['liability'][i]['name'],
                          'type': cal_list['liability'][i]['type'],
                          'level': cal_list['liability'][i]['level'],
                          'balance':cal_list['liability'][i]['balance'],
                          'code1': cal_list['asset'][i]['code'],
                          'name1': cal_list['asset'][i]['name'],
                          'type1': cal_list['asset'][i]['type'],
                          'level1': cal_list['asset'][i]['level'],
                          'balance1':cal_list['asset'][i]['balance'],
                          }
                    self.result_temp.append(temp)
                else:
                    if i < len(cal_list['asset']):
                        temp={
                              'code': '',
                              'name': '',
                              'type': '',
                              'level': False,
                              'balance':False,
                              'code1': cal_list['asset'][i]['code'],
                              'name1': cal_list['asset'][i]['name'],
                              'type1': cal_list['asset'][i]['type'],
                              'level1': cal_list['asset'][i]['level'],
                              'balance1':cal_list['asset'][i]['balance'],
                          }
                        self.result_temp.append(temp)
                    if  i < len(cal_list['liability']):
                        temp={
                              'code': cal_list['liability'][i]['code'],
                              'name': cal_list['liability'][i]['name'],
                              'type': cal_list['liability'][i]['type'],
                              'level': cal_list['liability'][i]['level'],
                              'balance':cal_list['liability'][i]['balance'],
                              'code1': '',
                              'name1': '',
                              'type1': '',
                              'level1': False,
                              'balance1':False,
                          }
                        self.result_temp.append(temp)
        #########Get Date###########
        result_initial_date = datetime.datetime.strptime(period.date_stop,"%Y-%m-%d").strftime("%Y-%m-%d")
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", result_initial_date
        
        result_initial_date = dateutil.parser.parse(result_initial_date)
        result_initial_date = result_initial_date.strftime('%d-%b-%y')
        result_date = {
                  'result_select_date_hdr' : result_select_date_hdr,
                  'result_select_date'     : result_select_date,
                  'result_initial_date'    : result_initial_date
                  }
        return result_date

    def get_lines(self):
        #print "AAAAAAAAAAAAAAAAA"
        return self.result_temp

    def get_lines_another(self, group):
        #print "self.result.get(group, [])------------------------->>", self.result.get(group, [])
        return self.result.get(group, [])
    
    def get_lines_another_total(self, group):
        dummy=self.result.get(group, [])
        #print "dummyyyyyyyyyyyyyyyyyy", dummy
        total=0.00
        for x in dummy:
            if x['type']!='view':
                total += x['balance']
                #print "xxxxxxx",x['balance'],"=======",abs(x['balance']),'=========',total
        #print "eeeeeeeeeeeeeeeeeeee",total
        return abs(total)
    
    def _sum_currency_amount_account(self, balance, data):
        rate = data['form']['rate_opt']
        #=======================================================================
        # # 1 = latest rate, 0 = average
        # pilihan = 1 
        # if pilihan == 1:
        #    qry= '''select b.rate as rate from res_currency a
        #            left join res_currency_rate b on a.id = b.currency_id and b.id = (select max(id) from res_currency_rate c where c.currency_id=b.currency_id) 
        #            where a.name = 'IDR' '''
        # else:
        #    qry= '''select avg(b.rate) as rate from res_currency a
        #            left join res_currency_rate b on a.id = b.currency_id
        #            where a.name = 'IDR' group by a.name'''
        #    
        # self.cr.execute(qry)
        # sum_currency = self.cr.fetchone()[0] or 0.0
        # #print "yyyy",sum_currency
        #=======================================================================
        #print "*******BAL",balance
        balance= self.digit(balance,9)
        #print "Amount------------>",balance,'--',type(balance),'---',type(rate)
        total = rate*balance*1000000000
        #print "TOTAL______________>",total
        return total

#report_sxw.report_sxw('report.ad.account.balancesheet.currency', 'account.account',
#    'addons/ad_account_optimization/report/account_balance_sheet_currency.rml',parser=report_balancesheet_horizontal_new,
#    header='internal landscape')

report_sxw.report_sxw('report.ad.account.balancesheet.new', 'account.account',
    'addons/ad_account_optimization/report/account_balance_sheet_new.mako',parser=report_balancesheet_horizontal_new,
    header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
