from openerp.osv import fields, osv

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class wizard_sale_order_agent(osv.osv_memory):
	_name = "wizard.sale.order.agent"

	_columns = {
		"agent_id" : fields.many2one('res.partner','Agent'),
		# "partner_id" : fields.many2one('res.partner','Partner Company'),
		"invoice_partner_id" : fields.many2one('res.partner','Payment To'),
		"commission_percentage" : fields.float('Commission Percentage',digits_compute=dp.get_precision('Commission Amount')),
	}

	def generate_default_agent(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		so_pool = self.pool.get('sale.order')
		partner_pool = self.pool.get('res.partner')
		soa_pool = self.pool.get('sale.order.agent')
		datas = self.read(cr, uid, ids, ['agent_id', 'invoice_partner_id', 'commission_percentage'])
		
		active_ids = context.get('active_ids', [])
		if not active_ids:
			return False

		partner_id = partner_pool.search(cr, uid, [('agent','=',True)])
		if partner_id:
			partner_id = partner_id[0]
		else:
			partner_id = 1
		for sale in so_pool.browse(cr, uid, active_ids, context=context):
			default_agent_id = datas and datas[0]['agent_id'] and datas[0]['agent_id'][0] or partner_id
			default_invoice_partner_id = datas and datas[0]['invoice_partner_id'] and datas[0]['invoice_partner_id'][0] or partner_id
			default_percentage = datas and datas[0]['commission_percentage'] or 0.0
			curr_so_line_in_agent_ids = []
			if sale.agent_ids:
				default_agent_id = sale.agent_ids[0].agent_id and sale.agent_ids[0].agent_id.id or default_agent_id
				default_invoice_partner_id = sale.agent_ids[0].invoice_partner_id and sale.agent_ids[0].invoice_partner_id.id or default_invoice_partner_id
				default_percentage = sale.agent_ids[0].commission_percentage and sale.agent_ids[0].commission_percentage or default_percentage
				curr_so_line_in_agent_ids = [x.sale_line_id for x in sale.agent_ids if x.sale_line_id]

			for line in sale.order_line:
				if not curr_so_line_in_agent_ids or (curr_so_line_in_agent_ids and line not in curr_so_line_in_agent_ids):
					soa_pool.create(cr, uid, {
						'sale_id':sale.id,
						'agent_id':default_agent_id,
						'invoice_partner_id':default_invoice_partner_id,
						'commission_percentage':default_percentage,
						'sale_line_id':line.id,
						})
		return True

wizard_sale_order_agent()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: