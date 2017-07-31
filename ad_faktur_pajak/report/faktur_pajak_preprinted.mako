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
		width: 100%;
	}
	td
	{
		padding:4px;
	}
	#page_note
	{
		border:0px solid #000;
		right:0px;
		position:relative;
		font-size:12px;
		margin-right:0px;
	}
	table .header
	{
		display:none;
		width: 100%;
	}
	.main
	{
		width:23.4cm;
		margin:-15px auto 0px;
	}
	.main td
	{
		border:0px solid #000;
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
		/*border-collapse:collapse;*/
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
	a{
		opacity: 0;
	}
	.label2{
		width: 45mm;
		min-width: 45mm;
	}
	.label3{
		padding-left: 1cm;
	}
	body{
	 /*font-family: Perfect DOS VGA 437 Win;*/
	 font-family: arial;
	}
	</style>
</head>
<body>
	<%
	i=1
	#print "??????????????????????????????", objects
	%>
	%for x in objects:
	<!-- %for i in (1,2,3): -->
	<div style="clear:both;">
		<table width="895px" cellpadding="0" style="opacity:0;">
			<tr>
				<td width="537px" ><a></a></td>
				<td width="358px" >
					<table id="page_note" right="0" width="358px">
						<tr>
							<td width="20%" valign="top"><a>Lembar ${i} : </a></td>
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
		<center style="width:23.4cm;" height= <h3><a>FAKTUR PAJAK</a></h3></center>
		%for o in objects:
		<% setLang(o.partner_id.lang) %>
		<table class="main" cellspacing="0">
			<tr>
				<td colspan="3"><a>Kode dan Nomor Seri Faktur Pajak : 
					</a>
					<%
					nomor = "%s.%s" % (o.kode_transaksi_faktur_pajak, o.nomor_faktur_id.name)
					%>
					<div style="position:absolute;margin-left:225px;margin-top:90px;">${nomor}</div>
				</td>
			</tr>
			<tr height="3cm">
				<td colspan="3"><a>Pengusaha Kena Pajak</a></td>
			</tr>
			<tr>
				<td colspan="3" width="100%">
					<table class="partner" border="0">
						<tr valign="top">
							<td class="label2"><a>Nama</a></td>
							<td><a>:</a></td>
							<td><a>${(o.company_id and o.company_id.name) or ''}</a></td>
						</tr>
						<tr valign="top">
							<td class="label2"><a>Alamat</a></td>
							<td><a>:</a></td>
							<td><a>${alamat(o.company_id and o.company_id.partner_id and o.company_id.partner_id.id or False ) or ''}</a></td>
						</tr>
						<tr valign="top">
							<td class="label2"><a>NPWP</a></td>
							<td><a>:</a></td>
							<td><a>${(o.company_id and o.company_id.partner_id and o.company_id.partner_id.npwp) or ''}</a></td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td colspan='3'><a>Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak</a></td>
			</tr>
			<tr>
				<td height="3.8mm"></td>
			</tr>
			<tr>
				<td colspan='3' style="padding-top:60px;">
					<table class="partner" border="0" style="margin-top:10px;">
						<tr valign="top">
							<td><a>Nama</a></td>
							<td><a>:</a></td>
							<td class="label3">${(o.partner_id and o.partner_id.title and o.partner_id.title.name) or ''} ${(o.partner_id and o.partner_id.name) or ''}<br /></td>
						</tr>
						<tr valign="top">
							<td><a>Alamat</a></td>
							<td><a>:</a></td>
							<td class="label3">${alamat(o.partner_id and o.partner_id.id or False) or ''}</td>
						</tr>
						<tr valign="top">
							<td><a>NPWP</a></td>
							<td><a>:</a></td>
							<td class="label3">${(o.partner_id and o.partner_id.npwp) or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td style='width:40px'><a>No.Urut</a></td>
				<td align="center"><a>Nama Barang Kena Pajak / Jasa Kena Pajak</a></td>
				<td align="center" width="20%"><a>Harga Jual /Penggantian /Uang Muka /Termin *)</a></td>
			</tr>
			<% tot=0 %>
			<% tot_tax=0 %>
			<% n=1 %>
			%for invoice_line in [line for line in o.invoice_line]:
				%if invoice_line.product_id.type != 'service':
				<tr></tr>
			<tr class='inv_line'>
				<td align='left' style="margin-bottom:-10px;">${n}</td>
				<td style="padding-top:12px">${get_desc_line(invoice_line) or ""}</td>
				<td style="padding-right:55px; padding-top:5px;" align='right' width="30%">${formatLang(int((invoice_line.price_subtotal)),digits=get_digits(dp='Faktur'))}</td>
			</tr>
					<% tot+=invoice_line.price_subtotal %>
					<% n+=1 %>
				%endif
				%if invoice_line.invoice_line_tax_id:
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
			<% 
			min_height=10.3-float(n)
			%>
			<tr class="inv_line" ><td style="height:${min_height}cm">&nbsp;</td><td style="height:${min_height}cm">&nbsp;</td><td style="height:${min_height}cm">&nbsp;</td></tr>
			<!-- <tr style="margin-top:-120px;"> -->
				<td style="margin-top:-100px;">&nbsp;</td>
				<td>
					Total Invoice : ${o.currency_id.name} ${formatLang(tot+tot_tax)}<br />
					<% from ad_num2word_id import num2word %>
					${num2word.num2word_id(tot+tot_tax,"en").decode('utf-8')}<br />
					Due Date of Payment : ${formatLang(o.date_due,date=True)}<br />
				</td>
				<!-- <td>&nbsp;</td> -->
			</tr>
			<tr>
				<td colspan='2' style="height:1mm;">
					<p style="height:-2px;margin-top:-10px;" valign="bottom">
					% if o.fp_harga_jual:
						<a style="opacity:0;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxxxxxxxxxxxx</a>
					% else:
						<a style="opacity:1;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxxxxxxxxxxxx</a>
					% endif
					&nbsp;&nbsp;
					% if o.fp_penggantian:
						<a style="opacity:0;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxxxx</a>
					% else:
						<a style="opacity:1;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxxxx</a>
					% endif
					&nbsp;&nbsp;
					% if o.fp_uang_muka:
						<a style="opacity:0;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxx</a>
					% else:
						<a style="opacity:1;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxxxxxxxx</a>
					% endif
					&nbsp;&nbsp;
					% if o.fp_termin:
						<a style="opacity:0;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxx</a>
					% else:
						<a style="opacity:1;text-decoration: line-through;margin-left:-45px;">xxxxxxxxxx</a>
					% endif
					&nbsp;&nbsp;
					</p>
				</td>
				<td style="height:1mm;padding-right:55px;text-align:right;">${formatLang(int(tot),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2' style="height:0.1mm;"><a>Dikurangi potongan harga></a></td>
				<td style="height:0.1mm;padding-right:55px;text-align:right;">0</td>
			</tr>
			<tr>
				<td colspan='2' style="height:0.3mm;"><a>Dikurangi Uang Muka yang sudah diterima</a></td>
				<td style="height:0.3mm;padding-right:55px;text-align:right;">0</td>
			</tr>
			<tr>
				<td colspan='2' style="height:0.3mm;"><a>Dasar Pengenaan Pajak</a></td>
				<td style="height:0.3mm;padding-right:55px;text-align:right;">${formatLang(int(tot),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2' style="height:0.1mm;"><a>PPN = 10% X Dasar Pengenaan Pajak</a></td>
				<td style="height:0.1mm;padding-right:55px;text-align:right;"> ${formatLang(int(round(tot_tax)),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='3'>
					<table width="100%" cellspacing='0' style="margin-top:-10px;" border="0">
						<tr>
							<td colspan='3' class='pajak'><a>Tarif Penjualan Atas Barang Mewah</a></td>
							<td width="30%" style="text-align:left; border: 0;"><a>${o.company_id.partner_id.city or ""}, ${time.strftime('%d %B %Y', time.strptime( o.date_invoice,'%Y-%m-%d'))}
									${o.company_id and ('<br/>For ' + o.company_id.name) or ''}
									</a>
							</td>
							<td></td>
							<td></td>
						</tr>
						<tr>
							<td><a>Tarif</a></td>
							<td><a>DPP</a></td>
							<td><a>PPn</a></td>
							<td width="30%" style="text-align:center; border: 0;padding-left:-110px;padding-right:110px">
								<%
								dfaktur= o.tax_date!='False' or o.date_invoice
								%>
								Semarang, ${formatLang(dfaktur,date=True)}<br/>
								for ${o.company_id and o.company_id.name or ''}
							</td>
							<td><a></a></td>
							<td></td>
						</tr>
						<tr>
							<td><a>........... %</a></td>
							<td><a>Rp </a></td>
							<td><a>Rp </a></td>
							<td rowspan='3' class='pajak'></td>
							<td></td>
							<td></td>
						</tr>
						<tr>
							<td><a>........... %</a></td>
							<td><a>Rp </a></td>
							<td><a>Rp</a></td>
							<td style="border: 0";></td>
							<td></td>
						</tr>
						<tr>
							<td><a>........... %</a></td>
							<td><a>Rp </a></td>
							<td><a>Rp</a></td>
							<td></td>
							<td></td>
						</tr>
						<tr>
							<td><a>........... %</a></td>
							<td><a>Rp </a></td>
							<td><a>Rp </a></td>
							<td rowspan="2" width="30%" style="text-align:center;border: 0;padding-left:-110px;padding-right:110px;">
								<p style="margin-top:-20px;margin-bottom:20px;">${o.authorized_by and o.authorized_by.name.upper() or 'None' }</p><br/>
								<p style="border-top:0px solid;margin-top:-33px;margin-bottom:20px;">
									${(o.authorized_by and o.authorized_by.department_id and o.authorized_by.department_id.name or '').upper()}&nbsp;${(o.authorized_by and o.authorized_by.job_id and o.authorized_by.job_id.name or '').upper()} 
								</p>
							</td>
							<td></td>
							<td></td>
						</tr>
						<tr>
							<td colspan='2'><a>Jumlah</a></td>
							<td></td>
							<td style="border: 0; margin-top: -10px;"></td>
							<td></td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
		<font size='0.5' style='margin-left:14px'><a>*) Coret yang tidak perlu</a></font>
		</div>
		%endfor
	%endfor
	</body>
</html>
