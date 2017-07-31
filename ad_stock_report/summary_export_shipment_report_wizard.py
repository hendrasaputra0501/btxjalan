from openerp.osv import fields,osv
import time
import datetime

class sum_expshipment_wizard(osv.osv_memory):
	_name = "sum.expshipment.wizard"
	_columns = {
		"as_on"	: fields.date("As On",required=False),
		"sale_type"     : fields.selection([('export','Export'),('local','Local')],"Sale Type",required=True),
		"output_type"	: fields.selection([('xls',"Excel (*.xls)")],"Output Type"),
	}

	_defaults = {
		"as_on":lambda self,cr,uid,context:time.strftime("%Y-%m-%d"),
		"output_type":'xls'
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model':'sum.expshipment.wizard',
			'as_on': wizard.as_on,
			'sale_type':wizard.sale_type,
			# 'location_exception':[le.id for le in wizard.location_exception],
			# 'location_force':[lf.id for lf in wizard.location_force],
			}
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'sum.expshipment.xls',
			'report_type': 'webkit',
			'datas': datas,
			}
