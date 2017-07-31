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
	#print ":::::::::::::::::::", data, objects[0]._name
	result_summary = []
%>
<body>
	<table>
		<thead>
		% for o in objects:
		<tr class="header" width="100%">
			% if report_title(data,objects)=='KBKB RM':
				<td width="14%" colspan="2">Receipt</td>
				<td width="15%" rowspan="2">Partner</td>
				<td width="12%" rowspan="2">Transporter</td>
				<td width="10%" rowspan="2">Truck<br/>No</td>
				<td width="11%" colspan="2">Surat Jalan</td>
				<td width="10%" rowspan="2">Qty</td>
				<td width="5%" rowspan="2">Rate</td>
				<td width="4%" rowspan="2">UOM</td>
				<td width="13%" rowspan="2">Amount</td>
				<!-- <td width="7%" rowspan="2">Bill Number</td> -->
				<!-- <td width="4%" rowspan="2">Bill Date</td> -->
			% else:
				<td width="10%" rowspan="2">Invoice</td>
				<td width="14%" colspan="2">Surat Jalan</td>
				<td width="15%" rowspan="2">Partner</td>
				<td width="12%" rowspan="2">Transporter</td>
				<td width="10%" rowspan="2">Truck<br/>No</td>
				<td width="10%" rowspan="2">Qty</td>
				<td width="5%" rowspan="2">Rate</td>
				<td width="4%" rowspan="2">UOM</td>
				<td width="13%" rowspan="2">Amount</td>
				<!-- <td width="7%" rowspan="2">Bill Number</td> -->
				<!-- <td width="4%" rowspan="2">Bill Date</td> -->
			% endif
		</tr>
		<tr class="header">
			% if report_title(data,objects)=='KBKB RM':
			<td width="10%">Number</td>
			<td width="4%">Date</td>
			<td width="7%">Number</td>
			<td width="4%">Date</td>
			% else:
			<td width="10%">Number</td>
			<td width="4">Date</td>
			% endif
		</tr>
		</thead>
			<% 
			total_qty = 0 
			total = 0 
			res_grouped = {}
			for line in o.ext_line:
				if line.partner_id:
					key = (line.partner_id.partner_code,line.partner_id.name)
				else:
					key = (" "," ")
				if key not in res_grouped:
					res_grouped.update({key:[]})
				res_grouped[key].append(line)
			%>
			% for key in res_grouped.keys():
				<% subtotal_qty = 0 %>
				<% subtotal = 0 %>
		<tr>
			% if report_title(data,objects)=='KBKB RM':
			<td colspan="11" align="left"><b>Porters ${(key[0] or '')+' '+key[1] or ''}</b></td>
			% else:
			<td colspan="10" align="left"><b>Porters ${(key[0] or '')+' '+key[1] or ''}</b></td>
			% endif
		</tr>
					% for line in sorted(res_grouped[key],key=lambda x:((x.picking_related_id and x.picking_related_id.date_done or ''))):
						<%
						rate = line.picking_related_id and line.picking_related_id.porters_charge and line.picking_related_id.porters_charge.cost or 0.0
						%>

		<tr>
			% if report_title(data,objects)=='KBKB RM':
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.name or ''}</td>
				<td valign="top" align="center">${line.picking_related_id and line.picking_related_id.date_done!=False and formatLang(line.picking_related_id.date_done,date=True) or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.partner_id and line.picking_related_id.partner_id.name or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.trucking_company and line.picking_related_id.trucking_company.partner_id.name or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.truck_number or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.supplier_delicery_slip or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.date_delivery_slip!=False and formatLang(line.picking_related_id.date_delivery_slip,date=True) or ''}</td>
				<td valign="top" align="right">${formatLang((line.debit and line.debit or -line.credit or 0.0)/(rate or 1)) or 0.0}</td>
				<td valign="top" align="right">${formatLang(rate) or ''}</td>
				<td valign="top" align="center">Bale</td>
				<td valign="top" align="right">${formatLang(line.debit and line.debit or -line.credit or 0.0)}</td>
				<!-- <td valign="top" align="left">${formatLang(report_date(data,objects),date=True)}</td> -->
				<!-- <td valign="top" align="center">${line.ext_transaksi_id and line.ext_transaksi_id.request_date!=False and formatLang(line.ext_transaksi_id.request_date,date=True) or ''}</td> -->
			% else:
				<td valign="top" align="left">${line.invoice_related_id and line.invoice_related_id.internal_number or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.name or ''}</td>
				<td valign="top" align="center">${line.picking_related_id and line.picking_related_id.date_done!=False and formatLang(line.picking_related_id.date_done,date=True) or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.partner_id and line.picking_related_id.partner_id.name or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.trucking_company and line.picking_related_id.trucking_company.partner_id.name or ''}</td>
				<td valign="top" align="left">${line.picking_related_id and line.picking_related_id.truck_number or ''}</td>
				<td valign="top" align="right">${formatLang((line.debit and line.debit or -line.credit or 0.0)/(rate or 1)) or 0.0}</td>
				<td valign="top" align="right">${formatLang(rate) or ''}</td>
				<td valign="top" align="center">Bale</td>
				<td valign="top" align="right">${formatLang(line.debit and line.debit or -line.credit or 0.0)}</td>
				<!-- <td valign="top" align="left">${formatLang(report_date(data,objects),date=True)}</td> -->
				<!-- <td valign="top" align="center">${line.ext_transaksi_id and line.ext_transaksi_id.request_date!=False and formatLang(line.ext_transaksi_id.request_date,date=True) or ''}</td> -->
			% endif
		</tr>
						<% subtotal_qty += (line.debit and line.debit or -line.credit or 0.0)/(rate or 1) %>
						<% subtotal += (line.debit and line.debit or -line.credit or 0.0) %>
					% endfor
				<% result_summary.append([key[0],key[1],subtotal]) %>
				<% total_qty += subtotal_qty %>
				<% total += subtotal %>
			% endfor
		<tr class="subtotal">
			% if report_title(data,objects)=='KBKB RM':
				<td colspan="4" align="left"></td>
				<td align="left"><b>Subtotal ${key[1] or ''}</b></td>
				<td colspan="2" align="left"></td>
				<td align="right">${formatLang(total_qty) or 0}</td>
				<td colspan="2" align="left"></td>
				<td align="right">${formatLang(total) or 0}</td>
				<!-- <td colspan="2" align="left"></td> -->
			% else:
				<td colspan="4" align="left"></td>
				<td align="left"><b>Subtotal ${key[1] or ''}</b></td>
				<td align="left"></td>
				<td align="right">${formatLang(total_qty) or 0}</td>
				<td colspan="2" align="left"></td>
				<td align="right">${formatLang(total) or 0}</td>
				<!-- <td colspan="2" align="left"></td> -->
			% endif
		</tr>
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
		<!-- <td align="center" width="10%">${line[2]}</td> -->
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
		% endfor
</body>
</html>