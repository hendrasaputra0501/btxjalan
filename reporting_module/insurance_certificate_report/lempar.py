from datetime import datetime
from report import report_sxw
from osv import osv
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale

class insc_lempar(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        print "Context",context
        super(insc_lempar, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr'            : cr,
            'uid'           : uid,
            'convert'       : self.convert,
            'get_address'   : self.get_address,
            'call_num2word': self._call_num2word,
        })  
          
    def get_address(self, partner_obj):
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

    def convert(self, val):
        return self.num2word.amount_to_text(val, 'id', 'idr')

    def _call_num2word(self,amount_total,cur):
        amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8') 
        return amt_id
        
report_sxw.report_sxw('report.insc.mako.rept', 'insurance.polis', 'reporting_module/insurance_certificate_report/insurance.mako', parser=insc_lempar, header=False)
report_sxw.report_sxw('report.insc2.mako.rept', 'insurance.polis', 'reporting_module/insurance_certificate_report/insurance2.mako', parser=insc_lempar, header=False)
