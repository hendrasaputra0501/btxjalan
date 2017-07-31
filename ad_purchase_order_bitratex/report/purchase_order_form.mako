<html>
<head>
	<style type='text/css'>
	body{
		font-family: Arial;
		font-size:12px;
	}
	
		.fontall{	
				font-family: Arial;
				font-size:11px;
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
				font-size:11px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}
		.sumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				text-align: right;
		}
		.sumtbltot{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				text-align: right;
				border-top: 1pt solid #808080;
		}
		.bwhsumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		.lbl{
			font-family: 'Arial';
			font-size:11px;
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
			font-size: 20px;
			text-transform: uppercase;
			padding-top:0px;
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
table
    {
        /*border-collapse: collapse;*/
        width: 98%;
        /*position: relative;*/
    }
td.title {
        font-weight: bold;
        font-size: 15px;
        text-align: center;
        /*background-color:red;*/
    }

thead { display: table-header-group; }
tfoot { display: table-row-group; }
tr { page-break-inside: avoid; }
	/*footer*/
html,
        body {
        margin:0;
        padding-top:0;
        height:90%;
        }
        .wrapper {
        min-height:100%;
        position:static;
        /*position:relative;*/
        font-family: Arial;
		font-size:11px;
        }
        .header {
        padding:10px;
        background:#5ee;
        }
        .content {
        	/*position:absolute;*/
        	display: block;
        	top:1em;
        /*padding:10px;*/
        width:100%;
        /*height:100%;*/
        /*padding-bottom:150px;  Height of the footer element  */
        /*background:green;*/
        /*height:910px;*/
        }
       /* .footer {
        width:100%;
        height:150px;
        position:absolute;
        bottom:0;
        left:0;
        background:#ee5;
        }*/
        
		h2 {
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
			page-break-before: always;
		}

		#footer {
	/*background:blue;*/
	width:100%;
	position:absolute;
	/*position:fixed;*/
	bottom:0;
	left:0;
	/*height:140px;*/
	height:120px;
	}
#break1{
	position:relative;
	display: block;
	/*background:green;*/
	/*height:1px;*/
	}
 #break2{
 		/*background: green;*/
 		bottom:0px;
 		
 		/*height:50px;*/
 		/*height:140px;*/
 		}
 #break3{
 		/*background: yellow;*/
 		bottom:0px;
 		
 		height:100px;
 		/*height:150px;*/
 		}


	</style>
</head>
<%
def xdate(x):
	try:
		x1 = x[:10]
	except:
		x1 = ''

	try:
		y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%b/%Y')
	except:
		y = x1
	return y
