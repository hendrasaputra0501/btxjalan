import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter
from datetime import datetime


class item_request_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		print
		super(item_request_parser, self).__init__(cr, uid, name, context=context)		
		self.localcontext.update({
			'time' : time,
			'get_data':self._get_data ,
			'get_matreq_line' : self._get_matreq_line ,
			'get_product_undefined' :self._get_product_undefined,

		})
	# def __init__(self, cr, uid, name, context):
	# 	super(item_request_parser, self).__init__(cr, uid, name, context=context)        
	# 	#======================================================================= 
	# 	# self.line_no = 0
	# 	self.localcontext.update({
	# 		'time': time,
	# 		'get_data':self._get_data,
	# 		'get_matreq_line' : self._get_matreq_line ,
	# 	})

	def _get_product_undefined(self,objline):
		cr=self.cr
		uid=self.uid
		line_product_id=objline
		# print line_product_id,"ggggggggggggggggggggggggggggg"
		product_undefined_obj=self.pool.get('product.undefined.info')
		# puo_ids=product_undefined_obj.search(cr, uid, [('product_id','like',line_product_id)])
		puo_ids=product_undefined_obj.search(cr, uid, [('product_id','=',line_product_id)])
		# print puo_ids,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		if puo_ids:
			puo=product_undefined_obj.browse(cr,uid,puo_ids)[0]
			puo_last_price=puo.price_unit
			puo_last_vendor=puo.partner_name
			puo_last_po=puo.po_number
			puo_last_date=puo.po_date
			puo_currency=puo.currency_id.name
			# print puo_currency,puo_last_price,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		else:
			puo_last_price=""
			puo_last_vendor=""
			puo_last_po=""
			puo_last_date=""
			puo_currency=""
		# print puo_last_price,"---------------------------"
		return puo_last_price,puo_last_vendor,puo_last_po,puo_last_date,puo_currency

	def _get_data(self):
		deptname=department.name or ''
		return deptname

	def _get_matreq_line(self,objline):
		grouped={}
		for x in objline:
			# mn_number = x.product_id and x.product_id.catalogue_lines and x.product_id.catalogue_lines[0].catalogue and x.product_id.catalogue_lines[0].catalogue.machine_number or "-"
			mn_number = x.machine_number or "-"
			catalog_number = x.catalogue_id and x.catalogue_id.catalogue or "-"
			# catalog_number = x.product_id and x.product_id.catalogue_lines and x.product_id.catalogue_lines[0].catalogue and x.product_id.catalogue_lines[0].catalogue.machine_number and x.product_id.catalogue_lines[0].catalogue.catalogue or "-"
			# part_number = x.product_id and x.product_id.catalogue_lines and x.product_id.catalogue_lines[0].catalogue and x.product_id.catalogue_lines[0].catalogue.machine_number and x.product_id.part_number or "-"
			part_number = x.part_number or "-"			
			# key=(mn_number, catalog_number, part_number)
			key=(mn_number)
			
			if key not in grouped:
				grouped.update({key:[]})
			grouped[key].append(x)
		return grouped

		# res=[]
		# list_group={}

		# for line in objline :
		# 	x=line.requisition_id and line.requisition_id.date_end[:10]
		# 	date_end=datetime.strptime(x,'%Y-%m-%d').strftime('%d/%m/%Y')
		# 	# key =(line.product_id.id)
		# 	# key=(line.product_id and line.product_id.part_number) or (line.product_id.id)
		# 	key = ((line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.machine_number) or (line.product_id and line.product_id.part_number), line.product_id.id)
		# 	# key=(line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.machine_number or line.product_id and line.product_id.part_number)
		# 	if key not in list_group:
		# 		list_group[key]=["","","","",0,"","","","",0,0,"","","",0,"","","","",""]
		# 	list_group[key][0]=line.product_id and line.product_id.default_code or''
		# 	list_group[key][1]=line.product_id and line.product_id.name_template or ''
		# 	list_group[key][2]=line.stock_uom_id and line.stock_uom_id.name or ''
		# 	# list_group[key][3]=line.requisition_id and line.requisition_id.location_dest_id and line.requisition_id.location_dest_id.name or ''
		# 	list_group[key][3]=line.requisition_id and line.requisition_id.location_dest_id and line.requisition_id.location_dest_id.alias or ''
		# 	# list_group[key][4]= int(line.product_qty)
		# 	list_group[key][4]= line.product_qty
		# 	list_group[key][5]=date_end or ''
		# 	list_group[key][6]=line.detail or ''
		# 	list_group[key][7]=line.product_id and line.product_id.part_number or ''
		# 	list_group[key][8]=line.product_id and line.product_id.manufacturer_pname or ''
		# 	list_group[key][9]=line.current_qty_available
		# 	list_group[key][10]=line.current_qty_virtual or 0.0
		# 	list_group[key][11]=line.last_po_id and line.last_po_id.id and line.last_po_id.name
		# 	list_group[key][12]=line.last_po_id and line.last_po_id.partner_id and (line.last_po_id.partner_id.partner_alias or line.last_po_id.partner_id.name) or ''
		# 	list_group[key][13]=line.currency_id and line.currency_id.name or ''
		# 	list_group[key][14]=line.price or ''
		# 	list_group[key][15]=line.remark or ''
		# 	list_group[key][16]=line.detail or ''
		# 	list_group[key][17]=line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.machine_number or ''
		# 	list_group[key][18]=line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.from_year or ''
		# 	list_group[key][19]=line.id

		
		# for x in list_group.keys():
		# 	res.append(list_group[x])
		# 	result=sorted(res,key=lambda res:res[19])
		# print "==================",list_group
		# print "==================",result
		# return result



report_sxw.report_sxw('report.item.request.form', 'material.request', 'ad_material_requisition/report/item_request_form.html', parser=item_request_parser,header=False) 
