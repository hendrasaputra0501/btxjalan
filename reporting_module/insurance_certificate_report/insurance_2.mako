<html>
<head>
	<style type="text/css">
		html,body{
			font-family: Arial;
			font-size:12px;
			height:100%;
		}
		table.content, table.content tr, table.content td{
			width: 100%;
		}
		table.ins-content-table{
			width: 100%;
		}
		table.ins-content-table td{
			vertical-align: top;
		}
		td.ins-content-table-lines{
			vertical-align: bottom;
			border-bottom: 1px solid #808080;
		}
		.label{
			/*text-transform: uppercase;*/
			font-weight: bold;
		}
		.value{
			text-transform: uppercase;
			/*font-weight: bold;*/
		}
		.value-number{
			/*text-transform: uppercase;*/
			/*font-weight: bold;*/
			text-align: right;
		}
		#wrapper{
			min-height:100%;
        	position:static;
        	width:100%;
			/*padding-top:125px;*/
			/*background-color:yellow;*/
		}
		/*.tot-premium a.value-number{
			text-align: right;
		}*/
		/*#footer {
			background:green;
			width:100%;
			position:absolute;
			
			bottom:0;
			left:0;
			height:140px;
		}*/
		/*#content1{
		padding-bottom:10px; 
		}*/
		/*#break1{
		position:relative;
		display: block;
		}*/
		 /*#break2{
 		background: yellow;
 		bottom:40;
 		height:5px;
 		}*/
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
        #content1{
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
 		height:100px;
 		}
	</style>
</head>
<%
from datetime import datetime
from ad_amount2text_idr import amount_to_text_id 
from openerp.tools import amount_to_text_en 
%>

