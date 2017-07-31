from openerp.osv import fields,osv

class account_invoice(osv.Model):
	_inherit = "account.invoice"
	_columns = {
	    'sale_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Order', readonly=True, help="This is the list of sales order source document"),
	    "goods_type"			: fields.selection([('finish','Finish Goods'),('finish_others','Finish Goods(Others)'),('raw','Raw Material'),('service','Services'),('stores','Stores'),('waste','Waste'),('scrap','Scrap'),('asset','Fixed Asset')],'Goods Type'),
		'sale_type'				: fields.selection([('export','Export'),('local','Local')],"Sale Type"),
		'locale_sale_type'		: fields.selection([('okb','Outside Kawasan Berikat'),('ikb','Inside Kawasan Berikat')],"Locale Sale Type"),
		'incoterms'				: fields.many2one('stock.incoterms','Incoterm Contract', readonly=False),
		'price_unit_digits'		: fields.integer("Price Unit Digits",help="Override this value to generate print digits in invoice, default 0 => 2 digits decimal"),
		'quantity_digits'		: fields.integer("Quantity Digits",help="Override this value to generate print digits in invoice, default 0 => 2 digits decimal"),
	}
