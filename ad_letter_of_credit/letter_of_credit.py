from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class loc(osv.osv):
	def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for lc in self.browse(cr, uid, ids, context=context):
			total=0.0
			for line in lc.contract_product_ids:
				price = line.price_unit * line.product_uom_qty
				total += price

			res[lc.id]=total
		return res

	def _lc_amount(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for lc in self.browse(cr, uid, ids, context=context):
			total=0.0
			for line in lc.lc_product_lines:
				price = line.price_unit * line.product_uom_qty
				total += price
			res[lc.id]=total
		return res

	_name = "letterofcredit"
	_inherit = ['mail.thread']
	_columns = {
		'name' : fields.char('Internal Ref.',required=True,readonly=True),
		'entry_date' : fields.date('Entry Date', required=True, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'parent_id' : fields.many2one('letterofcredit','Parent Doc'),
		'prev_revision_id' : fields.many2one('letterofcredit','Previous Rev Doc'),
		'lc_type'      : fields.selection([('tt','TT'),('in','LC'),('out','OUT')],"Type",readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'partner_id' : fields.many2one('res.partner','Customer',required=True,readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'parent_partner_id':fields.many2one('res.partner','Partner Group',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		
		'shipper' : fields.many2one('res.partner','Shipper', required=False,readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_shipper_address' : fields.boolean('Use Customs Address Desc?',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		's_address_text' : fields.text('Shipper Address Details',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),

		'applicant' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)], required=False, help="Applicant for Bill of Loading",readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_applicant_address' : fields.boolean('Use Customs Address Desc?',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'a_address_text' : fields.text('Applicant Address Details for Bill of Loading',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'consignee' : fields.many2one('res.partner','Consignee/Buyer',domain=[('customer', '=', True)], required=False, help="Consignee for Bill of Loading",readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_consignee_address' : fields.boolean('Use Customs Address Desc?',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'c_address_text' : fields.text('Consignee Address Details for Bill of Loading',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'notify' : fields.many2one('res.partner','Notify Party',domain=[('customer', '=', True)], required=False, help="Notify for Bill of Loading",readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_notify_address' : fields.boolean('Use Customs Address Desc?',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'n_address_text' : fields.text('Notify Address Details for Bill of Loading',readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),

		'applicant_pl' : fields.many2one('res.partner','Applicant',domain=[('customer', '=', True)], required=False, help="Applicant for Packing List/Commercial Invoice", readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_applicant_address_pl' : fields.boolean('Use Customs Address Desc?', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'a_address_text_pl' : fields.text('Applicant Address Details for Packing List/Commercial Invoice', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'consignee_pl' : fields.many2one('res.partner','Consignee/Buyer',domain=[('customer', '=', True)], required=False, help="Consignee for Packing List/Commercial Invoice", readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_consignee_address_pl' : fields.boolean('Use Customs Address Desc?', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'c_address_text_pl' : fields.text('Consignee Address Details for Packing List/Commercial Invoice', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'notify_pl' : fields.many2one('res.partner','Notify Party',domain=[('customer', '=', True)], required=False, help="Notify for Packing List/Commercial Invoice", readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'show_notify_address_pl' : fields.boolean('Use Customs Address Desc?', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'n_address_text_pl' : fields.text('Notify Address Details for Packing List/Commercial Invoice', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),

		'packing_list_header' : fields.text('Packing List Header', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'commercial_invoice_header' : fields.text('Commercial Invoice Header', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'shipping_instruction_header' : fields.text('Shipping Instruction Header', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		
		# Contract Detail
		'sale_ids' : fields.many2many('sale.order', 'sale_order_letterofcredit_rel','order_id','lc_id' ,'Sales Contract', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'sale_line_ids' : fields.many2many('sale.order.line', 'sale_order_line_letterofcredit_rel','order_line_id','lc_id' ,'Contract Products', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		
		'purchase_ids' : fields.many2many('purchase.order', 'purchase_order_letterofcredit_rel','order_id','lc_id' ,'Purchase Order', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'purchase_line_ids' : fields.many2many('purchase.order.line', 'purchase_order_line_letterofcredit_rel','order_line_id','lc_id' ,'Purchased Products', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),

		'contract_product_ids' : fields.one2many('letterofcredit.contract.product.line','lc_id','Product', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'amount_total' : fields.function(_amount_total, store=True,string='Amount', digits_compute= dp.get_precision('amount_total')),
		'contract_incoterm' : fields.many2one('stock.incoterms','Term', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'contract_dest' : fields.many2one('res.port','Destination', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'contract_lsd' : fields.date('Shipment', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'contract_payment_term' : fields.many2one('account.payment.term','Payment Term', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		# LC Detail
		'lc_number':fields.char("LC Number",size=160, required=True, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_product_lines' : fields.one2many('letterofcredit.product.line','lc_id','Product', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_amount' : fields.function(_lc_amount, store=True,string='Amount', digits_compute= dp.get_precision('lc_amount'), readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_incoterm' : fields.many2one('stock.incoterms','Term', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_dest' : fields.many2one('res.port','Destination', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_lsd' : fields.date('Shipment', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_payment_term' : fields.many2one('account.payment.term','Payment Term', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_auth' : fields.selection([('yes','Yes'),('no','No')],'LC Authentication', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_ship_valid_date' : fields.date('Last Shipment Date', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_ship_earliest_date' : fields.date('Earliest Shipment Date', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_expiry_date' : fields.date('LC Expiry Date/Place', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_expiry_place' : fields.char('LC Expiry Date/Place',size=50, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_term_doc_persentation' : fields.text('Term for Document Persentation', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'lc_negotiability' : fields.selection([('yes','Yes'),('no','No')],'LC Negotiability Any Bank In Indonesia', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'tolerance_percentage'  : fields.float("Min. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)", readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'tolerance_percentage_max'  : fields.float("Max. Tolerance(%)",help="Fill in the tolerance percentage (range 0.0 - 100.0)", readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'part_ship' : fields.selection([
			('allowed','ALLOWED'),
			('prohibited','PROHIBITED'),
			],'Partial Shipments', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'tranship' : fields.selection([
			('allowed','ALLOWED'),
			('prohibited','PROHIBITED'),
			],'Transhipment', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'opening_bank' : fields.many2one('res.bank', 'LC Opening Bank', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'intermed_bank' : fields.many2one('res.bank', 'Intermediary Bank if Any', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'negotiate_bank' : fields.many2one('res.bank', 'LC Negotating Bank', required=False, readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'draf_clause' : fields.text('Draf Clause', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'bank_charges' : fields.selection([('opener','Opener A/C'),('beneficiary','Beneficiary A/C')],'Bank Charges', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'confirm_charges' : fields.selection([('un','UN'),('confirm','Confirm')],'Confirmation Charges', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'packing' : fields.selection([('neutral','Neutral'),('bitratex_logo','Bitratex Logo')],'Packing', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'tt_reimbursment' : fields.selection([
			('available','Available'),
			('not','Not Available'),
			],'T/T Reimbursment', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'negotiate_confirm' : fields.selection([
			('available','Available'),
			('not','Not Available'),
			],'Negotiation Bank Confirmation', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'date_of_issue' : fields.date('LC Establised On', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'rcvd_jkt' : fields.date('LC Rcvd by MKT-JKT On', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'rcvd_smg' : fields.date('LC Rcvd by MKT-SMG On', readonly=False, states={'nonactive': [('readonly', True)], 'closed': [('readonly', True)]}),
		'prepared_by' : fields.many2one('res.users','Prepared By', readonly=True),
		'checked_by' : fields.many2one('res.users','Checked By', readonly=True),
		'approved_by' : fields.many2one('res.users','Approved By', readonly=True),
		'amandement_lines' : fields.one2many('letterofcredit.amandement.line','lc_id','Default Amandement Required'),
		'add_amandement_lines' : fields.one2many('letterofcredit.amandement.line','manual_lc_id','Additional Amandement Required'),
		'state' : fields.selection([
			('draft', 'Draft'),
			('confirmed','Need Review'),
			('checked','Need Approval'),
			('approved', 'Active'),
			('canceled', 'Cancelled'),
			('closed', 'Closed'),
			('nonactive', 'Non-Active'),
			], 'Status', readonly=True, track_visibility='onchange',select=True),
		
		'label_print' : fields.text('Label Document'),
		'label_print_help' : fields.text('Label Document Help'),
		"model_id":fields.many2one('ir.model','Model'),
		"hide" : fields.boolean('Hide this doc in the Reports?'), 
	}
	_defaults = {
		'state': 'draft',
		'name':'/',
		'model_id': lambda self,cr,uid,context:self.pool.get('ir.model').search(cr,uid,[('model','=',self._name)])[0],
		'lc_type':lambda self,cr,uid,context:context.get('lc_type','in'),
		'label_print':'{}',
		'tolerance_percentage_max':lambda *a:0.0,
		'tolerance_percentage':lambda *a:0.0,
	}

	_order = "entry_date desc"
	
	def onchange_consignee(self, cr, uid, ids, consignee_id, show_consignee_address, c_address_text):
		res = {
			'consignee_pl' : False,
			'show_consignee_address_pl' : False,
			'c_address_text_pl' : '',
		}
		if consignee_id:
			res['consignee_pl'] = consignee_id
		if show_consignee_address:
			res['show_consignee_address_pl'] = show_consignee_address
		if c_address_text:
			res['c_address_text_pl'] = c_address_text
		return {'value':res}

	def onchange_notify(self, cr, uid, ids, notify_id, show_notify_address, n_address_text):
		res = {
			'notify_pl' : False,
			'show_notify_address_pl' : False,
			'n_address_text_pl' : '',
		}
		if notify_id:
			res['notify_pl'] = consignee_id
		if show_notify_address:
			res['show_notify_address_pl'] = show_notify_address
		if n_address_text:
			res['n_address_text_pl'] = n_address_text
		return {'value':res}

	def onchange_applicant(self, cr, uid, ids, applicant_id, show_applicant_address, a_address_text):
		res = {
			'applicant_pl' : False,
			'show_applicant_address_pl' : False,
			'a_address_text_pl' : '',
		}
		if applicant_id:
			res['notify_pl'] = applicant_id
		if show_applicant_address:
			res['show_applicant_address_pl'] = show_applicant_address
		if a_address_text:
			res['a_address_text_pl'] = a_address_text
		return {'value':res}

	def name_get(self, cr, user, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		result = self.browse(cr, user, ids, context=context)
		res = []
		for rs in result:
			name = "%s"%(rs.lc_number and rs.lc_number or '')
			res += [(rs.id, name)]
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('lc_number', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

	def create(self,cr,uid,vals,context=None):
		if vals.get('name','/')=='/':
			cd = {}
			if vals.get('entry_date',False):
				cd = {'date':datetime.strptime(vals['entry_date'],DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'letterofcredit') or '/'
		return super(loc, self).create(cr, uid, vals, context=context)    
	
	def onchange_partner_id(self,cr,uid,ids,partner_id,context=None):
		if not context:context={}
		val = {'parent_partner_id':False}
		if partner_id:
			partner = self.pool.get('res.partner').browse(cr,uid,partner_id,context)
			if partner.group_id:
				val.update({'parent_partner_id':partner.group_id.id})
		return {"value":val}

	def contract_order_change(self,cr,uid,ids,contract_ids,context=None):
		so_pooler = self.pool.get('sale.order')
		result={}
		so_ids=so_pooler.search(cr,uid,[('id','in',contract_ids[0][2])])
		so=so_pooler.browse(cr,uid,so_ids)
		if so:
			result['contract_incoterm']=[(x.incoterm.id!=False and x.incoterm.id) for x in so][0] or False
			result['contract_dest']=[(x.dest_port_id.id!=False and x.dest_port_id.id) for x in so][0] or False
			result['contract_payment_term']=[(x.payment_term.id!=False and x.payment_term.id) for x in so][0] or False
			if not result['contract_incoterm']:
				raise osv.except_osv(_('Amandement Warning!'), _('All your Sales Contract doesnt have information of its Incoterm, while it is required for this LC' ))
			if not result['contract_dest']:
				raise osv.except_osv(_('Amandement Warning!'), _('All your Sales Contract doesnt have information of its Destination Port, while it is required for this LC' ))
			if not result['contract_payment_term']:
				raise osv.except_osv(_('Amandement Warning!'), _('All your Sales Contract doesnt have information of its Payment Term, while it is required for this LC' ))

		return {'value':result}


	def contract_order_line_change(self, cr, uid, ids, contract_line_ids, contract_line2_ids, lc_product_lines, tolerance_percentage, context=None):
		line_pooler = self.pool.get('sale.order.line')

		lc_pooler = self.pool.get('letterofcredit')
		line2_pooler = self.pool.get('letterofcredit.contract.product.line')
		lc_product_line_pooler = self.pool.get('letterofcredit.product.line')
		result={
		'contract_product_ids':[],
		'lc_product_lines':[]
		}
		
		if contract_line2_ids:
			contract_line2_ids = [x for x in contract_line2_ids if x[0]!=0 or x[1]!=False]
			result['contract_product_ids']+=contract_line2_ids
		curr_sale_line_ids = []
		if lc_product_lines:
			lc_product_lines = [x for x in lc_product_lines if x[0]!=0 or x[1]!=False]
			result['lc_product_lines'] += lc_product_lines
			lc_product_lines_brw = lc_product_line_pooler.browse(cr, uid, [x[1] for x in lc_product_lines])
			curr_sale_line_ids+=[x.sale_line_id.id for x in lc_product_lines_brw if x.sale_line_id]
		selected_sale_line_ids = [x for x in contract_line_ids[0][2] if x not in curr_sale_line_ids]
		
		sale_line_ids = line_pooler.search(cr,uid,[('id','in',selected_sale_line_ids)],order="product_id,price_unit asc")
		product = False
		price = False
		cone_weight = 0.0
		sale_line = line_pooler.browse(cr,uid,sale_line_ids)
		if sale_line: 
			result['contract_lsd']=max([x.est_delivery_date for x in sale_line]) or False
		else:
			result['contract_lsd']=False

		for line in sale_line:
			result['contract_product_ids'].append((0,0,{
				'product_id' : line.product_id and line.product_id.id or False,
				'product_uom_qty' : line.product_uom_qty,
				'price_unit' : line.price_unit,
				'order_id' : line.order_id.id,
				'order_line_id' : line.id,
				'name' : line.name,
				'other_description' : line.export_desc and line.export_desc or '',
				'cone_weight' : line.cone_weight,
				'application' : line.application,
				'count_number' : line.count_number,
				'bom_id' : line.bom_id.id,
				'wax' : line.wax,
				'est_delivery_date' : line.est_delivery_date,
				'lc_id' : ids
				}))

			result['lc_product_lines'].append((0,0,{
				'sale_line_id' : line.id,
				'lc_id' : ids,
				'product_id':line.product_id.id,
				'price_unit':line.price_unit or 0.0,
				'product_uom_qty':line.product_uom_qty or 0.0,
				'application':line.application,
				'name':line.name,
				'cone_weight':line.cone_weight,
				'count_number':line.count_number,
				'bom_id':line.bom_id and line.bom_id.id or False,
				'wax':line.wax,
				'est_delivery_date' : line.est_delivery_date,
				'qty_outstanding' : line.product_uom_qty or 0.0,
				'min_tolerance' : ((100.0-(tolerance_percentage or 0.0))/100.0)*(line.product_uom_qty or 0.0),
				'qty_shipped' : 0.0,
				}))
		return {'value': result}

	def contract_purchase_order_line_change(self, cr, uid, ids, contract_line_ids, lc_product_lines, tolerance_percentage, context=None):
		line_pooler = self.pool.get('purchase.order.line')

		lc_pooler = self.pool.get('letterofcredit')
		lc_product_line_pooler = self.pool.get('letterofcredit.product.line')
		result={
			'lc_product_lines':[]
		}
		
		curr_purchase_line_ids = []
		if lc_product_lines:
			lc_product_lines = [x for x in lc_product_lines if x[0]!=0 or x[1]!=False]
			result['lc_product_lines'] += lc_product_lines
			lc_product_lines_brw = lc_product_line_pooler.browse(cr, uid, [x[1] for x in lc_product_lines])
			curr_purchase_line_ids+=[x.purchase_line_id.id for x in lc_product_lines_brw if x.purchase_line_id]
		selected_purchase_line_ids = [x for x in contract_line_ids[0][2] if x not in curr_purchase_line_ids]
		
		purchase_line_ids = line_pooler.search(cr,uid,[('id','in',selected_purchase_line_ids)],order="product_id,price_unit asc")
		product = False
		price = False
		cone_weight = 0.0
		purchase_line = line_pooler.browse(cr,uid,purchase_line_ids)
		for line in purchase_line:
			result['lc_product_lines'].append((0,0,{
				'purchase_line_id' : line.id,
				'lc_id' : ids,
				'product_id':line.product_id.id,
				'price_unit':line.price_unit or 0.0,
				'product_uom_qty':line.product_qty or 0.0,
				'name':line.name,
				'qty_outstanding' : line.product_qty or 0.0,
				'min_tolerance' : ((100.0-(tolerance_percentage or 0.0))/100.0)*(line.product_qty or 0.0),
				'qty_shipped' : 0.0,
				}))
		return {'value': result}

	def action_confirm(self,cr,uid,ids,context=None):
		if not context:context={}
		amd_obj=self.pool.get('letterofcredit.amandement.line')
		line2_pooler = self.pool.get('letterofcredit.contract.product.line')
		product_pooler = self.pool.get('letterofcredit.product.line')
		
		for lc in self.browse(cr,uid,ids,context):
			amd_ids=amd_obj.search(cr,uid,[('lc_id','=',lc.id),('type','=','default'),('state','=','draft')])
			amd_obj.unlink(cr,uid,amd_ids)
			if lc.lc_type=='in':
				continue
			flag1=False
			for line in lc.contract_product_ids:
				product_ids=product_pooler.search(cr,uid,[('lc_id','=',lc.id),('product_id','=',line.product_id.id),('price_unit','=',line.price_unit),('cone_weight','=',line.cone_weight)])
				if not product_ids:
					flag1=True

			for x in lc.lc_product_lines:
				line2_ids1=line2_pooler.search(cr,uid,[('lc_id','=',lc.id),('product_id','=',x.product_id.id),('price_unit','=',x.price_unit),('cone_weight','=',x.cone_weight)])
				if not line2_ids1:
					flag1=True

			if flag1 and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','0001'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'There are product that define on L/C but not defined on Contract or vice versa',
					'type':'default',
					'state':'draft',
					'code' : '0001',
					'lc_id':lc.id,
				})

			if lc.amount_total!=lc.lc_amount and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','0100'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'Total Amount on Contract is different with Amount in this L/C',
					'type':'default',
					'state':'draft',
					'code' : '0100',
					'lc_id':lc.id,
				})
			if lc.contract_incoterm.id!=lc.lc_incoterm.id and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','0101'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'Incoterm on Contract is different with Incoterm in this L/C',
					'type':'default',
					'state':'draft',
					'code' : '0101',
					'lc_id':lc.id,
				})
			if lc.contract_dest.id!=lc.lc_dest.id and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','0110'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'Destination Port on Contract is different with Destination Port in this L/C',
					'type':'default',
					'state':'draft',
					'code' : '0110',
					'lc_id':lc.id,
				})
			if lc.contract_lsd!=lc.lc_lsd and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','0111'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'Last Shipment Date on Contract is different with Last Shipment Date in this L/C',
					'type':'default',
					'state':'draft',
					'code' : '0111',
					'lc_id':lc.id,
				})
			if lc.contract_payment_term.id!=lc.lc_payment_term.id and not amd_obj.search(cr,uid,[('lc_id','=',lc.id),('code','=','1000'),('state','=','forced')]):
				amd_obj.create(cr,uid,{
					'desc': 'Payment Term on Contract is different with Payment Term in this L/C',
					'type':'default',
					'state':'draft',
					'code' : '1000',
					'lc_id':lc.id,
				})
		for lc in self.browse(cr,uid,ids,context):
			self.write(cr,uid,lc.id,{'state':'confirmed','prepared_by':uid})
		return True
	

	def action_review(self,cr,uid,ids,context=None):
		if not context:context={}
		amd_obj=self.pool.get('letterofcredit.amandement.line')
		line2_pooler = self.pool.get('letterofcredit.contract.product.line')
		product_pooler = self.pool.get('letterofcredit.product.line')
		
		for lc in self.browse(cr,uid,ids,context):
			if lc.lc_type=='in':
				self.write(cr,uid,lc.id,{'state':'checked','checked_by':uid})
				continue
			amd_ids=amd_obj.search(cr,uid,[('lc_id','=',lc.id),('type','=','default'),('state','=','draft')])
			action = {}

			if not amd_ids:
				amd_ids_2=amd_obj.search(cr,uid,[('manual_lc_id','=',lc.id),('type','=','additional'),('state','=','draft')])
				if not amd_ids_2:
					self.write(cr,uid,lc.id,{'state':'checked','checked_by':uid})
				else:
					raise osv.except_osv(_('Amandement Warning!'), _('There are some Additional Amandement Line that are not Approved yet. You can approve it one by one force this document to be Approve by buttons Force Riviewed'))
			else:
				raise osv.except_osv(_('Amandement Warning!'), _('There are some Additional Amandement Line that are not Approved yet. You can approve it one by one force this document to be Approve by buttons Force Riviewed'))
		return True

	def action_setdraft(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'draft'})

	def action_cancel(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'canceled'})

	def action_deactivate(self,cr,uid,ids,context=None):

		for id in ids:
			original = self.browse(cr, uid, id)
			parent = original.parent_id and original.parent_id or original
			childs = self.search(cr, uid, [('parent_id','=',parent.id)])
			
			next_rev_number = len(childs) + 1
			
			self.write(cr,uid,original.id,{'state':'nonactive'})

			default = {
				'state':'draft',
				'parent_id':parent.id,
				'name':parent and (parent.name + ' Rev. ' + str(next_rev_number)) or '/',
				'prev_revision_id':parent.id==original.id and False or original.id,
			}
			
			new_lc_id=self.copy(cr,uid,id,default,context)
			data_pool = self.pool.get('ir.model.data')
			action_model,action_id = data_pool.get_object_reference(cr, uid, 'ad_letter_of_credit', "action_letterofcredit_2")
			if action_model:
				action_pool = self.pool.get(action_model)
				action = action_pool.read(cr, uid, action_id, context=context)
				action['res_id'] = int(new_lc_id)
		
			return action
		return True

	def action_approve(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'approved','approved_by':uid})
loc()

class contract_order_lines(osv.osv):
	def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			price = line.price_unit * line.product_uom_qty
			res[line.id] = price
		return res

	_name = "letterofcredit.contract.product.line"
	_columns = {
		'order_id':fields.many2one('sale.order','SC No',readonly=True),
		# 'order_line_id':fields.many2many('sale.order.line','order_line_lc_line_rel','line_id','lc_line_id','Order Lines'),
		'order_line_id':fields.many2one('sale.order.line','Delivery Ref'),
		'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True,readonly=True),
		'name': fields.text('Description', required=True),
		'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'),readonly=True),
		'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
		'application'           : fields.selection([('knitting',"Knitting"),('weaving',"Weaving")],'Application'),
		'other_description'     : fields.text('Other Description'),
		'cone_weight'           : fields.float('Cone Weight',required=False),
		'count_number'          : fields.float('Count Number',required=False,help="Yarn Count Number"),
		'bom_id'                : fields.many2one('mrp.bom','Blend',required=False,help="Yarn Blend Code"),
		'wax'                   : fields.selection([('none','None'),('waxed',"Waxed"),('unwaxed',"Unwaxed")],'Wax',help="Select waxed if the product that will be sold is using wax"),
		'est_delivery_date'     : fields.date('Last Shipment Date'),
		'lc_id' : fields.many2one('letterofcredit','LC')
	}
contract_order_lines()

class loc_product_lines(osv.osv):
	def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		if context is None:
			context = {}
		for line in self.browse(cr, uid, ids, context=context):
			price = line.price_unit * line.product_uom_qty
			res[line.id] = price
		return res

	def _get_qty_shipped(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		uom_pool = self.pool.get('product.uom')
		for line in self.browse(cr,uid,ids,context):
			res[line.id] = {
				'qty_shipped' : 0.0,
				'qty_outstanding' : 0.0,
				'min_tolerance' : 0.0,
			}

			query = "SELECT a.id\
					FROM stock_move a\
					WHERE a.lc_product_line_id='%s'"%(line.id)
			cr.execute(query)

			query_res = cr.dictfetchall()
			move_ids = [x['id'] for x in query_res]
			move_lines = self.pool.get('stock.move').browse(cr, uid, move_ids)
			res[line.id]['qty_outstanding'] = line.product_uom_qty
			min_out_qty = ((100-(line.lc_id.tolerance_percentage and line.lc_id.tolerance_percentage or 0))/100 * line.product_uom_qty)
			res[line.id]['min_tolerance'] = min_out_qty
			if move_lines:
				for move in move_lines:
					if move.state == 'done':
						if (line.lc_type in ('tt','in') and move.location_id.usage=='internal' and move.location_dest_id.usage=='customer') or \
							(line.lc_type=='out' and move.location_id.usage=='supplier' and move.location_dest_id.usage=='internal'):
							sign = 1
						elif (line.lc_type in ('tt','in') and move.location_id.usage=='customer' and move.location_dest_id.usage=='internal') or \
							(line.lc_type=='out' and move.location_id.usage=='internal' and move.location_dest_id.usage=='supplier'):
							sign = -1
						else:
							sign = 0

						res[line.id]['qty_shipped'] += sign*uom_pool._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, line.sale_line_id.product_uom, context=context)
			res[line.id]['qty_outstanding'] -= res[line.id]['qty_shipped']
			if res[line.id]['qty_shipped'] > 0:
				res[line.id]['min_tolerance'] -= res[line.id]['qty_shipped']
		return res

	def _get_stock_moves_related(self, cr, uid, ids, context=None):
		res=[]
		for move in self.pool.get('stock.move').browse(cr, uid, ids):
			if move.lc_product_line_id and move.lc_product_line_id.id not in res:
				res.append(move.lc_product_line_id.id)
		return res

	def _get_stock_picking_related(self, cr, uid, ids, context=None):
		results=[]
		for picking in self.pool.get('stock.picking').browse(cr, uid, ids):
			sale_line_ids = [x.sale_line_id.id for x in picking.move_lines if x.sale_line_id]
			
			for lc in picking.lc_ids:
				if lc.state not in ('canceled','closed','nonactive'):
					for line in lc.lc_product_lines:
						if line.sale_line_id.id in sale_line_ids and line.id not in results:
							results.append(line.id)
		return results

	def _get_lc_related(self, cr, uid, ids, context=None):
		res=[]

		for lc in self.pool.get('letterofcredit').browse(cr, uid, ids):
			if lc.lc_product_lines:
				for line in lc.lc_product_lines:
					if line.id not in res:
						res.append(line.id)
		return res

	_name = "letterofcredit.product.line"
	_columns = {
		'sale_line_id' : fields.many2one('sale.order.line','Order Line', required=False),
		'purchase_line_id' : fields.many2one('purchase.order.line','Order Line', required=False),
		'sequence_line' : fields.related('sale_line_id','sequence_line',type='char',size=150,string='Order Line', store=True),
		'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
		'name': fields.text('Description', required=True),
		'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
		'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
		'application'           : fields.selection([('knitting',"Knitting"),('weaving',"Weaving")],'Application'),
		'other_description'     : fields.text('Remarks'),
		'cone_weight'           : fields.float('Cone Weight',required=False),
		'count_number'          : fields.float('Count Number',required=False,help="Yarn Count Number"),
		'bom_id'                : fields.many2one('mrp.bom','Blend',required=False,help="Yarn Blend Code"),
		'wax'                   : fields.selection([('none','None'),('waxed',"Waxed"),('unwaxed',"Unwaxed")],'Wax',help="Select waxed if the product that will be sold is using wax"),
		'lc_dest' : fields.many2one('res.port','Destination', required=False),
		'lc_dest_desc' : fields.char('Port Desc', size=50),
		'earliest_delivery_date' : fields.date('Earliest Shipment Date'),
		'est_delivery_date'     : fields.date('Last Shipment Date',required=False),
		'lc_id' : fields.many2one('letterofcredit','LC'),
		'lc_number' : fields.related('lc_id','lc_number',string='Lc Number', type='char', size=150,store=True),
		'lc_type' : fields.related('lc_id','lc_type',string='LC Type', type='selection',store=True, selection=[('tt','TT'),('in','IN'),('out','OUT')]),
		'hide' : fields.related('lc_id','hide',string='Hide this doc in the Report', type='boolean'),
		# 'move_lines':fields.one2many('stock.move','lc_product_line_id','Inventory Moves'),
		'delivery_term_txt' :fields.char('Delivery Term',size=100),
		
		'consignee' : fields.many2one('res.partner','Consignee/Buyer 1',domain=[('customer', '=', True)], required=False, help="Consignee for Bill of Loading"),
		'show_consignee_address' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text' : fields.text('Consignee Address Details 1'),
		'notify' : fields.many2one('res.partner','Notify Party 1',domain=[('customer', '=', True)], required=False, help="Notify for Bill of Loading"),
		'show_notify_address' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text' : fields.text('Notify Address Details 1'),

		'consignee_pl' : fields.many2one('res.partner','Consignee/Buyer 2',domain=[('customer', '=', True)], required=False, help="Consignee for Packing List/Commercial Invoice"),
		'show_consignee_address_pl' : fields.boolean('Use Customs Address Desc?'),
		'c_address_text_pl' : fields.text('Consignee Address Details 2'),
		'notify_pl' : fields.many2one('res.partner','Notify Party',domain=[('customer', '=', True)], required=False, help="Notify for Packing List/Commercial Invoice"),
		'show_notify_address_pl' : fields.boolean('Use Customs Address Desc?'),
		'n_address_text_pl' : fields.text('Notify Address Details 2'),
		
		'knock_off' : fields.boolean('Knock Off'),
		'date_knock_off' : fields.date('Date Knock Off'),
		'qty_shipped' : fields.function(_get_qty_shipped, type='float', string='Qty Shipped.', 
							store={
								'stock.picking' : (_get_stock_picking_related, ['lc_ids','move_lines'], 10),
								'stock.picking.out':(_get_stock_picking_related,['state','lc_ids'],11),
								'stock.move':(_get_stock_moves_related,['state','lc_product_line_id'],10),
							}, multi="lc_lines_qty"
							),
		'qty_outstanding' : fields.function(_get_qty_shipped, type='float', string='Qty Outstanding', 
							store={
								'stock.picking' : (_get_stock_picking_related, ['lc_ids','move_lines'], 10),
								'stock.picking.out':(_get_stock_picking_related,['state','lc_ids'],11),
								'stock.move':(_get_stock_moves_related,['state','lc_product_line_id'],10),
							}, multi="lc_lines_qty"
							),
		'min_tolerance' : fields.function(_get_qty_shipped, type='float', string='Qty Tolerance', 
							store={
								'stock.picking' : (_get_stock_picking_related, ['lc_ids','move_lines'], 10),
								'stock.picking.out':(_get_stock_picking_related,['state','lc_ids'],11),
								'stock.move':(_get_stock_moves_related,['state','lc_product_line_id'],10),
								'letterofcredit':(_get_lc_related,['tolerance_percentage'],10),
							}, multi="lc_lines_qty"
							),
		'state' : fields.related('lc_id','state',type='selection',selection=[
			('draft', 'Draft'),
			('confirmed','Need Review'),
			('checked','Need Approval'),
			('approved', 'Active'),
			('canceled', 'Cancelled'),
			('closed', 'Closed'),
			('nonactive', 'Non-Active'),
			], string='Status', readonly=True),
	}

	def onchange_consignee(self, cr, uid, ids, consignee_id, show_consignee_address, c_address_text):
		res = {
			'consignee_pl' : False,
			'show_consignee_address_pl' : False,
			'c_address_text_pl' : '',
		}
		if consignee_id:
			res['consignee_pl'] = consignee_id
		if show_consignee_address:
			res['show_consignee_address_pl'] = show_consignee_address
		if c_address_text:
			res['c_address_text_pl'] = c_address_text
		return {'value':res}

	def onchange_notify(self, cr, uid, ids, notify_id, show_notify_address, n_address_text):
		res = {
			'notify_pl' : False,
			'show_notify_address_pl' : False,
			'n_address_text_pl' : '',
		}
		if notify_id:
			res['notify_pl'] = consignee_id
		if show_notify_address:
			res['show_notify_address_pl'] = show_notify_address
		if n_address_text:
			res['n_address_text_pl'] = n_address_text
		return {'value':res}

	def name_get(self, cr, user, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
			ids = [ids]
		result = self.browse(cr, user, ids, context=context)
		res = []
		for rs in result:
			lc = False
			deliv_ref = False
			if rs.lc_id:
				lc = rs.lc_id
			if rs.sale_line_id:
				deliv_ref = rs.sale_line_id
			name = "%s%s"%(lc and '['+lc.lc_number+']' or '', deliv_ref and '['+deliv_ref.sequence_line+']' or '')
			res += [(rs.id, name)]
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [('lc_number', operator, name), ('sequence_line', operator, name)]
		else:
			domain = ['|', ('sequence_line', operator, name), ('lc_number', operator, name)]
		ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
		return self.name_get(cr, user, ids, context=context)

	def product_id_change(self, cr, uid, ids, product, context=None):
		result={}
		if not product:
			result['name']=''
			return{'value':result}
		product_obj = self.pool.get('product.product')
		product_obj = product_obj.browse(cr, uid, product, context=None)
		result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context)[0][1]
		if product_obj.description_sale:
			result['name'] += '\n'+product_obj.description_sale
		return {'value': result}

	def lc_dest_change(self, cr, uid, ids, lc_dest, context=None):
		result={}
		result['lc_dest_desc']=''
		if not lc_dest:
			return{'value':result}
		port_obj = self.pool.get('res.port')
		port = port_obj(cr, uid,lc_dest)
		result['lc_dest_desc']=port.name
		return {'value': result}

	def onchange_sale_line_id(self, cr, uid, ids, sale_line_id, context=None):
		if context is None:
			context={}

		if not sale_line_id:
			return {'value':{}}

		sale_line = self.pool.get('sale.order.line').browse(cr, uid, sale_line_id, context=context)
		result = {
			'product_id':sale_line.product_id.id,
			'price_unit':sale_line.price_unit or 0.0,
			'product_uom_qty':sale_line.product_uom_qty or 0.0,
			'application':sale_line.application,
			'name':sale_line.name,
			'cone_weight':sale_line.cone_weight,
			'count_number':sale_line.count_number,
			'bom_id':sale_line.bom_id and sale_line.bom_id.id or False,
			'wax':sale_line.wax,
		}

		return {'value':result}

	def button_knock_off(self, cr, uid, ids, context=None):
		res = self.write(cr, uid, ids, {'knock_off': True, 'date_knock_off': fields.date.context_today(self, cr, uid, context=context)})
		return True

loc_product_lines()

class loc_amandement_lines(osv.osv):
	_name = "letterofcredit.amandement.line"
	_columns = {
		'desc' : fields.text('Amandement'),
		'lc_id' : fields.many2one('letterofcredit','LC'),
		'code' : fields.char('Code',size=5),
		'manual_lc_id' : fields.many2one('letterofcredit','LC'),
		'type' : fields.selection([('default','Default'),('additional','Additional')],'Type'),
		'state' : fields.selection([('forced','Approved'),('draft','Amandement Required')],'State'),
	}
	_defaults = {
		'state' : 'draft',
		'type' : 'additional',
	}

	_order = "type desc" 

	def action_forced(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'forced'})
loc_amandement_lines()
