import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _

class packing_list_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(packing_list_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
        })
try:           
	report_sxw.report_sxw('report.packing.list.form', 'stock.picking', 'ad_picking_report/packing_list/packing_list_form.mako', parser=packing_list_parser,header=False) 
except:
	pass