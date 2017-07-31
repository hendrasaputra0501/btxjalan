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
		#grsatstbl{
			border-top: 1px solid #808080;
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

		.left5px{padding-left:5px;}
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
		font-size:10px;
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
	height:130px;
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
 		height:130px;
 		}
     
#bwhtblup1{
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		border-top: 1px solid #808080;
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
		<a style="border-bottom:1px solid;">QUALITY CERTIFICATE</a> <br/>
		<span>${o.title_header_form or ''}</span>
		<span></span>
	</div>
	<table width="100%" >
		<tr>
			<td width="30%" style="vertical-align:top;">
				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">
						 Shipper</a></br>

						<span style="text-transform:uppercase;">
							%if o.sale_ids and o.sale_ids[0].company_id and o.sale_ids[0].company_id.name:
								${o.sale_ids and o.sale_ids[0].company_id and o.sale_ids[0].company_id.name or ''} <br/>
							%endif
							${get_address(o.sale_ids and o.sale_ids[0].company_id and o.sale_ids[0].company_id.partner_id) or ''}

						</span>
				</div>
					%if o.sale_ids and o.sale_ids[0].consignee and o.sale_ids[0].consignee.name:
						<div class="btsprg" style="vertical-align:top;margin-top:5px;">
							<a id="lbl1">
							 CONSIGNEE</a></br>
							<span style="text-transform:uppercase;">
								${o.sale_ids and o.sale_ids[0].consignee and o.sale_ids[0].consignee.name or ''} </br>
								${get_address(o.sale_ids and o.sale_ids[0].consignee and o.sale_ids[0].consignee.partner_id) or ''}
							</span>
						</div>
					% endif
					%if o.sale_ids and o.sale_ids[0].notify and o.sale_ids[0].notify.name:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">
							NOTIFY PATY</a></br>
						<span style="text-transform:uppercase;">
							${get_address(o.sale_ids and o.sale_ids[0].notify and o.sale_ids[0].notify.partner_id) or ''}
						</span>
					</div>
					%endif
			</td>
			<td width="40%">
			</td>
			<td width="30%">
				<table id="borderwhite"  width="100%"  rules="all">
					<tr>
						<td id="lblrght" width="50%" >CERTIFICATE NO</td><td id="borderwhite_rgt" width="50%">Date</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.name or ''}</td>
						<td id="borderwhite_rgtbtm">${o.date or ''}</td>
					</tr>
				</table>
				<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
					<tr>
						<td id="lblrght" width="50%" > SC. NO.</td><td id="borderwhite_rgt" width="50%">LC. NO.</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.sale_ids and o.sale_ids[0].name or ''}</td>
						<td id="borderwhite_rgtbtm">${o.sale_ids and o.sale_ids[0].lc_ids and o.sale_ids[0].lc_ids[0].lc_number or ''}</td>
					</tr>
				</table>
				
				<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
					<tr>
						<td id="lblrght" width="50%" >INVOICE NO.</td><td id="borderwhite_rgt" width="50%">BL. NO.</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.invoice_id and o.invoice_id.internal_number or ''}</td>
						<td id="borderwhite_rgtbtm">
							${o.sale_ids and o.sale_ids[0].invoice_ids and o.sale_ids[0].invoice_ids[0].bl_number or ''}
						</td>
					</tr>
				</table>

			</td>
		</tr>
		</table>
	</br>
		<div class="left5px">
			<span id="lbl1">PRODUCT</span></br>
			${o.product_id.name or ''}
		</div>
		<div class="left5px">
			${o.remarks or ''}
			
		</div>
	</br>
		<table  width="100%">
			<tr>
				<th id="jdltbl" style="text-align:left;" width="70%">PARAMETER</th><th id="jdltbl" style="text-align:right;"  width="30%">VALUE</th>
			</tr>
			<tr>
				<td id="grsatstbl" colspan="2" ></td>
			</tr>
		%for baris in o.uster_line_ids:
			<tr>
				<td style="border-bottom: 1px dashed #808080;">${baris.desc}</td><td style="text-align:right;border-bottom: 1px dashed #808080" >${baris.value or 0}</td>
			</tr>
			<!-- <tr>
				<td id="grsbwhtbl" colspan="2" style="border-bottom: 1px dashed #808080;"></td>
			</tr> -->
			
		%endfor:
			<tr>
				<td id="grsatstbl" colspan="2" ></td>
			</tr>
		</table>
</div> <!--content -->
%if o.note:
	<table>
		<tr>
			<td>REMARKS :</td>
		</tr>
		<tr>
			<td>${o.note or ''}</td>
		</tr>
	</table>
	%endif
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
						for <a id='lbl1'> ${get_company()}
						
					</a>
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
