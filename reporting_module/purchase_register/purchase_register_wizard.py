from openerp.osv import fields,osv
from datetime import datetime

class purchase_register_wizard(osv.osv_memory):
	_name="purchase.register.wizard"
	_columns={
		"start_date":fields.date("Start Date",required=True),
		"end_date":fields.date("End Date",required=True),
		"as_of_date":fields.date("As Of Date",required=True),
		"purchase_type": fields.selection([('import','Import'),('local','Local'),('all','All')],"Purchase Type",required=True),
		'header_group_by':fields.selection([('vendor_wise','Vendor Wise'),('date_wise','Date Wise')],'Header Group By',required=True),
		'report_type':fields.selection([('xls','Excel'),('pdf','PDF')],'Report Type',required=True),
		'filter_date':fields.selection([('period_of_date','Date'),('as_of','As Of Date')],'Filter Date',required=True),
		'goods_type' : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('asset','Fixed Asset'),('other','Other'),('packing','Packing Material')],'Goods Type',required=True),
		'force_purchase_ids' : fields.many2many("purchase.order","pr_wizard_rel_purchase","wizard_id","purchase_id","Force Purchases",domain=[('state','=','done')]),
		'force_department_ids' : fields.many2many("hr.department","pr_wizard_rel_hr_department","wizard_id","department_id","Force Department"),
		'force_location_ids' : fields.many2many("stock.location","pr_wizard_rel_stock_location","wizard_id","location_id","Force Location"),
		}
	_defaults={
		"purchase_type":lambda *p:'local',
		'filter_date':lambda *f:'period_of_date',
		"start_date":lambda *a:datetime.now().strftime("%Y-%m-01"),
		"end_date":lambda *a:datetime.now().strftime("%Y-%m-%d"),
		"as_of_date":lambda *a:datetime.now().strftime("%Y-%m-%d"),
		'report_type':lambda *a :'xls',
		'goods_type':lambda *g:'stores',
		'header_group_by':lambda *h:'vendor_wise',
		}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:
			context={}
		form_data=self.read(cr, uid, ids)[0]
		form_data_obj = self.browse(cr,uid,ids,context)[0]
		# print "=============",form_data
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'purchase.register.wizard',
			'form': form_data,
			'department_ids': [x.id for x in form_data_obj.force_department_ids],
			'location_ids': [x.id for x in form_data_obj.force_location_ids], 
			}
		if form_data['report_type']=='pdf': 
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'purchase.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}
		else:
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'xls.purchase.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}
