<html>
<head>
	<style type="text/css">
		#title1 {
				font-family: Arial;
				font-size: 15px;
				font-weight: bold;
		}
		.fontall{	
				font-family: Arial;
				font-size:10px;
		}
		
		.border1 {
				border:0px solid;
				margin:0 0px 0 0px;
				/*width:1300px;*/
		}
		#jdltbl{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
		}
		#jdltbl2{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				padding-left: 7px;
		}
		#isitblknn{
				text-align: right;
		}
		td {
		vertical-align:top;
		}
		#bwhtbl{text-transform: uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #A0A0A0;
		}
		#sumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
		}
		#bwhsumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		#lbl{
			font-family: "Arial";
			font-size:10px;
			font-weight: bold;
			padding:0px 10px 0px 20px;
			vertical-align: top;
			text-transform:uppercase;
		}
		#lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		#tdtxt{
			font-size:11px;
			padding:0px 20px 0px 10px;
		}
		#borderwhite{
			border-top:white;
			border-left:white;
		}
		#borderwhite_rgt{
			border-right:white;
			padding-left: 3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		#borderwhite_rgtbtm{
			border-right:white;
			border-bottom:white;
			padding-left: 3px;	
		}
		#borderwhite_btm{
			border-bottom:white;
			padding-right:3px;
		}
		#lblrght{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		#lbl2{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			text-align: center;
		}
		#borderwhite_rgt2{
			border-right:white;
			text-align: center;
			font-weight:bold;
			text-transform: uppercase;
		}
		#borderwhite_btm2{
			border-bottom:white;
			text-align: center;
			font-weight:bold;
		}
		#borderwhite_rgtbtm2{
			border-right:white;
			border-bottom:white;
			text-align: center;
		}
		#grsbwhtbl{
			border-bottom: 1px solid #A0A0A0;
		}
		#jdltblknn{
				text-transform: uppercase;
				text-align: right;
				font-family: Arial;
				font-weight: bold;
		}
		#jdltblpd7{
				text-transform: uppercase;
				padding-left:7px;
				font-family: Arial;
				font-weight: bold;

		}
		#isitblpd7{
				padding-left: 7px;
		}
		#hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
}
		#font-capitalize{
		text-transform:capitalize;
		}
	/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        font-size:10px;
        }
        #wrapper {
        min-height:100%;
        position:static;
        font-family: Arial;
		font-size:11px;
        }
        #header {
        padding:10px;
        background:#5ee;
        }
        #content {
	padding-bottom:10px; /* Height of the footer element */
		}
#footer {
	/*background:blue;*/
	width:100%;
	position:absolute;
	bottom:0;
	left:0;
	}
#break1{
	position:relative;
	display: block;
	}
 #break2{
 		/*background: yellow;*/
 		bottom:60;
 		height:140px;
 		}
     
#bwhtblup1{
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		border-top: 1px solid #A0A0A0;
		vertical-align:top;
}
	</style>
