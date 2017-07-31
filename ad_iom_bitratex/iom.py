from openerp.osv import fields,osv
from tools.translate import _
import datetime

#class sale_order_line_iom(osv.osv):
#	_name = "sale.order.line.iom"
#	_inherit = "sale.order.line"
#	_columns = {
#		"order_id": fields.many2one("sale.order","Order ID",required=False),
#		"iom_line_id" : fields.many2one("iom.request.line","IOM Request Line"),
#	}

class sale_order(osv.osv):
	_inherit = "sale.order"
	def _is_have_history(self,cr,uid,ids,fields,args,context=None):
		if not context:context={}
		res={}
		for so in self.browse(cr,uid,ids,context=context):
			ammend=False
			for rev in so.revision_ids:
				if rev.state=='approved':
					ammend=True
			res.update({so.id :ammend})
		# print "============",res
		return res

	_columns = {

		"have_history" : fields.function(_is_have_history,type="boolean",string="Amended",help="This field help us to filter amended user"),
		"revision_ids" : fields.one2many("iom.request","document_sale_id","Revision History",
					help="Revision History for contracts"),
	}

class iom_request(osv.osv):
	_name = "iom.request"
	_columns = {
		"name" 					: fields.char("IOM Number",required=True,size=64),
		"sequence"				: fields.integer("Sequence Number"),
		"date_request"			: fields.date("Request Date",required=True),
		"date_approve"			: fields.datetime("Approve Date",required=False),
		"request_uid"			: fields.many2one("res.users","Requested By",required=True),
		"approve_uid"			: fields.many2one("res.users","Approved By",required=False),
		"document_type" 		: fields.selection([('sale.order','Sales Contract'),('sale.order.line','Sales Contract Line')],"Document type",required=True),
		"model_id"				: fields.many2one("ir.model","Model"),
		"document_sale_id" 		: fields.many2one("sale.order","Sales Contract Number",required=True),
		"document_sale_line_id"	: fields.many2one("sale.order.line","Contract Line",required=False,),
		"iom_lines"				: fields.one2many("iom.request.line","iom_id","IOM Lines"),
		"reason"				: fields.text("Reason",required=True),
		"state"					: fields.selection([('draft','Draft'),('submitted',"Submitted"),('approved','Approved'),('rejected','Rejected')],"State",
					required=True),
		}
	_defaults = {
		"name":lambda *a:'Draft',
		"document_type":"sale.order",
		"date_request": lambda *a: datetime.date.today().strftime('%Y-%m-%d'),
		"state":"draft",
		"request_uid": lambda self,cr,uid,context:uid,
		"model_id" : lambda self,cr,uid,context:self.pool.get('ir.model').search(cr,uid,[('model','=','sale.order')])[0]
	} 
	_order = "sequence desc, date_approve desc, date_request desc"

	def action_submit(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'submitted'})

	def action_rejected(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'rejected'})

	def action_revised(self,cr,uid,ids,context=None):
		if not context:context={}
		return self.write(cr,uid,ids,{'state':'submitted'})

	def action_approve(self,cr,uid,ids,context=None):
		if not context:context={}
		for iom in self.browse(cr,uid,ids,context=context):
			is_any_delivery = False
			is_draft_delivery = False
			no_picking = False
			if iom.document_sale_id:
				if iom.document_sale_id.picking_ids:
					for do in iom.document_sale_id.picking_ids:
						if do.state in ('done'):
							is_any_delivery = True
						if do.state in ('draft','booking_created','booked','confirmed'):
							is_draft_delivery = True
				else:
					no_picking = True
			# override_val = {}
			try:
				if no_picking:
					# print "nopicking====================="
					for iom_line in iom.iom_lines:
						if not iom_line.add_new_line:
							if iom.document_sale_line_id:
								if iom_line.fields_id.name == 'product_id':

									self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,{'name':iom_line.new_ref_line.name,'product_id':iom_line.new_ref_line.id})
								else:
									if iom_line.fields_id.ttype !='many2one':
										get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
									else:
										get_field_val = eval("iom_line.new_ref_line.id")
									# get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
									override_val = {iom_line.fields_id.name:get_field_val}
									self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,override_val)
									# print "-------essss--------"
									# print "---------nopicking True-------"
									x=self.pool.get('sale.order').button_dummy(cr,uid,[iom.document_sale_id.id])
									# print "---------nopicking Truex-------",x
							else:
								if iom_line.fields_id.ttype !='many2one':
									get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
								else:
									get_field_val = eval("iom_line.new_ref.id")
								override_val = {iom_line.fields_id.name:get_field_val}
								self.pool.get('sale.order').write(cr,uid,iom.document_sale_id.id,override_val)
						else:
							# for order_line in iom_line.sale_line_ids:
							# 	self.pool.get()
							continue
				if is_any_delivery:
					# print "ANYDELIVERY====================="
					for iom_line in iom.iom_lines:
						if not iom_line.add_new_line:
							if iom.document_sale_line_id:
								if iom_line.fields_id.name == 'product_id':
									product_sent= False
									for sm in iom.document_sale_line_id.move_ids:
										if sm.state =='done':
											product_sent =True
											raise osv.except_osv(_('Error!'),_("Can not process the request, there's already a delivery for product %s from this contract"%iom.document_sale_line_id.product_id.name))
									if not product_sent:
										self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,{'name':iom_line.new_ref_line.name,'product_id':iom_line.new_ref_line.id})
										sm_ids = []
										for sm in iom.document_sale_line_id.move_ids:
											if sm.state not in ('done'):
												sm_ids.append(sm.id)
										self.pool.get('stock.move').write(cr,uid,sm_ids,{'product_id':iom_line.new_ref_line.id})
								else:
									if iom_line.fields_id.ttype !='many2one':
										get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
									else:
										get_field_val = eval("iom_line.new_ref_line.id")
									# get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
									# print "============",get_field_val
									override_val = {iom_line.fields_id.name:get_field_val}
									self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,override_val)
									self.pool.get('sale.order').button_dummy(cr,uid,[iom.document_sale_id.id])
							else:
								if iom_line.fields_id.ttype !='many2one':
									get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
								else:
									get_field_val = eval("iom_line.new_ref.id")
								override_val = {iom_line.fields_id.name:get_field_val}
								self.pool.get('sale.order').write(cr,uid,iom.document_sale_id.id,override_val)
						else:
							# for order_line in iom_line.sale_line_ids:
							# 	self.pool.get()
							continue
				elif not is_any_delivery and is_draft_delivery:
					# print "=======draft delivery========="
					for iom_line in iom.iom_lines:
						if not iom_line.add_new_line:
							if iom.document_sale_line_id:
								if iom_line.fields_id.name == 'product_id':
									product_sent= False
									for sm in iom.document_sale_line_id.move_ids:
										if sm.state =='done':
											product_sent =True
											raise osv.except_osv(_('Error!'),_("Can not process the request, there's already a delivery for product %s from this contract"%iom.document_sale_line_id.product_id.name))
									if not product_sent:
										# print "write----------"
										self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,{'name':iom_line.new_ref_line.name,'product_id':iom_line.new_ref_line.id})
										sm_ids = []
										for sm in iom.document_sale_line_id.move_ids:
											if sm.state not in ('done'):
												sm_ids.append(sm.id)
										self.pool.get('stock.move').write(cr,uid,sm_ids,{'name':iom_line.new_ref_line.name,'product_id':iom_line.new_ref_line.id})
										# print "write2----------"
								else:
									# print "====","iom_line.new_value_"+iom_line.fields_id.ttype
									if iom_line.fields_id.ttype !='many2one':
										get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
									else:
										get_field_val = eval("iom_line.new_ref_line.id")

									override_val = {iom_line.fields_id.name:get_field_val}
									override_val2 = {}
									if iom_line.fields_id.name=='product_uom_qty':
										override_val2.update({'product_qty':get_field_val,
											'product_uos_qty':get_field_val
											})
									elif iom_line.fields_id.name=='product_uom':
										override_val2.update({'product_uom':get_field_val,
											'product_uos':get_field_val
											})
									# print "==============",override_val,override_val2
									self.pool.get('sale.order.line').write(cr,uid,iom.document_sale_line_id.id,override_val)
									sm_ids = []
									for sm in iom.document_sale_line_id.move_ids:
										if sm.state not in ('done'):
											sm_ids.append(sm.id)
									# print "=======sms=======",sm_ids,override_val2
									self.pool.get('stock.move').write(cr,uid,sm_ids,override_val2)
									self.pool.get('sale.order').button_dummy(cr,uid,[iom.document_sale_id.id])
							else:
								if iom_line.fields_id.ttype !='many2one':
									get_field_val = eval("iom_line.new_value_"+iom_line.fields_id.ttype)
								else:
									get_field_val = eval("iom_line.new_ref.id")
								override_val = {iom_line.fields_id.name:get_field_val}
								self.pool.get('sale.order').write(cr,uid,iom.document_sale_id.id,override_val)
						else:

							# for order_line in iom_line.sale_line_ids:
							# 	self.pool.get()
							continue
				cr.execute("select max(sequence) from iom_request where document_sale_id=%s"%iom.document_sale_id.id)
				sequence=cr.fetchone()
				next=0
				new_name="Draft"
				if sequence[0]:
					next=sequence[0]+1
					# print "-----------------",next,sequence[0],"end"
				else:
					next=1
				if next>=0:
					new_name =iom.document_sale_id.name+" rev-%s "%next
					# print "sequenceee================",new_name


				self.write(cr,uid,iom.id,{'state':'approved',"approve_uid":uid,"date_approve":datetime.date.today().strftime('%Y-%m-%d %H:%M:%S'),"sequence":next>0 and next or False,'name':next>0 and new_name or 'Draft'})
			except:
				continue
		return 

	def onchange_document_type(self,cr,uid,ids,doc_type,context=None):
		if not context:context={}

		model_id=False
		if doc_type:
			model_id = self.pool.get('ir.model').search(cr,uid,[('model','=',doc_type)])
		else:
			model_id = self.pool.get('ir.model').search(cr,uid,[('model','=',"sale.order")])

		if model_id:
			try:
				model_id=model_id[0]
			except:
				model_id=model_id
		return {"value":{"model_id":model_id},'context':{'model':doc_type}}	
				
