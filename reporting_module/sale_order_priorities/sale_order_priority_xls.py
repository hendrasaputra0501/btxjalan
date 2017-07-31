import re
import time
import xlwt
from report import report_sxw
from report_xls.report_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _
from datetime import datetime
import netsvc
import datetime


class sale_order_priority_parser_xls (report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(sale_order_priority_parser_xls, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_pending_qty_data' : self._get_pending_qty_data,
			'uom_to_base' : self._uom_to_base,
			'xdate'	: self._xdate,
		})

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

	def _xdate(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''
		try:
			y = datetime.datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
		except:
			y = ''
		return y


	def _get_pending_qty_data(self,sale_line_id, as_on_date,sale_type):
		cr=self.cr
		uid=self.uid
		# print as_on_date,"nananananannaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
		as_on_date_str=datetime.datetime.strptime(as_on_date,'%Y-%m-%d')
		# print as_on_date_str,"blalaablablaaaaablablablablablab"
		sale_line_id=tuple(sale_line_id)
		
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
			# base_bal_qty = self._uom_to_base(cr,uid,line['sale_type'],line['bal_qty'] or 0.0,line['product_uom'] or '')
			base_bal_qty = self._uom_to_base(cr,uid,x[3],x[1],x[2])
			res=x[0],base_bal_qty
			# print res,"jajajajajajajajajajajajajajajajajajajajajaj"
			resx.append(res)
		# print resx,"brororororororororororor"
		return dict(resx)
	


class sale_order_priority_xls(report_xls):
	
	# no_ind = 0
	# def get_no_index(self):
	# 	self.set_no_index()
	# 	return self.no_ind
	# def set_no_index(self):
	# 	self.no_ind += 1
	# 	return True

	# def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
	# 	if not context:
	# 		context = {}
	# 	context = context.copy()
	# 	rml_parser = self.parser(cr, uid, self.name2, context=context)
	# 	objs = []
	# 	rml_parser.set_context(objs, data, ids, 'xls')
	# 	n = cStringIO.StringIO()
	# 	wb = xlwt.Workbook(encoding='utf-8')
	# 	self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
	# 	wb.save(n)
	# 	n.seek(0)
	# 	return (n.read(), 'xls')
		
	def generate_xls_report(self, parser, xls_style,data, objects, wb):
	# def generate_xls_report(self, parser, xls_style, data, objects, wb):
	# def generate_xls_report(self, parser, xls_style, data, objects, wb):
		print objects,"haaahaahahahahahahahahahahahahahahahahahahahahahahahaaaaaaaaaahahahahahahahahahahahahahahahahahaaaaaaaaaaaaah"
		
		ws = wb.add_sheet("Header")
		ws.panes_frozen = False
		ws.remove_splits = True
		ws.portrait = 0  # Landscape
		# ws.fit_width_to_pages = 1
		# ws.preview_magn = 90
		# ws.normal_magn = 90
		# ws.print_scaling = 100
		# ws.page_preview = True
		# ws.set_fit_width_to_pages(1)
		row_pos = 0
		

		# set print header/footer
		ws.header_str = self.xls_headers['standard']
		ws.footer_str = self.xls_footers['standard']

		title_style                     = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
		th_top_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top thin')
		th_both_style                   = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top dashed, bottom dashed;')
		th_bottom_style                 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom thin')
		
		normal_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float              = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_style_float_round        = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
		normal_style_float_bold         = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
		normal_bold_style               = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
		normal_bold_style_b             = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
		
		subtotal_title_style            = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; borders: bottom thin;')
		subtotal_style                  = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre; borders: top thin;',num_format_str='#,##0;-#,##0')
		subtotal_style2                 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: top thin;',num_format_str='#,##0.00;-#,##0.00')
		total_title_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
		total_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
		total_style2                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
		subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap off, vert centre, horiz left; pattern: pattern solid, fore_color white;')
		# print "dadadadadadadddddddddddddddddddddddddd"
		# for o in objects:
		# 	print o.as_on_date,"zazazazazazazazazazazazazazazazaaaazazazazazzazzzazazzaz"
		ws.write_merge(1,1,0,18,"PT. BITRATEX INDUSTRIES",title_style)
		ws.write_merge(2,2,0,18,"Sale Order Priority Report",title_style)

		ws.write(4,0, "Product", th_top_style)
		ws.write(4,1, "SC. NO", th_top_style)
		ws.write(4,2, "SC", th_top_style)
		ws.write(4,3, "Customer", th_top_style)
		ws.write(4,4, "Bales", th_top_style)
		ws.write(4,5, "P/C", th_top_style)
		ws.write(4,6, "Cn Wt", th_top_style)
		ws.write(4,7, "LSD", th_top_style)
		ws.write(4,8, "LSD", th_top_style)
		ws.write(4,9, "LSD", th_top_style)
		ws.write(4,10, "TT/LC", th_top_style)
		ws.write(4,11, "Priority",th_top_style) 
		ws.write(4,12, "Ready By", th_top_style)
		ws.write(4,13, "Good", th_top_style)
		ws.write(4,14, "Shipped", th_top_style)
		ws.write(4,15, "Shipped", th_top_style)
		ws.write(4,16, "Bitra", th_top_style)
		ws.write(4,17, "Internal", th_top_style)
		ws.write(4,18, "Country", th_top_style)
		ws.write(5,0, "", th_bottom_style)
		ws.write(5,1, "", th_bottom_style)
		ws.write(5,2, "Date", th_bottom_style)
		ws.write(5,3, "", th_bottom_style)
		ws.write(5,4, "", th_bottom_style)
		ws.write(5,5, "", th_bottom_style)
		ws.write(5,6, "", th_bottom_style)
		ws.write(5,7, "(SC)", th_bottom_style)
		ws.write(5,8, "(LC)", th_bottom_style)
		ws.write(5,9, "5 Day", th_bottom_style)
		ws.write(5,10, "", th_bottom_style)
		ws.write(5,11, "", th_bottom_style)
		ws.write(5,12, "", th_bottom_style)
		ws.write(5,13, "Actual Date", th_bottom_style)
		ws.write(5,14, "ETD", th_bottom_style)
		ws.write(5,15, "ETA", th_bottom_style)
		ws.write(5,16, "Remark", th_bottom_style)
		ws.write(5,17, "Remark", th_bottom_style)
		ws.write(5,18, "", th_bottom_style)

		max_width_col_0=len("Product")
		max_width_col_1=len("SC. NO")
		max_width_col_2=len("SC")
		max_width_col_3=len("Customer")
		max_width_col_4=len("Bales")
		max_width_col_5=len("P/C")
		max_width_col_6=len("Cn Wt")
		max_width_col_7=len("LSD")
		max_width_col_8=len("LSD")
		max_width_col_9=len("LSD")
		max_width_col_10=len("TT/LC")
		max_width_col_11=len("Priority")
		max_width_col_12=len("Ready By")
		max_width_col_13=len("Good")
		max_width_col_14=len("Shipped")
		max_width_col_15=len("Shipped")
		max_width_col_16=len("Bitra")
		max_width_col_17=len("Internal")
		max_width_col_18=len("Country")
		

		baris=6
		for o in objects:
			ws.write_merge(3,3,0,18,"As On Date "+o.as_on_date,title_style)
			sale_line_ids=[]
			for x in o.priority_lines_ids+o.sale_line_ids:
				sale_line_ids.append(x.id)
			data_pending =parser.get_pending_qty_data(sale_line_ids,o.as_on_date,o.sale_type)
			result_grouped={}
			for lines in o.priority_lines_ids+o.sale_line_ids:
				key_unit=lines.production_location.name or ''
				if key_unit not in result_grouped:
					result_grouped.update({key_unit:{}})
				key2_product=lines.product_id.id or ''
				if key2_product not in result_grouped[key_unit]:
					result_grouped[key_unit].update({key2_product:[]})
				result_grouped[key_unit][key2_product].append(lines)
			for unit in sorted(result_grouped.keys(),key=lambda l:l):
				ws.write(baris,0,unit,normal_bold_style)
				baris+=1
				for key_product in sorted(result_grouped[unit].keys(),key=lambda k:k):
					xy=sorted(result_grouped[unit][key_product],key=lambda j:j.product_id.id)
					for line in xy:
						lsd_str=line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date
						lsd=datetime.datetime.strptime(lsd_str,'%Y-%m-%d')
						date_5=datetime.timedelta(days=5)
						date5=lsd-date_5
	                    
						lsd_5=datetime.datetime.strftime(date5,'%d/%m/%Y')
						shipped_date=parser.xdate(line.move_ids[0].picking_id.estimation_arriv_date) or ''

						ws.write(baris,0,line.product_id and line.product_id.name or '',normal_style)
						if len(line.product_id and line.product_id.name or '')>max_width_col_0:
							ws.col(0).width=len(line.product_id and line.product_id.name or '')
						ws.write(baris,1,line.sequence_line or '',normal_style)
						if len(line.sequence_line)>max_width_col_1:
							max_width_col_1=len(line.sequence_line or '')
						ws.write(baris,2,line.order_id and line.order_id.date_order or '',normal_style)
						if len(line.order_id and line.order_id.date_order or '')>max_width_col_2:
							max_width_col_2=len(line.order_id and line.order_id.date_order or '')
						ws.write(baris,3,line.order_id and line.order_id.partner_id and line.order_id.partner_id.name or '',normal_style)
						if len(line.order_id and line.order_id.partner_id and line.order_id.partner_id.name or '')>max_width_col_3:
							max_width_col_3=len(line.order_id and line.order_id.partner_id and line.order_id.partner_id.name or '')
						ws.write(baris,4,data_pending[line.id],normal_style)
						# if len(data_pending[line.id])>max_width_col_4:
						# 	max_width_col_4=len(data_pending[line.id])
						ws.write(baris,5,line.packing_type.alias or '',normal_style)
						if len(line.packing_type.alias or '')>max_width_col_5:
							max_width_col_5=len(line.packing_type.alias or '')
						ws.write(baris,6,line.cone_weight or '',normal_style)
						# if len(line.cone_weight or '')>max_width_col_6:
						# 	max_width_col_6=len(line.cone_weight or '')
						ws.write(baris,7,parser.xdate(line.reschedule_date and line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''),normal_style)
						if len(parser.xdate(line.reschedule_date and line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''))> max_width_col_7:
							max_width_col_7=len(parser.xdate(line.reschedule_date and line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''))
						ws.write(baris,8,parser.xdate(line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''),normal_style)
						if len(parser.xdate(line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''))>max_width_col_8:
							max_width_col_8=len(parser.xdate(line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''))
						ws.write(baris,9,lsd_5,normal_style)
						if len(lsd_5)>max_width_col_9:
							max_width_col_9=len(lsd_5)
						ws.write(baris,10,line.order_id and line.order_id.payment_method or '',normal_style)
						# if len(line.order_id and line.order_id.payment_method or '')>max_width_col_10:
						# 	max_width_col_10=len(line.order_id and line.order_id.payment_method or '')
						ws.write(baris,11,line.priority or '',normal_style)
						ws.write(baris,12,line.ready_by or '',normal_style)
						ws.write(baris,13,parser.xdate(line.goods_actual_date or ''),normal_style)
						if len(parser.xdate(line.goods_actual_date or ''))>max_width_col_13:
							max_width_col_13=len(parser.xdate(line.goods_actual_date or ''))
						ws.write(baris,14,parser.xdate(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_deliv_date or ''),normal_style)
						if len(parser.xdate(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_deliv_date or ''))>max_width_col_14:
							max_width_col_14=len(parser.xdate(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_deliv_date or ''))
						ws.write(baris,15, shipped_date,normal_style)
						if len(shipped_date)>max_width_col_15:
							max_width_col_15=len(shipped_date)
						ws.write(baris,16,line.remark_priorities or '',normal_style)
						if len(line.remark_priorities or '')>max_width_col_16:
							max_width_col_16=len(line.remark_priorities or '')
						ws.write(baris,17,line.other_description or '',normal_style)
						if len(line.other_description or '')>max_width_col_17:
							max_width_col_17=len(line.other_description or '')
						ws.write(baris,18,line.order_id and line.order_id.dest_country_id and line.order_id.dest_country_id.name or '',normal_style)
						if len(line.order_id and line.order_id.dest_country_id and line.order_id.dest_country_id.name or '')>max_width_col_18:
							max_width_col_18=len(line.order_id and line.order_id.dest_country_id and line.order_id.dest_country_id.name or '')
						baris+=1
				# print lines.product_id and lines.product_id.name,"vavavavavvavaavavavaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
				# ws.write(baris,0, lines.product_id and lines.product_id.name , normal_style)
		
				ws.col(0).width = 256 * int(max_width_col_0*4)
				ws.col(1).width = 256 * int(max_width_col_1*1.2)
				ws.col(2).width = 256 * int(max_width_col_2*1.3)
				ws.col(3).width = 256 * int(max_width_col_3*1.2)
				ws.col(4).width = 256 * int(max_width_col_4*2)
				ws.col(5).width = 256 * int(max_width_col_5*2)
				ws.col(6).width = 256 * int(max_width_col_6*2)
				ws.col(7).width = 256 * int(max_width_col_7*1.3)
				ws.col(8).width = 256 * int(max_width_col_8*1.3)
				ws.col(9).width = 256 * int(max_width_col_9*1.3)
				ws.col(10).width = 256 * int(max_width_col_10*1.5)
				ws.col(11).width = 256 * int(max_width_col_11*2)
				ws.col(12).width = 256 * int(max_width_col_12*2)
				ws.col(13).width = 256 * int(max_width_col_13*1.3)
				ws.col(14).width = 256 * int(max_width_col_14*1.3)
				ws.col(15).width = 256 * int(max_width_col_15*1.3)
				ws.col(16).width = 256 * int(max_width_col_16*2)
				ws.col(17).width = 256 * int(max_width_col_17*0.8)
				ws.col(18).width = 256 * int(max_width_col_18*1)

sale_order_priority_xls('report.sale.order.priority.print.xls', 'sale.order.priority', parser=sale_order_priority_parser_xls,header=False)
# beacukai_doc_report_xls('report.beacukai.ceisa.tmpl.test','beacukai', parser=export_ceisa_template_parser, header=False)

