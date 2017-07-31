import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class partner_balance_detail(osv.osv_memory):
	_name = "partner.balance.detail"
	_columns = {
			"invoice_type" : fields.selection([
				('out_invoice','Customer Invoice'),
				('in_invoice','Supplier Invoice'),
				('out_refund','Customer Refund'),
				('in_refund','Supplier Refund'),
				],"Invoice Type",required=True),
			"start_date" : fields.date('Start Date', required=True),
			"end_date" : fields.date('End Date', required=True),
	}
	_defaults = {
		"invoice_type" : lambda self, cr, uid, context:context.get('invoice_type','out_invoice'),
	}

	def print_report(self, cr, uid, ids, context={}):
		data = self.read(cr, uid, ids)[0]
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'partner.balance.detail',
			 'form': data,
			}
		if data['invoice_type']=='out_invoice':
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'ar.sales.detail',
					'report_type': 'webkit',
					'datas': datas,
					}
		elif data['invoice_type']=='in_invoice':
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'ap.purchase.detail',
					'report_type': 'webkit',
					'datas': datas,
					}