<html>
<head>
	<style type="text/css">
		.fontall{	
				font-family: Arial;
				font-size:10px;
		}
		
		.border1 {
				border:0px solid;
				margin:0 0px 0 0px;
				/*width:1300px;*/
		}
		.jdltbl{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
		}
		.jdltbltop{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				border-bottom: 1px dotted #808080;
		}
		.jdltbl2{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				padding-left: 7px;
		}
		.isitblfill{
				text-align: left;
				/*border-bottom: 1px solid #808080;*/
		}
		.isitbl{
				text-align: left;
		}
		.isitblknn{
				text-align: right;
		}
		.isitblknnspn{
				text-align: right;
				/*width:30px;*/
				/*background-color:yellow;*/
		}
		td {
		vertical-align:top;
		}
		.bwhtbl{text-transform: uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}
		.sumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
		}
		.bwhsumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		.lbl{
			font-family: "Arial";
			font-size:10px;
			font-weight: bold;
			padding:0px 10px 0px 20px;
			vertical-align: top;
			text-transform:uppercase;
		}
		.lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		.tdtxt{
			font-size:11px;
			padding:0px 20px 0px 10px;
		}
		.borderwhite{
			border-top:white;
			border-left:white;
		}
		.borderwhite_rgt{
			border-right:white;
			padding-left: 3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.borderwhite_rgtbtm{
			border-right:white;
			border-bottom:white;
			padding-left: 3px;	
		}
		.borderwhite_btm{
			border-bottom:white;
			padding-right:3px;
		}
		.borderwhite_btmbig{
			border-bottom:white;
			font-size:14px;
			font-weight:bold;
			padding-right:3px;
		}
		.lblrght{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.lblrghtbig{
			padding-right:3px;
			font-size:14px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.lbl2{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			text-align: center;
		}
		.borderwhite_rgt2{
			border-right:white;
			text-align: center;
			font-weight:bold;
			text-transform: uppercase;
		}
		.borderwhite_btm2{
			border-bottom:white;
			text-align: center;
			font-weight:bold;
		}
		.borderwhite_rgtbtm2{
			border-right:white;
			border-bottom:white;
			text-align: center;
		}
		.grsbwhtbl{
			border-bottom: 1px solid #808080;
		}
		.jdltblknn{
				text-transform: uppercase;
				text-align: right;
				font-family: Arial;
				font-weight: bold;
		}
		.jdltblpd7{
				text-transform: uppercase;
				padding-left:7px;
				font-family: Arial;
				font-weight: bold;

		}
		.isitblpd7{
				padding-left: 7px;
		}
		.hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
		text-transform: uppercase;
}
		.font-capitalize{
		text-transform:capitalize;
		}
	/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        }
        .wrapper {
        min-height:100%;
        position:static;
        font-family: Arial;
		font-size:10px;
        }
        .header {
        padding:10px;
        background:#5ee;
        }
        .content {
        padding:10px;
        width:100%;
        padding-bottom:60px; /* Height of the footer element */ 
        /*background:green;*/
        /*height:910px;*/
        }
        .footer {
        width:100%;
        height:60px;
        position:absolute;
        bottom:0;
        left:0;
        /*background:#ee5;*/
        }
        

		h2 {
			font-family: Arial;
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
			page-break-before: always;
		}
	</style>
</head>
<%from operator import itemgetter, attrgetter, methodcaller%>
<%print_user_time=get_print_user_time()%>
%for o in objects:
	<%sale_type = get_sale_type(o)%>
	<%uom_base_name = get_uom_base(sale_type)%>
	%for unit in get_unit_group(o):
		<%retval = set_curr_unit(unit[0])%>
<body>
		<h2>
			<div class="hdr1">
				<a style="border-bottom:1px solid;">Stuffing Memo</a> <br/>
			</div>
		</h2>
		<div class="wrapper">
			<div class="content">
				<table width="100%" cellspacing="0" cellpadding="2">
					<tr>
						<td width="70%" style="vertical-align:top;">
							<table cellspacing="0" cellpadding="2">
								<tr>
									<td  style="vertical-align:top;"><span class="lbl1">FROM</span><br/>
										<span style="text-transform:uppercase;"> MARKETING<br/>SEMARANG</span></td>
								</tr>
							</table>
							<table>
								<tr>
									<td style="vertical-align:top;"><span class="lbl1">TO </span><br/>
										<span style="text-transform:uppercase;"> ${unit[0].upper()} </span>
									</td>
								</tr>
							</table>
							<table>
								<tr>
									<td style="vertical-align:top;"><span class="lbl1">CC</span><br/>
									<span style="text-transform:uppercase;">
									%if o.pic_id_1 and o.pic_id_1.name:
										${(o.pic_id_1 and o.pic_id_1.name or '').upper()}<br/>
									%endif
									%if o.pic_id_2 and o.pic_id_2.name:
										${(o.pic_id_2 and o.pic_id_2.name or '').upper()}<br/>
									%endif
									</span>
									</td>
								</tr>
							</table>
						</td>
						<td width="30%">
							<table class="borderwhite"  width="100%"  rules="all">
								<tr>
									<td class="lblrght" width="60%" >STUFFING MEMO NO.</td><td class="borderwhite_rgt" width="40%">DATE</td>
								</tr>
								<tr>
									<td class="borderwhite_btm">${o.name or ''}</td><td class="borderwhite_rgtbtm">${o.id and o.creation_date or ''}</td>
								</tr>
							</table>
							<table class="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
								<tr>
									<td class="lblrghtbig" width="100%">STUFFING DATE</td>
								</tr>
								<tr>
									<td class="borderwhite_btmbig">${xdate3month(o.stuffing_date).upper()}</td>
								</tr>
							</table>
							<table class="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
								<tr>
									<td class="lblrghtbig" width="100%">SHIPMENT TYPE</td>
								</tr>
								<tr>
									<td class="borderwhite_btmbig">${get_sale_type(o).upper()}</td>
								</tr>
							</table>
						</td>
					</tr>
				</table>
			</br>
				<table class='border1'  width='100%'  cellspacing="0" cellpadding="2">
					<tr>
						<td width="100%" style="vertical-align:top;">
							<table class='border1'  width='98%'  cellspacing="0" cellpadding="2">
								<tr>
									<td class='jdltbl' width='13%'>SHIPPING</td>
									<td class='jdltbl' width='25%'>&nbsp;</td>
									<td class='jdltbl' width='20%'>&nbsp;</td>
									<td class='jdltblknn' width='10%'>QUANTITY</td>
									<td class='jdltblknn' width='18%'>&nbsp;</td>
									<!-- <td class='jdltbl' width='3%'>&nbsp;</td> -->
									<td class='jdltbl' width='17%'></td>
									<!-- <td class='jdltbl' width='1%'>&nbsp;</td> -->
								</tr>
								<tr>
									<td class='jdltbl' width='13%'>INSTRUCTION</td>
									<td class='jdltbl' width='25%'>CUSTOMER</td>
									<td class='jdltbl' width='20%'>PRODUCT</td>
									<td class='jdltblknn' width='10%'>(${uom_base_name})</td>
									<td class='jdltblknn' width='18%' style="padding-right:5px;">PACKAGES</td>
									<!-- <td class='jdltbl' width='3%'>&nbsp;</td> -->
									<td class='jdltbl' width='17%'>CONTAINER SIZE</td>
									<!-- <td class='jdltbl' width='1%'>&nbsp;</td> -->
								</tr>
								<tr>
									<td class='grsbwhtbl' width='100%' colspan="8"></td>
								</tr>
								<%linecount = 0%>
								# <%goods_lines2=sorted(o.goods_lines, key=attrgetter('priority'), reverse=True)%>
								<%goods_lines2=sorted(o.goods_lines,key=lambda x:(x.picking_id and x.picking_id.container_book_id and x.picking_id.container_book_id.name, x.stock_move_id.sale_line_id.sequence_line))%>
								%for line in goods_lines2:
									<%line_unit = line.manufacturer.name or ''%>
									<%o_unit = o.manufacturer.name or ''%>
									%if line_unit != "":
										<%unit_name = line_unit%>
									%else:
										<%unit_name = o_unit%>
									%endif:
								
									%if unit_name == unit[0]:
										<%linecount = linecount + 1%>
										<%brcount1 = 0%>
										<%brcount2 = 0%>
										<%base_qty = uom_to_base(sale_type,line['product_qty'] or 0.0,line['product_uom'] or False)%>
										<tr>
											<td class='isitbl' style="padding-top:5px;" width='13%'>
												%if line.booking_id and line.booking_id.name:
													<b>${line.booking_id and line.booking_id.name or ''}</b></br>
												%endif
											</td>
											<td class='isitbl' style="padding-top:5px;" width='25%'>
												%if line.partner_id:
													${(line.partner_id.partner_alias and line.partner_id.partner_alias or line.partner_id.name or '').upper()}</br>
													<%brcount1 = brcount1 + 1%>
												%elif line.stock_move_id and line.stock_move_id.picking_id and line.stock_move_id.picking_id.sale_id and line.stock_move_id.picking_id.sale_id.partner_id.partner_alias:
													${(line.stock_move_id and line.stock_move_id.picking_id and line.stock_move_id.picking_id.sale_id and line.stock_move_id.picking_id.sale_id.partner_id.partner_alias or '').upper()}</br>
													<%brcount1 = brcount1 + 1%>
												%elif line.stock_move_id and line.stock_move_id.picking_id and line.stock_move_id.picking_id.sale_id and line.stock_move_id.picking_id.sale_id.partner_id.name:
													${(line.stock_move_id and line.stock_move_id.picking_id and line.stock_move_id.picking_id.sale_id and line.stock_move_id.picking_id.sale_id.partner_id.name or '').upper()}</br>
													<%brcount1 = brcount1 + 1%>
												%endif
												%if line.stock_move_id and line.stock_move_id.sale_line_id:
													SC No.: ${(line.stock_move_id.sale_line_id.sequence_line or '').upper()}</br>
													<%brcount1 = brcount1 + 1%>
												%endif
												%if line.remark:
													Remark : ${line.remark.replace('\n','<br/>') or ''}
												%endif
											</td>
											<td class='isitbl' style="padding-top:5px;" width='20%'>
												%if line.product_id and line.product_id.name:
													${(line.product_id and line.product_id.name or '').upper()}</br>
													<%brcount2 = brcount2 + 1%>
												%endif
												%if (line.tracking_id and line.tracking_id.name) or (line.product_id and line.product_id.count):
													%if line.tracking_id and line.tracking_id.name:
														LOT: ${(line.tracking_id.name or '').upper()}
													%endif
													&nbsp;&nbsp;
													</br>
													<%brcount2 = brcount2 + 1%>
												%endif

												%if line.picking_id and line.picking_id.lc_ids and line.picking_id.lc_ids[0].lc_number:
													L/C No.: ${(line.picking_id and line.picking_id.lc_ids and line.picking_id.lc_ids[0].lc_number or '').upper()}</br>
													<%brcount2 = brcount2 + 1%>
												%endif
											</td>
											<td class='isitblknn' width='10%' style="padding-top:5px;">
												${formatLang(base_qty or 0.0,digits=3)}
											</td> 
											<td class='isitblknn' width='18%' style="padding-top:5px;padding-right:3px;vertical-align:top;">
												<table width="100%">
													<tr>
														<td class='isitblknn' width="50%">${formatLang(line.product_uop_qty or 0.0,digits=0)}</td>
														<td class='isitblknn' width="2%"></td>
														<td class='isitbl' width="48%">
															%if line.product_uop and line.product_uop.packing_type:
																${(line.product_uop and line.product_uop.packing_type.name or '').upper()}
															%elif line.product_uop and line.product_uop.name:
																${(line.product_uop and line.product_uop.name or '').upper()}
															%endif
														</td>
													</tr>
												</table>
											</td>
											<!-- <td class='isitbl' width='3%' style="padding-top:5px;"></br></td> -->
											<td class='isitblfill' width='17%' style="padding-top:5px;">\
											
    										${line.container_size and line.container_size.name or ''}<br/>
											%if line.stock_move_id and line.stock_move_id.picking_id and line.stock_move_id.picking_id.container_book_id and line.stock_move_id.picking_id.container_book_id.port_to_desc:
												Destination: ${(line.stock_move_id.picking_id.container_book_id.port_to_desc or '').upper()}</br>
											%elif line.dest_port_id and line.dest_port_id.country and line.dest_port_id.country.name:
												Destination: ${(line.dest_port_id and line.dest_port_id.name or '').upper()}</br>
											%endif
											</td>
											<!-- <td class='isitbl' width='1%' style="padding-top:5px;"></br></td> -->
										</tr>
										<tr>
											<td class='isitbl' width='100%' style="padding-top:0px;" colspan="8"></td>
										</tr>
									%endif:
								%endfor
								<tr>
									<td class='grsbwhtbl' width='100%' colspan="8"></td>
								</tr>
								<tr>
									<td class='isitbl' width='100%' style="padding-top:5px;" colspan='9'>
										<b>PLEASE MAKE NECESSARY ARRANGEMENTS AT YOUR END AND SEND BACK THE MEMO TO US WITH APPROVAL</b>
									</td>
								</tr>
								<tr>
									<td class='isitbl' width='100%' style="padding-top:5px;" colspan='9'>
										% if o.note:
											<b>Note : </b><br/>
											${o.note.replace('\n','<br/>')}
										% endif
									</td>
								</tr>
							</table>
						</td>
					</tr>
				</table>
				</br>
				<div style="vertical-align:top;">
					<table width='100%'  cellspacing="0" cellpadding="2">
						<tr>
							<td width="100%" style="vertical-align:top;">
								<table width='100%'  cellspacing="0" cellpadding="2">
									<tr>
										<td width='100%'>
											<a style="vertical-align:top;">
											 </a>
										</td>				
									</tr>
								</table>
							</td>
						</tr>
					</table>
				</div>					
			</div>
			<div class="footer">			
				<table width='100%'>
					<tr width='100%'>
						<td width='9%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							<b>(${get_curr_unit().upper()})</b>
						</td>
						<td width='8%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							<b>(${get_curr_unit().upper()})</b>
						</td>
						<td width='8%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							<b>(MKT-SMG)</b>
						</td>
						<td width='8%'>
						</td>
					</tr>
					<tr width='100%'>
						<td>
						</td>
						<td Style="border-bottom:1pt solid #808080;">
						</td>
						<td>
						</td>
						<td Style="border-bottom:1pt solid #808080;">
						</td>
						<td>
						</td>
						<td Style="border-bottom:1pt solid #808080;">
						</td>
						<td>
						</td>
					</tr>
					<tr width='100%'>
						<td width='9%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							Stuffing Supervisor
						</td>
						<td width='8%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							Authorized By
						</td>
						<td width='8%'>
						</td>
						<td class="fontall" width='25%' align='center'>
							Authorized Signatory
						</td>
						<td width='8%'>
						</td>
					</tr>
				</table>
			</div>
		</div>
</body>
	%endfor
%endfor
</html>	
