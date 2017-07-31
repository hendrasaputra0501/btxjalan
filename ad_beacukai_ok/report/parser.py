import time
import datetime
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word

class beacukai_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(beacukai_parser, self).__init__(cr, uid, name, context=context)
		if name and name=='bc40.form' or name=='bc40_1.form':
			context.update({'document_type':'40'})
		elif name and name=='bc41.form' or name=='bc41_1.form' or name=='bc41_1_310.form':
			context.update({'document_type':'41'})
		elif name and name=='bc27.form' or name=='bc27_1.form' or name=='bc27_1_310.form':
			context.update({'document_type':'27'})

		bc = self.pool.get('beacukai').browse(cr, uid, context['active_ids'])[0]
		if context.get('document_type',False) and context.get('document_type',False)!="27":
			if bc.document_type!=context.get('document_type',False):
				raise osv.except_osv(_('Warning.'), _('You can not print this document on wrong menu !'))
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_tpb_type':self.get_tpb_type,
			'get_purpose':self.get_purpose,
			'get_address':self.get_address,
			'get_source_bc_number':self.get_source_bc_number,
			'get_contracts':self.get_contracts,
			'get_products':self.get_products,
		})

	def get_tpb_type(self, tpb_type):
		result = ''
		tpb_dict = {
			'berikat_wh':'Gudang Berikat',
			'berikat_area':'Kawasan Berikat',
			'berikat_exh':'Tempat Penyelenggaraan Pameran Berikat',
			'free_cost_shop':'Toko Bebas Bea',
			'berikat_auction':'Tempat Lelang Berikat',
			'berikat_refurbish':'Kawasan Daur Ulang Berikat',
		}
		if tpb_type in tpb_dict.keys():
			result = tpb_dict[tpb_type]

		return result

	def get_purpose(self, purpose):
		result = ''
		purpose_dict = {
			'subcont':'Subcontracted',
			'lent':'Lent',
			'repair':'Repair',
			'exhibit':'Exhibition',
			'other':'Lainnya',
		}
		if purpose in purpose_dict.keys():
			result = purpose_dict[purpose]
		print "==================",result	

		return result

	def get_address(self, partner):
		if partner:
			address = partner
			partner_address = ''
			partner_address += address.street and address.street + ', ' or ''
			partner_address += address.street2 and address.street2 +'. ' or ''
			partner_address += address.street3 and address.street3 +'. ' or ''
			partner_address += address.city and address.city +' ' or ''
			partner_address += address.zip and address.zip +', ' or ''
			partner_address += address.country_id.name and address.country_id.name or ''
			return  partner_address.replace('\n','<br />').upper()
		else:
			return ''

	def get_source_bc_number(self, picking):
		bc_number = ''
		bc_number = picking.supplier_bc_reference or ''
		return bc_number

	def get_contracts(self, obj):
		res={
			'contracts':[],
			'contracts_date':[]
		}
		if obj.shipment_type=='out':
			for sale in obj.sale_ids:
				res['contracts'].append(sale.name)
				res['contracts_date'].append(sale.date_order)
		elif obj.shipment_type=='in':
			for purchase in obj.purchase_ids:
				res['contracts'].append(purchase.name)
				res['contracts_date'].append(purchase.date_order)
		return res

	def get_products(self, moves):
		group_products = {}
		res = []
		if not moves:
			return []
		i = 0
		for move in moves:
			key = "%s-%s-%s-%s"%(move.product_id.id,move.product_uom.id,move.price_unit,str(i))
			if key not in group_products:
				i+=1
				group_products.update({key:{}})
				group_products[key].update({
					'index':i,
					'product':move.product_id.name,
					'qty':0.0,
					'uom':move.product_uom_kgs and move.product_uom_kgs.name or move.product_uom and move.product_uom.name or '',
					'price':0.0,
					'details':{}
					})
			group_products[key]['qty']+= move.product_qty_kgs or move.product_qty or 0.0
			group_products[key]['price']+= move.price_subtotal_idr
			if move.move_id:
				for x in move.move_id.stock_move_line_ids:
					if x.product_id and x.product_id.id not in group_products[key]['details'].keys():
						group_products[key]['details'].update({x.product_id.id:["",0.0,""]})
					group_products[key]['details'][x.product_id.id][0] = x.description or x.product_id.name or ""
					group_products[key]['details'][x.product_id.id][1] += (x.product_qty or 0.0)
					group_products[key]['details'][x.product_id.id][2] = x.product_uom and x.product_uom.name or ""
		s = sorted(group_products.items(),key=lambda y:y[1])
		for x in s:
			res.append(x[1])
		return res

# report_sxw.report_sxw('report.bc27.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_27.html', parser=beacukai_parser,header=False)
from netsvc import Service
try:
	del Service._services['report.bc40.form']
	del Service._services['report.bc41.form']
except:
	pass

report_sxw.report_sxw('report.bc40.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_40.html', parser=beacukai_parser,header=False)
report_sxw.report_sxw('report.bc40_1.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_40_1.html', parser=beacukai_parser,header=False)

report_sxw.report_sxw('report.bc41.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_41.html', parser=beacukai_parser,header=False)
report_sxw.report_sxw('report.bc41_1.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_41_1.html', parser=beacukai_parser,header=False)
report_sxw.report_sxw('report.bc41_1_310.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_41_1_310.html', parser=beacukai_parser,header=False)
report_sxw.report_sxw('report.bc27_1.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_27_1.html', parser=beacukai_parser,header=False)
report_sxw.report_sxw('report.bc27_1_310.form', 'beacukai', 'ad_beacukai_ok/report/mako/bc_27_1_310.html', parser=beacukai_parser,header=False)