<html>
<head>
	<style type='text/css'>
		.fontall{	
			font-family: Arial;
			font-size:10px;
		}		
		.jdltblleftbtmsol{
			text-transform: uppercase;
			font-family: Arial;
			font-weight: bold;
			border-left: 1px dotted #808080;
			border-bottom: 1px solid #808080;
		}
		.isitbllefttopbtmsol{
			text-align: left;
			border-left: 1px dotted #808080;
			border-top: 1px solid #808080;
			border-bottom: 1px solid #808080;
		}
		.isitblleftbtmsol{
			text-align: left;
			border-left: 1px dotted #808080;
			border-bottom: 1px solid #808080;
		}
		.isitbleftbtmdot{
			text-align: left;
			border-left: 1px dotted #808080;
			border-bottom: 1px dotted #808080;
		}
		td {
			vertical-align:top;
			padding-top: 6px;
			padding-left: 3px;
			padding-right: 3px;
			padding-bottom: 6px;
		}
		.lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		.lbl1btmdot{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			border-bottom: 1px dotted #808080;
		}
		.lbl1btmsol{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			border-bottom: 1px solid #808080;
		}
		.lbl1topbtmsol{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			border-top: 1px solid #808080;
			border-bottom: 1px solid #808080;
		}
		.hdr1{
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
		}
		h2 {
			font-family: Arial;
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
			page-break-before: always;
		}
        html, body {
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
        padding:10px;
        width:100%;
        padding-bottom:0px; 
        }
        .footer {
        width:100%;
        height:0px;
        position:absolute;
        bottom:0;
        left:0;
        }        
	</style>
