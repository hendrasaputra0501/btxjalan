import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale

class bill_passing_advise_of_other_emkl_cost(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(bill_passing_advise_of_other_emkl_cost, self).__init__(cr, uid, name, context=context)		
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_lc_number' : self._get_lc_number,
			'get_container_number' : self._get_container_number,
		})

	def _get_lc_number(self, inv):
		lc_number = []
		if inv:
			if inv.picking_ids:
				for picking in inv.picking_ids:
					for lc in picking.lc_ids:
						if lc.lc_number not in lc_number:
							lc_number.append(lc.lc_number)
		lc_num = ""
		for number in lc_number:
			lc_num += number + ";"

		return lc_num

	def _get_container_number(self, inv):
		container = []
		if inv:
			if inv.picking_ids:
				for picking in inv.picking_ids:
					if picking.container_number not in container:
						container.append(picking.container_number)

		cont_num = ""
		for number in container:
			cont_num += number + ";"

		return cont_num
		
report_sxw.report_sxw('report.bpa.report', 'ext.transaksi', 'reporting_module/bpa_ext_trans/bill_passing_advise_of_other_emkl_cost.mako', parser=bill_passing_advise_of_other_emkl_cost,header=False)