from openerp.osv import fields,osv
import datetime

class pending_purchase_order_wizard(osv.osv_memory):
	_name="pending.purchase.order.wizard"
	_columns={
		"date_start" :  fields.datetime("Date From", required=False),
		"date_stop"	: fields.datetime("Date To", required=False),
		"purchase_type" : fields.selection([('import','Import'),('local','Local'),('all','All')],"Purchase Type",required=True),
		# "output_type" : fields.selection([('pdf','Pdf (*.pdf)')], "Output Type"),
		'output_type':fields.selection([('xls','Excel'),('pdf','PDF')],'Output Type',required=True),
		"goods_type" : fields.selection([('packing','Packing'),('stores','Stores')], "Goods Type"),


	}
	_defaults={
		"date_start" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-01 00:00:00"),
		"date_stop" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-30 00:00:00"),
		"output_type" :'pdf',
		"purchase_type" :lambda *p:'local',
		"goods_type":lambda *p:'packing',
	}

	def generate_report(self,cr,uid,ids,context=None):
			if not context:
				context={}
			form_data=self.read(cr,uid,ids)[0]
			datas={
			'ids': context.get('active_ids',[]),
			'model' :'pending.purchase.order.wizard',
			'form' :form_data,
			}

			if form_data['output_type']=='pdf':
				return{
				'type' :'ir.actions.report.xml',
				'report_name' :'pending.purchase.order.report',
				'report_type' :'webkit',
				'datas' :datas,
				}
			else:
				return{
				'type' :'ir.actions.report.xml',
				'report_name' :'xls.pending.purchase.order.report',
				'report_type' :'xls',
				'datas' :datas,
				}
