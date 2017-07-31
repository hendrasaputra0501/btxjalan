<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
	<style>
	/*div
	{
		min-height:1280px;
		height:1280px;
		margin-top:0px;
		margin-bottom:0px;
		position:relative;
	}*/
	.lembar {
		font-size: 10pt;
		border: 1px solid grey;
		padding: 5px 5px 5px 5px;
		width:260px;
		right: 0px;
		float:right;
	}
	.lembar-wrap{
		float: left;
		margin-top:20px;
		width: 100%;
		padding-top: 10px;
		padding-bottom: 10px;
	}
	.main1 {
		display: table;
		font-size: 10pt;
		padding: 5px 5px 5px 5px;
		}
	.wrap1 {
		display: table-row;
	}
	.kiri {
		display: table-cell;
		padding-left: 5px;
		width: 200px;
		text-transform: uppercase;
	}
	.kanan {
		display: table-cell;
		padding-left: 5px;
		text-transform: uppercase;
	}
	.main-nh-wrap{
		float:left;
		width: 100%;

		border-bottom: 1px solid black;
		padding-top: 5px;
		padding-bottom: 5px;
	}
	.notahead{
		font-size: 16pt;
		font-weight: bold;
		text-align: center;
	}
	.notahead2{
		float: left;
		font-size: 10pt;
		left:0px;
		width:65%;
	}
	.notahead3{
		float: left
		font-size: 10pt;
		text-align: center;
	}
	.main-table{
		display: table;
		width: 100%;
		border:1px solid black;
		border-collapse: collapse;
		float: left;
	}
	.main-row{
		display: table-row;
	}
	.main-cell{
		display: table-cell;
	}
	
	.satu{
		vertical-align: top;
		border-right: 1px solid black;
		width: 30px;
		display: table-cell;
	}
	.dua{
		vertical-align: top;
		border-right: 1px solid black;
		width: 256px;
		display: table-cell;
		word-break:normal;
	}
	.tiga{
		vertical-align: top;
		border-right: 1px solid black;
		width: 130px;
		display: table-cell;
	}
	.empat{
		vertical-align: top;
		border-right: 1px solid black;
		width: 130px;
		display: table-cell;
	}
	.lima{
		vertical-align: top;
		width: 152px;
		display: table-cell;
	}
	
	.main1-th{
		display: table-row;
		width: 100%;
		border-top: 1px solid black;
		border-bottom: 1px solid black;
		padding: 5px;
	}
	.main1-td{
		width: 100%;
		display: table-row;
	}
	.curr{
		padding-left: 5px;
		text-align: left;
		float: left;
		left: 0px;
	}
	.amt{
		text-align: right;
		float: right;
		right: 0px;	
	}
	.foot{
	    margin: 0;
	    clear: both;
	    position: absolute;
		float:right;
		right:30px;
		width:250px;
		text-align: center;
		bottom: 120px;
		font-size: 10pt;
		height: 100px;
	}
	ul
	{
	    list-style-type: none;
	}
	li
	{
	    list-style-type: none;
	}

	</style>
