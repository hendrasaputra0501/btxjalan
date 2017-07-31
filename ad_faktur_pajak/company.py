import netsvc
from osv import fields, osv

class company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'npwp':fields.char('NPWP',size=64),
        'tax_base_currency':fields.many2one('res.currency',"Currency Tax Reference",required=True),
        }

    _defaults = {
    	'tax_base_currency':lambda self,cr,uid,context:self.pool.get('res.currency').search(cr,uid,[('name','=','IDR')])[0]
    }
company()