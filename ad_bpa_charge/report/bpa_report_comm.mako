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
	result_grouped = {}
	for res in results:
		key = res['agent_name']
		if key not in result_grouped:
			result_grouped.update({key:{}})
		key2 = res['due_date']
		if key2 not in result_grouped[key]:
			result_grouped[key].update({key2:[]})
		result_grouped[key][key2].append(res)
	result_summary = []
%>
<body>
	<table>
		<thead>
			<tr class="header" width="100%">
				<td width="1%" rowspan="2">&nbsp;</td>
				<td width="1%" rowspan="2">&nbsp;</td>
				<td width="13%" colspan="2">Invoice</td>
				<td width="13%" colspan="2">Surat Jalan</td>
				<td width="10%" rowspan="2">Sales Contract</td>
				<td width="10%" rowspan="2">Party</td>
				<td width="10%" rowspan="2">Product</td>
				<td width="5%" rowspan="2">Amount</td>
				<td width="10%" colspan="2">Commision</td>
				<td width="5%" rowspan="2">Freight</td>
				<td width="5%" rowspan="2">Amount Fob</td>
				<td width="5%" rowspan="2">Comm Fob</td> 
				<td width="5%" rowspan="2">Incoterm</td>
				<td width="11%" rowspan="2">Bill Number</td>
				<td width="5%" rowspan="2">Bill Date</td>
			</tr>
			<tr class="header">
				<td width="8%">No</td>
				<td width="5%">Date</td>
				<td width="8%">No</td>
				<td width="5%">Date</td>
				<td width="5%">%</td> 
				<td width="5%">Amt</td> 
			</tr>
		</thead>
		<%
			total = {1:0.0,2:0.0,3:0.0,4:0.0,5:0.0,6:0.0}
		%>
		% for key in result_grouped.keys():
			<tr><td colspan="18"><b>${key}</b></td></tr>
		% for key2 in result_grouped[key].keys():
			% if key2:
				<tr>
					<td valign="top" align="left">&nbsp;</td>
					<td colspan="17"><b>Due Date : ${key2}</b></td>
				</tr>
			% endif:
		% for res in sorted(result_grouped[key][key2], key = lambda x : (x['inv_date'],x['inv_no'],x['sj_date'],x['contract'])):
			<%
			total[1]+=res['price_subtotal']
			# comm_amt = res['amt1']*res['comm_percent']/100
			comm_amt = res['comm_amt']
			total[2]+=comm_amt
			# freight = res['amt1']/res['amt2']*res['freight']
			freight = res['freight']
			total[3]+=freight
			# insurance = res['amt1']/res['amt2']*res['insurance']
			insurance = res['insurance']
			total[4]+=insurance
			fob = res['fob']
			total[5]+=fob
			comm_amt_fob = res['comm_amt_fob']
			total[6]+=comm_amt_fob
			%>
		<tr>
			<td valign="top" align="left">&nbsp;</td>
			<td valign="top" align="left">&nbsp;</td>
			<td valign="top" align="left">${res['inv_no'] or ''}</td>
			<td valign="top" align="left">${formatLang(res['inv_date'],date=True) or ''}</td>
			<td valign="top" align="left">${res['sj_no'] or ''}</td>
			<td valign="top" align="left">${formatLang(res['sj_date'],date=True) or ''}</td>
			<td valign="top" align="left">${res['contract'] or ''}</td>
			<td valign="top" align="left">${res['party'] or ''}</td>
			<td valign="top" align="left">${res['prod_name'] or ''}</td>
			<td valign="top" align="right">${formatLang(res['price_subtotal'] or 0)}</td>
			<td valign="top" align="center">${res['comm_percent'] or ''}</td>
			<td valign="top" align="right">${formatLang(comm_amt) or ''}</td>
			<td valign="top" align="right">${formatLang(freight) or 0}</td>
			<td valign="top" align="right">${formatLang(fob) or 0}</td>
			<td valign="top" align="right">${formatLang(comm_amt_fob) or 0}</td>
			<td valign="top" align="center">${res['incoterm'] or ''}</td>
			<td valign="top" align="center">${res['bill_number'] or ''}</td>
			<td valign="top" align="center">${res['bill_date'] and formatLang(res['bill_date'],date=True) or ''}</td>
		</tr>
		% endfor
		% endfor
		% endfor
		<tr class="header">
			<td align="center" colspan="9"><b>T o t a l</b></td>
			<td valign="top" align="right">${formatLang(total[1])}</td>
			<td align="center" >&nbsp; </td>
			<td valign="top" align="right">${formatLang(total[2])}</td>
			<td valign="top" align="right">${formatLang(total[3])}</td>
			<td valign="top" align="right">${formatLang(total[5])}</td>
			<td valign="top" align="right">${formatLang(total[6])}</td>
			<td align="center" colspan="3">&nbsp; </td>
		</tr>
	</table>
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