<html>
<head>
	<style type="text/css">
		body {
				font-family:Arial;
				font-size: 10px;
		}

		table{
			border-collapse: collapse;
			width: 100%;
		}
		table tr {
			width: 100%;
		}
		td, th {
			vertical-align: top;
			padding: 3px;
		}

		table.content-header td {
			font-weight: bold;
			text-align: center;
			font-size: 15px;
		}

		table.list_table1 th{
			border:1px solid;
		}
		tr.journal_item2{
			border-top:1px solid;
		}

	</style>
</head>
<body>
	<% setLang(company.partner_id.lang) %>
	<table class="content-header">
		<tr>
			<td>
				${company.name}
			</td>
		</tr>
		<tr>
			<td>
				% if data.get('header',False):
					${data['header']}
				% else:
					Journal Entry
				% endif
			</td>
		</tr>
	</table>
	<hr size="2px" color="white">

	<table class="list_table1">
		<thead>
		<tr>
			<!-- <th width="8%">${_("Journal")}</th> -->
			<th width="7%">${_("Account Code")}</th>
			<th width="15%">${_("Account Desc")}</th>
			<th width="8%">${_("Batch.No")}</th>
			<th width="9%">${_("Reference")}</th>
			<th width="7%">${_("Trans. Date")}</th>
			<th width="19%">${_("Desc")}</th>
			<th width="3%">${_("Curr")}</th>
			<th width="14%">${_("Trans. Amt")}</th>
			<th width="4%">${_("Rate")}</th>
			<th width="14%">${_("USD Amt")}</th>
		</tr>
		</thead>
		<%
		i = 1
		totdebit = total_amt_dr_curr = 0
		line_dr_summary = {}
		%>
		%for line in get_move_lines(o for o in objects):
			%if line['type_line']=='dr' :
				<%
					key = (line['partner_name'],line['account_code'],line['account_name'],line['trans_currency'],line['rate_currency'])
					if key not in line_dr_summary:
						line_dr_summary.update({key:[0.0,0.0]})
					line_dr_summary[key][0]+=abs(line['trans_amt'])
					line_dr_summary[key][1]+=line['debit']
				%>
			<tr class='journal_item'>
				<td style="text-align:center;" >${line['account_code']|entity}</td>
				<td style="text-align:left;" >${line['account_name']|entity}</td>
				<td style="text-align:left;" >${line['batch']|entity}</td>
				<td style="text-align:left;" >${line['referense']|entity}</td>
				<td style="text-align:center;" >${line['date_maturity']|entity}</td>
				<td style="text-align:left;" >${line['description']|entity}</td>
				<td style="text-align:center;" >${line['trans_currency']|entity}</td>
				<td style="text-align:right;" >${formatLang(abs(line['trans_amt']),digits=get_digits(dp='Account')) or 0.0}</td>
				<td style="text-align:right;" >${formatLang(line['rate_currency'],digits=get_digits(dp='Account')) or 0.0}</td>
				<td style="text-align:right;" >${line['debit']|entity}</td>
			</tr>
				<% total_amt_dr_curr += abs(line['trans_amt']) %>
			%endif
			<%
			i=i+1
			totdebit += line['debit']
			%>
		%endfor
		
		<tr class='journal_item2'>
			<td style="text-align:left;" colspan="7"><b>Total DR</b></td>
			<td style="text-align:right;"><b>${ formatLang(total_amt_dr_curr,digits=get_digits(dp='Account')) or 0}</b></td>
			<td style="text-align:right;"></td>
			<td style="text-align:right;"><b>${ formatLang(totdebit,digits=get_digits(dp='Account')) or 0}</b></td>
		</tr>
		<%
		i = 1
		totcredit = total_amt_cr_curr = 0
		line_cr_summary = {}
		%>
		%for line in get_move_lines(o for o in objects):
			%if line['type_line']=='cr' :
				<%
					key = (line['partner_name'],line['account_code'],line['account_name'],line['trans_currency'],line['rate_currency'])
					if key not in line_cr_summary:
						line_cr_summary.update({key:[0.0,0.0]})
					line_cr_summary[key][0]+=abs(line['trans_amt'])
					line_cr_summary[key][1]+=line['credit']
				%>
			<tr class='journal_item'>
				<td style="text-align:center;" >${line['account_code']|entity}</td>
				<td style="text-align:left;" >${line['account_name']|entity}</td>
				<td style="text-align:left;" >${line['batch']|entity}</td>
				<td style="text-align:left;" >${line['referense']|entity}</td>
				<td style="text-align:center;" >${line['date_maturity']|entity}</td>
				<td style="text-align:left;" >${line['description']|entity}</td>
				<td style="text-align:center;" >${line['trans_currency']|entity}</td>
				<td style="text-align:right;" >${formatLang(abs(line['trans_amt']),digits=get_digits(dp='Account')) or 0.0}</td>
				<td style="text-align:right;" >${formatLang(line['rate_currency'],digits=get_digits(dp='Account')) or 0.0}</td>
				<td style="text-align:right;" >${line['credit']|entity}</td>
			</tr>
				<% total_amt_cr_curr += abs(line['trans_amt']) %>
			%endif
			<%
			i=i+1
			totcredit += line['credit']
			%>
		%endfor
		
		<tr class='journal_item2'>
			<td style="text-align:left;" colspan="7"><b>Total CR</b></td>
			<td style="text-align:right;"><b>${ formatLang(total_amt_cr_curr,digits=get_digits(dp='Account')) or 0}</b></td>
			<td style="text-align:right;"></td>
			<td style="text-align:right;"><b>${ formatLang(totcredit,digits=get_digits(dp='Account')) or 0}</b></td>
		</tr>
	</table>
	% if objects and not objects[0].statement_id:
	<center style="page-break-before:always;"><b>Journal Item Summary</b></center>
	% else:
	<table width="100%" style="page-break-before:always;">
		<tr valign="top">
			<td width="100%" style="font-family:Arial Black;" colspan="4" style="font-size:12" align="center">
			PT. Bitratex Industries
			</td>
		</tr>
		<tr valign="top">
			<td width="100%" style="font-family:Arial Black;" colspan="4" style="font-size:14" align="center"><u>
			% if data.get('header',False):
				${data['header']}
			% else:
				Journal Entry
			% endif
			</u>
			</td>
		</tr>
	</table>
	<table width="100%">
		<tr class="list_table1" style="font-family:Arial Black;">
			<td width="65%">Number. ${objects and objects[0].statement_id and objects[0].statement_id.name or ''|entity}</td>
			<td width="10%"></td>
			<td width="2%"></td>
			<td width="23%"></td>
		</tr>
		<tr class="list_table1" style="font-family:Arial Black;">
			<td width="65%">Jurnal. ${objects and objects[0].statement_id and objects[0].statement_id.journal_id.name or ''|entity}</td>
			<td width="10%">Tanggal</td>
			<td width="2%">:</td>
			<td width="23%">${time.strftime('%d %b %Y', time.strptime(objects and objects[0].statement_id and objects[0].statement_id.date,'%Y-%m-%d')) or ''|entity}</td>
		</tr>
		<tr class="list_table1" style="font-family:Arial Black;">
			<td width="65%">Referensi : </td>
			<td width="10%">Periode</td>
			<td width="2%">:</td>
			<td width="23%">${objects and objects[0].statement_id and objects[0].statement_id.period_id.name or ''|entity}</td>
		</tr>
	</table>
	% endif
	<table class="list_table1">
		<tr>
			<th width="7%">${_("Account Code")}</th>
			<th width="28%">${_("Account Desc")}</th>
			<th width="30%">${_("Partner")}</th>
			<th width="3%">${_("Curr")}</th>
			<th width="14%">${_("Trans. Amt")}</th>
			<th width="4%">${_("Rate")}</th>
			<th width="14%">${_("USD Amt")}</th>
		</tr>
		% if line_dr_summary:
			% for k in sorted(line_dr_summary.keys(), key=lambda k:(k[1],k[0])):
				<tr>
					<td width="7%">${k[1]}</td>
					<td width="28%">${k[2]}</td>
					<td width="30%">${k[0]}</td>
					<td width="3%">${k[3]}</td>
					<td align="right" width="14%">${formatLang(line_dr_summary[k][0],digits=get_digits(dp='Account')) or 0}</td>
					<td align="right" width="4%">${k[4]}</td>
					<td align="right" width="14%">${formatLang(line_dr_summary[k][1],digits=get_digits(dp='Account')) or 0}</td>
				</tr>
			% endfor
			<tr class='journal_item2'>
				<td style="text-align:left;" colspan="4"><b>Total DR</b></td>
				<td style="text-align:right;"><b>${ formatLang(total_amt_dr_curr,digits=get_digits(dp='Account')) or 0}</b></td>
				<td style="text-align:right;"></td>
				<td style="text-align:right;"><b>${ formatLang(totdebit,digits=get_digits(dp='Account')) or 0}</b></td>
			</tr>
		% endif
		% if line_cr_summary:
			% for k in sorted(line_cr_summary.keys(), key=lambda k:(k[1],k[0])):
				<tr>
					<td width="7%">${k[1]}</td>
					<td width="28%">${k[2]}</td>
					<td width="30%">${k[0]}</td>
					<td width="3%">${k[3]}</td>
					<td align="right" width="14%">${formatLang(line_cr_summary[k][0],digits=get_digits(dp='Account')) or 0}</td>
					<td align="right" width="4%">${k[4]}</td>
					<td align="right" width="14%">${formatLang(line_cr_summary[k][1],digits=get_digits(dp='Account')) or 0}</td>
				</tr>
			% endfor
			<tr class='journal_item2'>
				<td style="text-align:left;" colspan="4"><b>Total CR</b></td>
				<td style="text-align:right;"><b>${ formatLang(total_amt_cr_curr,digits=get_digits(dp='Account')) or 0}</b></td>
				<td style="text-align:right;"></td>
				<td style="text-align:right;"><b>${ formatLang(totcredit,digits=get_digits(dp='Account')) or 0}</b></td>
			</tr>
		% endif
	</table>

	<br/><br/>
	<table class="list_table1" border="1" >
		<tr style="text-align:center;">
			<td width="25%">Prepared By</td>
			<td width="25%">Checked By</td>
			<td width="25%">Approved By</td>
			<td width="25%">Received By</td>
		</tr>
		<tr>
			<td style="text-align:center;"><br/><br/><br/><br/></td>
			<td style="text-align:center;"></td>
			<td style="text-align:center;"></td>
			<td style="text-align:center;"></td>
		</tr>
	</table>	
</body>
</html>
