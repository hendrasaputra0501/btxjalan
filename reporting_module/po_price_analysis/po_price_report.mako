<html>
<head>
	<style type="text/css">
	body{
		font-family:Verdana;
		/*font-family:fontenc;*/
		font-size: 6.5pt;
		margin:0;
		padding-top:0;
		height:90%;
		/*background-color:green;*/
	}

	td.title{
		font-weight: bold;
		font-size: 10px;
		text-align: center;
	}

	table
	{
		border-collapse: collapse;
		/*width: 100%;*/
		/*width:98%;*/
	}

	tr.tr-title {
		border-top: 1px solid;
		border-bottom: 1px solid;
	}

	td.td-title {
		text-align: center;
		font-weight: bold;
	}

	td.td-loc_title {
		font-weight: bold;
		text-decoration: underline;
	}

	tr.tr-subtotal {
		border-top: 1px dashed;
	}

	td.td-subtotal-label {
		text-align: left;
		font-weight: bold;
	}
	
	td.td-subtotal-amount {
		text-align: right;
		font-weight: bold;
	}

	tr.tr-grandtotal {
		border-top: 1px solid;
	}

	td.td-grandtotal {
		font-weight: bold;
	}

	td.td-details {
		vertical-align: top;
	}
	</style>
</head>
<body>
% for inventory_type in [x[0] for x in data['goods_type']]:
	<%
	result_grouped = {}
	for line in get_result(data, inventory_type):
		key1 = (line['prod_code'],line['prod_name'])
		if key1 not in result_grouped:
			result_grouped.update({key1:{}})
		key2 = (line['partner_code'],line['partner_name'])
		if key2 not in result_grouped[key1]:
			result_grouped[key1].update({key2:[]})
		result_grouped[key1][key2].append(line)
	%>

	<table style="page-break-before:always;vertical-align:top;width:100%;top:0;">
		<thead>
			<tr><td colspan="10" width="100%" class="title">PT. BITRATEX INDUSTRIES</td></tr>
			<tr><td colspan="10" width="100%" class="title" style="text-transform:uppercase;">PURCHASE PRICE ANALYSIS</td></tr>
			<tr>
				<td colspan="10" width="100%" class="title">Goods Type : ${inventory_type}.&nbsp;FROM ${formatLang(data['start_date'],date=True)} TO ${formatLang(data['end_date'],date=True)}</td>
			</tr>
			<tr class="tr-title">
				<td colspan="2" width="20%" class="td-title">Product</td>
				<td colspan="2" width="20%" class="td-title">Supplier</td>
				<td colspan="2" width="20%" class="td-title">Purchase Order</td>
				<td rowspan="2" width="3%" class="td-title">UoM</td>
				<td rowspan="2" width="7%" class="td-title">Quantity</td>
				<td rowspan="2" width="3%" class="td-title">Cury</td>
				<td rowspan="2" width="10%" class="td-title">Price<br/>Unit</td>
				<td rowspan="2" width="7%" class="td-title">Price<br/>USD</td>
			</tr>
			<tr class="tr-title">
				<td width="7%" class="td-title">ID</td>
				<td width="13%" class="td-title">Description</td>
				<td width="5%" class="td-title">Code</td>
				<td width="15%" class="td-title">Name</td>
				<td width="7%" class="td-title">Date</td>
				<td width="13%" class="td-title">Number</td>
			</tr>
		</thead>
	% for product in sorted(result_grouped.keys(),key=lambda l:l[0]):
		<tfoot>
			<tr width="100%">
				<td colspan="10" width="100%">
				</td>
			</tr>
		</tfoot>
		<tbody>
			<tr>
				<td colspan="10" class="td-loc_title">${"%s - %s"%(product[0],product[1])}</td>
			</tr>
			%for supplier in sorted(result_grouped[product].keys(),key=lambda m:m[0]):
				<tr>
					<td colspan="10" class="td-loc_title">${"[%s] %s"%(supplier[0],supplier[1])}</td>
				</tr>
				<%
				lines = sorted(result_grouped[product][supplier], key=lambda x:x['po_date'])
				%>
				% for line in lines:
					<% price_usd=get_price_usd(line['po_id'],line['commpany_curr_id'],line['price_after_discount'],line['date_order'])%>
					<tr>
						<td class="td-details">${line['prod_code'] or ''}</td>
						<td class="td-details">${line['prod_name'] or ''}</td>
						<td class="td-details">${line['partner_code'] or ''}</td>
						<td class="td-details">${line['partner_name'] or ''}</td>
						<td class="td-details">${line['po_date'] or ''}</td>
						<td class="td-details">${line['po_name'] or ''}</td>
						<td class="td-details" align="center">${line['uom'] or ''}</td>
						<td class="td-details" align="right">${formatLang(line['qty'],digits=2) or ''}</td>
						<td class="td-details" align="center">${line['currency_name'] or ''}</td>
						<td class="td-details" align="right">
							<!-- ${formatLang(line['price_unit'],digits=2) or ''} -->
							${formatLang(line['price_after_discount'],digits=2) or ''}
						</td> 
						<td class="td-details" align="right">${formatLang(price_usd,digits=2) or ''}</td>
					</tr>
				% endfor
			% endfor
	% endfor
		</tbody>
	</table>
% endfor
</body>
</html>