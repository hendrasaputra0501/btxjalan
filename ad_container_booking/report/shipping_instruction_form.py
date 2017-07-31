import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _

class shipping_instruction_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(shipping_instruction_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_label':self.get_label,
		})

	def get_label(self,obj):
		lc_objs = []
		if obj.picking_ids and obj.picking_ids[0].sale_id and obj.picking_ids[0].sale_id.payment_method=='lc':
			for picking in obj.picking_ids:
				if picking.lc_ids:
					for lc in picking.lc_ids:
						if lc not in lc_objs and lc.state not in ['canceled','nonactive','closed']:
							lc_objs.append(lc)
		label_dict = {}
		for lc in lc_objs:
			label_on_lc = eval(lc.label_print)
			if label_on_lc:
				for k,v in label_on_lc.items():
					if k not in label_dict:
						label_dict.update({k:v})
		return label_dict
		   
report_sxw.report_sxw('report.shipping.instruction.form', 'container.booking', 'ad_container_booking/report/shipping_instruction_form.mako', parser=shipping_instruction_parser,header=False) 