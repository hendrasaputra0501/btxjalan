<html>
<head>
	<style type="text/css">
	body{
		font-family:Arial;
		font-size: 8px;
	}

	table {
		border-collapse: collapse;
		width: 100%;
	}

	tr {
		height:15px;
	}

	thead.cont-table-thead td{
		border-top: 1px solid;
		border-bottom: 1px solid;
		text-align: center;
		vertical-align: center;
		font-weight: bold;
	}

	tr.cont-table-lines td{
		vertical-align: top;
	}

	tr.cont-table-trtotal td{
		border-top: 1px solid;
		border-bottom: 1px solid;
		font-weight: bold;
	}
	tr.cont-table-trsubtotal td{
		border-top: 1px dashed;
		font-weight: bold;
	}
	</style>
</head>
<body>
	<% setLang(company.partner_id.lang) %>
	<table class="cont-table">
		<thead class="cont-table-thead">
			<tr>
				<td colspan="3" width="13%">Voucher</td>
				<td colspan="2" width="9%">PO</td>
				<td colspan="2" width="11%">Vendor</td>
				<td colspan="2" width="9%">Surat Jalan</td>
				<td colspan="2" width="9%">Receipt</td>
				<td rowspan="2" width="4%">Pay<br/>Terms</td>
				<td rowspan="2" width="4%">Due<br/>Date</td>
				<td rowspan="2" width="4%">Trans<br/>Cury</td>
				<td rowspan="2" width="4%">Quantity</td>
				<td rowspan="2" width="4%">Unit<br/>Price</td>
				<td rowspan="2" width="4%">Receipt</td>
				<td rowspan="2" width="4%">${company.currency_id.name}</td>
				<td colspan="2" width="8%">Tax Amount</td>
				<td colspan="2" width="8%">PPV</td>
				<td rowspan="2" width="4%"valign="bottom">Remarks</td>
			</tr>
			<tr>
				<td width="4%">Date</td>
				<td width="5%">BatchNo</td>
				<td width="4%">Ref.</td>
				<td width="5%">BatchNo</td>
				<td width="4%">Date</td>
				<td width="4%">ID</td>
				<td width="7%">Name</td>
				<td width="5%">No</td>
				<td width="4%">Date</td>
				<td width="5%">BatchNo</td>
				<td width="4%">Date</td>
				<td width="4%">Tran</td>
				<td width="4%">USD</td>
				<td width="4%">Tran</td>
				<td width="4%">USD</td>
			</tr>
		</thead>
		<% results_group_by_partner = get_results_group_by_partner(objects) %>
		<% total_untaxed, total_untaxed_usd, total_tax, total_tax_usd, total_ppv, total_ppv_usd = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 %>
		% for key in results_group_by_partner and (sorted(results_group_by_partner.keys(), key=lambda k:k[1])) or []:
			<% stotal_untaxed, stotal_untaxed_usd, stotal_tax, stotal_tax_usd, stotal_ppv, stotal_ppv_usd = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 %>
			% for l in sorted(results_group_by_partner[key], key=lambda l : l['date_maturity']):
				<tr class="cont-table-lines">
					<td>${formatLang(l['date_maturity'],date=True)}</td>
					<td>${l['move_name'] or ''}</td>
					<td>${l['move_ref'] or ''}</td>
					<td>${l['po_ref'] or ''}</td>
					<td>${l['po_date'] and formatLang(l['po_date'],date=True) or ''}</td>
					<td>${key[1] or ''}</td>
					<td>${key[2] or ''}</td>
					<td>${l['original_picking_names'] or ''}</td>
					<td>${l['original_picking_date'] and formatLang(l['original_picking_date'],date=True) or ''}</td>
					<td>${l['picking_names'] or ''}</td>
					<td>${l['picking_date'] and formatLang(l['picking_date'],date=True) or ''}</td>
					<td>${l['payment_terms'] or ''}</td>
					<td>${l['due_date'] and formatLang(l['due_date'],date=True) or ''}</td>
					<td>${l['inv_cury'] or ''}</td>
					<td align="right">${formatLang(l['quantity'] and l['quantity'] or '')}</td>
					<td align="right">${formatLang(l['avg_price_unit'] and l['avg_price_unit'] or '')}</td>
					<td align="right">${formatLang(l['amount_untaxed'] and l['amount_untaxed'] or '')}</td>
					<td align="right">${formatLang(l['amount_untaxed_usd'] and l['amount_untaxed_usd'] or '')}</td>
					<td align="right">${formatLang(l['amount_tax'] and l['amount_tax'] or '')}</td>
					<td align="right">${formatLang(l['amount_tax_usd'] and l['amount_tax_usd'] or '')}</td>
					<td align="right">${formatLang(l['amount_ppv'] and l['amount_ppv'] or '')}</td>
					<td align="right">${formatLang(l['amount_ppv_usd'] and l['amount_ppv_usd'] or '')}</td>
					<td>${l['remarks'] or ''}</td>
				</tr>
				<%
					stotal_untaxed += l['amount_untaxed']
					stotal_untaxed_usd += l['amount_untaxed_usd']
					stotal_tax += l['amount_tax']
					stotal_tax_usd += l['amount_tax_usd']
					stotal_ppv += l['amount_ppv']
					stotal_ppv_usd += l['amount_ppv_usd']
				%>
			% endfor
			<tr class="cont-table-trsubtotal">
				<td colspan="5" align="right"><i>Sub Total&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i/></td>
				<td >${key[1] or ''}</td>
				<td colspan="10">&nbsp;</td>
				<td align="right">${formatLang(stotal_untaxed)}</td>
				<td align="right">${formatLang(stotal_untaxed_usd)}</td>
				<td align="right">${formatLang(stotal_tax)}</td>
				<td align="right">${formatLang(stotal_tax_usd)}</td>
				<td align="right">${formatLang(stotal_ppv)}</td>
				<td align="right">${formatLang(stotal_ppv_usd)}</td>
				<td>&nbsp;</td>
			</tr>
			<%
				total_untaxed += stotal_untaxed
				total_untaxed_usd += stotal_untaxed_usd
				total_tax += stotal_tax
				total_tax_usd += stotal_tax_usd
				total_ppv += stotal_ppv
				total_ppv_usd += stotal_ppv_usd
			%>
		% endfor
		<tr class="cont-table-trtotal">
			<td colspan="16" align="center">Grand Total</td>
			<td align="right">${formatLang(total_untaxed)}</td>
			<td align="right">${formatLang(total_untaxed_usd)}</td>
			<td align="right">${formatLang(total_tax)}</td>
			<td align="right">${formatLang(total_tax_usd)}</td>
			<td align="right">${formatLang(total_ppv)}</td>
			<td align="right">${formatLang(total_ppv_usd)}</td>
			<td>&nbsp;</td>
		</tr>
		<tfoot>
			<tr>
				<td colspan="23">
					<table width="100%" >
						<tr>
							<td valign="bottom" width="10%"><br/><br/><br/><br/><br/>Prepared By : </td>
							<td valign="bottom" width="10%">&nbsp;</td>
							<td valign="bottom" width="3%">&nbsp;</td>
							<td valign="bottom" width="10%">Checked By : </td>
							<td valign="bottom" width="10%">&nbsp;</td>
							<td valign="bottom" width="3%">&nbsp;</td>
							<td valign="bottom" width="10%">Approved By : </td>
							<td valign="bottom" width="10%">&nbsp;</td>
						</tr>
					</table>
				</td>
			</tr>
		</tfoot>
</table>   
</body>
</html>
