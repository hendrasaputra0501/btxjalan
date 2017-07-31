from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

class stock_picking(osv.Model):
	def _get_order_number(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		for picking in self.browse(cr,uid,ids,context):
			delivery_ref = ''
			if picking.move_lines:
				for move in picking.move_lines:
					if move.sequence_line and move.sequence_line not in delivery_ref:
						delivery_ref += (move.sequence_line and (move.sequence_line + ';') or '')
			res[picking.id]=delivery_ref

		return res
	def _get_existing_ref_number(self, cr, uid, ids, field, args, context=None):
		if not context:
			context={}
		res={}
		for picking in self.browse(cr,uid,ids,context):
			delivery_ref = ''
			if picking.move_lines:
				cont=[]
				for move in picking.move_lines:
					sp=move.sequence_line and move.sequence_line.split("-") or move.sale_line_id and move.sale_line_id.sequence_line.split("-") or  False
					# print "xxxxxxxxxxxxx",sp,sp[len(sp)-1]
					dump= (sp and sp[len(sp)-1].strip())  or False
					if dump:
						cont.append(dump)
						# print "----------------",dump
				cont=sorted(list(set(cont)))
				i=8
				while (i<len(cont)):
					cont.insert(i,"\n")
					i+=8
				if len(cont)>0:
					delivery_ref = str('; '.join([x for x in cont]))
					# print "delivery_ref==========",delivery_ref,type(delivery_ref)
					delivery_ref.replace('\n; ','\n')
					# print "delivery_ref==========",delivery_ref
			res[picking.id]=delivery_ref

		return res

	_inherit = "stock.picking"
	_columns = {
		'is_retur': fields.boolean("Retur?"),
		'sale_type': fields.selection([('export','Export'),('local','Local')],"Sale Type",required=False),
		'existing_sequence_number' : fields.function(_get_existing_ref_number, type='char',size=500,method=True, string='Existing Delivery Ref.'),
		'goods_type' : fields.selection([('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],
			'Goods Type',required=True),
		'order_number' : fields.function(_get_order_number, type='char', size=500, string='Delivery Ref.'),
		'lc_ids' : fields.many2many('letterofcredit','stock_picking_letterofcredit_rel','picking_id','lc_id',"Letter of Credit(s)"),
		}
	_defaults = {
		'sale_type':lambda *a:'export',
		'goods_type':lambda self, cr, uid, ctx:ctx.get('goods_type',False),
	}

	def _get_price_unit_invoice(self, cursor, user, move_line, type):
		if move_line.picking_id and move_line.picking_id.is_retur:
			return move_line.price_unit
		return super(stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)
		
	def check_credit_limit(self,cr,uid,ids,context=None):
		if not context:context={}
		picking =self.browse(cr,uid,ids)

		currency_pool = self.pool.get('res.currency')
		
		curr_amount_payable = 0.0
		if picking[0].sale_type=='local':
			for pick in picking:
				for line in pick.move_lines:
					if line.sale_line_id:
						curr_amount_payable += (line.sale_line_id.price_unit*line.product_qty)
				curr_amount_payable = currency_pool.compute(cr, uid, pick.sale_id.pricelist_id.currency_id.id, pick.company_id.currency_id.id, curr_amount_payable, context=context)
		else:
			for pick in picking:
				for line in pick.move_lines:
					if line.sale_line_id:
						curr_amount_payable += (line.sale_line_id.price_unit*line.product_qty)
				curr_amount_payable = currency_pool.compute(cr, uid, pick.sale_id.pricelist_id.currency_id.id, pick.company_id.currency_id.id, curr_amount_payable, context=context)

		if (curr_amount_payable+picking[0].partner_id.credit)>picking[0].partner_id.credit_limit:
			return False,(curr_amount_payable+picking[0].partner_id.credit)
		return True,False
		
	def check_overdue_limit(self,cr,uid,ids,context=None):	
		if not context:context={}
		picking =self.browse(cr,uid,ids)
		currency_pool = self.pool.get('res.currency')
		
		curr_amount_payable = 0.0
		if picking[0].sale_type=='local':
			for pick in picking:
				for line in pick.move_lines:
					if line.sale_line_id:
						curr_amount_payable += (line.sale_line_id.price_unit*line.product_qty)
				curr_amount_payable = currency_pool.compute(cr, uid, pick.sale_id.pricelist_id.currency_id.id, pick.company_id.currency_id.id, curr_amount_payable, context=context)
		else:
			for pick in picking:
				for line in pick.move_lines:
					if line.sale_line_id:
						curr_amount_payable += (line.sale_line_id.price_unit*line.product_qty)
				curr_amount_payable = currency_pool.compute(cr, uid, pick.sale_id.pricelist_id.currency_id.id, pick.company_id.currency_id.id, curr_amount_payable, context=context)
		
		if (curr_amount_payable+picking[0].partner_id.credit_overdue)>picking[0].partner_id.credit_overdue_limit:
			return False,(curr_amount_payable+picking[0].partner_id.credit_overdue)
		return True,False
		
	def lc_advance_check(self,cr,uid,ids,context=None):
		if not context:context={}
		try:
			picking =self.browse(cr,uid,ids)[0]
		except:
			picking =self.browse(cr,uid,ids)
		if picking.sale_id:
			if picking.sale_id.payment_method=='lc':
				if picking.sale_id.lc_ids:
					for lc_id in picking.sale_id.lc_ids:
						if lc_id.state != 'open':
							# LC is available but not validated yet by manager
							# Not Pass I
							return False
				else:
					# There are no LC verification yet
					# Not Pass I
					return False
			#else if payment method in cash or tt
			else:
				if picking.sale_id.advance_percentage > 0.0:
					amount_estimated = picking.sale_id.advance_percentage/100*picking.sale_id.amount_total
					if picking.sale_id.advance_ids:
						total_advance_paid = 0.0
						for advance_id in picking.sale_id.advance_ids:
							if advance_id.state=='posted':
								total_advance_paid+=advance_id.total_amount
						if total_advance_paid<amount_estimated:
							# Not Pass II
							return False
					else:
						# There are no Advance payment yet
						# Not Pass II
						return False
		return True
		
	def action_move(self, cr, uid, ids, context=None):
		"""Process the Stock Moves of the Picking
		
		This method is called by the workflow by the activity "move".
		Normally that happens when the signal button_done is received (button 
		"Done" pressed on a Picking view). 
		@return: True
		"""
		res = super(stock_picking,self).action_move(cr, uid, ids, context=context)
		for pick in self.browse(cr, uid, ids, context=context):
			todo = []
			for move in pick.move_lines:
				if move.state == 'draft':
					self.pool.get('stock.move').action_confirm(cr, uid, [move.id],
						context=context)
					todo.append(move.id)
				elif move.state in ('assigned','confirmed'):
					todo.append(move.id)
			if len(todo):
				self.pool.get('stock.move').action_done(cr, uid, todo,
						context=context)
		return res
	
	def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):

		if context is None:
			context = {}
		
		invoice_vals = super(stock_picking,self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)

		if picking:
			if picking.sale_id:
				invoice_vals.update({'goods_type':picking.sale_id.goods_type})
				invoice_vals.update({'sale_type':picking.sale_id.sale_type})
				invoice_vals.update({'locale_sale_type':picking.sale_id.locale_sale_type})
				invoice_vals.update({'incoterms':picking.sale_id.incoterm and picking.sale_id.incoterm.id or False})

		return invoice_vals

	def do_partial(self, cr, uid, ids, partial_datas, context=None):
		if context is None:
			context = {}
		res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas,context=context)
		delivered_picking_id = [int(val['delivered_picking']) for val in res.values() if val.get('delivered_picking',False)]
		picking = self.browse(cr, uid, delivered_picking_id[0])
		name_set = ''
		company_pooler = self.pool.get('res.company')
		company_code = ''
		goods_code = ''
		company_id = False
		month = ''

		# only for sales return
		if picking.is_retur and picking.type=='in':
			seq_obj_name =  self._inherit
			company_pooler = self.pool.get('res.company')
			company_id = picking.company_id	or self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id or False
			if company_id:
				company_code=company_id.prefix_sequence_code
			
			
			seq_obj_name += '.in'
			if picking.goods_type and picking.sale_type:
				goods_type = picking.goods_type
				if goods_type == 'finish_others':
					goods_type = "finisho"
				elif goods_type not in ('finish','raw','asset','stores','packing','service'):
					goods_type = 'others'
				seq_obj_name += '.'+picking.sale_type+'.'+goods_type
			name_set = company_code + self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)

			self.write(cr, uid, picking.id, {'name':name_set,'surat_jalan_number':name_set})
		return res

