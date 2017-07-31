from openerp.osv import fields,osv
import datetime

class pending_shipment_register_wizard(osv.osv_memory):
	_name ="pending.shipment.register.wizard"
	_columns={
		"date_start"	:	fields.datetime("Start Range", required=False),
		"date_stop"		:	fields.datetime("Stop Range", required=False),
		"output_type"	: 	fields.selection([('pdf',"Pdf (*.pdf)")],"Output Type"),
		"purchase_type" :	fields.selection([('import','Import'),('local','Local'),('all','All')],"Purchase Type",required=True),
		# "grouping"		: 	fields.selection([('department',"Department Wise")],"Grouping",required=True),
	}
	_defaults = {
		"date_start":lambda self,cr,uid,context:datetime.date.today().strftime("2015-02-01 00:00:00"),
		# "date_stop":lambda self,cr,uid,context:datetime.date.today().strftime("%Y-%m-%d 23:59:59"),
		"date_stop":lambda self,cr,uid,context:datetime.date.today().strftime("2015-02-28 23:59:59"),
		"output_type":'pdf',
		"purchase_type":lambda *p:'import',
		# "grouping": lambda *a: "department",
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:
			context={}
		form_data=self.read(cr, uid, ids)[0]
		# form=self.read(cr, uid, ids)[0]
		# print "=============",form_data
		datas = {
			'ids': context.get('active_ids',[]),
			'model'	: 'pending.shipment.register.wizard',
			'form': form_data,
			# 'date_start': form.date_start,
			# 'date_stop': form.date_stop,
			}
		print "==============================xwzxwzxwzxwzxwzxwzxwzxwzxwz================="
		if form_data['output_type']=='pdf':
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'pending.shipment.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}
		else:
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'xls.pending.shipment.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}

		
