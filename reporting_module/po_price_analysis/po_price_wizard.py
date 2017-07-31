import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp

class po_price_wizard(osv.osv_memory):
	_name = "po.price.wizard"
	_columns = {
			"start_date" : fields.date('Start Date',required=True),
			"end_date" : fields.date('End Date',required=True),
			# "header_group_by" : fields.selection([('supplier_wise','Supplier Wise'),('product_wise','Product Wise')],'Header Group By', required=True),
			"goods_type" : fields.many2many("goods.type",'goods_type_po_price_rel','type_id','wizard_id',"Goods Type", required=True),
			"product_ids" : fields.many2many("product.product","product_po_price_rel","product_id","wizard_id","Products"),
			"partner_ids" : fields.many2many("res.partner","res_partner_po_price_rel","partner_id","wizard_id","Force Analytic Account"),
	}
	_defaults = {
		"start_date": time.strftime("%Y-%m-01"),
		"end_date" : time.strftime("%Y-%m-%d"),
		# "header_group_by" : lambda *h:'site_wise',
		'goods_type':lambda self,cr,uid,context=None:self.pool.get('goods.type').search(cr,uid,[('id','=',5)],context=None),
	}

	def print_report(self, cr, uid, ids, context={}):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'po.price.wizard',
			'start_date' : wizard.start_date,
			'end_date' : wizard.end_date,
			'goods_type':[(x.code,x.name) for x in wizard.goods_type],
			'product_ids' : [x.id for x in wizard.product_ids],
			'partner_ids' : [x.id for x in wizard.partner_ids],
			}
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'po.price.analysis.report',
				'report_type': 'webkit',
				'datas': datas,
				}
po_price_wizard()