class stock_picking_in(osv.Model):
	_inherit = "stock.picking.in"
	_columns = {
		'is_retur': fields.boolean("Retur?"),
		'sale_type': fields.selection([('export','Export'),('local','Local')],"Sale Type",required=False),
		'goods_type' : fields.selection([('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],
			'Goods Type'),
	}

	def onchange_retur(self, cr, uid, ids, is_retur, context=None):
		if context is None:
			context = {}

		if is_retur:
			return {'value':{'invoice_state':'2binvoiced'}}
		else:
			return {'value':{}}

class stock_picking_out(osv.Model):
	_inherit = "stock.picking.out"
	def _get_order_number(self, cr, uid, ids, fields, args, context=None):
		if not context:
			context={}
		res={}
		for picking in self.browse(cr,uid,ids,context):
			delivery_ref = ''
			if picking.move_lines:
				for move in picking.move_lines:
					delivery_ref += move.sequence_line + ';'
			res[picking.id]=delivery_ref

		return res
	def _get_existing_ref_number(self, cr, uid, ids, field, args, context=None):
		if not context:
			context={}
		res={}
		print "----------------"
		for picking in self.browse(cr,uid,ids,context):
			delivery_ref = ''
			if picking.move_lines:
				for move in picking.move_lines:
					sp=move.sequence_line.split("-")
					delivery_ref += move.sale_line_id and move.sale_line_id.sequence_line_1 or sp[len(sp)-1].trim() + ';'
			res[picking.id]=delivery_ref

		return res

	_columns = {
		'sale_type': fields.selection([('export','Export'),('local','Local')],"Sale Type",required=False),
		'order_number' : fields.function(_get_order_number, type='char', size=500, string='Delivery Ref.'),
		'existing_sequence_number' : fields.function(_get_existing_ref_number, type='char',method=True, string='Existing Delivery Ref.'),
		"lc_ids" : fields.many2many('letterofcredit','stock_picking_letterofcredit_rel','picking_id','lc_id',"Letter of Credit(s)"),
		'goods_type' : fields.selection([('finish','Finish Goods'),
			('finish_others','Finish Goods(Others)'),
			('raw','Raw Material'),
			('service','Services'),
			('stores','Stores'),
			('waste','Waste'),
			('scrap','Scrap'),
			('packing','Packing Material'),
			('asset','Fixed Asset')],
			'Goods Type'),
		}
	_defaults = {
		'sale_type':lambda *a:'export',
	}

	# def create(self, cr, uid, vals, context=None):
	# 	res=super(stock_picking_out, self).create(cr, uid, vals, context=context)
	# 	picking_id = self.pool.get('stock.picking').browse(cr, uid, res)
	# 	if picking_id.sale_id:
	# 		company_code = ''

	# 		if picking_id.sale_id.company_id:
	# 			company_code=picking_id.sale_id.company_id.name[0:1]
			
	# 		if picking_id.sale_id.sale_type=='export':
	# 			self.pool.get('stock.picking').write(cr, uid, res ,{'name': (company_code+'E'+(self.pool.get('ir.sequence').get(cr, uid, self._inherit+'.export') or '/'))})
	# 		elif picking_id.sale_id.sale_type=='local':
	# 			self.pool.get('stock.picking').write(cr, uid, res ,{'name': (company_code+'L'+(self.pool.get('ir.sequence').get(cr, uid, self._inherit+'.local') or '/'))})
	# 	return res

class stock_move(osv.osv):
	_inherit='stock.move'

	def _get_stock_picking(self, cr, uid, ids, context=None):
		res=[]
		for picking in self.pool.get('stock.picking').browse(cr, uid, ids):
			for move in picking.move_lines:
				if move.id not in res:
					res.append(move.id)

		return res

	def _get_lc_product_line_id(self, cr, uid, ids, field_names, arg=None, context=None):
		if context is None:
			context = {}
		result = {}
		if not ids: return result
		for move in self.browse(cr,uid,ids):
			result[move.id] = {
				'lc_product_line_id': False,
			}
			lc_prod_line = []
			if move.picking_id and move.sale_line_id:
				for lc in move.picking_id.lc_ids:
					if lc.state not in ('canceled','closed','nonactive'):
						for line in lc.lc_product_lines:
							if line.sale_line_id == move.sale_line_id:
								lc_prod_line.append(line)
			result[move.id] = lc_prod_line and lc_prod_line[0].id or False
		return result

	def onchange_sale_line(self, cr, uid, ids, sale_line_id, context=None):
		if context is None:
			context = {}
		sale_line_pool = self.pool.get('sale.order.line')
		if sale_line_id:
			sale_line = sale_line_pool.browse(cr, uid, sale_line_id, context=context)
			return {'value':{'product_id':sale_line.product_id and sale_line.product_id.id or False}}
		else:
			return {'value':{}}

	_columns={
		'is_retur': fields.related('picking_id', 'is_retur', type='boolean',string="Retur?"),
		'sequence_line':fields.related('sale_line_id','sequence_line', type='char', size=50, string='Delivery Ref.', readonly=True, store=True),
		'sale_type' : fields.related('picking_id','sale_type',type='selection',selection=[('export','Export'),('local','Local')],string="Sale Type"),
		'lc_product_line_id' : fields.function(_get_lc_product_line_id,type='many2one', relation='letterofcredit.product.line',string='LC Line',
			store={
				'stock.picking' : (_get_stock_picking, ['lc_ids','move_lines'], 10),
				'stock.picking.out' : (_get_stock_picking, ['lc_ids','move_lines'], 10),
			}),
	}
