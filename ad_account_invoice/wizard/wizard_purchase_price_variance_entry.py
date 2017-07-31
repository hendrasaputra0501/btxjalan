from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc

class wizard_purchase_price_variance_entry(osv.osv_memory):
	_name = "wizard.purchase.price.variance.entry"
	_columns = {
		'account_id':fields.many2one('account.account','Account PPV', required=True),
		'invoice_lines':fields.one2many('wizard.account.invoice.line','wizard_id','Invoice Lines', required=True),
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(wizard_purchase_price_variance_entry, self).view_init(cr, uid, fields_list, context=context)
		invoice_pool = self.pool.get('account.invoice')
		inv_id = context.get('active_id',False)
		if not inv_id:
			raise osv.except_osv(_('Error!'), _('Please Select the invoice that you want to input its PPVs'))
		inv = invoice_pool.browse(cr, uid, inv_id, context=context)
		if inv.state in ('open','paid','cancel'):
			raise osv.except_osv(_('Warning!'), _('This Invoice was already generate Journal Entries. Please Cancel this invoice and then try to input its PPV again.'))
		return res

	def _prepare_invoice_lines(self, cr, uid, line):
		res = {
			'invoice_line_id' : line.id,
			'product_id' : line.product_id and line.product_id.id or False,
			'name' : line.name,
			'price_unit' : line.price_unit,
			'invoice_line_tax_id' : [x.id for x in line.invoice_line_tax_id],
			}
		return res

	def default_get(self, cr, uid, fields_list, context=None):
		"""
		Returns default values for fields
		@param fields_list: list of fields, for which default values are required to be read
		@param context: context arguments, like lang, time zone

		@return: Returns a dict that contains default values for fields
		"""
		res = super(wizard_purchase_price_variance_entry, self).default_get(cr, uid, fields_list, context=context)
		if context is None:
			context = {}
		inv_id = context.get('active_id',False)
		invoice_line_pool = self.pool.get('account.invoice.line')
		if not inv_id:
			raise osv.except_osv(_('Error!'), _('Please Select the invoice that you want to input its PPVs'))
		invoice_line_ids = invoice_line_pool.search(cr,uid,[('invoice_id','=',inv_id),('is_ppv_entry','=',False)])
		if 'invoice_lines' in fields_list:
			invoice_lines = [self._prepare_invoice_lines(cr, uid, line) for line in invoice_line_pool.browse(cr, uid, invoice_line_ids)]
			res.update(invoice_lines=invoice_lines)
		return res

	def set_ppv_entries(self, cr, uid, ids, context=None):
		if context is None: context = {}
		
		invoice_line_pool = self.pool.get('account.invoice.line')
		invoice_pool = self.pool.get('account.invoice')

		inv_id = context.get('active_id',False)
		data = self.read(cr, uid, ids, ['account_id','invoice_lines'])
		if not data:
			return False
		data_line = self.pool.get('wizard.account.invoice.line').browse(cr, uid, data[0].get('invoice_lines',[]))
		if not data[0].get('account_id',False) and not data_line:
			return False
		ppv_line_ids = invoice_line_pool.search(cr,uid,[('invoice_id','=',inv_id),('is_ppv_entry','=',True)])
		if ppv_line_ids:
			invoice_line_pool.unlink(cr, uid, ppv_line_ids)
		
		# group invoice line : group by invoice_line_tax_id, picking_id
		invoice_line_grouped = {}
		for line in data_line:
			if line.invoice_line_id.price_unit == line.price_unit:
				continue
			tax_ids = map(lambda x:x.id, line.invoice_line_id.invoice_line_tax_id)
			picking_id = line.invoice_line_id.move_line_ids and line.invoice_line_id.move_line_ids[0].picking_id and line.invoice_line_id.move_line_ids[0].picking_id.id or False
			account_id = line.invoice_line_id.account_id.id
			key = (account_id, ','.join(map(lambda t: str(t), tax_ids)), picking_id)
			if key not in invoice_line_grouped.keys():
				invoice_line_grouped.update({
					key:[{
							'is_ppv_entry' : True,
							'invoice_id' : line.invoice_line_id.invoice_id.id,
							'invoice_related_id' : line.invoice_line_id.invoice_id.id,
							'picking_related_id' : picking_id,
							'name' : 'Entry PPV for account %s %s'%(line.invoice_line_id.account_id.name, (picking_id and "and picking no. %s"%(line.invoice_line_id.move_line_ids[0].picking_id.name) or "")),
							'account_id' : data[0]['account_id'][0], 
							'quantity' : 1.0,
							'price_unit' : 0.0,
							'invoice_line_tax_id' : [(6, 0, tax_ids)]
						},{
							'is_ppv_entry' : True,
							'invoice_id' : line.invoice_line_id.invoice_id.id,
							'name' : 'Counter-part PPV Entry for account %s'%(line.invoice_line_id.account_id.name),
							'account_id' : account_id, 
							'quantity' : 1.0,
							'price_unit' : 0.0,
							'invoice_line_tax_id' : [(6, 0, tax_ids)]
						}]
					})
			invoice_line_grouped[key][0]['price_unit'] += (line.price_subtotal - line.invoice_line_id.price_subtotal)
			invoice_line_grouped[key][1]['price_unit'] += -1*(line.price_subtotal - line.invoice_line_id.price_subtotal)
		new_lines = []
		for value in invoice_line_grouped.values():
			new_lines.append(value[0])
			new_lines.append(value[1])
		for l in new_lines:
			invoice_line_pool.create(cr, uid, l)
		for line in data_line:
			if line.invoice_line_id.price_unit == line.price_unit:
				continue
			invoice_line_pool.write(cr, uid, line.invoice_line_id.id, {'price_unit':line.price_unit})
		invoice_pool.button_reset_taxes(cr, uid, [inv_id])
		return True

wizard_purchase_price_variance_entry()

class wizard_account_invoice_line(osv.osv_memory):
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit * (1-(line.invoice_line_id.discount or 0.0)/100.0)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.invoice_line_id.quantity, product=line.invoice_line_id.product_id, partner=line.invoice_line_id.invoice_id.partner_id)
			res[line.id] = taxes['total']
			if line.invoice_line_id.invoice_id:
				cur = line.invoice_line_id.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res
	
	_name = "wizard.account.invoice.line"
	_columns = {
		'wizard_id':fields.many2one('wizard.purchase.price.variance.entry','Wizard'),
		'invoice_line_id':fields.many2one('account.invoice.line','Invoice Line', readonly=True, required=True),
		'product_id':fields.many2one('product.product','Product', readonly=True),
		'name':fields.text('Description',required=True, readonly=True),
		'price_unit':fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
		'invoice_line_tax_id': fields.many2many('account.tax', 'wizard_ppv_account_invoice_line_tax', 'wizard_invoice_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)], readonly=True),
		'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
			digits_compute= dp.get_precision('Account')),
	}
wizard_account_invoice_line()