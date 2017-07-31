from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler
import time

class wizard_pending_shipment_status_register(osv.osv_memory):
	_name="wizard.pending.shipment.status.register"
	_description="Pending Shiment Status Register"

	_columns={
		# 'from_date'	: fields.date('From Date',required=True),
		'from_date'	: fields.date('From Date'),
		# 'to_date'	: fields.date('To Date', required=True),
		'to_date'	: fields.date('To Date',),
		"output_type"	: 	fields.selection([('pdf',"Pdf (*.pdf)")],"Output Type"),
		# "purchase_type" :	fields.selection([("['import']",'Import'),("['local']",'Local'),("['import','local']",'All')],"Purchase Type",required=True),
		"purchase_type" :	fields.selection([("['import']",'Import'),("['local']",'Local'),("['import','local']",'All')],"Purchase Type"),
		'line_ids'	: fields.one2many('wizard.pending.shipment.status.register.line','wizard_id','Purchase Order'),
		'po_number'	: fields.char('Po Number'),
		'filter_by' : fields.selection([('po_number','PO Number'),('po_date','PO Date')],"Filter By"),
	}

	_defaults={
		# "purchase_type":lambda *p:['import'],
		"output_type":lambda *p:'pdf',
		"filter_by":lambda *p:'po_date',
	}

	def onchange_po(self,cr,uid,ids,po_number,context=None):
		purchase_obj=self.pool.get('purchase.order')
		res=[]
		if not po_number :
			return {'value':{'line_ids':[]}}
		purchase_ids=purchase_obj.search(cr,uid,[('name','=',po_number),('goods_type','in',['stores']),('state','in',['approved'])])
		if not purchase_ids:
			return {'value':{'line_ids':[]}}
		for purchase in purchase_obj.browse(cr,uid,purchase_ids):
			res.append({
				'purchase_id' : purchase.id ,
				'department' :purchase.department.id,
				'partner' : purchase.partner_id.id,
				'pending_itemdesc' :purchase.pending_itemdesc,
				'divy_by' :purchase.divy_by,
				# 'shipment_etd_dt' :purchase.shipment_etd_dt,
				'last_shipment_date' :purchase.last_shipment_date,
				'actual_shipment_date':purchase.actual_shipment_date,
				'transit_shipment_date':purchase.transit_shipment_date,
				'document_ref' :purchase.document_ref,
				# 'arrival_harbour' :purchase.arrival_harbour,
				# 'arrival_factory' :purchase.arrival_factory,
				'shipment_remarks' :purchase.shipment_remarks,
				})
		return {'value':{'line_ids':res}}


	def onchange_fields(self,cr,uid,ids,from_date,to_date,purchase_type, context=None):
		purchase_obj=self.pool.get('purchase.order')
		# print purchase_obj,"-----------------------------------------------------------------"
		res=[]
		if not from_date or not to_date or not purchase_type:
			return {'value':{'line_ids':[]}}
		# sale_ids = sale_obj.search(cr, uid, [('freight_rate_value','<=',0),('date_order','>=',from_date),('date_order','<=',to_date),('state','not in',['cancel','draft','sent']),('sale_type','=','export')])
		purchase_ids =purchase_obj.search(cr,uid,[('date_order','>=',from_date),('date_order','<=',to_date),('goods_type','in',['stores']),('state','in',['approved']),('purchase_type','in',eval(purchase_type))])
		# print purchase_ids,"++++++++++++++++++++++++++++++++++++++++++"
		if not purchase_ids:
			return {'value':{'line_ids':[]}}
		# for sale in sale_obj.browse(cr, uid, sale_ids):
		for purchase in purchase_obj.browse(cr,uid,purchase_ids):
			# print purchase.id,"++++++++++++++++++++++++++++++++"
			res.append({
				'purchase_id' : purchase.id ,
				'department' :purchase.department.id,
				'partner' :purchase.partner_id.id,
				'pending_itemdesc' :purchase.pending_itemdesc,
				'divy_by' :purchase.divy_by,
				# 'shipment_etd_dt' :purchase.shipment_etd_dt,
				'last_shipment_date' :purchase.last_shipment_date,
				'actual_shipment_date':purchase.actual_shipment_date,
				'transit_shipment_date':purchase.transit_shipment_date,
				'document_ref' :purchase.document_ref,
				# 'arrival_harbour' :purchase.arrival_harbour,
				# 'arrival_factory' :purchase.arrival_factory,
				'shipment_remarks' :purchase.shipment_remarks,
				

				})
			print res,"++++++++++++++++++++++++++++++++"
		return {'value':{'line_ids':res}}

	def save_data(self,cr,uid,ids,context=None):
		if not context:
			context={}
		wf_service = netsvc.LocalService("workflow")
		pool_obj=self.pool.get('purchase.order')
		data=self.browse(cr,uid,ids[0],context=context)
		print data.line_ids,"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		for line in data.line_ids:
			# pool_obj.write(cr,uid,line.purchase_id.id,{'department':line.department,'pending_itemdesc':line.pending_itemdesc,
			pool_obj.write(cr,uid,line.purchase_id.id,{'pending_itemdesc':line.pending_itemdesc,
			#'partner' :line.partner_id.id,
			'divy_by':line.divy_by,
			# 'shipment_etd_dt': line.shipment_etd_dt,
			'last_shipment_date': line.last_shipment_date,
			'actual_shipment_date':line.actual_shipment_date,
			'transit_shipment_date':line.transit_shipment_date,
			'document_ref' :line.document_ref,
			# 'arrival_harbour':line.arrival_harbour,
			# 'arrival_factory':line.arrival_factory,
			'shipment_remarks':line.shipment_remarks,
			},context=context)
			return {
				'type': 'ir.actions.act_window_close',
				}


	def generate_report(self,cr,uid,ids,context=None):
		if not context:
			context={}
		wf_service = netsvc.LocalService("workflow")
		pool_obj=self.pool.get('purchase.order')
		data=self.browse(cr,uid,ids[0],context=context)
		for line in data.line_ids:
			# pool_obj.write(cr,uid,line.purchase_id.id,{'department':line.department,'pending_itemdesc':line.pending_itemdesc,
			pool_obj.write(cr,uid,line.purchase_id.id,{'pending_itemdesc':line.pending_itemdesc,
			'divy_by':line.divy_by,
			# 'shipment_etd_dt': line.shipment_etd_dt,
			'last_shipment_date': line.last_shipment_date,
			'actual_shipment_date':line.actual_shipment_date,
			'transit_shipment_date':line.transit_shipment_date,
			'document_ref' :line.document_ref,
			# 'arrival_harbour':line.arrival_harbour,
			# 'arrival_factory':line.arrival_factory,
			'shipment_remarks':line.shipment_remarks,
			},context=context)

		# print "=============", ids
		form_data=self.read(cr, uid, ids)[0]
		# print "==============================xwzxwzxwzxwzxwzxwzxwzxwzxwz=================", form_data
		# form=self.read(cr, uid, ids)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model'	: 'wizard.pending.shipment.status.register',
			'form': form_data,
			# 'date_start': form.date_start,
			# 'date_stop': form.date_stop,
			}
		if form_data['output_type']=='pdf':
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'pending.shipment.status.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}
		else:
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'xls.pending.shipment.register.report',
				'report_type': 'webkit',
				'datas': datas,
				}

