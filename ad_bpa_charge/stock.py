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
import logging
_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
	_inherit = "stock.picking"
	_columns = {
		"freight_invoice_id":fields.many2one("account.invoice","Invoice Freight Charge"),
		"trucking_invoice_id":fields.many2one("account.invoice","Invoice Trucking Charge"),
		"lifton_bpa_id":fields.many2many("ext.transaksi",'picking_lifton_bpa_rel','bpa_id','picking_id',"Lift On BPA"),
		"kbkb_bpa_id":fields.many2many("ext.transaksi",'picking_kbkb_bpa_rel','bpa_id','picking_id',"KBKB BPA"),
	}
	
	def _prepare_expense_transport_invoice_line(self, cr, uid, group, picking, charge, invoice_id,
		invoice_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: forwading_charge: forwading_charge object
			@param: invoice_id: ID of the related invoice
			@param: invoice_vals: dict used to created the invoice
			@return: dict that will be used to create the invoice line
		"""
		if context is None:
			context={}

		if charge.transporter_id.type=='container':
			# name =  (charge.name or '' ) + ' - Freight for ' + (picking.name or '')
			name =  (picking.invoice_id and picking.invoice_id.internal_number and picking.invoice_id.internal_number + ' : ' or '') + (picking.name or '')
		else:
			# name =  (charge.name or '' ) + ' - EMKL for ' + (picking.name or '')
			name =  (picking.invoice_id and picking.invoice_id.internal_number and picking.invoice_id.internal_number + ' : ' or '') + (picking.name or '')
			
		origin = charge.name or ''
		
		# if charge.transporter_id.account_id:
		# 	account_id=charge.transporter_id.account_id.id
		# else:
		# 	raise osv.except_osv(_('Error, no expense account!'),
		# 		_('Please put an account on the freight expense account if you want to accrue as expense.'))
		
		qty = 1
		uos_id = False
		invoice_currency = invoice_vals['currency_id'] or False
		freight_cost_currency = charge.currency_id and charge.currency_id.id or False
		uom_obj = self.pool.get('product.uom')
		if invoice_currency and freight_cost_currency:
			if charge.cost_type == 'type1':
				qty = 0
				for move in picking.move_lines:
					qty += uom_obj._compute_qty(cr, uid, move.product_uom.id, move.gross_weight and move.gross_weight or move.product_qty, charge.uom_id.id)
				uos_id = charge.uom_id.id
			context.update({'date': invoice_vals['date_invoice'] or time.strftime('%Y-%m-%d')})
			freight_cost = self.pool.get('res.currency').compute(cr, uid, freight_cost_currency, invoice_currency, charge.cost, context=context)
		else:
			freight_cost = charge.cost

		charge_type=False
		charge_type_ids=[]
		if charge.transporter_id.type=='container':
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','Freight')])
		elif charge.transporter_id.type=='trucking' and not context.get('transport',False):
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','EMKL')])
		elif context.get('transport',False):
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','Transport')])
			
		charge_type = charge_type_ids and self.pool.get('charge.type').browse(cr, uid, charge_type_ids)[0] or False
		charge_type_id = charge_type and charge_type.id or False
		account_id = charge_type and (charge_type.account_id and charge_type.account_id.id or account_id) or False
		
		return {
			'name': name,
			'type_of_charge' : charge_type_id,
			'invoice_related_id' : picking.invoice_id and picking.invoice_id.id or False,
			'picking_related_id' : picking.id,
			'origin': origin,
			'invoice_id': invoice_id,
			'uos_id': uos_id,
			'product_id': False,
			'account_id': account_id,
			'price_unit': freight_cost,
			'quantity': round(qty,2),
		}

	def _prepare_expense_transport_less_load_inv_line(self, cr, uid, group, picking, charge, invoice_id,
		invoice_vals, line_vals, context=None):
		""" Builds the dict containing the values for the invoice line
			@param group: True or False
			@param picking: picking object
			@param: forwading_charge: forwading_charge object
			@param: invoice_id: ID of the related invoice
			@param: invoice_vals: dict used to created the invoice
			@return: dict that will be used to create the invoice line
		"""
		if context is None:
			context={}
		
		date_deliver = datetime.strptime(picking.date_done,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
		key = (picking.truck_number and (picking.truck_number.encode('utf-8')+':'+date_deliver) or picking.name.encode('utf-8'),invoice_vals['partner_id'])
		if key not in line_vals:
			line_vals.update({key:{
							'name': context.get('dispensation',False) and 'Dispensation of ' or 'Less Loading of ',
							'type_of_charge' : False,
							'invoice_related_id' : False,
							'picking_related_id' : False,
							'origin': False,
							'invoice_id': False,
							'uos_id': False,
							'product_id': False,
							'account_id': False,
							'price_unit': 0.0,
							'quantity': 0.0,	
							}})

		qty = 1
		uos_id = False
		invoice_currency = invoice_vals['currency_id'] or False
		transport_cost_currency = charge.currency_id and charge.currency_id.id or False
		uom_obj = self.pool.get('product.uom')
		if invoice_currency and transport_cost_currency:
			if charge.cost_type == 'type1':
				qty = 0
				for move in picking.move_lines:
					qty += uom_obj._compute_qty(cr, uid, move.product_uom.id, move.gross_weight and move.gross_weight or move.product_qty, charge.uom_id.id)
				uos_id = charge.uom_id.id
				line_vals[key]['quantity'] += round(qty,2)
				line_vals[key]['uos_id'] = uos_id
			else:
				line_vals[key]['quantity'] = qty
			context.update({'date': invoice_vals['date_invoice'] or time.strftime('%Y-%m-%d')})
			price_unit = self.pool.get('res.currency').compute(cr, uid, transport_cost_currency, invoice_currency, charge.cost, context=context)
			
			min_load_qty = picking.truck_type and uom_obj._compute_qty(cr, uid, picking.truck_type.uom_id.id, (picking.truck_type.min_uom_qty or 0.0), charge.uom_id.id)
			price_unit = (((min_load_qty and min_load_qty or line_vals[key]['quantity']) - line_vals[key]['quantity']) * price_unit) / line_vals[key]['quantity']
			if context.get('dispensation',False):
				line_vals[key]['quantity'] = 1
				price_unit = self.pool.get('res.currency').compute(cr, uid, transport_cost_currency, invoice_currency, charge.dispensation_cost, context=context)
		else:
			price_unit = charge.cost
			line_vals[key]['quantity'] = qty
			if context.get('dispensation',False):
				price_unit = charge.dispensation_cost

		line_vals[key]['invoice_related_id'] = line_vals[key]['invoice_related_id'] and line_vals[key]['invoice_related_id'] or (picking.invoice_id and picking.invoice_id.id or False)
		line_vals[key]['picking_related_id'] = line_vals[key]['picking_related_id'] and line_vals[key]['picking_related_id'] or (picking.id or False)
		line_vals[key]['name'] = line_vals[key]['name'] and (line_vals[key]['name']+'; '+(picking.name or '')) or (picking.name or '')
		line_vals[key]['origin'] = charge.name or ''
		line_vals[key]['price_unit'] = price_unit

		charge_type=False
		charge_type_ids=[]
		if charge.transporter_id.type=='container':
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','Freight')])
		elif charge.transporter_id.type=='trucking' and not context.get('transport',False) and not context.get('transport_less_load',False) and not context.get('dispensation',False):
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','EMKL')])
		elif context.get('transport',False) or context.get('transport_less_load',False) or context.get('dispensation',False):
			charge_type_ids = self.pool.get('charge.type').search(cr, uid, [('name','=','Transport')])
		
		line_vals[key]['type_of_charge'] = line_vals[key]['type_of_charge'] and line_vals[key]['type_of_charge'] or charge_type_ids[0]

		charge_type = charge_type_ids and self.pool.get('charge.type').browse(cr, uid, charge_type_ids)[0] or False
		charge_type_id = charge_type and charge_type.id or False
		account_id = charge_type and (charge_type.account_id and charge_type.account_id.id or account_id) or False
		
		line_vals[key]['account_id'] = line_vals[key]['account_id'] and line_vals[key]['account_id'] or account_id
		line_vals[key]['invoice_id'] = line_vals[key]['invoice_id'] and line_vals[key]['invoice_id'] or invoice_id
		return line_vals

	def action_freight_invoice_create(self, cr, uid, ids, journal_id=False, group=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: ID of journal,
		@param group: Whether to create a group stuffing memo or not
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		partner_obj = self.pool.get('res.partner')
		invoices_group = {}
		inv_type='in_invoice'
		res = {}
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.freight_invoice_id:
				continue
			partner = picking.forwading and picking.forwading.partner_id.id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the transporter data if you want to generate invoice.'))
			
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
				del invoice_vals['payment_term']
				invoice_vals.update({'charge_type':'sale','payment_term':False, 'currency_tax_id': picking.company_id.currency_id.id})
				if context.get('currency_id',False):
					invoice_vals.update({'currency_id':context.get('currency_id',False)})
				if context.get('number',False):
					invoice_vals.update({'reference':context.get('number',False)})
				invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
				invoices_group[partner.id] = invoice_id

			res[picking.id] = invoice_id
			
			if picking.forwading_charge:
				vals = self._prepare_expense_transport_invoice_line(cr, uid, group, picking, picking.forwading_charge,
								invoice_id, invoice_vals, context=context)
				if vals:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
					
			invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
					set_total=(inv_type in ('in_invoice', 'in_refund')))
			self.write(cr, uid, [picking.id], {
				'freight_invoice_id': invoice_id,
				}, context=context)
			# run the trigger of freight charge to compute total freigth cost
			invoice_obj.write(cr, uid, invoice_id, {'state':'draft'})
			
		return res

	def action_trucking_invoice_create(self, cr, uid, ids, journal_id=False, group=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: ID of journal,
		@param group: Whether to create a group stuffing memo or not
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		partner_obj = self.pool.get('res.partner')
		invoices_group = {}
		inv_type='in_invoice'
		res = {}
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.trucking_invoice_id:
				continue
			partner = picking.trucking_company and picking.trucking_company.partner_id.id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the transporter data if you want to generate invoice.'))
			
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
				del invoice_vals['payment_term']
				invoice_vals.update({'charge_type':'sale','payment_term':False, 'currency_tax_id': picking.company_id.currency_id.id})
				if context.get('currency_id',False):
					invoice_vals.update({'currency_id':context.get('currency_id',False)})
				if context.get('number',False):
					invoice_vals.update({'reference':context.get('number',False)})
				invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
				invoices_group[partner.id] = invoice_id

			res[picking.id] = invoice_id
			
			if picking.trucking_charge:
				vals = self._prepare_expense_transport_invoice_line(cr, uid, group, picking, picking.trucking_charge,
								invoice_id, invoice_vals, context=context)
				if vals:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
					
			invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
					set_total=(inv_type in ('in_invoice', 'in_refund')))
			self.write(cr, uid, [picking.id], {
				'trucking_invoice_id': invoice_id,
				}, context=context)
		
		return res

	def action_transport_invoice_create(self, cr, uid, ids, journal_id=False, group=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: ID of journal,
		@param group: Whether to create a group stuffing memo or not
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		partner_obj = self.pool.get('res.partner')
		invoices_group = {}
		inv_type='in_invoice'
		res = {}
		line_vals = {}
		invoice_ids = []
		for picking in self.browse(cr, uid, ids, context=context):
			if picking.trucking_invoice_id and not context.get('transport_less_load',False) and not context.get('dispensation',False):
			# if not context.get('transport_less_load',False) and not context.get('dispensation',False):
				continue
			partner = picking.trucking_company and picking.trucking_company.partner_id.id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the transporter data if you want to generate invoice.'))
			
			if group and partner.id in invoices_group:
				invoice_id = invoices_group[partner.id]
				invoice = invoice_obj.browse(cr, uid, invoice_id)
				invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
				invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
			else:
				invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
				del invoice_vals['payment_term']
				invoice_vals.update({'charge_type':'sale','payment_term':False, 'currency_tax_id': picking.company_id.currency_id.id})
				if context.get('currency_id',False):
					invoice_vals.update({'currency_id':context.get('currency_id',False)})
				if context.get('number',False):
					invoice_vals.update({'reference':context.get('number',False)})
				invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
				invoices_group[partner.id] = invoice_id

			res[picking.id] = invoice_id
			if invoice_id not in invoice_ids:
				invoice_ids.append(invoice_id)
			if picking.trucking_charge and not context.get('transport_less_load',False) and not context.get('dispensation',False):
				vals = self._prepare_expense_transport_invoice_line(cr, uid, group, picking, picking.trucking_charge,
								invoice_id, invoice_vals, context=context)
				if vals:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
			elif picking.trucking_charge and (context.get('transport_less_load',False) or context.get('dispensation',False)):
				line_vals = self._prepare_expense_transport_less_load_inv_line(cr, uid, group, picking, picking.trucking_charge,
								invoice_id, invoice_vals, line_vals, context=context)
			
			if not context.get('transport_less_load',False):
				self.write(cr, uid, [picking.id], {
					'trucking_invoice_id': invoice_id,
					}, context=context)
		if line_vals:
			for vals in line_vals.values():
				if vals and vals.get('price_unit',0.0)>0.0:
					invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
		invoice_obj.button_compute(cr, uid, invoice_ids, context=context,
			set_total=(inv_type in ('in_invoice', 'in_refund')))
		return res

	def action_kbkb_bpa_create(self, cr, uid, ids, journal_id=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: ID of journal,
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		bpa_obj = self.pool.get('ext.transaksi')
		bpa_line_obj = self.pool.get('ext.transaksi.line')
		partner_obj = self.pool.get('res.partner')
		charge_type_obj = self.pool.get('charge.type')
		uom_obj = self.pool.get('product.uom')
		current_bpa_id=False
		res = {}
		for picking in self.browse(cr, uid, ids, context=context):
			
			partner = picking.porters and picking.porters.name.id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the transporter data if you want to generate invoice.'))
			
			date=context.get('bpa_date', False)
			bpa_currency = context.get('currency_id',False)
			if current_bpa_id:
				bpa_id=current_bpa_id
			else:
				bpa_id = bpa_obj.create(cr, uid, {
					'name' : '/',
					'journal_id': journal_id and journal_id or False,
					'ref': '',
					'request_date': date,
					'due_date':context.get('due_date', False),
					'currency_id':bpa_currency,
					'number':context.get('number',False),
					'is_bpa':True,
					}, context=context)
				res[picking.id] = bpa_id
				current_bpa_id=bpa_id
			type_of_charge_ids=[]

			if picking.type=='out':
				if picking.sale_type == 'export' :
					type_of_charge_ids=charge_type_obj.search(cr, uid, [('trans_type','=','sale'),('sale_type','=','export'),('name','=','Finish Good Handling Export')])
				if picking.sale_type == 'local' :
					type_of_charge_ids=charge_type_obj.search(cr, uid, [('trans_type','=','sale'),('sale_type','=','local'),('name','=','Finish Good Handling Local')])
			else:
				type_of_charge_ids=charge_type_obj.search(cr, uid, [('trans_type','=','purchase'),('purchase_type','=','local'),('code','=','RMKB')])

			type_of_charge_id=False
			account_id=False
			if type_of_charge_ids:
				type_of_charge=charge_type_obj.browse(cr, uid, type_of_charge_ids)[0]
				type_of_charge_id=type_of_charge.id
				account_id = type_of_charge.account_id and type_of_charge.account_id.id or False
			
			# calculate the cost
			amount = 0.0
			total_qty_onporters = 0.0
			for move in picking.move_lines:
				total_qty_onporters += uom_obj._compute_qty(cr, uid, (picking.type=='out' and move.product_uom.id or move.product_uop.id), (picking.type=='out' and move.product_qty or move.product_uop_qty), picking.porters_charge.uom_id.id)

			if bpa_currency:
				context.update({'date': date or time.strftime('%Y-%m-%d')})
				amount = self.pool.get('res.currency').compute(cr, uid, picking.porters_charge.currency_id.id, bpa_currency, (picking.porters_charge.cost*total_qty_onporters), context=context)

			bpa_line_id = bpa_line_obj.create(cr, uid, {
					'type_of_charge': type_of_charge_id,
					'account_id' : account_id,
					'invoice_related_id' : picking.invoice_id and picking.invoice_id.id,
					'picking_related_id' : picking.id,
					'name' : 'KBKB Charge'+(picking.type=='out' and ' for DO No. ' or (picking.type=='in' and ' for MRR No. ' or ''))+picking.name,
	   				'ext_transaksi_id': bpa_id,
					'debit': amount,
					'partner_id': partner.id,
					}, context=context)
			cek_kbkb_bpa_id=False
			for bpa in picking.kbkb_bpa_id:
				if bpa and bpa.id==bpa_id:
					cek_kbkb_bpa_id=True

			if not cek_kbkb_bpa_id:
				self.write(cr, uid, picking.id, {'kbkb_bpa_id':[(4,bpa_id)]})
		return res

	def action_lifton_bpa_create(self, cr, uid, ids, journal_id=False, context=None):
		""" Creates invoice based on the invoice state selected for picking.
		@param journal_id: ID of journal,
		@return: Ids of created stuffing memos for the pickings
		"""
		if context is None:
			context = {}

		bpa_obj = self.pool.get('ext.transaksi')
		bpa_line_obj = self.pool.get('ext.transaksi.line')
		partner_obj = self.pool.get('res.partner')
		charge_type_obj = self.pool.get('charge.type')
		current_bpa_id=False
		res = {}
		for picking in self.browse(cr, uid, ids, context=context):
			
			partner = picking.trucking_company and picking.trucking_company.partner_id.id
			if isinstance(partner, int):
				partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
			if not partner:
				raise osv.except_osv(_('Error, no partner!'),
					_('Please put a partner on the transporter data if you want to generate invoice.'))
			
			date=context.get('bpa_date', False)
			if current_bpa_id:
				bpa_id=current_bpa_id
			else:
				bpa_id = bpa_obj.create(cr, uid, {
					'name' : '/',
					'journal_id': journal_id and journal_id or False,
					'ref': '',
					'is_bpa':True,
					'request_date': date,
					'due_date': context.get('due_date',False),
					'currency_id':context.get('currency_id',False),
					'number':context.get('number',False),
					}, context=context)
				res[picking.id] = bpa_id
				current_bpa_id=bpa_id

			type_of_charge_ids=charge_type_obj.search(cr, uid, [('name','=','Lift On Lift Off')])
			type_of_charge_id=False
			account_id=False
			if type_of_charge_ids:
				type_of_charge=charge_type_obj.browse(cr, uid, type_of_charge_ids)[0]
				type_of_charge_id=type_of_charge.id
				account_id=type_of_charge.account_id and type_of_charge.account_id.id or False
			
			bpa_line_id = bpa_line_obj.create(cr, uid, {
					'type_of_charge': type_of_charge_id,
					'account_id':account_id,
					'invoice_related_id' : picking.invoice_id and picking.invoice_id.id,
					'picking_related_id' : picking.id,
					'name' : 'Lift On Lift Off for Invoice ' + picking.invoice_id.internal_number,
	   				'ext_transaksi_id': bpa_id,
					'debit': 0.0,
					'partner_id': partner.id,
					}, context=context)
			cek_lifton_bpa_id=False
			for bpa in picking.lifton_bpa_id:
				if bpa and bpa.id==bpa_id:
					cek_lifton_bpa_id=True

			if not cek_lifton_bpa_id:
				self.write(cr, uid, picking.id, {'lifton_bpa_id':[(4,bpa_id)]})
		return res


class stock_picking_out(osv.osv):
	_inherit = "stock.picking.out"
	_columns = {
		"freight_invoice_id":fields.many2one("account.invoice","Invoice Freight Charge"),
		"trucking_invoice_id":fields.many2one("account.invoice","Invoice Trucking Charge"),
		"lifton_bpa_id":fields.many2many("ext.transaksi",'picking_lifton_bpa_rel','bpa_id','picking_id',"Lift On BPA"),
		"kbkb_bpa_id":fields.many2many("ext.transaksi",'picking_kbkb_bpa_rel','bpa_id','picking_id',"KBKB BPA"),
	}

stock_picking_out()
