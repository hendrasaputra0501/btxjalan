import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class certificate_fumigation_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(certificate_fumigation_report_parser, self).__init__(cr, uid, name, context=context)		
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_label':self._get_label,
			'get_lc_number':self._get_lc_number,
		})

	def _get_label(self,inv_obj):
		lc_objs = []
		if inv_obj.sale_ids and inv_obj.picking_ids and (inv_obj.sale_ids[0].payment_method=='lc' or inv_obj.sale_ids[0].payment_method=='tt') :
			for picking in inv_obj.picking_ids:
				if picking.lc_ids:
					for lc in picking.lc_ids:
						# if lc not in lc_objs and lc.state not in ['canceled','nonactive','closed']:
							lc_objs.append(lc)
		label_dict = {}
		for lc in lc_objs:
			label_on_lc = eval(lc.label_print)
			if label_on_lc:
				for k,v in label_on_lc.items():
					if k not in label_dict:
						label_dict.update({k:v})
		if not lc_objs and not label_dict:
			label_dict = (eval(inv_obj.label_print)).copy()
		return label_dict

	def _get_lc_number(self, inv_obj):
		lc_ids = []
		for picking in inv_obj.picking_ids:
			for lc in picking.lc_ids:
				if lc.lc_type=='in' and lc not in lc_ids:
					lc_ids.append(lc)
		
		arr_temp_lc = []
		if lc_ids:
			for lc in lc_ids:
				arr_temp_lc.append(lc.lc_number)

		return arr_temp_lc and '<br/>'.join(arr_temp_lc) or ''

report_sxw.report_sxw('report.certificate.fumigation.form', 'declaration.form', 'addons/ad_shipment_certificate/report/certificate_fumigation_form.mako', parser=certificate_fumigation_report_parser,header=True)