import time
import datetime
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word

class inventory_issue(report_sxw.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(inventory_issue, self).__init__(cr, uid, name, context=context)		
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			'get_qty_bale' : self._get_qty_bale,
			'get_move_lines' : self._get_move_lines,
		})

	def _get_qty_bale(self,uom_id,uom_qty):
		cr=self.cr
		uid=self.uid
		uom_obj = self.pool.get('product.uom')
		# precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
		qty = 0.00000
		if not uom_id or not uom_qty:
			return qty
		uom_bale_ids = uom_obj.search(cr, uid, [('name','like','BALES')])
		# uom_kgs = uom_obj.browse(cr, uid, uom_id)
		if uom_bale_ids:
			qty = uom_obj._compute_qty(cr, uid, uom_id, uom_qty, uom_bale_ids[0])
		return qty

	def _get_move_lines(self, obj):
		query = "\
		SELECT coalesce(a.price_unit,0) as price_unit, a.id as sequence,c.id as prod_id, c.internal_type, c.default_code as code, d.name as desc, coalesce(to_char(b.date_done, 'DD/MM/YY'),'-') as trans_date, \
		f.id as dest_loc_id, coalesce(f.alias,f.name) as site_loc, f.name as site_loc_name, coalesce(e.alias,e.name) as source_loc, h.name as uop, a.product_uop_qty as qty2, \
		g.name as uom, g.id as uom_id, a.product_qty as qty1, i.name as lot,j.code as reasoncode,k.code as analytic_account, \
		a.remarks as remarks, coalesce(b.goods_type,'') as goods_type,coalesce(move_pres.qty_kg_pres,0) as qty_onhand \
		FROM stock_move a \
		INNER JOIN stock_picking b ON b.id=a.picking_id \
		LEFT JOIN product_product c ON c.id=a.product_id \
		LEFT JOIN product_template d ON d.id=c.product_tmpl_id \
		LEFT JOIN stock_location e ON e.id=a.location_id \
		LEFT JOIN stock_location f ON f.id=a.location_dest_id \
		LEFT JOIN product_uom g ON g.id=a.product_uom \
		LEFT JOIN product_uom h ON h.id=a.product_uop \
		LEFT JOIN stock_tracking i ON i.id=a.tracking_id \
		LEFT JOIN product_reason_code j on j.id=a.reason_code \
		LEFT JOIN account_analytic_account k on k.id=a.analytic_account_id \
		LEFT JOIN (	SELECT \
						move_present.loc_id, \
						move_present.product_id, \
						move_present.tracking_id, \
						sum(move_present.qty) as qty_kg_pres, \
						sum(move_present.qty/181.44) as qty_bale_pres, \
						sum(move_present.product_uop_qty) as product_uop_qty_pres \
					FROM \
						(SELECT \
							location_dest_id as loc_id, \
							product_id, \
							product_uop, \
							sum(qty_kg) as qty, \
							sum(product_uop_qty) as product_uop_qty, \
							tracking_id \
						FROM \
							(SELECT \
								sm.location_dest_id, \
								sm.product_id, \
								sm.product_uop, \
								round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg, \
								sm.product_uop_qty, \
								coalesce(sm.tracking_id,0) as tracking_id \
							FROM \
								stock_move sm \
								LEFT JOIN product_product pp ON sm.product_id = pp.id \
								LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id \
								LEFT JOIN product_uom pu_sm ON sm.product_uom = pu_sm.id \
								LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id \
								LEFT JOIN stock_location e on e.id = sm.location_dest_id \
							WHERE \
								e.usage='internal' \
								AND sm.state in ('done') \
								AND sm.date <= current_timestamp \
							ORDER BY sm.location_dest_id,sm.product_id,sm.tracking_id,sm.product_uop \
							) incoming \
						GROUP BY location_dest_id, product_id,product_uop,tracking_id \
						UNION ALL \
						SELECT \
							location_id as loc_id, \
							product_id, \
							product_uop, \
							-1*sum(qty_kg) as qty, \
							-1*sum(product_uop_qty) as product_uop_qty, \
							tracking_id \
						FROM \
							(SELECT \
								sm.location_id, \
								sm.product_id, \
								sm.product_uop, \
								round(round(sm.product_qty/pu_sm.factor,4)*pu_pt.factor,4) as qty_kg, \
								sm.product_uop_qty, \
								coalesce(sm.tracking_id,0) as tracking_id \
							FROM \
								stock_move sm \
								LEFT JOIN product_product pp ON sm.product_id = pp.id \
								LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id \
								LEFT JOIN product_uom pu_sm on sm.product_uom = pu_sm.id \
								LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id \
								LEFT JOIN stock_location e on e.id = sm.location_id \
							WHERE \
								e.usage='internal' \
								AND sm.state in ('done') \
								AND sm.date <= current_timestamp \
							ORDER BY sm.location_id,sm.product_id,sm.tracking_id,sm.product_uop \
							) outgoing \
						GROUP BY location_id, product_id,product_uop,tracking_id \
						) move_present \
		            GROUP BY move_present.loc_id, move_present.product_id,move_present.tracking_id) move_pres \
		ON move_pres.loc_id=a.location_id AND move_pres.product_id=a.product_id AND move_pres.tracking_id=coalesce(a.tracking_id,0) \
		WHERE a.picking_id='%s' \
		ORDER BY c.id \
		"%(obj.id)
		self.cr.execute(query)
		move_lines_grouped = {}
 		for move in self.cr.dictfetchall():
 			key = (move['dest_loc_id'],move['site_loc_name'])
 			sequence=(move['sequence'])
 			if key not in move_lines_grouped:
 				move_lines_grouped.update({key:[]})
 			print move['uom_id']
 			if move['internal_type'] == 'Finish':
 				move.update({'qty_bale':self._get_qty_bale(move['uom_id'],move['qty1'])})
 			move_lines_grouped[key].append(move)
 		# res = sorted(move_lines_grouped[key], key=lambda k: sequence)
 		return move_lines_grouped
 		# return res

report_sxw.report_sxw('report.inventory.issue.form', 'stock.picking', 'reporting_module/inventory_issue/inventory_issue_form.mako', parser=inventory_issue,header=False)