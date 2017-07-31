<html>
<head>
	<style type="text/css">
		#title1 {
				font-family: Arial;
				font-size: 15px;
				font-weight: bold;
				text-transform: uppercase;
				text-align: center;
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
		#isitbl{
				page-break-inside: always;
		}
		#isitblknn{
				text-align: right;
				page-break-inside: always;
		}
		td {
		vertical-align:top;
		}
		#bwhtbl{text-transform: uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
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
			border-bottom: 1px solid #808080;
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
		.hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
}
		#txt1{
			text-align: center;
			text-transform: capitalize;
		}
			/*footer*/
/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        }
        #wrapper {
        /*min-height:100%;*/
        position:static;
        font-family: Verdana;
		font-size:9.5px;
		padding-top:10px;
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
	height:135px;
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
 		height:135px;
 		}
        .btsprg{

			    /*width:22em; */
			    /*border: 1px solid #000000;*/
			    word-wrap: break-word;
			    vertical-align:top;
			    margin-top:5px;
        }
		/*h2 {page-break-before: always;}*/
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

<body>
<%
def xupper(x):
	if isinstance(x, basestring):
		return x.upper()
	else:
		return x or ''

def xdate(x):
	try:
		x1 = x[:10]
	except:
		x1 = ''

	try:
		y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
	except:
		y = x
	return y
%>
% for o in objects:
<%
	# label=eval(o.label_print)	
	label = get_label(o)				
%>
	<div  id="wrapper">
		<div id="title1">
			<a style="border-bottom:1px solid;">${label.get('','Shipping Instruction')}</a> <br/>
		</div>
		<br/>
		<br/>
	<div id="content">
		<table width="100%" >
		<tr>
			<td width="33%" style="vertical-align:top;">

				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">${label.get('','Shipper')}<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							% if o.show_shipper_address:
								${(xupper(o.s_address_text and o.s_address_text or '')).replace('\n','<br/>')}
							% else:
								${xupper(o.shipper.name)} <br/>
								${xupper(o.shipper.street)} </br/>
								%if o.shipper.street2:
								${xupper(o.shipper.street2)} <br/>
								%endif
								${xupper(o.shipper.city)} &nbsp; ${xupper(o.shipper.zip)} , &nbsp;${o.shipper.country_id and xupper(o.shipper.country_id.name or '')}
							% endif
						</span>
				</div>
			% if o.show_consignee_address:
				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">${label.get('','Consignee')}<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
								<!-- #${xupper(o.picking_ids and o.picking_ids.notify and o.picking_ids.notify[0].name or '')} <br/> -->
							${(xupper(o.c_address_text and o.c_address_text or '')).replace('\n','<br/>') }
						</span>
				</div>
			%endif
			% if o.show_notify_address:
				<div class="btsprg" style="vertical-align:top;">
							<a id="lbl1">${label.get('','Notify Party/Final Buyer')}<a/></br>
							<span style="text-transform:uppercase;vertical-align:top;">
									<!-- #${xupper(o.picking_ids and o.picking_ids.notify and o.picking_ids.notify[0].name or '')} <br/> -->
								${(xupper(o.n_address_text and o.n_address_text or '')).replace('\n','<br/>') }
							</span>
				</div>
			%endif
			
			% if o.show_buyer_address:
				<div class="btsprg" style="vertical-align:top;">
							<a id="lbl1">${label.get('','Buyer')}<a/></br>
							<span style="text-transform:uppercase;vertical-align:top;">
								${(xupper(o.b_address_text and o.b_address_text or '')).replace('\n','<br/>') }
							</span>
				</div>
			%endif
			</td>
			<td width="33%">
				<div class="btsprg" style="vertical-align:top;">
							<a id="lbl1">${label.get('','Forwarder')}<a/></br>
							<span style="text-transform:uppercase;vertical-align:top;">
								${o.forwading and o.forwading.partner_id and o.forwading.partner_id.name or ''}
							</span>
				</div>
				<div class="btsprg" style="vertical-align:top;">
							<a id="lbl1">${label.get('','Transporter')}<a/></br>
							<span style="text-transform:uppercase;vertical-align:top;">
								<%p1s = []%>
				%for p in o.picking_ids:
					<%u1 = True%>
					<%p2 = p.trucking_company.name%>
					%for p1 in p1s:
						%if p1 == p2:
							<%u1 = False%>
							<%break%>
						%endif
					%endfor
					%if u1:
						<%p1s.append(p2)%>
						${p2}<br/> 				
					%endif
				%endfor
							</span>
				</div>
				<div class="btsprg" style="vertical-align:top;">
							<a id="lbl1">${label.get('','Booking No')}<a/></br>
							<span style="text-transform:uppercase;vertical-align:top;">
								${o.booking_no or ''} 
							</span>
				</div>
				<table id="borderwhite"  width="100%" style="border-collapse:collapse;">
						<tr>
							<td id="lblrght" width="50%" >Container</td><td id="borderwhite_rgt" width="50%">SEAL</td>
						</tr>
						%for container in o.picking_ids:
						<tr>
							<td id="borderwhite_btm">
								
									${container.container_number or ''} </br>
								
							</td>
							<td id="borderwhite_rgtbtm">
									${container.seal_number or ''} 
							</td>
						</tr>
						%endfor
				</table>
			

				%if o.picking_ids and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.lc_ids and o.picking_ids[0].sale_id.lc_ids[0].shipping_instruction_header:
								<div class="btsprg" style="vertical-align:top;margin-top:5px;">
										<a id="lbl1"> ${label.get('','Info LC')} </a> <br/>
										<span style="text-transform:uppercase;">
											${o.picking_ids and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.lc_ids and o.picking_ids[0].sale_id.lc_ids[0].shipping_instruction_header or ''}
										</span>
								</div>
				%endif
			</td>
			<td width="34%">
				<table id="borderwhite"  width="100%"  rules="all">
					<tr>
						<td id="lblrght" width="50%" >${label.get('','Shipping Instruction')}</td><td id="borderwhite_rgt" width="50%">Date</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.name or ''}</td>
						<td id="borderwhite_rgtbtm">${o.date_instruction or ''} </td>
					</tr>
				</table>
				<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
					<tr>
						<td id="lblrght" width="50%" >${label.get('','PEB No.')}</td><td id="borderwhite_rgt" width="50%">PEB Date</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.peb_no or ''}</td>
						<td id="borderwhite_rgtbtm">${o.peb_date or ''} </td>
					</tr>
				</table>
				
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;" >${label.get('','Port/Country of Destination')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							${xupper(o.port_to_desc)}
						</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">${label.get('','Port/Country of Origin')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							${xupper(o.port_from_desc)}
						</td>
					</tr>
				</table>
			</td>
		</tr>
		</table>
		</br>
