import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class check_preview_parser(report_sxw.rml_parse):
	"""docstring for check_preview_parser"""
	def __init__(self, cr, uid, name, context):
		super(check_preview_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time':time,
			'get_lines_grouped' : self._get_lines_grouped,
			'get_user_name' : self._get_user_name,
			})

	def _get_user_name(self):
		uid = self.uid
		user = self.pool.get('res.users').browse(self.cr, uid, uid)
		return user.name.upper()

	def _get_lines_grouped(self, line_ids):
		line_grouped = {}
		for line in line_ids:
			key = line.partner_id or False
			if key not in line_grouped:
				line_grouped.update({key:{
					'partner_name' : line.partner_id and line.partner_id.name or '',
					'bank_name' : line.partner_bank_id and line.partner_bank_id.bank_name or '',
					'acc_number' : line.partner_bank_id and line.partner_bank_id.acc_number or '',
					'owner_name' : line.partner_bank_id and line.partner_bank_id.owner_name or '',
					'amount_to_pay' : 0.0,
					'amount_balance' : 0.0,
					'name' : '',
					'ref' : '',
					'lines' : [],
					}})
			line_grouped[key]['amount_balance']+=line.amount
			line_grouped[key]['amount_to_pay']+=line.amount
			line_grouped[key]['name']+=(line.name and str(line.name)+"\n" or "")
			line_grouped[key]['ref']+=(line.ref and str(line.ref)+"\n" or "")
			line_grouped[key]['lines'].append(line)
		return line_grouped

report_sxw.report_sxw('report.check.preview', 'account.bank.statement', 'ad_vourcher_payment_rate/report/check_preview.mako', parser=check_preview_parser,header=False)