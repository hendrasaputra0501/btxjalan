import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class invoice_sample_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(invoice_sample_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'call_num2word' :self._call_num2word,
        })

    def _call_num2word(self,amount_total,cur):
        amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
        return amt_id
report_sxw.report_sxw('report.invoice.sample.form', 'invoice.sample', 'ad_invoice_sample/report/invoice_sample_report.mako', parser=invoice_sample_parser,header=False)