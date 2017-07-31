from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _
from datetime import datetime
import time

class report_stock_wip_pabean(osv.osv):
	_name = "report.stock.wip.pabean"
	_description = "WIP Statistics"
	_auto = False

	_columns = {
		"product_id":fields.many2one("product.product","Product"),

		"name":fields.char("Name",size=128),
		"product_uom":fields.many2one("product.uom","Unit of Measure"),
		"company_id":fields.many2one("res.company","Company"),
		"picking_id":fields.many2one("stock.picking","Picking ID"),
		"product_qty":fields.float("Quantity"),
		'date': fields.date('Order Date', readonly=True),
		'year': fields.char('Year', size=4, readonly=True),
		'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
			('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
			('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
		"location_id":fields.many2one("stock.location","Source Location"),
		"location_dest_id":fields.many2one("stock.location","Production Location"),
		"move_id":fields.many2one("stock.move","Move ID"),
		'categ_id': fields.many2one('product.category', 'Product Category', ),
		"state":fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
	}

	def init(self, cr):
		tools.drop_view_if_exists(cr, 'report_stock_wip_pabean')
		cr.execute("""
			CREATE OR REPLACE view report_stock_wip_pabean AS (
				SELECT 
					sm.id as id,
					sm.id as move_id,
					to_char(date_trunc('day',sm.date), 'YYYY') as year,
					to_char(date_trunc('day',sm.date), 'MM') as month,
					to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as date,
					pt.name as name,
					sm.product_id as product_id,
					sm.company_id as company_id,
					sm.picking_id as picking_id,
					pt.uom_id as product_uom,
					sm.location_id as location_id,
					sm.location_dest_id as location_dest_id,
					sm.state as state,
					(sm.product_qty * pu.factor / pu2.factor) as product_qty,
					pt.categ_id as categ_id
				FROM
					stock_move sm
					left join stock_location sl on sm.location_dest_id=sl.id 
					left join product_product pp on sm.product_id = pp.id
					left join product_template pt on pp.product_tmpl_id = pt.id
					LEFT JOIN product_uom pu ON (sm.product_uom=pu.id)
					LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)
				WHERE 
					sm.location_dest_id in (select id from stock_location where usage='production')
				GROUP BY
					sm.id,sm.date,
					sm.product_id,sm.state,sm.product_uom,
					sm.picking_id, sm.product_qty,sm.id,
					sm.company_id,pt.uom_id,pt.categ_id, sm.location_id,sm.location_dest_id,pt.name,pu.factor,pu2.factor
				ORDER BY
					sm.date DESC,
					sm.product_id ASC
					   )
		""")

report_stock_wip_pabean()


class report_stock_location_product(osv.osv_memory):
	_name = "report.stock.location.product"
	_description = "Report Products by Location"
	_columns = {
		'from_date': fields.date('From'), 
		'to_date': fields.date('To'),
		'type': fields.selection([('inventory','Analyse Current Inventory'),
			('period','Analyse a Period')], 'Analyse Type', required=True), 
   		'report_type':fields.selection([('1','Laporan Posisi WIP'),('2','Pertanggungjawaban Mutasi')],"Report Type",required=True),
   		# 'categ_ids':fields.many2many('product.category','report_stock_product_category_rel','report_id','categ_id',"Product Category"),
   		'location': fields.many2one('stock.location','Location',domain="[('usage','=','production')]"),
   		'internal_type':fields.selection([('Finish',"Barang Jadi"),
			('Finish_others',"Sampah Barang Lain-lain"),
			('Raw Material',"Bahan Baku"),
			('Stores',"Stores"),
			('Waste',"Sampah Produksi"),
			('asset',"Scrap"),
			('Fixed','Fixed Assets'),
			('Packing','Bahan Penolong')],"Internal Type"),
	}

	_defaults = {
		'from_date' : lambda *f : time.strftime('%Y-%m-01'),
		'to_date' : lambda *t : time.strftime('%Y-%m-%d'),
		'report_type' : lambda self, cr, uid, context: context.get('report_type',False),
		'internal_type' : lambda self, cr, uid, context: context.get('internal_type',False),
	}

	def onchange_report_type(self,cr,uid,ids,report_type,context=None):
		if not context:context={}
		if report_type and report_type=='1':
			return {'domain':{'location':"[('usage','=','production')]"}}
		elif report_type and report_type=='2':
			return {'domain':{'location':"[('usage','!=','view')]"}}
		
		return {}

	def action_open_window(self, cr, uid, ids, context=None):
		""" To open location wise product information specific to given duration
		 @param self: The object pointer.
		 @param cr: A database cursor
		 @param uid: ID of the user currently logged in
		 @param ids: An ID or list of IDs (but only the first ID will be processed)
		 @param context: A standard dictionary 
		 @return: Invoice type
		"""
		if context is None:
			context = {}
		wizard = self.read(cr, uid, ids, ['from_date', 'to_date','location','report_type','internal_type','type'], context=context)
		if wizard:
			locs = wizard[0]['location'] and wizard[0]['location'][0] or False
			data_obj = self.pool.get('ir.model.data')
			#domain = [('categ_id','in',location_products[0]['categ_ids']),('type', '<>', 'service')]
			if wizard[0]['report_type'][0]=='1':
				res_model = 'product.rm.type.category'
				result = data_obj._get_id(cr, uid, 'ad_beacukai_report', 'view_product_rm_type_category_tree_pabean')
				domain = []
			else:
				res_model = 'product.product'
				result = data_obj._get_id(cr, uid, 'ad_beacukai_report', 'view_product_tree2_pabean')
				domain = [('internal_type','=',wizard[0]['internal_type']),('type','<>','service'),('bc_remarks','=','bc')]
			view_id = data_obj.browse(cr, uid, result).res_id
			
			if wizard[0]['type']=='period':
				from_date = wizard[0]['from_date']!=False and datetime.strptime(wizard[0]['from_date'],'%Y-%m-%d').strftime('%Y-%m-%d 00:00:00') or False
				to_date = wizard[0]['to_date'] and datetime.strptime(wizard[0]['to_date'],'%Y-%m-%d').strftime('%Y-%m-%d 23:59:59') or False
			else:
				from_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
				to_date = datetime.now().strftime('%Y-%m-%d 23:59:59')
			
			return {
				'name': _('Current Inventory'),
				'view_type': 'form',
				'view_mode': 'tree',
				'res_model': res_model,
				'view_id':[view_id],
				'type': 'ir.actions.act_window',
				
				'context': {'location': locs,
							'from_date': from_date or False,
							'to_date': to_date or False,},
				"domain":domain,
			}

report_stock_location_product()
