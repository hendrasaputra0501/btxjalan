import time
import datetime

from openerp.osv import fields, osv
from openerp import pooler
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class work_order_invoice(osv.Model):
	_name = 'work.order.invoice'
	_columens = {
		'line_ids': fields.one2many('work.order.invoice.line', 'wizard_id', 'Work Orders', required=True),
		'date_invoice': fields.date('Invoice Date', required=True),
		'project_id': fields.many2one('project.project', 'Project Ref'),
	}

	_defaults = {
		'project_id' : lambda self, cr, uid, context: context.get('project_id',False),
	}

work_order_invoice()


class work_order_invoice_line(osv.Model):
	_name = "work.order.invoice.line"
	_columns = {
		'wizard_id': fields.many2one('work.order.invoice', 'Ref', ondelete='cascade', required=True, select="1"),
		'work_order_id': fields.many2one('project.work.order', 'Work Order', required=True),
		'name': fields.char('Work summary', size=128),
		'product_id' : fields.many2one('product.product', 'Product', domain=[('type','=','service')], required=True),
		'quantity' : fields.float('Quantity', digits_compute= dp.get_precision('Account')),
		'uom_id' : fields.many2one('product.uom', 'UoS'),
		'unit_price' : fields.float('Price Unit', digits_compute= dp.get_precision('Account')),
		# 'amount_subtotal' : fields.function(_get_amount_subtotal, type='float', digits_compute= dp.get_precision('Account'), string='Amount Subtotal'),
	}
work_order_invoice_line()