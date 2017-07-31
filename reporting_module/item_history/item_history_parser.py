import re
import time
import xlwt
from report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
 
class item_history_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(item_history_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_item':self._get_item,
			'get_location':self._get_location,
			'get_result':self._get_result,
		})

	def _get_item(self, data):
		res = []
		product_id=data['product_id']
		query = "\
			SELECT coalesce(pfsc.code,'') || coalesce(pssc.code,'') || coalesce(third_segment_code,'') as item_code, \
				pp.name_template as item_description \
			FROM product_product pp \
			INNER JOIN product_first_segment_code pfsc ON pfsc.id=pp.first_segment_code \
			INNER JOIN product_second_segment_code pssc ON pssc.id=pp.second_segment_code \
			WHERE pp.id = '%s'" 	
		query = query%(product_id)
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _get_location(self,data):
		cr = self.cr
		uid = self.uid
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXX", "ADA" if data['location_exception'] else "TIDAK ADA"
		if not data['location_force']:
			location_ids = self.pool.get('stock.location').search(cr,uid,[('scrap_location','=',False),\
				('usage',"in",['internal','customer','supplier','inventory','production'])])
			#print "-----------sssssssssssssssssss----------",location_ids
		else:
			location_ids = data['location_force']
		if location_ids:
			#print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",sorted(list(set(location_ids)))
			all_loc_ids = self.pool.get('stock.location').search(cr,uid,[('id','in',sorted(list(set(location_ids))))],order="sequence asc, name asc")
			return self.pool.get('stock.location').browse(cr,uid,all_loc_ids)
		return []

	def _get_result(self, data, location_id):
		res = []
		start_date=data['start_date']
		end_date=data['end_date']
		product_id=data['product_id']

		#sp.internal_shipment_type 
		#pm_issue
		#pm_transfer
		#rm_issue
		#rm_return
		#fg_receipt
		#fg_return
		#fg_move
		#wm_issue
		#wm_receipt
		#fgo_receipt
		#ss_issue
		#ss_return
		#ss_transfer

		query_prod_receipt_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'production' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_prod_receipt_op = query_prod_receipt_op%(start_date,start_date,product_id,location_id)

		query_prod_return_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'production' \
				and sm.state='done'"
		query_prod_return_op = query_prod_return_op%(start_date,start_date,product_id,location_id)

		query_receipt_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'supplier' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_receipt_op = query_receipt_op%(start_date,start_date,product_id,location_id)

		query_purch_return_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'supplier' \
				and sm.state='done'"
		query_purch_return_op = query_purch_return_op%(start_date,start_date,product_id,location_id)

		query_issue_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'inventory' \
				and sm.state='done'"
		query_issue_op = query_issue_op%(start_date,start_date,product_id,location_id)

		query_dept_return_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'inventory' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_dept_return_op = query_dept_return_op%(start_date,start_date,product_id,location_id)

		query_transfer_in_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_transfer_in_op = query_transfer_in_op%(start_date,start_date,product_id,location_id)

		query_transfer_out_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_transfer_out_op = query_transfer_out_op%(start_date,start_date,product_id,location_id)

		query_sales_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'customer' \
				and sm.state='done'"
		query_sales_op = query_sales_op%(start_date,start_date,product_id,location_id)

		query_sales_return_op = "\
			SELECT \
				'%s'::date as tran_date, '_Opening' as tran_type, '' as doc_ref, \
				'' as source, '' as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date < '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'customer' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_sales_return_op = query_sales_return_op%(start_date,start_date,product_id,location_id)

		query_prod_receipt = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Production Receipt' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'production' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_prod_receipt = query_prod_receipt%(start_date,end_date,product_id,location_id)

		query_prod_return = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Production Return' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'production' \
				and sm.state='done'"
		query_prod_return = query_prod_return%(start_date,end_date,product_id,location_id)

		query_receipt = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Receipt' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'supplier' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_receipt = query_receipt%(start_date,end_date,product_id,location_id)

		query_purch_return = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Purchased Return' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'supplier' \
				and sm.state='done'"
		query_purch_return = query_purch_return%(start_date,end_date,product_id,location_id)

		query_issue = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Issue' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage in ('inventory','production') \
				and sm.state='done'"
		query_issue = query_issue%(start_date,end_date,product_id,location_id)

		query_dept_return = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, case when coalesce(sp.id,0)=0 then 'Adjustment' else 'Department Return' end as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'inventory' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_dept_return = query_dept_return%(start_date,end_date,product_id,location_id)

		query_transfer_in = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Transfer In' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_transfer_in = query_transfer_in%(start_date,end_date,product_id,location_id)

		query_transfer_out = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Transfer Out' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_transfer_out = query_transfer_out%(start_date,end_date,product_id,location_id)

		query_sales = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Sales' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				-sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				-sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and ssl.id='%s' \
				and ssl.usage = 'internal' \
				and dsl.usage = 'customer' \
				and sm.state='done'"
		query_sales = query_sales%(start_date,end_date,product_id,location_id)

		query_sales_return = "\
			SELECT \
				coalesce(sp.date_done,sm.date)::date as tran_date, 'Sales Return' as tran_type, sp.name as doc_ref, \
				coalesce(ssl.alias,ssl.name) as source, coalesce(dsl.alias,dsl.name) as destination, \
				sm.product_qty as qty, pu.name as uom, \
				coalesce(sm.price_unit, 0) as unit_price, \
				sm.product_qty*coalesce(sm.price_unit, 0) as amount \
			FROM \
				stock_move sm \
				LEFT OUTER JOIN stock_picking sp ON sp.id=sm.picking_id \
				INNER JOIN product_uom pu ON pu.id=sm.product_uom \
				LEFT JOIN stock_location ssl ON ssl.id=sm.location_id \
				LEFT JOIN stock_location dsl ON dsl.id=sm.location_dest_id \
			WHERE coalesce(sp.date_done,sm.date)::date between '%s' and '%s' \
				and sm.product_id='%s' \
				and dsl.id='%s' \
				and ssl.usage = 'customer' \
				and dsl.usage = 'internal' \
				and sm.state='done'"
		query_sales_return = query_sales_return%(start_date,end_date,product_id,location_id)
				
		query = "\
			SELECT ih.tran_date,ih.tran_type,ih.doc_ref,ih.source,ih.destination,ih.uom,\
			sum(ih.qty) as qty,avg(ih.unit_price) as unit_price,sum(ih.amount) as amount \
			FROM (\
			("+query_prod_receipt_op+") \
			UNION ALL \
			("+query_prod_return_op+") \
			UNION ALL \
			("+query_receipt_op+") \
			UNION ALL \
			("+query_purch_return_op+") \
			UNION ALL \
			("+query_issue_op+") \
			UNION ALL \
			("+query_dept_return_op+") \
			UNION ALL \
			("+query_transfer_in_op+") \
			UNION ALL \
			("+query_transfer_out_op+") \
			UNION ALL \
			("+query_sales_op+") \
			UNION ALL \
			("+query_sales_return_op+") \
			UNION ALL \
			("+query_prod_receipt+") \
			UNION ALL \
			("+query_prod_return+") \
			UNION ALL \
			("+query_receipt+") \
			UNION ALL \
			("+query_purch_return+") \
			UNION ALL \
			("+query_issue+") \
			UNION ALL \
			("+query_dept_return+") \
			UNION ALL \
			("+query_transfer_in+") \
			UNION ALL \
			("+query_transfer_out+") \
			UNION ALL \
			("+query_sales+") \
			UNION ALL \
			("+query_sales_return+")) ih\
			GROUP BY ih.tran_date,ih.tran_type,ih.doc_ref,ih.source,ih.destination,ih.uom\
			ORDER BY ih.tran_date,ih.tran_type,ih.doc_ref,ih.source,ih.destination,ih.uom"
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		# print query
		# print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		self.cr.execute(query)
		res = self.cr.dictfetchall()
		return res

	def _uom_to_base(self,data,qty,uom_source,dest_uom_name):
		cr = self.cr
		uid = self.uid
		uom_base = dest_uom_name
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result


	def _price_per_base(self,data,price,uom_source,dest_uom_name):
		cr = self.cr
		uid = self.uid
		uom_base = dest_uom_name
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=base and base[0] or False)
		if qty_result>0:
		  price_result = price*1000.0/qty_result 
		else:
		  price_result = price 
		return price_result
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

	def _get_date_range(self,data):
		date_start = data['start_date']
		date_stop = data['end_date']
		if date_start and not date_stop:
			da = datetime.strptime(date_start,"%Y-%m-%d")
			return "From : %s"%da.strftime("%d/%m/%Y")
		elif date_stop and not date_start:
			db = datetime.strptime(date_stop,"%Y-%m-%d")
			return "Until : %s"%db.strftime("%d/%m/%Y")
		elif date_stop and date_start:
			da = datetime.strptime(date_start,"%Y-%m-%d")
			db = datetime.strptime(date_stop,"%Y-%m-%d")
			return "%s - %s"%(da.strftime("%d/%m/%Y"),db.strftime("%d/%m/%Y"))
		else:
			return "Wholetime"

