from openerp.osv import fields,osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

class summary_stock_wizard(osv.osv_memory):
	_name = "summary.stock.wizard"
	_columns = {
		"filter_type"	: fields.selection([('date_period','Date Period'),('as_on_date','As On')], 'Filter', required=True),
		"as_on"			: fields.date("As On",required=False),
		"start_date"	: fields.date("Start Date",required=False),
		"end_date"		: fields.date("End Date",required=False),
		"goods_type"	: fields.many2many("goods.type",'goods_type_stock_summary_rel','type_id','wizard_id',"Goods Type"),
		"output_type"	: fields.selection([('xls',"Excel (*.xls)")],"Output Type"),
		# "location_exception": fields.many2many("stock.location","location_stock_ageing_rel","location_id","wizard_id","Location Exception"),
		"location_force": fields.many2many("stock.location","location_stock_ageing_force_rel","location_id","wizard_id","Force Location"),
	}

	_defaults = {
		# "as_on":lambda self,cr,uid,context:datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		"filter_type":lambda *a : 'as_on_date',
		"as_on":lambda self,cr,uid,context:time.strftime("%Y-%m-%d"),
		"start_date":lambda self,cr,uid,context:time.strftime("%Y-%m-01"),
		"end_date":lambda self,cr,uid,context:time.strftime("%Y-%m-%d"),
		"output_type":'xls',
		'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',1)],context=None)
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'summary.stock.wizard',
			'filter_type' : wizard.filter_type,
			'prev_date' : (datetime.strptime(wizard.as_on,"%Y-%m-%d")).strftime("%Y-%m-%d 00:00:00"),
			'as_on' : (datetime.strptime(wizard.as_on,"%Y-%m-%d")).strftime("%Y-%m-%d 23:59:59"),
			'start_date' : (datetime.strptime(wizard.start_date,"%Y-%m-%d")).strftime("%Y-%m-%d 00:00:00"),
			'end_date' : (datetime.strptime(wizard.end_date,"%Y-%m-%d")).strftime("%Y-%m-%d 23:59:59"),
			'goods_type':[x.id for x in wizard.goods_type],
			# 'location_exception':[le.id for le in wizard.location_exception],
			'location_force':[lf.id for lf in wizard.location_force],
			}
		return {
				'type': 'ir.actions.report.xml',
				# 'report_name': 'stock.ageing.report.pdf',
				'report_name': 'summary.stock.report.xls',
				'report_type': 'webkit',
				'datas': datas,
				}