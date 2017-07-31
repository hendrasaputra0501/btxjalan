<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<%
import math
%>
<html>
<head>
	<style>
	div
	{
		min-height:1280px;
		height:1280px;
		margin-top:0px;
		margin-bottom:0px;
		position:relative;
	}
	table
	{
		font-size:13px;
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
		font-size:12px;
		margin-right:0px;
	}
	table .header
	{
		display:none;
	}
	.main
	{
		width:23.4cm;
		margin:-15px auto 0px;
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
		width:23.4cm;
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
	<%
	i=1
	%>
	%for x in objects:
	<!-- %for i in (1,2,3): -->
	<div style="clear:both;">
		<table width="895px" cellpadding="0" style="opacity:0;">
			<tr>
				<td width="537px" ></td>
				<td width="358px" >
					<table id="page_note" right="0" width="358px">
						<tr>
							<td width="20%" valign="top">Lembar ${i} : </td>
							<td width="80%">
								%if i==1:
								Untuk Pembeli BKP / Penerima JKP sebagai bukti Pajak Masukan
								%elif i==2:
								Untuk Pengusaha Kena Pajak yang menerbitkan Faktur Pajak Standar sebagai  bukti Pajak Keluaran
								%else:
								Untuk Pembukuan</br>
								%endif
							</td>
						</tr>	
					</table>
				</td>
			</tr>
		</table>
		<center style="width:23.4cm;"><h3>FAKTUR PAJAK</h3></center>
		%for o in objects:
		<% setLang(o.partner_id.lang) %>
		<table class="main" cellspacing="0">
			<tr>
				<td colspan="3">Kode dan Nomor Seri Faktur Pajak : 
					<%
					nomor = "%s.%s" % (o.kode_transaksi_faktur_pajak, o.nomor_faktur_id.name)
					%>
					${nomor}
				</td>
			</tr>
			<tr>
				<td colspan="3">Pengusaha Kena Pajak</td>
			</tr>
			<tr>
				<td colspan="3">
					<table class="partner" border="0">
						<tr valign="top">
							<td>Nama</td>
							<td>:</td>
							<td>${(o.company_id and o.company_id.name) or ''}</td>
						</tr>
						<tr valign="top">
							<td>Alamat</td>
							<td>:</td>
							<td>${alamat(o.company_id and o.company_id.partner_id and o.company_id.partner_id.id or False ) or ''}</td>
						</tr>
						<tr valign="top">
							<td>NPWP</td>
							<td>:</td>
							<td>${(o.company_id and o.company_id.partner_id and o.company_id.partner_id.npwp) or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td colspan='3'>Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak</td>
			</tr>
			<tr>
				<td colspan='3'>
					<table class="partner" border="0">
						<tr valign="top">
							<td>Nama</td>
							<td>:</td>
							<td>${(o.partner_id and o.partner_id.title and o.partner_id.title.name) or ''} ${(o.partner_id and o.partner_id.name) or ''}</td>
						</tr>
						<tr valign="top">
							<td>Alamat</td>
							<td>:</td>
							<td>${alamat(o.partner_id and o.partner_id.id or False) or ''}</td>
						</tr>
						<tr valign="top">
							<td>NPWP</td>
							<td>:</td>
							<td>${(o.partner_id and o.partner_id.npwp) or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td style='width:40px'>No.Urut</td>
				<td align="center">Nama Barang Kena Pajak / Jasa Kena Pajak</td>
				<td align="center" width="30%">Harga Jual /Penggantian /Uang Muka /Termin *)</td>
			</tr>
			<!-- loop IDR line start-->
			<% tot=0 %>
			<% tot_tax=0 %>
			<% n=1 %>
			%for invoice_line in [line for line in o.invoice_line]:
				%if invoice_line.product_id.type != 'service':
			<tr class='inv_line' valign="top">
				<td align='right'>${n}</td>
				<td>${get_desc_line(invoice_line) or ""}</td>
				<td align='right' width="30%">${formatLang(int((invoice_line.price_subtotal)),digits=get_digits(dp='Faktur'))}</td>
			</tr>
					<% tot+=invoice_line.price_subtotal %>
					<% n+=1 %>
				%endif
				%if invoice_line.invoice_line_tax_id:
					<%print "------- ada tax ---------"%>
					%for t in invoice_line.invoice_line_tax_id:
						%if t.type == 'percent':
							%if not t.inside_berikat:
								<% tot_tax+=t.amount*invoice_line.price_subtotal %>
							%else:
								<% tot_tax+=t.tax_amount_kb*invoice_line.price_subtotal %>
							%endif
						%elif t.type == 'fixed':
							%if not t.inside_berikat:
								<% tot_tax+=t.amount %>
							%else:
								<% tot_tax+=t.tax_amount_kb %>
							%endif
						%endif
					%endfor
				%else:
					<% #tot_tax+=0.1*invoice_line.price_subtotal 
						tot_tax+=0.0
					%>
				%endif
			<!-- loop IDR line end-->
			%endfor
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
			<tr class="inv_line">
				<td>&nbsp;</td>
				<td>
					Total Invoice : ${o.currency_id.name} ${formatLang(tot+tot_tax)}<br/>
					<% from ad_num2word_id import num2word %>
					${num2word.num2word_id(tot+tot_tax,"en").decode('utf-8')}<br/>
					Due Date of Payment : ${formatLang(o.date_due,date=True)}
				</td>
				<td>&nbsp;</td>
			</tr>
			<tr>
				<td colspan='2'>
					Harga Jual /Penggantian /Uang Muka /Termin *)
				</td>
				<td align='right'>${formatLang(int(tot),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2'>Dikurangi potongan harga</td>
				<td align='right'>0</td>
			</tr>
			<tr>
				<td colspan='2'>Dikurangi Uang Muka yang sudah diterima</td>
				<td align='right'>0</td>
			</tr>
			<tr>
				<td colspan='2'>Dasar Pengenaan Pajak</td>
				<td align='right'>${formatLang(int(tot),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2'>PPN = 10% X Dasar Pengenaan Pajak</td>
				<td align='right'>${formatLang(int(round(tot_tax)),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='3'>
					<table width="100%" border="0px" cellspacing='0'>
						<tr>
							<td colspan='4' class='pajak'>Tarif Penjualan Atas Barang Mewah</td>
							<td width="30%" style="text-align:left; border: 0;">${o.company_id.partner_id.city or ""}, ${time.strftime('%d %B %Y', time.strptime( o.date_invoice,'%Y-%m-%d'))}
									${o.company_id and ('<br/>For ' + o.company_id.name) or ''}
							</td>
						</tr>
						<tr>
							<td>Tarif</td>
							<td>DPP</td>
							<td>PPn</td>
						</tr>
						<tr>
							<td>........... %</td>
							<td>Rp </td>
							<td>Rp </td>
							<td rowspan='4' class='pajak'></td>
						</tr>
						<tr>
							<td>........... %</td>
							<td>Rp </td>
							<td>Rp</td>
							<td style="border: 0";></td>
						</tr>
						<tr>
							<td>........... %</td>
							<td>Rp </td>
							<td>Rp</td>
							<td style="border: 0";></td>
						</tr>
						<tr>
							<td>........... %</td>
							<td>Rp </td>
							<td>Rp</td>
							<td rowspan="2" width="30%" style="text-align:left; border: 0;">
								<span style="border-bottom: 1px solid;">Nama : </span>
								<p style="margin-top: 0;">
									Jabatan : 
								</p>
							</td>
						</tr>
						<tr>
							<td colspan='2'>Jumlah</td>
							<td></td>
							<td style="border: 0; margin-top: -10px;"></td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
		%endfor
		<font size='0.5' style='margin-left:14px'>*) Coret yang tidak perlu</font>
		</div>
		<!-- %endfor -->
		%endfor
	</body>
</html>