<table id="borderwhite" width="100%" rules="all">
		<tr>
			<td id="lbl2" width="18%">Stuffing Date</td>
			<td id="lbl2" width="20%">Feeder vessel</td>
			<td id="lbl2" width="21%">connect vessel</td>
			<td id="lbl2" width="21%">freight</td>
			<td id="lbl2" width="20%" style="border-right:white;">Document</td>
		</tr>
		<tr>
			<td  id="txt1" width="18%" style="border-bottom:white;">${xdate(o.stuffing_date)}</td>
			<td id="txt1" width="20%" style="border-bottom:white;">${o.feeder_vessel or ''}</td>
			<td id="txt1" width="21%" style="border-bottom:white;">${o.connect_vessel or ''}</td>
			<td id="txt1" width="21%" style="border-bottom:white;">${o.freight or ''}</td>
			<td id="txt1" width="21%" style="border-right:white;border-bottom:white">${o.documentation or ''}</td>
		</tr>
</table>
</br>
<table  width='98%' >
	<!-- <table class='border1'  width='98%' cellspacing="0"> -->
		<tr>
			<!-- <td id='jdltbl' width='2%'></td> -->
			<td id='jdltbl' width='14%'></td>
			<td id='jdltbl' width='45%'></td>
			<td id='jdltbl' width='7%'  colspan="2"></td>
			<td id='jdltblknn' width='13%'>GR.WT</td>   
			<td id='jdltblknn' width='13%'>NT.WT</td>
			<td id='jdltblknn' width='8%'>VOLUME</td>
		</tr>
		<tr>
			<!-- <td id='jdltbl' width='2%'>SR.</td> -->
			<td id='jdltbl' width='14%' style="padding-left:5px;">Mark & NOS.</td>
			<td id='jdltbl' width='45%'>DESCRIPTION OF GOODS</td>
			<td id='jdltblknn' width='7%'  colspan="2">PACKAGES</td>
			<td id='jdltblknn' width='13%'>${o.picking_ids and o.picking_ids[0].move_lines and o.picking_ids[0] and o.picking_ids[0].move_lines[0].product_uom.name or ''}</td>
			<td id='jdltblknn' width='13%'>${o.picking_ids and o.picking_ids[0].move_lines and o.picking_ids[0] and o.picking_ids[0].move_lines[0].product_uom.name or ''}</td>
			<td id='jdltblknn' width='8%'>cbm</td>
		</tr>
		<tr>

			<td id='grsbwhtbl' width='98%'  colspan="7"></td>
		</tr>
			<%linecount = 0%>
			<%xgross_weight_sum = 0.0%>
			<%xnet_weight_sum = 0.0%>
			<%xvolume_sum = 0.0%>
			<% 
				qty_digit = 2
				uom = o.picking_ids and o.picking_ids[0].move_lines and o.picking_ids[0] and o.picking_ids[0].move_lines[0].product_uom.name or ''
				if uom == 'BALES':
					qty_digit = 4
				goods_lines = sorted([(x.sequence,x) for x in o.goods_lines],key=lambda k:k[0])
			%>
