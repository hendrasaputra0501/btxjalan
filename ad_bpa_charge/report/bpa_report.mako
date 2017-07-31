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
			<td width="10%" rowspan="2">Invoice</td>
			<td width="20%" colspan="2">BL</td>
			<td width="10%" rowspan="2">Surat Jalan</td>
			<td width="30%" rowspan="2">Carrier</td>
			<td width="8%" rowspan="2">Bill Date</td>
			<td width="14%" rowspan="2">Amount</td> 
			<td width="8%" rowspan="2">Due Date</td>
		</tr>
		<tr class="header">
			<td width="12%">Number</td>
			<td width="8%">Date</td>
		</tr>
		</thead>
		% for key in results[2]:
			<% total = 0 %>
			% for key2 in results[2][key]:
				<% subtotal = 0 %>
				% for key3 in results[2][key][key2]:
		<tr>
			<td colspan="8" align="left">Carrier ${(key2[0] or '')+' '+key2[1]+' '+str(key3) or ''}</td>
		</tr>
					% for res in results[2][key][key2][key3]:

		<tr>
			<td align="left">${res['related_invoice'] or ''}</td>
			<td align="left">${res['bl_number'] or ''}</td>
			<td align="center">${res['bl_date'] or ''}</td>
			<td align="left">${res['picking_name'] or ''}</td>
			<td align="left">${res['partner_code'] or ''} ${res['partner_name'] or ''}</td>
			<td align="center">${res['bill_date'] or ''}</td>
			<td align="right">${formatLang(res['amount']) or ''}</td>
			<td align="center">${res['due_date'] or ''}</td>
		</tr>
						<% subtotal += res['amount'] %>
					% endfor
				% endfor
		<!-- <tr class="subtotal">
			<td colspan="6" align="left">Subtotal ${(key2[0] or '')+' '+key2[1] or ''}</td>
			<td align="right">${subtotal or 0}</td>
			<td align="center"></td>
		</tr> -->
				<% result_summary.append([key2[0],key2[1],subtotal,key]) %>
				<% total += subtotal %>
			% endfor
		<!-- <tr class="subtotal">
			<td colspan="6" align="left"><b>Subtotal ${key or ''}</b></td>
			<td align="right">${total or 0}</td>
			<td align="center"></td>
		</tr> -->
		% endfor
	</table>
	% if result_summary:
	<br/>
	<br/>
	<br/>
	<table style="width:50%;">
	<thead>
	<tr width="100%" class="header">
		<th colspan="4" align="left">Total Summary</th>
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
	</table>
	%endif
</body>
</html>