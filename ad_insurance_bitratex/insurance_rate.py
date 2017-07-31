from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta


class insurance_type(osv.osv):
	_name = "insurance.type"

	_columns = {
		"name" : fields.char("Description", size=50, required=True),
		"type" : fields.selection([('sale','Sale'),('purchase','Purchase'),('general','General')],"Type"),
		"sale_type" : fields.selection([('local','Local'),('export','Export')],"Sale Type"),
		"purchase_type" : fields.selection([('local','Local'),('import','Import')],"Purchase Type"),
		"incoterms" : fields.many2one("stock.incoterms","Incoterms"),
		"rate_ids" : fields.one2many("insurance.rate","insurance_id","Insurance Rate"),
	}

	def _get_rate(self, cr, uid, insurance_id=False, itype=None, sale_type=None, purchase_type=None, incoterms=False, context=None):
		if context is None:
			context = {}
		#process the case where the account doesn't work with an outgoing currency rate method 'at date' but 'average'
		insurance_rate_pool = self.pool.get('insurance.rate')
		if insurance_id:
			rate_ids = insurance_rate_pool.search(cr, uid, [('insurance_id','=',insurance_id),('name','<=',context.get('date',datetime.date.today().strftime('%Y-%m-%d')))], context=context)
			if rate_ids:
				rate = insurance_rate_pool.browse(cr, uid, rate_ids, context=context)[0].rate
				return rate
			else:
				raise osv.except_osv(_('Warning!'), _('Please Insert Insurance Rate'))
		
		else: 
			insurance_ids = []
			if itype and sale_type:
				if incoterms:
					insurance_ids = self.search(cr, uid, [('type','=',itype),('sale_type','=',sale_type),('incoterms','=',incoterms)], context=context)
				else:
					insurance_ids = self.search(cr, uid, [('type','=',itype),('sale_type','=',sale_type)], context=context)
			elif itype and purchase_type:
				insurance_ids = self.search(cr, uid, [('type','=',itype),('purchase_type','=',purchase_type)], context=context)
			else:
				raise osv.except_osv(_('Warning!'), _('All parameters inputed for searching the insurance rate is not complete or not valid'))
			
			if insurance_ids:
				rate_ids = insurance_rate_pool.search(cr, uid, [('insurance_id','=',insurance_ids[0]),('name','<=',context.get('date',time.strftime('%Y-%m-%d')))], order="name", context=context)
				if rate_ids:
					rate = insurance_rate_pool.browse(cr, uid, rate_ids, context=context)[0].rate
					return rate
				else:
					raise osv.except_osv(_('Warning!'), _('Please Insert Insurance Rate Masters'))
			else:
				raise osv.except_osv(_('Warning!'), _('Please Insert Insurance Masters'))

insurance_type()

class insurance_rate(osv.osv):
	_name = "insurance.rate"

	_columns = {
		"insurance_id" : fields.many2one("insurance.type","Insurance"),
		"rate" : fields.float("Rate %", digits=(2,5)),
		"name" : fields.date("Valid From", required=True),
	}

	_order = "id desc"
insurance_rate()