import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict
import datetime



class sale_order_priorities_parser(report_sxw.rml_parse):	
	def __init__(self, cr, uid, name, context):
		super(sale_order_priorities_parser, self).__init__(cr, uid, name, context=context)        
		#======================================================================= 
		self.line_no = 0
		self.localcontext.update({
			'time': time,
			# 'get_result': self._get_result,
			'get_date': self._get_date,
			'uom_to_base' : self._uom_to_base,
			'get_pending_qty_data':self._get_pending_qty_data,
		}) 

	def _get_date(self,sol_id):
		print sol_id,"mamamamamamamamamamaa"
		cr=self.cr
		uid=self.uid
		stock_move_obj=self.pool.get('stock.move')
		for lines in stock_move_obj.search(cr,uid,[('sale_line_id','=',sol_id)]):
			if not lines:
				continue
			return lines.picking_id.estimation_deliv_date,lines.estimation_arriv_date
		# search(cr, uid, [('booking_id','in',container_booking_ids),('product_id','=',product_id),('product_uop','=',product_uop)])

	
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


	def _get_pending_qty_data(self,sale_line_id, as_on_date,sale_type):
		cr=self.cr
		uid=self.uid
		# print as_on_date,"nananananannaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
		as_on_date_str=datetime.datetime.strptime(as_on_date,'%Y-%m-%d')
		# print as_on_date_str,"blalaablablaaaaablablablablablab"
		sale_line_id=tuple(sale_line_id)
		# sale_order_id=self.pool.get('sale.order.line').browse(cr, uid, sale_line_id).order_id.id
		# # order_id=sale_order_line_obj.order_id
		# print sale_order_id,"zazazazazazazazazazazazazaza"
		# sale_order_obj=self.pool.get('sale.order').browse(cr, uid, sale_order_id)
		# sale_type=sale_order_obj.sale_type
		# print sale_type,"tytytytytytytytytytytytytytytyt"
		# priority_id=self.pool.get('sale.order.line').browse(cr, uid, sale_line_id).priority_id.id
		# print priority_id,"mbabababababababababababa"
		# sale_priority_obj=self.pool.get('sale.order.priority').browse(cr, uid, priority_id)
		# as_on_date=sale_priority_obj.as_on_date
		# print as_on_date,"kakakakakakakakakakaakakak"
		
		s=	"select sol.id as sale_order_line_id,\
					(sol.product_uom_qty-coalesce(dump_lc.total_shipped_lc_as_on,dum_smm.shipped_qty,0.0)) as bal_qty, \
					sol.product_uom,so.sale_type \
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
				sol.id in %s \
				"
		query=s%(as_on_date_str,sale_type,as_on_date_str,sale_type,as_on_date_str,sale_type,sale_line_id)
		self.cr.execute(query)
		result = self.cr.fetchall()
		# print result,"dudududududududududududududududud"
		resx =[]
		for x in result:
			# print x[1],"papaaaaapapapapapapapapapapapapapapapapapa"
			base_bal_qty = self._uom_to_base(cr,uid,x[3],x[1],x[2])
			res=x[0],base_bal_qty
			# print res,"jajajajajajajajajajajajajajajajajajajajajaj"
			resx.append(res)
		# print resx,"brororororororororororor"
		return dict(resx)

report_sxw.report_sxw('report.sale.order.priority.print.form', 'sale.order.priority', 'reporting_module/sale_order_priorities/sale_order_priority_report.mako', parser=sale_order_priorities_parser,header=False)