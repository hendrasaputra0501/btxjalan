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
				font-family: Verdana;
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
		.grsatasdash{
			border-top: 1px dashed #808080;
		}
		#grsbwhtbl{
			border-bottom: 1px solid #808080;
		}
		.grstotal{
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
		.hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
}
			/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        }
        #wrapper {
        	/*padding-top:10px;*/
        min-height:100%;
        position:static;
        font-family: Verdana;
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
	height:150px;
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
			    /*width:30em; */
			    width: 100%;
			    /*border: 1px solid #000000;*/
			    word-wrap: break-word;
			    vertical-align:top;
			    margin-top:5px;
        }
  .btsprg1{
			    /*width:20em; */
			    width: 100%;
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
% for o in objects:
<%
	# label_print="{}"
	# if o.sale_ids and o.picking_ids and (o.sale_ids[0].payment_method=="lc" or o.sale_ids[0].payment_method=="tt"):
	# 	label_print = o.picking_ids[0].lc_ids and o.picking_ids[0].lc_ids[0].label_print or '{}'
	# else:
	# 	label_print = o.label_print
	# label = eval(label_print)
	label = get_label(o)
%>
<body>
	<div  id="wrapper">
		<div id="title1">
			<a style="border-bottom:1px solid;">Commercial Invoice</a> <br/>
		</div>
		<br/>
		<br/>
	<div id="content">
%if o.sale_type=="export":
		<table width="100%" >
		<tr>
			<td width="35%" style="vertical-align:top;">
				<table>
					<tr>
						<td rowspan="5" width="70%" style="vertical-align:top;text-transform:uppercase;"><a style="font-weight:bold;text-transform:uppercase;">
							${label.get('shipper','Shipper/Exporter')}<a/></br>
							%if o.show_shipper_address==False:
							<!-- %if o.sale_ids and o.sale_ids[0].payment_method=="cash": -->
								PT BITRATEX INDUSTRIES</br>
								MENARA KADIN INDONESIA 12TH FLOOR,</br>
								JL. HR RASUNA SAID, Blok X-5 KAV. 2 AND 3, </br>
								JAKARTA 12950, INDONESIA
							%else:
								%if o.show_shipper_address==True:
									<div class="btsprg" style="vertical-align:top;">
										<span style="text-transform:uppercase;">
											${(o.s_address_text or '').replace('\n','<br/>')} 
										</span>
									</div>
								% else:

								<span style="text-transform:uppercase;">
									%if o.company_id and o.company_id.name:
										${o.company_id and o.company_id.name or ''} <br/>
									%endif
									%if o.company_id and o.company_id.street:
										${o.company_id and o.company_id.street or ''} <br/>
									%endif
									%if o.company_id and o.company_id.street2:
										${o.company_id and o.company_id.street2 or ''}  <br/>
									%endif
									%if o.company_id and o.company_id.city:
										${o.company_id and o.company_id.city or ''} </br>
									%elif o.company_id and o.company_id.zip and o.company_id and o.company_id.country_id and o.company_id.country_id.name:
										${o.company_id and o.company_id.zip or ''},${o.company_id and o.company_id.country_id and o.company_id.country_id.name or ''} </br>
									%endif
								</span>
								%endif
							%endif			
						</td>
					</tr>
				</table>
			
				%if o.show_buyer_address==True:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">
						 ${label.get('buyer','Buyer')}</a></br>
						<span style="text-transform:uppercase;">
							${o.buyer.name or ''} <br/>
							${o.address_text or ''} 
						</span>
					</div>
				%elif not o.show_buyer_address and not o.show_consignee_address and not o.show_notify_address and not o.show_applicant_address:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">
						 ${label.get('buyer','Buyer')}</a></br>
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
								${o.partner_id and o.partner_id.city or ''}<br/>
							%endif
							%if o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or o.partner_id and o.partner_id.zip:
								${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
							%elif partner_id and o.partner_id.zip:
								${o.partner_id and o.partner_id.zip or ''}<br/>
							%endif
							
							%if o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name:
								${o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name or ''}<br/>
							%endif
							%if o.partner_id and o.partner_id.npwp:
								<b>NPWP :</b> &nbsp; ${o.partner_id and o.partner_id.npwp or ''}
							%endif
						</span>
					</div>
				%endif
				
				%if o.show_applicant_address==True:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1"> 
							${label.get('applicant','applicant')} </a></br>
						<span style="text-transform:uppercase;">
							<!-- # ${o.applicant.name or ''} <br/> -->
							${(o.a_address_text or '').replace('\n','<br/>')}
						</span>
					</div>
				%endif
			
				%if o.show_consignee_address==True:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1">
							${label.get('consignee','Consignee')}</a></br>
						<span style="text-transform:uppercase;">
							<!-- # ${o.consignee.name or ''} <br/> -->
							${(o.c_address_text or '').replace('\n','<br/>')}
						</span>
					</div>
				%endif
			
				%if o.show_notify_address==True:
					<div class="btsprg" style="vertical-align:top;">
						<a id="lbl1"> 
							${label.get('notify','Notify')}</a></br>
						<span style="text-transform:uppercase;">
							<!-- # ${o.notify.name or ''} <br/> -->
							${(o.n_address_text or '').replace('\n','<br/>')}
						</span>
					</div>
				%endif
			
			</br>
			</td>
			<td width="30%">
				% if o.sale_ids and o.sale_ids[0].payment_method in ('lc','tt'):
					%if o.picking_ids and o.picking_ids[0].lc_ids and o.picking_ids[0].lc_ids[0].commercial_invoice_header:
									<div class="btsprg1" style="vertical-align:top;margin-top:5px;">
											<a id="lbl1"> ${label.get('','Info LC')} </a> <br/>
											<span style="text-transform:uppercase;">
												${o.picking_ids[0].lc_ids[0].commercial_invoice_header or ''}
											</span>
									</div>
					<!-- %elif o.sale_ids and o.sale_ids[0].lc_ids and o.sale_ids[0].lc_ids[0].commercial_invoice_header:
									<div class="btsprg1" style="vertical-align:top;margin-top:5px;">
											<a id="lbl1"> ${label.get('','Info LC')} </a> <br/>
											<span style="text-transform:uppercase;">
												${o.sale_ids[0].lc_ids[0].commercial_invoice_header or ''}
											</span>
									</div> -->
					%endif
				% endif
			</td>
			<td width="35%">
				<table id="borderwhite"  width="100%"  rules="all">
					<tr>
						<td id="lblrght" width="50%" > ${label.get('invoice','Invoice No. ')} </td><td id="borderwhite_rgt" width="50%">Date</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.internal_number or ''}</td>
						<td id="borderwhite_rgtbtm">${o.date_invoice or ''}</td>
					</tr>
				</table>
				<table id="borderwhite"  width="100%"  rules="all" style="margin-top:5px;">
					<tr>
						<td id="lblrght" width="50%" > ${label.get('sale_order','SC NO. ')} </td><td id="borderwhite_rgt" width="50%">Customer's Ref</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${'<br/>'.join(list(set([move.sale_line_id.order_id.name for picking in o.picking_ids for move in picking.move_lines if move.sale_line_id and move.sale_line_id.order_id])))}</td>
						<td id="borderwhite_rgtbtm">${o.name or ''}</td>
					</tr>
				</table>
				
				<!-- <table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Delivery Terms</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">-</td>
					</tr>
				</table> -->		
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('lc_number','Letter of credit ')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							<a id="lbl1">
								%if get_lc_number(o):
									${ get_lc_number(o)}
								%else:
									&nbsp;
								%endif
						</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all" style="margin-top:5px;">
					<tr>
						<td id="borderwhite_rgt" width="100%" > ${label.get('delivery_term','Price Terms ')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
						${o.picking_ids and o.picking_ids[0].lc_ids and o.picking_ids[0].move_lines and o.picking_ids[0].move_lines[0].lc_product_line_id and o.picking_ids[0].move_lines[0].lc_product_line_id.delivery_term_txt or (o.sale_ids and o.sale_ids[0].incoterm and o.sale_ids[0].incoterm.code or '')}
						</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;" > ${label.get('port_from','Port/Country of Loading')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							%if o.picking_ids and o.picking_ids.container_book_id[0] and o.picking_ids.container_book_id[0].port_from_desc:
								${o.picking_ids and o.picking_ids.container_book_id[0] and o.picking_ids.container_book_id[0].port_from_desc or ''}
							%else:
								&nbsp;
							%endif
						</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('port_to','Port/Country of Destination')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							%if o.picking_ids and o.picking_ids.container_book_id[0] and o.picking_ids.container_book_id[0].port_to_desc:
								${o.picking_ids and o.picking_ids.container_book_id[0] and o.picking_ids.container_book_id[0].port_to_desc or ''}
							%else:
								&nbsp;
							%endif
						</td>
					</tr>
				</table>
			</td>
		</tr>
		</table>
		</br>
%elif o.sale_type=="local":
<!-- local -->
<table width="100%">
		<tr>
			<td width="70%" style="vertical-align:top;">
				<table>
					<tr>
						<td rowspan="5" width="70%" style="vertical-align:top;"><a style="font-weight:bold;text-transform:uppercase;"> ${label.get('shipper','Seller')}<a/></br>
							%if o.shipper:
								% if o.show_shipper_address==True:
								<div class="btsprg" style="vertical-align:top;">
									<span style="text-transform:uppercase;">
										%if o.shipper and o.shipper.name:
											${o.shipper and o.shipper.name or ''} <br/>
										%endif
										${o.s_address_text or ''} 
									</span>
								</div>
								% else:
								<div class="btsprg" style="vertical-align:top;">
									<span style="text-transform:uppercase;">
										%if o.shipper and o.shipper.name:
											${o.shipper and o.shipper.name or ''} <br/>
										%endif
										${get_address(o.shipper) or ''} 
									</span>
								</div>
								% endif
							% else:
								%if o.company_id and o.company_id.name:
									${o.company_id and o.company_id.name or ''} <br/>
								%endif
								%if o.company_id and o.company_id.street:
									${o.company_id and o.company_id.street or ''} <br/>
								%endif
								%if o.company_id and o.company_id.street2:
									${o.company_id and o.company_id.street2 or ''}  <br/>
								%endif
								%if o.company_id and o.company_id.city:
									${o.company_id and o.company_id.city or ''} </br>
								%elif o.company_id and o.company_id.zip and o.company_id and o.company_id.country_id and o.company_id.country_id.name:
									${o.company_id and o.company_id.zip or ''},${o.company_id and o.company_id.country_id and o.company_id.country_id.name or ''} </br>
								%endif
								%if o.company_id.partner_id.npwp:
									<b>NPWP :</b> &nbsp; ${o.company_id.partner_id.npwp or ''}
								%endif
							% endif
						</td>
					</tr>
				</table>
				<table style="padding-top:5px;vertical-align:top;">
					<tr>
						<td ><a id="lbl1"> ${label.get('buyer','Buyer ')}</a></br>
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
							${o.partner_id and o.partner_id.city or ''}<br/>
						%endif
						%if o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or o.partner_id and o.partner_id.zip:
							${o.partner_id and o.partner_id.state_id and o.partner_id.state_id.name or ''} &nbsp; ${o.partner_id and o.partner_id.zip or ''}<br/>
						%elif partner_id and o.partner_id.zip:
							${o.partner_id and o.partner_id.zip or ''}<br/>
						%endif
						
						%if o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name:
							${o.partner_id and o.partner_id.country_id and o.partner_id.country_id.name or ''}<br/>
						%endif
						%if o.partner_id and o.partner_id.npwp:
							<b>NPWP :</b> &nbsp; ${o.partner_id and o.partner_id.npwp or ''}
						%endif
						</td>
					</tr>
				</table>
			</br>
				<!-- <table width="50%">
					<tr>
						<td id="lbl1" width="100%" >Notify Party</td>
					</tr>
					<tr>
					#	<td>${o.picking_ids and o.picking_ids.notify and o.picking_ids.notify[0].name or '' } </br>
					#		${o.picking_ids and o.picking_ids.notify and o.picking_ids.notify[0].street or '' } </br>
					#		CNPJ : ${o.picking_ids and o.picking_ids[0].notify and o.picking_ids.notify[0].npwp or '' }   </br>
						</td>
					</tr>
				</table> -->
			</td>
			<td width="30%">
				<table id="borderwhite"  width="100%"  rules="all">
					<tr>
						<td id="lblrght" width="60%" > ${label.get('invoice','Invoice No. ')}</td><td id="borderwhite_rgt" width="40%">Date</td>
					</tr>
					<tr>
						<td id="borderwhite_btm">${o.internal_number or ''}</td>
						<td id="borderwhite_rgtbtm">${o.date_invoice or ''}</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('','Sales Confirmation ')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm"><a style="text-transform:uppercase;">${o.sale_ids[0] and o.sale_ids[0].name or ''}</td>
					</tr>
				</table>
				<!-- <table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;">Delivery Terms</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">-</td>
					</tr>
				</table> -->		
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('surat_jalan_number','Surat Jalan No. ')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							<a id="lbl1">${o.picking_ids and o.picking_ids[0].name or ''}
						</td>
					</tr>

				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('delivery_term','Payment Terms')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							${o.sale_ids and o.sale_ids[0].payment_term and  o.sale_ids[0].payment_term.name or ''}
						</td>
					</tr>
				</table>
				<table id="borderwhite" width="100%" rules="all">
					<tr>
						<td id="borderwhite_rgt" width="100%" style="padding-top:5px;"> ${label.get('payment_due_date','Payment Due Date')}</td>
					</tr>
					<tr>
						<td id="borderwhite_rgtbtm">
							${o.date_due}
						</td>
					</tr>
				</table>
			</td>
		</tr>
		</table>
%endif
		<table id="data_container" class='border1'  width='98%' cellspacing="0" style="margin-top:5px;">
				<tr width='100%'>
					<td id="lbl2" colspan="2"></td>
					<td id="lbl2" style="border-bottom:solid 1pt #808080; " colspan="3">Quantity</td>
					<!-- <td id='jdltblknn' width='9%' align='center' rowspan="2">${label.get('price_unit',('Price<br/>('+o.currency_id.name+')'))} -->
					<td id='jdltblknn'  width='9%' align='center' rowspan="2">${label.get('price_unit',('Price<br/>('+o.currency_id.name+')'))}</td>
					<td id='jdltblknn' width='10%' rowspan="2">${label.get('amount',('Amount<br/>('+o.currency_id.name+')'))}</td>
				</tr>
				<tr>
					<td id='jdltbl' width='14%'>Marks & Nos</td>
					<td id='jdltbl' width='40%'>DESCRIPTION OF GOODS</td>
					<td id='jdltblknn' width='10%' colspan="2" >Packages</td>
					<td id='jdltblknn' width='15%' style='padding-right:10px;'>N.W (${o.invoice_line and o.invoice_line[0].uos_id and o.invoice_line[0].uos_id.name})</td>
					<!-- <td id='jdltblknn'></td> -->
					<!-- <td id='jdltblknn' width='9%'>(${o.currency_id.name or ''})</td> -->
					<!-- <td id='jdltblknn' width='10%'>${label.get('price_unit',('('+o.currency_id.name+')'))}</td> -->
				</tr>
				<tr>
					<td id='grsbwhtbl' colspan="7"></td>
				</tr>
		<%
		totamt,ortotqty,totqty=get_totline_amt(o.invoice_line)
		%>
		%for baris in get_totline2(o.invoice_line):
				<tr>
					<td style="padding-top:5px;">
						${baris[0] or ''}
					</td>
					<td id='isitbl' style="padding-top:5px;">
						${baris[1].upper() or ''}
					</td>
					<td width='8%' id='isitblknn' style="padding-top:5px;padding-right:3px;">
						${formatLang(baris[6],digits=0) or ''} 
					</td>
					<td width='4%' style="padding-top:5px;text-transform:capitalize; padding-right:3px;">${baris[7] or ''}</td>
					<td id='isitblknn' style="padding-top:5px;padding-right:10px;">
						${formatLang(baris[3],digits=o.quantity_digits and o.quantity_digits>0 and o.quantity_digits or 2)}

					</td>
					<td id='isitblknn' style="padding-top:5px;">
						${formatLang(baris[4],digits=o.price_unit_digits and o.price_unit_digits>0 and o.price_unit_digits or 2)}
					</td>

					<td id='isitblknn' style="padding-top:5px;">
						${formatLang(baris[5],digits=2)}
					</td>
				</tr>
		%endfor
				%if not o.amount_tax or o.amount_tax==0.0:
					<tr>
						<td id="empty_container" colspan="7">
						</td>
					</tr>
				%else:
					<tr>
						<td  colspan="2">
						&nbsp;
						</td>
						<td id="isitbl" class="grsatasdash" style="text-align:left;" colspan="4">
							Additional Tax: VAT
						</td>
						<td id="isitblknn" class="grsatasdash" style=''>
							${o.amount_tax or 0.0}
						</td>
					</tr>
				%endif
				<!-- <tr>
					<td>&nbsp;</td><td>&nbsp;</td><td id='grsbwhtbl' width='43%' colspan="5">&nbsp;</td>
				</tr> -->
				<tr>
					<td></td>
					<td></td>
					<td id="jdltbl" class="grstotal" style="text-align:left;">Total :</td>
					<td class="grstotal" ></td>
					<td id="jdltbl" class="grstotal"  style="text-align:right;padding-right:10px;">${formatLang(ortotqty,digits=o.quantity_digits and o.quantity_digits>0 and o.quantity_digits or 2)}</td>
					<td class="grstotal" ></td>
					<td id="jdltbl"  class="grstotal"  style="text-align:right;">${formatLang(totamt+(o.amount_tax or 0.0),digits=2)}</td>
				</tr>
				<tr>
					<td id='grsbwhtbl' width='100%' colspan="7"></td>
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
				terbilang=call_num2word(totamt+(o.amount_tax or 0.0),"en")
		%>
		<div  style="font-weight:bold;text-transform:capitalize;">
		TOTAL AMOUNT : ${o.currency_id.name or ''} ${terbilang} only
		</div>
			<br/>
			<table width="100%">
			<tr>
				<td width="100%"> 
					${(o.additional_remarks or '').replace('\n','<br/>')}
				</td>
			</tr>
		</table>
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
						<a id='lbl1'>${o.company_id and o.company_id.name or ''}</a>
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
					<td Style="border-bottom:1pt solid #808080; text-align:center;">
						${o.sale_type=='export' and o.authorized_by and o.authorized_by.name or ''}
					</td>
				</tr>
				<tr width='100%'>
					<td width='30%' align='center'>
						&nbsp;
					</td>
					<td width='40%'>
					</td>
					<td  width='30%' align='center'>
						${o.sale_type=='export' and o.job_position_id and o.job_position_id.name or (o.sale_type=='export' and o.authorized_by and o.authorized_by.job_id and o.authorized_by.job_id.name or 'Authorized Signatory (Stamp & Sign)')}
					</td>
				</tr>
			</table>
	</div>
	</div>
</div>
</body>
%endfor
</html>	

