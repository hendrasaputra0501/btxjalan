import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _

class surat_jalan_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(surat_jalan_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
        })
           
report_sxw.report_sxw('report.surat.jalan.form', 'stock.picking', 'ad_picking_report/surat_jalan/surat_jalan_form.mako', parser=surat_jalan_parser,header=False) 