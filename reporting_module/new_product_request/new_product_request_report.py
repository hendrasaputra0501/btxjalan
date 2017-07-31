import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter

class new_product_request_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(new_product_request_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_address':self.get_address,
			'get_material_line':self._get_material_line,
			'call_num2word':self._call_num2word,
			'get_matline_amt':self._get_matline_amt,
		})
		   
	def get_address(self, partner_obj):
		if partner_obj:
			partner_address = ''
			partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
			partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
			partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
			partner_address += partner_obj.city and partner_obj.city +' ' or ''
			partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
			partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''

			return  partner_address.replace('\n','<br />')
		else:
			return False

	def _get_requisition_line(self,reqline_obj):
		res=[]
		reqline_group={}
		for line in reqline_obj:
			key=(line.product_id.name,line.purchase_line_id.price_unit,(line.tracking_id and line.tracking_id or False))
			if key not in reqline_group:
				reqline_group[key]=["","","",0,0,0,"",0,0,""]
			loc = line.location_dest_id.name.split(" ")
			
			lenloc=len(loc)
			if lenloc==1:
				loc_out= (loc[0] or "")
			else:
				loc_out = (loc[2] or "") + (loc[4] and loc[4][0:1] or "")
			
			reqline_group[key][0]=line.product_id and line.product_id.name or ''			
			reqline_group[key][1]= loc_out or ''
			reqline_group[key][2]=line.product_uom.name or ''
			reqline_group[key][3]+=line.product_qty
			reqline_group[key][4]=line.purchase_line_id.price_unit or 0.0
			reqline_group[key][5]+=(line.purchase_line_id and line.purchase_line_id.price_unit*line.product_qty) or 0.0
			reqline_group[key][6]=line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.requisition_id and line.purchase_line_id.order_id.requisition_id.name or '-'

			if line.product_id.internal_type=='Raw Material':
				reqline_group[key][7]+=line.gross_weight or 0.0
				reqline_group[key][8]=line.moisturity or 0.0

			reqline_group[key][8]=line.tracking_id and line.tracking_id.name or ""

		for x in reqline_group.keys():
			res.append(reqline_group[x])
		return res

	def _get_matline_amt(self,matline_obj):
		tot_amt=0
		for a in matline_obj:
			tot_amt=tot_amt+(a.purchase_line_id.price_unit*a.product_qty or 0.0)
		return tot_amt
	
	def _call_num2word(self,amount_total,cur):
		amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
		return amt_id


 
# report_sxw.report_sxw('report.incoming.shipment.form', 'stock.picking.in', 'reporting_module/incoming_shipment_report/incoming_shipment_form.mako', parser=new_product_request_parser,header=False) 
