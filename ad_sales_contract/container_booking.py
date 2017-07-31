from openerp.osv import fields,osv
from tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class container_booking(osv.Model):
	_inherit = "container.booking"

	_columns ={
		'approval_reason':fields.text('Approval Reason'),
		'state' : fields.selection([
			('cancel','Cancelled'),
			('draft','Draft'),
			('need_approval','Need Approval'),
			('booked','Booked'),
			('instructed','Instructed')],'Status')
	}
	_defaults = {
		"state":'draft',
	}

	def action_booked(self,cr,uid,ids,context=None):
		"""
		* Never inherit this method (do not do super) *
		"""
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		picking_line = [picking.id for picking in container_id.picking_ids]
		picking_pool = self.pool.get('stock.picking')
		credit_limit,limit_c = picking_pool.check_credit_limit(cr,uid,picking_line,context=context)
		overdue_limit,limit_o = picking_pool.check_overdue_limit(cr,uid,picking_line,context=context)
		lc_advance_check = picking_pool.lc_advance_check(cr,uid,picking_line,context=context)
		# print "sales_contract===================",credit_limit,overdue_limit,lc_advance_check
		reason=""
		if not credit_limit or not overdue_limit or not lc_advance_check:
			if not credit_limit:
				reason += "The amount of total outstanding receivable + current delivery is %s,\nbut the partner credit limit is %s\n"%(limit_c,container_id.picking_ids[0].partner_id.credit_limit)
			if not overdue_limit:
				reason += "The amount of total overdue receivable + current delivery is %s,\nbut the partner overdue credit limit is %s\n"%(limit_o,container_id.picking_ids[0].partner_id.credit_overdue_limit)			
			if not lc_advance_check:
				reason += "LC(s) or Advance(s) have not been paid yet, please check the payment(s)\n"
			return self.write(cr,uid,ids[0],{'state':'need_approval','approval_reason':reason,'need_approval':True})
		for picking_id in container_id.picking_ids:
			wf_service.trg_validate(uid, 'stock.picking', picking_id.id, 'booked', cr)
		# print "sales_contract2==================="
		return self.write(cr,uid,ids[0],{'state':'booked','approved_by':uid})

	def action_booked_manager(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		container_id = self.browse(cr,uid,ids[0],context=context)
		for picking_id in container_id.picking_ids:
			wf_service.trg_validate(uid, 'stock.picking', picking_id.id, 'booked', cr)

		return self.write(cr,uid,ids,{'state':'booked','approved_by':uid})