%for line in [g[1] for g in goods_lines]:
			<%xgross_weight_sum = xgross_weight_sum + line.gross_weight%>
			<%xnet_weight_sum = xnet_weight_sum + line.net_weight%>
			<%xvolume_sum = xvolume_sum + line.volume%>
		<tr style="page-break-inside:always;page-break-before:avoid;">
				<!-- <td id='isitbl' style="padding-top:5px;" width='2%'>
					{srno1}
				</td> -->
				<td id='isitbl' style="padding-top:5px;padding-left:5px;" >
					${(xupper(line.marks_nos)).replace('\n','<br/>')}
				</td>
				<td id='isitbl' style="padding-top:5px;" >
					${line.product_desc and line.product_desc.upper() or ''} </br>
					HS CODE : ${line.product_id and line.product_id.hscode or ''}
				</td>
				<td id='isitblknn' style="padding-top:5px;">
					${int(line.packages) or '' }
				</td>
				<td id='isitbl' style="padding-top:5px;">
					%if line.packing_type:
						${line.packing_type}
					%elif line.packing_type==False and (line.product_uop and line.product_uop.packing_type.name):
						${line.product_uop and line.product_uop.packing_type.name or ''}
					%else:
						''
					%endif
				</td>

				<td id='isitblknn' style="padding-top:5px;" >${ formatLang(line.gross_weight,digits=qty_digit)}</td>
				<td id='isitblknn' style="padding-top:5px;">
					${formatLang(line.net_weight,digits=qty_digit)}
				</td>
				<td id='isitblknn' style="padding-top:5px;">
					${formatLang(line.volume,digits=qty_digit) or '' }
				</td>
			</tr>
			%endfor
			<tr>
				<!-- <td></td> -->
				<td></td><td style="border-top: 1px dashed #808080;">${(o.desc_SIforBL or '').replace('\n','<br/>')}</td><td width='35%' colspan="5"></td>
			</tr>
			<tr>
				<!-- <td></td> -->
				<td></td><td></td><td id='grsbwhtbl' width='35%' colspan="5"></td>
			</tr>
			
			<tr>
				<!-- <td width='2%'></td> -->
				<td width='17%'></td>
				<!-- <td id="jdltbl" style="text-align:left;">total :</td> -->
				<td width='46%'></td>
				<td id="jdltbl">total</td><td></td>
				<td id="jdltbl" style="text-align:right;">${formatLang(xgross_weight_sum,digits=qty_digit)}</td>
				<td id="jdltbl" style="text-align:right;">${formatLang(xnet_weight_sum,digits=qty_digit)}</td>
				<td id="jdltbl" style="text-align:right;">${xvolume_sum}</td>
			</tr>

			<tr>
				<td id='grsbwhtbl' width='98%' colspan="7"></td>
			</tr>

		</table>
		<script>
			var tablex = document.getElementById("data_container");
			var tablex_height = tablex.offsetHeight
			var container=document.getElementById("empty_container")
			container.height = (20-tablex_height) + "px";
			//container.innerHTML = 1200-tablex_height
		</script>
			%if o.note:
				<table width="100%" style="margin-top:5px;">
						<tr>
							<td width="100%"> 
								<a style="font-weight:bold;">${label.get('','NOTE :')}</a>
									<a>${o.note.replace('\n','<br/>')} </a>
							</td>
						</tr>
				</table>
			%endif
	</div> <!--content -->
	<div id="break2" style="vertical-align:top;">&nbsp;</div>
	<div id="break1" style="page-break-before: always;">
	<div id="footer">
			<br/>
			<table width='100%'>
				<tr width='100%'>
					<td id='lbl' width='30%' align='center'>
						&nbsp;
					</td>
					<td width='40%'>
					</td>
					<td  width='30%' align='center' style="font-weight:bold;">
						for <a id='lbl1'>${o.shipper.partner_id and o.shipper.partner_id.name or ''}</a>
					</td>
				</tr>
				<tr width='100%'>
					<td align='center'><br/><br/><br/>
						<b>&nbsp;</b>
					</td>
					<td><br/><br/><br/>
					</td>
					<td align='center'><br/><br/><br/>
						<b>&nbsp;</b>
					</td>
				</tr>
				<tr width='100%'>
					<td>
					</td>
					<td>
					</td>
					<td Style="border-bottom:1pt solid #808080;">
					</td>
				</tr>
				<tr width='100%'>
					<td width='30%' align='center'>
						&nbsp;
					</td>
					<td width='40%'>
					</td>
					<td  width='30%' align='center'>
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

