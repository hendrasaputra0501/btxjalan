from openerp.osv import fields,osv
from datetime import datetime

class delay_shipment_wizard(osv.osv_memory):
	_name="delay.shipment.wizard"
	_columns={
		"start_date":fields.date("Start Date",required=True),
		"end_date":fields.date("End Date",required=True),
		'report_type':fields.selection([('xls','Excel'),('pdf','PDF')],'Report Type',required=True),
		'sale_type':fields.selection([('export','Export'),('local','Local')],'Shipment Type',required=True)
		}
	_defaults={
		"start_date":lambda *a:datetime.now().strftime("%Y-01-01"),
		"end_date":lambda *a:datetime.now().strftime("%Y-%m-%d"),
		'report_type':lambda *a :'xls',
		'sale_type': lambda *a : 'export'
		}

	def calculate_delay(self,cr,uid,ids,context=None):
		if not context:
			context={}
		form_data=self.read(cr, uid, ids)[0]

		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'delay.shipment.wizard',
			'form': form_data,
			}
		if form_data['report_type']=='pdf': 
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'delay.shipment.report',
				'report_type': 'webkit',
				'datas': datas,
				}
		else:
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'xls.delay.shipment.report',
				'report_type': 'webkit',
				'datas': datas,
				}


