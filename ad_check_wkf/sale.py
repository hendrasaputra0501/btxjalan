from openerp.osv import fields,osv
from openerp import netsvc

class sale_order(osv.Model):
	_inherit = "sale.order"
	_columns = {

	}

	def check_wkf(self,cr,uid,ids,context=None):
		wf_service = netsvc.LocalService("workflow")
		workflow_id = self.pool.get('workflow').search(cr,uid,[('name','=','sale.order.basic'),('osv','=','sale.order')])
		try:
			workflow_id = workflow_id[0]
		except:
			workflow_id = workflow_id or False
		activity = self.pool.get('workflow.activity').search(cr,uid,[('name','=','ship'),('wkf_id','=',workflow_id)])
		try:
			activity = activity[0]
		except:
			activity = activity or False
		for sale in self.browse(cr,uid,ids,context=context):
			
			for line in sale.order_line:
				x=wf_service.trg_trigger(uid, 'procurement.order', line.procurement_id.id, cr)
				print "x==============",x
			state=self.test_state(cr,uid,[sale.id],'finished')
			if sale.state=='done' and not state:
				if workflow_id:
					instance=self.pool.get('workflow.instance').search(cr,uid,[('wkf_id','=',workflow_id),('res_type','=','sale.order'),('res_id','=',sale.id)])
					try:
						instance = instance[0]
					except:
						instance = instance or False
					wkf_item = self.pool.get('workflow.workitem').search(cr,uid,[('wkf_id','=',workflow_id),('inst_id','=',instance)])
					if wkf_item:
						self.pool.get('workflow.workitem').write(cr,uid,wkf_item,{'act_id':activity})	
						self.pool.get('sale.order').write(cr,uid,[sale.id],{'state':'ready_to_deliver','date_done':False})
		return True
