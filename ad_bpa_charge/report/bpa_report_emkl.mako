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
				<td width="20%" colspan="2">Surat Jalan</td>
				<td width="15%" rowspan="2">Party</td>
				% if data['form']['type_of_charge'][1].encode('utf-8').upper() == 'TRANSPORT':
					<td width="15%" rowspan="2">Truck No.</td>
					<td width="10%" rowspan="2">Qty</td>
					<td width="10%" rowspan="2">Rate</td>
				% else:
					<td width="15%" rowspan="2">Container</td>
					<td width="10%" rowspan="2">Bill Number</td>
					<td width="8%" rowspan="2">Bill Date</td>
				% endif
				<td width="14%" rowspan="2">Amount</td>
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
				<% subtotal_qty = 0 %>
				<% summary_party = {} %>
				% for key3 in results[2][key][key2]:
		<tr>
			<td colspan="7" align="left"><b>Carrier ${(key2[0] or '')+' '+key2[1] or ''}<br/>${str(key3) or ''}</b></td>
		</tr>
					% for res in results[2][key][key2][key3]:
						<% 
						if res['party'] not in summary_party:
							summary_party.update({res['party']:{'amount':0.0,'qty':0.0}})
						summary_party[res['party']]['amount']+=res['amount']
						summary_party[res['party']]['qty']+=res['qty']
						%>

		<tr>
			<td valign="top" align="left">${res['related_invoice'] or ''}</td>
			<td valign="top" align="left">${res['picking_name'] or ''}</td>
			<td valign="top" align="center">${res['picking_date'] or ''}</td>
			<td valign="top" align="left">${res['party'] or ''}</td>
			% if data['form']['type_of_charge'][1].encode('utf-8').upper() == 'TRANSPORT':
				<td valign="top" align="center">${res['container'] or ''}</td>
				<td valign="top" align="right">${res['qty'] or ''}</td>
				<td valign="top" align="right">${res['price_unit'] or ''}</td>
			% else:
				<td valign="top" align="left">${res['container'] or ''}</td>
				<td valign="top" align="left">${res['inv_number'] or ''}</td>
				<td valign="top" align="center">${res['bill_date'] or ''}</td>
			% endif
			<td valign="top" align="right">${formatLang(res['amount']) or ''}</td>
		</tr>
						<% subtotal += res['amount'] %>
						<% subtotal_qty += res['qty'] %>
					% endfor
				% endfor
		<!-- <tr class="subtotal">
			<td colspan="6" align="left">Subtotal ${(key2[0] or '')+' '+key2[1] or ''}</td>
			<td align="right">${subtotal or 0}</td>
		</tr> -->
				<% result_summary.append([key2[0],key2[1],subtotal,subtotal_qty,key,summary_party]) %>
				<% total += subtotal %>
			% endfor
		<tr class="subtotal">
			<td colspan="7" align="left"><b>Subtotal ${key or ''}</b></td>
			<td align="right">${formatLang(total) or 0}</td>
		</tr>
		% endfor
	</table>
	% if result_summary:
	<br/>
	<br/>
	<br/>
	<table style="width:60%;">
	<thead>
		<tr width="100%" class="header">
			<td colspan="3" align="center">&nbsp;</td>
			<td align="center">Total Qty</td>
			<td colspan="2" align="center">Total Summary</td>
		</tr>
	</thead>
	% for line in result_summary:
	<tr width="100%" style='background-color:#D1D0D0;'>
		<td align="left" width="5%">${line[0]}</td>
		<td colspan="2" align="left" width="50%">${line[1]}</td>
		<td align="right" width="20%">${formatLang(line[2])}</td>
		<td align="right" width="20%">${formatLang(line[3])}</td>
		<td align="center" width="5%">${line[4]}</td>
	</tr>
		% if line[4]:
			% for k,v in line[5].items():
			<tr width="100%">
				<td align="left" width="5%"> </td>
				<td align="left" width="5%"> </td>
				<td align="left" width="40%">${k or ''}</td>
				<td align="right" width="20%">${formatLang(v['qty'])}</td>
				<td align="right" width="20%">${formatLang(v['amount'])}</td>
				<td align="center" width="10%">${line[3]}</td>
			</tr>
			% endfor
		% endif
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