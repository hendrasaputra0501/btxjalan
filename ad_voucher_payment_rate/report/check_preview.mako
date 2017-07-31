<html>
<head>
	<style type="text/css">
	body{
		font-family: Arial;
		font-size: 12px;
		/*width: 100%;*/
	}
	table, table tr{
		width: 100%;
	}
	tr {
		vertical-align: top;
	}
	table.content-table {
		border-collapse: collapse;
		/*border:1px solid black;*/
	}
	table.content-table thead {
		border-top:2px solid black;
		border-bottom:2px solid black;
	}
	table.content-table tr, table.content-table td{
		padding: 2px;
		font-size: 10px;
	}
	td.content-td-subtotal {
		padding-top: 0px;
		border-top:1px solid black;
	}
	</style>
</head>
<body>
<%
	from datetime import datetime
%>
% for o in objects:
	<table class="content-table">
		<thead>
			<tr>
				<td width="9%" valign="bottom" align="center" style="border-bottom:1px solid black;padding-bottom:0px;">Check Batch</td>
				<td width="9%" valign="bottom" align="center" style="border-bottom:1px solid black;padding-bottom:0px;">Vendor ID</td>
				<td width="16%" valign="bottom" align="center" style="border-bottom:1px solid black;padding-bottom:0px;">Vendor Status</td>
				<td width="8%" valign="bottom" align="center" style="border-bottom:1px solid black;padding-bottom:0px;">Vendor Name</td>
				<td width="8%" rowspan="2" align="left">Pay<br/>Date</td>
				<td width="8%" rowspan="2" align="left">Due<br/>Date</td>
				<td width="21%" rowspan="2" align="right">Document<br/>Balance</td>
				<td width="21%" rowspan="2" align="right">Amount<br/>To Pay</td>
			</tr>
			<tr>
				<td valign="top" align="center" style="padding-top:0px;">Doc Type</td>
				<td valign="top" align="center" style="padding-top:0px;">Ref Nbr</td>
				<td valign="top" align="center" style="padding-top:0px;">Invoice Nbr</td>
				<td valign="top" align="center" style="padding-top:0px;">Invc Date</td>
			</tr>
		</thead>
		<% 
			n = 0
			total_amount = 0.0 
			line_grouped = get_lines_grouped(o.line_ids)
		%>
		% for key in (line_grouped and sorted(line_grouped.keys(), key=lambda x:(x and x.partner_code or False)) or []):
			<% 
				total_amount+=abs(line_grouped[key]['amount_to_pay'])
				subtotal = 0.0
			%>
			<tr>
				<td>${o.name or ''}</td>
				<td>${key and key.partner_code or ''}</td>
				<td></td>
				<td colspan="5">
					${key and key.name or ''}
				</td>
			</tr>
			% for line in (line_grouped[key]['lines'] and sorted(line_grouped[key]['lines'],key = lambda l:(l.move_line_id and l.move_line_id.date or False)) or []):
				<%
					subtotal+=abs(line.amount)
				%>
			<tr>
				<td> </td>
				<td>${line.move_line_id and line.move_line_id.ref or ''}</td>
				<td>${line.move_line_id and (line.move_line_id.invoice and line.move_line_id.invoice.internal_number or line.move_line_id.name) or ''}</td>
				<td>${line.move_line_id and formatLang(line.move_line_id.date, date=True) or ''}</td>
				<td>${formatLang(o.date, date=True) or ''}</td>
				<td>${line.move_line_id and line.move_line_id.date_maturity!='False' and formatLang(line.move_line_id.date_maturity, date=True) or ''}</td>
				<td align="right">${formatLang(abs(line.amount or 0.0), digits=2)}</td>
				<td align="right">${formatLang(abs(line.amount or 0.0), digits=2)}</td>
			</tr>
			% endfor
			<tr>
				<td colspan="6" > </td>
				<td class="content-td-subtotal" >Check Total</td>
				<td class="content-td-subtotal" align="right">${formatLang(subtotal)}</td>
			</tr>	
		% endfor
		<tr>
			<td colspan="6" > </td>
			<td class="content-td-subtotal"><b>Company Total</b></td>
			<td class="content-td-subtotal" align="right"><b>${formatLang(total_amount)}</b></td>
			<td></td>
		</tr>
	</table>
% endfor
</body>
</html>
