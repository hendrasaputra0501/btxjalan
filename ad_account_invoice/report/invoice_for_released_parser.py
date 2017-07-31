import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class invoice_for_released_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(invoice_for_released_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
				"get_results_group_by_partner" : self._get_results_group_by_partner,
			})

	def _get_picking_objs(self, objects):
		cr = self.cr
		uid = self.uid
		res = {}
		picking_ids = self.pool.get('stock.picking').search(cr, uid, [('invoice_id','in',[inv.id for inv in objects])])
		if picking_ids:
			for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids):
				key = picking.invoice_id.id
				if key not in res.keys():
					res.update({key:[]})
				res[key].append(picking)
		return res

	def _get_results_group_by_partner(self, objects):
		cr = self.cr
		uid = self.uid
		result_grouped = {}
		res_picking_objs = self._get_picking_objs(objects)
		curr_obj = self.pool.get('res.currency')
		for inv in objects:
			company_currency = inv.company_id.currency_id
			current_currency = inv.currency_id and inv.currency_id or False
			context = {}
			context.update({'date':inv.date_effective!=False and inv.date_effective or inv.date_invoice or time.strftime("%Y-%m-%d")})
			
			key = (inv.partner_id.id, inv.partner_id and inv.partner_id.partner_code or '', inv.partner_id and inv.partner_id.name or '')
			if key not in result_grouped.keys():
				result_grouped.update({key:[]})
			picking_objs = res_picking_objs and res_picking_objs.get(inv.id, False) and res_picking_objs[inv.id] or []
			po_objs = picking_objs and list(set([picking.purchase_id for picking in picking_objs if picking.purchase_id])) or []

			result_grouped[key].append({
				'date_maturity' : inv.date_effective!=False and inv.date_effective or inv.date_invoice,
				'move_name' : inv.move_id and inv.move_id.name or '',
				'move_ref' : inv.move_id and inv.move_id.ref or '',
				'po_ref' : po_objs and "<br/>".join([po.name for po in po_objs]) or '',
				'po_date' : po_objs and po_objs[0].date_order or False,
				'original_picking_names' : picking_objs and "<br/>".join(list(set([picking.supplier_delicery_slip for picking in picking_objs if picking.supplier_delicery_slip]))) or '',
				'original_picking_date' : picking_objs and list(set([picking.supplier_delicery_slip for picking in picking_objs if picking.supplier_delicery_slip and picking.date_delivery_slip])) and list(set([picking for picking in picking_objs if picking.supplier_delicery_slip and picking.date_delivery_slip]))[0].date_delivery_slip or False,
				'picking_names' : picking_objs and "<br/>".join(list(set([picking.name for picking in picking_objs if picking.name]))) or '',
				'picking_date' : picking_objs and list(set([picking.name for picking in picking_objs if picking.name and picking.date_done])) and list(set([picking for picking in picking_objs if picking.name and picking.date_done]))[0].date_done or False,
				'payment_terms':inv.payment_term and inv.payment_term.name or '',
				'due_date' : inv.date_due!=False and inv.date_due or False,
				'inv_cury' : inv.currency_id and inv.currency_id.name or '',
				'amount_untaxed' : sum(map(lambda x:x.price_subtotal, [line for line in inv.invoice_line if not line.is_ppv_entry])),
				'amount_untaxed_usd' : curr_obj.compute(cr, uid, current_currency.id ,company_currency.id, sum(map(lambda x:x.price_subtotal, [line for line in inv.invoice_line if not line.is_ppv_entry])),round=True, context=context),
				'amount_tax' : sum(map(lambda x:x.tax_amount, [line for line in inv.invoice_line if not line.is_ppv_entry])),
				'amount_tax_usd' : curr_obj.compute(cr, uid, current_currency.id ,company_currency.id, sum(map(lambda x:x.tax_amount, [line for line in inv.invoice_line if not line.is_ppv_entry])),round=True, context=context),
				'amount_ppv' : sum(map(lambda x:abs(x.price_subtotal), [line for line in inv.invoice_line if line.is_ppv_entry]))/2,
				'amount_ppv_usd' : curr_obj.compute(cr, uid, current_currency.id ,company_currency.id, sum(map(lambda x:abs(x.price_subtotal), [line for line in inv.invoice_line if line.is_ppv_entry]))/2,round=True, context=context),
				'remarks' : inv.reference or '', 
				'quantity' : sum([(x.quantity or 0.0) for x in inv.invoice_line]),
				'avg_price_unit' : sum(map(lambda x:x.price_subtotal, [line for line in inv.invoice_line if not line.is_ppv_entry]))/sum([(x.quantity or 0.0) for x in inv.invoice_line]),
				})
		
		return result_grouped
report_sxw.report_sxw('report.invoice.for.released', 'account.invoice', 'ad_account_invoice/report/invoice_for_released.mako', parser=invoice_for_released_parser,header=False)