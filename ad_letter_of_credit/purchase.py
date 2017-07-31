from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class purchase_order(osv.Model):
	_inherit = "purchase.order"
	STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('confirmed', 'Waiting Approval'),
        ('lc_created',"Draft LC Created"),
        ('adv_created','Draft Advance Created'),
        ('approved', 'Purchase Order'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]
	_columns = {
		"lc_ids"				: fields.many2many('letterofcredit','purchase_order_letterofcredit_rel','lc_id','order_id',"Letter of Credit(s)"),
		"new_lc"				: fields.boolean("Use New LC?",help="Check this field if you want to create new LC instead of using existing LC"),
		'payment_method'		: fields.selection([('cash','Cash'),('tt','Telegraphic Transfer (TT)'),('lc','LC')],"Payment Method",required=True),
		'state'					: fields.selection(STATE_SELECTION, 'Status', readonly=True, help="The status of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' status. Then the order has to be confirmed by the user, the status switch to 'Confirmed'. Then the supplier must confirm the order to change the status to 'Approved'. When the purchase order is paid and received, the status becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the status becomes in exception.", select=True),
		'force_release'			: fields.boolean("Force Release"),
		'incoterm'				: fields.many2one('stock.incoterms',"Incoterm"), 
	}
	_defaults = {
		'new_lc':lambda *a:True,
		'payment_method': lambda *a:'cash',
	}

	def check_draft(self,cr,uid,ids,context=None):
		if not context:context={}
		po = self.browse(cr,uid,ids,context)
		if isinstance(po,(tuple,list)):
			if po[0].lc_ids:
				return True
		else:
			if po.lc_ids:
				return True
		return False

	def force_release(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'force_release':True},context=context)