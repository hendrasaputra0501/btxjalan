import re
import time
import xlwt
from report import report_sxw
from report_xls.report_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
import netsvc
 
class bc_xls_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		if context is None:
			context = {}
		super(bc_xls_report_parser, self).__init__(cr, uid, name, context=context)
		# if context.get('active_model',False) == 'beacukai.document.line.in':
		# 	report_name = 'Laporan Penerimaan Barang'
		# 	shipment_type = 'in'
		# else:
		# 	report_name = 'Laporan Pengeluaran Barang'
		# 	shipment_type = 'out'
		self.localcontext.update({
			'time': time,
			# 'report_name': report_name,
			# 'shipment_type': shipment_type,

		})


class bc_xls_report(report_xls):
	def generate_report(self, parser, xls_style, data, objects, wb):
		# Sheet Header
		ws = wb.add_sheet("Header")
		ws.panes_frozen = False
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		ws.fit_width_to_pages = 1
		ws.preview_magn = 90
		ws.normal_magn = 90
		ws.print_scaling = 100
		ws.page_preview = True
		# ws.set_fit_width_to_pages(1)
		row_pos = 0

bc_xls_report('report.beacukai.xls.report','report.stock.move.pabean', parser=bc_xls_report_parser, header=False)