class item_history_xls(report_xls):
	def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
		if not context:
			context = {}
		context = context.copy()
		rml_parser = self.parser(cr, uid, self.name2, context=context)
		objs = []
		rml_parser.set_context(objs, data, ids, 'xls')
		n = cStringIO.StringIO()
		wb = xlwt.Workbook(encoding='utf-8')
		self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
		wb.save(n)
		n.seek(0)
		return (n.read(), 'xls')
 
	def generate_xls_report(self, parser, data, obj, wb):
		ws = wb.add_sheet('Item History',cell_overwrite_ok=True)
		ws.panes_frozen = True
		ws.remove_splits = True
		ws.portrait = 0 # Landscape
		ws.fit_width_to_pages = 1 

		title_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		title_style_left				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; pattern : pattern solid, fore_color white;')
		th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed')
		th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom dashed')
		
		normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float4 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.0000;-#,##0.0000')
		normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold 		= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style 				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz center; borders: bottom thin;')
		subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style_left				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		
		label = xlwt.easyxf('font : name calibri, colour_index black; align: vert centre, horiz center;' "borders:top dashed, bottom thin")
		body_detail2 = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz right;')
		body_detail = xlwt.easyxf('font: name Calibri, colour_index black; align: wrap on, vert center, horiz left;')

		items = parser._get_item(data)
		for item in items:
			ws.write_merge(0,0,0,11,"Item History : "+item['item_code']+'-'+item['item_description'], title_style) 
		ws.write_merge(1,1,0,11, "Period: ("+parser._get_date_range(data)+") As of : "+time.strftime('%d/%m/%Y'), title_style)
		
		ws.write_merge(3,4,0,1, "Tran Date", th_both_style)
		ws.write_merge(3,4,2,2, "Tran Type", th_both_style)
		ws.write_merge(3,4,3,3, "Doc Ref", th_both_style)
		ws.write_merge(3,4,4,4, "Source", th_both_style)
		ws.write_merge(3,4,5,5, "Destination", th_both_style)
		ws.write_merge(3,4,6,6, "Qty", th_both_style)
		ws.write_merge(3,4,7,7, "UOM", th_both_style)
		ws.write_merge(3,4,8,8, "Unit Price", th_both_style)
		ws.write_merge(3,4,9,9, "Amount", th_both_style)
		ws.write_merge(3,3,10,11, "Balance", th_top_style)
		ws.write(4,10, "Qty", th_bottom_style)
		ws.write(4,11, "Amount", th_bottom_style)
		
		rowcount=5
		qty = 0.0
		amount = 0.0

		max_width_col ={
			0:8,1:10,2:10,3:10,4:10,5:10,6:8,7:8,8:8,9:8,10:8,11:8,12:8
		}
		
		loc_ids = parser._get_location(data)

		for loc in loc_ids:
			lcount=0
			result=parser._get_result(data,loc['id'])

			for line in result:
				if lcount==0:
					ws.write(rowcount,0,loc['name'], normal_style)
					rowcount+=1
				ws.write(rowcount,1,line['tran_date'], normal_style)			
				ws.write(rowcount,2,line['tran_type'], normal_style)			
				ws.write(rowcount,3,line['doc_ref'], normal_style)			
				ws.write(rowcount,4,line['source'], normal_style)			
				ws.write(rowcount,5,line['destination'], normal_style)			
				ws.write(rowcount,6,line['qty'], normal_style_float)			
				ws.write(rowcount,7,line['uom'], normal_style)
				if abs(line['qty'])>0.0:			
					ws.write(rowcount,8,round(line['amount']/line['qty'],4), normal_style_float4)			
				else:
					ws.write(rowcount,8,line['unit_price'], normal_style_float4)			
				ws.write(rowcount,9,line['amount'], normal_style_float)			
				if lcount == 0:
					qty = line['qty']
					amount = line['amount']
				else:
					qty += line['qty']
					amount += line['amount']
				ws.write(rowcount,10,qty, normal_style_float)			
				ws.write(rowcount,11,amount, normal_style_float)
				rowcount+=1
				lcount+=1			

		for x in range(0,12):
			ws.col(x).width = 256*int(max_width_col[x]*1.4)
		pass

		pass

item_history_xls('report.item.history','item.history.wizard','addons/reporting_module/item_history/item_history.mako', parser=item_history_parser, header=False)