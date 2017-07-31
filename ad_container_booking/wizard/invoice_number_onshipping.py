from openerp.osv import fields, osv

from openerp.tools.translate import _

class invoice_number_onshipping(osv.osv_memory):
	_name = "invoice.number.onshipping"
	_description = "Stock Invoice Onshipping"

	_columns = {
		'group': fields.boolean("Group by partner"),
	}

	_defaults = {
		"group" : True,
	}

	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		res = super(invoice_number_onshipping, self).view_init(cr, uid, fields_list, context=context)
		pick_obj = self.pool.get('stock.picking')
		count = 0
		active_ids = context.get('active_ids',[])
		for pick in pick_obj.browse(cr, uid, active_ids, context=context):
			if pick.sale_type != 'export':
				raise osv.except_osv(_('Warning!'), _('This Functions is only for Export Sales.\n Maybe you mean to create Invoice.\n Dont click Generate Draft Invoice Number.\n Please try again and click Create Draft Invoice. \n'))
			if pick.draft_invoice_number:
				count += 1
		if len(active_ids) == 1 and count:
			raise osv.except_osv(_('Warning!'), _('This picking list does not require invoicing.'))
		if len(active_ids) == count:
			raise osv.except_osv(_('Warning!'), _('None of these picking lists require invoicing.'))
		return res

	def generate_invoice_draft(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		data_pool = self.pool.get('ir.model.data')
		
		self.generate_invoice_number(cr, uid, ids, context=context)
		
		return {'type': 'ir.actions.act_window_close'}

	def generate_invoice_number(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		picking_pool = self.pool.get('stock.picking')
		onshipdata_obj = self.read(cr, uid, ids, ['group'])
		active_ids = context.get('active_ids', [])
		active_picking = picking_pool.browse(cr, uid, active_ids, context=context)
		number = ''
		inv_type = picking_pool._get_invoice_type(active_picking[0])
		if inv_type and inv_type in ['out_invoice','out_refund']:
			invoices_group = {}
			for picking in active_picking:
				if picking.invoice_state != '2binvoiced':
					continue
				partner = picking_pool._get_partner_to_invoice(cr, uid, picking, context=context)
				if not partner:
					raise osv.except_osv(_('Error, no partner!'),
						_('Please put a partner on the picking list if you want to generate invoice.'))
				if onshipdata_obj[0]['group'] and partner.id in invoices_group:
					inv_number = invoices_group[partner.id]
				else:
					inv_number = ''
					company_id = picking.company_id
					company_code = ''
					goods_type = ''
					if company_id:
						company_code=company_id.prefix_sequence_code
					
					if picking.sale_id:
						sale=picking.sale_id
						goods_type = sale.goods_type
						cd = {'date':picking.date_done}
						if goods_type not in ('finish','finish_others','raw','asset','stores','packing','service'):
							goods_type = 'others'
						inv_number = company_code+(self.pool.get('ir.sequence').get(cr, uid, 'invoice.'+sale.sale_type+'.'+goods_type, context=cd) or '/')
					invoices_group[partner.id] = inv_number
				picking_pool.write(cr, uid, [picking.id], {
					'draft_invoice_number': inv_number,
					}, context=context)
		return True

invoice_number_onshipping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
