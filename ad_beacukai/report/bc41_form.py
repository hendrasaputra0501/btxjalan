# import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from datetime import datetime
    
class bc41_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(bc41_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
        })

# report_sxw.report_sxw('report.bc41.form', 'beacukai', 'ad_beacukai/report/bc41_form.mako', parser=bc41_parser,header='false') 