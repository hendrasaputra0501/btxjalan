<html>
<head>
	<style type="text/css">
		.border1 {
				border:0px solid;
				margin:0 0px 0 0px;
				/*width:1300px;*/
		}
		.jdltbl{
				text-transform: uppercase;
				/*text-align: center;*/
				font-weight: bold;
		}
		.isitbl{
				text-align: left;
		}
		.isitblknn{
				text-align: right;
		}
		/*.bwhtbl{text-transform: uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}*/
		/*.sumtbl{text-transform:uppercase;
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
		}*/
		/*.lbl{
			font-family: "Arial";
			font-size:10px;
			font-weight: bold;
			padding:0px 10px 0px 20px;
			vertical-align: top;
			text-transform:uppercase;
		}*/
		.lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		/*.tdtxt{
			font-size:11px;
			padding:0px 20px 0px 10px;
		}*/
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
		.lblrght{
			padding-right:3px;
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
			font-family: Arial;
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
		}
		.font-capitalize{
		text-transform:capitalize;
		}
	/*footer*/
		html, body {
        margin:0;
        padding:0;
        /*page-break-inside: auto;*/
        }
        .wrapper{
		width:100%;
        page-break-inside: auto;
        }
		.header {
        padding:10px;
        background:#5ee;
        }
        .content {
        width:100%;
        /*padding-bottom:0px;  Height of the footer element  */
        /*height:910px;*/
        }
        table{
			width:100%;
			page-break-inside: auto;
		}
		tr{
			page-break-inside: avoid;
			page-break-before: auto;
		}
		td {
		vertical-align:top;
        font-size: 10px;
		}
        /*.footer {
        width:100%;
        height:0px;
        position:absolute;
        bottom:0;
        left:0;
        }*/
        
		h2 {
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
			page-break-before: always;
		}
	</style>