def _get_old_reference(self, cr, uid, context=None):
	cr.execute("select * from (select relation,field_description from ir_model_fields where model_id = (select id from ir_model where model='sale.order') and ttype='many2one' order by relation,field_description) dummy order by field_description asc")
	return cr.fetchall()
def _get_old_reference_line(self, cr, uid, context=None):
	cr.execute("select * from (select relation,field_description from ir_model_fields where model_id = (select id from ir_model where model='sale.order.line') and ttype='many2one' order by relation,field_description) dummy order by field_description asc")
	return cr.fetchall()
# def _get_selection(self,cr,uid,context=None):
# 	print "==========================selection==============================",context
# 	if not context: 
# 		context={}
# 	fields_id=context.get('fields_id',False)
# 	if not fields_id:
# 		return [('keriting','KERITING'),('ikal','IKAL'),('lurus','LURUS')]
# 	else:
# 		fields = self.pool.get('ir.model.fields').browse(cr,uid,fields_id)
# 		selection = fields.model
# 		pooler = self.pool.get(selection)._columns[fields.name].selection
# 		return pooler
class iom_request_line(osv.osv):
	_name = "iom.request.line"

	def _get_old_value(self,cr,uid,ids,fields,args,context=None):
		if not context:
			context={}
		res = {}
		for xid in self.browse(cr,uid,ids,context=context):
			res.update({
				xid.id : xid.old_value_text or (xid.old_ref and xid.old_ref.name) or (xid.old_ref_line and xid.old_ref_line.name) or xid.old_value_float or xid.old_value_char or xid.old_value_date or xid.old_value_datetime or False,
				})
		return res
	def _get_new_value(self,cr,uid,ids,fields,args,context=None):
		if not context:
			context={}
		res = {}
		for xid in self.browse(cr,uid,ids,context=context):
			res.update({
				xid.id : xid.new_value_text or (xid.new_ref and xid.new_ref.name) or (xid.new_ref_line and xid.new_ref_line.name) or xid.new_value_float or xid.new_value_char or xid.new_value_date or xid.new_value_datetime or False,
				})
		return res

	_columns ={
		"iom_id" 			: fields.many2one("iom.request","IOM Document",required=True,ondelete="cascade"),
		"old_value"			: fields.function(_get_old_value,type="text",string="Old Value",store=True),
		"new_value"			: fields.function(_get_new_value,type="text",string="New Value",store=True),
		"fields_id" 		: fields.many2one('ir.model.fields',"Fields",required=True),
		"ttype"				: fields.selection([("binary","Binary"),("boolean","Boolean"),("char","Char"),("date","Date"),("datetime","Datetime"),("float","Float"),("html","HTML"),("integer","Integer"),
							("many2many","Many2Many"),("many2one","Many2One"),("one2many","One2Many"),("reference","Reference"),("selection","Selection"),("text","Text")],
							"Type"),
		"document_type" 	: fields.selection([('sale.order','Sales Contract'),('sale.order.line','Sales Contract Line')],"Document type",required=True),
		"old_value_text"	: fields.text("Old Value"),
		"new_value_text"	: fields.text("New Value"),
		"old_ref"			: fields.reference('Old Reference', required=False, selection=_get_old_reference, size=128, help="Old Reference"),
		"new_ref"			: fields.reference('New Reference', required=False, selection=_get_old_reference, size=128, help="New Reference"),
		"old_ref_line"		: fields.reference('Old Reference', required=False, selection=_get_old_reference_line, size=128, help="Old Reference"),
		"new_ref_line"		: fields.reference('New Reference', required=False, selection=_get_old_reference_line, size=128, help="New Reference"),
		"old_value_float"	: fields.float("Old Float Value"),
		"new_value_float"	: fields.float("New Float Value"),
		"old_value_integer"	: fields.integer("Old Integer Value"),
		"new_value_integer"	: fields.integer("New Integer Value"),
		"old_value_char"	: fields.char("Old Char Value"),
		"new_value_char"	: fields.char("New Char Value"),
		"old_value_date"	: fields.date("Old Date Value"),
		"new_value_date"	: fields.date("New Date Value"),
		# "old_value_selection": fields.selection(_get_selection,string="Old Selection Value"),
		# "new_value_selection": fields.selection(_get_selection,string="New Selection Value"),
		"old_value_datetime": fields.datetime("Old Datetime Value"),
		"new_value_datetime": fields.datetime("New Datetime Value"),
		"add_new_line"		: fields.boolean("Add New Product?"),
		#"sale_line_ids"		: fields.one2many("sale.order.line.iom","iom_line_id","Sale Order Line"),
	}

	def _get_fields_id(self,cr,uid,context=None):
		if not context:context={}
		model=context.get('model','sale.order')
		fields_id = self.pool.get('ir.model.fields').search(cr,uid,[('name','not in',('active','user_id','state')),('ttype','not in',('many2many','one2many','reference')),('model_id.model','=',model)])
		return fields_id[0]
	def _get_ttype(self,cr,uid,context=None):
		if not context:context={}
		field_id = self._get_fields_id(cr,uid,context=context)
		fields = self.pool.get('ir.model.fields').browse(cr,uid,field_id)
		return fields.ttype

	_defaults = {
		'fields_id': _get_fields_id,
		"ttype":_get_ttype,
		"document_type": lambda self,cr,uid,context:context.get('model','sale.order')
	}
	
	def onchange_fields(self,cr,uid,ids,fields_id,sale_id,order_line_id,context=None):
		if not context:context={}
		fields=False
		val={}
		if fields_id:
			fields = self.pool.get('ir.model.fields').browse(cr,uid,fields_id)
			if fields.ttype != 'many2one':
				field_name = 'old_value_'+fields.ttype
			else:
				if order_line_id:
					field_name = 'old_ref_line'
				else:
					field_name = 'old_ref'
			if order_line_id:
				data = self.pool.get('sale.order.line').browse(cr,uid,order_line_id,context)
			elif sale_id:
				data = self.pool.get('sale.order').browse(cr,uid,sale_id,context)
			try:
				if fields.ttype !='many2one':
					data_val = eval("data."+fields.name)
					data_val2 = eval("data."+fields.name)
				else:
					# print "=--------------->",fields.relation+","+str(eval("data."+fields.name+".id"))
					data_val = fields.relation+","+str(eval("data."+fields.name+".id"))
					data_val2 = eval("data."+fields.name+".name") 
			except:
				data_val = False
				data_val2 = False
			val = {
					'value':{
						'ttype':fields and fields.ttype or False,
						field_name : data_val,
						'old_value': data_val2,
					},
					'context':{'fields_id':fields_id},
					}
			# print "===========",val
		return val
