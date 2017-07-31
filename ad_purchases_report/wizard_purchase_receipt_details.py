from openerp.osv import fields,osv
import datetime

class wizard_purchase_receipt_details(osv.osv_memory):
	_name="wizard.purchase.receipt.details"
	_columns={
		"date_start" :  fields.date("Date From", required=False),
		"date_stop"	: fields.date("Date To", required=False),
		"purchase_type" : fields.selection([('import','Import'),('local','Local'),('all','All')],"Purchase Type",required=True),
		# 'output_type':fields.selection([('xls','Excel'),('pdf','PDF')],'Output Type',required=True),
		"goods_type" : fields.selection([('packing','Packing'),('stores','Stores'),('raw','Raw Material')], "Goods Type"),
	}
	_defaults={
		"date_start" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-01"),
		"date_stop" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-30"),
		# "output_type" :'pdf',
		"purchase_type" :lambda *p:'local',
		# "goods_type":lambda *p:'packing',
	}

	def print_report(self,cr,uid,ids,context=None):
		if not context:
			context={}
		form_data=self.read(cr,uid,ids)[0]
		datas={
			'ids': context.get('active_ids',[]),
			'model' :'wizard.purchase.receipt.details',
			'form' :form_data,
		}

		# if form_data['output_type']=='pdf':
		# 	return{
		# 	'type' :'ir.actions.report.xml',
		# 	'report_name' :'pending.purchase.order.report',
		# 	'report_type' :'webkit',
		# 	'datas' :datas,
		# 	}
		# else:
		return{
			'type' :'ir.actions.report.xml',
			'report_name' :'purchase.receipt_details',
			'report_type' :'xls',
			'datas' :datas,
			}
