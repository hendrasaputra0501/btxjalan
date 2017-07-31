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

# from osv import osv, fields
# from tools.translate import _
# import openerp.addons.decimal_precision as dp
# from openerp import netsvc

class covering_doc(osv.osv):
	_name = "covering.doc"
	_columns ={

	'date' : fields.date('Covering Date', size=32,required=True),
	'city' : fields.text('City'),
	'consignee_id' : fields.many2one('res.partner', "Applicant"),
	'invoice_ids' : fields.many2many('account.invoice','account_invoice_covering_doc_rel','invoice_id','covering_id', 'Related invoice(s)',readonly=True),
	'doc_lines_ids' : fields.one2many('covering.doc.line','covering_doc_id','Document Lines'),
	'sign_by' : fields.many2one('res.partner', "Sign By"),
	'show_consignee' : fields.boolean('Use Custom Address Descr ?'),
	'c_address_text' :fields.text('Applicant Address'),
	}

	def default_get(self, cr, uid, fields, context):
		if context is None: context = {}
		res = super(covering_doc, self).default_get(cr, uid, fields, context=context)
		
		if 'doc_lines_ids' in fields:
			cr.execute("select id from covering_document_parameter")
			res_ids = [id[0] for id in cr.fetchall()]
			line_ids = []
			for uyp in self.pool.get('covering.document.parameter').browse(cr,uid, res_ids):
				line_ids.append({
					'parameter_id':uyp.id,
					'desc' : uyp.name,
					# 'desc':uyp.desc or uyp.name or '',
					'original':0,
					'copy_1':0,
					})
			res.update(doc_lines_ids=line_ids)
		
		return res

	# def get_consignee_address(self,cr,uid,consignee_id,context):
	# 	res=[]
	# 	res1=[]
	# 	res2=[]
	# 	if consignee_id:
	# 		res.append(consignee_id.street)
	# 		res1.append(consignee_id.stree2)
	# 		res2.append(consignee_id.street3)
	# 	return res,res1,res2





class covering_doc_line(osv.osv):
	_name = "covering.doc.line"
	_columns = {
		'parameter_id' : fields.many2one('covering.document.parameter', 'Parameter', required=False),
		'desc' : fields.char('Parameter Desc', size=200, required=True),
		'original' : fields.integer('Original',required=True),
		'copy_1' : fields.integer('Copy',required=True),
		'covering_doc_id' : fields.many2one('covering.doc',string='Covering Document'),
	}

covering_doc_line()	

class covering_document_parameter(osv.osv):
	_name = "covering.document.parameter"
	_columns = {
		'name' : fields.char('Parameter Desc', size=200, required=True),
		# 'desc' : fields.char('Desc', size=200),
		'original' : fields.integer('Original', required=True),
		'copy_1' : fields.integer('Copy', required=True),
	}

covering_document_parameter()