<html><head>
<style>

table
	{
	font-size:12px;
	}
td
	{
	padding:4px;
	}
#page_note
	{
	border:1px solid #000;
	right:0px;
	position:relative;
	font-size:10px;
	margin-right:0px;
	}
table .header
	{
	display:none;
	}
.main
	{
	width:23.7cm;
	margin:0 auto;
	}
.main td
	{
	border:1px solid #000;
	}
td .pajak
	{
	border:0px;
	}
.partner td
	{
	border:0px;
	}
.lines
	{
	border-collapse:collapse;
	width:23.7cm;
	}
.inv_line td
	{
	border-top:0px;
	border-bottom:0px;
	}
.inv_cell
	{
	text-align:right;
	}
	
</style>

</head>
<body>
%for o in objects :
<div><table width="80%" border="0">
<tr><td><div align="right">
<table border="0" id="pagenote">
	<tr>
		<td>Lembar Ke-1 (Putih)</td>
		<td>:</td>
		<td>Untuk Pembeli BKP/penerima JKP sebagai bukti Pajak Masukan</td>
	</tr>
	<tr>
		<td><font size="2">Lembar Ke-2 (Merah)</font></td>
		<td><font size="2">:</font></td>
		<td><font size="2">Untuk PKP yang menerbitkan Faktur Pajak sebagai bukti Pajak Keluaran</font></td>
	</tr>
	<tr>
		<td><font size="2">Lembar Ke-3 (Kuning)</font></td>
		<td><font size="2">:</font></td>
		<td><font size="2">Untuk Arsip Tambahan</font></td>
	</tr>
</table>
</div>
<br><br>
<center><b><font size="5">FAKTUR PAJAK</font></b></center>
<table border="1" width="100%" id="main">
	<tr>
	<td colspan="3"> 
		<table border="0" width="100%"><tr>
					<td width="50%">Kode dan Nomor Seri Pajak</td>
					<td>:</td>
					<td>--------------</td>
				</tr>
		</table>
	</td>
	</tr>
	<tr>
		<td colspan="3">Pengusaha Kena Pajak</td>
	</tr>
	<tr>
		<td colspan="3">
			<table border="0" width="100%">
			<tr>
				<td  width="50%">Nama</td>
				<td>:</td>
				<td>${o.company_id.name}</td>
			</tr>
			<tr>
				<td width="50%">Alamat</td>
				<td>:</td>
				<td>${o.company_id.street or ''} ${o.company_id.street2 or ''}<br> ${o.company_id.city or ''} - ${o.company_id.country_id.name or ''}</td>
			</tr>
			<tr>
				<td width="50%">NPWP</td>
				<td>:</td>
				<td>${o.company_id.npwp or '-'}</td>
			</tr>
			</table>
		</td>
	</tr>
	<tr>
		<td colspan="3">
			<table border="0" width="100%">
			<tr>
				<td colspan="3">Pembeli Barang Kena Pajak / Penerima Jasa Kena Pajak</td>
			</tr>
			<tr>
				<td  width="50%">Nama</td>
				<td>:</td>
				<td>${o.partner_id.name}</td>
			</tr>
			<tr>
				<td width="50%">Alamat</td>
				<td>:</td>
				<td>${o.partner_id.street or ''} ${o.partner_id.street2 or ''}<br> ${o.partner_id.city or ''} - ${o.partner_id.country_id.name or ''}</td>
			</tr>
			<tr>
				<td width="50%">NPWP</td>
				<td>:</td>
				<td>${o.partner_id.npwp or '-'}</td>
			</tr>
			</table>
		</td>
	</tr>
	<tr>
		<td width="20%"><center>No.Urut</center></td>
		<td width="50%"><center>Nama Barang Kena Pajak / Jasa Kena Pajak</center></td>
		<td><center>Harga Jual / Penggantian / Uang Muka / Termin (Rp)</center></td>
	</tr>
	<%
	urut=1
	%>
	%for i in o.invoice_line :
	
	<tr style="border-spacing:100px">
		<td><center>${urut}</center></td>
		<td><center>${i.name}</center></td>
		<td><div align="right">${o.amount_total}</div></td>
	</tr>
	<%
	urut+=1
	%>
	%endfor
	<tr>
		<td colspan="2">Harga Jual / Penggantian / Uang Muka / Termin *)</td>
		<td width="30%"><div align="right">${o.amount_total}</div></td>
	</tr>
	<tr>
		<td colspan="2">Dikurangi Potongan Harga</td>
		<td width="30%"><div align="right">${o.amount_untaxed}</div></td>
	</tr>
	<tr>
		<td colspan="2">Dasar Pengenaan Pajak</td>
		<td width="30%"><div align="right">${o.amount_untaxed}</div></td>
	</tr>
	<tr>
		<td colspan="2">PPN = 10% x Dasar Pengenaan Pajak</td>
		<td width="30%"><div align="right">${o.amount_tax}</div></td>
	</tr>
	<tr>
	<td colspan="3">
		<table width="100%">
			<tr>
				<td> 
					<div style="float:left;width:40%">
						<table border="1" width="100%">
						<tr>
							<td>Tarif</td>
							<td>DPP</td>
							<td>PPn BM</td>
						</tr>
						<tr>
							<td>....%</td>
							<td>Rp ...........</td>
							<td>Rp ...........</td>
						</tr>
						<tr>
							<td>....%</td>
							<td>Rp ...........</td>
							<td>Rp ...........</td>
						</tr>
						<tr>
							<td>....%</td>
							<td>Rp ...........</td>
							<td>Rp ...........</td>
						</tr>
						</table>
					</div>
					<div align="center">
						Bandung , ${ time.strftime('%d/%m/%Y') }<br><br><br><br><br>
						Nama ILONA<br><br>
					</div>
				</td>
			</tr>
		</table>
	</td>
	</tr>
</table>
</td></tr></table>
</div><div align="left"><table><tr><td>*) Coret yang tidak perlu<br>Faktur Pajak ini berlaku juga sebagai Kwitansi Pembayaran yang sah</td></tr></table></div>
%endfor
</body></html>