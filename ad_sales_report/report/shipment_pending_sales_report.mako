<html>
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type"/>
	<style type="text/css">
		td {
		    word-break: break-all;
		}
		body {
		  font-family: "times new roman";
		}
		.title1 {
		    text-transform:uppercase;
		    font-size: 15px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.title2 {
		    font-size: 12px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.title3 {
		    font-size: 10px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.header1{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    border-bottom: 1px solid #000000;
		    height: 1px;
		}
		.header2{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    border-bottom: 1px dotted #000000;
		    height: 1px;
		}
		.header3{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px solid #000000;
		    height: 1px;
		}
		.header4{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    height: 1px;
		}
		.detail{
		    font-size: 8px;
		    vertical-align:top;
		    height: 1px;
		}
		.detailcap{
		    text-transform:uppercase;
		    font-size: 8px;
		    vertical-align:top;
		    height: 1px;
		}
		.group{
		    font-weight: bold;
		    font-size: 9px;
		    vertical-align:top;
		    height: 1px;
		}
		.space{
		    font-size: 6px;
		    height: 1px;
		}
		.subtotal{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px dotted #000000;
		    vertical-align:middle;
		    height: 1px;
		}
		.grandtotal{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px solid #000000;
		    vertical-align:middle;
		    height: 1px;
		}
		h2 {
		    font-size: 6px;
		    height: 1px;
			page-break-before: always;
		}
	</style>
</head>
	<body style='border:0; margin: 0;'>
        <%uom_base_name = get_uom_base(data)%>
		<table width='100%' cellspacing='0' cellpadding='1'>
			<%details = get_view(data)%>
			
			<%cust_uom_base_qty = 0.0%>
			<%cust_amount = 0.0%>
			<%cust_item_count = 0%>
			<%group_uom_base_qty = 0.0%>
			<%group_amount = 0.0%>
			<%group_item_count = 0%>
			<%subgroup_uom_base_qty = 0.0%>
			<%subgroup_amount = 0.0%>
			<%subgroup_item_count = 0%>
			<%grand_uom_base_qty = 0.0%>
			<%grand_amount = 0.0%>
			<%grand_item_count = 0.0%>
			
			<%old_cust_name = "None"%>
			<%old_group_name = "None"%>
			<%old_subgroup_name = "None"%>
			<%cust_name = "None"%>
			<%group_name = "None"%>
			<%subgroup_name = "None"%>
			
			%for line in details:	
				<%cust_name = line['cust_name'] or ''%>
				%if (line['report_group'] or 0) == 1:
					<%group_name = "SHIPMENTS:"%>
				%elif (line['report_group'] or 0) == 2:
					<%group_name = "PENDING ORDERS:"%>
				%elif (line['report_group'] or 0) == 3:
					<%group_name = "AMMENDED ORDERS:"%>
				%else:
					<%group_name = "CANCELLED ORDERS:"%>
				%endif:

				<%subgroup_name = line['curr_name'] or ''%>

				%if (subgroup_name != old_subgroup_name) or (group_name != old_group_name) or (cust_name != old_cust_name):
					%if old_subgroup_name != "None":
						<tr>
							<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='subtotal' width='1%' align='left' colspan='9'>Total of ${old_subgroup_name}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_amount or 0.0,dp='Account')}</td>
							<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
						</tr>
					%endif:
				%endif:

				%if (group_name != old_group_name) or (cust_name != old_cust_name):
					%if old_group_name != "None":
						<tr>
							<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='subtotal' width='1%' align='left' colspan='10'>Total of ${old_group_name}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(group_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(group_amount or 0.0,dp='Account')}</td>
							<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
						</tr>
					%endif:
				%endif:

				%if cust_name != old_cust_name:
					%if old_cust_name != "None":
						<tr>
							<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${old_cust_name}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(cust_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='subtotal' width='5%' align='right'>${formatLang(cust_amount or 0.0,dp='Account')}</td>
							<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
						</tr>
						</table>		
						<h2>&nbsp;</h2>
						<table width='100%' cellspacing='0' cellpadding='1'>
						<%cust_uom_base_qty = 0.0%>
						<%cust_amount = 0.0%>		
						<%group_uom_base_qty = 0.0%>
						<%group_amount = 0.0%>
						<%subgroup_uom_base_qty = 0.0%>
						<%subgroup_amount = 0.0%>
						<%old_group_name = "None"%>
						<%old_subgroup_name = "None"%>
					%endif:
					<%old_cust_name = cust_name%>
					<tr class='group' >
						<td class='group' width='1%' align='left' colspan='22'>${cust_name}</td>
					</tr>
				%endif:
			
				%if group_name != old_group_name:
					<%old_group_name = group_name%>
					<tr class='group' >
						<td class='group' width='1%' align='left'>&nbsp;</td>
						<td class='group' width='1%' align='left' colspan='21'>${group_name}</td>
					</tr>
					<%group_uom_base_qty = 0.0%>
					<%group_amount = 0.0%>
					<%subgroup_uom_base_qty = 0.0%>
					<%subgroup_amount = 0.0%>
					<%old_subgroup_name = "None"%>
				%endif:

				%if subgroup_name != old_subgroup_name:
					<%old_subgroup_name = subgroup_name%>
					<tr class='group' >
						<td class='group' width='1%' align='left'>&nbsp;</td>
						<td class='group' width='1%' align='left'>&nbsp;</td>
						<td class='group' width='10%' align='left' colspan='20'>${subgroup_name}</td>
					</tr>
					<%subgroup_uom_base_qty = 0.0%>
					<%subgroup_amount = 0.0%>
				%endif:

				<%uom_base_qty = line['uom_base_qty'] or 0.0%>
				<%amount = line['amount'] or 0.0%>

				<%cust_uom_base_qty = cust_uom_base_qty+uom_base_qty%>
				<%cust_amount = cust_amount+amount%>
				<%group_uom_base_qty = group_uom_base_qty+uom_base_qty%>
				<%group_amount = group_amount+amount%>
				<%subgroup_uom_base_qty = subgroup_uom_base_qty+uom_base_qty%>
				<%subgroup_amount = subgroup_amount+amount%>
				<%grand_uom_base_qty = grand_uom_base_qty+uom_base_qty%>
				<%grand_amount = grand_amount+amount%>

				<tr class='detail'>
	               	<td class='detail' width='1%' align='left'>&nbsp;</td>
	               	<td class='detail' width='1%' align='left'>&nbsp;</td>
	               	<td class='detail' width='1%' align='left'>&nbsp;</td>
					<td class='detailcap' width='6%' align='left'>${line['sc_no'] or ''}</td>
					<td class='detail' width='4%' align='left'>${line['sc_date'] or ''}</td>
					<td class='detailcap' width='9%' align='left'>${line['prod_name'] or ''}</td>
					<td class='detailcap' width='7%' align='left'>${xdate(line['destination'])}</td>
					<td class='detailcap'  width='3%' align='left'>${line['curr_name'] or ''}</td>
					<td class='detailcap'   width='3%' align='right'>${formatLang(line['uom_base_price_unit'] or 0.0,dp='Product Price')}</td>
					<td class='detailcap' width='3%' align='left'>${line['lc_terms'] or ''}</td>
					<td class='detailcap' width='9%' align='left'>${line['lc_no'] or ''}</td>
					<td class='detail'  width='5%' align='right'>${formatLang(uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
					<td class='detail' width='5%' align='right'>${formatLang(amount or 0.0,dp='Account')}</td>
					<td class='detail' width='7%' align='left'>${line['delivery'] or ''}</td>
					<td class='detailcap' width='5%' align='left'>${line['invc_no'] or ''}</td>
					<td class='detail' width='4%' align='left'>${line['invc_dt'] or ''}</td>
					<td class='detailcap' width='5%' align='left'>${line['container'] or ''}</td>
					<td class='detailcap' width='7%' align='left'>${line['bl_no'] or ''}</td>
					<td class='detail' width='4%' align='left'>${line['bl_dt'] or ''}</td>
					<td class='detail' width='4%' align='left'>${line['eta'] or ''}</td>
					<td class='detail' width='3%' align='left'>${line['lot_no'] or ''}</td>
                    <td class='detail' width='4%' align='left'>${line['tpi'] or ''}</td>
				</tr>
			%endfor
		
			%if old_subgroup_name:
				<tr>
					<td class='detail' width='1%' align='left'>&nbsp;</td>
					<td class='detail' width='1%' align='left'>&nbsp;</td>
					<td class='subtotal' width='1%' align='left' colspan='9'>Total of ${old_subgroup_name}</td>
					<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
					<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_amount or 0.0,dp='Account')}</td>
					<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
				</tr>
			%endif:

			%if old_group_name:
				<tr>
					<tr>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='subtotal' width='1%' align='left' colspan='10'>Total of ${old_group_name}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(group_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(group_amount or 0.0,dp='Account')}</td>
						<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
					</tr>
				</tr>
			%endif:

			%if old_cust_name:
				<tr>
					<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${old_cust_name}</td>
					<td class='subtotal' width='5%' align='right'>${formatLang(cust_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
					<td class='subtotal' width='5%' align='right'>${formatLang(cust_amount or 0.0,dp='Account')}</td>
					<td class='subtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
				</tr>
			%endif:

			<tr>
				<td class='grandtotal' width='1%' align='left' colspan='11'>GRAND TOTAL</td>
				<td class='grandtotal' width='5%' align='right'>${formatLang(grand_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
				<td class='grandtotal' width='5%' align='right'>${formatLang(grand_amount or 0.0,dp='Account')}</td>
				<td class='grandtotal' width='5%' align='right' colspan='9'>&nbsp;</td>
			</tr>
		</table>		
	</body>
</html>