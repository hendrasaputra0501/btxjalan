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

class declaration_form(osv.osv):
	_name = "declaration.form"
	_rec_name = "partner_id"
	_columns = {
		"city" : fields.char("City",size=120, required=True),
		"date_declaration" : fields.date("Date Declaration", required=True),
		"partner_id" : fields.many2one('res.partner','Customer',domain=[('customer','=','True')], required=True),
		"invoice_id" : fields.many2one('account.invoice', 'Invoice',domain=[('type','=','out_invoice')], required=True),
		"invoice_ids" : fields.many2many('account.invoice','declaration_invoice_rel','declaration_id','invoice_id','Invoices',domain=[('type','=','out_invoice')]),
		"lc_ids" : fields.many2many('letterofcredit','declaration_letterofcredit_rel','declaration_id','lc_id','LCs',domain=[('lc_type','=','in')]),
		"sale_ids" : fields.many2many('sale.order','declaration_sale_order_rel','declaration_id','sale_id','Sale Orders'),
		"picking_ids" : fields.many2many('stock.picking','declaration_stock_picking_rel','declaration_id','picking_id','Delivery Orders',domain=[('type','=','out')]),
		# "sale_line_ids" : fields.many2many('sale.order','declaration_sale_order_rel','declaration_id','sale_id','Invoice'),
		"declaration_template_id" : fields.many2one("declaration.template","Declaration Template"),
		"declaration_title" : fields.char("Declaration Title", size=120, required=True),
		"declaration_header" : fields.text("Declaration Header"),
		"declaration_content" : fields.text("Declaration Content", required=True),
		"declaration_footer" : fields.text("Declaration Footer"),
		
		"fax" : fields.char("Fax",size=120),
		"to" : fields.char("To",size=120),
		"attn" : fields.char("Attention",size=120),
		"source_person" : fields.char("From",size=120),
		"sn" : fields.char("SN",size=120),
		"fumigation_title" : fields.char("Certificate Fumigation Title",size=500),
		"type_of_wood_packaging" : fields.char("Type of Wood Packaging",size=120),
	}

	_defaults = {
		'city' : lambda *a:'Semarang',
		'date_declaration' : lambda *d: time.strftime('%Y-%m-%d'),
		'type_of_wood_packaging' : lambda *a:'PALLET',
		'fumigation_title' : lambda *a:'FUMIGATION CERTIFICATE'
	}

	def onchange_declaration_template(self, cr, uid, ids, template_id, context=None):
		res = {
			'declaration_title':False,
			'declaration_header':False,
			'declaration_content':False,
			'declaration_footer':False,	
		}
		if template_id:
			template = self.pool.get("declaration.template").browse(cr, uid, template_id)
			res['declaration_title'] = template.declaration_title_template and template.declaration_title_template.encode("utf-8") or ""
			res['declaration_header'] = template.declaration_header_template and template.declaration_header_template.encode("utf-8") or ""
			res['declaration_content'] = template.declaration_content_template and template.declaration_content_template.encode("utf-8") or ""
			res['declaration_footer'] = template.declaration_footer_template and template.declaration_footer_template.encode("utf-8") or ""
		return {'value':res}
declaration_form()

class declaration_template(osv.osv):
	_name = "declaration.template"
	_columns = {
		"partner_id" : fields.many2one('res.partner','Customer',domain=[('customer','=','True')]),
		"declaration_title_template" : fields.char("Declaration Title", size=120, required=True),
		"declaration_header_template" : fields.text("Declaration Header"),
		"declaration_content_template" : fields.text("Declaration Content", required=True),
		"declaration_footer_template" : fields.text("Declaration Footer"),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['partner_id'], context)
		res = []
		for record in reads:
			partner_id = record['partner_id'][0]
			name = self.pool.get('res.partner').browse(cr, uid, partner_id).name
			res.append((record['id'], name))
		return res