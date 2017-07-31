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
	import time
	results = get_result(data)
	result_summary = []
%>
<body>
	<table>
		<thead>
		<tr class="header" width="100%">
			<td width="10%" rowspan="2">Invoice</td>
			<td width="10%" colspan="2">Surat Jalan</td>
			<td width="15%" rowspan="2">Customer</td>
			<td width="10%" rowspan="2">Qty</td>
			<td width="5%" rowspan="2">Rate</td>
			<td width="5%" rowspan="2">UOM</td>
			<td width="14%" rowspan="2">Amount</td>
			<td width="10%" rowspan="2">Bill Number</td>
			<td width="8%" rowspan="2">Bill Date</td>
		</tr>
		<tr class="header">
			<td width="5%">Number</td>
			<td width="5%">Date</td>
		</tr>
		</thead>
		% for key in results:
			<% total = 0 %>
			<% total_qty = 0 %>
			% for key2 in results[key]:
				<% subtotal = 0 %>
		<tr>
			<td colspan="8" align="left"><b>Porters ${(key2[0] or '')+' '+key2[1] or ''}</b></td>
		</tr>
					% for res in results[key][key2]:

		<tr>
			<td valign="top" align="left">${res['related_invoice'] or ''}</td>
			<td valign="top" align="left">${res['picking_name'] or ''}</td>
			<td valign="top" align="center">${res['picking_date'] or ''}</td>
			<td valign="top" align="left">${res['party'] or ''}</td>
			<td valign="top" align="right">${formatLang((res['amount'] and res['amount'] or 0)/(res['cost'] and res['cost'] or 1)) or ''}</td>
			<td valign="top" align="right">${formatLang(res['cost'] and res['cost'] or 0) or ''}</td>
			<td valign="top" align="center">Bale</td>
			<td valign="top" align="right">${formatLang(res['amount']) or ''}</td>
			<td valign="top" align="left">${''}</td>
			<td valign="top" align="center">${res['bill_date'] or ''}</td>
		</tr>
						<% subtotal += res['amount'] %>
						<% total_qty += (res['amount'] and res['amount'] or 0)/(res['cost'] and res['cost'] or 1) %>
					% endfor
		<!-- <tr class="subtotal">
			<td colspan="6" align="left">Subtotal ${(key2[0] or '')+' '+key2[1] or ''}</td>
			<td align="right">${subtotal or 0}</td>
		</tr> -->
				<% result_summary.append([key2[0],key2[1],subtotal,key]) %>
				<% total += subtotal %>
			% endfor
		<tr class="subtotal">
			<td colspan="4" align="left"><b>Subtotal ${key or ''}</b></td>
			<td align="right">${formatLang(total_qty) or 0}</td>
			<td colspan="2" align="left">&nbsp;</td>
			<td align="right">${formatLang(total) or 0}</td>
			<td colspan="2" align="left"></td>
		</tr>
		% endfor
	</table>
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
		<td align="left" width="10%">${line[0] or ''}</td>
		<td align="left" width="50%">${line[1] or ''}</td>
		<td align="right" width="30%">${formatLang(line[2])}</td>
		<td align="center" width="10%">${line[3]}</td>
	</tr>
	% endfor 
	</table>
	%endif
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