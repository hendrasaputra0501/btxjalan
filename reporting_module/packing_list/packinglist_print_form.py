import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word

class packing_list_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(packing_list_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'call_num2word':self._call_num2word,
			'packing_serial':self._packing_serial,
			'packingdtl_line':self._packingdtl_line,
			'packinglist_line':self._packinglist_line,
			'packingtot_line':self._packingtot_line,
			'get_lc_number':self._get_lc_number,
			'get_address':self._get_address,
			'get_label':self._get_label,
			'get_tracking':self._get_tracking,

		})

	def _packing_serial(self,number_obj):
		if number_obj:
			for a in number_obj:
				packing_nbr=a.replace(a[0],"I")
		else:
			packing_nbr=''
		return packing_nbr

	def _packingdtl_line(self,packingdtl_obj):
		res=[]
		totline_group={}
		for line in packingdtl_obj:
			key=(line.product_id)
			if key not in totline_group:
				totline_group[key]=["","",0,0,0]
			totline_group[key][0]=line.marks_nos
			totline_group[key][1]=line.product_desc
			totline_group[key][2]+=int(line.gross_weight)
			totline_group[key][3]+=int(line.net_weight)
			totline_group[key][4]+=int(line.volume)
		for x in totline_group.keys():
			res.append(totline_group[x])
		return res

	def _packinglist_line(self,packinglist_obj):
		res=[]
		totlist_group={}
		for line in packinglist_obj:
			key=(line.product_id)
			if key not in totlist_group:
				totlist_group[key]=[0,0,0,0,0,0,""]
			totlist_group[key][0]+=line.net_weight_per_cone
			totlist_group[key][1]+=line.gross_weight_per_cone
			totlist_group[key][2]+=line.total_cone
			totlist_group[key][3]+=line.package_net_weight
			totlist_group[key][4]+=line.package_gross_weight
			totlist_group[key][5]+=line.total_package
			totlist_group[key][6]=line and line.product_id and line.product_id.name 

		for x in totlist_group.keys():
			res.append(totlist_group[x])
		return res

	def _packingtot_line(self,packingtot_obj):
		totgross=0
		totnwt=0
		totvolume=0
		for line in packingtot_obj:
			totgross=totgross+line.gross_weight
			totnwt=totnwt+line.net_weight
			totvolume=totvolume+line.volume
		return totgross,totnwt,totvolume

	def _call_num2word(self,ammount_total,cur):
		amt_id=num2word.num2word_id(ammount_total,cur).decode('utf-8')
		return amt_id
		
	def _get_address(self, partner_obj):
		if partner_obj:
			partner_address = ''
			partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
			partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
			partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
			partner_address += partner_obj.city and partner_obj.city +' ' or ''
			partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
			partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''
			
			return  partner_address.replace('\n','<br />').upper()
		else:
			return False


 	def _get_lc_number(self, obj):
		lc_ids = []
		for picking in obj.picking_ids:
			for lc in picking.lc_ids:
				if lc.lc_type=='in' and lc not in lc_ids:
					lc_ids.append(lc)
		
		arr_temp_lc = []
		if lc_ids:
			for lc in lc_ids:
				arr_temp_lc.append(lc.lc_number)

		return arr_temp_lc and '<br/>'.join(arr_temp_lc) or ''

	def _get_label(self,obj):
	 	lc_objs = []
	 	if obj.picking_ids and obj.picking_ids[0].sale_id and (obj.picking_ids[0].sale_id.payment_method=='lc' or obj.picking_ids[0].sale_id.payment_method=='tt') :
	 		for picking in obj.picking_ids:
	 			if picking.lc_ids:
	 				for lc in picking.lc_ids:
	 					if lc not in lc_objs and lc.state not in ['canceled','nonactive','closed']:
	 						lc_objs.append(lc)
	 	label_dict = {}
	 	for lc in lc_objs:
	 		label_on_lc = eval(lc.label_print)
	 		if label_on_lc:
	 			for k,v in label_on_lc.items():
	 				if k not in label_dict:
	 					label_dict.update({k:v})
	 	if not lc_objs and not label_dict:
	 		label_dict = (eval(obj.label_print)).copy()
	 	return label_dict

	def _get_tracking(self,obj):
		if obj:
			move_lines = []
	 		if obj.booking_id and obj.booking_id.picking_ids:
	 			for move in [m for x in obj.booking_id.picking_ids for m in x.move_lines]:
	 				cek = True
	 				if move.product_id and obj.product_id:
	 					cek = cek and (move.product_id.id==obj.product_id.id)
	 				else:
	 					cek = cek and False

	 				if move.product_uop and obj.product_uop:
	 					cek = cek and (move.product_uop.id==obj.product_uop.id)
	 				else:
	 					cek = cek and False

	 				if move.product_uop_qty and obj.packages:
	 					cek = cek and (move.product_uop_qty==obj.packages)
	 				else:
	 					cek = cek and False

	 				if cek:
	 					move_lines.append(move)

	 		tracking_names = []
	 		tracking2 =False
	 		if move_lines:
	 			tracking_names=[(x.tracking_id.alias and x.tracking_id.alias or x.tracking_id.name) for x in move_lines if x.tracking_id]
	 		if tracking_names:
	 			tracking = tracking_names[0].decode("utf-8").encode("utf-8")
	 			if tracking and len(tracking)>1:
		 			temp = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","1","2","3","4","5","6","7","8","9","0"," "]
		 			tracking2 = list(tracking)
					for indx in range(0,len(tracking2)):
		 				if tracking2[indx] not in temp:
							tracking2.pop(indx)
		return obj.tracking_name and obj.tracking_name or (tracking2 and "".join(tracking2) or "")

	# def _get_lines(self, good_lines):
	# 	res_grouped = {}
	# 	for line in good_lines:
	# 		key = (line.product_id and line.product_id.id or False,
	# 			line.product_uop and line.product_uop.packing_type or False)
	# 		if key not in res_grouped:
	# 			res_grouped.update({
	# 				key : {
	# 					'marks_nos' : '',
	# 					'desc' : '',
	# 					'total_package' : 0,
	# 					'package_type' : '',
	# 					'gross_weight' : 0.0,
	# 					'net_weight' : 0.0,
	# 					'volume' : 0.0,
	# 					'package_detail': 
	# 					}
	# 				})
	# 		res_grouped[key]['marks_nos'] = 
	# 		res_grouped[key]['desc'] = 
	# 		res_grouped[key]['total_package'] += 
	# 		res_grouped[key]['package_type'] = 
	# 		res_grouped[key]['gross_weight'] += 
	# 		res_grouped[key]['net_weight'] += 
	# 		res_grouped[key]['volume'] += 

report_sxw.report_sxw('report.print.packinglist.form', 'container.booking', 'reporting_module/packing_list/packinglist_print_form_ok.html', parser=packing_list_parser,header=False) 