</head>
<body>
	%for o in objects:
		<% setLang(o.partner_id.lang) %>
		<div></div>
		<div class="main-table">
			<div class="main-row">
				<div class="main-cell">
					<div class="main-nh-wrap">
						<div class="notahead-wrap">
							<div class="notahead">NOTA RETUR</div>
						</div>
						<div class="notahead-wrap">
							<div class="notahead3">Nomor : ${o.return_source_doc or ''}</div>
						</div>
						<%
						nomor = "%s.%s" % (o.kode_transaksi_faktur_pajak, o.nomor_faktur_id.name)
						source_date = ""
						if o.nomor_faktur_id:
							source_date = [inv for inv in o.nomor_faktur_id.account_invoice_ids if inv.id!=o.id] and [inv for inv in o.nomor_faktur_id.account_invoice_ids if inv.id!=o.id][0].date_invoice or o.faktur_pajak_date_entry
							%>
						<div class="notahead-wrap">
							<div class="notahead3">( Atas Faktur Pajak Nomor Seri: ${nomor}&nbsp;&nbsp;&nbsp;Tanggal :${source_date and formatLang(source_date,date=True) or ""} )</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell">
					<div class="main1 main-nh-wrap">
						<div class="wrap1">
							<div class="kiri" style="padding-top:10px;">PEMBELI</div>
							<div class="tengah" style="padding-top:10px;"></div>
							<div class="kanan" style="padding-top:10px;">&nbsp;</div>
						</div>
						<div class="wrap1">
							<div class="kiri">Nama</div>
							<div class="tengah">:</div>
							<div class="kanan">${(o.partner_id and o.partner_id.title and o.partner_id.title.name) or ''} ${(o.partner_id and o.partner_id.name) or ''}</div>
						</div>
						<div class="wrap1">
							<div class="kiri">Alamat</div>
							<div class="tengah">:</div>
							<div class="kanan">${alamat(o.partner_id and o.partner_id.id or False) or ''}</div>
						</div>
						<div class="wrap1">
							<div class="kiri">NPWP</div>
							<div class="tengah">:</div>
							<div class="kanan">${o.partner_id.npwp or ''}</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell">
					<div class="main1">
						<div class="wrap1">
							<div class="kiri" style="padding-top:10px;">KEPADA PENJUAL</div>
							<div class="tengah" style="padding-top:10px;"></div>
							<div class="kanan" style="padding-top:10px;">&nbsp;</div>
						</div>
						<div class="wrap1">
							<div class="kiri">Nama</div>
							<div class="tengah">:</div>
							<div class="kanan">${(o.company_id and o.company_id.name) or ''}</div>
						</div>
						<div class="wrap1">
							<div class="kiri">Alamat</div>
							<div class="tengah">:</div>
							<div class="kanan">${alamat(o.company_id and o.company_id.partner_id and o.company_id.partner_id.id or False ) or ''}</div>
						</div>
						<div class="wrap1">
							<div class="kiri">NPWP</div>
							<div class="tengah">:</div>
							<div class="kanan">${(o.company_id and o.company_id.partner_id and o.company_id.partner_id.npwp) or ''}</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
					<div class="main-cell">
						<div style="display:table;">
							<div class="main1 main1-th">
								<div class="satu" style="text-align: center;">No.</div>
								<div class="dua" style="text-align: center;">Nama Barang Kena Pajak/Barang Mewah yang dikembalikan</div>
								<div class="tiga" style="text-align: center;">Kwantum</div>
								<div class="empat" style="text-align: center;">Harga Satuan menurut Faktur Pajak (${o.currency_id and o.currency_id.symbol or ''})</div>
								<div class="lima" style="text-align: center;">Harga Jual yang dikembalikan (${o.currency_id and o.currency_id.symbol or ''})</div>
							</div>
						<div>
					</div>	
				</div>
			<%
			n=1
			%>
			%for line in o.invoice_line:
				<div class="main-row">
					<div class="main-cell">
						<div style="display:table;">
							<div class="main1 main1-td">
								<div class="satu" style="text-align: right;">${n}</div>
								<div class="dua" style="text-align: left;">${line.name.strip() or ""}</div>
								<div class="tiga" style="text-align: right;">${get_line_qty_retur(line).strip()}</div>
								<div class="empat" style="text-align: right;">${get_line_price_retur(line).strip()}</div>
								<div class="lima"  style="text-align: right;">${line.price_subtotal}</div>
							</div>
						</div>
					</div>	
				</div>
				<%
				n+=1
				%>
			%endfor	
			%for l in range(0,20-n-1):
				<div class="main-row">
					<div class="main-cell">
						<div style="display:table;">
							<div class="main1 main1-td">
								<div class="satu">&nbsp;</div>
								<div class="dua">&nbsp;</div>
								<div class="tiga">&nbsp;
								</div>
								<div class="empat">
									<div class="amt">&nbsp;</div>
								</div>
								<div class="lima">
									<div class="amt">&nbsp;</div>
								</div>
							</div>
						</div>
					</div>	
				</div>
			%endfor
			<div class="main-row">
				<div class="main-cell">
					<div style="display:table;">
						<div class="main1 main1-td">
							<div style="border-top:1px solid black;border-right:1px solid black; text-align: left; width:549px; display:table-cell;">Jumlah harga BKP yang dikembalikan</div>
							<div style="border-top:1px solid black; width:152px; display:table-cell;">
								<div class="amt">${formatLang(round(o.amount_untaxed),digits=0)}</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell">
					<div style="display:table;">
						<div class="main1 main1-td">
							<div style="border-top:1px solid black;border-right:1px solid black; text-align: left; width:549px; display:table-cell;">Pajak Pertambahan Nilai yang diminta kembali</div>
							<div style="border-top:1px solid black; width:152px; display:table-cell;">
								<div class="amt">${formatLang(round(o.amount_tax),digits=0)}</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell">
					<div style="display:table;">
						<div class="main1 main1-td">
							<div style="border-top:1px solid black;border-right:1px solid black; text-align: left; width:549px; display:table-cell;">Pajak Penjualan Atas Barang Mewah yang diminta kembali</div>
							<div style="border-top:1px solid black; width:152px; display:table-cell;">
								<div class="amt">&nbsp;</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell" style="height:${350-n*30}px; border-top:1px solid black;float-right;">&nbsp;
					<%
					import datetime
					date_invoice = datetime.datetime.strptime(o.date_invoice,'%Y-%m-%d').strftime('%d %B %Y')
					%>
					<div class="foot">.......................,${date_invoice or "..............."}<br/>Pembeli<br/><br/><br/><br/><br/>
					(_____________________)<br/>
					&nbsp;&nbsp;&nbsp;<br/>
					</div>
				</div>
			</div>
			<div class="main-row">
				<div class="main-cell" style="border-top:1px solid black; float:left; text-align:left; font-size:10pt; width:702px;">
					Lembar ke 1 : untuk Pengusaha Kena Pajak yang menerbitkan Faktur Penjualan<br/>
					Lembar ke 2 : untuk Pembeli
				</div>
			</div>
		</div>
	%endfor
	</body>
</html>
