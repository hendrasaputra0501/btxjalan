from openerp.osv import fields,osv
import datetime


class waste_transfer_summary_wizard(osv.osv_memory):
	_name="waste.transfer.summary.wizard"
	_columns={
		"date_start" :  fields.datetime("Date From", required=False),
		"date_stop"	: fields.datetime("Date To", required=False),
		'output_type' :fields.selection([('xls','Excel'),('pdf','PDF')],'Output Type',required=True),
		"location_force"            : fields.many2many("stock.location","location_waste_report_force_rel","location_id","wizard_id","Force Location"),
		"goods_type"  : fields.selection([('finish_others','Finish Goods Other')],"Goods Type"),

	}
	_defaults={
		"date_start" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-01 00:00:00"),
		"date_stop" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-30 00:00:00"),
		"output_type" :'pdf',
		"goods_type":lambda *p:'finish_others',
	}

	def generate_report(self,cr,uid,ids,context=None):
			if not context:
				context={}
			form_data=self.read(cr,uid,ids)[0]
			wizard = self.browse(cr,uid,ids,context)[0]
			datas={
			'ids': context.get('active_ids',[]),
			'model' :'waste.transfer.summary.wizard',
			'location_force':[lf.id for lf in wizard.location_force],
			'form' :form_data,
			}

			if form_data['output_type']=='pdf':
				return{
				'type' :'ir.actions.report.xml',
				'report_name' :'waste.transfer.sum.report',
				'report_type' :'webkit',
				'datas' :datas,
				}
			else:
				return{
				'type' :'ir.actions.report.xml',
				'report_name' :'xls.waste.transfer.summary',
				'report_type' :'xls',
				'datas' :datas,
				}

