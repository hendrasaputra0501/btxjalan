from osv import osv, fields
from openerp.tools.translate import _

class nomor_faktur_pajak(osv.osv):
    
    _name = 'nomor.faktur.pajak'
    _description = 'Nomor faktur Pajak'

    def _nomor_faktur(self, cr, uid, ids, nomorfaktur, arg, context=None):
        res = {}
        for nomor in self.browse(cr, uid, ids, context):    
            res[nomor.id] = "%s.%s.%s" % (nomor.nomor_perusahaan, nomor.tahun_penerbit, nomor.nomor_urut)
        return res

    def _get_invoice_related(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        res = []
        for inv in self.pool.get('account.invoice').browse(cr, uid, ids, context=context):
            if inv.nomor_faktur_id and inv.nomor_faktur_id.id not in res:
                res.append(inv.nomor_faktur_id.id)
        return res

    def _get_state(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for nomor in self.browse(cr, uid, ids, context):    
            res[nomor.id] = '0'
            if nomor.account_invoice_ids:
                res[nomor.id] = '1'
        return res
    
    _columns = {
        'nomor_perusahaan' : fields.char('Nomor Perusahaan', size=3),
        'tahun_penerbit': fields.char('Tahun Penerbit', size=2),
        'nomor_urut': fields.char('Nomor Urut', size=8),
        'name': fields.function(_nomor_faktur, type='char', string="Nomor Faktur", store=True),
        'status': fields.function(_get_state,method=True,type='selection',selection=[('1','Used'),('0','Not Used')],string='Status',
            store={
                'account.invoice':(_get_invoice_related, ['nomor_faktur_id'], 10),
            }),
        # 'status': fields.selection([('1','Used'),('0','Not Used')],'Status'),
        'account_invoice_ids': fields.one2many('account.invoice', 'nomor_faktur_id', string='Account Invoice'),
        'active': fields.boolean("Active"),
    }
    
    _defaults = {
        'status': '0',
        'active': True,
    }
nomor_faktur_pajak()


class generate_faktur_pajak(osv.osv_memory):
    _name = 'generate.faktur.pajak'
    
    def generate_faktur(self, cr, uid, ids, context=None):
        if not context: context={}
        wizard = self.browse(cr, uid, ids[0], context)
        while (wizard.nomor_awal <= wizard.nomor_akhir):
            nomor = ''
            if (len(str(wizard.nomor_awal)) == 8):
                nomor = str(wizard.nomor_awal)
            elif (len(str(wizard.nomor_awal)) == 7):
                nomor = '0'+str(wizard.nomor_awal)
            elif (len(str(wizard.nomor_awal)) == 6):
                nomor = '00'+str(wizard.nomor_awal)
            value = {
                'nomor_perusahaan': wizard.nomor_perusahaan,
                'tahun_penerbit': wizard.tahun,
                'nomor_urut': nomor,
                'status': '0',
            }
            self.pool.get('nomor.faktur.pajak').create(cr,uid,value,context=context)
            wizard.nomor_awal += 1
        return {'type': 'ir.actions.act_window_close'}
    
    def onchange_nomor_faktur(self, cr, uid, ids, akhir, context=None):
        res = {}
        wizard = self.browse(cr, uid, ids[0], context)
        if akhir <= wizard.nomor_awal:
            warning = {
                'title': _('Warning'),
                'message': _('Wrong Format must 15 digit'),
            }
            return {'warning': warning, 'value' : {'nomor_akhir' : False}}
        return res
    
    _columns = {
                'nomor_perusahaan' : fields.char('Nomor Perusahaan', size=3, required=True),
                'nomor_awal' : fields.integer('Nomor Awal', size=8, required=True),
                'nomor_akhir' : fields.integer('Nomor Akhir', size=8, required=True),
                'tahun' : fields.char('Tahun Penerbit', size=2,  required=True),
                }
    
generate_faktur_pajak()