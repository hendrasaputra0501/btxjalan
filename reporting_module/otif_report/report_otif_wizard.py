from openerp.osv import fields,osv
import time
import datetime

class _otif_wizard(osv.osv_memory):
	_name = "otif.wizard"
	_columns ={
		"date_from"	: fields.date("Date From", required=False),
		"date_to"	: fields.date("Date To", required=False),
		"sale_type"	: fields.selection([('export','Export'),('local','Local')], "Sale Type",required=True),
		"output_type"	: fields.selection([('xls','Excel'),('pdf','PDF')], "Output Type", required=True),


	}
	_defaults ={
		"date_from" :lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-01 00:00:00"),
		"date_to"	:lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-30 00:00:00"),
		"sale_type" : 'export',
		"output_type"	: 'xls',
	}


	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard= self.browse(cr,uid,ids,context)[0]
		datas ={
			'ids'	: context.get('active_ids',[]),
			'model'	: 'otif.wizard',
			'date_from'	:	wizard.date_from,
			'date_to'	:	wizard.date_to,
			'sale_type'	:	wizard.sale_type,
			'output_type'	:	wizard.output_type,
			}
		return{
			'type'	:	'ir.actions.report.xml',
			'report_name' 	:	'otif.xls',
			'report_type'	:	'webkit',
			'datas'			:	datas,
			}
