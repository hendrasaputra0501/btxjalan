import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
from operator import itemgetter

class sca_rpt_parser(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(sca_rpt_parser, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'call_num2word':self._call_num2word,
			"get_result":self._get_result,
			"get_price_usd":self.get_price_usd,
			"get_rate":self._get_rate,
			"get_lines":self._get_lines,
		})
		   
	
	def _call_num2word(self,amount_total,cur):
		amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
		return amt_id

	def get_price_usd(self, rfq, price_unit, sca_date):
		currency_pool = self.pool.get("res.currency")
		usd_amt = 0.0
		
		company_curr = rfq.company_id and rfq.company_id.currency_id.id
		po_curr = rfq.pricelist_id and rfq.pricelist_id.currency_id and rfq.pricelist_id.currency_id.id
		ctx = {'date':sca_date!='False' and sca_date or time.strftime('%Y-%m-%d')}
		usd_amt = currency_pool.compute(self.cr, self.uid, po_curr, company_curr, (price_unit or 0.0), context=ctx)
		
		return usd_amt

	def _get_rate(self, purc_req_obj):
		cr=self.cr
		uid=self.uid
		curr_obj = self.pool.get('res.currency')

		ctx = {'date':purc_req_obj.sca_date!='False' and purc_req_obj.sca_date or time.strftime('%Y-%m-%d')}
		curry_id=purc_req_obj.company_id and purc_req_obj.company_id.currency_id and purc_req_obj.company_id.currency_id
		rate_dict = {}
		for rfq in purc_req_obj.purchase_ids:
			cury_id2= rfq.pricelist_id and rfq.pricelist_id.currency_id
			if rfq not in rate_dict:
				rate=curr_obj._get_conversion_rate(cr, uid,curry_id,cury_id2 ,  context=ctx)
				rate_dict.update({cury_id2.name : rate})
		return rate_dict

	def _get_lines(self, obj):

		res = {}
		for line in obj.line_ids:
			key = line.product_id
			if key not in res:
				last_price = line.product_id.last_price
				last_po = line.product_id and line.product_id.last_order_id and line.product_id.last_order_id.name or ''
				last_po_date =  line.product_id and line.product_id.last_date_order
				last_po_vendor = line.product_id and line.product_id.last_partner_id and line.product_id.last_partner_id.name or ''
				last_po_currency =  line.product_id and line.product_id.last_order_id and line.product_id.last_order_id.pricelist_id and line.product_id.last_order_id.pricelist_id.currency_id and line.product_id.last_order_id.pricelist_id.currency_id.name or ''
				# print line.product_id.id,last_price,"----------------------------------------"
				if not last_price:
					cr=self.cr
					uid=self.uid
					order_product_obj=self.pool.get('product.undefined.info')
					id_product=order_product_obj.search(cr,uid,[('product_id','=',line.product_id.id)],order='po_date desc',limit=1)
					if id_product:
						product_undefined_obj = self.pool.get('product.undefined.info').browse(cr,uid,id_product)[0]
						last_price=product_undefined_obj.price_unit
						last_po=product_undefined_obj.po_number
						last_po_date=product_undefined_obj.po_date
						last_po_vendor=product_undefined_obj.partner_name
						last_po_currency=product_undefined_obj.currency_id.name
					# print line.product_id.id,last_price,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
				res.update({key:{
					'seq' : line.id,
					'product_id' : line.product_id.id,
					'product_code' : line.product_id.default_code,
					'product_name' : line.product_id.name,
					'last_po' : last_po,
					'last_po_date' : last_po_date,
					'last_po_vendor' : last_po_vendor,
					'last_po_currency' :  last_po_currency,
					'last_price' : last_price,
					}})
		last_pr_id = max([v['seq'] for v in res.values()])
		for rfq in obj.purchase_ids:
			if rfq.state != 'cancel':
				for line in rfq.order_line:
					if not line.product_id or line.other_cost_type:
						continue
					key = line.product_id
					if key not in res:
						last_pr_id += 1
						last_price = line.product_id.last_price
						last_po=line.product_id.last_order_id.name
						last_po_date = line.product_id.last_date_order
						last_po_vendor = line.product_id.last_partner_id.name
						last_po_currency =  line.product_id and line.product_id.last_order_id and line.product_id.last_order_id.pricelist_id and line.product_id.last_order_id.pricelist_id.currency_id and line.product_id.last_order_id.pricelist_id.currency_id.name 
						
						# last_po = line.last_order_id and line.last_order_id.name or ''
						# last_po_date = line.last_date_order
						# last_po_vendor = line.last_partner_id and line.last_partner_id.name or ''
						# last_po_currency =  line.last_order_id and line.last_order_id.pricelist_id and line.last_order_id.pricelist_id.currency_id and line.last_order_id.pricelist_id.currency_id.name or ''
						if not last_price:
							cr=self.cr
							uid=self.uid
							order_product_obj=self.pool.get('product.undefined.info')
							id_product=order_product_obj.search(cr,uid,[('product_id','=',line.product_id.id)],order='po_date desc',limit=1)
							if id_product:
								product_undefined_obj = self.pool.get('product.undefined.info').browse(cr,uid,id_product)[0]
								last_price=product_undefined_obj.price_unit
								last_po=product_undefined_obj.po_number
								last_po_date=product_undefined_obj.po_date
								last_po_vendor=product_undefined_obj.partner_name
								last_po_currency=product_undefined_obj.currency_id.name
						res.update({key:{
							'seq' : last_pr_id,
							'product_id' : line.product_id.id,
							'product_code' : line.product_id.default_code,
							'product_name' : line.product_id.name,
							'last_po' : last_po,
							'last_po_date' : last_po_date,
							'last_po_vendor' : last_po_vendor,
							'last_po_currency' :  last_po_currency,
							'last_price' : last_price,
							
							}})
						# print line.product_id.id,last_price,"+++++++++++++++++++++++++++++++++++++++++++"
		return res and res.values() or []


	def _get_result(self, data):
		prid = data.id
		sql= "\
				select sca.product_id as product_id,\
						sca.default_code default_code,\
						sca.sca_req_id as sca_req_id,\
						sca.partner_id as  partner_id,\
						sca.name_partner as name_partner,\
						sca.price_unit as price_unit,\
						sca.price_unit_oth\
						from(\
							select pp.id as product_id,\
							poa.requisition_id as sca_req_id,\
							pap.name as name_partner,\
							pol.price_unit,\
							pp.default_code,\
							poa.partner_id, \
							coalesce(pui.price_unit,0.00) as price_unit_oth\
							from purchase_order_sca poa \
								left outer join res_partner pap on poa.partner_id=pap.id \
								left outer join purchase_order_line pol on poa.po_line_id=pol.id \
								left outer join product_product pp on pol.product_id=pp.id \
								left outer join product_undefined_info pui on pui.product_id=pp.id \
								) sca\
								left join (\
									select prl.product_id,\
									pr.id\
									from purchase_requisition_line prl\
									 	left  join purchase_requisition pr on prl.requisition_id=pr.id)prq\
											on sca.product_id=prq.product_id and sca.sca_req_id=prq.id\
						where sca.sca_req_id='%s'\
			"
		sql = sql%(str(prid))
		self.cr.execute(sql)
		res = self.cr.dictfetchall()
		return res
 
report_sxw.report_sxw('report.sca.report', 'purchase.requisition', 'reporting_module/sca_report/sca_report.mako', parser=sca_rpt_parser,header=False) 
