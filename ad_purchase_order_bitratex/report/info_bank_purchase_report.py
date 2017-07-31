import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from datetime import datetime
from ad_num2word_id import num2word

class info_bank_purchase_report_parser(report_sxw.rml_parse):    
    def __init__(self, cr, uid, name, context=None):
        super(info_bank_purchase_report_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
        'time':time,
        'xdate':self._xdate,
        'xdatepmonth':self._xdatepmonth,
        'xdatepday':self._xdatepday,
        'call_num2word':self._call_num2word,
        'get_address':self._get_address,
        'get_print_user_time':self._get_print_user_time,
        }),
    def _call_num2word(self,amount_total,cur):
        amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
        return amt_id

    def _get_address(self, partner_obj):
        if partner_obj:
            partner_address = ''
            partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
            partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
            partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
            partner_address += partner_obj.city and partner_obj.city +' ' or ''
            partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
            partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''

            return  partner_address.replace('\n','<br />')
        else:
            return False

    def _get_print_user_time(self,context=None):
        cr = self.cr
        uid = self.uid
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
        tlocal = time.localtime()
        slocal = str(tlocal.tm_year) + '-' + str(tlocal.tm_mon) + '-' + str(tlocal.tm_mday) + ' ' + str(tlocal.tm_hour) + ':' + str(tlocal.tm_min) 
        print_user_time = 'Printed By ' + curr_user.partner_id.name + ' On ' + datetime.strptime(slocal,'%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M')
        return print_user_time

    def _xdate(self,x):
        try:
            x1 = x[:10]
        except:
            x1 = ''

        try:
            y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            y = x1
        return y

    def _xdatepday(self,x):
        try:
            x1 = x[:10]
        except:
            x1 = ''

        try:

            y = datetime.strptime(x1,'%Y-%m-%d').strftime('%A, %d/%m/%Y')
        except:
            y = x
        return y

    def _xdatepmonth(self,x):
        try:
            x1 = x[:10]
        except:
            x1 = ''

        try:
            y = datetime.strptime(x1,'%Y-%m-%d').strftime('%B %d, %Y')
        except:
            y = x
        return y

report_sxw.report_sxw('report.info.bank.purchase.form','purchase.order','ad_purchase_order_bitratex/report/info_bank_purchase_report.mako',parser=info_bank_purchase_report_parser,header=False)
