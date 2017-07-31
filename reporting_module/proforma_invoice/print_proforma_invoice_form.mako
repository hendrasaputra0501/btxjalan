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

.top-margin{
	padding-top:5px;
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

        .btsprg{

			    width:25em; 
			    /*border: 1px solid #000000;*/
			    word-wrap: break-word;
			    vertical-align:top;
			    margin-top:5px;
        }
        
        .bank{
        		list-style-type: none;
        		text-decoration: none;
        		vertical-align: bottom;
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
% for o in objects:

<body>
	<div  id="wrapper">
		<div id="title1">
			<a style="border-bottom:1px solid;">Proforma Invoice</a> <br/>
		</div>
		<br/>
		<br/>
	<div id="content">

		
		</div>

		<table width="100%" >
		<tr>
			<td width="65%" style="vertical-align:top;">
				<div class="btsprg" style="vertical-align:top;">
						<a style="font-weight:bold;text-transform:uppercase;">Shipper<a/></br>
						<span style="text-transform:uppercase;">
								${o.shipper_id and o.shipper_id.name or ''}<br/>
								%if o.s_use_custom_address:
									${(o.s_address_text).replace('\n','</br>')}
								%else:
									${get_address(o.shipper_id) or ''}
								%endif
						</span>
				</div>

				<div class="btsprg" style="vertical-align:top;">
						<a style="font-weight:bold;text-transform:uppercase;">Consignee<a/></br>
						<span style="text-transform:uppercase;">
							${o.consignee_partner_id and o.consignee_partner_id.name or ''}<br/>
							%if o.c_use_custom_address:
								${(o.c_address_text).replace('\n','</br>')}
							%else:
								${get_address(o.consignee_partner_id or o.partner_id) or ''}
							%endif
						</span>
				</div>

				<div class="btsprg" style="vertical-align:top;">
						<a style="font-weight:bold;text-transform:uppercase;">Notify Party<a/></br>
						<span style="text-transform:uppercase;">
							${o.notify_partner_id and o.notify_partner_id.name or (o.partner_id and o.partner_id.name or '')}<br/>
								%if o.n_use_custom_address:
									${(o.n_address_text).replace('\n','</br>')}
								%else:
									${get_address(o.notify_partner_id or o.partner_id) or ''}
								%endif
						</span>
				</div>
			</td>
			<td width="35%">
					<table id="borderwhite"  width="100%"  rules="all">
						<tr>
							<td id="lblrght" width="57%" >Proforma Invoice No.</td>
							<td id="borderwhite_rgt" width="43%">Date</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${o.sale_id and o.sale_id.name or ''} - 
								${o.sequence}</td>
							<td id="borderwhite_rgtbtm">${o.date_invoice or ''}</td>
						</tr>
					</table>
					<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
						<tr>
							<td id="lblrght" width="57%" >SC NO.</td>
							<td id="borderwhite_rgt" width="43%">Date</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${o.sale_id and o.sale_id.name or ''}</td>
							<td id="borderwhite_rgtbtm">${o.sale_id and o.sale_id.date_order or ''}</td>
						</tr>

				<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Customer Reff</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
							${o.sale_id and o.sale_id.client_order_ref or ''}
						</tr>
					</table>
						
				<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Delivery Terms</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
							${o.sale_id and o.sale_id.incoterm and o.sale_id.incoterm.code or ''}
							
						</tr>
						
					</table>
				</td>
			</tr>
			</table>


		<table id="data_container" class='border1 top-margin'  width='98%' cellspacing="0" style="padding-top:5px;">
				<tr>
					<td id="lbl2" colspan="2"></td><td id="jdltblknn" >Quantity</td>
					<td id='jdltblknn'>Price</td>
					<td id='jdltblknn'>amount</td>
				</tr>
				<tr>
					<td id='jdltbl' width='59%' colspan="2">Product</td>
					<td id='jdltblknn' width='14%'>${o.invoice_line and o.invoice_line.uom_id[0] and o.invoice_line.uom_id[0].name or ''}</td>
					<td id='jdltblknn' width='12%'>${o.currency_id and o.currency_id.name or ''} / ${o.invoice_line and o.invoice_line.uom_id[0] and o.invoice_line.uom_id[0].name or ''}</td>
					<td id='jdltblknn' width='13%'>${o.currency_id and o.currency_id.name or ''}</td>
				</tr>
				<tr>
					<td id='grsbwhtbl'  width='98%' colspan="5"></td>
				</tr>
		<%
		vardeflocsumqty,varsumloctotprice,varsumtotprice=get_invline_totprice(o.invoice_line)
		%>
		% for baris in o.invoice_line:

				<tr>
					<td id='isitbl' style="padding-top:5px;" width='59%' colspan="2">
						${(baris.name or '').replace('\n','<br/>')}
					</td>
					<td id='isitblknn' style="padding-top:5px;" width='14%'> ${formatLang(baris.quantity,digits=4)}</td>
					<td id='isitblknn' style="padding-top:5px;" width='12%'>
						${formatLang(baris.price_unit,digits=4)} 
					</td>
					<td id='isitblknn' style="padding-top:5px;" width='13%'>
						${formatLang(baris.quantity*baris.price_unit)} 
					</td>
				</tr>
		%endfor:
				<tr>
					<td id="empty_container" colspan="5">
					</td>
				</tr>
				<tr>
					<td width='58%'>&nbsp;</td><td id='grsbwhtbl' width='39%' colspan="4">&nbsp;</td>
				</tr>
				<tr>
					<td width='58%'>&nbsp;</td>
					<td id="jdltbl"  width="1%" >Total :</td>
					<td id="jdltbl" style="text-align:right;" width='14%'>${formatLang(vardeflocsumqty,digits=4)}</td>
					<td width='12%'>&nbsp;</td>
					<td id="jdltbl" style="text-align:right;"  width='13%'>${formatLang(varsumloctotprice)} </td>
				</tr>
				<tr>
					<td id='grsbwhtbl' width='98%' colspan="5"></td>
				</tr>
		</table>
		<script>
			var tablex = document.getElementById("data_container");
			var tablex_height = tablex.offsetHeight
			var container=document.getElementById("empty_container")
			container.height = (20-tablex_height) + "px";
			//container.innerHTML = 1200-tablex_height
		</script>
		<%
		terbilang=call_num2word(varsumtotprice,'en')
		%>
		<div  style="font-weight:bold;text-transform:capitalize;">
		TOTAL AMOUNT : ${o.currency_id.name or ''} &nbsp; ${terbilang} only
		</div>
			<div style="padding-top:5px;">
			%if o.note:
				<a style="font-weight:bold;text-transform:uppercase;">Remarks :</a>
				</br>${(o.note or '').replace('\n','<br/>')} 
				</br>
			%endif
				
			</br>
				<span id="jdltbl">PAYMENT DETAILS :</span>
				<table>
					<tr>
						<td width="100%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">Remit To<a/></br>
							${o.remit_to and o.remit_to.name or ''}
							%if o.remit_to and o.remit_to.bic:
								</br> Swift : ${o.remit_to and o.remit_to.bic or ''}
							%endif
						</td>
					</tr>

					<tr>
						<td width="100%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">For Credit to<a/></br>
							${o.credit_to and o.credit_to.name or ''}
							%if o.credit_to and o.credit_to.bic:
								</br> Swift : ${o.credit_to and o.credit_to.bic or ''}
							%endif
						</td>
					</tr>
					<tr>
						<td width="100%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">Favoring<a/></br>
							${o.company_bank_account and o.company_bank_account.partner_id and o.company_bank_account.partner_id.name or ''}
							%if o.company_bank_account and o.company_bank_account.acc_number:
								</br> US$ A/C No : ${o.company_bank_account and o.company_bank_account.acc_number or ''}
							%endif
						</td>
					</tr>
				</table>
			</div>
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
						for <a id='lbl1'>${o.company_id and o.company_id.name or ''}</a>
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

