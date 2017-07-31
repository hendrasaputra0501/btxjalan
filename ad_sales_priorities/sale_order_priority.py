from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import datetime

import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
from report import report_sxw
from ad_sales_report.report.pending_sales_report_parser import pending_sales_parser

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class sale_order_priority(osv.Model):
	_name="sale.order.priority"
	_columns={
		'as_on_date'	: fields.date('As on Date',required=True,readonly=True, states={'draft':[('readonly',False)],'cancelled':[('readonly',False)]}),
		'priority_lines_ids' : fields.one2many('sale.order.line','priority_id','Priority Lines'),
		'sale_type'	:	fields.selection([('export','Export'),('local','Local')],'Shipment Type',required=True, readonly=True, states={'draft':[('readonly',False)],'cancelled':[('readonly',False)]}),
		'state'	:	fields.selection([('draft','Draft'),('validated','Validated'),('cancelled','Cancelled')], "State"),
		'sale_line_ids' : fields.many2many("sale.order.line","sol_rel_so_priority","so_priority_id","so_line_id","Sale Order Line"),
	}
	_defaults = {
		'state' : 'draft',
		# 'name' : '/'
	}

	def action_validate(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'validated'})

	def action_cancelled(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'cancelled'})

	def action_generate(self, cr, uid, ids, context=None):

		if not context:context={}

		for priority in self.browse(cr, uid, ids, context=context):
			as_on_date=priority.as_on_date
			sale_type=priority.sale_type
			s=	"select sol.id, \
					so.sale_type, \
					sol.product_uom, \
					(sol.product_uom_qty-coalesce(dump_lc.total_shipped_lc_as_on,dum_smm.shipped_qty,0.0)) as bal_qty, \
					coalesce(dump_lc.shipped_lc_qty,dum_smm.shipped_qty,0.0) as shipped_qty \
					from sale_order_line sol \
					inner join sale_order so on sol.order_id=so.id \
					left join ( \
		                        select dum1.*,dum2.total_shipped_lc_as_on,rank() OVER (PARTITION BY dum1.sol_id ORDER BY dum1.lc_prod_line_id DESC) \
		                        from lc_shipment_sol('%s'::timestamp,'finish','%s') dum1 \
		                        left join \
                            		( \
			                            select xr.sol_id,min(xr.lc_lsd) as min_dt,sum(xr.shipped_lc_qty) as total_shipped_lc_as_on \
			                            from lc_shipment_sol('%s'::timestamp,'finish','%s') xr group by xr.sol_id,xr.prod_id \
			                            ) dum2 \
		                            on \
		                            dum2.sol_id=dum1.sol_id \
		                            and dum1.lc_lsd=dum2.min_dt \
                    		) dump_lc on dump_lc.sol_id=sol.id and dump_lc.rank=1 \
					left join ( \
                    select \
                        smm.sale_line_id,smm.product_id, \
                        case when spm.type='out' then \
                            sum(round((coalesce(smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
                        else \
                            sum(round((coalesce(-1*smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
                        end as shipped_qty \
                    from stock_move smm \
                        left join sale_order_line solm on smm.sale_line_id=solm.id \
                        inner join stock_picking spm on smm.picking_id=spm.id \
                        inner join stock_location slm1 on smm.location_id=slm1.id \
                        inner join stock_location slm2 on smm.location_dest_id=slm2.id \
                        inner join product_uom pum1 on solm.product_uom=pum1.id \
                        inner join product_uom pum2 on smm.product_uom=pum2.id \
                    where \
                        smm.date::date<='%s'::date and smm.state='done' \
                        and ((slm1.usage='internal' and slm2.usage='customer') or (slm1.usage='customer' and slm2.usage='internal')) \
                        and spm.goods_type='finish' and spm.sale_type='%s' \
                    group by smm.sale_line_id,smm.product_id,spm.type \
                    ) dum_smm on sol.id=dum_smm.sale_line_id and sol.product_id=dum_smm.product_id \
				where \
				so.state not in ('draft','cancel') and so.date_order::date <='%s' \
                and to_char(so.date_order,'YYYY-MM-DD') <= substring('%s',1,10) \
                and ((so.date_done is null) or (to_char(so.date_done,'YYYY-MM-DD') > substring('%s',1,10))) \
                and ((so.date_cancel is null) or (to_char(so.date_cancel,'YYYY-MM-DD') > substring('%s',1,10))) \
                and ((sol.date_knock_off is null or sol.knock_off=false) or (to_char(sol.date_knock_off,'YYYY-MM-DD') > substring('%s',1,10))) \
                and so.goods_type ='finish' \
                and so.sale_type='%s' \
				"
			 
			
                
			query=s%(
						 as_on_date,
                            # data['form']['goods_type'],
                            sale_type,
                            as_on_date,
                            # data['form']['goods_type'],
                            sale_type,
                            as_on_date,
                            # data['form']['goods_type'],
                            sale_type,
					as_on_date,as_on_date,as_on_date,as_on_date,as_on_date,sale_type)
			cr.execute(query)
			result = cr.dictfetchall()
			sale_order_line_obj=self.pool.get('sale.order.line')
			# res=[]
			# for dict_line in result:
			# 	# print dict_line,"nanananananananaananananananana"
			# 	line_ids=[]
			# 	for k,v in dict_line.items():
			# 		# print v,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
			# 		if not line_ids:
			# 			line_ids.append(v)
			# 			for sol in sale_order_line_obj.browse(cr,uid,line_ids):
			# 		# for sol in sale_order_line_obj:
			# 				print sol.sequence_line,"dadadadadadadadadadadadd"
			# 				res.append({
			# 					id:sol.sequence_line
			# 					})
			min_bale_bal_qty=5.0
			sale_line_ids=[]
			for line in result :
				base_bal_qty = self._uom_to_base(cr,uid,line['sale_type'],line['bal_qty'] or 0.0,line['product_uom'] or '')
				bale_shipped_qty = self._uom_to_base(cr,uid,line['sale_type'],line['shipped_qty'] or 0.0,line['product_uom'] or '')
				if base_bal_qty <= min_bale_bal_qty and bale_shipped_qty>0.0:
					continue
				# sale_line_ids=sale_order_line_obj.search(cr,uid,[('id','=',line['id'])])
					# sale_line_ids=line['id']
				# print sale_line_ids,"zzzzzzzzzzzzzzzzzzzzzzzzzzz"
				# print line['id'],"vzvavavavvavavavavavavavava"
				# sale_order_line_obj.write(cr, uid, line['id'], {
				# 	'qty_bal_priority':base_bal_qty
				# 	})
				# print base_bal_qty,"xxxyxyxyxyxyxyxyxyxyxyxyyx"
				if line['id'] not in sale_line_ids:
					sale_line_ids.append(line['id'])
			for sol in sale_order_line_obj.browse(cr,uid,sale_line_ids):
				if sol.priority_id:
					sale_order_line_obj.write(cr, uid, sol.id, {
						'prev_priorities_ids' :[(4, sol.priority_id.id)], 
						})
				sale_order_line_obj.write(cr, uid, sol.id, {
					'priority_id' :priority.id
					})


			return True
					
				
			# sale_line_ids = [x.values()[0] for x in result]
			# print sale_line_ids,"ssssssssssssssssssssssssssss"
			# for sol in sale_order_line_obj.browse(cr,uid,sale_line_ids):
			# 	if sol.priority_id:
			# 		sale_order_line_obj.write(cr, uid, sol.id, {
			# 			'prev_priorities_ids' :[(4, sol.priority_id.id)], 
			# 			})
			# 	sale_order_line_obj.write(cr, uid, sol.id, {
			# 		'priority_id' :priority.id
			# 		})


			# return True

	def _uom_to_base(self,cr,uid, sale_type,qty,uom_source):
		# cr = self.cr
		# uid = self.uid
		if sale_type == 'export':
		  uom_base = 'BALES'
		elif sale_type == 'local':
		  uom_base = 'BALES'
		else:
		  uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result


	def unlink(self, cr, uid, ids, context=None):
		
		for priority_rec in self.browse(cr, uid, ids, context=context):
			print "------------------------",type(priority_rec),getattr(priority_rec, 'priority_lines_ids')
			if priority_rec.priority_lines_ids:
				raise osv.except_osv(_('Error!'), _('You cannot delete sale order priority items if they has been generate by the \
															priority.'))
		return super(sale_order_priority, self).unlink(cr, uid, ids, context=context)			






class sale_order_line(osv.Model):
	_inherit="sale.order.line"
	_columns={
		# 'sale_line_id' : fields.many2one('sale.order.line',string='Delivery Order'), states={'draft':[('readonly',False)]}
		'goods_actual_date'	:	fields.date("Goods Actual Date", ),
		'priority'	:	fields.char("Priority", ),
		'remark_priorities'	:	fields.text("Remark Priorities", ),
		'priority_id'	: fields.many2one('sale.order.priority',string='Sale Order Priority'),
		'ready_by'	: fields.char("Ready By", ),
		'prev_priorities_ids' : fields.many2many("sale.order.priority","sol_rel_so_priority","so_line_id","so_priority_id","Sale Order Priority"),
	}
