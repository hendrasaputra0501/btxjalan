import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter


class quality_certificate_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(quality_certificate_parser, self).__init__(cr, uid, name, context=context)		
		self.localcontext.update({
			'time': time,
			'get_company' : self._get_company,
			'get_address' :	self._get_address,
		})


	def _get_company(self,context=None):
		self.cr.execute ("select b.name as name \
							from res_company a \
							left join res_partner b on a.partner_id = b.id")

		res = self.cr.fetchone()
		#print ">>>>>>>>>", res[0].encode('utf-8')
		return res[0].encode('utf-8')

	def _get_address(self, partner_obj):
		if partner_obj:
			partner_address = ''
			partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
			partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
			partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
			partner_address += partner_obj.city and partner_obj.city +' ' or ''
			partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
			partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''
			
			return  partner_address.replace('\n','<br />').upper()
		else:
			return False

report_sxw.report_sxw('report.quality.certificate.report', 'uster.form', 'reporting_module/quality_certificate_report/quality_certificate_report.mako', parser=quality_certificate_parser,header=False)