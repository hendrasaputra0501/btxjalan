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
			text-align: center;
		}
		.header{
			vertical-align: top;
			text-align: center;
			border-top: 1px solid black;
			border-bottom: 1px solid black;
		}

	</style>
</head>
<body>
	% for o in objects:
	<center> Bitratex Industries </center>
	<center> BILL PASSING ADVICE OF OTHER EMKL COST </center>
	<center> BPA No : ${o.number or ''} Date : ${o.request_date} </center>
	<table>
		<tr class="header">
			<td width='4%' >SR<br />No</td>
			<td width='12%' align="left">Invoice</td>
			<td width='10%' align="left">LC<br />Batch</td>
			<td width='20%' align="left">Container</td>
			<td width='4%' ></td>
			<td width='4%' align="left">Date</td>
			<td width='4%' >Bill</td>
			<td width='4%' >Amount</td> 
			<td width='4%' >Carrier</td>
			<td width='3%' >Curry Id</td>
			<td width='7%' >BPA<br />Amount</td>
			<td width='20%' >Party</td>
			<td width='4%' >Due Date</td>
		</tr>
		% for line in o.ext_line:
		<tr>
			<td></td>
			<td align="left">${line.invoice_related_id and line.invoice_related_id.internal_number or ''}</td>
			<td align="left">${ get_lc_number(line.invoice_related_id and line.invoice_related_id or False) }</td>
			<td align="left">${ get_container_number(line.invoice_related_id and line.invoice_related_id or False) }</td>
			<td align="left">${line.invoice_related_id and line.invoice_related_id.date_invoice or''}</td>
			<td></td>
			<td></td>
			<td>${line.debit and line.debit or 0}</td>
			<td align="left">${line.partner_id and line.partner_id.name or ''}</td>
			<td>${o.currency_id and o.currency_id.name or ''}</td>
			<td>${line.debit and line.debit or 0}</td>
			<td align="left">${line.invoice_related_id and line.invoice_related_id.partner_id.name or ''}</td>
			<td>${o.due_date and o.due_date or 0}</td>
		</tr>
		% endfor
	</table>
	% endfor
</body>
</html>