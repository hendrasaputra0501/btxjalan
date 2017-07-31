<html>
<head>
	<style type='text/css'>
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
		.jdltbl2{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				padding-left: 7px;
		}
		.isitbl{
				text-align: left;
		}
		.isitblknn{
				text-align: right;
		}
		td {
		vertical-align:top;
		}
		.bwhtbl{text-transform: uppercase;
				font-family: 'Arial';
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}
		.sumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:10px;
				font-weight: bold;
				text-align: right;
		}
		.sumtbltot{text-transform:uppercase;
				font-family: 'Arial';
				font-size:10px;
				font-weight: bold;
				text-align: right;
				border-top: 1pt solid #808080;
		}
		.bwhsumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		.lbl{
			font-family: 'Arial';
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
		#lbl2{
		font-family:Arial;
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		padding-left:5px;
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
		.lblrght{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.lblbtm{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
			border-bottom: 1px solid #808080;
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
		#txt1{
		text-align: center;
		padding-left:5px;
}
#borderwhite{
		border-top:white;
		border-left:white;
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
        /*padding:10px;*/
        /*width:100%;*/
        /*padding-bottom:150px;  Height of the footer element  */
        padding-bottom:10px;
        /*background:green;*/
        /*height:910px;*/
        }
        .footer {
        width:100%;
        height:115px;
        position:absolute;
        bottom:0;
        left:0;
        /*background:#ee5;*/
        }
        .break1{
		position:relative;
		display: block;
		/*background:red;*/
		}
 		.break2{
 		/*background: yellow;*/
 		bottom:60;
 		height:90px;
 		}

        
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
<body>
		<h2>
			<div class='hdr1'>
				<a style='border-bottom:1px solid;'>Request For Quotation</a> <br/>
			</div>
		</h2>
		<div class='wrapper'>
			<div class='content'>
					<table>
						<thead>
								<tr>
									<td colspan="7">
										<table width='100%' cellspacing='0' cellpadding='2'>
											<tr>
												<td width='30%' style='vertical-align:top;'>
															<table cellspacing='0' cellpadding='2'>
																<tr>
																	<td style='vertical-align:top;'>
																		<table>
																		<tr>
																		<td>
																			<span class='lbl1'>To</span><br/>
																		%if not o.agent:
																			<span style="text-transform:uppercase;">
																				%if o.partner_id and o.partner_id.name:
																					${o.partner_id and o.partner_id.type_of_companies and o.partner_id.type_of_companies.affix=='prefix' and o.partner_id.type_of_companies.name or ''} ${o.partner_id and o.partner_id.name or ''}${o.partner_id and o.partner_id.type_of_companies and o.partner_id.type_of_companies.affix=='suffix' and o.partner_id.type_of_companies.name or ''}<br/> 
																				%endif
																				%if o.partner_id and o.partner_id.street:
																					${o.partner_id and o.partner_id.street or ''}<br/>
																				%endif
																				%if o.partner_id and o.partner_id.street2:
																					${o.partner_id and o.partner_id.street2 or ''}<br/>
																				%endif
																				%if o.partner_id and o.partner_id.street3:
																					${o.partner_id and o.partner_id.street3 or ''}<br/>
																				%endif
																				%if o.partner_id and o.partner_id.phone:
																					Phone: ${o.partner_id and o.partner_id.phone or ''}<br/>
																				%endif
																				%if o.partner_id and o.partner_id.fax:
																					Fax : ${o.partner_id and o.partner_id.fax or ''}<br/>
																				%endif
																				%if o.partner_id and o.partner_id.city:
																					%if o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name:
																						%if partner_id and o.partner_id.zip:
																							${o.partner_id and o.partner_id.city or ''} &nbsp; ${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
																						%else:
																							${o.partner_id and o.partner_id.city or ''} &nbsp; ${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''}<br/>
																						%endif:
																					%else:
																						%if partner_id and o.partner_id.zip:
																							${o.partner_id and o.partner_id.city or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
																						%else:
																							${o.partner_id and o.partner_id.city or ''}<br/>
																						%endif:
																					%endif
																				%else:
																					%if o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name:
																						%if partner_id and o.partner_id.zip:
																							${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
																						%else:
																							${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''}<br/>
																						%endif:
																					%else:
																						%if partner_id and o.partner_id.zip:
																							${o.partner_id and o.partner_id.zip or ''}<br/>
																						%endif:
																					%endif
																				%endif
																				%if o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name:
																					${o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name or ''}
																				%endif
																			</span>
																		%else:
																			<span style="text-transform:uppercase;">	
																				%if o.agent and o.agent.name:
																					%if o.agent and o.agent.name:
																					${o.agent and o.agent.type_of_companies and o.agent.type_of_companies.affix=='prefix' and o.agent.type_of_companies.name or ''} ${o.agent and o.agent.name or ''}${o.agent and o.agent.type_of_companies and o.agent.type_of_companies.affix=='suffix' and o.agent.type_of_companies.name or ''}<br/> 
																				%endif
																				%endif
																				%if o.agent and o.agent.street:
																					${o.agent and o.agent.street or ''}<br/>
																				%endif
																				%if o.agent and o.agent.street2:
																					${o.agent and o.agent.street2 or ''}<br/>
																				%endif
																				%if o.agent and o.agent.street3:
																					${o.agent and o.agent.street3 or ''}<br/>
																				%endif
																				%if o.agent and o.agent.phone:
																					Phone: ${o.agent and o.agent.phone or ''}<br/>
																				%endif
																				%if o.agent and o.agent.fax:
																					Fax : ${o.agent and o.agent.fax or ''}<br/>
																				%endif
																				%if o.agent and o.agent.city:
																					%if o.agent and o.agent.state_id and o.agent.state_id.name:
																						%if agent and o.agent.zip:
																							${o.agent and o.agent.city or ''} &nbsp; ${o.agent and o.agent.state_id and o.agent.state_id.name or ''} &nbsp; ${o.agent and o.agent.zip or ''}<br/>
																						%else:
																							${o.agent and o.agent.city or ''} &nbsp; ${o.agent and o.agent.state_id and o.agent.state_id.name or ''}<br/>
																						%endif:
																					%else:
																						%if agent and o.agent.zip:
																							${o.agent and o.agent.city or ''} &nbsp; ${o.agent and o.agent.zip or ''}<br/>
																						%else:
																							${o.agent and o.agent.city or ''}<br/>
																						%endif:
																					%endif
																				%else:
																					%if o.agent and o.agent.state_id and o.agent.state_id.name:
																						%if agent and o.agent.zip:
																							${o.agent and o.agent.state_id and o.agent.state_id.name or ''} &nbsp; ${o.agent and o.agent.zip or ''}<br/>
																						%else:
																							${o.agent and o.agent.state_id and o.agent.state_id.name or ''}<br/>
																						%endif:
																					%else:
																						%if agent and o.agent.zip:
																							${o.agent and o.agent.zip or ''}<br/>
																						%endif:
																					%endif
																				%endif
																				%if o.agent and o.agent.country_id and o.agent.country_id.name:
																					${o.agent and o.agent.country_id and o.agent.country_id.name or ''}
																				%endif
																				<br/>
																				<u>Note</u><br/>
																				Request from : <br/>
																					${o.partner_id and o.partner_id.type_of_companies and o.partner_id.type_of_companies.affix=='prefix' and o.partner_id.type_of_companies.name or ''} ${o.partner_id and o.partner_id.name or ''}${o.partner_id and o.partner_id.type_of_companies and o.partner_id.type_of_companies.affix=='suffix' and o.partner_id.type_of_companies.name or ''}<br/>
																			</span>
																		%endif
																	</td>
																	</tr>
																	</table>
																	</td>
																</tr>
															</table>
														</td>
														<td width='5%' style='vertical-align:top;'> &nbsp; <br/><br/></td>
														<td width='30%' style='vertical-align:top;'>
															&nbsp;
														</td>
														<td width='5%' style='vertical-align:top;'> &nbsp; <br/><br/></td>
														<td width='30%'>
															<table class='borderwhite'  width='100%'  rules='all'>
																<tr>
																	<td class='lblrght' width='60%' >RFQ NO.</td>
																	<td class='borderwhite_rgt' width='40%'>DATE</td>
																</tr>
																<tr>
																	<td class='borderwhite_btm'>${o.name2 or ''}</td>
																	<td class='borderwhite_rgtbtm'>${o.id and o.date_order or ''}</td>
																</tr>
															</table>
															<table class='borderwhite'  width='100%'>
																<tr>
																	<td class='lblbtm' width='100%'>PRICE TERMS</td>
																</tr>
																<tr>
																	<td class='borderwhite_rgtbtm'>${o.incoterm and o.incoterm.code or ''}</td>
																</tr>
															</table>
															<table class='borderwhite'  width='100%'>
																<tr>
																	<td class='lblbtm' width='100%'>Expected Date</td>
																</tr>
																<tr>
																	<td class='borderwhite_rgtbtm'>
																		<span style="text-transform:uppercase;">${o.payment_term_id and o.payment_term_id.name or ''} </span>
																	</td>
																</tr>
																<!-- <tr>
																	<td class='lbl1' style='vertical-align:top;'>AGENT<br/>

																	</td>
																</tr> -->
															</table>
												</td>
											</tr>
										</table>
									</td>
								</tr>
							</br>
				
				<!-- <table class='border1'  width='100%'  cellspacing='0' cellpadding='2'> -->
								<tr>
									<td colspan="7" width='100%' style='vertical-align:top;'>
										<span>
													PLEASE QUOTE YOUR BEST POSSIBLE PRICE FOR  FOLLOWING:		
										</span>
									</td>
								</tr>
							<!-- <table class='border1'  width='100%'  cellspacing='0' cellpadding='2' style="margin-top:5px;"> -->
								<tr>
									<td class='jdltbl' width='4%'>SN.</td>
									<td class='jdltbl' width='30%'>MATERIAL</td>
									<td class='jdltbl' width='21%'>PART NO.</td>
									<td class='jdltbl' width='5%'>UOM</td>
									<td class='jdltblknn' width='12%' style="padding-right:5px;">QUANTITY</td>
									<td class='jdltbl' width='13%'>INDENT NO.</td>
									<td class='jdltbl' width='10%'>REMARKS</td>
									
								</tr>
								<tr>
									<td class='grsbwhtbl' width='100%' colspan='7'></td>
								</tr>
						</thead>
						<tbody>
								<%linecount = 0%>
								<%sumtax = 0.0%>
								<%sumwhtax = 0.0%>
								<%sn=1%>
								%for line in o.order_line:
									<%linecount = linecount + 1%>
									<%taxes = False or ''%>
								%if line.header_for_print:
									<tr>
										<td>&nbsp;</td>
										<td colspan="3" style="font-weight:bold;">${line.header_for_print.replace('\n','<br/>')}</td>
										<td></td>
										<td></td>
										<td></td>
									</tr>
									<tr>
									<td>${sn}</td>
										<td class='isitbl' style=''>
											%if line.name or line.product_id and line.product_id.name:
												${(line.name or (line.product_id and line.product_id.name) or '').upper()}</br>
												${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.detail or '-'}	
											%endif
											%if (line.catalogue_id and line.catalogue_id.catalogue) or (line.product_id and line.product_id.catalogue_numbers):
												%if (line.catalogue_id and line.catalogue_id.catalogue):
													Catalogue No.: ${((line.catalogue_id and line.catalogue_id.catalogue) or (line.product_id and line.product_id.catalogue_numbers) or '').upper()} &nbsp;&nbsp;
												%endif
												<br/>
											%endif:
											<!--
											Ship before {'no field'}<br/>
											{'no remarks field'}<br/>
											-->
										</td>
										<td class='isitbl' style=''>
											${(line.part_number or (line.product_id and line.product_id.part_number) or '').upper()}
										</td>

										<td class='isitbl' style=''>
											%if line.product_uom and line.product_uom.name:
												${line.product_uom and line.product_uom.name or ''}
											%endif
										</td>
										<td class='isitblknn' style='padding-right:5px;' >
											%if o.goods_type in ('stores',packing):
												${formatLang(line.product_qty or 0.0, 2)}
											%else:
												${formatLang(line.product_qty or 0.0, dp='Product Unit of Measure')}
											%endif
										</td>
										<td class='isitbl' style=''>${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.requisition_id and line.pr_lines[0].material_req_line_id.requisition_id.name or '-'}</td>
										<td class='isitbl' style=''> ${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.remark or '-'}	
										</td>
									</tr>
								%else:	
									<tr>
										<td>${sn}</td>
										<td class='isitbl' style=''>
											%if line.name or line.product_id and line.product_id.name:
												${(line.name or (line.product_id and line.product_id.name) or '').upper()}</br>
												${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.detail or '-'}	
											%endif:
											%if (line.catalogue_id and line.catalogue_id.catalogue) or (line.product_id and line.product_id.catalogue_numbers):
												%if (line.catalogue_id and line.catalogue_id.catalogue):
													Catalogue No.: ${((line.catalogue_id and line.catalogue_id.catalogue) or (line.product_id and line.product_id.catalogue_numbers) or '').upper()} &nbsp;&nbsp;
												%endif
												<br/>
											%endif:
											<!--
											Ship before {'no field'}<br/>
											{'no remarks field'}<br/>
											-->
										</td>
										<td class='isitbl' style=''>
											${(line.part_number or (line.product_id and line.product_id.part_number) or '').upper()}
										</td>

										<td class='isitbl' style=''>
											%if line.product_uom and line.product_uom.name:
												${line.product_uom and line.product_uom.name or ''}
											%endif:
										</td>
										<td class='isitblknn' style='padding-right:5px;' >
											%if o.goods_type in ('stores',packing):
												${formatLang(line.product_qty or 0.0, 2)}
											%else:
												${formatLang(line.product_qty or 0.0, dp='Product Unit of Measure')}
											%endif
										</td>
										<td>${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.requisition_id and line.pr_lines[0].material_req_line_id.requisition_id.name or '-'}</td>
										<td class='isitbl' style=''> ${line.pr_lines and line.pr_lines[0] and line.pr_lines[0].material_req_line_id and line.pr_lines[0].material_req_line_id.remark or '-'}
										</td>
									</tr>
								%endif
									<% sn+=1%>
								%endfor
									<tr>
											<td class='grsbwhtbl' width='98%' colspan='7'></td>
									</tr>
									<tr>
											<td colspan="7">
							<!-- </table> -->
						<!-- </td>
					</tr>
				</table> -->
													</br>
													<div style="vertical-align:top;">
														%if o.notes:	
															<a style="vertical-align:top;"><b id="jdltbl">TERMS AND CONDITIONS :</b></br>
															 ${o.notes.replace('\n','<br/>')} </a>
														%endif
													</div>
											</td>
									</tr>
						</tbody>
						<tfoot>
						</tfoot>
					</table>

			</div>
			<div class="break2" style="vertical-align:top;">&nbsp;</div>
			<div class="break1" style="page-break-before: always;">
			<div class='footer'>			
				<br/>
				<table width='100%'>
					<tr width='100%'>
						<td  width='5%' align='center' style="font-weight:bold;">&nbsp;</td>
						<td  width='30%' align='center' style="font-weight:bold;">
						<!-- 	for <a class='lbl1'>${o.partner_id and o.partner_id.name or ''}</a> --> &nbsp;
						</td>
						<td width='30%'>
						</td>
						<td  width='30%' align='center' >
							Thanks & Regards, </br>
							<a class='lbl1' style="font-weight:bold;">for &nbsp; ${o.company_id and o.company_id.name or ''}</a> &nbsp;
						</td>
						<td  width='5%' align='center' style="font-weight:bold;">&nbsp;</td>
					</tr>
					<tr width='100%'>
						<td  width='5%' align='center' class='lbl1'><br/><br/>&nbsp;</td>
						<td  width='30%' align='center' class='lbl1'><br/><br/>&nbsp;</td>
						<td  width='30%' align='center' class='lbl1'><br/><br/>&nbsp;</td>
						<td  width='30%' align='center' class='lbl1'><br/><br/>&nbsp;</td>
						<td  width='5%' align='center' class='lbl1'><br/><br/>&nbsp;</td>
					</tr>
					<tr width='100%'>
						<td  width='5%' align='center' class='lbl1'></td>
						<td class='' width='30%'></td>
						<td  width='30%' align='center' class='lbl1'></td>
						<td class='grsbwhtbl' width='30%'></td>
						<td  width='5%' align='center' class='lbl1'></td>
					</tr>
					<tr width='100%'>
						<td  width='5%' align='center' class='lbl1'></td>
						<td  width='30%' align='center'>
							<!-- Authorized Signatory (Stamp & Sign) --> &nbsp;
						</td>
						<td  width='30%' align='center' class='lbl1'></td>
						</td>
						<td  width='30%' align='center'>
							RK JAIN / ARDHI
						</td>
						<td  width='5%' align='center' class='lbl1'></td>
					</tr>
				</table>
			</div>
		</div>
		</div>
</body>
%endfor:
</html>	
