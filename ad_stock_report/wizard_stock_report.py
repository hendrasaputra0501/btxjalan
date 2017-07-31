from openerp.osv import fields,osv
import datetime
class goods_type(osv.Model):
	_name = "goods.type"
	_columns = {
		"name" 			: fields.char("Name",required=True),
		"code"			: fields.char("Code",required=True),
		"description"	: fields.text("Description")
	}

class stock_report_bitratex_wizard(osv.osv_memory):
	_name = "stock.report.bitratex.wizard"
	_columns = {
		"date_start"	: fields.datetime("Start Range",required=False),
		"date_stop"		: fields.datetime("Stop Range",required=False),
		"goods_type"	: fields.many2many("goods.type",'goods_type_stock_report_rel','type_id','wizard_id',"Goods Type"),
		"output_type"	: fields.selection([('xls',"Excel (*.xls)")],"Output Type"),
		"grouping"		: fields.selection([('product',"Product Wise"),('location',"Site Wise")],"Grouping",required=True),
		"location_exception": fields.many2many("stock.location","location_stock_report_rel","location_id","wizard_id","Location Exception"),
		"location_force": fields.many2many("stock.location","location_stock_report_force_rel","location_id","wizard_id","Force Location"),
		"product_ids": fields.many2many("product.product","product_stock_report_rel","product_id","wizard_id","Product Filter"),
		"with_valuation": fields.boolean("Print with valuation"),
		"show_only_qty_less_than_1_kg" : fields.boolean("FG Qty Less than 1/-1 Kg?"),
	}

	_defaults = {
		"date_start":lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-01 00:00:00"),
		# "date_stop":lambda self,cr,uid,context:datetime.date.today().strftime("%Y-%m-%d 23:59:59"),
		"date_stop":lambda self,cr,uid,context:datetime.date.today().strftime("2016-01-31 23:59:59"),
		"output_type":'xls',
		"grouping": lambda *a: "location",
		'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',5)],context=None),
		'with_valuation': True,
	}

	def generate_report(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'stock.report.bitratex.wizard',
			'date_start' : wizard.date_start,
			'date_stop' : wizard.date_stop,
			'goods_type':[x.id for x in wizard.goods_type],
			'location_exception':[le.id for le in wizard.location_exception],
			'location_force':[lf.id for lf in wizard.location_force],
			'product_ids':[p.id for p in wizard.product_ids],
			'grouping':wizard.grouping,
			'show_only_qty_less_than_1_kg':wizard.show_only_qty_less_than_1_kg,
			'valuation': wizard.with_valuation,
			}
		# print "--------------------sssssssssssssssssssssss",datas
		if not wizard.with_valuation:
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'stock.report.bitratex',
					'report_type': 'webkit',
					'datas': datas,
					}
		else:
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'valuation.stock.report.bitratex',
					'report_type': 'webkit',
					'datas': datas,
					}