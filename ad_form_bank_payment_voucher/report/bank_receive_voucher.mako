<html>
	<head>
	<style>
		th {
		text-align:left;
		}
		table.voucher_header{
			font-size:11px;
		}
		table.move_lines{
			font-size:9px;
			border-collapse:collapse;
			border-color:#CCCCCC;
			/*
			border-top:2px solid #C9C9C9;
			border-bottom:2px solid #C9C9C9;
			border-left:2px solid #C9C9C9;
			border-right:2px solid #C9C9C9;
			*/
		}
		table.tr_description{
			font-size:9px;

		}
		table.tr_description2{
			font-size:9px;
		}
		table.voucher_header tr th{
			padding:3px 3px 3px 3px;
		}
		.voucher_header_left{
			width:120px;
			font-size:12px;
		}
		.voucher_header_right{
			width:300px;
		}
		table tr td.valign{
			vertical-align:top;
		}
		td.amount{
			text-align:right;
		}
		th.acc_no,th.acc_name,th.debit,th.credit,th.amount,th.amount_header{
			text-align:center;
		}
		.acc_no{
			width:105px;
		}
		.amount{
			min-width:70px;
		}
		td.cq_1{
			min-width:25%;
			width:25%;
		}
		td.cq_2{
			min-width:25%;
			width:25%;
			border-bottom:1px solid #CCC;
		}
		td.cq_3{
			min-width:25%;
			width:25%;
		}
		td.cq_4{
			min-width:25%;
			width:25%;
			border-bottom:1px solid #CCC;
		}

		td.pp{
			min-width:15%;
			width:15%;
		}
		td.pp2{
			min-width:35%;
			width:35%;
			border-bottom:1px solid #CCC;
		}
	</style>
	</head>
	<body>
	<% 
	setLang(company.partner_id.lang) 
	%>
	%for voucher in objects:
		<center class="head_title"><h1>BANK RECEIVE VOUCHER</h1></center>
		<table class="voucher_header" width="100%">
			<tr>
				<th class="voucher_header_left" colspan="2" rowspan="2" style="vertical-align:top;">${voucher.company_id and voucher.company_id.name.upper() or ""}</th>
				<th>No</th>
				<th>: BM/${voucher.number or ""}</th>
			</tr>
			<tr>
				<th>Tgl</th>
				<th>: ${voucher.date or ""}</th>
			</tr>
			<tr>
				<th class="voucher_header_left">Bank</th>
				<th class="voucher_header_right">: ${voucher.journal_id and voucher.journal_id.name or ""}</th>
				<th>&nbsp;</th>
				<th>&nbsp;</th>
			</tr>
			<tr>
				<th class="voucher_header_left">Please Pay To</th>
				<th class="voucher_header_right">: ${voucher.partner_id and voucher.partner_id.name or ""}</th>
				<th>&nbsp;</th>
				<th>&nbsp;</th>
			</tr>
			<tr>
				<th class="voucher_header_left">The Sum of</th>
				<th class="voucher_header_right" colspan="4">: ${voucher.currency_id.symbol} ${voucher.amount or 0.0}</th>
			</tr>
			<tr>
				<th class="voucher_header_left">Description</th>
				<th class="voucher_header_right" colspan="4" style="border-bottom:1px solid #CCC;">: ${voucher.name or ""}</th>
			</tr>
		</table>
		<br/>
		<table class="move_lines" width="100%" border="1">
			<tr>
				<th rowspan="2" class="acc_no valign">Acc. No</th>
				<th rowspan="2" class="acc_name valign">Account Name</th>
				<th colspan="2" class="amount_header">Amount</th>
			</tr>
			<tr>
				<th class="debit">Debit</th>
				<th class="credit">Credit</th>
			</tr>

			%for move_line in sorted(voucher.move_ids,key=lambda x: x['credit']):
				<tr>
					<td class="acc_no" style="padding-left:${move_line.credit and 20 or 5}px">${move_line.account_id and move_line.account_id.code or ""}</td>
					<td class="acc_name" style="padding-left:${move_line.credit and 20 or 5}px">${move_line.account_id and move_line.account_id.name or ""}</td>
					<td class="amount">${move_line.debit or ""}</td>
					<td class="amount">${move_line.credit or ""}</td>
				</tr>
			%endfor
			<tr>
				<td colspan="2" style="text-align:center"><b>TOTAL</b></td>
				<td class="amount">${ formatLang(sum([mvl.debit for mvl in voucher.move_ids]),digits=get_digits(dp='Account')) or 0.0}</td>
				<td class="amount">${ formatLang(sum([mvl.credit for mvl in voucher.move_ids]),digits=get_digits(dp='Account')) or 0.0}</td>
			</tr>
		</table>
		<br>
		<table class="tr_description" width="100%">
			<tr>
				<td class="cq_1"></td>
				<td class="cq_2">&nbsp;</td>
				<td class="cq_3">Bank</td>
				<td class="cq_4">&nbsp;</td>
			</tr>
			<tr>
				<td style="padding-left:38px;" class="cq_1"></td>
				<td class="cq_2">&nbsp;</td>
				<td class="cq_3">Acc. No</td>
				<td class="cq_4">&nbsp;</td>
			</tr>
			<tr>
				<td style="padding-left:38px;" class="cq_1"></td>
				<td class="cq_2">&nbsp;</td>
			</tr>
			<tr>
				<td class="cq_1">Date of Cheque/BG/Transfer</td>
				<td class="cq_2">&nbsp;</td>
			</tr>
		</table>
		<br>
		<table class="tr_description2" width="100%">
			<tr>
				<td class="pp">Prepared By:</td>
				<td class="pp2">&nbsp;</td>
				<td class="pp">Received By:</td>
				<td class="pp2">&nbsp;</td>
			<tr>
			<tr>
				<td colspan="4">&nbsp;</td>
			</tr>
			</tr>
				<td class="pp">Posted By:</td>
				<td class="pp2">&nbsp;</td>
				<td class="pp">Checked/Approved By:</td>
				<td class="pp2">&nbsp;</td>
			</tr>
		</table>
	%endfor
	</body>
</html>