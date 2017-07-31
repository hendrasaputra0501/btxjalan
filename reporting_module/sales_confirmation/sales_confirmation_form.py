import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter

class sales_confirmation_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(sales_confirmation_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_upper_incoterm':self._get_incoterm_code,
			'get_total_line':self._get_totline_qty,
			'call_num2word':self._call_num2word,
			'get_prodline_group':self._get_prodline_group,
			'get_prod_remarks':self._get_prod_remarks,
            'uom_to_kgs': self._uom_to_kgs,            
            'price_per_kgs': self._price_per_kgs,
            'get_qtyshipment' :self._get_qtyshipment,
		})
		   
	def _get_incoterm_code(self,incoterm_obj):
		if incoterm_obj:
			return incoterm_obj.code.upper()
		else:
			False
		

	def _get_prodline_group(self,prodline_obj):
		res=[]
		prod_group={}
		for line in prodline_obj:
			key=(line.id)
			if key not in prod_group:
				prod_group[key]=["","","","","",0,"",0,0,"","",0,0,"","","",0,0,"","","",False,"","",0,False,"",0,""]
			prod_group[key][0]=line.product_id.name
			prod_group[key][1]=line.packing_type.name
			prod_group[key][2]=line.tpi
			prod_group[key][3]=line.cone_weight
			prod_group[key][4]=line.sequence_line
			prod_group[key][5]=line.product_uom_qty
			prod_group[key][6]=line.product_uom and line.product_uom.name
			prod_group[key][7]=line.price_unit
			prod_group[key][8]=line.price_unit*line.product_uom_qty
			prod_group[key][9]=line.est_delivery_date
			prod_group[key][10]=line.remarks
			prod_group[key][11]+=int(line.product_uom_qty)
			prod_group[key][12]+=int(line.price_unit*line.product_uom_qty)
			prod_group[key][13]=line.product_id and line.product_id.hscode or ''
			prod_group[key][14]=line.bom_id and line.bom_id.name
			prod_group[key][15]=line.remarks
			prod_group[key][16]=line.cone_weight
			prod_group[key][17]=line.id
			prod_group[key][18]=line.packing_detail
			prod_group[key][19]=line.name
			prod_group[key][20]=line.sale_type=='export' and line.export_desc or line.local_desc
			prod_group[key][21]=line.use_template_on_print 
			prod_group[key][22]=line.sale_type=='export' and line.product_id.export_desc  or line.product_id.local_desc 
			prod_group[key][23]=line.application
			prod_group[key][24]=line.product_uom.id
			prod_group[key][25]=line.container_size and line.container_size.desc or False
			prod_group[key][26]=line.tpm
			prod_group[key][27]=line.product_id.id
			prod_group[key][28]=line.knock_off

		# for x in prod_group.keys():
		for x in prod_group.keys():
			res.append(prod_group[x])
			result=sorted(res, key=lambda res:res[17])
		return result
		#return res

	def _get_totline_qty(self,ordline_obj):
		cr=self.cr
		uid=self.uid
		context=None
		tot_qty=0
		tot_amt=0
		for a in ordline_obj:
			stockmove_obj=self.pool.get('stock.move')
			stockmove_ids=stockmove_obj.search(cr,uid,[('sale_line_id','=',a.id),('product_id','=',a.product_id.id)])
			qty_shipment=0.00
			if stockmove_ids:
				for moveline in stockmove_ids:
					qty_shipment=stockmove_obj.browse(cr,uid,moveline,context=context).product_qty
			if not a.knock_off or (a.knock_off and a.product_uom_qty==qty_shipment):
				tot_qty=tot_qty+a.product_uom_qty
				tot_amt=tot_amt+round((a.product_uom_qty*a.price_unit),2)
		return tot_qty,tot_amt


	def _get_qtyshipment(self,soline_id,productline_id):
		cr=self.cr
		uid=self.uid
		context=None
		stockmove_obj=self.pool.get('stock.move')
		stockmove_ids=stockmove_obj.search(cr,uid,[('sale_line_id','=',soline_id),('product_id','=',productline_id)])
		qty_shipment=0.00
		if stockmove_ids:
			for moveline in stockmove_ids:
			# qty_received=self.pool.get('stock.move').browse(cr,uid,move_line,context=context).product_qty
				qty_shipment=stockmove_obj.browse(cr,uid,moveline,context=context).product_qty
		return qty_shipment

	def _get_prod_remarks(self,prodrmk_obj):
		res=[]
		prod_group={}
		for line in prodrmk_obj:
			key=(line.product_id.name)
			if key not in prod_group:
				prod_group[key]=["",""]
			prod_group[key][0]=line.product_id.name
			prod_group[key][1]=line.other_description
		for x in prod_group.keys():
			res.append(prod_group[x])
		return res

    # def _get_totline(self,invline_obj):
    #     res=[]
    #     totline_group={}
    #     for line in invline_obj:
    #         key=(line.product_id,line.account_id)
    #         if key not in totline_group:
    #             totline_group[key]=["","","",0,0,0]
    #         totline_group[key][0]=line.invoice_id and line.invoice_id.picking_ids and line.invoice_id.picking_ids.container_book_id and line.invoice_id.picking_ids.container_book_id.good_lines and line.invoice_id.picking_ids.container_book_id.good_lines.marks_nos
    #         totline_group[key][1]=line.name
    #         totline_group[key][2]=line.uos_id and line.uos_id.name
    #         totline_group[key][3]+=int(line.quantity)
    #         totline_group[key][4]+=int(line.price_unit)
    #         totline_group[key][5]+=int(line.price_subtotal)

    #     for x in totline_group.keys():
    #         res.append(totline_group[x])
    #     return res


	def _call_num2word(self,ammount_total,cur):
		amt_id=num2word.num2word_id(ammount_total,cur).decode('utf-8')
		return amt_id

	def _uom_to_kgs(self,qty,uom_source):
		print '+++++++++++++++++++++++++++++++'
		print uom_source
		cr = self.cr
		uid = self.uid
		kgs = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=kgs and kgs[0] or False)
		return qty_result

	def _price_per_kgs(self,price,uom_source):
		print '+++++++++++++++++++++++++++++++'
		print uom_source
		cr = self.cr
		uid = self.uid
		kgs = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=kgs and kgs[0] or False)
		if qty_result>0:
			price_result = price*1000.0/qty_result 
		else:
			price_result = price 
		return price_result

report_sxw.report_sxw('report.sales.confirmation.form', 'sale.order', 'reporting_module/sales_confirmation/sales_confirmation_form.mako', parser=sales_confirmation_parser,header=False) 