from openerp.osv import fields, osv

from tools.translate import _

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _description = 'Inheritance of res_partner'
    _columns = {
        'npwp' : fields.char("NPWP",size= 20),
        'partner_type'	:fields.selection([('local','Local'),('overseas','Overseas')],"Partner Type",required=True),
			
    }
    _defaults = {
        'npwp': lambda *a: '/',
        'partner_type': lambda *a: 'overseas',
    }
