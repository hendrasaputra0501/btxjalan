import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _

class container_booking_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(container_booking_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
        })
           
report_sxw.report_sxw('report.container.booking.form', 'container.booking', 'ad_container_booking/report/container_booking_form.mako', parser=container_booking_parser,header=False) 