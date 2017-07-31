<html>
<head>
	<style type='text/css'>
	body{
		font-size:12px;
		font-family: arial;
		margin:0px;
		padding:0px;
				/*text-transform:uppercase;
				font-weight:900;*/
			}
			table{
				font-size:12px;
				font-family: arial;
				border-collapse:collapse;
				margin:0px;
			}
			table tr td{
				padding-left:10px;
			}
			.header-td1{
				width: 120px;
			}

			.header-td2{
				padding-left:20px;
				width:180px;
			}
			.header-td3{
				width:10px;
			}
			.second-table{
				margin-left:-800px;
			}
			</style>
		</head>

		<body>
			%for o in objects: 
				<table style="text-align: left; width: 1100px; height: 112px;"border="1" cellpadding="2" cellspacing="2">
					<tbody>
						<tr>
							<td colspan="2" rowspan="2" style="vertical-align: top; width: 250px;"><br>
								<br>
								<br>
								<font style="font-size: 10px;"><br>DEPARTEMEN KEUANGAN RI<br>DIREKTORAT JENDRAL PAJAK</font> </td>
								<td style="vertical-align: top; width: 600px; text-align: center;">LAMPIRAN1<br>DAFTAR PAJAK KELUARAN DAN PPn BM<br></td>
								<td colspan="1" rowspan="2"style="vertical-align: top; width: 250px; text-align: center;">1 <br>
									FORMULIR<br>
									<font style="font-size: 21px;"><br>
										<br>
										1107 A</font><br>
									</td>
								</tr>
								<tr>
									<td style="vertical-align: top; width: 600px;">
										<table style="text-align: left; width: 100%;" border="0"cellpadding="2" cellspacing="2">
										<tbody>
											<tr>
												<td style="vertical-align: top; width: 295px;">&nbsp;&nbsp;&nbsp;&nbsp;
													Masa Pajak<br>
												</td>
												<td style="vertical-align: top; width: 10px;">:<br>
												</td>
												<td style="vertical-align: top; width: 295px;">${o.date_start} s.d. ${o.date_end}<br>
												</td>
											</tr>
											<tr>
												<td style="vertical-align: top; width: 295px;">&nbsp;&nbsp;&nbsp;&nbsp;
													Pembetulan Ke<br>
												</td>
												<td style="vertical-align: top; width: 10px;">:<br>
												</td>
												<td style="vertical-align: top; width: 295px;">&nbsp;&nbsp;&nbsp;&nbsp;
													0<br>
												</td>
											</tr>
										</tbody>
									</table>
									<br>
								</td>
							</tr>
						</tbody>
					</table>
					<center class="second-table">
						<table style="text-align: center;" border="0" cellpadding="2" cellspacing="2">
							<tr class="header2">
								<td class="header-td1">&nbsp;Nama PKP&nbsp;</td>
								<td class="header-td3">&nbsp;:&nbsp;</td>
								<td class="header-td2">&nbsp;PT. Bitratex Industries&nbsp;</td>
							</tr>
							<br />
							<tr>
								<td class="header-td1">&nbsp;N.P.W.P&nbsp;</td>
								<td class="header-td3">&nbsp;:&nbsp;</td>
								<td class="header-td2" style="letter-spacing:1px">${o.company_id.npwp}</td>
							</tr>
						</table>
					</center>
					<br>
						<table style="text-align:left; height:116px; width: 1100px;" cellpadding="2" cellspacing="2">
							<tbody>
								<tr>
									<td colspan="6" rowspan="1" style="vertical-align: top; border:1px solid; width: 1100px;">Ekspor<br></td>
								</tr>
								<tr>
									<td rowspan="2" style="vertical-align: top; border:1px solid; width: 25px;">NO.<br></td>
									<td rowspan="2" style="vertical-align: top; border:1px solid; width: 251px; text-align: center;">Nama Pembeli<br>BKP/ Penerima JKP<br></td>
									<td colspan="2" rowspan="1" style="vertical-align: top; border:1px solid; width: 200px; text-align: center;">PEB<br></td>
									<td rowspan="2" style="vertical-align: top; border:1px solid; width: 20px; text-align: center;">DPP<br>(Rupiah)<br></td>
									<td rowspan="2" style="vertical-align: top; border:1px solid; width: 604px;"><br>
									<br></td>
								</tr>
								<tr>
									<td style="vertical-align: top; border:1px solid; width: 120px; text-align: center;">Nomor<br></td>
									<td style="vertical-align: top; border:1px solid; width: 80px; text-align: center;">Tanggal<br></td>
								</tr>
						<%
							number=1
						%>
						%for line in o.tax_lines_cr:
								<tr>
									<td style="vertical-align: top; border-left:1px solid; width: 55px;padding-top:1px; text-align: right; padding-right">${number}</td>
									<td style="vertical-align: top;padding-top:1px; border-left:1px solid; width: 393px;">${line.move_line_id.partner_id.name}</td>
									<td style="vertical-align: top;padding-top:1px; border-left:1px solid; width: 277px;">${line.invoice_id.peb_number}</td>
									<td style="vertical-align: top;padding-top:1px; border-left:1px solid; width: 99px;">${line.effective_date}</td>
									<td style="vertical-align:top;padding-top:1px; border-left:1px solid; width:356px;text-align:right;">${abs(line.amount_currency)}</td>
									<td style="vertical-align: top;padding-top:1px; border-left:1px solid; width: 293px; border-right: 1px solid">&nbsp;</td>
								</tr>
							<%
								number+=1
							%>	
						%endfor
								<tr>
									<td colspan="4" rowspan="1"style="vertical-align: top; width: 1100px;border:1px solid">Grand Total&nbsp;&nbsp;&nbsp;&nbsp; :</td>
									<td style="vertical-align: top; text-align: right; border:1px solid"></td>
									<td style="vertical-align: top;border-left-:1px solid;border-bottom:1px solid; border-right:1px solid"><br></td>
								</tr>
						
							</tbody>
						</table>
				%endfor
						<br>
						<br>
		</body>
</html>