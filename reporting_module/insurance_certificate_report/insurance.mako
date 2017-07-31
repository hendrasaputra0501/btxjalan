<html>
<head>
	<style type="text/css">
		#title1 {
				font-family: Arial;
				font-size: 15px;
				font-weight: bold;
				text-transform: uppercase;
				text-align: center;
				padding-top:80px;
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
	height:210px;
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
 		height:210px;
 		}
     
        .bank{
        		list-style-type: none;
        		text-decoration: none;
        		vertical-align: bottom;
        }
.btsprg{

			    width:22em; 
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
		# y = datetime.strptime(x1,'%Y-%m-%d').strftime("%Y-%m-%d")
		# y = datetime.strptime(x1,'%Y-%m-%d').strftime("%d %b %Y")
		y = datetime.strptime(x1,'%d/%m/%Y').strftime("%d %b %Y")
	except:
		y = x1
	return y
%>



<% from ad_amount2text_idr import amount_to_text_id %> 
<%	from openerp.tools import amount_to_text_en %>
% for ins in objects:
<body>
	<div  id="wrapper">
		<div id="title1">
			<span>${ins.title_document_header_one or 'Insurance Policy Instruction'}</span> <br/>
			<span style="border-top:1px solid;">${ins.title_document_header_two or ''}</span>
		</div>
		<br/>
		<br/>
	<div id="content">
		<table width="100%" >
		<tr>
			<td width="30%" style="vertical-align:top;">
				<table>
					<tr>
						<td rowspan="5" width="70%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">Insured By<a/></br>
						%if ins.show_insuredby_address:
							${ins.address_text or ''}
						%else:
							${ins.insured.name} </br>
							${get_address(ins.insured) or ''}
							%endif
						</td>
					</tr>
				</table>

				<!--  CONSIGNEE  -->
				% if ins.shipper:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">Shipper<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							${(ins.shipper  or '').replace('\n','<br/>') }
						</span>
				</div>
				%endif

				<!--  CONSIGNEE  -->
				% if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.show_consignee_address:
				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">Consignee<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							${(ins.invoice_id.picking_ids[0].container_book_id.c_address_text  or '').replace('\n','<br/>') }
						</span>
				</div>
				% elif ins.consignee:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">Consignee<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							${(ins.consignee  or '').replace('\n','<br/>') }
						</span>
				</div>
				%endif


				<!--  NOTIFY  -->
				% if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.show_notify_address:
				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">Notify<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							${(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.n_address_text  or '').replace('\n','<br/>') }
						</span>
				</div>
				% elif ins.notify:
				<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">Notify<a/></br>
						<span style="text-transform:uppercase;vertical-align:top;">
							${(ins.notify  or '').replace('\n','<br/>') }
						</span>
				</div>
				%endif
			</td>

			<td width="40%" style="vertical-align:top;">
				%if ins.desc_surveyor:
					<table>
						<tr>
							<td rowspan="5" width="70%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;">Surveyor/Agent<a/></br>
							${ins.desc_surveyor or ''}
						</tr>
					</table>
				%endif
				%if ins.claim_data:
					<table style="margin-top:5px;">
							<tr>
								<td rowspan="5" width="70%" style="vertical-align:top;">
									<span style="font-weight:bold;text-transform:uppercase;">${ins.claim_title or ''}</span></br>
									${ins.claim_data or ''}
							</tr>
					</table>
				%endif
				%if ins.value_at:
					<table style="margin-top:5px;">
							<tr>
								<td rowspan="5" width="70%" style="vertical-align:top;">
									<span style="font-weight:bold;text-transform:uppercase;">Claim Value</span></br>
									${ins.value_at or ''}
								</td>
							</tr>
					</table>
				%endif
				<table style="margin-top:5px;">
						<tr>
							<td rowspan="5" width="70%" style="vertical-align:top;">
								<span style="font-weight:bold;text-transform:uppercase;">Deductable details</span></br>
								${ins.deductable_premi or ''}
							</td>
						</tr>
				</table>
				<table style="margin-top:5px;">
						<tr>
							<td rowspan="5" width="70%" style="vertical-align:top;">
								<span style="font-weight:bold;text-transform:uppercase;">Vessel/conveyance</span></br>
							${ins.vessel_conveyance or ''}
							</td>
						</tr>
				</table>
				<table style="margin-top:5px;">
						<tr>
							<td rowspan="5" width="70%" style="vertical-align:top;">
								<span style="font-weight:bold;text-transform:uppercase;">Connect Vessel</span></br>
							${ins.connect_vessel or ''}
							</td>
						</tr>
				</table>
			</td>
			<td width="30%">
					<table id="borderwhite"  width="100%"  rules="all">
						<tr>
							<td id="lblrght" width="45%" >Policy No.</td>
							<td id="borderwhite_rgt" width="55%">Date</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${ins.name}</td>
							<td id="borderwhite_rgtbtm">
								%if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
									${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True))}
								%elif ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids:
									${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True))}
								%elif ins.entry_date!='False':
									${xdate(formatLang(ins.entry_date,date=True))}
								%endif
								</td>
						</tr>
					</table>

					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Open Cover No.</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
							%if ins.open_cover_no:
								${ins.open_cover_no or ''}
							%else:
								&nbsp;
							%endif
							
						</tr>
					</table>

					<table id="borderwhite"  width="100%"  rules="all">
						<tr>
							<td id="lblrght" width="45%" >SC NO.</td>
							<td id="borderwhite_rgt" width="55%">LC No.</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${ins.contract_number or ''}</td>
							<td id="borderwhite_rgtbtm">${ins.lc_number or ''}</td>
						</tr>
					</table>

					<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
						<tr>
							<td id="lblrght" width="45%" >B/L NO.</td>
							<td id="borderwhite_rgt" width="55%">Date of Sailing</td>
						</tr>
						<tr>
							<td id="borderwhite_btm">${ins.bl_number or ''}</td>
							<td id="borderwhite_rgtbtm">
								%if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
									${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True))}
								%elif ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids:
									${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True))}
								%elif ins.entry_date!='False':
									${xdate(formatLang(ins.entry_date,date=True))}
								%endif
							</td>
						</tr>
					</table>
						
					
					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Voyage from</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
								${ins.voyage_from or ''}
								
							</br>
						</tr>
					</table>
					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Transhipment</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
								${ins.transhipment or ''}
							</br>
						</tr>
					</table>
					<table id="borderwhite" width="100%" rules="all">
						<tr>
							<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Voyage to</td>
						</tr>
						<tr>
							<td id="borderwhite_rgtbtm">
								${ins.voyage_to or ''}
							</br>
						</tr>
					</table>
				</td>
			</tr>
			</table>

		<table id="data_container" class='border1 top-margin'  width='98%' cellspacing="0" style="padding-top:5px;">
				<tr>
					<td id="lbl2" colspan="3"></td><td id="jdltblknn"></td><td id="jdltblknn"></td><td id='jdltblknn'>amount</td>
				<tr>
					<td id='jdltbl' width='13%'>Invoice No.</td>
					<td id='jdltbl' width='58%' colspan="2">Product / interest</td>
					<td id='jdltblknn' width='10%'>Quantity</td>
					<td id='jdltbl' width='8%' style="padding-left:5px;">unit</td>
					<td id='jdltblknn' width='9%'>(${ins.currency_id.name or ''})</td>
				</tr>
				<tr>
					<td id='grsbwhtbl'  width='98%' colspan="6"></td>
				</tr>
		
		%for baris in ins.product_ids:

				<tr>
					<td id='isitbl' style="padding-top:5px;" width='13%'>
						${baris.invoice_id and baris.invoice_id.internal_number or baris.invoice_id.number or ''}
					</td>
					<td id='isitbl' style="padding-top:5px;" width='58%' colspan="2"> 
						${baris.invoice_line_id and baris.invoice_line_id.name or (baris.name and baris.name.replace('\n','<br/>') or '')}
					</td>
					<td id='isitblknn' style="padding-top:5px;" width='10%'>
						${baris.quantity or ''} &nbsp; 
					</td>
					<td id='isitbl' style="padding-top:5px;padding-left:5px;" width='8%'>
						${baris.uom_id and baris.uom_id.name or ''}
					</td>
					<td id='isitblknn' style="padding-top:5px;" width='9%'>
						${baris.price_subtotal or ''}
					</td>
				</tr>
		%endfor
				<tr>
					<td id="empty_container" colspan="6">
					</td>
				</tr>
				<tr><td width='35%' colspan="2"></td>
					<td id='grsbwhtbl' width='63%' colspan="4"></td>
				</tr>
				<tr>
					<td id="jdltbl"  width="12%"></td>
					<td id="jdltbl"  width="22%"></td>
					<td id="jdltbl"  width="37%">Invoice Total (${ins.currency_id.name}) :</td>
					<td id="jdltbl" style="text-align:right;" width='10%'></td>
					<td id="jdltbl" style="text-align:right;" width='8%'></td>
					<td id="jdltbl" style="text-align:right;"  width='9%'>${formatLang(ins.amount_total,digits=2)}</td>
				</tr>
				<tr>
					<td id="jdltbl"  width="12%"></td>
					<td id="jdltbl"  width="22%"></td>
					<td id="jdltbl"  width="37%">Add: Tolerance Margin (10%) :</td>
					<td id="jdltbl" style="text-align:right;" width='10%'></td>
					<td id="jdltbl" style="text-align:right;" width='8%'></td>
					<td id="jdltbl" style="text-align:right;"  width='9%'>${formatLang(ins.amount_total*0.1,digits=2)}</td>
				</tr>
				<tr><td width='35%' colspan="2"></td>
					<td id='grsbwhtbl' width='63%' colspan="4"></td>
				</tr>
				<tr>
					<td id="jdltbl"  width="12%"></td>
					<td id="jdltbl"  width="22%"></td>
					<td id="jdltbl"  width="37%">sum insured (${ins.currency_id.name}) :</td>
					<td id="jdltbl" style="text-align:right;" width='10%'></td>
					<td id="jdltbl" style="text-align:right;" width='8%'></td>
					<td id="jdltbl" style="text-align:right;border-bottom:1px solid #808080;"  width='9%'> <a>${formatLang(ins.insured_amount,digits=2)}</a></td>
				</tr>
				<tr>
					<td id="jdltbl"  width="12%"></td>
					<td id="jdltbl"  width="22%"></td>
					<td id="jdltbl"  width="37%">
						Rate : ${formatLang(ins.premi_rate,4)}<br/>
						%if ins.paid and ins.show_premi_rate:
							Premium Paid (${formatLang(ins.insured_amount,2)} X ${formatLang(ins.premi_rate,4)}% ) :
						%elif ins.paid==False and  ins.show_premi_rate:
							Premium (${ins.currency_id.name or ''} ${formatLang(ins.insured_amount,2)} X ${formatLang(ins.premi_rate,4)}% ${ins.currency_id.name or ''}) :
						%elif ins.paid and ins.show_premi_rate==False:
							Premium Paid :
						%elif ins.paid==False and ins.show_premi_rate==False:
							Premium :
						%endif
						</td>
					<td id="jdltbl" style="text-align:right;" width='10%'></td>
					<td id="jdltbl" style="text-align:right;" width='8%'></td>
					<td id="jdltbl" style="text-align:right;vertical-align:bottom;" width='9%'>${formatLang(ins.insured_amount*ins.premi_rate/100,digits=2)}</td>
				</tr>
				<tr>
					<td id='grsbwhtbl' width='98%' colspan="6"></td>
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
		terbilang=call_num2word(ins.insured_amount,'en')
		%>
					
		<div  style="font-weight:bold;text-transform:uppercase;">
		Sum Insured : ${ins.currency_id.name or ''} <a style="text-transform:capitalize;"> ${terbilang} only</a>
		</div>
	</br>
			<div style="padding-top:5px;"><a style="font-weight:bold;text-transform:uppercase;">Conditions / clauses :</a></br>  ${(ins.clause_ids and ins.clause_ids[0].description or '').replace('\n','<br/>')} </div>
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
					<td width='20%'>
					</td>
					<td  width='40%' align='center' style="font-weight:bold;">
						for  <span style="text-transform:uppercase;">${ins.insurer and ins.insurer.name or ''}</span>
					</td>
					<td width='10%'>
					</td>
				</tr>
				<tr width='100%'>
					<td align='center'><br/><br/><br/></br><br/></br>
						<b>&nbsp;</b>
					</td>
					<td><br/><br/><br/></br><br/></br>
					</td>
					<td align='center'><br/><br/><br/></br><br/></br>
						<b>&nbsp;</b>
					</td>
				</tr>
				<tr width='100%'>
					<td>
					</td>
					<td  width='20%'>
						
					</td>
					<td width='40%'Style="border-bottom:1pt solid #808080;" align='center'>
						<span style="font-weight:bold;">
							%if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
								JAKARTA,	${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True))}
							%elif ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids:
								JAKARTA,	${xdate(formatLang(ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True))}
							%elif ins.entry_date!='False':
								JAKARTA,	${xdate(formatLang(ins.entry_date,date=True))}
							%endif

						</span>
					</td>
					<td width='10%'>
					</td>
				</tr>
				<tr width='100%'>
					<td width='30%' align='center'>
						Stamp duty of Policy Rp. 6000,-
					</td>
					<td width='20%'>
					</td>
					<td  width='40%' align='center'>
						Authorized Signatory (Stamp & Sign)
					</td>
					<td width='10%'>
					</td>
				</tr>
			</table>
	</div>
	</div>
</div>
</body>
%endfor
</html>	