</head>
<%
from datetime import datetime
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
% for o in objects:
<body>
<div  id="wrapper">
	<div id="hdr1">
		<a style="border-bottom:1px solid;">SALES CONFIRMATION</a> <br/><br/>
	</div>
	<div id="content">
		<table width="100%" >
			<tr>
				<td width="60%" style="vertical-align:top;">
					<table>
						<tr>
							<td style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">
							Buyer: </a></br>
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
									%if o.partner_id and o.partner_id.city:
										${o.partner_id and o.partner_id.city or ''}<br/>
									%elif o.partner_id and o.partner_id.street3 or o.partner_id and o.partner_id.city: 
										${o.partner_id and o.partner_id.street3 or ''} &nbsp; ${o.partner_id and o.partner_id.city or ''}<br/>
									%endif
									%if partner_id and o.partner_id.zip:
										${o.partner_id and o.partner_id.zip or ''}<br/>
									%elif o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or o.partner_id and o.partner_id.zip:
										${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
									%endif
									%if o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name:
										${o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name or ''}<br/>
									%endif
								</span>
							</td>
						</tr>
					</table>
					%if o.consignee and o.consignee.name:
						<table>
							<tr>
								<td style="vertical-align:top;">
									<a style="font-weight:bold;text-transform:uppercase;">Consignee</a>
									</br>
									<span style="text-transform:uppercase;">
										%if o.consignee.name:
											${o.consignee.name or ''} <br/>
										%endif
										%if o.consignee and o.consignee.street:
											${o.consignee and o.consignee.street or ''}<br/>
										%endif
										%if o.consignee and o.consignee.street2:
											${o.consignee and o.consignee.street2 or ''}<br/>
										%endif
										%if o.consignee and o.consignee.city:
											${o.consignee and o.consignee.city or ''}<br/>
										%elif o.consignee and o.consignee.street3 or o.consignee and o.consignee.city: 
											${o.consignee and o.consignee.street3 or ''} &nbsp; ${o.consignee and o.consignee.city or ''}<br/>
										%endif
										%if o.consignee and o.consignee.zip:
											${o.consignee and o.consignee.zip or ''}<br/>
										%elif o.consignee and o.consignee.state_id and o.consignee.state_id.name or o.consignee and o.consignee.zip:
											${o.consignee and o.consignee.state_id and o.consignee.state_id.name or ''} &nbsp; ${o.consignee and o.consignee.zip or ''}<br/>
										%endif
										%if o.consignee and o.consignee.country_id and o.consignee.country_id.name:
											${o.consignee and o.consignee.country_id and o.consignee.country_id.name or ''}<br/>
										%endif
									</span>
								</td>
							</tr>
						</table>
					%endif
					%if o.notify.name:
						<table>
							<tr>
								<td style="vertical-align:top;">
									<a style="font-weight:bold;text-transform:uppercase;">Notify</a>
									</br>
									<span style="text-transform:uppercase;">
										%if o.notify.name:
											${o.notify.name or ''} <br/>
										%endif
										%if o.notify and o.notify.street:
											${o.notify and o.notify.street or ''}<br/>
										%endif
										%if o.notify and o.notify.street2:
											${o.notify and o.notify.street2 or ''}<br/>
										%endif
										%if o.notify and o.notify.city:
											${o.notify and o.notify.city or ''}<br/>
										%elif o.notify and o.notify.street3 or o.partner_id and o.notify.city: 
											${o.notify and o.notify.street3 or ''} &nbsp; ${o.notify and o.notify.city or ''}<br/>
										%endif
										%if o.notify and o.notify.zip:
											${o.notify and o.notify.zip or ''}<br/>
										%elif o.notify and o.notify.state_id and o.notify.state_id.name or o.notify and o.notify.zip:
											${o.notify and o.notify.state_id and o.notify.state_id.name or ''} &nbsp; ${o.notify and o.notify.zip or ''}<br/>
										%endif
										%if o.notify and o.notify.country_id and o.notify.country_id.name:
											${o.notify and o.notify.country_id and o.notify.country_id.name or ''}<br/>
										%endif
									</span>
								</td>
							</tr>
						</table>
					%endif
				</td>
				<td width="40%">
					<table id="borderwhite"  width="100%"  rules="all">
						<tr>
							<td id="lblrght" width="60%" >SC NO.</td><td id="borderwhite_rgt" width="40%">Date</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${o.name or ''}</td><td id="borderwhite_rgtbtm">${o.date_order or ''}</td>
						</tr>
					</table>
					<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
						<tr>
							<td id="lblrght" width="60%" >Customer Reference</td><td id="borderwhite_rgt" width="40%">Date</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${o.client_order_ref or ''}</td><td id="borderwhite_rgtbtm">${o.client_order_ref_date or ''}</td>
						</tr>
					</table>
					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Payment Terms</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm"><a style="text-transform:uppercase;">${o.payment_method or ''} : </a> &nbsp; ${o.payment_term and o.payment_term.name or ''}</td>
						</tr>
					</table>

					<% 
					kode=get_upper_incoterm(o.incoterm)
					%>		
						
					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Delivery Term</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
								%if kode:
									${o.incoterm.name or ''} (${kode or ''})
								%else:
									&nbsp;
								%endif
							</td>
							
						</tr>
					</table>
					<table id="borderwhite" width="100%" rules="all">
					%if o.sale_type=="export":
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Port/Country of Loading</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm" style="text-transform:uppercase;">
								%if o.source_country_id and o.source_country_id.name:
									${o.source_port_id and o.source_port_id.name or ''} &nbsp; ${o.source_country_id and o.source_country_id.name or ''}
								%elif o.source_port_id and o.source_port_id.name:
									${o.source_port_id and o.source_port_id.name or ''}
								%endif
							</td>
						</tr>
					%endif
					</table>

					%if o.sale_type=="export":
						<table id="borderwhite" width="100%" rules="all">
							<tr>
								<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Port/Country of Destination</td>
							</tr>
							<tr>
								<td id="borderwhite_rgtbtm" style="text-transform:uppercase;">
									%if o.dest_country_id and o.dest_country_id.name:
										${o.dest_port_id and o.dest_port_id.name or ''} &nbsp; ${o.dest_country_id and o.dest_country_id.name or ''}
									%elif o.dest_port_id and o.dest_port_id.name:
										${o.dest_port_id and o.dest_port_id.name or ''}
									%endif
								</td>
							</tr>
						</table>
					%endif
				</td>
			</tr>
		</table>
		</br>
		<%
		totline_qty,subtot_amt=get_total_line(o.order_line)
		terbilang=call_num2word(subtot_amt,"en")
		%>
		<!-- <table id="borderwhite" width="100%" rules="all">
				<tr>
					<td id="lbl2" width="15%">quantity(${o.order_line and o.order_line.product_uom and o.order_line.product_uom[0].name})</td>
					<td id="lbl2" width="10%">currency</td>
					<td id="lbl2" width="15%">amount</td>
					<td id="borderwhite_rgt2" width="70%">amount in words</td>
				</tr>
				<tr>
					<td id="borderwhite_btm2" width="15%">
						${formatLang(totline_qty)}
						</td>
					<td id="borderwhite_btm2" width="10%">${o.pricelist_id.currency_id.name or ''}</td>
					<td id="borderwhite_btm2" width="15%">${formatLang(subtot_amt)}</td>
					<td id="borderwhite_rgtbtm2" width="70%" style="text-transform:capitalize;font-weight:bold;">${o.pricelist_id.currency_id.name or ''} &nbsp; ${terbilang}</td>
				</tr>
		</table> -->

		<%line_count=0%>
		<table class='border1'  width='98%' cellspacing="0">
			<tr>
				<td id='jdltbl' width='15%'></td>
				<td id='jdltbl' width='51%'></td>
				<td id='jdltbl' width='5%'></td>
				<td id='jdltblknn' width='11%'></td>
				<td id='jdltblknn' width='8%' style="padding-right:5px;">Price</td>
				<td id='jdltblknn' width='10%'>amount</td>
			</tr>
			<tr>
				<td id='jdltbl' width='15%'>Delivery No.</td>
				<td id='jdltbl' width='51%'>PRoduct</td>
				<td id='jdltbl' width='5%' style="padding-right:5px;">UOM</td>
				<td id='jdltblknn' width='11%' style="padding-right:5px;">Quantity</td>
				<td id='jdltblknn' width='8%' style="padding-right:5px;">(${o.pricelist_id.currency_id.name or ''})</td>
				<td id='jdltblknn' width='10%'>(${o.pricelist_id.currency_id.name or ''})</td>
			</tr>
			<tr>
				<td id='grsbwhtbl' width='98%'  colspan="7"></td>
				<%totamt_shipment=0%>
				%for baris1 in get_prodline_group(o.order_line):
					<%
					qtyshipment=get_qtyshipment(baris1[17],baris1[27])
					# print baris1[17],"hahahahahahahahahahahahaah"
					# print baris1[27],"gagagagagagagagagaag"
					# print baris1[17],baris1[28] ,"xxxxaaaxaxaxaxaxaxxaxaxa"
					%>
					% if not baris1[28] or not (baris1[28] and baris1[5]==qtyshipment):
					<tr>
						<td id='isitbl' style="padding-top:5px;" width='15%'>
							${baris1[4] or ''}
						</td>
						<td id='isitbl' style="padding-top:5px;" width='51%'>
							${(baris1[19] or '').replace('\n','<br/>')} </br>
							${baris1[21] and baris1[20] or baris1[22] or ''} </br>
							%if o.goods_type=='finish':
								%if baris1[3]:
									Cone Weight : ${baris1[3]} &nbsp; Kg(s) </br>
								%else:
									Cone Weight : Standard </br>
								%endif
							%endif
							<%line_count+=4%>
							%if baris1[1]:
								<a id="font-capitalize" > packing : ${baris1[1] or ''}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[18]:
								<a id="font-capitalize" > packing details : ${baris1[18].replace('\n','<br/>')  or ''}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[2]:
								<a id="font-capitalize" > TPI : ${baris1[2] or ''}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[26]:
								<a id="font-capitalize" > TPM : ${baris1[26] or ''}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[13]:
								<a id="font-capitalize" > HS Code : ${baris1[13]}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[9]:
								<b>Last Shipment Date : ${xdate(baris1[9])}</b> </br>
								<%line_count+=1%>
							%else:
							%endif
							%if baris1[25]:
								<a id="font-capitalize" > ${baris1[25] or ''}</a></br>
								<%line_count+=1%>
							%endif
							%if baris1[15]:
								${baris1[15].replace('\n','<br/>')  or ''} 
								<%line_count+=1%>
							%endif	
						</td>
						<td id='isitbl' width='5%' style="padding-top:5px;padding-right:5px;" >
							%if baris1[6]=="KGS":
								${baris1[6]}
							%else:
								${baris1[6]}</br>(KGS)
							%endif
						</td>
						<td id='isitblknn' width='11%' style="padding-top:5px;padding-right:5px;" >
							%if baris1[6]=="KGS":
								${formatLang(baris1[5],digits=3) or 0.0}
							%else:
								${formatLang(baris1[5],digits=3) or 0.0}</br>(${formatLang(uom_to_kgs(baris1[5],baris1[24]),digits=3) or 0.0})
							%endif
						</td>
						<td id='isitblknn' width='8%' style="padding-top:5px;padding-right:5px;">
							%if baris1[6]=="KGS":
								%if o.pricelist_id.currency_id.name == "IDR":
									${formatLang(baris1[7],digits=2) or 0.0} 
								%else:
									${formatLang(baris1[7],digits=4) or 0.0} 
								%endif
							%else:
								%if o.pricelist_id.currency_id.name == "IDR":
									${formatLang(baris1[7],digits=2) or 0.0}</br>(${formatLang(price_per_kgs(baris1[7],baris1[24]),digits=2) or 0.0})
								%else:
									${formatLang(baris1[7],digits=4) or 0.0}</br>(${formatLang(price_per_kgs(baris1[7],baris1[24]),digits=4) or 0.0})
								%endif
							%endif
						</td>
						<td id='isitblknn' width='10%' style="padding-top:5px;">
							${formatLang(baris1[8],digits=2) or 0.0}
						</td>
						<%line_count+=4%>
					</tr>
						<%totamt_shipment+=baris1[8]%>
					%endif
				%endfor:
			<tr>
				<td></td><td></td><td id='grsbwhtbl' width='32%' colspan="4"></td>
			</tr>
			<tr>
				<td></td><td></td><td id="jdltbl" style="text-align:left;" colspan="2">Total (${o.pricelist_id.currency_id.name or ''}) :</td>
				<!--#<td id="jdltbl" style="text-align:right;">${formatLang(totline_qty)}</td>-->
				
				<td></td>
				<td id="jdltbl" style="text-align:right;">${formatLang(subtot_amt)}</td>
				<!-- <td id="jdltbl" style="text-align:right;">${formatLang(totamt_shipment)}</td> -->
			</tr>
			<tr>
				<td id='grsbwhtbl' width='98%' colspan="6"></td>
			</tr>
		</table>
		<div  style="font-weight:bold;text-transform:capitalize;">
		TOTAL AMOUNT : ${o.pricelist_id.currency_id.name or ''} ${terbilang} only
		</div>
		</br>				
		<%line_count+=2%>
		<div style="vertical-align:top;">
			%if o.note:
				<%line_count+=o.note.count('\n')%>				
				%if line_count > 35:	
					<!-- Halaman 2  -->
					<div id="footer">
			        	<table width='100%'>
			                <tr width='100%'>
			                    <td Style="border-bottom:1pt solid #A0A0A0;">
			                    </td>
			                    <td>
			                    </td>
			                    <td Style="border-bottom:1pt solid #A0A0A0;">
			                    </td>
			                </tr>
			                <tr width='100%'>
			                    <td width='30%' align='center' style="font-size:10px;">
			                        Initial of Buyer
			                    </td>
			                    <td width='40%'>
			                    </td>
			                    <td width='30%' align='center' style="font-size:10px;">
			                        Initial of Seller
			                    </td>
			                </tr>
			            </table>
			        </div>
					<div style="page-break-before:always;"></div>
					<table width="100%" cellspacing="0" cellpadding="0">
						<tr>
							</br>
							<td width="60%" style="vertical-align:top;">
								<table cellspacing="0" cellpadding="0">
									<tr>
										<td style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">Page 2</a></br></td>
									</tr>
								</table>
							</td>
							<td width="40%">
								<table id="borderwhite"  width="100%"  rules="all">
									<tr>
										<td id="lblrght" width="60%" >SC NO.</td><td id="borderwhite_rgt" width="40%">Date</td>
									</tr>
									<tr>
										<td id="borderwhite_btm">${o.name or ''}</td><td id="borderwhite_rgtbtm">${o.date_order or ''}</td>
									</tr>
								</table>
							</td>
						</tr>
					</table>
					</br>
				%endif
				</br>
				<a style="vertical-align:top;"><b id="jdltbl">Special Conditions :</b></br>
				 ${o.note.replace('\n','<br/>')} </a>
			%endif
		</div>
		<br/>
	</div> <!--content -->
	<div id="break2" style="vertical-align:top;">&nbsp;</div>
	<div id="break1" style="page-break-before: always;">
		<div id="footer">
			<a style="font-size:9px;">
				The above is subject to the General Terms and Conditions of sale downloadable from http://www.bitratex.com/download which is an integral part of this Sales Confirmation. Please sign and return one copy of Sales Confirmation as your acceptance within 2 working days or else it is considered as being fully accepted. 
			</a></br>
			<div style="border-bottom:2px dotted #000000;border-top:2px dotted #000000;font-size:9px;" >
				If our yarn is used with any yarns like lycra, spandex, filament or any other spun yarn from other suppliers at any stage of manufacturing, we shall not be liable for the quality of intermediate or final products unless it is clearly established that our yarn is the source of quality problem.
			</div>
			<br/>
        	<table width='100%'>
                <tr width='100%'>
                    <td width='30%' align='center' style="font-weight:bold;vertical-align:top;text-transform:uppercase;font-size:10px;">
                        Ordered & Accepted by
                    </td>
                    <td width='40%'>
                    </td>
                    <td  width='30%' align='center' style="font-weight:bold;font-size:10px;">
                        for <a style="text-align:left;font-weight:bold;vertical-align:top;text-transform:uppercase;font-size:10px;">PT. BITRATEX INDUSTRIES </a>
                    </td>
                </tr>
                <tr width='100%'>
                    <td align='center'><br/><br/><br/>
                        <b style="font-size:10px;">(BUYER)</b>
                    </td>
                    <td><br/><br/><br/>
                    </td>
                    <td align='center'><br/><br/><br/>
                        <b style="font-size:10px;">(SELLER)</b>
                    </td>
                </tr>
                <tr width='100%'>
                    <td Style="border-bottom:1pt solid #A0A0A0;">
                    </td>
                    <td>
                    </td>
                    <td Style="border-bottom:1pt solid #A0A0A0;">
                    </td>
                </tr>
                <tr width='100%'>
                    <td width='30%' align='center' style="font-size:10px;">
                        Authorized Signatory (Stamp & Sign)
                    </td>
                    <td width='40%'>
                    </td>
                    <td width='30%' align='center' style="font-size:10px;">
                        Authorized Signatory (Stamp & Sign)
                    </td>
                </tr>
            </table>
        </div>
	</div>
</div>
</body>
%endfor
</html>	
