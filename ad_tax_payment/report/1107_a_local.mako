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
			table tr td {
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
								<font style="font-size: 14px;"><br>DEPARTEMEN KEUANGAN RI<br>DIREKTORAT JENDRAL PAJAK</font> </td>
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
					<br />
		<table style="text-align: left; width: 1100px; height: 376px;" border="0" cellpadding="2" cellspacing="2">
			<tbody>
				<tr>
					<td colspan="9" rowspan="1" style="vertical-align: top; border: 1px solid;">Penyerahan Dalam Negeri
							Dengan Faktur Pajak<br>
					</td>
				</tr>
				<tr>
					<td colspan="1" rowspan="2" style="vertical-align: top;border:1px solid; text-align: center;">No.<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top; border:1px solid; text-align: center;">Nama
					Pembeli<br> BKP/ Penerima JKP<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top; text-align: center;border:1px solid">NPWP<br></td>
					<td colspan="2" rowspan="1" style="vertical-align: top;border:1px solid; text-align: center;">Faktur
					Pajak/Nota Retur<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top; border:1px solid; text-align: center;">DPP<br>
					(Rupiah)<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top; text-align: center; border:1px solid;">PPN<br>
					(Rupiah)<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top; border:1px solid; text-align: center;">PPN BM<br>
					(Rupiah)<br></td>
					<td colspan="1" rowspan="2" style="vertical-align: top;border-left-:1px solid;border-bottom:1px solid; border-right:1px solid">Kode dan<br>No. Seri PPN<br>Yang Diganti<br></td>
				</tr>
				<tr>
					<td style="vertical-align: top; text-align: center; border:1px solid;">Kode dan <br> Nomor Seri<br></td>
					<td style="vertical-align: top; text-align: center; border:1px solid;">Tanggal<br></td>
				</tr>
				<%
					gt=0
					number=1
				%>
				%for line in o.tax_lines_cr:
				<tr>
					<td style="vertical-align: top; border-left:1px solid">${number}</td>
					<td style="vertical-align: top; border-left:1px solid">${line.move_line_id.partner_id.name}</td>
					<td style="vertical-align: top; border-left:1px solid">${line.move_line_id.partner_id.npwp or "-"}</td>
					<td style="vertical-align: top; border-left:1px solid">${line.move_line_id.faktur_pajak_no}</td>
					<td style="vertical-align: top; border-left:1px solid">${line.invoice_id.date_invoice}</td>
					<td style="vertical-align: top; text-align: right;border-left:1px solid">${abs(line.amount_currency)}</td>
					<td style="vertical-align: top; text-align: right;border-left:1px solid">${abs(line.amount_currency)}</td>
					<td style="vertical-align: top; text-align: right;border-left:1px solid">0</td>
					<td style="vertical-align: top; border-left:1px solid; border-right:1px solid">&nbsp;</td>
				</tr>
				<%
					gt=gt+line.amount_currency
					number+=1
				%>
				%endfor
				<tr>
					<td colspan="5" rowspan="1" style="vertical-align: top; width: 350px;border:1px solid">Jumlah Penyerahan Dalam
						Negeri Dengan Faktur Pajak<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">0<br></td>
					<td style="vertical-align: top;border-left:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1" style="vertical-align: top;border:1px solid; width: 350px;">Penyerahan Dalam Negeri
						Dengan Faktur Pajak Sederhana<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">0<br></td>
					<td style="vertical-align: top;border-left-:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1"style="vertical-align: top; width: 350px;border:1px solid">Penyerahan yang PPn dan PPn
					BM-nya Harus Dipungut Sendiri<br> ( Jumlah II dengan Faktur Pajak Kode 01,04,05,06 dan 09 + III )<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">0<br></td>
					<td style="vertical-align: top;border-left-:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1" style="vertical-align: top; width: 350px;border:1px solid">Penyerahan yang PPn atau
					PPN dan PPn BM-nya Dipungut Oleh Pemungut PPN<br> ( Jumlah II Dengan Faktur Pajak Kode 02 dan 03 )<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">0<br></td>
					<td style="vertical-align: top;border-left-:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1" style="vertical-align: top; width: 350px;border:1px solid">Penyerahan yang PPN atau PPN dan PPn BM-nya Tidak Dipungut<br> ( Jumlah II dengan Faktur Pajak Kode 07 )<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; text-align: right;border:1px solid">0<br></td>
					<td style="vertical-align: top;border-left-:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1" style="vertical-align: top; width: 350px;border:1px solid">Penyerahann yang Dibebaskan
						dari Pengenaan PPN atau PPN dan PPn BM<br> ( Jumlah II dengan Faktur Pajak Kode 08 )<br></td>
					<td style="vertical-align: top; text-align: right; border:1px solid">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top; border:1px solid; text-align:right;">${abs(line.amount_currency)}<br></td>
					<td style="vertical-align: top;border:1px solid"><br></td>
					<td style="vertical-align: top;border-left-:1px solid; border-right:1px solid"><br></td>
				</tr>
				<tr>
					<td colspan="5" rowspan="1"style="vertical-align: top; width: 350px;border:1px solid">Grand Total&nbsp;&nbsp;&nbsp;&nbsp; :</td>
					<td style="vertical-align: top; text-align: right; border:1px solid">${gt}</td>
					<td style="vertical-align: top; text-align: right; border:1px solid">${gt}</td>
					<td style="vertical-align: top; text-align: right; border:1px solid"></td>
					<td style="vertical-align: top;border-left-:1px solid;border-bottom:1px solid; border-right:1px solid"><br></td>
				</tr>
			</tbody>
		</table>
		%endfor
		<br>
	</body>
</html>
