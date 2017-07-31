import time
from tools.translate import _
import tools
from osv import fields, osv

class report_priorities(osv.osv_memory):
    _name = "report.priorities.wizard"
    _columns = {
            "as_on" : fields.date('As On',required=True)
    } 
    
    _defaults ={
                'as_on' : lambda *a:time.strftime("%Y-%m-%d"),
                }
    def compute_report(self, cr, uid, ids, context={}):
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'report.priorities.wizard',
             'form': self.read(cr, uid, ids)[0],
                 }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'priorities.report',
                'report_type': 'webkit',
                'datas': datas,
                }
report_priorities()