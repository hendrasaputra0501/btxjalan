import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class surat_kuasa_parser(report_sxw.rml_parse):
	"""docstring for surat_kuasa_parser"""
	def __init__(self, cr, uid, name, context):
		super(surat_kuasa_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'get_lines_grouped' : self._get_lines_grouped,
			})

	def _get_lines_grouped(self, line_ids):
		line_grouped = {}
		for line in line_ids:
			key = (line.partner_id and str(line.partner_id.id) or 'False', line.partner_id and str(line.partner_id.partner_code) or 'False', line.partner_bank_id and str(line.partner_bank_id.id) or 'False', line.move_line_id and 'True' or str(line.id))
			if key not in line_grouped:
				line_grouped.update({key:{
					'partner_name' : line.partner_id and line.partner_id.name or '',
					'bank_name' : line.partner_bank_id and line.partner_bank_id.bank_name or '',
					'acc_number' : line.partner_bank_id and line.partner_bank_id.acc_number or '',
					'owner_name' : line.partner_bank_id and line.partner_bank_id.owner_name or '',
					'amount' : 0.0,
					'name' : '',
					'ref' : '',
					}})
			line_grouped[key]['amount']+=line.amount
			line_grouped[key]['name']+=(line.name and str(line.name)+"\n" or "")
			line_grouped[key]['ref']+=(line.ref and str(line.ref)+"\n" or "")

		return line_grouped

report_sxw.report_sxw('report.surat.kuasa', 'account.bank.statement', 'ad_vourcher_payment_rate/report/surat_kuasa.mako', parser=surat_kuasa_parser,header=False)