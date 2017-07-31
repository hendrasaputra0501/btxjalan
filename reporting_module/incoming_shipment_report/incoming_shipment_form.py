import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter

class incoming_shipment_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(incoming_shipment_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_address':self.get_address,
			'get_material_line':self._get_material_line,
			'call_num2word':self._call_num2word,
			'get_matline_amt':self._get_matline_amt,
			'amount_line':self._amount_line,
		})
	# def _amount_line(self, cr, uid, ids, prop, arg, context=None):
	def _amount_line(self,line):
		res = {}
		cr=self.cr
		uid=self.uid
		context={}
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		# for line in _matline_obj:
		disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.purchase_line_id.discount_ids],line.purchase_line_id.price_unit,line.purchase_line_id.product_qty,context=context)
		price_after = disc.get('price_after',line.purchase_line_id.price_unit)
		taxes = tax_obj.compute_all(cr, uid, line.purchase_line_id.taxes_id, price_after, line.product_qty, line.product_id, line.purchase_line_id.order_id.partner_id)
		order_id = line.purchase_line_id.order_id
		cur = order_id.pricelist_id.currency_id
		sub_total = cur_obj.round(cr, uid, cur, taxes['total'])
		return sub_total

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

	def _get_material_line(self,matline_obj):
		res=[]
		matline_group={}
		for line in matline_obj:
			loc = line.location_dest_id.name.split(" ")
			# print "======",loc,line.location_dest_id.name
			lenloc=len(loc)
			if lenloc==1:
				loc_out= (loc[0] or "")
			elif lenloc==2:
				loc_out=(loc[1] or "")
			elif lenloc==3:
				loc_out=(loc[0] + loc[2] or "")
			elif lenloc==4:
				loc_out=(loc[2] +" " + loc[3] or "")
			else:
				loc_out = (loc[2] or "") + (loc[4] and loc[4][0:1] or "")
			key=(line.product_id.name,loc_out,line.purchase_line_id.price_unit,(line.tracking_id and line.tracking_id or False),line.id)
			if key not in matline_group:
				matline_group[key]=["","","",0,0,0,"",0,0,"","",0,"","","","","","",0,"","","",0]
			
			
			matline_group[key][0]=line.product_id and line.product_id.name or ''			
			matline_group[key][1]= loc_out or ''
			matline_group[key][2]=line.product_uom.name or ''
			matline_group[key][3]+=line.product_qty
			matline_group[key][4]=line.purchase_line_id.price_unit or 0.0
			matline_group[key][5]+=(line.purchase_line_id and line.purchase_line_id.price_unit*line.product_qty) or 0.0
			# matline_group[key][6]=line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.requisition_id and line.purchase_line_id.order_id.requisition_id.name or '-'
			# matline_group[key][6]=line.purchase_line_id and line.purchase_line_id.requisition_id and line.purchase_line_id.requisition_id.material_req_id and line.purchase_line_id.requisition_id.material_req_id.name or '-'
			# matline_group[key][6]=line.purchase_line_id and line.purchase_line_id.requisition_id and line.purchase_line_id.requisition_id.mr_lines and line.purchase_line_id.requisition_id.mr_lines[0].requisition_id and line.purchase_line_id.requisition_id.mr_lines[0].requisition_id.name or '-'
			matline_group[key][6]=line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.requisition_id and line.purchase_line_id.order_id.requisition_id.mr_lines or ''
			if line.product_id.internal_type=='Raw Material':
				matline_group[key][7]+=line.gross_weight or 0.0
				matline_group[key][8]=line.moisturity or 0.0

			matline_group[key][9]=line.tracking_id and line.tracking_id.name or ""
			if line.product_id.internal_type=='Raw Material':
				matline_group[key][10]=line.product_uop and line.product_uop.name or ""
				matline_group[key][11]+=(line.product_uop_qty or 0.0)
			matline_group[key][12]=line.location_dest_id and line.location_dest_id.alias or loc_out or ""
			# matline_group[key][13]=line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.requisition_id and line.purchase_line_id.order_id.requisition_id.mr_lines and line.purchase_line_id.order_id.requisition_id.mr_lines[0].product_id
			matline_group[key][13]=line.product_id or ''
			matline_group[key][14]=line.purchase_line_id and line.purchase_line_id.part_number or ''
			matline_group[key][15]=line.purchase_line_id and line.purchase_line_id.catalogue_id and line.purchase_line_id.catalogue_id.catalogue or ''
			matline_group[key][16]=line.product_id and line.product_id.default_code or ''
			matline_group[key][17]=line.product_id and line.product_id.old_code or ''
			# matline_group[key][18]=line.purchase_line_id and line.purchase_line_id.discount_ids and line.purchase_line_id.discount_ids[0].discount_amt or 0.0
			matline_group[key][18]=line.purchase_line_id and line.purchase_line_id.discount_ids
			matline_group[key][19]=line.purchase_line_id and line.purchase_line_id.taxes_id
			matline_group[key][20]=line.product_id
			matline_group[key][21]=line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.partner_id
			if line.purchase_line_id:
				matline_group[key][22]+=self._amount_line(line)
			else:
				matline_group[key][22]+=0.0
		for x in matline_group.keys():
			res.append(matline_group[x])
		return res

	def _get_matline_amt(self,matline_obj):
		tot_amt=0
		for a in matline_obj:
			if a.purchase_line_id:
				if a.purchase_line_id and a.purchase_line_id.discount_ids and a.purchase_line_id.discount_ids[0]:
					discount=(a.purchase_line_id and a.purchase_line_id.discount_ids and a.purchase_line_id.discount_ids[0].discount_amt)/100
				else:
					discount=0
				# tot_amt=tot_amt+((a.purchase_line_id.price_unit-(a.purchase_line_id.price_unit*discount))*a.product_qty or 0.0)
				tot_amt=tot_amt+round(((a.purchase_line_id.price_unit-(a.purchase_line_id.price_unit*discount))*a.product_qty or 0.0),2)
		return tot_amt
	
	def _call_num2word(self,amount_total,cur):
		amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
		return amt_id

	


 
report_sxw.report_sxw('report.incoming.shipment.form', 'stock.picking.in', 'reporting_module/incoming_shipment_report/incoming_shipment_form.mako', parser=incoming_shipment_parser,header=False) 
