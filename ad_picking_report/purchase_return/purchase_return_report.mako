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
		#hdr2{
			text-align: center;
			/*font-weight: bold;*/
			font-size: 11px;
			/*margin-top:40px;*/
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
		#txt1{
		text-align: center;
		padding-left:5px;
}
#borderwhite{
		border-top:white;
		border-left:white;
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
        }
        #wrapper {
        min-height:100%;
        position:static;
        font-family: Arial;
		font-size:10px;
		padding-top:40px;
        }
        #header {
        padding:10px;
        background:#5ee;
        }
        #content {
        padding:10px;
        width:100%;
        padding-bottom:50px; /* Height of the footer element */ 
        /*background:green;*/
        /*height:910px;*/
        }
        #footer {
        width:100%;
        height:50px;
        position:absolute;
        bottom:0;
        left:0;
        /*background:#ee5;*/
        }
#bwhtblup1{
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		border-top: 1px solid #808080;
		vertical-align:top;
}
#break1{
	position:relative;
	display: block;
	}
 #break2{
 		/*background: yellow;*/
 		bottom:60;
 		height:100px;
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
		y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
	except:
		y = x1
	return y
%>
<body>
<div  id="wrapper">
% for o in objects:
	<div id="hdr2">
		<a>PT. BITRATEX INDUSTRIES</a><br/>
	</div>
	<div id="hdr1">
		<a style="border-bottom:1px solid;">PURCHASE RETURN NOTE</a> <br/>
	</div>
	<div id="content">
	
					<table width="100%" >
					<tr>
						<td width="35%" style="vertical-align:top;">
							<table>
								<tr>
									<td  style="vertical-align:top;"><a id="lbl1">Return To</a></br>
									<span style="text-transform:uppercase;">
										${o.partner_id.name or ''} <br/>
										${get_address(o.partner_id) or ''}
									</span>

									</td>
								</tr>
							</table>
						</td>
						<td width="35%" style="vertical-align:top;">
							&nbsp;
						</td>
						<td width="30%">
							<table id="borderwhite"  width="100%"  rules="all">
								<tr>
									<td id="lblrght" width="60%" >PRN NO.</td>
									<td id="borderwhite_rgt" width="40%">Date</td>
								</tr>
								<tr>
									<td id="borderwhite_btm" style="font-weight:bold;">${o.name or ''}</td><td id="borderwhite_rgtbtm">${xdate(o.date_done) or ''}</td>
								</tr>
							</table>
							
						</td>
					</tr>
				</table>
			</br>
				<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="lbl2" width="13%">PO NO.</td>
							<td id="lbl2" width="12%">PO DATE</td>
							<td id="lbl2" width="12%">DO NO.</td>
							<td id="lbl2" width="12%">DO DATE</td>
							<!-- <td id="lbl2" width="13%">AP NO</td>
							<td id="lbl2" width="12%">AP DATE</td>
							<td id="lbl2" width="13%">INV. NO</td>
							<td id="lbl2" width="13%">INV. DATE</td> -->
						</tr>
						<tr>
							<td  id="txt1" width="13%" style="border-bottom:white;">
								${o.move_lines and o.move_lines[0].move_history_ids and o.move_lines[0].move_history_ids[0].purchase_id and o.move_lines[0].move_history_ids[0].purchase_id.name}
								
								</td>
							 <td id="txt1" width="12%" style="border-bottom:white;">${o.move_lines and o.move_lines[0].move_history_ids and o.move_lines[0].move_history_ids[0].purchase_id and o.move_lines[0].move_history_ids[0].purchase_id.date_order}</td>
							<td id="txt1" width="12%" style="border-bottom:white;">${o.surat_jalan_number or ''}</td>
							<td id="txt1" width="12%" style="border-bottom:white;"></td>
							<!-- <td id="txt1" width="13%" style="border-bottom:white;">&nbsp;</td>
							<td id="txt1" width="12%" style="border-bottom:white;">&nbsp;</td>
							<td id="txt1" width="12%" style="border-bottom:white;">&nbsp;</td> -->
						</tr>
					</table>

			</br>
				<%
				# totamt=get_matline_amt(o.move_lines)
				totamt=0
				sn=1
				%>
				<table class='border1'  width='98%' cellspacing="0">
							<tr>
								<td id='jdltbl' width='3%'></td>
								<td id='jdltbl' width='10%'></td>
								<td id='jdltbl' width='15%'></td>
								<td id='jdltbl' width='30%'></td>
								<td id='jdltbl' width='8%'>Store</td>
								<td id='jdltblknn' width='6%'></td>
								<td id='jdltblknn' width='6%'></td>
								<td id='jdltblknn' width='8%'>Price</td>
								<td id='jdltblknn' width='12%'>amount</td>
							</tr>
							
							<tr>
								<td id='jdltbl' width='3%'>SN.</td>
								<td id='jdltbl' width='10%'>IR NO.</td>
								<td id='jdltbl' width='15%'>Item Code</td>
								<td id='jdltbl' width='30%'>Material</td>
								<td id='jdltbl' width='8%'>Location</td>
								<td id='jdltbl' width='6%' style="padding-left:8px;" >unit</td>
								<td id='jdltblknn' width='6%'>quantity</td>
								<td id='jdltblknn' width='8%'>${o.invoice_id and o.invoice_id.currency_id and o.invoice_id.currency_id.name or ''}</td>
								<td id='jdltblknn' width='12%'>${o.invoice_id and o.invoice_id.currency_id and o.invoice_id.currency_id.name or ''}</td>
							</tr>
							<tr>
								<td id='grsbwhtbl' width='98%'  colspan="9"></td>

							<% sumitem=0 %>
					%for baris in get_movelines_group(o.move_lines):
							<% sumitem+=1 %>
							<%
								net_price_unit=get_price_unit(baris[13])
							%>
							<tr>
								<td id='isitbl' style="padding-top:5px;" >
									${sn}
								</td>
								<td id='isitbl' style="padding-top:5px;">
									${baris[10]}
								</td>
								<td id='isitbl' style="padding-top:5px;">
									${baris[8] or ''}
								</td>
								<td id='isitbl' style="padding-top:5px;" >
									${baris[5] or baris[5] or ''}	
									
								</td>
								<td id='isitbl'  style="padding-top:5px;" >${baris[12] or ''}</td>
								<td id='isitbl'  style="padding-top:5px;padding-left:8px;">
									${baris[4] or ''}
								</td>
								<td id='isitblknn' style="padding-top:5px;">
									${formatLang(baris[3],digits=4) or ''}
								</td>
								<td id='isitblknn'  style="padding-top:5px;">
									${formatLang(net_price_unit,digits=2)}
								</td>
								<td id='isitblknn' style="padding-top:5px;">
									${formatLang(net_price_unit*baris[3],digits=2)}
								</td>
							</tr>
							<%
							sn+=1
							totamt+=net_price_unit*baris[3]
							%>
					%endfor:
							<tr>
								<td id='grsbwhtbl' width='40%' colspan="9"></td>
							</tr>
							<tr>
								<td colspan="3">${sumitem} &nbsp; ITEM(S) &nbsp; <a id="jdltbl" style="text-align:left;">Total  : </a></td>
								<td></td>
								<td></td>
								<td></td>
								<td></td>
								<td></td>
								<td id="jdltbl" style="text-align:right;">${formatLang(totamt,digits=2)}</td>
							</tr>
							<tr>
								<td id='grsbwhtbl' width='98%' colspan="9"></td>
							</tr>

					</table>
					<%
							terbilang=call_num2word(totamt,"en") 
					%>
					
					<div  style="font-weight:bold;text-transform:capitalize;">
					TOTAL AMOUNT :  ${o.invoice_id and o.invoice_id.currency_id and o.invoice_id.currency_id.name or ''} ${terbilang} only
					</div>
					</br>
					<div style="vertical-align:top;">
							%if o.note:
								<a style="vertical-align:top;"><b id="jdltbl">Remarks :</b></br>
								  </a>
									${(o.note or '').replace('\n','<br/>')}
							%endif
					</div>
					</div>
					
					<div>

					</div>
					
					<br/>
	</div>
	<div id="break2" style="vertical-align:top;">&nbsp;</div>
	<div id="break1" style="page-break-before: always;">
	<div id="footer">					
	<table width="100%" align="top">
	<tr>
		<td id="bwhtblup1" width="15%">Prepared By</td><td width="5%" style="border-top:none;">&nbsp;</td><td id="bwhtblup1" width="15%">Checked by</td><td width="5%" style="border-top:none;">&nbsp;</td><td id="bwhtblup1" width="15%">Bill Passed By</td><td width="3%" style="border-top:none;">&nbsp;</td><td id="bwhtblup1" width="17%">Bill Approved by</td>
	</tr>
	<tr>
		<td id="bwhtbl2" colspan="9" width="100%"></td>
	</tr>
	</table>					
	</div>
</div>
%endfor
</div>
</body>
</html>	
