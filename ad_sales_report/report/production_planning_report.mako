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
		<%price_base_name = get_price_base(data)%>
		<%min_bale_bal_qty = 5.0%>
		<table width='100%' cellspacing='0' cellpadding='1'>
			<%details = get_view(data,data['form']['report_type'])%>
			
			<%loc_product_uom_qty = 0.0%>
			<%loc_bal_qty = 0.0%>		
			<%loc_item_count = 0%>
			<%group_product_uom_qty = 0.0%>
			<%group_bal_qty = 0.0%>
			<%group_item_count = 0%>
			<%subgroup_product_uom_qty = 0.0%>
			<%subgroup_bal_qty = 0.0%>
			<%subgroup_item_count = 0%>
			<%subgroup2_product_uom_qty = 0.0%>
			<%subgroup2_bal_qty = 0.0%>
			<%subgroup2_item_count = 0%>
			<%grand_product_uom_qty = 0.0%>
			<%grand_bal_qty = 0.0%>
			
			<%old_loc_name = "None"%>
			<%old_group_name = "None"%>
			<%old_subgroup_name = "None"%>
			<%old_subgroup2_name = "None"%>
			<%loc_name = "None"%>
			<%group_name = "None"%>
			<%subgroup_name = "None"%>
			<%subgroup2_name = "None"%>
			
			%for line in details:	
				<%bale_bal_qty = uom_to_bales(line['bal_qty'] or 0.0,line['product_uom'])%>
				<%bale_shipped_qty = uom_to_bales(line['shipped_qty'] or 0.0,line['product_uom'])%>
				%if (bale_bal_qty >= min_bale_bal_qty) or (bale_shipped_qty==0.0):
					<%loc_name = line['loc_name'] or ''%>

					%if data['form']['report_type'] == 'customer':
						<%group_name = line['blend'] or ''%>
						<%subgroup_name = line['customer_name'] or ''%>
						<%subgroup2_name = line['blend_count_sd'] or ''%>
					%elif data['form']['report_type'] == 'product':
						<%group_name = line['blend'] or ''%>
						<%subgroup_name = line['blend_count'] or ''%>
						<%subgroup2_name = line['blend_count_sd'] or ''%>
					%elif data['form']['report_type'] == 'contract':
						<%group_name = line['sale_order_name'] or ''%>
						<%subgroup_name = line['blend'] or ''%>
						<%subgroup2_name = line['blend_count_sd'] or ''%>
					%endif:			

					%if data['form']['report_type'] == 'contract':
						%if (group_name != old_group_name) or (loc_name != old_loc_name):
							%if old_group_name != "None":
								<tr>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${old_group_name}</td>
									<td class='subtotal' width='5%' align='right'>${formatLang(group_product_uom_qty or 0.0,dp='Product Unit of Measure')}</td>
									<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
								</tr>
							%endif:
						%endif:
					%else:
						%if (subgroup2_name != old_subgroup2_name) or (subgroup_name != old_subgroup_name) or (group_name != old_group_name) or (loc_name != old_loc_name):
							%if old_subgroup2_name != "None":
								<tr>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='subtotal' width='10%' align='left' colspan='9'>Total of ${old_subgroup2_name}</td>
									<td class='subtotal' width='5%' align='right'>${formatLang(subgroup2_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
									<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
								</tr>
							%endif:
						%endif:

						%if (subgroup_name != old_subgroup_name) or (group_name != old_group_name) or (loc_name != old_loc_name):
							%if old_subgroup_name != "None":
								<tr>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='subtotal' width='10%' align='left' colspan='10'>Total of ${old_subgroup_name}</td>
									<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
									<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
								</tr>
							%endif:
						%endif:

						%if (group_name != old_group_name) or (loc_name != old_loc_name):
							%if old_group_name != "None":
								<tr>
									<td class='detail' width='1%' align='left'>&nbsp;</td>
									<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${old_group_name}</td>
									<td class='subtotal' width='5%' align='right'>${formatLang(group_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
									<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
								</tr>
							%endif:
						%endif:
					%endif:

					%if loc_name != old_loc_name:
						%if old_loc_name != "None":
							<tr>
								%if data['form']['report_type'] != 'contract':
									<td class='subtotal' width='1%' align='left' colspan='12'>Total of ${old_loc_name}</td>
								%else:
									<td class='subtotal' width='1%' align='left' colspan='12'>Total of ${old_loc_name}</td>
								%endif:
								<td class='subtotal' width='5%' align='right'>${formatLang(loc_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
								<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
							</tr>
							</table>		
							<h2>&nbsp;</h2>
							<table width='100%' cellspacing='0' cellpadding='1'>
							<%loc_product_uom_qty = 0.0%>
							<%loc_bal_qty = 0.0%>		
							<%group_product_uom_qty = 0.0%>
							<%group_bal_qty = 0.0%>
							<%subgroup_product_uom_qty = 0.0%>
							<%subgroup_bal_qty = 0.0%>
							<%subgroup2_product_uom_qty = 0.0%>
							<%subgroup2_bal_qty = 0.0%>
							<%old_group_name = "None"%>
							<%old_subgroup_name = "None"%>
							<%old_subgroup2_name = "None"%>
						%endif:
						<%old_loc_name = loc_name%>
						<tr class='group' >
							%if data['form']['report_type'] != 'contract':
								<td class='group' width='1%' align='left' colspan='19'>${loc_name}</td>
							%else:
								<td class='group' width='1%' align='left' colspan='19'>${loc_name}</td>
							%endif:
						</tr>
					%endif:
				
					%if data['form']['report_type'] == 'contract':
						%if group_name != old_group_name:
							<%old_group_name = group_name%>
							<tr class='group' >
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='1%' align='left' colspan='18'>${group_name}</td>
							</tr>
							<%group_product_uom_qty = 0.0%>
							<%group_bal_qty = 0.0%>
							<%subgroup_product_uom_qty = 0.0%>
							<%subgroup_bal_qty = 0.0%>
							<%subgroup2_product_uom_qty = 0.0%>
							<%subgroup2_bal_qty = 0.0%>
							<%old_subgroup_name = "None"%>
							<%old_subgroup2_name = "None"%>
						%endif:
					%else:
						%if group_name != old_group_name:
							<%old_group_name = group_name%>
							<tr class='group' >
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='1%' align='left' colspan='18'>${group_name}</td>
							</tr>
							<%group_product_uom_qty = 0.0%>
							<%group_bal_qty = 0.0%>
							<%subgroup_product_uom_qty = 0.0%>
							<%subgroup_bal_qty = 0.0%>
							<%subgroup2_product_uom_qty = 0.0%>
							<%subgroup2_bal_qty = 0.0%>
							<%old_subgroup_name = "None"%>
							<%old_subgroup2_name = "None"%>
						%endif:

						%if subgroup_name != old_subgroup_name:
							<%old_subgroup_name = subgroup_name%>
							<tr class='group' >
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='10%' align='left' colspan='17'>${subgroup_name}</td>
							</tr>
							<%subgroup_product_uom_qty = 0.0%>
							<%subgroup_bal_qty = 0.0%>
							<%subgroup2_product_uom_qty = 0.0%>
							<%subgroup2_bal_qty = 0.0%>
							<%old_subgroup2_name = "None"%>
						%endif:

						%if subgroup2_name != old_subgroup2_name:
							<%old_subgroup2_name = subgroup2_name%>
							<tr class='group' >
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='1%' align='left'>&nbsp;</td>
								<td class='group' width='10%' align='left' colspan='16'>${subgroup2_name}</td>
							</tr>
							<%subgroup2_product_uom_qty = 0.0%>
							<%subgroup2_bal_qty = 0.0%>
						%endif:
					%endif:

					<%base_product_uom_qty = uom_to_base(data,line['product_uom_qty'] or 0.0,line['product_uom'])%>
					<%base_bal_qty = uom_to_base(data,line['bal_qty'] or 0.0,line['product_uom'])%>

					<%loc_product_uom_qty = loc_product_uom_qty+base_product_uom_qty%>
					<%loc_bal_qty = loc_bal_qty+base_bal_qty%>
					<%group_product_uom_qty = group_product_uom_qty+base_product_uom_qty%>
					<%group_bal_qty = group_bal_qty+base_bal_qty%>
					<%subgroup_product_uom_qty = subgroup_product_uom_qty+base_product_uom_qty%>
					<%subgroup_bal_qty = subgroup_bal_qty+base_bal_qty%>
					<%subgroup2_product_uom_qty = subgroup2_product_uom_qty+base_product_uom_qty%>
					<%subgroup2_bal_qty = subgroup2_bal_qty+base_bal_qty%>
					<%grand_product_uom_qty = grand_product_uom_qty+base_product_uom_qty%>
					<%grand_bal_qty = grand_bal_qty+base_bal_qty%>

					%if data['form']['report_type'] == 'customer':
						<tr class='detail'>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='detailcap' width='9%' align='left'>${line['product_descr'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['blend_count'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['date_order'])}</td>
							<td class='detailcap' width='5%' align='left'>${line['destination'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_lsd'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_scd'])}</td>
							<td class='detailcap' width='3%' align='left'>${line['packing_name'] or ''}</td>
							<td class='detail' width='3%' align='right'>${formatLang(line['cone_weight'] or 0.0,digits=2)}</td>
							<td class='detail' width='6%' align='right'>${formatLang(base_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='detailcap' width='4%' align='left'>${line['incoterm'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['container_size_name'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['payment_term_name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_recvd_date'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_lsd'])}</td>
		                    <td class='detail' width='23%' align='left'>${line['remarks'] or ''}</td>
						</tr>
					%elif data['form']['report_type'] == 'product':
						<tr class='detail' >
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='detailcap' width='10%' align='left'>${line['product_descr'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['date_order'])}</td>
							<td class='detailcap' width='10%' align='left'>${line['customer_name'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['destination'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_lsd'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_scd'])}</td>
							<td class='detailcap' width='3%' align='left'>${line['packing_name'] or ''}</td>
							<td class='detail' width='3%' align='right'>${formatLang(line['cone_weight'] or 0.0,digits=2)}</td>
							<td class='detail' width='6%' align='right'>${formatLang(base_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='detailcap' width='4%' align='left'>${line['incoterm'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['container_size_name'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['payment_term_name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_recvd_date'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_lsd'])}</td>
		                    <td class='detail' width='17%' align='left'>${line['remarks'] or ''}</td>
						</tr>
					%elif data['form']['report_type'] == 'contract':
						<tr class='detail' >
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
			               	<td class='detail' width='1%' align='left'>&nbsp;</td>
							<td class='detailcap' width='10%' align='left'>${line['product_descr'] or ''}</td>
							<td class='detailcap' width='6%' align='left'>${line['blend_count'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['date_order'])}</td>
							<td class='detailcap' width='10%' align='left'>${line['customer_name'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['destination'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_lsd'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['sale_order_scd'])}</td>
							<td class='detailcap' width='3%' align='left'>${line['packing_name'] or ''}</td>
							<td class='detail' width='3%' align='right'>${formatLang(line['cone_weight'] or 0.0,digits=2)}</td>
							<td class='detail' width='6%' align='right'>${formatLang(base_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
							<td class='detailcap' width='4%' align='left'>${line['incoterm'] or ''}</td>
							<td class='detailcap' width='7%' align='left'>${line['container_size_name'] or ''}</td>
							<td class='detailcap' width='5%' align='left'>${line['payment_term_name'] or ''}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_recvd_date'])}</td>
							<td class='detail' width='4%' align='left'>${xdate(line['lc_lsd'])}</td>
		                    <td class='detail' width='12%' align='left'>${line['remarks'] or ''}</td>
						</tr>
					%endif:			
				%endif:			
			%endfor
		
			%if data['form']['report_type'] == 'contract':
				%if old_group_name:
					<tr>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${group_name}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(group_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
						<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
					</tr>
				%endif:
			%else:
				%if old_subgroup2_name:
					<tr>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='subtotal' width='10%' align='left' colspan='9'>Total of ${old_subgroup2_name}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(subgroup2_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
						<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
					</tr>
				%endif:

				%if old_subgroup_name:
					<tr>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='subtotal' width='1%' align='left' colspan='10'>Total of ${old_subgroup_name}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(subgroup_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
						<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
					</tr>
				%endif:

				%if old_group_name:
					<tr>
						<td class='detail' width='1%' align='left'>&nbsp;</td>
						<td class='subtotal' width='1%' align='left' colspan='11'>Total of ${group_name}</td>
						<td class='subtotal' width='5%' align='right'>${formatLang(group_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
						<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
					</tr>
				%endif:
			%endif:

			%if old_loc_name:
				<tr>
					%if data['form']['report_type'] != 'contract':
						<td class='subtotal' width='1%' align='left' colspan='12'>Total of ${loc_name}</td>
					%else:
						<td class='subtotal' width='1%' align='left' colspan='12'>Total of ${loc_name}</td>
					%endif:
					<td class='subtotal' width='5%' align='right'>${formatLang(loc_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
					<td class='subtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
				</tr>
			%endif:

			<tr>
				%if data['form']['report_type'] != 'contract':
					<td class='grandtotal' width='1%' align='left' colspan='12'>GRAND TOTAL</td>
				%else:
					<td class='grandtotal' width='1%' align='left' colspan='12'>GRAND TOTAL</td>
				%endif:
				<td class='grandtotal' width='5%' align='right'>${formatLang(grand_bal_qty or 0.0,dp='Product Unit of Measure')}</td>
				<td class='grandtotal' width='5%' align='right' colspan='6'>&nbsp;</td>
			</tr>
		</table>		
	</body>
</html>