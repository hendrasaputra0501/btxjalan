from openerp.osv import osv,fields

class move_tax_source_doc(osv.Model):
	_name="account.move.tax.source"
	_columns = {
		'name': fields.char('Name', size=60, required=True),
		'model': fields.many2one('ir.model', 'Object', required=True),
	}

def _get_tax_source_types(self, cr, uid, context=None):
	cr.execute('select m.model, s.name from account_move_tax_source s, ir_model m WHERE s.model = m.id order by s.name')
	return cr.fetchall()

class account_move_line(osv.Model):
	_inherit = "account.move.line"

	def _get_faktur_pajak_number(self,cr,uid,ids,field_name,args,context=None):
		if not context:
			context={}
		res = {}
		for mvl in self.browse(cr,uid,ids,context):
			# print "################################",mvl.faktur_pajak_source._name, "##",mvl.faktur_pajak_source.name
			if mvl.faktur_pajak_source._name=='ext.transaksi.line':
				res.update({mvl.id : mvl.faktur_pajak_source and mvl.faktur_pajak_source.tax_ext_transaksi_id and mvl.faktur_pajak_source.faktur_pajak and mvl.faktur_pajak_source.faktur_pajak or ''})
			else:
				res.update({mvl.id : mvl.faktur_pajak_source and mvl.faktur_pajak_source.nomor_faktur_id and mvl.faktur_pajak_source.nomor_faktur_id.name or ''})
		return res

	_columns = {
		'ar_ap_tax':fields.boolean("AR/AP Tax?",help="This field indicates that this journal item record comes from splitted AR/AP Tax"),
		"faktur_pajak_source"	: fields.reference('Source Document', required=False, selection=_get_tax_source_types, size=128, help="User can choose the source document on which he wants to create documents"),
		"faktur_pajak_no"		: fields.function(_get_faktur_pajak_number,type="char",size=40,string="Faktur Pajak Number"),
	}