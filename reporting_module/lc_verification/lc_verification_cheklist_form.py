import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word

class lc_verification_cheklist_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(lc_verification_cheklist_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'call_num2word':self._call_num2word,
            
        })

    def _call_num2word(self,amount_total,cur):
        amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8') 
        return amt_id

report_sxw.report_sxw('report.lc.verification.cheklist.form', 'letterofcredit', 'reporting_module/lc_verification/lc_verification_cheklist_form.mako', parser=lc_verification_cheklist_parser,header=False)