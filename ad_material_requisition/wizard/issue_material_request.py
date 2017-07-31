from openerp.osv import osv,fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
import time

class issue_material_request_line(osv.TransientModel):
	_name = 'issue.material.request.line'
	_columns = {
		'wizard_id' : fields.many2one('issue.material.request', string='Wizard ID', ondelete="CASCADE"),
		'mr_line_id' : fields.many2one('material.request.line',required=True, ondelete="CASCADE", string="MR Line ID"),
		'product_id' : fields.many2one('product.product', required=True, readonly=True, ondelete="CASCADE", string="Product"),
		'product_uom' : fields.many2one('product.uom', required=True, readonly=True, ondelete="CASCADE", string="Unit of Measure"),
		'qty_remaining' : fields.float(digits_compute=dp.get_precision('Product Unit of Measure'), string='Qty Remaining to Issue',readonly=True),
		'qty_to_issue'	: fields.float(digits_compute=dp.get_precision('Product Unit of Measure'), string='Issue Quantity', required=True),
	}

	def onchange_qty_to_issue(self, cr, uid, ids, qty_remaining, qty_to_issue, context=None):
		if not qty_to_issue or qty_to_issue<0:
			return {'value':{'qty_to_issue':0.0}}
		if qty_to_issue>qty_remaining:
			warning = {
				'title': _('Warning!'),
				'message': _('Total maximum quantity that you can issue is %s.'% (qty_remaining,))
			}
			return {'warning':warning,'value':{'qty_to_issue':0.0}}
		else:
			return {'value':{'qty_to_issue':qty_to_issue}}

class issue_material_request(osv.osv_memory):
	_name = 'issue.material.request'
	_columns = {
		'issue_date' : fields.date('Issue Date', required=True),
		'mr_id' : fields.many2one('material.request','Material Request Ref'),
		'line_ids' : fields.one2many('issue.material.request.line','wizard_id', required=True),
	}

	def _partial_issue_for(self, cr, uid, mr_line):
		line = {
			'mr_line_id' : mr_line.id,
			'product_id' : mr_line.product_id.id,
			'qty_remaining' : mr_line.qty_remaining or 0.0,
			'product_uom' : mr_line.product_uom_id.id,
			'qty_to_issue' : mr_line.qty_remaining or 0.0,
		}
		return line

	def default_get(self, cr, uid, fields, context=None):
		if context is None: context = {}
		res = super(issue_material_request, self).default_get(cr, uid, fields, context=context)
		mr_ids = context.get('active_ids', [])
		active_model = context.get('active_model')

		if not mr_ids or len(mr_ids) != 1:
			# Partial Picking Processing may only be done for one picking at a time
			return res
		assert active_model in ('material.request'), 'Bad context propagation'
		mr_id, = mr_ids
		if 'mr_id' in fields:
			res.update(mr_id=mr_id)
		if 'line_ids' in fields:
			mr = self.pool.get('material.request').browse(cr, uid, mr_id, context=context)
			lines = [self._partial_issue_for(cr, uid, m) for m in mr.line_ids if (m.state not in ('done','cancel') and m.qty_remaining>0.0)]
			res.update(line_ids=lines)
		if 'issue_date' in fields:
			res.update(issue_date=time.strftime('%Y-%m-%d'))
		return res

	def create_issue(self, cr, uid, ids, context=None):
		if context is None: context={}
		mr_obj = self.pool.get('material.request')
		mr_line_obj = self.pool.get('material.request.line')
		stock_picking_obj = self.pool.get('stock.picking')
		stock_move_obj = self.pool.get('stock.move')
		wizard_data = self.browse(cr, uid, ids[0], context=context)

		issue_rec = {
			'origin' : wizard_data.mr_id.name,
			'type' : "internal",
			'req_employee' : wizard_data.mr_id.req_employee.id,
			'material_req_id' : wizard_data.mr_id.id,
			'mr_description' : wizard_data.mr_id.origin,
			'internal_shipment_type':'ss_transfer',
			'date': datetime.strptime(wizard_data.issue_date, '%Y-%m-%d').strftime('%Y-%m-%d 12:00:00'),
		}
		lines = []
		for line in wizard_data.line_ids:
			if line.mr_line_id:
				line_rec = {
					'product_id'			: line.product_id.id,
					'product_qty'			: line.qty_to_issue,
					'product_uos_qty'		: line.qty_to_issue,
					'product_uom'			: line.product_uom.id,
					'location_id'			: line.mr_line_id.location_id and line.mr_line_id.location_id.id or wizard_data.mr_id.location_id.id,
					'location_dest_id'		: line.mr_line_id.location_dest_id and line.mr_line_id.location_dest_id.id or wizard_data.mr_id.location_dest_id.id,
					'date'					: datetime.strptime(wizard_data.issue_date, '%Y-%m-%d').strftime('%Y-%m-%d 12:00:00'),
					'analytic_account_id'	: line.mr_line_id.account_analytic_id and line.mr_line_id.account_analytic_id.id or False,
					
					'name'					: line.product_id.name,
					'reason_code'			: line.mr_line_id.reason_code and line.mr_line_id.reason_code.id or False,
					'price_unit'			: line.mr_line_id.price,
					'note'					: line.mr_line_id.description,
					'date_expected'		 	: time.strftime('%Y-%m-%d %H:%M:%S'),
					'company_id'			: wizard_data.mr_id.company_id and wizard_data.mr_id.company_id.id or False,
					'state'				 	: "draft",
				}
				lines.append(line_rec)
			else:
				 raise osv.except_osv(_('Can not create new issue document!'),_("Issue Document has already created before!") )
		lines = map(lambda x:(0,0,x),lines)
		issue_rec.update({'move_lines':lines})
		stock_picking_obj.create(cr, uid, issue_rec)
		return {'type': 'ir.actions.act_window_close'}