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
		border:1px solid black;
	}
	table.content-table tr, table.content-table th, table.content-table td{
		border:1px solid black;
		padding: 2px;
		font-size: 10px;
	}
	tr.content-tr-subtotal td {
		border:0px;
	}
	</style>
</head>
<body>
<%
	from datetime import datetime
%>
% for o in objects:
	<table class="content-header">
		<tr>
			<td colspan="2" width="50%">
				To&nbsp;&nbsp;&nbsp;:<br/>
				${o.company_bank_id and (o.company_bank_id.bank and o.company_bank_id.bank.name or o.company_bank_id.bank_name) or ''}<br/>
				${o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.street or ''}<br/>
				%if o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.street2:
					${o.company_bank_id.bank.street2 or ''}<br/>
				%endif
				%if o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.city:
					${o.company_bank_id.bank.city or ''}&nbsp;
				%endif
				%if o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.zip:
					${o.company_bank_id.bank.zip or ''},&nbsp;
				%endif
				%if o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.state:
					${o.company_bank_id.bank.state.name or ''}.&nbsp;
				%endif
				%if o.company_bank_id and o.company_bank_id.bank and o.company_bank_id.bank.country:
					${o.company_bank_id.bank.country.name or ''}
				%endif
			</td>
			<td width="50%" align="right">Semarang, 
				<% 
				doc_date = o.document_date or o.date or False
				date = doc_date and datetime.strptime(doc_date,"%Y-%m-%d").strftime("%d %b %Y") or '' %>
				${date} 
			</td>
		</tr>
		<tr>
			<td width="10%">Attn.</td>
			<td width="40%">:&nbsp;&nbsp;&nbsp;${o.attention or ''}</td>
			<td width="50%"></td>
		</tr>
		<tr>
			<td width="10%">CC.</td>
			<td width="40%">:&nbsp;&nbsp;&nbsp;${o.cc or ''}</td>
			<td width="50%"></td>
		</tr>
		<tr>
			<td colspan="3"></td>
		</tr>
		<tr>
			<td colspan="3" style="padding-left:20px;">
				Please debit our account no. ${o.company_bank_id and o.company_bank_id.acc_number or 'None'} date ${o.date!='False' and formatLang(o.date, date=True) or '-'} for transfering to some party<br/>
				with the following details:
			</td>
		</tr>
	</table>
	<br/>
	<table class="content-table">
		<thead>
			<tr>
				<th>No.</th>
				<th>Supplier</th>
				<th>Rekening Address</th>
				<th>Amount (${o.journal_id and o.journal_id.currency and o.journal_id.currency.name or 'USD'})</th>
				<th>Invoice Ref</th>
			</tr>
		</thead>
		<% 
			n = 0
			total_amount = 0.0 
			line_grouped = get_lines_grouped(o.line_ids)
		%>
		% for key in (line_grouped and sorted(line_grouped.keys(), key=lambda x:x[1]) or []):
			<% 
				n+=1 
				total_amount+=abs(line_grouped[key]['amount'])
			%>
			<tr>
				<td>${n}</td>
				<td>${line_grouped[key]['partner_name'] or ''}</td>
				<td>
					${line_grouped[key]['bank_name'] or '' }<br/>
					No.Rek ${line_grouped[key]['acc_number'] or '' }<br/>
					a.n ${line_grouped[key]['owner_name'] or '' }
				</td>
				<td align="right">${formatLang(abs(line_grouped[key]['amount']))}</td>
				<td>
					${line_grouped[key]['ref'] and line_grouped[key]['ref'].replace('\n','<br/>') or ''}
				</td>
			</tr>
		% endfor
		<tr class="content-tr-subtotal">
			<td colspan="3" align="center">T O T A L</td>
			<td align="right">${formatLang(total_amount)}</td>
			<td></td>
		</tr>
	</table>
	<br/>
	<table class="content-footer">
		<tr>
			<td colspan="3" style="padding-left:20px;">
				Kindly acknowledge receipt to this instruction letter and advice us after affecting the above transfer </br>
				<br/>
				Thanking you for kind attention and cooperation<br/>
				<br/>
				Your Faithfully,<br/>
				PT Bitratex Industries<br/>
				<br/>
				<br/>
				<br/>
				<br/>
				Authorised signatory
			</td>
		</tr>
	</table>
% endfor
</body>
</html>