%>
<body>
%for o in objects:
<!-- <div class='wrapper' style="background:red;width:100%;"> -->
<div class='wrapper' style="width:100%;">
	<div class='content' style="width:99%;vertical-align:top;">
	<table style="page-break-before:always; width:98%;">
        <thead >
            <tr style="height:100px;">
            %if o.purchase_type=='import':
            	%if o.state=='draft':
            		<td class="title" colspan="11"  ><a class="hdr1" style='border-bottom:1px solid;'>Quotation</a> <br/></td>
            	%else:
            		<td class="title" colspan="11"><a class="hdr1" style='border-bottom:1px solid;'>Purchase Order</a> <br/></td>
            	%endif
            %else:
            	%if o.state=='draft':
            		<td class="title" colspan="10" ><a class="hdr1" style='border-bottom:1px solid;'>Quotation</a> <br/></td>
            	%else:
            		<td class="title" colspan="10"><a class="hdr1" style='border-bottom:1px solid;'>Purchase Order</a> <br/></td>
            	%endif
            %endif
           </tr>
           <tr>
       		%if o.purchase_type=='import':
				<td width='30%' style='vertical-align:top;' colspan="6">
			%else:
				<td width='30%' style='vertical-align:top;' colspan="5">
			%endif
					<table cellspacing='0' cellpadding='2'>
						<tr>
							<td style='vertical-align:top;'>
								<table>
									<tr>
										<td>
											<span class='lbl1'>To</span><br/>
											<span style="text-transform:uppercase;">	
											%if o.partner_id and o.partner_id.name:
												${o.partner_id and o.partner_id.name or ''} <br/>
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
										</td>
									</tr>
								</table>
							</td>
						</tr>
					</table>
				</td>
				<td width='5%' style='vertical-align:top;'> &nbsp; <br/><br/></td>
				<td>&nbsp;</td>
				<td width='30%' colspan="3">
					<table class='borderwhite'  width='100%'  rules='all'>
						<tr>
							<td class='lblrght' width='70%' >PO NO.</td>
							<td class='borderwhite_rgt' width='30%'>DATE</td>
						</tr>
						<tr>
							<td class='borderwhite_btm'>
								%if o.po_suffix_number:
									${o.id and o.name or ''}/${o.po_suffix_number or ''}
								%else:
									${o.id and o.name or ''}
								%endif
							</td>
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
							<td class='lblbtm' width='100%'>MODE OF PAYMENT</td>
						</tr>
						<tr>
							<td class='borderwhite_rgtbtm'>
								<!-- <span style="text-transform:uppercase;">${o.payment_method or ''}, &nbsp; ${o.payment_term_id and o.payment_term_id.name or ''} </span> -->
								<span style="text-transform:uppercase;">${o.payment_term_id and o.payment_term_id.name or ''} </span>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				%if o.purchase_type=='import':	
					<td colspan="11">
				%else:
					<td colspan="10">
				%endif
				<!-- agentttttttttttttttttttttttttt -->
					<table id="borderwhite"  width="98%" rules="all">
						<tr>
							<td id="lbl2" width="10%">AGENT</td>
							<td id="lbl2" width="25%">IR NO.</td>
							<td id="lbl2" width="15%">IR DATE</td>
							<!-- <td id="lbl2" width="20%">PR NO.</td>
							<td id="lbl2" width="20%">PR DATE</td> -->
							<td id="lbl2"  width="20%">SUPPLIER REFERENCE</td>
							<td id="lbl2"  width="20%">SUPPLIER REF. DATE</td>
							<td id="lbl2" style="border-right:white;" width="10%">DEPARTMENT USER</td>
						</tr>
						<tr>
							<td  id="txt1" width="10%" style="border-bottom:white;">
								${o.agent and o.agent.name or ''}
							</td>

							<%
							indent_lines = []
							if o.requisition_id and o.requisition_id.line_ids:
								for l in o.requisition_id.line_ids:
									if l.material_req_line_id:
										indent_lines.append(l.material_req_line_id and l.material_req_line_id.requisition_id)
							indent_lines = list(set(indent_lines))
							indent_lines = sorted(indent_lines, key=lambda x:x.date_start)
							
							%>


							<td  id="txt1" width="25%" style="border-bottom:white;">
									
									%if indent_lines:
										%for i in range(0,(len(indent_lines)>4 and 4 or len(indent_lines))):
											%if i==3 or i==(len(indent_lines)-1):
									 			${indent_lines[i].name}
									 		%else:
									 			${indent_lines[i].name}<br/>
									 		%endif
									 	%endfor
								 	%else:
								 	 	&nbsp;
								  %endif
							</td>
							 <td id="txt1" width="15%" style="border-bottom:white;">
							 	% if indent_lines:
									% for i in range(0,(len(indent_lines)>4 and 4 or len(indent_lines))):
										% if i==3 or i==(len(indent_lines)-1):
											${formatLang(indent_lines[i].date_start, date=True)}
										% else:
											${formatLang(indent_lines[i].date_start, date=True)}<br/>
										% endif
									% endfor
								% else:
									&nbsp;
								%endif
							 	
							</td>

							<td id="txt1" width="20%" style="border-bottom:white;">
								${o.partner_ref or ''}
							</td>
							<td id="txt1" width="20%" style="border-bottom:white;">
								%if o.partner_ref_date:
									${xdate(formatLang(o.partner_ref_date,date=True))}
								%else:
									&nbsp;
								%endif:
							</td>
							<td id="txt1" width="10%" style="border-bottom:white;border-right:white;">
								% if indent_lines:
									% for i in range(0,(len(indent_lines)>4 and 4 or len(indent_lines))):
										% if i==3 or i==(len(indent_lines)-1):
											${indent_lines[i].req_employee_name}
										% else:
											${indent_lines[i].req_employee_name}<br/>
										% endif
									% endfor
								% else:
									&nbsp;
								%endif
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				%if o.purchase_type=='import':	
					<td colspan="11">
				%else:
					<td colspan="10">
				%endif
				</br>
					<span style="margin-left:60px;margin-top:100px;">
								PLEASE ARRANGE TO SUPPLY MATERIALS AS DETAILED BELOW :	
					</span>
				</br>
				</td>
			</tr>
			<!-- <table class='border1'  width='98%' cellspacing="0" style="margin-top:5px;"> -->
			<tr>
				<td class='jdltbl'  width='3%'></td>
				<td class='jdltbl' width='15%'></td>
				<!-- <td class='jdltbl' width='3%'>Catalogue</td> -->
			%if o.purchase_type=='import':
				<td class='jdltbl' width='27%'></td>
				<td class='jdltbl' width='13%'>Part</td>
			%else:
				<td class='jdltbl' width='40%'></td>
			%endif
				<td class='jdltbl' width='4%'></td>
				<td class='jdltblknn' width='10%'></td>
				<td class='jdltblknn' width='9%'>PRICE</td>
				<td class='jdltbl' width='1%'>&nbsp;</td>
				<td class='jdltblknn' style="padding-right:4px;" width='9%'>AMOUNT</td>
				<td class='jdltbl' width='3%'>SITE</td>
				<td class='jdltbl' width='4%'></td>
			</tr>
			<tr>
				<td class='jdltbl'  width='3%'>SN</td>
				<td class='jdltbl' width='15%'>Item Code</td>
				<!-- <td class='jdltbl' width='3%'>Catalogue</td> -->
			%if o.purchase_type=='import':
				<td class='jdltbl' width='27%'>MATERIAL</td>
				<td class='jdltbl' width='13%'>No.</td>
			%else:
				<td class='jdltbl' width='40%'>MATERIAL</td>
			%endif
				<td class='jdltbl' style="padding-right:2px;" width='4%'>UNIT</td>
				<td class='jdltblknn' width='10%'>QTY</td>
				<td class='jdltblknn' width='9%'>(${o.pricelist_id.currency_id.name or ''})</td>
				<td class='jdltbl' width='1%'>&nbsp;</td>
				<td class='jdltblknn' width='9%' style="padding-right:4px;" >(${o.pricelist_id.currency_id.name or ''})</td>
				<td class='jdltbl' width='3%'>ID</td>
				<td class='jdltbl' width='4%' >REMARK</td>
			</tr>
			<tr>
				%if o.purchase_type=='import':
					<td class='grsbwhtbl' width='98%' colspan='11'></td>
				%else:		
					<td class='grsbwhtbl' width='98%' colspan='10'></td>
				%endif
			</tr>
			<!-- importtttttttttttttttt -->
		<!-- bodyyyyyyyyyyyyyyyyyyyyyyyyyyyy -->
		</thead>
         <tbody width="100%">
        	<!-- <tr>
            <td colspan="5"> -->
            <% total_discount = 0.0 %>
            <% total_untaxed = 0.0 %>
			%if o.purchase_type=='import':	
				<%linecount = 0%>
				<%sumtax = 0.0%>
				<%sumwhtax = 0.0%>

				<%sn=1%>
				%for line in sorted(o.order_line, key=lambda x:x.id):
					<%
					net_price = line.price_unit
					price_subtotal = line.price_subtotal
					%>
					%if line.discount_ids:
						<% amount_line = get_amount_line(line) %>
						%if check_alldiscounts_ispercentage(o):
							<% net_price = amount_line['price_after'] %>
						%else:
							<% price_subtotal = amount_line['subtotal_before_discount'] %>
							<% total_discount += amount_line['subtotal_before_discount'] - amount_line['subtotal_after_discount'] %>
						%endif
					%else:
						<% discount=0 %>
					%endif
					<!-- item -->
					%if line.other_cost_type==False:
						<%linecount = linecount + 1%>
						<%taxes = False or ''%>
						%if line.header_for_print:
							<tr>
								<td>&nbsp;</td>
								<td colspan="3" style="font-weight:bold;">${line.header_for_print.replace('\n','<br/>')}</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
								<td>&nbsp;</td>
							</tr>
							<tr>
								<td class='isitbl' style='padding-top:5px;' >
									${sn}
								</td>
								<td class='isitbl' style='padding-top:5px;' >
										${(line.product_id and line.product_id.default_code or '').upper()}						
								</td>
								<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
								<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
								<td class='isitbl' style='padding-top:5px;'>
										%if line.name:
											<%
											product_code = line.product_id and '['+line.product_id.default_code+']' or ''
											desc = line.name
											%>
											%if product_code in desc:
												<%
												index = desc.find(']') and desc.find(']')+1 or 0 
												%>
												${(desc[index:] or '').upper().replace('\n','<br/>').replace(' ','&nbsp;')}</br>
											%else:
												${(line.name or '').replace('\n','<br/>').replace(' ','&nbsp;')}
											%endif
										%endif
										<!-- catalog -->
										%if line.catalogue_appears==1:
											</br>
											%if line.catalogue_id and line.catalogue_id.catalogue or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue:
												<b>Cat No. :</b> ${ line.catalogue_id and line.catalogue_id.catalogue.upper() or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.catalogue.upper()}</br>
											%endif
										%endif
									<!--
									Ship before {'no field'}<br/>
									{'no remarks field'}<br/>
									-->
								</td>
								<td class='isitbl' style='padding-top:5px;'>
										%if line.part_number:
											${line.part_number or ''}
										%elif line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number or line.part_number:
											${line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number.upper() or line.part_number.upper()}</br>
										%endif :
								</td>
								<td class='isitbl' style='padding-top:5px;padding-left:5px;padding-right:2px;'>
										%if line.product_uom and line.product_uom.name:
											${line.product_uom and line.product_uom.name or ''}
										%endif:
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									${formatLang(line.product_qty or 0.0,dp='Product Unit of Measure')}
								</td>
								<td class='isitblknn' style='padding-top:5px;'>											 
									%if o.pricelist_id.currency_id.name=='USD':
										${formatLang(net_price or 0.0,digits=2)}
									%else:
										${formatLang(net_price or 0.0,dp='Account')}
									%endif
								</td>
								<td class='isitbl' style='padding-top:5px;'>&nbsp;
								</td>
								<td class='isitblknn' style='padding-top:5px;padding-right:4px;'>
									${formatLang(price_subtotal or 0.0,dp='Account')}
									<% total_untaxed += price_subtotal %>
								</td>
								<td class='' style='padding-top:5px;'>
									% if line.pr_lines:
										% if line.pr_lines[0].material_req_line_id:
											% if line.pr_lines[0].material_req_line_id.location_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.location_id.name or ''}
											% elif line.pr_lines[0].material_req_line_id.requisition_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.requisition_id.location_id.name or ''}
											% endif
										% else:
											${''}
										% endif
									% else:
										${''}
									% endif
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									${line.remark or ''}
								</td>
							</tr>
						%else:
							<tr>

								<td class='isitbl' style='padding-top:5px;' >
										${sn}
									</td>
									<td class='isitbl' style='padding-top:5px;' >
											${(line.product_id and line.product_id.default_code or '').upper()}						
									</td>
									<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
									<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
									<td class='isitbl' style='padding-top:5px;'>
									%if line.name:
										<%
										product_code = line.product_id and '['+line.product_id.default_code+']' or ''
										desc = line.name
										%>
										%if product_code in desc:
											<%
											index = desc.find(']') and desc.find(']')+1 or 0 
											%>
											${(desc[index:] or '').upper().replace('\n','<br/>').replace(' ','&nbsp;')}</br>
										%else:
											${(line.name or '').replace('\n','<br/>').replace(' ','&nbsp;')}</br>
										%endif
									%endif
										
										<!-- catalog -->
									%if line.catalogue_appears==1:
											</br>
											%if line.catalogue_id and line.catalogue_id.catalogue or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue:
												<b>Cat No. :</b> ${line.catalogue_id and line.catalogue_id.catalogue.upper() or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.catalogue.upper()}</br>
											%endif
									%endif	
										<!--
										Ship before {'no field'}<br/>
										{'no remarks field'}<br/>
										-->
									</td>
									<td class='isitbl' style='padding-top:5px;'>
										%if line.part_number:
											${line.part_number or ''}
										%elif line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number or line.part_number:
											${line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number.upper() or line.part_number.upper()}</br>
										%endif
									</td>
									<td class='isitbl' style='padding-top:5px;padding-left:5px;padding-right:2px;'>
											%if line.product_uom and line.product_uom.name:
												${line.product_uom and line.product_uom.name or ''}
											%endif:
									</td>
									<td class='isitblknn' style='padding-top:5px;'>
										${formatLang(line.product_qty or 0.0,dp='Product Unit of Measure')}
									</td>
									<td class='isitblknn' style='padding-top:5px;'>
										%if o.pricelist_id.currency_id.name=='USD':
											${formatLang(net_price or 0.0,digits=2)}
										%else:
											${formatLang(net_price or 0.0,dp='Account')}
										%endif
									</td>
									<td class='isitbl' style='padding-top:5px;'>&nbsp;
									</td>
									<td class='isitblknn' style='padding-top:5px;padding-right:4px;'>
											${formatLang(price_subtotal or 0.0,dp='Account')}
											<% total_untaxed += price_subtotal %>
									</td>
									<td class='' style='padding-top:5px;'>
										% if line.pr_lines:
											% if line.pr_lines[0].material_req_line_id:
												% if line.pr_lines[0].material_req_line_id.location_id:
													${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.location_id.name or ''}
												% elif line.pr_lines[0].material_req_line_id.requisition_id:
													${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.requisition_id.location_id.name or ''}
												% endif
											% else:
												${''}
											% endif
										% else:
											${''}
										% endif
									</td>
									<td class='isitblknn' style='padding-top:5px;'>
										${line.remark or ''}
									</td>
								<!-- <td class='isitbl' width='1%' style='padding-top:5px;'>&nbsp;
								</td> -->
								
								<!-- <td class='isitbl' width='10%' style='padding-top:5px;'>
									${taxes or ''}
								</td> -->
							</tr>
						%endif
						<tr>
							<td class='isitbl'  style="padding-top:0px;" colspan='11'></td>
						</tr>
						<%sn+=1%>
					%endif
				%endfor
				<!-- other Cost Type-->
				%for line in o.order_line:
					<%
					net_price = line.price_unit
					price_subtotal = line.price_subtotal
					%>
					%if line.discount_ids:
						<% amount_line = get_amount_line(line) %>
						%if check_alldiscounts_ispercentage(o):
							<% net_price = amount_line['price_after'] %>
						%else:
							<% price_subtotal = amount_line['subtotal_before_discount'] %>
						%endif
					%else:
						<% discount=0 %>
					%endif

					%if line.other_cost_type:
						<%taxes = False or ''%>
						<tr>
							<td class='isitbl' style='padding-top:5px;' >
								<!-- ${sn} -->&nbsp;
							</td>
							<td class='isitbl' style='padding-top:5px;' >&nbsp;</td>
							<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
							<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
							<td class='isitbl' style='padding-top:5px;'>
								${(line.name or '').upper().replace(' ','&nbsp;')}
							</td>
							<td class='isitbl' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitbl' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								%if o.pricelist_id.currency_id.name=='USD':
									${formatLang(net_price or 0.0,digits=2)}
								%else:
									${formatLang(net_price or 0.0,dp='Account')}
								%endif:
							</td>
							<td class='isitbl' style='padding-top:5px;'>&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								${formatLang(price_subtotal or 0.0,dp='Account')}
								<% total_untaxed += price_subtotal %>
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								${line.remark or ''}
							</td>
							<!-- <td class='isitbl' width='1%' style='padding-top:5px;'>&nbsp;
							</td> -->
							
							<!-- <td class='isitbl' width='10%' style='padding-top:5px;'>
								${taxes or ''}
							</td> -->
						</tr>
						<tr>
								<td class='isitbl'  style="padding-top:0px;" colspan='11'></td>
						</tr>
											
					%endif
				%endfor
								
						<tr>
							<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
								TOTAL:
							</td>
							<td class='isitbl'  style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='sumtbltot'  style="padding-top:0px;">
								${formatLang(total_untaxed or 0.0,dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
							<!-- <td width='1%'>
									&nbsp;
							</td> -->
						</tr>
				%for tax in line.taxes_id:
					%if (tax.amount or 0.0) < 0.0:
						<%sumwhtax += abs(tax.amount or 0.0)%>
					%else:
						<%sumtax += (tax.amount or 0.0)%>
					%endif
					%if taxes != "":
						<%taxes += ', '%>
					%endif
					<%taxes += formatLang((tax.amount or 0.0)*100.0,digits=1) + '%'%>
				%endfor
				%if not check_alldiscounts_ispercentage(o) and total_discount>0.0:
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
							TOTAL DISCOUNT:
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbl'  style="padding-top:0px;">
							${formatLang(total_discount or 0.0,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
							<!-- <td width='1%'>
								&nbsp;
							</td> -->
					</tr>
				%endif
				%if sumtax > 0.0:
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
							TAX (${taxes or ''}):
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbl'  style="padding-top:0px;">
							${formatLang((o.amount_untaxed or 0.0)*sumtax,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
							<!-- <td width='1%'>
								&nbsp;
							</td> -->
					</tr>
				%endif
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
							GRAND TOTAL:
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						%if sumtax > 0.0:
							<td class='sumtbltot' style="padding-top:0px;">
								${formatLang((o.amount_untaxed or 0.0)*(1.0+sumtax),dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
						%else:
							<td class='sumtbl'  style="padding-top:0px;">
								${formatLang((o.amount_untaxed or 0.0)*(1.0+sumtax),dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
						%endif:
						</tr>
				%if sumwhtax > 0.0:
						<tr>
							<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
								LESS WHTAX:
							</td>
							<td class='isitbl'  style='padding-top:5px;'>&nbsp;
							</td>
							<td class='sumtbl'  style="padding-top:0px;">
								${formatLang((o.amount_untaxed or 0.0)*sumwhtax,dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
							<!-- <td width='1%'>
							&nbsp;
							</td> -->
						</tr>
				%endif
				%if sumwhtax > 0.0:
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='7'>
							NET AMOUNT:
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbltot' style="padding-top:0px;">
							${formatLang(o.amount_total or 0.0,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
						<!-- <td width='1%'>
						&nbsp;
						</td> -->
					</tr>
				%endif
					<tr>
						<td class='grsbwhtbl'  colspan='11'></td>
					</tr>
					<tr>
						<td class='lbl1'  colspan='11'>
							TOTAL AMOUNT : ${o.pricelist_id.currency_id.name or ''} ${call_num2word(o.amount_total,'en')} ONLY
						</td>
					</tr>

					<!-- </table> -->
			%else:
			<!-- ################# LOCAL ################# -->
				<%linecount = 0%>
				<%sumtax = 0.0%>
				<%sumwhtax = 0.0%>

				<%sn=1%>
						
				%for line in sorted(o.order_line, key=lambda x:x.id):
					<%
					net_price = line.price_unit
					%>
					%if line.discount_ids:
						<% discount=(line.discount_ids and line.discount_ids[0].discount_amt)/100
						%>
						%for disc in  line.discount_ids:
							<%
							# net_price -= (disc.type == 'percentage') and round((disc.discount_amt)*net_price/100,2) or disc.discount_amt
							net_price -= (disc.type == 'percentage') and (disc.discount_amt/100)*net_price or disc.discount_amt
							%>
						%endfor:
					%else:
						<% discount=0 %>
					%endif					
					<!-- item -->
					%if line.other_cost_type==False:
						<%linecount = linecount + 1%>
						<%taxes = False or ''%>
					
						%if line.header_for_print:
							<tr>
								<td>&nbsp;</td>
								<td colspan="3" style="font-weight:bold;">${line.header_for_print.replace('\n','<br/>')}</td>
								<td></td>
								<td></td>
								<td></td>
								<td></td>
								<td></td>
								<td></td>
								<!-- <td></td> -->
								<!-- <td></td> -->
							</tr>
							<tr>
								<td class='isitbl' style='padding-top:5px;' >
									${sn}
								</td>
								<td class='isitbl' style='padding-top:5px;' >
									${(line.product_id and line.product_id.default_code or '').upper()}						
								</td>
								<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
								<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
								<td class='isitbl' style='padding-top:5px;'>
									%if line.name:
										<%
										product_code = line.product_id and '['+line.product_id.default_code+']' or ''
										desc = line.name
										%>
										%if product_code in desc:
											<%
											index = desc.find(']') and desc.find(']')+1 or 0 
											%>
											${(desc[index:] or '').upper().replace('\n','<br/>').replace(' ','&nbsp;')}</br>
										%else:
											${(line.name or '').replace('\n','<br/>').replace(' ','&nbsp;')}
										%endif
									%endif
									<!-- catalog -->
									%if line.catalogue_appears==1:
										</br>
										%if line.catalogue_id and line.catalogue_id.catalogue or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue:
											<b>Cat No. :</b> ${line.catalogue_id and line.catalogue_id.catalogue.upper() or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.catalogue.upper()}</br>
										%endif
									%endif
									<!--
									Ship before {'no field'}<br/>
									{'no remarks field'}<br/>
									-->
								</td>
								<%
								# <td class='isitbl' style='padding-top:5px;'>
								# 		%if line.part_number:
								# 			${line.part_number or ''}
								# 		%elif line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number or line.part_number:
								# 			${line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number.upper() or line.part_number.upper()}</br>
								# 		%endif :
								# </td>
								%>
								<td class='isitbl' style='padding-top:5px;padding-left:5px;padding-right:2px;'>
									%if line.product_uom and line.product_uom.name:
										${line.product_uom and line.product_uom.name or ''}
									%endif
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									${formatLang(line.product_qty or 0.0,dp='Product Unit of Measure')}
								</td>
								<td class='isitblknn' style='padding-top:5px;'>							
								%if o.pricelist_id.currency_id.name=='USD':
									${formatLang(net_price or 0.0,digits=2)}
								%else:
									${formatLang(net_price or 0.0,dp='Account')}
								%endif:
								</td>
								<td class='isitbl' style='padding-top:5px;'>&nbsp;
								</td>
								<td class='isitblknn' style='padding-top:5px;padding-right:4px;'>
									${formatLang(line.price_subtotal or 0.0,dp='Account')}
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									% if line.pr_lines:
										% if line.pr_lines[0].material_req_line_id:
											% if line.pr_lines[0].material_req_line_id.location_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.location_id.name or ''}
											% elif line.pr_lines[0].material_req_line_id.requisition_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.requisition_id.location_id.name or ''}
											% endif
										% else:
											${''}
										% endif
									% else:
										${''}
									% endif
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									${line.remark or ''}
								</td>
							</tr>
						%else:
						<tr>
							<td class='isitbl' style='padding-top:5px;' >
									${sn}
								</td>
								<td class='isitbl' style='padding-top:5px;' >
										${(line.product_id and line.product_id.default_code or '').upper()}						
								</td>
								<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
								<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
								<td class='isitbl' style='padding-top:5px;'>
								%if line.name:
									<%
									product_code = line.product_id and '['+line.product_id.default_code+']' or ''
									desc = line.name
									%>
									%if product_code in desc:
										<%
										index = desc.find(']') and desc.find(']')+1 or 0 
										%>
										${(desc[index:] or '').upper().replace('\n','<br/>').replace(' ','&nbsp;')}</br>
									%else:
										${(line.name or '').replace('\n','<br/>').replace(' ','&nbsp;')}
									%endif
								%endif				
									<!-- catalog -->
									%if line.catalogue_appears==1:
										</br>

										%if line.catalogue_id and line.catalogue_id.catalogue or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue:
											<b>Cat No. :</b> ${line.catalogue_id and line.catalogue_id.catalogue.upper() or line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].catalogue and line.product_id.catalogue_lines[0].catalogue.catalogue.upper()}</br>
										%endif
									%endif
									<!--
									Ship before {'no field'}<br/>
									{'no remarks field'}<br/>
									-->
								</td>
								<%
									# <td class='isitbl' style='padding-top:5px;'>
									# 	%if line.part_number:
									# 		${line.part_number or ''}
									# 	%elif line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number or line.part_number:
									# 		${line.product_id and line.product_id.catalogue_lines and line.product_id.catalogue_lines[0].part_number.upper() or line.part_number.upper()}</br>
									# 	%endif
									# </td>
								%>
								<td class='isitbl' style='padding-top:5px;padding-left:5px;padding-right:2px;'>
									%if line.product_uom and line.product_uom.name:
										${line.product_uom and line.product_uom.name or ''}
									%endif
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
									${formatLang(line.product_qty or 0.0,dp='Product Unit of Measure')}
								</td>
								<td class='isitblknn' style='padding-top:5px;'>
								%if o.pricelist_id.currency_id.name=='USD':
									${formatLang(net_price or 0.0,digits=2)}
								%else:
									${formatLang(net_price or 0.0,dp='Account')}
								%endif:
								</td>
								<td class='isitbl' style='padding-top:5px;'>&nbsp;
								</td>
								<td class='isitblknn' style='padding-top:5px;padding-right:4px;'>
									${formatLang(line.price_subtotal or 0.0,dp='Account')}
								</td>
								<td class='' style='padding-top:5px;'>
									% if line.pr_lines:
										% if line.pr_lines[0].material_req_line_id:
											% if line.pr_lines[0].material_req_line_id.location_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.location_id.name or ''}
											% elif line.pr_lines[0].material_req_line_id.requisition_id:
												${line.pr_lines[0].material_req_line_id.location_id.alias or line.pr_lines[0].material_req_line_id.requisition_id.location_id.name or ''}
											% endif
										% else:
											${''}
										% endif
									% else:
										${''}
									% endif
								</td>
								<td class='' style='padding-top:5px;'>
										${line.remark or ''}
								</td>
								<!-- <td class='isitbl' width='1%' style='padding-top:5px;'>&nbsp;
								</td> -->
								
								<!-- <td class='isitbl' width='10%' style='padding-top:5px;'>
									${taxes or ''}
								</td> -->
							</tr>
						%endif
						<tr>
							<td class='isitbl'  style="padding-top:0px;" colspan='10'></td>
						</tr>
						<%sn+=1%>
					%endif
				%endfor
				<!-- other Cost Type-->
				%for line in o.order_line:
					<%
					net_price = line.price_unit
					%>
					%if line.discount_ids:
						<% discount=(line.discount_ids and line.discount_ids[0].discount_amt)/100
						%>
						%for disc in  line.discount_ids:
							<%
							# net_price -= (disc.type == 'percentage') and round((disc.discount_amt)*net_price/100,2) or disc.discount_amt
							net_price -= (disc.type == 'percentage') and (disc.discount_amt/100)*net_price or disc.discount_amt
							%>
						%endfor:
					%else:
						<% discount=0 %>
					%endif
					%if line.other_cost_type:
						<%taxes = False or ''%>
						<tr>
							<td class='isitbl' style='padding-top:5px;' >
								<!-- ${sn} -->
							</td>
							<td class='isitbl' style='padding-top:5px;' >&nbsp;</td>
							<!-- <td class='isitbl' style='padding-top:5px;' width='3%'></td>
							<td class='isitbl' style='padding-top:5px;' width='5%'></td> -->
							<td class='isitbl' style='padding-top:5px;'>
								${(line.name or '').replace(' ','&nbsp;').upper()}</td>
							</td>
							<!-- <td class='isitbl' style='padding-top:5px;'>
								&nbsp;
							</td> -->
							<td class='isitbl' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								%if o.pricelist_id.currency_id.name=='USD':
									${formatLang(net_price or 0.0,digits=2)}
								%else:
									${formatLang(net_price or 0.0,dp='Account')}
								%endif:
							</td>
							<td class='isitbl' style='padding-top:5px;'>&nbsp;
							</td>
							<td class='isitblknn' style='padding-top:5px;'>
								${formatLang(line.price_subtotal or 0.0,dp='Account')}
							</td>
							<td class='' style='padding-top:5px;'>
								&nbsp;
							</td>
							<td class='' style='padding-top:5px;'>
								${line.remark or ''}
							</td>
							<!-- <td class='isitbl' width='1%' style='padding-top:5px;'>&nbsp;
							</td> -->
							
							<!-- <td class='isitbl' width='10%' style='padding-top:5px;'>
								${taxes or ''}
							</td> -->
						</tr>
						<tr>
							<td class='isitbl'  style="padding-top:0px;" colspan='10'></td>
						</tr>
					%endif
				%endfor
						<tr>
							<!-- <td class='sumtbl' width='86%' style="padding-top:0px;" colspan='6'> -->
							<td class='sumtbl'  style="padding-top:0px;" colspan='6'>
								TOTAL:
							</td>
							<!-- <td class='isitbl' width='1%' style='padding-top:5px;'> -->
							<td class='isitbl' style='padding-top:5px;'>
								&nbsp;
							</td>
							<!-- <td class='sumtbltot' width='12%' style="padding-top:0px;"> -->
							<td class='sumtbltot'  style="padding-top:0px;">
								${formatLang(o.amount_untaxed or 0.0,dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
							<!-- <td width='1%'>
									&nbsp;
							</td> -->
						</tr>
				%for tax in line.taxes_id:
					%if (tax.amount or 0.0) < 0.0:
						<%sumwhtax += abs(tax.amount or 0.0)%>
					%else:
						<%sumtax += (tax.amount or 0.0)%>
					%endif:
					%if taxes != "":
						<%taxes += ', '%>
					%endif:
					<%taxes += formatLang((tax.amount or 0.0)*100.0,digits=1) + '%'%>
				%endfor
				%if sumtax > 0.0:
					<tr>
						<!-- <td class='sumtbl' width='86%' style="padding-top:0px;" colspan='6'> -->
						<td class='sumtbl'  style="padding-top:0px;" colspan='6'>
							TAX (${taxes or ''}):
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbl'  style="padding-top:0px;">
							${formatLang((o.amount_untaxed or 0.0)*sumtax,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
							<!-- <td width='1%'>
								&nbsp;
							</td> -->
					</tr>
				%endif
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='6'>
							GRAND TOTAL:
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						%if sumtax > 0.0:
							<td class='sumtbltot'  style="padding-top:0px;">
								${formatLang((o.amount_untaxed or 0.0)*(1.0+sumtax),dp='Account')}
							</td>
						%else:
							<td class='sumtbl'  style="padding-top:0px;">
								${formatLang((o.amount_untaxed or 0.0)*(1.0+sumtax),dp='Account')}
							</td>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
						%endif
					</tr>
				%if sumwhtax > 0.0:
					<tr>
						<td class='sumtbl' style="padding-top:0px;" colspan='6'>
							LESS WHTAX:
						</td>
						<td class='isitbl' style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbl'  style="padding-top:0px;">
							${formatLang((o.amount_untaxed or 0.0)*sumwhtax,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
						<!-- <td width='1%'>
						&nbsp;
						</td> -->
					</tr>
				%endif
				%if sumwhtax > 0.0:
					<tr>
						<td class='sumtbl'  style="padding-top:0px;" colspan='6'>
							NET AMOUNT:
						</td>
						<td class='isitbl'  style='padding-top:5px;'>&nbsp;
						</td>
						<td class='sumtbltot'  style="padding-top:0px;">
							${formatLang(o.amount_total or 0.0,dp='Account')}
						</td>
						<td>&nbsp;</td>
						<td>&nbsp;</td>
						<!-- <td width='1%'>
						&nbsp;
						</td> -->
					</tr>
				%endif
					<tr>
						<td class='grsbwhtbl'  colspan='10'></td>
					</tr>
					<tr>
						<td class='lbl1'  colspan='10'>
							TOTAL AMOUNT : ${o.pricelist_id.currency_id.name or ''} ${call_num2word(o.amount_total,'en')} ONLY
						</td>
					</tr>
			%endif
			<!-- ################# END LOCAL ################# -->
            <tr>
		    	%if o.purchase_type=='import':	
					<td colspan="11">
				%else:
					<td colspan="10">
				%endif
        		%if o.purchase_type=="import":
					%if o.order_line and o.order_line[0].discount_ids and o.order_line[0].discount_ids[0].discount_amt and check_alldiscounts_ispercentage(o):
					<div style="vertical-align:top;margin-bottom:5px;text-transform:uppercase;">
								&nbsp; &nbsp; above price after&nbsp; ${formatLang(o.order_line[0].discount_ids[0].discount_amt or '',digits=2)} % discount		
					</div>
					%endif
				%endif
				%if o.purchase_type=="local":
					<div style="vertical-align:top;">
						%if o.remark_po:
							</br>
							<a style="vertical-align:top;"><b id="jdltbl">REMARK :</b></br>	
							 ${o.remark_po.replace('\n','<br/>')} </a>
							 </br></br>
						%endif
					</div>
				%endif
					<div style="vertical-align:top;">
						%if o.notes:	
							<a style="vertical-align:top;"><b id="jdltbl">TERMS AND CONDITIONS :</b></br>
							 ${o.notes.replace('\n','<br/>')} </a>
						%endif
					</div>
					<div id="break3" style="vertical-align:top;">
						&nbsp;
					</div>
				</td>
	        	</tr>
        </tbody>   
        <tfoot>
            <tr width="100%" >
                %if o.purchase_type=='import':	
	                <td colspan="11"  style="height:10px;" width="100%">
	                	&nbsp;
	                </td>
            	%else:
	            	<td colspan="10" style="height:10px;" width="100%">
	                	&nbsp;
	                </td>
				%endif
            </tr>
            <!-- <div id="break1" style="page-break-before: always;background:black;"> -->
            <div id="break1" style="page-break-before: always;">
	            <tr>
	            	<td>
	            		<!-- <div style="position:absolute;bottom:0;background:black;height:5px;">&nbsp;</div> -->
	            		<!-- <div style="position:absolute;bottom:0;height:1px;">&nbsp;</div> -->
	            	</td>
	            </tr>
        	</div>
        </tfoot>
    </table>
    </div><!--  content -->
	<div id="break2" style="vertical-align:top;">&nbsp;</div>
	<div id="break1" style="page-break-before: always;">
		<div id='footer'>
			<table width='100%'>
				<tr width='100%'>
					<td  width='5%' align='center' style="font-weight:bold;height:50px">&nbsp;</td>
					<td  width='20%' align='center' style="font-weight:bold;">
						&nbsp;<!-- for <a class='lbl1'>${o.partner_id and o.partner_id.name or ''}</a> -->
					</td>
					<!-- <td width='30%'>
					</td> -->
					<td  width='70%' align='center' style="font-weight:bold;text-align:right;" colspan="3">
						 for<a class='lbl1'>&nbsp; ${o.company_id and o.company_id.name or ''}</a>
					</td>
					<td  width='5%' align='center' style="font-weight:bold;">&nbsp;</td>
				</tr>
				<tr width='100%'>
					<td  width='5%' align='center' class='lbl1'><br/>&nbsp;</td>
					<td  width='20%' align='center' class='lbl1'><br/>&nbsp;</td>
					<td  width='30%' align='center' class='lbl1'><br/>&nbsp;</td>
					<td  width='10%' align='center' class='lbl1'><br/>&nbsp;</td>
					<td  width='30%'  align='center' class='lbl1'><br/>&nbsp;</td>
					<td  width='5%' align='center' class='lbl1'><br/>&nbsp;</td>
				</tr>
				<tr width='100%'>
					<td  width='5%' align='center' class='lbl1'></td>
					<!-- <td class='grsbwhtbl' width='30%'></td> -->
					<td class='grsbwhtbl' width='20%'></td>
					<td class='' width='30%'></td>
					<!-- <td  width='30%' align='center' class='lbl1'></td> -->
					<td class='grsbwhtbl' width='40%' style="text-align:right;" colspan="2"></td>
					<td  width='5%' align='center' class='lbl1'></td>
				</tr>
				<tr width='100%'>
					<td  width='5%' align='center' class='lbl1'></td>
					<td  width='20%' align='center'>
						&nbsp; Prepared by
					</td>
					<!-- <td  width='30%' align='center' class='lbl1'></td>
					</td> -->
					<td  width='70%' style="text-align:right;" align='center' colspan="3">
						Authorized Signatory (Stamp & Sign)
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
