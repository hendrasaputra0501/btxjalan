<html>
<head>
	<style type="text/css">
		body{
			font-size: 10px;
			font-family: arial;
		}
		table{
			font-family: "calibri";
			font-size: 10px;
			margin: 0px;
			padding: 0px;
			width:100%;
			border-collapse: collapse;
		}
		.header{
			text-align: center;
			border-top: 1px solid;
			border-bottom: 1px solid;
		}
		.subtotal{
			border-top: 1px dashed;
		}
		#footer {
			width:100%;
			height:130px;
			position:absolute;
			bottom:0;
			left:0;
		}
	</style>
</head>
<%
	results = get_result(data)
	result_summary = []
%>
<body>
	<table>
		<thead>
			<tr class="header" width="100%">
				<td width="7%" rowspan="2">Invoice</td>
				<td width="12%" colspan="2">Surat Jalan</td>
				<td width="12%" rowspan="2">Customer</td>
				<td width="8%" rowspan="2">Destination Port</td>
				<td width="2%" rowspan="2">Container<br/>Size</td>
				<td width="10%" rowspan="2">Shipping Lines</td>
				<td width="16%" colspan="2">BL</td>
				<td width="14%" rowspan="2">Carrier</td>
				<td width="7%" rowspan="2">Bill Number</td>
				<td width="5%" rowspan="2">Bill Date</td>
				<td width="7%" rowspan="2">Amount</td> 
				<!-- <td width="6%" rowspan="2">Due Date</td> -->
			</tr>
			<tr class="header">
				<td width="7%">Number</td>
				<td width="5%">Date</td>
				<td width="11%">Number</td>
				<td width="5%">Date</td>
			</tr>
		</thead>
		<% total0 = 0.0 %>
		% for key in results[3].keys():
		<tr>
			<td valign="top" align="left" colspan="13"><b>Due Date : ${key or ''}<b/></td>
		</tr>
			% for res in results[3][key]:
			<tr>
				<td valign="top" align="left">${res['related_invoice'] or ''}</td>
				<td valign="top" align="left">${res['picking_name'] or ''}</td>
				<td valign="top" align="center">${res['picking_date'] or ''}</td>
				<td valign="top" align="left">${res['party'] or ''}</td>
				<td valign="top" align="left">${res['dest_port'] or ''}</td>
				<td valign="top" align="left">${res['container'] or ''}</td>
				<td valign="top" align="left">${res['shipping_lines'] or ''}</td>
				<td valign="top" align="left">${res['bl_number'] or ''}</td>
				<td valign="top" align="center">${res['bl_date'] or ''}</td>
				<td valign="top" align="left">${res['partner_code'] or ''} ${res['partner_name'] or ''}</td>
				<td valign="top" align="left">${res['inv_number'] or ''}</td>
				<td valign="top" align="center">${res['bill_date'] or ''}</td>
				<td valign="top" align="right">${formatLang(res['amount']) or ''}</td>
			</tr>
			<% total0 += res['amount'] %>
			% endfor
		% endfor
		<tr  style="border-top:1px solid;border-bottom:1px solid">
			<td align="center" colspan="12"><b>Total</b></td>
			<td align="right"><b>${formatLang(total0) or ''}</b></td>
		</tr>
	</table>
	
	% for key in results[1]:
		<% total = 0 %>
		% for key2 in results[1][key]:
			<% subtotal = 0 %>
			% for key3 in results[1][key][key2]:
				%for res in results[1][key][key2][key3]:
					<% subtotal += res['amount'] %>
				% endfor
			% endfor
			<% result_summary.append([key2[0],key2[1],subtotal,key]) %>
			<% total += subtotal %>
		% endfor
	% endfor
	% if result_summary:
	<br/>
	<br/>
	<br/>
	<table style="width:50%;">
	<thead>
	<tr width="100%" class="header">
		<td colspan="4" align="left">Total Summary</td>
	</tr>
	</thead>
	% for line in result_summary:
	<tr width="100%">
		<td align="left" width="10%">${line[0]}</td>
		<td align="left" width="50%">${line[1]}</td>
		<td align="right" width="30%">${formatLang(line[2])}</td>
		<td align="center" width="10%">${line[3]}</td>
	</tr>
	% endfor
	<tr width="100%" style="border-top:1px solid">
		<td align="left" width="10%"><b>Total</b></td>
		<td align="left" width="50%"></td>
		<td align="right" width="30%"><b>${formatLang(total)}</b></td>
		<td align="center" width="10%"></td>
	</tr>
	</table>
	% endif
	<table width='100%'>
		<tr width='100%'>
			<td width='30%'><br/>&nbsp;<br/>&nbsp;
			</td>
			<td width='30%'><br/>&nbsp;<br/>&nbsp;
			</td>
			<td  width='30%'><br/>&nbsp;<br/>&nbsp;
			</td>
		</tr>
		<tr width='100%'>
			<td width='30%'>Prepared By : 
			</td>
			<td width='30%'>Checked By : 
			</td>
			<td  width='30%'>Approved By : 
			</td>
		</tr>
	</table>
</body>
</html>