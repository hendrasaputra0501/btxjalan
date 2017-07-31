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

class quality_certificate_form(osv.osv):
	_name = "quality.certificate.form"
	_columns = {
		'name' : fields.char('Number',size=128),
		'sale_ids' : fields.many2many('sale.order','sale_quality_certificate_rel','sale_id','quality_certificate_id','Sales Contract', required=False),
		'date' : fields.date('Date', required=True),
		'sale_line_ids' : fields.many2many('sale.order.line','sale_line_quality_certificate_rel','sale_line_id','quality_certificate_id','Order Number', required=False, domain="[('order_id','=',sale_id)]"),
		'product_id' : fields.many2one('product.product',string='Product'),
		'shipper' : fields.many2one('res.partner','Shipper'),
		'consignee' : fields.many2one('res.partner','Consignee'),
		'notify' : fields.many2one('res.partner','Notify Party'),
		'invoice_id':fields.many2one('account.invoice','Invoice'),
		'quality_certificate_line_ids' : fields.one2many('quality.certificate.form.line','quality_certificate_id'),
		'note' : fields.text('Additional Note'),
		'remarks' : fields.text('Remarks'),
		'title_header_form' : fields.char('Title Header Print Form', size=200),
		'company_id' : fields.many2one('res.company', 'Company'),
	}

	_defaults = {
		'company_id' : lambda self, cr, uid, ids: self.pool.get('res.users').browse(cr, uid, uid).company_id.id, 
		'name' : '/',
	}

	def default_get(self, cr, uid, fields, context):
		if context is None: context = {}
		res = super(quality_certificate_form, self).default_get(cr, uid, fields, context=context)
		
		if 'quality_certificate_line_ids' in fields:
			cr.execute("select id from quality_certificate_yarn_parameter")
			res_ids = [id[0] for id in cr.fetchall()]
			line_ids = []
			for uyp in self.pool.get('quality.certificate.yarn.parameter').browse(cr,uid, res_ids):
				line_ids.append({
					'parameter_id':uyp.id,
					'desc':uyp.desc or uyp.name or '',
					'value':0,
					})
			res.update(quality_certificate_line_ids=line_ids)
		
		return res

	def create(self, cr, uid, vals, context=None):
		if context is None:
			context={}
		company_pooler = self.pool.get('res.company')
		sale_pooler = self.pool.get('sale.shop')
		company_code = ''
		company_id = False
		if vals.get('name','/')=='/':
			if vals.get('company_id',False):
				company_id = company_pooler.browse(cr, uid, vals.get('company_id',False))
			
			if company_id:
				company_code=company_id.prefix_sequence_code
			
			vals['name'] = (company_code + (self.pool.get('ir.sequence').get(cr, uid, self._name) or '/'))

		res = super(quality_certificate_form,self).create(cr, uid, vals, context=context)
		return res
quality_certificate_form()

class quality_certificate_form_line(osv.osv):
	_name = "quality.certificate.form.line"
	_columns = {
		'parameter_id' : fields.many2one('quality.certificate.yarn.parameter', 'Parameter', required=False),
		'desc' : fields.char('Parameter Desc', size=200, required=True),
		'value' : fields.float('Value', digits=(2,4),required=True),
		'quality_certificate_id' : fields.many2one('quality.certificate.form','Reference'),
	}

quality_certificate_form_line()

class quality_certificate_yarn_parameter(osv.osv):
	_name = "quality.certificate.yarn.parameter"
	_columns = {
		'name' : fields.char('Parameter Desc', size=200, required=True),
		'desc' : fields.char('Desc', size=200),
	}

quality_certificate_yarn_parameter()
