import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter
from datetime import datetime


class land_in_transit_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(land_in_transit_parser, self).__init__(cr, uid, name, context=context)		
		self.localcontext.update({
			'time' : time,
			'get_list_transaction' : self._get_list_transaction,
		})

	def _get_list_transaction(self, ins_obj,list_transact_obj):
		res=[]
		list_group={}
		cr=self.cr
		uid=self.uid
		curr_obj = self.pool.get('res.currency')
		uom_obj = self.pool.get('product.uom')
		tax_obj = self.pool.get('account.tax')
		
		ctx = {}
		base = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
		for line in list_transact_obj:
			if ins_obj.type=='purchase' and not line.purchase_id:
				continue

			date_do = line.date_done
			key=(date_do,line.truck_number,line.partner_id.name)
			if key not in list_group:
				list_group[key]=["","",0,0,0,"","",[],0,0,0,False]
			# if ins_obj.type=='purchase':
			# 	ctx.update({'date':datetime.strptime(date_do!='False' and date_do or time.strftime('%Y-%m-%d'),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')})
			# else:
			ctx.update({'date':ins_obj.entry_date!='False' and ins_obj.entry_date or time.strftime('%Y-%m-%d')})
			curry_id=ins_obj.type=='sale' and (line.invoice_id and line.invoice_id.currency_id and line.invoice_id.currency_id) or line.purchase_id.pricelist_id.currency_id
			price_subtotal = 0.0
			price_subtotal_2 = 0.0
			product_qty = 0.0
			current_inv_line = []
			for move_line in line.move_lines:
				qty_kgs = uom_obj._compute_qty(cr, uid, move_line.product_uom.id, ins_obj.type=='purchase' and (move_line.net_weight or move_line.product_qty) or move_line.product_qty ,to_uom_id=base and base[0] or False, round=False)
				qty_to_uom_po_line = ins_obj.type=='purchase' and move_line.purchase_line_id and uom_obj._compute_qty(cr, uid, move_line.product_uom.id, move_line.net_weight or move_line.product_qty, to_uom_id=move_line.purchase_line_id.product_uom.id) or 0.0
				if move_line.invoice_line_id and move_line.invoice_line_id.id not in current_inv_line: 
					price_subtotal+=ins_obj.type=='sale' and (move_line.invoice_line_id and move_line.invoice_line_id.price_subtotal or 0.0) or (move_line.purchase_line_id and tax_obj.compute_all(cr, uid, move_line.purchase_line_id.taxes_id, move_line.purchase_line_id.price_unit, move_line.product_qty, product=(move_line.purchase_line_id.product_id or False), partner=(move_line.purchase_line_id.order_id.partner_id or False))['total'] or 0.0)
					price_subtotal_2+=ins_obj.type=='sale' and (move_line.invoice_line_id and move_line.invoice_line_id.price_subtotal or 0.0) or (round(move_line.product_qty*move_line.price_unit,2) or 0.0)
					current_inv_line.append(move_line.invoice_line_id.id)
				# price_subtotal+=ins_obj.type=='sale' and (move_line.invoice_line_id and move_line.invoice_line_id.price_subtotal or 0.0) or (move_line.purchase_line_id and move_line.price_unit*move_line.product_qty or 0.0)
				product_qty+=qty_kgs
			
			list_group[key][0]=date_do
			list_group[key][1]=line.partner_id.name
			list_group[key][2]+=product_qty
			# list_group[key][3]+=curr_obj.compute(cr, uid, curry_id.id, ins_obj.currency_id.id, price_subtotal, round=False, context=ctx)
			list_group[key][3]+=ins_obj.type=='sale' and curr_obj.compute(cr, uid, curry_id.id, ins_obj.currency_id.id, price_subtotal_2, round=False, context=ctx) or price_subtotal_2
			#int(line.move_lines and line.move_lines[0].invoice_line_id and line.move_lines[0].invoice_line_id.price_subtotal)
			# list_group[key][4]+=curr_obj.compute(cr, uid, curry_id.id, ins_obj.currency_id.id, price_subtotal+(price_subtotal*10/100), round=False, context=ctx)
			list_group[key][4]+=ins_obj.type=='sale' and curr_obj.compute(cr, uid, curry_id.id, ins_obj.currency_id.id, price_subtotal_2+(price_subtotal_2*10/100), round=False, context=ctx) or (price_subtotal_2+(price_subtotal_2*10/100))
			
			list_group[key][5]=line.truck_number
			list_group[key][6]=line.partner_id and line.partner_id.shipment_local_area_id and line.partner_id.shipment_local_area_id.name or line.partner_id.street3 or line.partner_id.street2 or ''
			if ins_obj.type=='sale' and line.invoice_id and line.invoice_id.internal_number and line.invoice_id.internal_number not in list_group[key][7]:
				list_group[key][7].append(line.invoice_id and line.invoice_id.internal_number or '')
			list_group[key][8]+=price_subtotal
			list_group[key][9]+=price_subtotal+(price_subtotal*10/100)
			list_group[key][10]=curr_obj._get_conversion_rate(cr, uid, ins_obj.currency_id, curry_id, context=ctx)
			list_group[key][11]=curry_id
		for x in list_group.keys():
			res.append(list_group[x])
		return res
report_sxw.report_sxw('report.land.transit.rpt', 'insurance.polis', 'reporting_module/land_in_transit/land_in_transit_report.mako', parser=land_in_transit_parser,header=False)