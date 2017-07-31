from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp

class account_payment_term(osv.osv):
	_inherit = "account.payment.term"

	_columns = {
		'due_date_from_bl_date' : fields.boolean('Due Date From BL Date'),
		'type' : fields.selection([('sight','Sight'),('usance','Usance')],"Payment Term Type"),
	}

	def compute(self, cr, uid, id, value, date_ref=False, context=None):
		if not context:context={}
		due_date_from_bl_date=context.get('due_date_from_bl_date',False)
		
		if due_date_from_bl_date and context.get('bl_date',False):
			date_ref=context.get('bl_date')
		
		if not date_ref:
			date_ref = datetime.now().strftime('%Y-%m-%d')
		pt = self.browse(cr, uid, id, context=context)
		amount = value
		result = []
		obj_precision = self.pool.get('decimal.precision')
		prec = obj_precision.precision_get(cr, uid, 'Account')
		for line in pt.line_ids:
			if line.value == 'fixed':
				amt = round(line.value_amount, prec)
			elif line.value == 'procent':
				amt = round(value * line.value_amount, prec)
			elif line.value == 'balance':
				amt = round(amount, prec)
			if amt:
				next_date = (datetime.strptime(date_ref, '%Y-%m-%d') + relativedelta(days=line.days))
				if line.days2 < 0:
					next_first_date = next_date + relativedelta(day=1,months=1) #Getting 1st of next month
					next_date = next_first_date + relativedelta(days=line.days2)
				if line.days2 > 0:
					next_date += relativedelta(day=line.days2, months=1)
				result.append( (next_date.strftime('%Y-%m-%d'), amt) )
				amount -= amt

		amount = reduce(lambda x,y: x+y[1], result, 0.0)
		dist = round(value-amount, prec)
		if dist:
			result.append( (time.strftime('%Y-%m-%d'), dist) )
		return result