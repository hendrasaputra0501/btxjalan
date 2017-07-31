import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale

class print_proforma_invoice_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(print_proforma_invoice_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_invline_totprice':self._get_invline_totprice,
		   # 'get_totinvline':self._get_totinvline,
			'call_num2word':self._call_num2word,
			'get_address':self.get_address,			
		})

	def _get_invline_totprice(self,invline_obj):
		sumqty=0
		sumtotprice=0
		for a in invline_obj:
			sumqty=sumqty+a.quantity
			sumtotprice=sumtotprice+(a.quantity*a.price_unit)
		sumlocqty=sumqty
		sumloctotprice=sumtotprice
		return sumlocqty,sumloctotprice,sumtotprice

	def _call_num2word(self,amount_total,cur):
		amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8') 
		return amt_id

	def get_address(self, partner_obj):
		if partner_obj:
			partner_address = ''
			partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
			partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
			partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
			partner_address += partner_obj.city and partner_obj.city +' ' or ''
			partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
			partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''
			
			return  partner_address.replace('\n','<br />')
		else:
			return False
		
report_sxw.report_sxw('report.print.proforma.invoice.form', 'proforma.invoice', 'reporting_module/proforma_invoice/print_proforma_invoice_form.mako', parser=print_proforma_invoice_parser,header=False)