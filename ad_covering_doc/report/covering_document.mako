<html>
<head>
	<style>
		body {
		  font-family: "times new roman";
		}
		.sn{
			padding-right:5px;
		}
		.tabel-label{
			border-top: 1px solid black;
			border-right:1px solid black;
			border-bottom:1px solid black;
			text-align:center;
			padding-right:5px;
		}
		.label-2{
			padding-top:40px;
		}
		.label-2{
			padding-top:20px;
		}
		.int-entry{
			border-bottom:1px solid black;
			border-right:1px solid black;
			text-align:right;
			padding-right:5px;
		}
		.label-label{
			text-transform: uppercase;
			font-weight: bold;
		}
	</style>

</head>
<body>
% for o in objects:
<table width="100%">
	<tr>
		<td width="5%"></td><td width="10%"></td><td width="85%"></td>
	</tr>
	<tr>
		<td colspan="3" style="text-transform:uppercase;">${o.city or ""}, ${o.date or ""}</td>
	</tr>
	<tr>
		<td class="label-label">TO : </td>
		<td colspan="2" width=""> ${o.consignee_id.name or ''}</td>
	</tr>
	<tr>
		<td></td>
		%if o.show_consignee:
			<td colspan="2"> ${(o.c_address_text or '').replace('\n','<br/>')}</td>
		%else:
			<td colspan="2"> ${o.consignee_id.street or ''}</br>${o.consignee_id.street2 or ''}</br> ${o.consignee_id.street3 or ''}</td>
		%endif
	</tr>
	<tr>
		<td class="label-label" colspan="3">Ref</td>
	</tr>
	<tr>
		<td class="label-label" colspan="2">Invoice No :</td>
		<td>	
			<table>
				<tr>
				% for invoice in o.invoice_ids:
					<td>
					${ invoice.internal_number or ''}
					</td>
		 		%endfor
		 	</tr>
		 	</table>
		</td>
	</tr>
	<tr>
		<td colspan="3">Dear Sir,</td>
	</tr>
	<tr>
		<td colspan="3">Sending you herewith one set of shipping documents as under :</td>
	</tr>
</table>
<table style="border-collapse:collapse;width:100%;">
	<%
		sn=1
	%>
	<tr>
		<td width='5%' ></td><td width='65%'></td><td width="15%" class="tabel-label label-label" style="border-left:1px solid black;">Original</td><td width="15%" class="tabel-label label-label">Copy</td>
	</tr>
	%for line in o.doc_lines_ids:
	<tr>
		<td class="sn">${sn}.</td><td>${line.desc}</td><td class="int-entry" style="border-left:1px solid black;">${line.original}</td><td class="int-entry">${line.copy_1}</td>
	</tr>
	<%
	sn+=1
	%>
	% endfor
</table>
<table style="border-collapse:collapse;width:100%;">
	<tr>
		<td width='40%' style="padding-top:40px;">Please acknowledge receipt</td>
		<!-- <td colspan="4" width='60%' class="label-2 label-label">DETAILS COURIER TO CUSTOMER</td> -->
		<!-- <td width='10%'>dd</td>
		<td width="10%" class="tabel-label" style="border-left:1px solid black;">Original</td>
		<td width="10%" class="tabel-label">Copy</td> -->
	<tr>
	<tr>
		<td width='40%' ></td>
		<!-- <td width='15%' class="tabel-label" style="border-left:1px solid black;"></td>
		<td width='15%' class="tabel-label">TNT</td>
		<td width="15%" class="tabel-label">DHL</td>
		<td width="15%" class="tabel-label">FEDEX</td> -->
	<tr>
	<tr>
		<td ></td>
		<!-- <td  class="int-entry" style="border-left:1px solid black;">AWB NO.</td>
		<td  class="int-entry"></td>
		<td  class="int-entry"></td>
		<td  class="int-entry"></td> -->
	<tr>
</table>
<table style="border-collapse:collapse;width:100%;">
	<tr>
		<td width='40%' style="padding-top:20px;">Yours faithfully,</td>
		<!-- <td colspan="4" width='60%' class="label-3 label-label">BANK TO BANK DHL COURIER</td> -->
		<!-- <td width='10%'>dd</td>
		<td width="10%" class="tabel-label" style="border-left:1px solid black;">Original</td>
		<td width="10%" class="tabel-label">Copy</td> -->
	<tr>
	<tr>
		<td width='40%' >PT. Bitratex Industries</td>
		<!-- <td width='15%' class="tabel-label" style="border-left:1px solid black;"></td>
		<td width='15%' class="tabel-label">HSBC</td>
		<td width="15%" class="tabel-label">BCA</td>
		<td width="15%" class="tabel-label">OTHER</td> -->
	<tr>
	<tr>
		<td >&nbsp;</td>
		<!-- <td  class="int-entry" style="border-left:1px solid black;">AWB NO.</td>
		<td  class="int-entry"></td>
		<td  class="int-entry"></td>
		<td  class="int-entry"></td> -->
	<tr>
	<tr >
		<td width="40%" style="padding-top:60px;">${o.sign_by.name or ''}</td>
		<!-- <td width="60%" colspan="4"></td> -->
	<tr>
</table>
% endfor
</body>
</html>