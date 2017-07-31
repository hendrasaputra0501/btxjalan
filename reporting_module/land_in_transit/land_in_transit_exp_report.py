import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter
from datetime import datetime


class land_in_transit_exp_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(land_in_transit_exp_parser, self).__init__(cr, uid, name, context=context)		
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
		uom_categ = self.pool.get('product.uom.categ').search(cr,uid,[('name','=','Bitratex Weight')])
		
		ctx = {}
		base = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
		totalqty=0
		for line in list_transact_obj:
			date_do = line.date_done
			key=(date_do,line.truck_number,line.partner_id.name)
			if key not in list_group:
				list_group[key]=["","",0,0,0,[],"","",[]]
			ctx.update({'date':ins_obj.entry_date!='False' and ins_obj.entry_date or time.strftime('%Y-%m-%d')})
			curry_id=line.invoice_id and line.invoice_id.currency_id and line.invoice_id.currency_id.id
			price_subtotal = 0.0
			product_qty = 0.0
			current_inv_line = []
			for move_line in line.move_lines:
				product_qty+=move_line.product_qty
				if move_line.invoice_line_id and move_line.invoice_line_id.id not in current_inv_line:
					price_subtotal+=move_line.invoice_line_id.price_subtotal
					current_inv_line.append(move_line.invoice_line_id.id)
			list_group[key][0]=date_do
			list_group[key][1]=line.partner_id.name
			totalSub_qty=0
			for sj_line in line.move_lines:
				uom2_id=sj_line.product_uom and sj_line.product_uom.id
				totalSub_qty+=uom_obj._compute_qty(cr, uid, uom2_id,sj_line.product_qty,to_uom_id=base and base[0] or False)
			list_group[key][2]+=totalSub_qty
			list_group[key][3]+=curr_obj.compute(cr, uid, curry_id, ins_obj.currency_id.id, price_subtotal, context=ctx)
			#int(line.move_lines and line.move_lines[0].invoice_line_id and line.move_lines[0].invoice_line_id.price_subtotal)
			list_group[key][4]+=curr_obj.compute(cr, uid, curry_id, ins_obj.currency_id.id, price_subtotal+(price_subtotal*10/100), context=ctx)
			if line.container_number and line.container_number not in list_group[key][5]:
				list_group[key][5].append(line.container_number)
			list_group[key][6]=line.partner_id and line.partner_id.city or (line.container_book_id and line.container_book_id.port_to.name or '')
			list_group[key][7]=line.partner_id and line.partner_id.country_id and line.partner_id.country_id.name or (line.container_book_id and line.container_book_id.port_to_desc or '')
			if line.invoice_id and line.invoice_id.internal_number and line.invoice_id.internal_number not in list_group[key][8]:
				list_group[key][8].append(line.invoice_id and line.invoice_id.internal_number or '')

		for x in list_group.keys():
			res.append(list_group[x])
		return res
report_sxw.report_sxw('report.land.transit.exp.rpt', 'insurance.polis', 'reporting_module/land_in_transit/land_in_transit_exp_report.mako', parser=land_in_transit_exp_parser,header=False)