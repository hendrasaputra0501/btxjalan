import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter

class stock_inventory_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(stock_inventory_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			
		})


report_sxw.report_sxw('report.stock.inventory.report', 'stock.inventory', 'reporting_module/stock_inventory/stock_inventory.mako', parser=stock_inventory_parser,header=False) 