from openerp.osv import fields,osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

class stock_ageing_wizard(osv.osv_memory):
	_name = "stock.ageing.wizard"
	_columns = {
		"as_on"			: fields.date("As On",required=False),
		"goods_type"	: fields.many2many("goods.type",'goods_type_stock_ageing_rel','type_id','wizard_id',"Goods Type"),
		"output_type"	: fields.selection([('xls',"Excel (*.xls)")],"Output Type"),
		"location_exception": fields.many2many("stock.location","location_stock_ageing_rel","location_id","wizard_id","Location Exception"),
		"location_force": fields.many2many("stock.location","location_stock_ageing_force_rel","location_id","wizard_id","Force Location"),
		"period_length" : fields.integer("Period Length (days)"),
	}

	_defaults = {
		# "as_on":lambda self,cr,uid,context:datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		"as_on":lambda self,cr,uid,context:time.strftime("%Y-%m-%d"),
		"output_type":'xls',
		'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',1)],context=None)
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
            'model': 'stock.ageing.wizard',
			'prev_date' : (datetime.strptime(wizard.as_on,"%Y-%m-%d")).strftime("%Y-%m-%d 00:00:00"),
			'as_on' : (datetime.strptime(wizard.as_on,"%Y-%m-%d")).strftime("%Y-%m-%d 23:59:59"),
			'goods_type':[x.id for x in wizard.goods_type],
			'location_exception':[le.id for le in wizard.location_exception],
			'location_force':[lf.id for lf in wizard.location_force],
			'period_length':wizard.period_length or 30,
			}
		return {
                'type': 'ir.actions.report.xml',
                # 'report_name': 'stock.ageing.report.pdf',
                'report_name': 'stock.ageing.report.xls',
                'report_type': 'webkit',
                'datas': datas,
                }