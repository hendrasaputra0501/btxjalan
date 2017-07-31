import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from report_engine_xls import report_xls
from ad_stock_report.report.stock_valuation_parser import ReportStockValBitra

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class valuation_report_xls(report_xls):
	no_ind = 0
	def get_no_index(self):
		self.set_no_index()
		return self.no_ind
	def set_no_index(self):
		self.no_ind += 1
		return True

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
		company = parser.localcontext['company']
		i=0

		prods = parser._get_product_info()
		trackings = parser._get_tracking_info()
		uoms = parser._get_uom_info()
		if data['grouping']=='location':
			for inventory_type in parser._get_inventory_type(data): 
				# try:
				# 	stock_lines,available_parent,location_line,product_line,track_lines,uop_lines = parser._get_stock(data,inventory_type)
				# except:
				# 	stock_lines,available_parent,location_line,product_line,track_lines,uop_lines = [],[],[],[],[],[]
				ws = wb.add_sheet('Class - %s'%inventory_type.name,cell_overwrite_ok=True)
				ws.panes_frozen = True
				ws.remove_splits = True
				ws.portrait = 0 # Landscape
				ws.fit_width_to_pages = 1
				ws.preview_magn = 48
				ws.normal_magn = 48
				ws.print_scaling=48
				ws.page_preview = False
				ws.set_fit_width_to_pages(1)
				##Penempatan untuk template rows
				title_style  = xlwt.easyxf('font: height 220, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
				normal_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
				normal_style_float = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
				normal_style_float_round = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
				normal_style_float_bold = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
				normal_bold_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
				normal_bold_style_a = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
				normal_bold_style_b = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
				th_top_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
				th_both_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
				th_both_style_left = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left;')
				th_both_style_dashed = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom dashed',num_format_str='#,##0.00;-#,##0.00')
				th_both_style_dashed_bottom = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right; border:bottom dashed',num_format_str='#,##0.00;-#,##0.00')
				th_bottom_style = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
				rowcount = 0
				max_width_col = {0:8.0, 1:12.0, 2:5.0}
				if inventory_type.code=='Finish':	
					ws.write_merge(rowcount,rowcount,0,23, company.name, title_style)
					rowcount+=1
					# ws.write_merge(rowcount,rowcount,0,2, "Site ID %s"%(inventory_type.name), normal_bold_style_a)
					ws.write_merge(rowcount,rowcount,0,23, "%s Stock Valuation - %s"%(inventory_type.name,parser._get_mode(data)), title_style)
					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,23, "As on - %s"%parser._get_date_range(data), title_style)
					rowcount+=3
					ws.write_merge(rowcount,rowcount+1,0,0, "Item Code", th_both_style)
					ws.write_merge(rowcount,rowcount+1,1,1, "Description", th_both_style)
					ws.write_merge(rowcount,rowcount,2,4, "Opening Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,5,7, "Transfer", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,8,10, "Sales", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,11,13, "Sales Return", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,14,16, "Closing Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,17,18, "Op.Process", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,19,20, "Cl.Process", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,21,23, "Net Production", th_both_style_dashed)
					rowcount+=1
					ws.write(rowcount,2, "Qty", th_bottom_style)
					ws.write(rowcount,3, "Price/Kg", th_bottom_style)
					ws.write(rowcount,4, "Amount", th_bottom_style)
					ws.write(rowcount,5, "Qty", th_bottom_style)
					ws.write(rowcount,6, "Price/Kg", th_bottom_style)
					ws.write(rowcount,7, "Amount", th_bottom_style)
					ws.write(rowcount,8, "Qty", th_bottom_style)
					ws.write(rowcount,9, "Price/Kg", th_bottom_style)
					ws.write(rowcount,10, "Amount", th_bottom_style)
					ws.write(rowcount,11, "Qty", th_bottom_style)
					ws.write(rowcount,12, "Price/Kg", th_bottom_style)
					ws.write(rowcount,13, "Amount", th_bottom_style)
					ws.write(rowcount,14, "Qty", th_bottom_style)
					ws.write(rowcount,15, "Price/Kg", th_bottom_style)
					ws.write(rowcount,16, "Amount", th_bottom_style)
					ws.write(rowcount,17, "Qty", th_bottom_style)
					ws.write(rowcount,18, "Amount", th_bottom_style)
					ws.write(rowcount,19, "Qty", th_bottom_style)
					ws.write(rowcount,20, "Amount", th_bottom_style)
					ws.write(rowcount,21, "Qty", th_bottom_style)
					ws.write(rowcount,22, "Price/Kg", th_bottom_style)
					ws.write(rowcount,23, "Amount", th_bottom_style)
					rowcount += 1
					call_valuation = parser.get_valuation(inventory_type.code,data)

					try:
						stocks,available_parent_loc,available_loc,available_prod = call_valuation
					except:
						stocks = parser.get_valuation(inventory_type.code,data)
						available_parent_loc,available_loc,available_prod =[],[],[]
					
					locations = parser.get_location(data)
					product_info = parser._get_product_info()
					# current_parent = False
					# current_location = False
					# current_mbc = False
					previous_location = False
					# print "############################################",available_parent_loc,available_loc
					for parent in available_parent_loc:
						# print "locations====================",parent
						totalparent = {}
						for i in range(0,24):
							totalparent.update({i:0.0})
						if stocks.get(parent,False):

							ws.write_merge(rowcount,rowcount,0,2, parent, th_both_style_left)
							rowcount+=2
							# current_location = False
							for locs in locations:
								location = locs.id
								# print "============= ADA ATAU NGGA 2 =============",location
								# current_mbc = False
								# previous_mbc = False
								total_location = {}
								for i in range(0,24):
									total_location.update({i:0.0})
								if stocks[parent].get(location):

									ws.write_merge(rowcount,rowcount,0,2, locs.name, th_both_style_left)
									rowcount+=2
									start_row_mbc = rowcount+1
									
									for mbc in sorted(stocks[parent][location].keys()):
										# print "mbc============>",mbc
										if stocks[parent][location].get(mbc,False):
											start_row_mbc = rowcount
											current_row_mbc=rowcount
											pname_dict = {}
											pid_dict = {}
											for dummy_pname_dict in stocks[parent][location][mbc]:
												pname_dict.update({
													(dummy_pname_dict,product_info[dummy_pname_dict]['code']):dummy_pname_dict
													})
											# for dummy_pid_dict in stocks[parent][location][mbc]:
											# 	pid_dict.update({
											# 		dummy_pid_dict : product_info[pid_dict]
											# 		})
											# print "-------------dunnnyyyy--------------",pname_dict
											line_mbc_printed = 0
											for product in sorted(pname_dict.keys(), key=lambda p : p[1]):
												dummy = stocks[parent][location][mbc][pname_dict[product]]
												cols = {}
												cols.update({
													0:product_info[pname_dict[product]]['code'],
													1:product_info[pname_dict[product]]['name'],
													2:('opening' in dummy.keys()) and dummy['opening'].get("uom_qty",0.0) or 0.0,
													3:('opening' in dummy.keys()) and dummy['opening'].get("price_kg",0.0) or 0.0,
													4:('opening' in dummy.keys()) and dummy['opening'].get("amount",0.0) or 0.0,
													5:('transfer' in dummy.keys()) and dummy['transfer'].get("uom_qty",0.0) or 0.0,
													# 6:('transfer' in dummy.keys()) and dummy['transfer'].get("price_kg",0.0) or 0.0,
													# 7:('transfer' in dummy.keys()) and dummy['transfer'].get("amount",0.0) or 0.0,
													8:('outgoing' in dummy.keys()) and dummy['outgoing'].get("uom_qty",0.0) or 0.0,
													9:('outgoing' in dummy.keys()) and dummy['outgoing'].get("price_kg",0.0) or 0.0,
													10:('outgoing' in dummy.keys()) and dummy['outgoing'].get("amount",0.0) or 0.0,
													#10: cols[8]*cols[9] or 0.0,
													})
												cols.update({
													11:('out_return' in dummy.keys()) and dummy['out_return'].get("uom_qty",0.0) or 0.0,
													12:('out_return' in dummy.keys()) and dummy['out_return'].get("fob_rate",0.0) or 0.0,
												})
												cols.update({
													13:cols[11]*cols[12] or 0.0,
													14:('closing' in dummy.keys()) and dummy['closing'].get("uom_qty",0.0) or 0.0,
													15:('closing' in dummy.keys()) and dummy['closing'].get("price_kg",0.0) or 0.0,
													16:('closing' in dummy.keys()) and dummy['closing'].get("amount",0.0) or 0.0,
													17:('opening' in dummy.keys()) and dummy['opening'].get("qty_process",0.0) or 0.0,
													18:('opening' in dummy.keys()) and dummy['opening'].get("qty_process_amt",0.0) or 0.0,
													19:('closing' in dummy.keys()) and dummy['closing'].get("qty_process",0.0) or 0.0,
													20:('closing' in dummy.keys()) and dummy['closing'].get("qty_process_amt",0.0) or 0.0,
													})
												cols.update({
													6: cols[5] and ((cols[16]+cols[10]-cols[13]-cols[4])/cols[5]) or 0.0, #transfer price
													7: (cols[16]+cols[10]-cols[13]-cols[4]) or 0.0, #transfer qty
													21:(cols.get(5,0.0)+cols.get(19,0.0)-cols.get(17,0.0)),
													})
												
												cols.update({
													23:cols.get(7,0.0)+cols.get(20,0.0)-cols.get(18,0.0)
													})
												cols.update({
													22:cols.get(21,0.0)!=0.0 and (cols.get(23,0.0)/cols.get(21,0.0)) or 0.0
													})
												
												if cols[2]<1 and cols[5]<1 and cols[8]<1 and cols[11]<1 and cols[14]<1 and cols[17]<1 and cols[19]<1 and cols[21]<1:
													continue

												line_mbc_printed+=1
												if len(product_info[pname_dict[product]]['code'])>max_width_col[0]:
													max_width_col[0]=len(product_info[pname_dict[product]]['code'])
												if len(product_info[pname_dict[product]]['name'])>max_width_col[1]:
													max_width_col[1]=len(product_info[pname_dict[product]]['name'])
												# if len(product_info[pname_dict[product]]['code'])>max_width_col[0]:
												# 	max_width_col[0]=len(product_info[pname_dict[product]]['code'])
												ws.write(rowcount,0, cols[0], normal_style)
												ws.write(rowcount,1, cols[1], normal_style)
												ws.write(rowcount,2, cols[2]/181.44, normal_style_float)
												ws.write(rowcount,3, cols[3], normal_style_float)
												ws.write(rowcount,4, cols[4], normal_style_float)
												ws.write(rowcount,5, cols[5]/181.44, normal_style_float)
												ws.write(rowcount,6, cols[6], normal_style_float)
												ws.write(rowcount,7, cols[7], normal_style_float)
												ws.write(rowcount,8, cols[8]/181.44, normal_style_float)
												ws.write(rowcount,9, cols[9], normal_style_float)
												ws.write(rowcount,10, cols[10], normal_style_float)
												ws.write(rowcount,11, cols[11]/181.44, normal_style_float)
												ws.write(rowcount,12, cols[12], normal_style_float)
												ws.write(rowcount,13, cols[13], normal_style_float)
												ws.write(rowcount,14, cols[14]/181.44, normal_style_float)
												ws.write(rowcount,15, cols[15], normal_style_float)
												ws.write(rowcount,16, cols[16], normal_style_float)
												ws.write(rowcount,17, cols[17]/181.44, normal_style_float)
												ws.write(rowcount,18, cols[18], normal_style_float)
												ws.write(rowcount,19, cols[19]/181.44, normal_style_float)
												ws.write(rowcount,20, cols[20], normal_style_float)
												ws.write(rowcount,21, cols[21]/181.44, normal_style_float)
												ws.write(rowcount,22, cols[22], normal_style_float)
												ws.write(rowcount,23, cols[23], normal_style_float)
												current_row_mbc +=1
												rowcount+=1
												# current_location = locs.id
												for i in range(2,24):
													# print "cols-------------",cols[i]
													if i in (3,6,9,12,15,22):
														total_location.update({
															i:total_location.get(i,0.0)+(cols[i]*cols[i-1]),
															})
													else:
														total_location.update({
															i:total_location.get(i,0.0)+cols[i],
															})
												for i in range(2,24):
													# print "cols-------------",cols[i]
													if i in (3,6,9,12,15,22):
														totalparent.update({
															i:totalparent.get(i,0.0)+(cols[i]*cols[i-1]),
															})
													else:
														totalparent.update({
															i:totalparent.get(i,0.0)+cols[i],
															})
											if line_mbc_printed>0:
												rowcount+=1
												current_row_mbc = rowcount-1
												avg_row = current_row_mbc+2
												ws.write_merge(rowcount,rowcount,0,1,"*** Subtotal ***", th_both_style_dashed_bottom)
												ws.write(rowcount,2, xlwt.Formula("SUM($C$"+str(start_row_mbc)+":$C$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,3, xlwt.Formula("IF($C$"+str(avg_row)+"<>0.0,$E$"+str(avg_row)+"/$C$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,4, xlwt.Formula("SUM($E$"+str(start_row_mbc)+":$E$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,5, xlwt.Formula("SUM($F$"+str(start_row_mbc)+":$F$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,6, xlwt.Formula("IF($F$"+str(avg_row)+"<>0.0,$H$"+str(avg_row)+"/$F$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,7, xlwt.Formula("SUM($H$"+str(start_row_mbc)+":$H$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,8, xlwt.Formula("SUM($I$"+str(start_row_mbc)+":$I$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,9, xlwt.Formula("IF($I$"+str(avg_row)+"<>0.0,$K$"+str(avg_row)+"/$I$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,10, xlwt.Formula("SUM($K$"+str(start_row_mbc)+":$K$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,11, xlwt.Formula("SUM($L$"+str(start_row_mbc)+":$L$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,12, xlwt.Formula("IF($L$"+str(avg_row)+"<>0.0,$N$"+str(avg_row)+"/$L$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,13, xlwt.Formula("SUM($N$"+str(start_row_mbc)+":$N$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,14, xlwt.Formula("SUM($O$"+str(start_row_mbc)+":$O$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,15, xlwt.Formula("IF($O$"+str(avg_row)+"<>0.0,$Q$"+str(avg_row)+"/$O$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,16, xlwt.Formula("SUM($Q$"+str(start_row_mbc)+":$Q$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,17, xlwt.Formula("SUM($R$"+str(start_row_mbc)+":$R$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,18, xlwt.Formula("SUM($S$"+str(start_row_mbc)+":$S$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,19, xlwt.Formula("SUM($T$"+str(start_row_mbc)+":$T$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,20, xlwt.Formula("SUM($U$"+str(start_row_mbc)+":$U$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,21, xlwt.Formula("SUM($V$"+str(start_row_mbc)+":$V$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,22, xlwt.Formula("IF($V$"+str(avg_row)+"<>0.0,$X$"+str(avg_row)+"/$V$"+str(avg_row)+"/181.44,0.0)"), th_both_style_dashed_bottom)
												ws.write(rowcount,23, xlwt.Formula("SUM($X$"+str(start_row_mbc)+":$X$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												rowcount+=2

									ws.write_merge(rowcount,rowcount,0,1,"*** Total Location ***", th_both_style_dashed_bottom)
									for i in range(2,24):
										if i in (2,5,8,11,14,17,19,21):
											ws.write(rowcount,i,total_location.get(i,0.0)/181.44,th_both_style_dashed_bottom)
										elif i in (3,6,9,12,15,22):
											ws.write(rowcount,i,total_location.get((i-1),0.0)!=0.0 and total_location.get(i,0.0)/total_location.get((i-1),0.0) or 0.0,th_both_style_dashed_bottom)
										else:
											ws.write(rowcount,i,total_location.get(i,0.0),th_both_style_dashed_bottom)
									rowcount+=1	
							ws.write_merge(rowcount,rowcount,0,1,"*** Total ***", th_both_style_dashed_bottom)
							for i in range(2,24):
								if i in (2,5,8,11,14,17,19,21):
									ws.write(rowcount,i,totalparent.get(i,0.0)/181.44,th_both_style_dashed_bottom)
								elif i in (3,6,9,12,15,22):
									ws.write(rowcount,i,totalparent.get((i-1),0.0)!=0.0 and  totalparent.get(i,0.0)/totalparent.get((i-1),0.0) or 0.0,th_both_style_dashed_bottom)
								else:
									ws.write(rowcount,i,totalparent.get(i,0.0),th_both_style_dashed_bottom)
							rowcount+=1
				elif inventory_type.code in ('Finish_others','Waste','Scrap'):
					ws.write_merge(rowcount,rowcount,0,16, company.name, title_style)
					rowcount+=1
					# ws.write_merge(rowcount,rowcount,0,2, "Site ID %s"%(inventory_type.name), normal_bold_style_a)
					ws.write_merge(rowcount,rowcount,0,16, "%s Stock Valuation - %s"%(inventory_type.name,parser._get_mode(data)), title_style)
					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,16, "As on - %s"%parser._get_date_range(data), title_style)
					rowcount+=3
					ws.write_merge(rowcount,rowcount+1,0,0, "Item Code", th_both_style)
					ws.write_merge(rowcount,rowcount+1,1,1, "Description", th_both_style)
					ws.write_merge(rowcount,rowcount,2,4, "Opening Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,5,7, "Transfer", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,8,10, "Issue", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,11,13, "Issue Return", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,14,16, "Closing Stock", th_both_style_dashed)
					ws.write(rowcount,17, "Avg.", th_both_style_dashed)
					rowcount+=1
					ws.write(rowcount,2, "Qty", th_bottom_style)
					ws.write(rowcount,3, "Price/Kg", th_bottom_style)
					ws.write(rowcount,4, "Amount", th_bottom_style)
					ws.write(rowcount,5, "Qty", th_bottom_style)
					ws.write(rowcount,6, "Price/Kg", th_bottom_style)
					ws.write(rowcount,7, "Amount", th_bottom_style)
					ws.write(rowcount,8, "Qty", th_bottom_style)
					ws.write(rowcount,9, "Price/Kg", th_bottom_style)
					ws.write(rowcount,10, "Amount", th_bottom_style)
					ws.write(rowcount,11, "Qty", th_bottom_style)
					ws.write(rowcount,12, "Price/Kg", th_bottom_style)
					ws.write(rowcount,13, "Amount", th_bottom_style)
					ws.write(rowcount,14, "Qty", th_bottom_style)
					ws.write(rowcount,15, "Price/Kg", th_bottom_style)
					ws.write(rowcount,16, "Amount", th_bottom_style)
					ws.write(rowcount,17, "Weight", th_bottom_style)
					rowcount += 1

				elif inventory_type.code in ('Stores','Packing'):
					ws.write_merge(rowcount,rowcount,0,16, company.name, title_style)
					rowcount+=1
					# ws.write_merge(rowcount,rowcount,0,2, "Site ID %s"%(inventory_type.name), normal_bold_style_a)
					ws.write_merge(rowcount,rowcount,0,16, "%s Stock Valuation - %s"%(inventory_type.name,parser._get_mode(data)), title_style)
					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,16, "As on - %s"%parser._get_date_range(data), title_style)
					rowcount+=3
					ws.write_merge(rowcount,rowcount+1,0,0, "Item Code", th_both_style)
					ws.write_merge(rowcount,rowcount+1,1,1, "Description", th_both_style)
					ws.write_merge(rowcount,rowcount+1,2,2, "UoM", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,3,4, "Opening Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,5,6, "Receipt", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,7,8, "Retur", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,9,10, "Issue", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,11,12, "Issue Return", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,13,14, "Adjustment", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,15,16, "Closing Stock", th_both_style_dashed)
					
					rowcount+=1
					ws.write(rowcount,3, "Qty", th_bottom_style)
					ws.write(rowcount,4, "Amount", th_bottom_style)
					ws.write(rowcount,5, "Qty", th_bottom_style)
					ws.write(rowcount,6, "Amount", th_bottom_style)
					ws.write(rowcount,7, "Qty", th_bottom_style)
					ws.write(rowcount,8, "Amount", th_bottom_style)
					ws.write(rowcount,9, "Qty", th_bottom_style)
					ws.write(rowcount,10, "Amount", th_bottom_style)
					ws.write(rowcount,11, "Qty", th_bottom_style)
					ws.write(rowcount,12, "Amount", th_bottom_style)
					ws.write(rowcount,13, "Qty", th_bottom_style)
					ws.write(rowcount,14, "Amount", th_bottom_style)
					ws.write(rowcount,15, "Qty", th_bottom_style)
					ws.write(rowcount,16, "Amount", th_bottom_style)
					rowcount += 1

					call_valuation = parser.get_valuation(inventory_type.code,data)
					try:
						stocks,available_parent_loc,available_loc,available_prod = call_valuation
					except:
						stock, available_parent_loc, available_loc, available_prod ={}, [], [], []
					
					locations = parser.get_location(data)
					product_info = parser._get_product_info()
					grand_total = {}
					for i in range(3,17):
						grand_total.update({i:0.0})
					for parent in available_parent_loc:
						totalparent = {}
						for i in range(3,17):
							totalparent.update({i:0.0})
						if stocks.get(parent,False):
							ws.write_merge(rowcount,rowcount,0,2, parent, th_both_style_left)
							rowcount+=2
							for locs in locations:
								location = locs.id
								total_location = {}
								for i in range(3,17):
									total_location.update({i:0.0})
								if stocks[parent].get(location, False):
									ws.write_merge(rowcount,rowcount,0,2, locs.name, th_both_style_left)
									rowcount+=2
									start_row_mbc = rowcount+1
									for mbc in sorted(stocks[parent][location].keys()):
										if stocks[parent][location].get(mbc,False):
											start_row_mbc = rowcount
											current_row_mbc = rowcount
											pname_dict = {}
											pid_dict = {}
											for dummy_pname_dict in stocks[parent][location][mbc]:
												pname_dict.update({
													(dummy_pname_dict, product_info[dummy_pname_dict]['code']) : dummy_pname_dict
													})
											line_mbc_printed = 0
											for product in sorted(pname_dict.keys(), key=lambda p : p[1]):
												for track_id in stocks[parent][location][mbc][pname_dict[product]].keys():
													for uom_id in stocks[parent][location][mbc][pname_dict[product]][track_id].keys():
														line = stocks[parent][location][mbc][pname_dict[product]][track_id][uom_id]
														cols = {}
														cols.update({
															0:product_info[pname_dict[product]]['code'],
															1:product_info[pname_dict[product]]['name'],
															2:uoms[uom_id]['name'],
															3:('opening' in line.keys()) and line['opening'].get("uom_qty",0.0) or 0.0,
															4:('opening' in line.keys()) and line['opening'].get("uom_qty_value",0.0) or 0.0,
															5:('receipt' in line.keys()) and line['receipt'].get("uom_qty",0.0) or 0.0,
															6:('receipt' in line.keys()) and line['receipt'].get("uom_qty_value",0.0) or 0.0,
															7:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty",0.0) or 0.0,
															8:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty_value",0.0) or 0.0,
															9:('issue' in line.keys()) and line['issue'].get("uom_qty",0.0) or 0.0,
															10:('issue' in line.keys()) and line['issue'].get("uom_qty_value",0.0) or 0.0,
															11:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty",0.0) or 0.0,
															12:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty_value",0.0) or 0.0,
															13:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty",0.0) or 0.0,
															14:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty_value",0.0) or 0.0,
															15:('closing' in line.keys()) and line['closing'].get("uom_qty",0.0) or 0.0,
															16:('closing' in line.keys()) and line['closing'].get("uom_qty_value",0.0) or 0.0,
															})

														if cols[3]<0.0001 and cols[5]<0.0001 and cols[7]<0.0001 and cols[9]<0.0001 and cols[11]<0.0001 and (cols[13]>-0.0001 and cols[13]<0.0001) and cols[15]<0.0001:
															continue

														line_mbc_printed+=1
														if len(product_info[pname_dict[product]]['code'])>max_width_col[0]:
															max_width_col[0]=len(product_info[pname_dict[product]]['code'])
														if len(product_info[pname_dict[product]]['name'])>max_width_col[1]:
															max_width_col[1]=len(product_info[pname_dict[product]]['name'])
														if len(uoms[uom_id]['name'])>max_width_col[2]:
															max_width_col[2]=len(uoms[uom_id]['name'])
														ws.write(rowcount,0, cols[0], normal_style)
														ws.write(rowcount,1, cols[1], normal_style)
														ws.write(rowcount,2, cols[2], normal_style)
														ws.write(rowcount,3, cols[3], normal_style_float)
														ws.write(rowcount,4, cols[4], normal_style_float)
														ws.write(rowcount,5, cols[5], normal_style_float)
														ws.write(rowcount,6, cols[6], normal_style_float)
														ws.write(rowcount,7, cols[7], normal_style_float)
														ws.write(rowcount,8, cols[8], normal_style_float)
														ws.write(rowcount,9, cols[9], normal_style_float)
														ws.write(rowcount,10, cols[10], normal_style_float)
														ws.write(rowcount,11, cols[11], normal_style_float)
														ws.write(rowcount,12, cols[12], normal_style_float)
														ws.write(rowcount,13, cols[13], normal_style_float)
														ws.write(rowcount,14, cols[14], normal_style_float)
														ws.write(rowcount,15, cols[15], normal_style_float)
														ws.write(rowcount,16, cols[16], normal_style_float)
														current_row_mbc +=1
														rowcount+=1
														
														for i in range(3,17):
															total_location.update({
																i:total_location.get(i,0.0)+cols[i],
																})
															
														for i in range(3,17):
															totalparent.update({
																i:totalparent.get(i,0.0)+cols[i],
																})

											if line_mbc_printed>0:
												rowcount+=1
												current_row_mbc = rowcount-1
												# avg_row = current_row_mbc+2
												ws.write_merge(rowcount,rowcount,0,2,"*** Subtotal "+str(mbc)+" ***", th_both_style_dashed_bottom)
												ws.write(rowcount,3, xlwt.Formula("SUM($D$"+str(start_row_mbc)+":$D$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,4, xlwt.Formula("SUM($E$"+str(start_row_mbc)+":$E$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,5, xlwt.Formula("SUM($F$"+str(start_row_mbc)+":$F$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,6, xlwt.Formula("SUM($G$"+str(start_row_mbc)+":$G$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,7, xlwt.Formula("SUM($H$"+str(start_row_mbc)+":$H$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,8, xlwt.Formula("SUM($I$"+str(start_row_mbc)+":$I$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,9, xlwt.Formula("SUM($J$"+str(start_row_mbc)+":$J$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,10, xlwt.Formula("SUM($K$"+str(start_row_mbc)+":$K$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,11, xlwt.Formula("SUM($L$"+str(start_row_mbc)+":$L$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,12, xlwt.Formula("SUM($M$"+str(start_row_mbc)+":$M$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,13, xlwt.Formula("SUM($N$"+str(start_row_mbc)+":$N$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,14, xlwt.Formula("SUM($O$"+str(start_row_mbc)+":$O$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,15, xlwt.Formula("SUM($P$"+str(start_row_mbc)+":$P$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,16, xlwt.Formula("SUM($Q$"+str(start_row_mbc)+":$Q$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												rowcount+=2

									ws.write_merge(rowcount,rowcount,0,2,"*** Total Location "+str(locs.name)+" ***", th_both_style_dashed_bottom)
									for i in range(3,17):
										ws.write(rowcount, i, total_location.get(i,0.0), th_both_style_dashed_bottom)
									rowcount+=1	
							
							ws.write_merge(rowcount,rowcount,0,2,"*** Total "+str(parent)+" ***", th_both_style_dashed_bottom)
							for i in range(3,17):
								ws.write(rowcount,i,totalparent.get(i,0.0),th_both_style_dashed_bottom)
								grand_total[i]+=totalparent.get(i,0.0)
							rowcount+=1
					
					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,2,"*** Grand Total ***", th_both_style_dashed_bottom)
					for i in range(3,17):
						ws.write(rowcount,i,grand_total.get(i,0.0),th_both_style_dashed_bottom)

					for c in range(0,3):
						ws.col(c).width = 256 * int(max_width_col[c]*1.4)
				elif inventory_type.code=='Raw Material':
					ws.write_merge(rowcount,rowcount,0,24, company.name, title_style)
					rowcount+=1
					# ws.write_merge(rowcount,rowcount,0,2, "Site ID %s"%(inventory_type.name), normal_bold_style_a)
					ws.write_merge(rowcount,rowcount,0,24, "%s Stock Valuation - %s"%(inventory_type.name,parser._get_mode(data)), title_style)
					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,24, "As on - %s"%parser._get_date_range(data), title_style)
					rowcount+=3
					ws.write_merge(rowcount,rowcount+1,0,0, "Item Code", th_both_style)
					ws.write_merge(rowcount,rowcount+1,1,1, "Description", th_both_style)
					ws.write_merge(rowcount,rowcount+1,2,2, "UoM", th_both_style)
					ws.write_merge(rowcount,rowcount,3,5, "Opening Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,6,8, "Receipt", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,9,11, "Retur", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,12,14, "Issue", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,15,17, "Issue Return", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,18,20, "Adjustment", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount,21,23, "Closing Stock", th_both_style_dashed)
					ws.write_merge(rowcount,rowcount+1,24,24, "Avg\nWeight", th_both_style)
					
					rowcount+=1
					ws.write(rowcount,3, "Qty", th_bottom_style)
					ws.write(rowcount,4, "2nd Qty", th_bottom_style)
					ws.write(rowcount,5, "Amount", th_bottom_style)
					ws.write(rowcount,6, "Qty", th_bottom_style)
					ws.write(rowcount,7, "2nd Qty", th_bottom_style)
					ws.write(rowcount,8, "Amount", th_bottom_style)
					ws.write(rowcount,9, "Qty", th_bottom_style)
					ws.write(rowcount,10, "2nd Qty", th_bottom_style)
					ws.write(rowcount,11, "Amount", th_bottom_style)
					ws.write(rowcount,12, "Qty", th_bottom_style)
					ws.write(rowcount,13, "2nd Qty", th_bottom_style)
					ws.write(rowcount,14, "Amount", th_bottom_style)
					ws.write(rowcount,15, "Qty", th_bottom_style)
					ws.write(rowcount,16, "2nd Qty", th_bottom_style)
					ws.write(rowcount,17, "Amount", th_bottom_style)
					ws.write(rowcount,18, "Qty", th_bottom_style)
					ws.write(rowcount,19, "2nd Qty", th_bottom_style)
					ws.write(rowcount,20, "Amount", th_bottom_style)
					ws.write(rowcount,21, "Qty", th_bottom_style)
					ws.write(rowcount,22, "2nd Qty", th_bottom_style)
					ws.write(rowcount,23, "Amount", th_bottom_style)
					rowcount += 1

					call_valuation = parser.get_valuation(inventory_type.code,data)
					try:
						stocks,available_parent_loc,available_loc,available_prod = call_valuation
					except:
						stock, available_parent_loc, available_loc, available_prod ={}, [], [], []
					
					locations = parser.get_location(data)
					product_info = parser._get_product_info()
					grand_total = {}
					for i in range(3,25):
						grand_total.update({i:0.0})
					for parent in available_parent_loc:
						totalparent = {}
						for i in range(3,25):
							totalparent.update({i:0.0})
						if stocks.get(parent,False):
							ws.write_merge(rowcount,rowcount,0,2, parent, th_both_style_left)
							rowcount+=2
							for locs in locations:
								location = locs.id
								total_location = {}
								for i in range(3,25):
									total_location.update({i:0.0})
								if stocks[parent].get(location, False):
									ws.write_merge(rowcount,rowcount,0,2, locs.name, th_both_style_left)
									rowcount+=2
									start_row_mbc = rowcount+1
									for mbc in sorted(stocks[parent][location].keys()):
										if stocks[parent][location].get(mbc,False):
											start_row_mbc = rowcount
											current_row_mbc = rowcount
											pname_dict = {}
											pid_dict = {}
											for dummy_pname_dict in stocks[parent][location][mbc]:
												pname_dict.update({
													(dummy_pname_dict, product_info[dummy_pname_dict]['code']) : dummy_pname_dict
													})
											line_mbc_printed = 0
											for product in sorted(pname_dict.keys(), key=lambda p : p[1]):
												for uom_id in stocks[parent][location][mbc][pname_dict[product]].keys():
													line = stocks[parent][location][mbc][pname_dict[product]][uom_id]
													cols = {}
													cols.update({
														0:product_info[pname_dict[product]]['code'],
														1:product_info[pname_dict[product]]['name'],
														2:uoms[uom_id]['name'],
														3:('opening' in line.keys()) and line['opening'].get("uom_qty",0.0) or 0.0,
														4:('opening' in line.keys()) and line['opening'].get("uop_qty",0.0) or 0.0,
														5:('opening' in line.keys()) and line['opening'].get("uom_qty_value",0.0) or 0.0,
														6:('receipt' in line.keys()) and line['receipt'].get("uom_qty",0.0) or 0.0,
														7:('receipt' in line.keys()) and line['receipt'].get("uop_qty",0.0) or 0.0,
														8:('receipt' in line.keys()) and line['receipt'].get("uom_qty_value",0.0) or 0.0,
														9:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty",0.0) or 0.0,
														10:('return_receipt' in line.keys()) and line['return_receipt'].get("uop_qty",0.0) or 0.0,
														11:('return_receipt' in line.keys()) and line['return_receipt'].get("uom_qty_value",0.0) or 0.0,
														12:('issue' in line.keys()) and line['issue'].get("uom_qty",0.0) or 0.0,
														13:('issue' in line.keys()) and line['issue'].get("uop_qty",0.0) or 0.0,
														14:('issue' in line.keys()) and line['issue'].get("uom_qty_value",0.0) or 0.0,
														15:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty",0.0) or 0.0,
														16:('return_issue' in line.keys()) and line['return_issue'].get("uop_qty",0.0) or 0.0,
														17:('return_issue' in line.keys()) and line['return_issue'].get("uom_qty_value",0.0) or 0.0,
														18:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty",0.0) or 0.0,
														19:('adjustment' in line.keys()) and line['adjustment'].get("uop_qty",0.0) or 0.0,
														20:('adjustment' in line.keys()) and line['adjustment'].get("uom_qty_value",0.0) or 0.0,
														21:('closing' in line.keys()) and line['closing'].get("uom_qty",0.0) or 0.0,
														22:('closing' in line.keys()) and line['closing'].get("uop_qty",0.0) or 0.0,
														23:('closing' in line.keys()) and line['closing'].get("uom_qty_value",0.0) or 0.0,
														})
													
													cols.update({24:cols[22]>0 and round(cols[21]/cols[22],4) or 0.0})

													if cols[2]<0.01 and cols[4]<0.01 and cols[6]<0.01 and cols[8]<0.01 and cols[10]<0.01 and cols[12]<0.01 and cols[14]<0.01:
														continue

													line_mbc_printed+=1
													if len(product_info[pname_dict[product]]['code'])>max_width_col[0]:
														max_width_col[0]=len(product_info[pname_dict[product]]['code'])
													if len(product_info[pname_dict[product]]['name'])>max_width_col[1]:
														max_width_col[1]=len(product_info[pname_dict[product]]['name'])
													if len(uoms[uom_id]['name'])>max_width_col[2]:
														max_width_col[2]=len(uoms[uom_id]['name'])
													ws.write(rowcount,0, cols[0], normal_style)
													ws.write(rowcount,1, cols[1], normal_style)
													ws.write(rowcount,2, cols[2], normal_style)
													ws.write(rowcount,3, cols[3], normal_style_float)
													ws.write(rowcount,4, cols[4], normal_style_float)
													ws.write(rowcount,5, cols[5], normal_style_float)
													ws.write(rowcount,6, cols[6], normal_style_float)
													ws.write(rowcount,7, cols[7], normal_style_float)
													ws.write(rowcount,8, cols[8], normal_style_float)
													ws.write(rowcount,9, cols[9], normal_style_float)
													ws.write(rowcount,10, cols[10], normal_style_float)
													ws.write(rowcount,11, cols[11], normal_style_float)
													ws.write(rowcount,12, cols[12], normal_style_float)
													ws.write(rowcount,13, cols[13], normal_style_float)
													ws.write(rowcount,14, cols[14], normal_style_float)
													ws.write(rowcount,15, cols[15], normal_style_float)
													ws.write(rowcount,16, cols[16], normal_style_float)
													ws.write(rowcount,17, cols[17], normal_style_float)
													ws.write(rowcount,18, cols[18], normal_style_float)
													ws.write(rowcount,19, cols[19], normal_style_float)
													ws.write(rowcount,20, cols[20], normal_style_float)
													ws.write(rowcount,21, cols[21], normal_style_float)
													ws.write(rowcount,22, cols[22], normal_style_float)
													ws.write(rowcount,23, cols[23], normal_style_float)
													ws.write(rowcount,24, cols[24], normal_style_float)
													current_row_mbc +=1
													rowcount+=1
													
													for i in range(3,25):
														total_location.update({
															i:total_location.get(i,0.0)+cols[i],
															})
														
													for i in range(3,25):
														totalparent.update({
															i:totalparent.get(i,0.0)+cols[i],
															})

											if line_mbc_printed>0:
												rowcount+=1
												current_row_mbc = rowcount-1
												# avg_row = current_row_mbc+2
												ws.write_merge(rowcount,rowcount,0,2,"*** Subtotal "+str(mbc)+" ***", th_both_style_dashed_bottom)
												ws.write(rowcount,3, xlwt.Formula("SUM($D$"+str(start_row_mbc)+":$D$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,4, xlwt.Formula("SUM($E$"+str(start_row_mbc)+":$E$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,5, xlwt.Formula("SUM($F$"+str(start_row_mbc)+":$F$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,6, xlwt.Formula("SUM($G$"+str(start_row_mbc)+":$G$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,7, xlwt.Formula("SUM($H$"+str(start_row_mbc)+":$H$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,8, xlwt.Formula("SUM($I$"+str(start_row_mbc)+":$I$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,9, xlwt.Formula("SUM($J$"+str(start_row_mbc)+":$J$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,10, xlwt.Formula("SUM($K$"+str(start_row_mbc)+":$K$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,11, xlwt.Formula("SUM($L$"+str(start_row_mbc)+":$L$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,12, xlwt.Formula("SUM($M$"+str(start_row_mbc)+":$M$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,13, xlwt.Formula("SUM($N$"+str(start_row_mbc)+":$N$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,14, xlwt.Formula("SUM($O$"+str(start_row_mbc)+":$O$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,15, xlwt.Formula("SUM($P$"+str(start_row_mbc)+":$P$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,16, xlwt.Formula("SUM($Q$"+str(start_row_mbc)+":$Q$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,17, xlwt.Formula("SUM($R$"+str(start_row_mbc)+":$R$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,18, xlwt.Formula("SUM($S$"+str(start_row_mbc)+":$S$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,19, xlwt.Formula("SUM($T$"+str(start_row_mbc)+":$T$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,20, xlwt.Formula("SUM($U$"+str(start_row_mbc)+":$U$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,21, xlwt.Formula("SUM($V$"+str(start_row_mbc)+":$V$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,22, xlwt.Formula("SUM($W$"+str(start_row_mbc)+":$W$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,23, xlwt.Formula("SUM($X$"+str(start_row_mbc)+":$X$"+str(current_row_mbc)+")"), th_both_style_dashed_bottom)
												ws.write(rowcount,24, " ", th_both_style_dashed_bottom)
												rowcount+=2

									ws.write_merge(rowcount,rowcount,0,2,"*** Total Location : "+str(locs.name)+" ***", th_both_style_dashed_bottom)
									for i in range(3,24):
										ws.write(rowcount, i, total_location.get(i,0.0), th_both_style_dashed_bottom)
									ws.write(rowcount,24, " ", th_both_style_dashed_bottom)
									rowcount+=1	
							
							ws.write_merge(rowcount,rowcount,0,2,"*** Total "+str(parent)+" ***", th_both_style_dashed_bottom)
							for i in range(3,24):
								ws.write(rowcount,i,totalparent.get(i,0.0),th_both_style_dashed_bottom)
								grand_total[i]+=totalparent.get(i,0.0)
							ws.write(rowcount,24, " ", th_both_style_dashed_bottom)
							rowcount+=1

					rowcount+=1
					ws.write_merge(rowcount,rowcount,0,2,"*** Grand Total ***", th_both_style_dashed_bottom)
					for i in range(3,24):
						ws.write(rowcount,i,grand_total.get(i,0.0),th_both_style_dashed_bottom)

					for c in range(0,3):
						ws.col(c).width = 256 * int(max_width_col[c]*1.4)
		pass
							
#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
valuation_report_xls('report.valuation.stock.report.bitratex','stock.report.bitratex.wizard', 'addons/ad_stock_report/report/stock_report.mako',
						parser=ReportStockValBitra)