wizard_pending_shipment_status_register()

# class wizard_input_pending_shipment_status_register(osv,osv_memory):
# 	_name="wizard.input.pending.shipment.status.register"
# 	_columns={
# 		from_date	: fields.date("From Date",requiered=True),
# 		to_date		: fields.date("To Date",required=True),
# 	}

class wizard_pending_shipment_status_register_line(osv.osv_memory):
	_name="wizard.pending.shipment.status.register.line"
	_columns={
		'wizard_id'	:	fields.many2one('wizard.pending.shipment.status.register','Wizard Reference'),
		'purchase_id'	:	fields.many2one('purchase.order', 'Purchase Order', required=True),
		'department'	:	fields.many2one('hr.department', 'Department', required=False),
		'partner'		: fields.many2one('res.partner','Partner', required=False),
		'pending_itemdesc'	:	fields.char('Description',size=50,required=False),
		'divy_by'	:	fields.char('Ship By',size=10,required=False),
		# 'shipment_etd_dt'	: fields.date('Shipment ETD Date'),
		'last_shipment_date'	: fields.date('Last Shipment Date'),
		'actual_shipment_date': fields.date('Actual Shipment Date'),
		'transit_shipment_date': fields.date('Transit Shipment Date'),
		# 'eta_date' : fields.date('ETA Date'),
		'document_ref' : fields.char('Document Reference',size=50),
		# 'arrival_harbour' : fields.date('Arrival Harbour'),
		# 'arrival_factory' : fields.date('Arrival Factory'),
		'shipment_remarks' :fields.char('Remarks',size=50,required=False),

	}
wizard_pending_shipment_status_register_line()