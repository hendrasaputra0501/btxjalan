from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class sale_order(osv.Model):
	_inherit = "sale.order"
	_description = "Sales Order"
	_track = {
		'state': {
			'sale.mt_order_confirmed': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['manual', 'progress'],
			'sale.mt_order_sent': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['sent']
		},
	}
	_columns = {
		"lc_ids":fields.many2many('letterofcredit','sale_order_letterofcredit_rel','lc_id','order_id',"Letter of Credit(s)"),
		"new_lc":fields.boolean("Use New LC?",help="Check this field if you want to create new LC instead of using existing LC"),
		'payment_method': fields.selection([('cash','Cash'),('tt','Telegraphic Transfer (TT)'),('lc','LC')],"Payment Method"),
		'state': fields.selection([
			('draft', 'Draft Quotation'),
			('sent', 'Quotation Sent'),
			('lc_draft', 'LC Generated'),
			# ('lc_check', 'LC Check'),
			# ('lc_verified','LC Verified'),
			('cancel', 'Cancelled'),
			('waiting_date', 'Waiting Schedule'),
			('progress', 'Sales Order'),
			('manual', 'Sale to Invoice'),
			('shipping_except', 'Shipping Exception'),
			('invoice_except', 'Invoice Exception'),
			('done', 'Done'),
			], 'Status', readonly=True,
			help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
	}

	_defaults ={
		'state': 'draft',
		'new_lc': lambda *a:True,
	}
	
	def onchange_payment_method(self,cr,uid,ids,payment_method,context=None):
		if not context:context={}
		value={'new_lc':False}
		if payment_method=='lc':
			value={'new_lc':True}
		return {'value':value}
	
	def check_draft(self,cr,uid,ids,context=None):
		if not context:context={}
		sale = self.browse(cr,uid,ids,context)
		if isinstance(sale,(tuple,list)):
			if sale[0].lc_ids:
				return True
		else:
			if sale.lc_ids:
				return True
		return False


class sale_order_line(osv.osv):
	_inherit = 'sale.order.line'
	
	def name_get(self, cr, user, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		result = self.browse(cr, user, ids, context=context)
		res = []
		for rs in result:
			deliv_ref = False
			name = "%s" % (rs.sequence_line)
			res += [(rs.id, name)]
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		domain=[]
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [('sequence_line', operator, name)]
		else:
			if name:
				domain = [('sequence_line', operator, name)]
			# print "===============",domain
		ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
		return self.name_get(cr, user, ids, context=context)	