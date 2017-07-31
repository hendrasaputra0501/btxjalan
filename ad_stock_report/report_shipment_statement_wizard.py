from openerp.osv import fields,osv
import time
import datetime

class shipment_statement_wizard(osv.osv_memory):
	_name = "shipment.statement.wizard"
	_columns = {
		#"date_from"	: fields.datetime("Date From",required=False),
		#"date_to"		: fields.datetime("Date To",required=False),
		"date_from"		: fields.date("Date From",required=False),
		"date_to"		: fields.date("Date To",required=False),
		"sale_type"     : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"output_type"	: fields.selection([('xls',"Excel (*.xls)")],"Output Type"),
		"report_type"	: fields.selection([('shipment','Shipment Statement'),('otif','OTIF')],"Report Type"),
	}

	_defaults = {
		"date_from":lambda self,cr,uid,context:datetime.date.today().strftime("2015-01-01 00:00:00"),
		# "date_from":lambda self,cr,uid,context:time.strftime("%Y-%m-%d"),
		"date_to":lambda self,cr,uid,context:datetime.date.today().strftime("2015-01-31 23:59:59"),
		#'sale_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',1)],context=None),
		"output_type":'xls',
		"report_type":'shipment'
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model':'shipment.statement.wizard',
			'date_from': wizard.date_from,
			'date_to': wizard.date_to,
			'sale_type':wizard.sale_type,
			'report_type':wizard.report_type
			# 'location_exception':[le.id for le in wizard.location_exception],
			# 'location_force':[lf.id for lf in wizard.location_force],
			}
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'shipment.statement.xls',
			'report_type': 'webkit',
			'datas': datas,
 			}