</head>
<body>
% for o in objects:
	<h2>
		<div class='hdr1'>
			<a style='border-bottom:1px solid;'>LC VERIFICATION CHECKLIST</a><br/>
		</div>
	</h2>
	<div class='wrapper'>
		<div class='content'>
			<table width='100%' cellspacing='0'>
				<tr>
					<td width='3%' class='lbl1topbtmsol' align='center'>01</td>
					<td width='3%' class='isitbllefttopbtmsol' colspan='4'> CUSTOMER NAME : &nbsp; <b>${o.partner_id and o.partner_id.name or ''}</b></td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmsol' align='center'>02</td>
					<td width='3%' class='jdltblleftbtmsol' colspan='2'>DETAIL</td>
					<td width='25%' class='jdltblleftbtmsol'>CONTRACT</td>
					<td width='44%' class='jdltblleftbtmsol'>LC</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.1</td>
					<td width='25%' class='isitbleftbtmdot'>NO & DATE</td>
					<td width='25%' class='isitbleftbtmdot'>
						%if len(o.sale_line_ids) > 0:
							%if o.sale_line_ids[0] and o.sale_line_ids[0].order_id and o.sale_line_ids[0].order_id.name:
								<b>${o.sale_line_ids[0] and o.sale_line_ids[0].order_id and o.sale_line_ids[0].order_id.name or ''}</b>
							%endif
						%endif
					</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_number}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.2</td>
					<td width='25%' class='isitbleftbtmdot'>PRODUCT</td>
					<td width='25%' class='isitbleftbtmdot'>
						% for product_id in o.contract_product_ids:
							${product_id.product_id and product_id.product_id.name or ''}<br/>
						% endfor
					</td>
					<td width='44%' class='isitbleftbtmdot'>
						% for product_line in o.lc_product_lines:
							${product_line.product_id and product_line.product_id.name or ''}<br/>
						% endfor
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.3</td>
					<td width='25%' class='isitbleftbtmdot'>QUANTITY</td>
					<td width='25%' class='isitbleftbtmdot'>
						% for product_id in o.contract_product_ids:
							${product_id.product_uom_qty or 0.0} <br/>
						% endfor
					</td>
					<td width='44%' class='isitbleftbtmdot'>
						% for product_line in o.lc_product_lines:
							${product_line.product_uom_qty or 0.0} <br/>
						% endfor
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.4</td>
					<td width='25%' class='isitbleftbtmdot'>PRICE</td>
					<td width='25%' class='isitbleftbtmdot'>
						% for product_id in o.contract_product_ids:
							${product_id.price_unit or 0.0}<br/>
						% endfor
					</td>
					<td width='44%' class='isitbleftbtmdot'>
						% for product_line in o.lc_product_lines:
							${product_line.price_unit or 0.0} <br/>
						% endfor
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.5</td>
					<td width='25%' class='isitbleftbtmdot'>AMOUNT</td>
					<td width='25%' class='isitbleftbtmdot'>
						<% total1 = 0.0 %>
						% for product_id in o.contract_product_ids:
							<% subtotal1 = (product_id.price_unit or 0.0)*(product_id.product_uom_qty or 0.0) %>
							<% total1+=subtotal1 %>
							${formatLang(subtotal1)} <br/>
						% endfor
						Total : ${formatLang(total1)}
					</td>
					<td width='44%' class='isitbleftbtmdot'>
						<% total2 = 0.0 %>
						% for product_line in o.lc_product_lines:
							<% subtotal2 = (product_line.price_unit or 0.0)*(product_line.product_uom_qty or 0.0) %>
							<% total2+=subtotal2 %>
							${formatLang(subtotal2)} <br/>
						% endfor
						Total : ${formatLang(total2)}
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.6</td>
					<td width='25%' class='isitbleftbtmdot'>TERMS</td>
					<td width='25%' class='isitbleftbtmdot'>${o.contract_incoterm and o.contract_incoterm.name or ''}</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_incoterm and o.lc_incoterm.name or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.7</td>
					<td width='25%' class='isitbleftbtmdot'>DESTINATION</td>
					<td width='25%' class='isitbleftbtmdot'>${o.contract_dest and o.contract_dest.name or ''}</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_dest and o.lc_dest.name or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.8</td>
					<td width='25%' class='isitbleftbtmdot'>SHIPMENT</td>
					<td width='25%' class='isitbleftbtmdot'>${o.contract_lsd or ''}</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_lsd or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'></td>
					<td width='3%' class='lbl1btmdot' align='center'>2.9</td>
					<td width='25%' class='isitbleftbtmdot'>PAYMENT TERMS</td>
					<td width='25%' class='isitbleftbtmdot'>${o.contract_payment_term and o.contract_payment_term.name or ''}</td>
					<td width='44%' class='isitbleftbtmdot'>L/C AT &nbsp; ${o.lc_payment_term and o.lc_payment_term.name or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>03</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>L/C AUTHENTICATION</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_auth or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>04</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>SHIPMENT VALIDITY DATE</td>
					<td width='44%' class='isitbleftbtmdot'></td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>05</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>L/C EXPIRY DATE / PLACE</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_expiry_date or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>06</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>TIME FOR DOCUMENT PRESENTATION</td>
					<td width='44%' class='isitbleftbtmdot'></td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>07</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>LC NEGOTIABILITY BANK IN INDONESIA</td>
					<td width='44%' class='isitbleftbtmdot'>${o.lc_negotiability or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>08</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>QUANTITY & VALUE ALLOWANCE</td>
					<td width='44%' class='isitbleftbtmdot'>${o.tolerance_percentage or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>09</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>PART SHIPMENT</td>
					<td width='44%' class='isitbleftbtmdot'>${o.part_ship or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>10</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>TRANSHIPMENT</td>
					<td width='44%' class='isitbleftbtmdot'>${o.tranship or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>11</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>ADVISING BANK INDONESIA</td>
					<td width='44%' class='isitbleftbtmdot'></td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>12</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>NEGOTIATING BANK</td>
					<td width='44%' class='isitbleftbtmdot'>${o.negotiate_bank and o.negotiate_bank.name or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>13</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>DRAFT CLAUSE</td>
					<td width='44%' class='isitbleftbtmdot'>${o.draf_clause or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>14</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>BANK CHARGES</td>
					<td width='44%' class='isitbleftbtmdot'>${o.bank_charges or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>15</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>CONFIRMATION CHARGES</td>
					<td width='44%' class='isitbleftbtmdot'>${o.confirm_charges or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>16</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>PACKING</td>
					<td width='44%' class='isitbleftbtmdot'>${o.packing or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>17</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>T.T. REIMBURSEMENT</td>
					<td width='44%' class='isitbleftbtmdot'>
						%if o.tt_reimbursment=='not':
							NOT AVAILABLE
						%else: 
							${o.tt_reimbursment or ''}
						%endif
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>18</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>NEGOTIATING BANK CONFIRMATION</td>
					<td width='44%' class='isitbleftbtmdot'> 
						%if o.negotiate_confirm=='not':
							NOT AVAILABLE
						%else:
							${o.negotiate_confirm or ''}
						%endif
					</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>19</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>LC ESTABLISED ON</td>
					<td width='44%' class='isitbleftbtmdot'>${o.date_of_issue or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>20</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>L/C RCD BY ADVISSING BANK NAME/DATE</td>
					<td width='44%' class='isitbleftbtmdot'></td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>21</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>L/C RCD BY MKT - JKT ON</td>
					<td width='44%' class='isitbleftbtmdot'>${o.rcvd_jkt or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>22</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>L/C RCD BY MKT - SMG ON</td>
					<td width='44%' class='isitbleftbtmdot'>${o.rcvd_smg or ''}</td>
				</tr>
				<tr>
					<td width='3%' class='lbl1btmdot' align='center'>23</td>
					<td width='3%' class='isitbleftbtmdot' colspan='3'>PREPARED BY</td>
					<td width='44%' class='isitbleftbtmdot'>${o.prepared_by and o.prepared_by.name or ''}</td>
				</tr>
				<tr class='border4'>
					<td width='3%' class='lbl1btmsol' align='center'>24</td>
					<td width='3%' class='isitblleftbtmsol' colspan='3'>AMENDMENTS REQUORED:<br/>
						${o.amandement_lines or ''}</td>
					<td width='44%' class='isitblleftbtmsol'></td>
				</tr>
			</table>
		</div>					
	</div>
%endfor
</body>
</html>