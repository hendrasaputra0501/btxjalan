import time
import xlwt
from ad_account_optimization.report.report_engine_xls import report_xls
#from report_engine_xls import report_xls
from ad_stock_report.report.stock_report_parser import ReportStockBitra

import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class stock_report_xls(report_xls):
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
		c = parser.localcontext['company']
		i=0
		#inventory_types = parser._get_inventory_type(data)
		# print "==============",data['grouping']
		
		prods = parser._get_product_info()
		trackings = parser._get_tracking_info()
		uoms = parser._get_uom_info()
		# print "************************",uoms
		# print "xxxxxxxxxxxxxxxxxxxxxxxxxxx",trackings

		if data['grouping']=='location':
			for inventory_type in parser._get_inventory_type(data): 
				stock_lines,available_parent,location_line,product_line,track_lines,uop_lines = parser._get_stock(data,inventory_type)
				# try:
				# except:
				# 	stock_lines,available_parent,location_line,product_line,track_lines,uop_lines = [],[],[],[],[],[]
				ws = wb.add_sheet('Class - %s'%inventory_type.name,cell_overwrite_ok=True)
				ws.panes_frozen = True
				ws.remove_splits = True
				ws.portrait = 0 # Landscape
				ws.fit_width_to_pages = 1
				ws.preview_magn = 65
				ws.normal_magn = 65
				ws.print_scaling=65
				ws.page_preview = False
				ws.set_fit_width_to_pages(1)
				##Penempatan untuk template rows
				title_style 					= xlwt.easyxf('font: height 220, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz center; ')
				normal_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz left;',num_format_str='#,##0.00;-#,##0.00')
				normal_style_float 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
				normal_style_float_round 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz right;',num_format_str='#,##0')
				normal_style_float_bold 		= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
				normal_bold_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
				normal_bold_style_a 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap on, vert centre, horiz left; ')
				normal_bold_style_b 			= xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap on, vert centre, horiz left; ')
				th_top_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick')
				th_both_style 					= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:top thick, bottom thick')
				th_bottom_style 				= xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap on, vert centre, horiz center; border:bottom thick')
				
				#with border
				subtotal_title_style			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left; borders: bottom thin;')
				subtotal_style				  	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0;-#,##0')
				subtotal_style2				 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right; borders: bottom thin;',num_format_str='#,##0.00;-#,##0.00')
				#without border
				subtotal_title_style_2			= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;')
				subtotal_style_2				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0;-#,##0')
				subtotal_style2_2				= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
				
				total_title_style			   	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
				total_style					 	= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
				total_style2					= xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap on, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
				subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap on, vert centre, horiz left; pattern: pattern solid, fore_color white;')


				rowcount = 0
				ws.write_merge(rowcount,rowcount,0,18, c.name, title_style)
				rowcount+=1
				ws.write_merge(rowcount,rowcount,0,18, "STOCK STATUS - %s"%parser._get_mode(data), title_style)
				rowcount+=1
				ws.write_merge(rowcount+1,rowcount+1,0,1, "Class ID - %s"%inventory_type.name,normal_style)
				ws.write_merge(rowcount,rowcount,0,18, "As on - %s"%parser._get_date_range(data), title_style)
				rowcount+=3
				ws.write_merge(rowcount,rowcount,0,1, "Inventory", th_top_style)
				ws.write_merge(rowcount,rowcount+1,2,2, "Lot No.", th_both_style)
				ws.write_merge(rowcount,rowcount+1,3,3, "UoP", th_both_style)
				ws.write_merge(rowcount,rowcount,4,5, "Opening", th_top_style)
				ws.write_merge(rowcount,rowcount,6,7, "Receipt", th_top_style)
				ws.write_merge(rowcount,rowcount,8,9, "Return", th_top_style)
				if inventory_type.code == 'Finish':
					ws.write_merge(rowcount,rowcount,10,11, "Sales", th_top_style)
				elif inventory_type.code in ('Finish_others','Waste','Scrap','Stores','Packing','Raw Material'):
					ws.write_merge(rowcount,rowcount,10,11, "Issue", th_top_style)
				ws.write_merge(rowcount,rowcount,12,13, "Return", th_top_style)
				ws.write_merge(rowcount,rowcount,14,15, "Adjustment", th_top_style)
				ws.write_merge(rowcount,rowcount,16,17, "Closing", th_top_style)
				if inventory_type.code == 'Finish':
					ws.write(rowcount,18, "Qty to Adjust", th_top_style)
					ws.write(rowcount+1,18, "KGS", th_bottom_style)
				elif inventory_type.code == 'Raw Material':
					ws.write(rowcount,18, "AVG", th_top_style)
					ws.write(rowcount+1,18, "Weight", th_bottom_style)
				
				rowcount+=1
				
				ws.write(rowcount,0, "ID", th_bottom_style)
				ws.write(rowcount,1, "Name", th_bottom_style)
				rowcount+=1

				if inventory_type.code in ('Finish_others','Raw Material'):
					uom_label = "Kgs"
				elif inventory_type.code == 'Finish':
					uom_label = "Bales"
				else:
					uom_label = "NOS"
				
				for cols in range(4,18):
					if cols%2==0:
						ws.write(rowcount-1,cols,uom_label,th_both_style)
					elif cols%2!=0:
						ws.write(rowcount-1,cols,"2nd Qty",th_both_style)
				rowcount+=1
				max_length_loc=0
				max_length_prod_code = 0
				max_length_prod_name = 0
				max_length_uom_name = 0
				total_location={
					1:0.0,
					2:0.0,
					3:0.0,
					4:0.0,
					5:0.0,
					6:0.0,
					7:0.0,
					8:0.0,
					9:0.0,
					10:0.0,
					11:0.0,
					12:0.0,
					13:0.0,
					14:0.0,
					}
				total_blend = total_location.copy()
				total_wax = total_location.copy()
				total_sd = total_location.copy()
				total_ct = total_location.copy()
				total_parent = total_location.copy()
				grand_total = total_location.copy()

				current_parent= False
				# print "---------###########################--------",available_parent
				for parent_loc in available_parent:			
					current_location=False
					for location in parser._get_available_location(parent_loc,location_line):
						# print "======================",location._model._columns['usage'].selection
						if location.id in location_line:
							# SEPENUH HATIKU~
							ws.write_merge(rowcount,rowcount,0,18,location.name,normal_bold_style_b)
							rowcount+=1
						else:
							continue
						########## write the datas ###############
						if stock_lines:
							# print "===============",stock_lines[parent_loc][location.id]
							current_blend=False
							# print "xxxxxxxxxxxxxx",parent_loc,location.id,stock_lines[parent_loc]
							if location.id in stock_lines[parent_loc]:
								for bl in sorted(stock_lines[parent_loc][location.id].keys()):
									if inventory_type.code == 'Finish':
										current_ct = False
										for ct in sorted(stock_lines[parent_loc][location.id][bl].keys()):
											current_sd = False
											for sd in stock_lines[parent_loc][location.id][bl][ct]:
												current_wax = False
												for wax in sorted(stock_lines[parent_loc][location.id][bl][ct][sd].keys()):
													for pl in stock_lines[parent_loc][location.id][bl][ct][sd][wax]:
														# print "pl===========",pl,stock_lines[parent_loc][location.id][bl][ct][sd]
														for tl in stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl]:
															# print "tl===========",stock_lines[parent_loc][location.id][bl][ct][sd]
															for uop_l in stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl]:
																# inisialisasi quantity kg
																try:
																	opening_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']
																except:
																	opening_kg = 0
																try:
																	incoming_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uom_qty']
																except:
																	incoming_kg = 0
																try:
																	in_return_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uom_qty']
																except:
																	in_return_kg = 0
																try:
																	outgoing_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uom_qty']
																except:
																	outgoing_kg = 0
																try:
																	out_return_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uom_qty']
																except:
																	out_return_kg = 0
																try:
																	issue_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uom_qty']
																except:
																	issue_kg = 0
																try:
																	closing_kg = stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']
																except:
																	closing_kg = 0
																# jika semua nilai opening sampai closing dibawah 1 kg, dihilangkan saja
																if opening_kg<1 and opening_kg>-1 and incoming_kg<1 and incoming_kg>-1 and in_return_kg<1 and in_return_kg>-1 and outgoing_kg<1 and outgoing_kg>-1 and out_return_kg<1 and out_return_kg>-1 and issue_kg<1 and issue_kg>-1 and closing_kg<1 and closing_kg>-1:
																	if data['show_only_qty_less_than_1_kg'] and closing_kg<>0.0:
																		ws.write(rowcount,0, prods[pl]['code'], normal_style)
																		ws.write(rowcount,1, prods[pl]['name'], normal_style)
																		if len(prods[pl]['name'])>max_length_prod_name:
																			max_length_prod_name=len(prods[pl]['name'])

																		if len(prods[pl]['code'])>max_length_prod_code:
																			max_length_prod_code=len(prods[pl]['code'])
																		# print "==============", uop_l, uoms[uop_l]
																		if len(uoms[uop_l]['name'])>max_length_uom_name:
																			max_length_uom_name=len(uoms[uop_l]['name'])
																		if tl != 0:
																			ws.write(rowcount,2, trackings[tl]['name'], normal_style)
																		else:
																			ws.write(rowcount,2, "Undef.Lot", normal_style)
																		if uop_l != 0:
																			ws.write(rowcount,3, uoms[uop_l]['name'], normal_style)
																		else:
																			ws.write(rowcount,3, "Undef.Pack", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44,2) or 0.0
																			# ws.write(rowcount,4, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44 or "", normal_style_float)
																			ws.write(rowcount,4, stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44, normal_style_float)
																		except:
																			ws.write(rowcount,4, 0.0, normal_style_float)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'],2) or 0.0
																			ws.write(rowcount,5, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,5, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uom_qty']/181.44,2) or 0.0
																			ws.write(rowcount,6, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uom_qty']/181.44 or "", normal_style_float)
																		except:
																			ws.write(rowcount,6, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'],2) or 0.0
																			ws.write(rowcount,7, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,7, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uom_qty']/181.44,2) or 0.0
																			ws.write(rowcount,8, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uom_qty']/181.44 or "", normal_style_float)
																		except:
																			ws.write(rowcount,8, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'],2) or 0.0
																			ws.write(rowcount,9, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,9, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uom_qty']/181.44,2) or 0.0
																			ws.write(rowcount,10, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uom_qty']/181.44 or "", normal_style_float)
																		except:
																			ws.write(rowcount,10, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'],2) or 0.0
																			ws.write(rowcount,11, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,11, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uom_qty']/181.44,2) or 0.0
																			ws.write(rowcount,12, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uom_qty']/181.44 or "", normal_style_float)
																		except:
																			ws.write(rowcount,12, "", normal_style)
																		try:	
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'],2) or 0.0
																			ws.write(rowcount,13, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,13, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uom_qty']/181.44,2) or 0.0
																			ws.write(rowcount,14, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uom_qty']/181.44 or "", normal_style_float)
																		except:
																			ws.write(rowcount,14, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'],2) or 0.0
																			ws.write(rowcount,15, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,15, "", normal_style)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44,2) or 0.0
																			# ws.write(rowcount,16, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44 or "", normal_style_float)
																			ws.write(rowcount,16, stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44, normal_style_float)
																		except:
																			ws.write(rowcount,16, 0.0, normal_style_float)
																		try:
																			rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'],2) or 0.0
																			ws.write(rowcount,17, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or "", normal_style_float_round)
																		except:
																			ws.write(rowcount,17, "", normal_style)
																		try:
																			rounder=stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty'] or 0.0
																			# ws.write(rowcount,16, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44 or "", normal_style_float)
																			ws.write(rowcount,18, stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty'], normal_style_float)
																		except:
																			ws.write(rowcount,18, 0.0, normal_style_float)
																		rowcount+=1

																		if wax==current_wax or current_wax==False:
																			total_wax.update({
																				1:total_wax[1]+(opening_kg/181.44 or 0.0),
																				2:total_wax[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_wax[3]+(incoming_kg/181.44 or 0.0),
																				4:total_wax[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_wax[5]+(in_return_kg/181.44 or 0.0),
																				6:total_wax[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_wax[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_wax[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_wax[9]+(out_return_kg/181.44 or 0.0),
																				10:total_wax[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_wax[11]+(issue_kg/181.44 or 0.0),
																				12:total_wax[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_wax[13]+(closing_kg/181.44 or 0.0),
																				14:total_wax[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_wax=wax
																		if sd==current_sd or current_sd==False:
																			total_sd.update({
																				1:total_sd[1]+(opening_kg/181.44 or 0.0),
																				2:total_sd[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_sd[3]+(incoming_kg/181.44 or 0.0),
																				4:total_sd[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_sd[5]+(in_return_kg/181.44 or 0.0),
																				6:total_sd[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_sd[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_sd[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_sd[9]+(out_return_kg/181.44 or 0.0),
																				10:total_sd[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_sd[11]+(issue_kg/181.44 or 0.0),
																				12:total_sd[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_sd[13]+(closing_kg/181.44 or 0.0),
																				14:total_sd[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_sd=sd
																		if ct==current_ct or current_ct==False:
																			total_ct.update({
																				1:total_ct[1]+(opening_kg/181.44 or 0.0),
																				2:total_ct[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_ct[3]+(incoming_kg/181.44 or 0.0),
																				4:total_ct[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_ct[5]+(in_return_kg/181.44 or 0.0),
																				6:total_ct[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_ct[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_ct[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_ct[9]+(out_return_kg/181.44 or 0.0),
																				10:total_ct[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_ct[11]+(issue_kg/181.44 or 0.0),
																				12:total_ct[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_ct[13]+(closing_kg/181.44 or 0.0),
																				14:total_ct[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_ct=ct
																		if bl==current_blend or current_blend==False:
																			total_blend.update({
																				1:total_blend[1]+(opening_kg/181.44 or 0.0),
																				2:total_blend[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_blend[3]+(incoming_kg/181.44 or 0.0),
																				4:total_blend[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_blend[5]+(in_return_kg/181.44 or 0.0),
																				6:total_blend[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_blend[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_blend[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_blend[9]+(out_return_kg/181.44 or 0.0),
																				10:total_blend[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_blend[11]+(issue_kg/181.44 or 0.0),
																				12:total_blend[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_blend[13]+(closing_kg/181.44 or 0.0),
																				14:total_blend[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_blend=bl
																		if location.id==current_location or current_location==False:
																			total_location.update({
																				1:total_location[1]+(opening_kg/181.44 or 0.0),
																				2:total_location[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_location[3]+(incoming_kg/181.44 or 0.0),
																				4:total_location[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_location[5]+(in_return_kg/181.44 or 0.0),
																				6:total_location[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_location[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_location[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_location[9]+(out_return_kg/181.44 or 0.0),
																				10:total_location[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_location[11]+(issue_kg/181.44 or 0.0),
																				12:total_location[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_location[13]+(closing_kg/181.44 or 0.0),
																				14:total_location[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_location=location.id
																		# print "===============================",total_wax
																		if parent_loc==current_parent or current_parent==False:
																			total_parent.update({
																				1:total_parent[1]+(opening_kg/181.44 or 0.0),
																				2:total_parent[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																				3:total_parent[3]+(incoming_kg/181.44 or 0.0),
																				4:total_parent[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																				5:total_parent[5]+(in_return_kg/181.44 or 0.0),
																				6:total_parent[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																				7:total_parent[7]+(outgoing_kg/181.44 or 0.0),
																				8:total_parent[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																				9:total_parent[9]+(out_return_kg/181.44 or 0.0),
																				10:total_parent[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																				11:total_parent[11]+(issue_kg/181.44 or 0.0),
																				12:total_parent[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																				13:total_parent[13]+(closing_kg/181.44 or 0.0),
																				14:total_parent[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																				})
																			current_parent=parent_loc
																	else:
																		continue
																# if False:
																# 	continue
																else:
																	if data['show_only_qty_less_than_1_kg']:
																		continue
																	ws.write(rowcount,0, prods[pl]['code'], normal_style)
																	ws.write(rowcount,1, prods[pl]['name'], normal_style)
																	if len(prods[pl]['name'])>max_length_prod_name:
																		max_length_prod_name=len(prods[pl]['name'])

																	if len(prods[pl]['code'])>max_length_prod_code:
																		max_length_prod_code=len(prods[pl]['code'])
																	# print "==============", uop_l, uoms[uop_l]
																	if len(uoms[uop_l]['name'])>max_length_uom_name:
																		max_length_uom_name=len(uoms[uop_l]['name'])
																	if tl != 0:
																		ws.write(rowcount,2, trackings[tl]['name'], normal_style)
																	else:
																		ws.write(rowcount,2, "Undef.Lot", normal_style)
																	if uop_l != 0:
																		ws.write(rowcount,3, uoms[uop_l]['name'], normal_style)
																	else:
																		ws.write(rowcount,3, "Undef.Pack", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44,2) or 0.0
																		# ws.write(rowcount,4, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44 or "", normal_style_float)
																		ws.write(rowcount,4, stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uom_qty']/181.44, normal_style_float)
																	except:
																		ws.write(rowcount,4, 0.0, normal_style_float)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'],2) or 0.0
																		ws.write(rowcount,5, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,5, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uom_qty']/181.44,2) or 0.0
																		ws.write(rowcount,6, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uom_qty']/181.44 or "", normal_style_float)
																	except:
																		ws.write(rowcount,6, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'],2) or 0.0
																		ws.write(rowcount,7, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,7, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uom_qty']/181.44,2) or 0.0
																		ws.write(rowcount,8, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uom_qty']/181.44 or "", normal_style_float)
																	except:
																		ws.write(rowcount,8, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'],2) or 0.0
																		ws.write(rowcount,9, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,9, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uom_qty']/181.44,2) or 0.0
																		ws.write(rowcount,10, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uom_qty']/181.44 or "", normal_style_float)
																	except:
																		ws.write(rowcount,10, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'],2) or 0.0
																		ws.write(rowcount,11, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,11, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uom_qty']/181.44,2) or 0.0
																		ws.write(rowcount,12, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uom_qty']/181.44 or "", normal_style_float)
																	except:
																		ws.write(rowcount,12, "", normal_style)
																	try:	
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'],2) or 0.0
																		ws.write(rowcount,13, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,13, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uom_qty']/181.44,2) or 0.0
																		ws.write(rowcount,14, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uom_qty']/181.44 or "", normal_style_float)
																	except:
																		ws.write(rowcount,14, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'],2) or 0.0
																		ws.write(rowcount,15, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,15, "", normal_style)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44,2) or 0.0
																		# ws.write(rowcount,16, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44 or "", normal_style_float)
																		ws.write(rowcount,16, stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uom_qty']/181.44, normal_style_float)
																	except:
																		ws.write(rowcount,16, 0.0, normal_style_float)
																	try:
																		rounder=round(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'],2) or 0.0
																		ws.write(rowcount,17, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or "", normal_style_float_round)
																	except:
																		ws.write(rowcount,17, "", normal_style)
																	rowcount+=1

																	if wax==current_wax or current_wax==False:
																		total_wax.update({
																			1:total_wax[1]+(opening_kg/181.44 or 0.0),
																			2:total_wax[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_wax[3]+(incoming_kg/181.44 or 0.0),
																			4:total_wax[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_wax[5]+(in_return_kg/181.44 or 0.0),
																			6:total_wax[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_wax[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_wax[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_wax[9]+(out_return_kg/181.44 or 0.0),
																			10:total_wax[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_wax[11]+(issue_kg/181.44 or 0.0),
																			12:total_wax[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_wax[13]+(closing_kg/181.44 or 0.0),
																			14:total_wax[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_wax=wax
																	if sd==current_sd or current_sd==False:
																		total_sd.update({
																			1:total_sd[1]+(opening_kg/181.44 or 0.0),
																			2:total_sd[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_sd[3]+(incoming_kg/181.44 or 0.0),
																			4:total_sd[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_sd[5]+(in_return_kg/181.44 or 0.0),
																			6:total_sd[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_sd[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_sd[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_sd[9]+(out_return_kg/181.44 or 0.0),
																			10:total_sd[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_sd[11]+(issue_kg/181.44 or 0.0),
																			12:total_sd[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_sd[13]+(closing_kg/181.44 or 0.0),
																			14:total_sd[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_sd=sd
																	if ct==current_ct or current_ct==False:
																		total_ct.update({
																			1:total_ct[1]+(opening_kg/181.44 or 0.0),
																			2:total_ct[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_ct[3]+(incoming_kg/181.44 or 0.0),
																			4:total_ct[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_ct[5]+(in_return_kg/181.44 or 0.0),
																			6:total_ct[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_ct[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_ct[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_ct[9]+(out_return_kg/181.44 or 0.0),
																			10:total_ct[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_ct[11]+(issue_kg/181.44 or 0.0),
																			12:total_ct[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_ct[13]+(closing_kg/181.44 or 0.0),
																			14:total_ct[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_ct=ct
																	if bl==current_blend or current_blend==False:
																		total_blend.update({
																			1:total_blend[1]+(opening_kg/181.44 or 0.0),
																			2:total_blend[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_blend[3]+(incoming_kg/181.44 or 0.0),
																			4:total_blend[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_blend[5]+(in_return_kg/181.44 or 0.0),
																			6:total_blend[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_blend[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_blend[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_blend[9]+(out_return_kg/181.44 or 0.0),
																			10:total_blend[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_blend[11]+(issue_kg/181.44 or 0.0),
																			12:total_blend[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_blend[13]+(closing_kg/181.44 or 0.0),
																			14:total_blend[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_blend=bl
																	if location.id==current_location or current_location==False:
																		total_location.update({
																			1:total_location[1]+(opening_kg/181.44 or 0.0),
																			2:total_location[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_location[3]+(incoming_kg/181.44 or 0.0),
																			4:total_location[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_location[5]+(in_return_kg/181.44 or 0.0),
																			6:total_location[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_location[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_location[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_location[9]+(out_return_kg/181.44 or 0.0),
																			10:total_location[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_location[11]+(issue_kg/181.44 or 0.0),
																			12:total_location[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_location[13]+(closing_kg/181.44 or 0.0),
																			14:total_location[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_location=location.id
																	# print "===============================",total_wax
																	if parent_loc==current_parent or current_parent==False:
																		total_parent.update({
																			1:total_parent[1]+(opening_kg/181.44 or 0.0),
																			2:total_parent[2]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																			3:total_parent[3]+(incoming_kg/181.44 or 0.0),
																			4:total_parent[4]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																			5:total_parent[5]+(in_return_kg/181.44 or 0.0),
																			6:total_parent[6]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																			7:total_parent[7]+(outgoing_kg/181.44 or 0.0),
																			8:total_parent[8]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																			9:total_parent[9]+(out_return_kg/181.44 or 0.0),
																			10:total_parent[10]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																			11:total_parent[11]+(issue_kg/181.44 or 0.0),
																			12:total_parent[12]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																			13:total_parent[13]+(closing_kg/181.44 or 0.0),
																			14:total_parent[14]+(stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][ct][sd][wax][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																			})
																		current_parent=parent_loc
													cek_total_wax = True
													for i in range(1,15):
														cek_total_wax = cek_total_wax and (total_wax[i]==0)
													if not cek_total_wax:
														ws.write_merge(rowcount,rowcount,1,3,"Subtotal:",subtotal_title_style_2)
														ws.write(rowcount,4,total_wax[1]!=0.0 and total_wax[1] or '',subtotal_style2_2)
														ws.write(rowcount,5,total_wax[2]!=0.0 and total_wax[2] or '',subtotal_style_2)
														ws.write(rowcount,6,total_wax[3]!=0.0 and total_wax[3] or '',subtotal_style2_2)
														ws.write(rowcount,7,total_wax[4]!=0.0 and total_wax[4] or '',subtotal_style_2)
														ws.write(rowcount,8,total_wax[5]!=0.0 and total_wax[5] or '',subtotal_style2_2)
														ws.write(rowcount,9,total_wax[6]!=0.0 and total_wax[6] or '',subtotal_style_2)
														ws.write(rowcount,10,total_wax[7]!=0.0 and total_wax[7] or '',subtotal_style2_2)
														ws.write(rowcount,11,total_wax[8]!=0.0 and total_wax[8] or '',subtotal_style_2)
														ws.write(rowcount,12,total_wax[9]!=0.0 and total_wax[9] or '',subtotal_style2_2)
														ws.write(rowcount,13,total_wax[10]!=0.0 and total_wax[10] or '',subtotal_style_2)
														ws.write(rowcount,14,total_wax[11]!=0.0 and total_wax[11] or '',subtotal_style2_2)
														ws.write(rowcount,15,total_wax[12]!=0.0 and total_wax[12] or '',subtotal_style_2)
														ws.write(rowcount,16,total_wax[13]!=0.0 and total_wax[13] or '',subtotal_style2_2)
														ws.write(rowcount,17,total_wax[14]!=0.0 and total_wax[14] or '',subtotal_style_2)
														rowcount+=1
													current_wax=False
													for i in range(1,15):
														total_wax[i]=0.0
											# print "============================",rowcount
											# ws.write_merge(rowcount,rowcount,1,3,"Total Single/Double: %s"%sd,normal_bold_style)
											# ws.write(rowcount,4,total_sd[1]!=0.0 and total_sd[1] or '',normal_style_float_bold)
											# # ws.write(rowcount,5,total_sd[2],normal_style_float_bold)
											# ws.write(rowcount,6,total_sd[3]!=0.0 and total_sd[3] or '',normal_style_float_bold)
											# # ws.write(rowcount,7,total_sd[4],normal_style_float_bold)
											# ws.write(rowcount,8,total_sd[5]!=0.0 and total_sd[5] or '',normal_style_float_bold)
											# # ws.write(rowcount,9,total_sd[6],normal_style_float_bold)
											# ws.write(rowcount,10,total_sd[7]!=0.0 and total_sd[7] or '',normal_style_float_bold)
											# # ws.write(rowcount,11,total_sd[8],normal_style_float_bold)
											# ws.write(rowcount,12,total_sd[9]!=0.0 and total_sd[9] or '',normal_style_float_bold)
											# # ws.write(rowcount,13,total_sd[10],normal_style_float_bold)
											# ws.write(rowcount,14,total_sd[11]!=0.0 and total_sd[11] or '',normal_style_float_bold)
											# # ws.write(rowcount,15,total_sd[12],normal_style_float_bold)
											# ws.write(rowcount,16,total_sd[13]!=0.0 and total_sd[13] or '',normal_style_float_bold)
											# ws.write(rowcount,17,total_sd[14],normal_style_float_bold)
											# rowcount+=1
											current_sd=False
											for i in range(1,15):
												total_sd[i]=0.0
									elif inventory_type.code in ('Finish_others','Waste','Scrap','Stores','Packing','Fixed'):
										for pl in stock_lines[parent_loc][location.id][bl]:
											# print "pl===========",pl,stock_lines[parent_loc][location.id][bl][ct][sd]
											for tl in stock_lines[parent_loc][location.id][bl][pl]:
												# print "tl===========",stock_lines[parent_loc][location.id][bl][ct][sd]
												for uop_l in stock_lines[parent_loc][location.id][bl][pl][tl]:
													# inisialisasi quantity kg
													try:
														opening_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty']
													except:
														opening_kg = 0
													try:
														incoming_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty']
													except:
														incoming_kg = 0
													try:
														in_return_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty']
													except:
														in_return_kg = 0
													try:
														outgoing_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty']
													except:
														outgoing_kg = 0
													try:
														out_return_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty']
													except:
														out_return_kg = 0
													try:
														issue_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty']
													except:
														issue_kg = 0
													try:
														closing_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty']
													except:
														closing_kg = 0
													# jika semua nilai opening sampai closing dibawah 1 kg, dihilangkan saja
													if opening_kg<0.01 and opening_kg>-0.01 and incoming_kg<0.01 and incoming_kg>-0.01 and in_return_kg<0.01 and in_return_kg>-0.01 and outgoing_kg<0.01 and outgoing_kg>-0.01 and out_return_kg<0.01 and out_return_kg>-0.01 and issue_kg<0.01 and issue_kg>-0.01 and closing_kg<0.01 and closing_kg>-0.01:
														continue
													# if False:
													# 	continue
													else:
														ws.write(rowcount,0, prods[pl]['code'], normal_style)
														ws.write(rowcount,1, prods[pl]['name'], normal_style)
														if len(prods[pl]['name'])>max_length_prod_name:
															max_length_prod_name=len(prods[pl]['name'])

														if len(prods[pl]['code'])>max_length_prod_code:
															max_length_prod_code=len(prods[pl]['code'])
														# print "==============", uop_l, uoms[uop_l]
														if uoms.get(uop_l,False) and len(uoms[uop_l]['name'])>max_length_uom_name:
															max_length_uom_name=len(uoms[uop_l]['name'])
														if tl != 0:
															ws.write(rowcount,2, trackings[tl]['name'], normal_style)
														else:
															ws.write(rowcount,2, "", normal_style)
														if uop_l != 0:
															ws.write(rowcount,3, uoms.get(uop_l,False) and uoms[uop_l]['name'] or '', normal_style)
														else:
															ws.write(rowcount,3, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty'],2) or 0.0
															ws.write(rowcount,4, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,4, 0.0, normal_style_float)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'],2) or 0.0
															ws.write(rowcount,5, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,5, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty'],2) or 0.0
															ws.write(rowcount,6, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,6, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'],2) or 0.0
															ws.write(rowcount,7, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,7, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty'],2) or 0.0
															ws.write(rowcount,8, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,8, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'],2) or 0.0
															ws.write(rowcount,9, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,9, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty'],2) or 0.0
															ws.write(rowcount,10, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,10, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'],2) or 0.0
															ws.write(rowcount,11, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,11, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty'],2) or 0.0
															ws.write(rowcount,12, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,12, "", normal_style)
														try:	
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'],2) or 0.0
															ws.write(rowcount,13, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,13, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty'],2) or 0.0
															ws.write(rowcount,14, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,14, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'],2) or 0.0
															ws.write(rowcount,15, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,15, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty'],2) or 0.0
															ws.write(rowcount,16, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,16, 0.0, normal_style_float)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'],2) or 0.0
															ws.write(rowcount,17, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,17, "", normal_style)
														rowcount+=1

														if bl==current_blend or current_blend==False:
															total_blend.update({
																1:total_blend[1]+(opening_kg or 0.0),
																2:total_blend[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_blend[3]+(incoming_kg or 0.0),
																4:total_blend[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_blend[5]+(in_return_kg or 0.0),
																6:total_blend[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_blend[7]+(outgoing_kg or 0.0),
																8:total_blend[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_blend[9]+(out_return_kg or 0.0),
																10:total_blend[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_blend[11]+(issue_kg or 0.0),
																12:total_blend[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_blend[13]+(closing_kg or 0.0),
																14:total_blend[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_blend=bl
														if location.id==current_location or current_location==False:
															total_location.update({
																1:total_location[1]+(opening_kg or 0.0),
																2:total_location[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_location[3]+(incoming_kg or 0.0),
																4:total_location[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_location[5]+(in_return_kg or 0.0),
																6:total_location[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_location[7]+(outgoing_kg or 0.0),
																8:total_location[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_location[9]+(out_return_kg or 0.0),
																10:total_location[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_location[11]+(issue_kg or 0.0),
																12:total_location[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_location[13]+(closing_kg or 0.0),
																14:total_location[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_location=location.id
														# print "===============================",total_wax
														if parent_loc==current_parent or current_parent==False:
															total_parent.update({
																1:total_parent[1]+(opening_kg or 0.0),
																2:total_parent[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_parent[3]+(incoming_kg or 0.0),
																4:total_parent[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_parent[5]+(in_return_kg or 0.0),
																6:total_parent[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_parent[7]+(outgoing_kg or 0.0),
																8:total_parent[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_parent[9]+(out_return_kg or 0.0),
																10:total_parent[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_parent[11]+(issue_kg or 0.0),
																12:total_parent[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_parent[13]+(closing_kg or 0.0),
																14:total_parent[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_parent=parent_loc
									elif inventory_type.code == 'Raw Material':
										for pl in stock_lines[parent_loc][location.id][bl]:
											# print "pl===========",pl,stock_lines[parent_loc][location.id][bl][ct][sd]
											for tl in stock_lines[parent_loc][location.id][bl][pl]:
												# print "tl===========",stock_lines[parent_loc][location.id][bl][ct][sd]
												for uop_l in stock_lines[parent_loc][location.id][bl][pl][tl]:
													# inisialisasi quantity kg
													try:
														opening_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty']
													except:
														opening_kg = 0
													try:
														incoming_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty']
													except:
														incoming_kg = 0
													try:
														in_return_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty']
													except:
														in_return_kg = 0
													try:
														outgoing_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty']
													except:
														outgoing_kg = 0
													try:
														out_return_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty']
													except:
														out_return_kg = 0
													try:
														issue_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty']
													except:
														issue_kg = 0
													try:
														closing_kg = stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty']
													except:
														closing_kg = 0
													# jika semua nilai opening sampai closing dibawah 1 kg, dihilangkan saja
													if opening_kg<0.01 and opening_kg>-0.01 and incoming_kg<0.01 and incoming_kg>-0.01 and in_return_kg<0.01 and in_return_kg>-0.01 and outgoing_kg<0.01 and outgoing_kg>-0.01 and out_return_kg<0.01 and out_return_kg>-0.01 and issue_kg<0.01 and issue_kg>-0.01 and closing_kg<0.01 and closing_kg>-0.01:
														continue
													# if False:
													# 	continue
													else:
														ws.write(rowcount,0, prods[pl]['code'], normal_style)
														ws.write(rowcount,1, prods[pl]['name'], normal_style)
														if len(prods[pl]['name'])>max_length_prod_name:
															max_length_prod_name=len(prods[pl]['name'])

														if len(prods[pl]['code'])>max_length_prod_code:
															max_length_prod_code=len(prods[pl]['code'])
														# print "==============", uop_l, uoms[uop_l]
														if uoms.get(uop_l,False) and len(uoms[uop_l]['name'])>max_length_uom_name:
															max_length_uom_name=len(uoms[uop_l]['name'])
														if tl != 0:
															ws.write(rowcount,2, trackings[tl]['name'], normal_style)
														else:
															ws.write(rowcount,2, "Undef.Lot", normal_style)
														if uop_l != 0:
															ws.write(rowcount,3, uoms[uop_l]['name'], normal_style)
														else:
															ws.write(rowcount,3, " ", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty'],2) or 0.0
															ws.write(rowcount,4, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,4, 0.0, normal_style_float)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'],2) or 0.0
															ws.write(rowcount,5, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,5, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty'],2) or 0.0
															ws.write(rowcount,6, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,6, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'],2) or 0.0
															ws.write(rowcount,7, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,7, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty'],2) or 0.0
															ws.write(rowcount,8, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,8, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'],2) or 0.0
															ws.write(rowcount,9, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,9, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty'],2) or 0.0
															ws.write(rowcount,10, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,10, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'],2) or 0.0
															ws.write(rowcount,11, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,11, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty'],2) or 0.0
															ws.write(rowcount,12, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,12, "", normal_style)
														try:	
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'],2) or 0.0
															ws.write(rowcount,13, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,13, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty'],2) or 0.0
															ws.write(rowcount,14, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,14, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'],2) or 0.0
															ws.write(rowcount,15, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,15, "", normal_style)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty'],2) or 0.0
															ws.write(rowcount,16, stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty'], normal_style_float)
														except:
															ws.write(rowcount,16, 0.0, normal_style_float)
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'],2) or 0.0
															ws.write(rowcount,17, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,17, "", normal_style)
														### avg 20161001
														try:
															rounder=round(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty']/stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'],2) or 0.0
															ws.write(rowcount,18, rounder !=0.0 and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uom_qty']/stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or "", normal_style_float_round)
														except:
															ws.write(rowcount,18, "", normal_style)
														rowcount+=1

														if bl==current_blend or current_blend==False:
															total_blend.update({
																1:total_blend[1]+(opening_kg or 0.0),
																2:total_blend[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_blend[3]+(incoming_kg or 0.0),
																4:total_blend[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_blend[5]+(in_return_kg or 0.0),
																6:total_blend[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_blend[7]+(outgoing_kg or 0.0),
																8:total_blend[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_blend[9]+(out_return_kg or 0.0),
																10:total_blend[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_blend[11]+(issue_kg or 0.0),
																12:total_blend[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_blend[13]+(closing_kg or 0.0),
																14:total_blend[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_blend=bl
														if location.id==current_location or current_location==False:
															total_location.update({
																1:total_location[1]+(opening_kg or 0.0),
																2:total_location[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_location[3]+(incoming_kg or 0.0),
																4:total_location[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_location[5]+(in_return_kg or 0.0),
																6:total_location[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_location[7]+(outgoing_kg or 0.0),
																8:total_location[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_location[9]+(out_return_kg or 0.0),
																10:total_location[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_location[11]+(issue_kg or 0.0),
																12:total_location[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_location[13]+(closing_kg or 0.0),
																14:total_location[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_location=location.id
														# print "===============================",total_wax
														if parent_loc==current_parent or current_parent==False:
															total_parent.update({
																1:total_parent[1]+(opening_kg or 0.0),
																2:total_parent[2]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('opening',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['opening']['uop_qty'] or 0.0),
																3:total_parent[3]+(incoming_kg or 0.0),
																4:total_parent[4]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('incoming',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['incoming']['uop_qty'] or 0.0),
																5:total_parent[5]+(in_return_kg or 0.0),
																6:total_parent[6]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('in_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['in_return']['uop_qty'] or 0.0),
																7:total_parent[7]+(outgoing_kg or 0.0),
																8:total_parent[8]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('outgoing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['outgoing']['uop_qty'] or 0.0),
																9:total_parent[9]+(out_return_kg or 0.0),
																10:total_parent[10]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('out_return',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['out_return']['uop_qty'] or 0.0),
																11:total_parent[11]+(issue_kg or 0.0),
																12:total_parent[12]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('issue',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['issue']['uop_qty'] or 0.0),
																13:total_parent[13]+(closing_kg or 0.0),
																14:total_parent[14]+(stock_lines[parent_loc][location.id][bl][pl][tl][uop_l].get('closing',False) and stock_lines[parent_loc][location.id][bl][pl][tl][uop_l]['closing']['uop_qty'] or 0.0),
																})
															current_parent=parent_loc
									# print "============================",rowcount
									# cek_total_blend = False
									cek_total_blend = True
									for i in range(1,15):
										cek_total_blend = cek_total_blend and (total_blend[i]==0)
									if not cek_total_blend:
										ws.write_merge(rowcount,rowcount,1,3,"Total Blend: %s"%bl,subtotal_title_style)
										ws.write(rowcount,4,total_blend[1]!=0.0 and total_blend[1] or '',subtotal_style2)
										ws.write(rowcount,5,total_blend[2]!=0.0 and total_blend[2] or '',subtotal_style)
										ws.write(rowcount,6,total_blend[3]!=0.0 and total_blend[3] or '',subtotal_style2)
										ws.write(rowcount,7,total_blend[4]!=0.0 and total_blend[4] or '',subtotal_style)
										ws.write(rowcount,8,total_blend[5]!=0.0 and total_blend[5] or '',subtotal_style2)
										ws.write(rowcount,9,total_blend[6]!=0.0 and total_blend[6] or '',subtotal_style)
										ws.write(rowcount,10,total_blend[7]!=0.0 and total_blend[7] or '',subtotal_style2)
										ws.write(rowcount,11,total_blend[8]!=0.0 and total_blend[8] or '',subtotal_style)
										ws.write(rowcount,12,total_blend[9]!=0.0 and total_blend[9] or '',subtotal_style2)
										ws.write(rowcount,13,total_blend[10]!=0.0 and total_blend[10] or '',subtotal_style)
										ws.write(rowcount,14,total_blend[11]!=0.0 and total_blend[11] or '',subtotal_style2)
										ws.write(rowcount,15,total_blend[12]!=0.0 and total_blend[12] or '',subtotal_style)
										ws.write(rowcount,16,total_blend[13]!=0.0 and total_blend[13] or '',subtotal_style2)
										ws.write(rowcount,17,total_blend[14]!=0.0 and total_blend[14] or '',subtotal_style)
										ws.write(rowcount,18,'',subtotal_style)
										rowcount+=1
									current_blend=False
									for i in range(1,15):
										total_blend[i]=0.0

								# print "============================",rowcount
								ws.write_merge(rowcount,rowcount,1,3,"Total Location: %s"%location.name,subtotal_title_style)
								ws.write(rowcount,4,total_location[1]!=0.0 and total_location[1] or '',subtotal_style2)
								ws.write(rowcount,5,total_location[2]!=0.0 and total_location[2] or '',subtotal_style)
								ws.write(rowcount,6,total_location[3]!=0.0 and total_location[3] or '',subtotal_style2)
								ws.write(rowcount,7,total_location[4]!=0.0 and total_location[4] or '',subtotal_style)
								ws.write(rowcount,8,total_location[5]!=0.0 and total_location[5] or '',subtotal_style2)
								ws.write(rowcount,9,total_location[6]!=0.0 and total_location[6] or '',subtotal_style)
								ws.write(rowcount,10,total_location[7]!=0.0 and total_location[7] or '',subtotal_style2)
								ws.write(rowcount,11,total_location[8]!=0.0 and total_location[8] or '',subtotal_style)
								ws.write(rowcount,12,total_location[9]!=0.0 and total_location[9] or '',subtotal_style2)
								ws.write(rowcount,13,total_location[10]!=0.0 and total_location[10] or '',subtotal_style)
								ws.write(rowcount,14,total_location[11]!=0.0 and total_location[11] or '',subtotal_style2)
								ws.write(rowcount,15,total_location[12]!=0.0 and total_location[12] or '',subtotal_style)
								ws.write(rowcount,16,total_location[13]!=0.0 and total_location[13] or '',subtotal_style2)
								ws.write(rowcount,17,total_location[14]!=0.0 and total_location[14] or '',subtotal_style)
								ws.write(rowcount,18,'',subtotal_style)
								rowcount+=1
								# print "============================",rowcount
								current_location=False
								for i in range(1,15):
									grand_total[i]+=total_location[i]

								for i in range(1,15):
									total_location[i]=0.0


					ws.write_merge(rowcount,rowcount,1,3,"Total Parent Location: %s"%parent_loc,subtotal_title_style)
					ws.write(rowcount,4,total_parent[1]!=0.0 and total_parent[1] or '',subtotal_style2)
					ws.write(rowcount,5,total_parent[2]!=0.0 and total_parent[2] or '',subtotal_style)
					ws.write(rowcount,6,total_parent[3]!=0.0 and total_parent[3] or '',subtotal_style2)
					ws.write(rowcount,7,total_parent[4]!=0.0 and total_parent[4] or '',subtotal_style)
					ws.write(rowcount,8,total_parent[5]!=0.0 and total_parent[5] or '',subtotal_style2)
					ws.write(rowcount,9,total_parent[6]!=0.0 and total_parent[6] or '',subtotal_style)
					ws.write(rowcount,10,total_parent[7]!=0.0 and total_parent[7] or '',subtotal_style2)
					ws.write(rowcount,11,total_parent[8]!=0.0 and total_parent[8] or '',subtotal_style)
					ws.write(rowcount,12,total_parent[9]!=0.0 and total_parent[9] or '',subtotal_style2)
					ws.write(rowcount,13,total_parent[10]!=0.0 and total_parent[10] or '',subtotal_style)
					ws.write(rowcount,14,total_parent[11]!=0.0 and total_parent[11] or '',subtotal_style2)
					ws.write(rowcount,15,total_parent[12]!=0.0 and total_parent[12] or '',subtotal_style)
					ws.write(rowcount,16,total_parent[13]!=0.0 and total_parent[13] or '',subtotal_style2)
					ws.write(rowcount,17,total_parent[14]!=0.0 and total_parent[14] or '',subtotal_style)
					ws.write(rowcount,18,'',subtotal_style)
					rowcount+=1
					# print "============================",rowcount
					current_parent=False
					for i in range(1,15):
						total_parent[i]=0.0


							# ws.write(rowcount,17, "xxxxx", normal_style)
						##########################################
				# print "============================",rowcount
			ws.write_merge(rowcount,rowcount,1,3,"Grand Total:",subtotal_title_style)
			ws.write(rowcount,4,grand_total[1]!=0.0 and grand_total[1] or '',subtotal_style2)
			ws.write(rowcount,5,grand_total[2]!=0.0 and grand_total[2] or '',subtotal_style)
			ws.write(rowcount,6,grand_total[3]!=0.0 and grand_total[3] or '',subtotal_style2)
			ws.write(rowcount,7,grand_total[4]!=0.0 and grand_total[4] or '',subtotal_style)
			ws.write(rowcount,8,grand_total[5]!=0.0 and grand_total[5] or '',subtotal_style2)
			ws.write(rowcount,9,grand_total[6]!=0.0 and grand_total[6] or '',subtotal_style)
			ws.write(rowcount,10,grand_total[7]!=0.0 and grand_total[7] or '',subtotal_style2)
			ws.write(rowcount,11,grand_total[8]!=0.0 and grand_total[8] or '',subtotal_style)
			ws.write(rowcount,12,grand_total[9]!=0.0 and grand_total[9] or '',subtotal_style2)
			ws.write(rowcount,13,grand_total[10]!=0.0 and grand_total[10] or '',subtotal_style)
			ws.write(rowcount,14,grand_total[11]!=0.0 and grand_total[11] or '',subtotal_style2)
			ws.write(rowcount,15,grand_total[12]!=0.0 and grand_total[12] or '',subtotal_style)
			ws.write(rowcount,16,grand_total[13]!=0.0 and grand_total[13] or '',subtotal_style2)
			ws.write(rowcount,17,grand_total[14]!=0.0 and grand_total[14] or '',subtotal_style)
			ws.write(rowcount,18,'',subtotal_style)
			rowcount+=1
			# print "*************************",max_length_prod_code
			ws.col(0).width = 256*int(max_length_prod_code)>=2304 and 256*int(max_length_prod_code) or 2560
			ws.col(1).width = 256*int(max_length_prod_name)>=2304 and 256*int(max_length_prod_name) or 2560
			ws.col(3).width = 256*int(max_length_uom_name)>=2304 and 256*int(max_length_uom_name) or 2560
			for i in range(1,15):
				# print "grand_total %s %s"%(i,len(str(round(grand_total[i],4))))
				ws.col(3+i).width = 256*len(str(round(grand_total[i],4)))>=2304 and 256*len(str(round(grand_total[i],4))) or 2560
		pass
#from netsvc import Service
#del Service._services['report.stock.report.bitratex']
stock_report_xls('report.stock.report.bitratex','stock.report.bitratex.wizard', 'addons/ad_stock_report/report/stock_report.mako',
						parser=ReportStockBitra)