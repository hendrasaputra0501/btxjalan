from openerp.osv import fields,osv
from datetime import datetime

class purchase_receipt_register_daily_wizard(osv.osv_memory):
	_name="purchase.receipt.register.daily.wizard"
	_columns={
		"start_date":fields.date("Start Date",required=True),
		"end_date":fields.date("End Date",required=True),
		"as_of_date":fields.date("As Of Date",required=True),
		"purchase_type": fields.selection([('import','Import'),('local','Local'),('all','All')],"Purchase Type",required=True),
		'header_group_by':fields.selection([('vendor_wise','Vendor Wise'),('date_wise','Date Wise')],'Header Group By',required=True),
		'report_type':fields.selection([('xls','Excel'),('pdf','PDF')],'Report Type',required=True),
		'filter_date':fields.selection([('period_of_date','Date'),('as_of','As Of Date')],'Filter Date',required=True),
		'goods_type' : fields.selection([('finish','Finish Goods'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('asset','Fixed Asset'),('other','Other'),('packing','Packing Material')],'Goods Type',required=True),
		'with_invoice_information' : fields.boolean('With Invoices Information'),
		'force_picking_ids' : fields.many2many("stock.picking","prr_daily_wizard_rel_picking","wizard_id","picking_id","Force Pickings",domain=[('type','=','in'),('state','=','done')]),
		}
	_defaults={
		"purchase_type":lambda *p:'import',
		'filter_date':lambda *f:'as_of',
		"start_date":lambda *a:datetime.now().strftime("%Y-%m-01"),
		"end_date":lambda *a:datetime.now().strftime("%Y-%m-%d"),
		"as_of_date":lambda *a:datetime.now().strftime("%Y-%m-%d"),
		'report_type':lambda *a :'pdf',
		'goods_type':lambda *g:'raw',
		'header_group_by':lambda *h:'vendor_wise',
		}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:
			context={}
		form_data=self.read(cr, uid, ids)[0]
		# print "=============",form_data
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'purchase.receipt.register.daily.wizard',
			'form': form_data,
			}
		if form_data['report_type']=='pdf': 
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'purchase.receipt.register.daily.report',
				'report_type': 'webkit',
				'datas': datas,
				}
		else:
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'xls.purchase.receipt.register.daily.report',
				'report_type': 'webkit',
				'datas': datas,
				}