</head>
%for o in objects:
	%for unit in get_unit_group(o):
		<body>
			<h2>
				<div class="hdr1">
					<a style="border-bottom:1px solid;">Production Memo</a> <br/>
				</div>
			</h2>
			<div class="wrapper">
				<div class="content">
					<table width="100%" cellspacing="0" cellpadding="2">
						<tr>
							<td width="70%" style="vertical-align:top;">
								<table cellspacing="0" cellpadding="2">
									<tr>
										<td ><span class="lbl1" style="vertical-align:top;">TO</span><br/>
										<span>${unit[0].upper()}</span>
										</td>
									</tr>
								</table>
								<table>
									<tr>
										<td><span class="lbl1" style="vertical-align:top;">TYPE </span><br/>
											<span style="vertical-align:top;">NEW ORDER / REVISION</span>
										</td>
									</tr>
								</table>
								<table>
									<tr>
										<td><span  class="lbl1" style="vertical-align:top;">CUSTOMER</span><br/>
											<span style="vertical-align:top;">
												%if o.sale_id and o.sale_id.partner_id and o.sale_id.partner_id.name:
													${(o.sale_id and o.sale_id.partner_id and o.sale_id.partner_id.name or '').upper()}<br/>
												%endif
												%if o.sale_id and o.sale_id.partner_id and o.sale_id.partner_id.country_id and o.sale_id.partner_id.country_id.name:
													${(o.sale_id and o.sale_id.partner_id and o.sale_id.partner_id.country_id and o.sale_id.partner_id.country_id.name or '').upper()}
												%endif
											</span>
										</td>
									</tr>
								</table>
							</td>
							<td width="30%">
								<table class="borderwhite"  width="100%"  rules="all">
									<tr>
										<td class="lblrght" width="60%" >MEMO NO.</td><td class="borderwhite_rgt" width="40%">Date</td>
									</tr>
									<tr>
										<td class="borderwhite_btm">${o.id and o.name or ''}</td><td class="borderwhite_rgtbtm">${o.id and o.date_instruction or ''}</td>
									</tr>
								</table>
								<table class="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
									<tr>
										<td class="lblrght" width="60%" >SC NO.</td><td class="borderwhite_rgt" width="40%">Date</td>
									</tr>
									<tr>
										<td class="borderwhite_btm">${o.sale_id and o.sale_id.name or ''}</td><td class="borderwhite_rgtbtm">${o.sale_id and o.sale_id.date_order or ''}</td>
									</tr>
								</table>
								<br/>
							</td>
						</tr>
					</table>
					<br/>
					<table class='border1'  width='100%'  cellspacing="0" cellpadding="2">
						<tr width='100%'>
							<td width="100%" style="vertical-align:top;">
								<table class='border1'  width='100%'  cellspacing="0" cellpadding="2">
									<tr>
										<td class='jdltbl' width='15%'>DELIVERY NO.</td>
										<td class='jdltbl' width='40%'>Product</td>
										<td class='jdltbl' width='5%'>UOM</td>
										<td class='jdltblknn' width='13%'>Quantity</td>
										<!-- <td class='jdltblknn' width='3%'></td> -->
										<td class='jdltbl' width='27%' style="padding-left:3px;">Remarks</td>
									</tr>
									<tr>
										<td class='grsbwhtbl' width='100%' colspan="5"></td>
									</tr>
									<%linecount = 0%>
									%for line in o.goods_lines:
										<%line_unit = line.manufacturer.name or ''%>
										<%o_unit = o.manufacturer.name or ''%>
										%if line_unit != "":
											<%unit_name = line_unit%>
										%else:
											<%unit_name = o_unit%>
										%endif:
									
										%if unit_name == unit[0]:
											<%linecount = linecount + 1%>
											<tr >
												<td class='isitbl' style="padding-top:5px;">
													%if line.sequence_line:
														${line.sequence_line or ''}</br>
													%endif:
												</td>
												<td class='isitbl' style="padding-top:5px;">
													<%order_line = get_order_line(o.sale_id.id,line.sequence_line,line.product_id.id)%>
													%if line.name:
														${(line.name or '').upper()}</br>
													%endif:
													
													%if line.product_id and line.product_id.blend_code and line.product_id.blend_code.desc:
														${line.product_id.blend_code.desc or ''}<br/>
													%endif

													%if line.cone_weight:
														Cone Weight: ${formatLang(line.cone_weight or 0,digits=3)} Kg(s)</br>
													%else:
														Cone Weight: Standard</br>
													%endif:
													%if line.tpi:
														TPI: ${line.tpi or ''}</br>
													%endif

													%if line.tpm:
														TPM: ${line.tpm or ''}</br>
													%endif

													%if line.sale_line_id:
														Packing : ${line.sale_line_id.packing_type.name} <br/>
													%elif order_line and order_line.packing_type:
														Packing : ${order_line.packing_type.name} <br/>
													%endif

													% if line.sale_line_id:
														Packing Details : ${line.sale_line_id.packing_detail or ''}</br>
													%elif order_line:
														Packing Details : ${order_line.packing_detail or ''}</br>
													%elif line.memo_id and line.memo_id.sale_id and line.memo_id.sale_id.order_line:
														% for sol in line.memo_id.sale_id.order_line:
															% if sol.sequence_line == line.sequence_line:
																Packing Details : ${sol.packing_detail or ''}</br>
															% endif
														% endfor
													%endif

													%if line.sale_line_id and line.sale_line_id.container_size:
														Container Size: ${line.sale_line_id.container_size and line.sale_line_id.container_size.name or ''}</br>
													%elif order_line and order_line.container_size and order_line.container_size.name:
														Container Size: ${order_line.container_size and order_line.container_size.name or ''}</br>
													%endif:
													%if line.est_delivery_date:
														<b>Last Shipment Date: ${line.est_delivery_date or ''}</b>
													%endif:
												</td>
												<td class='isitbl' width='5%' style="padding-top:5px;" >
												% if o.sale_id and o.sale_id.sale_type=='export':
													KGS
												% else:
													${line.uom_id.name or ''}
													%if line.uom_id.name !="KGS":
														</br>KGS
													%endif
												% endif
												</td>
												<td class='isitblknn' style="padding-top:5px;">
													% if o.sale_id and o.sale_id.sale_type=='export': 
														%if line.uom_id.name =="LBS":
															${formatLang(line.product_uom_qty/2.2046,digits=2)}
														%elif line.uom_id.name=="BALES":
															${formatLang(line.product_uom_qty*(400/2.2046),digits=4)}
														%else:
															${formatLang(line.product_uom_qty,digits=2)}
														%endif
													% else:
														${formatLang(line.product_uom_qty,digits=2)}
														%if line.uom_id.name !="KGS":
															</br>
															%if line.uom_id.name =="LBS":
																(${formatLang(line.product_uom_qty/2.2046,digits=2)})
															%elif line.uom_id.name=="BALES":
																(${formatLang(line.product_uom_qty*(400/2.2046),digits=4)})
															%endif
														%endif
													% endif	
												</td>
												<!-- <td class='isitblknn' width='13%' style="padding-top:5px;">
													${formatLang(line.product_uom_qty,digits=4)}
													%if line.uom_id.name =="LBS":
													</br>${formatLang(line.product_uom_qty/2.2046,digits=4)}
													%elif line.uom_id.name=="BALES":
													</br>${formatLang(line.product_uom_qty*(400/2.2046),digits=4)}
													%endif:
												</td> -->
												<!-- <td class='isitblknn' width='3%' style="padding-top:5px;">
												</td> -->
												<td class='isitbl' style="padding:5px 0 0 3px;">
													${line.remarks or ''}
												</td>
											</tr>
										%endif:
									%endfor
									<tr>
										<td class='grsbwhtbl' width='100%' colspan="5"></td>
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
												%if o.note:	
													<a style="vertical-align:top;"><b class="jdltbl">Remarks :</b></br>
													 ${o.note.replace('\n','<br/>')} </a>
												%endif
											</td>				
										</tr>
									</table>
								</td>
							</tr>
						</table>
					</div>					
				</div>
				<div class="footer">			
				</div>
			</div>
		</body>
	%endfor
%endfor
</html>	
