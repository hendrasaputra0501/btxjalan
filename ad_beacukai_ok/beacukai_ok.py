'''
Created on 9 Jan 2015

@author: okkype
'''

from openerp.osv import osv, fields

class beacukai(osv.Model):
    _name = 'beacukai'
    _inherit = 'beacukai'
    _columns = {
                'document_type' : fields.selection([
                                                    ('23', "BC 2.3"),
                                                    ('25','BC 2.5'),
                                                    ('261','BC 2.61'),
                                                    ('262','BC 2.62'),
                                                    ('27_in', "BC 2.7 Masukan"),
                                                    ('27_out', "BC 2.7 Keluaran"),
                                                    ('30', "BC 3.0"),
                                                    ('40', "BC 4.0"),
                                                    ('41','BC 4.1'),
                                                    ], "Document Type", required=True),
                }
    
    def onchange_src_partner(self, cr, uid, ids, partner_id):
        res = {
               'source_address' : '',
               'source_npwp' : '',
               }
        if partner_id:
          sps = self.pool.get('res.partner').browse(cr, uid, partner_id)
          res = {
                 'source_address' : sps.street or '',
                 'source_npwp' : sps.npwp or '',
                 }
        return {'value' : res}
    
    def onchange_dst_partner(self, cr, uid, ids, partner_id):
        # res = {}
        res = {
               'dest_address' : '',
               'dest_npwp' : '',
               }
        if partner_id:
            sps = self.pool.get('res.partner').browse(cr, uid, partner_id)
            res = {
                   'dest_address' : sps.street or '',
                   'dest_npwp' : sps.npwp or '',
                   }

        return {'value' : res}
    
    def onchange_info_partner(self, cr, uid, ids, partner_id):
        
        res = {
               'info_address' : '',
               'info_npwp' : '',
               }
        if partner_id:
          sps = self.pool.get('res.partner').browse(cr, uid, partner_id)
          res = {
                 'info_address' : sps.street or '',
                 'info_npwp' : sps.npwp or '',
                 }
        return {'value' : res}
    
    
    '''
    def print_bc(self, cr, uid, ids, context=None):
        data = {}
        data['form'] = {}
        data['ids'] = context.get('active_ids',[])
        data['form']['data'] = self.read(cr, uid, ids)[0]
         
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'form.jamsostek',
                'datas': data,
                'nodestroy':True
        }
    '''