% for ins in objects:
<body>
</br>
<div  id="wrapper">
	<div id="content1" >
		<!-- <table class="content-table" width="100%" style="background-color:orange;"> -->
		<table class="content-table" width="100%">
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">The Insured</a>
							</td>
							<td width="60%">
								<a class="value">${ins.insured.name}</a>
							</td>
						</tr>
						<tr>
							<td>
								<a class="label">Address Insured</a>
							</td>
							<td>
								<a class="value">
									%if ins.show_insuredby_address:
										${ins.address_text or ''}
									%else:
										${get_address(ins.insured) or ''}
									%endif		
								</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">Invoice Value</a>
							</td>
							<td width="60%">
								<a class="value">${ins.currency_id.name}&nbsp;${formatLang(ins.amount_total,digits=2)}</a>
							</td>
						</tr>
						<tr>
							<td>
								<a class="label">Insured Value</a>
							</td>
							<td>
								<a class="value">${ins.currency_id.name}&nbsp;${formatLang(ins.insured_amount,digits=2)}</a>
							</td>
						</tr>
						<tr>
							<td>
								<a class="label">Date of Sailing</a>
							</td>
							<td>
								<a class="value">
									%if ins.invoice_id and ins.invoice_id.picking_ids:
										% if ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
											${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
										% elif ins.invoice_id.picking_ids[0].estimation_deliv_date!='False':
											${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
										%endif
									%elif ins.entry_date!='False':
										${datetime.strptime(ins.entry_date,"%Y-%m-%d").strftime("%d/%m/%Y")}
									%endif
								</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<a class="label">&nbsp;Interest Insured</a><br/>
					<table class="ins-content-table">
						<tr>
							<td class="ins-content-table-lines" width="60%"><a class="label"><br/>Product</a></td>
							<td class="ins-content-table-lines" align="right" width="14%"><a class="label"><br/>Quantity</a></td>
							<td class="ins-content-table-lines" width="8%"><a class="label"><br/>Unit</a></td>
							<td class="ins-content-table-lines" align="right" width="18%"><a class="label">Amount<br/>(${ins.currency_id.name or ''})</a></td>
						</tr>
						%for baris in ins.product_ids:
						<tr>
							<td>
								<a class="value">
									${baris.invoice_line_id and baris.invoice_line_id.name or (baris.name and baris.name.replace('\n','<br/>') or '')}
								</a>
							</td>
							<td align="right">
								<a class="value-number">
									${formatLang(baris.quantity or 0.0)}
								</a>
							</td>
							<td>
								<a class="value">
									${baris.uom_id and baris.uom_id.name or ''}
								</a>
							</td>
							<td align="right">
								<a class="value-number">
									${formatLang(baris.price_subtotal or 0.0)}
								</a>
							</td>
						</tr>
						%endfor
						<tr>
							<td class="ins-content-table-lines" colspan="4">&nbsp;</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<%
						invs = {}
						for baris in ins.product_ids:
							if baris.invoice_id and (baris.invoice_id.internal_number or baris.invoice_id.number) not in invs:
								invs.update({(baris.invoice_id.internal_number or baris.invoice_id.number):baris.invoice_id.date_invoice})
						%>
						<tr>
							<td width="20%">
								<a class="label">Invoice No.</a>
							</td>
							<td width="35%">
								<a class="value">${invs and "<br/>".join([str(x) for x in sorted(invs.keys())])  or ins.invoice_number or ''}</a>
							</td>
							<td width="15%">
								<a class="label">DATED :</a>
							</td>
							<td width="30%">
								<a class="value">${invs and "<br/>".join([formatLang(invs[x],date=True) for x in sorted(invs.keys())]) or ins.invoice_date or ''}</a>
							</td>
						</tr>
						<tr>
							<td>
								<a class="label">LC No.</a>
							</td>
							<td>
								<a class="value">
									${ins.lc_number or ''}
								</a>
							</td>
							<td>
								<a class="label">DATED :</a>
							</td>
							<td>
							
								<a> ${ins.lc_date or ''} </a>
								
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">Coveyance</a>
							</td>
							<td width="30%">
								<a class="value">${ins.vessel_conveyance or ''}</a>
							</td>
							<td width="20%">
								<a class="label">Connect Vessel</a>
							</td>
							<td width="30%">
								<a class="value">${ins.connect_vessel or ''}</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">B/L No.</a>
							</td>
							<td width="35%">
								<a class="value">${ins.bl_number or ''}</a>
							</td>
							<td width="15%">
								<a class="label">DATED :</a>
							</td>
							<td width="30%">
								<a class="value">
									%if ins.invoice_id and ins.invoice_id.picking_ids:
										% if ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
											${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
										% elif ins.invoice_id.picking_ids[0].estimation_deliv_date!='False':
											${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
										%endif
									%elif ins.entry_date!='False':
										${datetime.strptime(ins.entry_date,"%Y-%m-%d").strftime("%d/%m/%Y")}
									%endif
								</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">At And from</a>
							</td>
							<td width="60%">
								<a class="value">${ins.voyage_from or ''}</a>
							</td>
						</tr>
						% if ins.transhipment:
						<tr>
							<td>
								<a class="label">Transhipment</a>
							</td>
							<td>
								<a class="value">${ins.transhipment or ''}</a>
							</td>
						</tr>
						% endif
						<tr>
							<td>
								<a class="label">To</a>
							</td>
							<td>
								<a class="value">${ins.voyage_to or ''}</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table class="ins-content-table">
						<!--  CONSIGNEE  -->
						<tr>
							<td width="20%">
								<a class="label">Consignee</a>
							</td>
							<td width="60%">
								<a class="value">
								% if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.show_consignee_address:
									${(ins.invoice_id.picking_ids[0].container_book_id.c_address_text  or '').replace('\n','<br/>') }
								% elif ins.consignee:
									${(ins.consignee  or '').replace('\n','<br/>') }
								% endif
								</a>
							</td>
						</tr>
						
						<!--  NOTIFY  -->
						<tr>
							<td width="20%">
								<a class="label">Notify Party</a>
							</td>
							<td width="20%">
								<a class="value">
								% if ins.invoice_id and ins.invoice_id.picking_ids and ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.show_notify_address:
									${(ins.invoice_id.picking_ids[0].container_book_id.n_address_text  or '').replace('\n','<br/>') }
								% elif ins.notify:
									${(ins.notify  or '').replace('\n','<br/>') }
								%endif
								</a>
							</td>
						</tr>
						<!--  Claimb Payable  -->
						%if ins.claim_data:
						<tr>
							<td width="20%">
								<span style="font-weight:bold;">${ins.claim_title or ''}</span>
							</td>
							<td width="60%">
								<a class="value">
									${ins.claim_data or ''}
								</a>
							</td>
						</tr>
						%endif
						<!-- Claimb value -->
						%if ins.value_at:
						<tr>
							<td width="20%">
								<span style="font-weight:bold;">Claim Value</span>
							</td>
							<td width="60%">
								<a class="value">
									${ins.value_at or ''}
								</a>
							</td>
						</tr>
						%endif
						<!-- deductable details -->
						%if ins.type=="sale":
						<tr>
							<td width="20%">
								<span style="font-weight:bold;">Deductable details</span>
							</td>
							<td width="60%">
								<a class="value">
									${ins.deductable_premi or ''}
								</a>
							</td>
						</tr>
						%endif
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<a class="label">Conditions</a><br/>
					<a class="value">
						% for cls in ins.clause_ids:
							${(cls.description or '').replace('\n','<br/>')}<br/>
						% endfor
					</a>
				</td>
			</tr>
			% if ins.shipper:
			<tr>
				<td>
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">Shipper</a>
							</td>
							<td width="60%">
								<a class="value">${(ins.shipper  or '').replace('\n','<br/>') }</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			%endif
			</table>
			<!-- <tr>
				<td> -->
			<div>
					<table class="ins-content-table" style="width:70%;">
						<tr>
							<td width="30%">
								<a class="label">Premium Calculation</a>
							</td>
							<td width="30%">
								<a class="label">: &nbsp; ${(ins.currency_id and ins.currency_id.name or '')} &nbsp; ${formatLang(ins.insured_amount or 0.0)} x ${formatLang(ins.premi_rate or 0.0)}%</a>
							</td>
							<td width="10%">
								<a class="value">${(ins.currency_id and ins.currency_id.name or '')}</a>
							</td>
							<td width="30%" align='right'>
								<a class="value">${formatLang(ins.deductible_amount or 0.0)}</a>
							</td>
						</tr>
						<%
							total_grouped = {ins.currency_id and ins.currency_id.name or '':ins.deductible_amount or 0.0}
						%>
						% for cc in sorted(ins.additional_cost,key=lambda c:c.sequence):
							<%
							if cc.currency_id.name not in total_grouped:
								total_grouped.update({cc.currency_id.name:0.0})
							total_grouped[cc.currency_id.name]+=cc.amount
							%>
							<tr>
								<td width="30%">
									<a class="label">${cc.name or ''}</a>
								</td>
								<td width="45%">
									<a class="label">:&nbsp;</a>
								</td>
								<td width="5%">
									<a class="value">${(cc.currency_id.name or '')}</a>
								</td>
								<td width="20%" align='right'>
									<a class="value">${formatLang(cc.amount or 0.0)}</a>
								</td>
							</tr>
						% endfor


									<!-- <tr>
										<td style="height:1000px;">
										% for key in total_grouped.keys():
											<a class="value">${(key or '')}</a><br/>
										% endfor
										</td>
									</tr> -->
									<!-- <tr>
										<td width="30%">
											<a class="label">Total Premium</a>
										</td>
										<td width="30%">
											<a class="label">:&nbsp;</a>
										</td>
										<td width="10%" style="height:200px;background-color:blue;">
										% for key in total_grouped.keys():
											<a class="value" style="background-color:yellow;">${(key or '')}</a>
										% endfor
										</td>
										<td width="30%" align="right" style="border-top:1px solid;">
										% for key in total_grouped.keys():
											<a class="value">${formatLang(total_grouped[key] or 0.0)}</a>
										% endfor
										</td>
									</tr> -->
					</table>
					<!-- <div style="height:200px;width:100%;"> -->
						<!-- <div class="label" style="background-color:blue;height:20px;width:52%;float:left;"> -->
						<div class="label" style="height:20px;width:52%;float:left;">
							Total Premium   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</div>
						<!-- <div style="height:30px;background-color:red;;width:18%;float:left;border-top:black solid 1px;"> -->
						<div  style="height:30px;width:18%;float:left;border-top:black solid 1px;">
							% for key in total_grouped.keys():
											<!-- <a class="value" style="background-color:yellow;"> -->
											<div class="value" style="float:left;">
												${(key or '')}</div>
											<!-- <a class="value-number" style="background-color:yellow;margin-left:45px;"> -->
											<div  style="float:right;" class="value-number" style=";margin-left:45px;text-align:right;">${formatLang(total_grouped[key] or 0.0)}</div>
										</br>
							% endfor
						</div>
						<!-- <div style="width:30%;float:right;background-color:red;height:40px;"> -->
						<div style="width:30%;float:right;height:30px;">
							&nbsp;
						</div>


			% if ins.desc_surveyor:
			<table style="margin-top:40px;">
			<tr>
				<td>
					<!-- <table class="ins-content-table" style="background-color:blue;"> -->
					<table class="ins-content-table">
						<tr>
							<td width="20%">
								<a class="label">Survey Agents</a>
							</td>
							<td width="60%" height="156px" >
								<a class="value">${(ins.desc_surveyor or '').replace('\n','<br/>')}</a>
							</td>
						</tr>
					</table>
				</td>
			</tr>
			</table>
			% endif
		
		<!-- <div style="padding-top:60px;">
			
		</div> -->
	</div>
	
	</div>
	<!-- <div id="break2" style="vertical-align:top;background-color:red;">&nbsp;</div> -->
	<div id="break2" >&nbsp;</div>
	<div id="break1" style="page-break-before: always;">
		<div id="footer">
			<table>
				<tr>
					<td>
			%if ins.invoice_id and ins.invoice_id.picking_ids:
				% if ins.invoice_id.picking_ids[0].container_book_id and ins.invoice_id.picking_ids[0].container_book_id.estimation_date!='False':
					JAKARTA, ${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].container_book_id.estimation_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
				% elif ins.invoice_id.picking_ids[0].estimation_deliv_date!='False':
					${datetime.strptime(formatLang(ins.invoice_id.picking_ids[0].estimation_deliv_date,date=True),"%d/%m/%Y").strftime("%d/%m/%Y")}
				%endif
			%elif ins.entry_date!='False':
				JAKARTA, ${datetime.strptime(ins.entry_date,"%Y-%m-%d").strftime("%d/%m/%Y")}
			%endif
				</td>
			</tr>
		</table>
		</div>
	</div>
</div>
</body>
%endfor
</html>	

