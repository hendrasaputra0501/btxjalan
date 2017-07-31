import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class bill_passing_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(bill_passing_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
		})

 
report_sxw.report_sxw('report.bill.passing.report.form', 'account.bill.passing', 'ad_sales_agent_bitratex/account_bill_passing_report.mako', parser=bill_passing_parser,header=False) 