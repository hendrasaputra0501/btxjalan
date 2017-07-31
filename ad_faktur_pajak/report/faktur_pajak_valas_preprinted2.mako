<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<%
import math
%>
<html>
<head>
	<style>
	div
	{
		/*min-height:1280px;*/
		/*height:1280px;*/
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
	body{
	 /*font-family: Perfect DOS VGA 437 Win;*/
	 font-family: arial;
	}
	</style>
</head>
<body>
	<%
	i=1
	%>
	%for x in objects:
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
		<table class="main" cellspacing="0" >
			<tr style=''>
				<td colspan="3" style="">
					<%
					nomor = "%s.%s" % (o.kode_transaksi_faktur_pajak, o.nomor_faktur_id.name)
					%>
					<div style="position:absolute;margin-left:225px; margin-top:88px;">${nomor}</div>
				</td>
			</tr>
			<tr height="5cm" style="">
				<td colspan="3"><a>Pengusaha Kena Pajak</a>&nbsp;<br/></td>
			</tr>
			<tr>
				<td colspan="3" width="100%" style="padding-top:0px;">
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
				<td height="3.7mm"></td>
			</tr>
			<tr style=''>
				<td colspan='3' style=''>
					<table class="partner" style="margin-top:87px;margin-bottom:-20px;">
						<tr valign="top" >
							<td width="10%"><a>Nama</a></td>
							<td width="2%"><a>:</a></td>
							<td width="88%" class="label3" style="padding-left:115px;">${(o.partner_id and o.partner_id.title and o.partner_id.title.name) or ''} ${(o.partner_id and o.partner_id.name) or ''}<br /></td>
						</tr>
						<tr valign="top" style=''>
							<td><a>Alamat</a></td>
							<td><a>:</a></td>
							<td class="label3" style="padding-left:115px;" valign="top" align="left">
								<div style="position:absolute;width:500px;margin-top:0px,margin-left:0px;" align="left" valign="top">
									${alamat(o.partner_id and o.partner_id.id or False) or ''}
								</div>
								<br/>&nbsp;
							</td>
						</tr>
						<tr valign="top">
							<td><a>NPWP</a></td>
							<td><a>:</a></td>
							<td class="label3" style="padding-left:115px;">${(o.partner_id and o.partner_id.npwp) or ''}<br/>&nbsp;</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td style='width:5%' rowspan="2"><a>No.Urut</a></td>
				<td align="center" width="50%" rowspan="2"><a>Nama Barang Kena Pajak / Jasa Kena Pajak</a></td>
				<td align="center" width="45%" colspan="2"><a>Harga Jual /Penggantian /Uang Muka /Termin *)</a></td>
			</tr>
			<tr>
				<td width="20%"><a>Valas*)</a></td>
				<td width="25%"><a>(Rp.)</a></td>
			</tr>
			<% 
			last_cur_tax = get_rate_tax(o)
			last_cur_kpmen = get_rate_kpmen(o) 
			tot=0
			tot_2=0
			tot_tax=0
			tot_tax_kb=0
			tot_tax_2=0
			n=1 
			big_line = 0
			%>
			%for invoice_line in [line for line in o.invoice_line]:
				%if invoice_line.product_id.type != 'service':
			<tr class='inv_line' style="">
				<td style="padding-top:12px" align='left' valign='top'>${n}</td>
				<td style="padding-top:12px">${get_desc_line(invoice_line) or ""}</td>
				<td style="padding-right:30px; padding-top:12px;" valign='top' align='right' >${invoice_line.invoice_id and invoice_line.invoice_id.currency_id and invoice_line.currency_id.name or ''} &nbsp; ${formatLang((invoice_line.price_subtotal) or "",digits=get_digits(dp='Faktur'))}</td>
				<% 
					price_subtotal_2 = invoice_line.price_subtotal*last_cur_tax
				%>
				<td style="padding-right:60px; padding-top:12px;" valign='top' align='right' >${formatLang(int(price_subtotal_2) or "",digits=get_digits(dp='Faktur'))}</td>
			</tr>
					<% 
						tot+=invoice_line.price_subtotal 
						tot_2+=price_subtotal_2
						n+=1
						curr_line = get_desc_line(invoice_line) or ""
						split_line = curr_line.split("<br/>")
					%>
					%if len(split_line[0])>55:
						<%
						big_line+=1
						%>
					%endif
				%endif
				%if invoice_line.invoice_line_tax_id:
					%for t in invoice_line.invoice_line_tax_id:
						%if t.type == 'percent':
							%if not t.inside_berikat:
								<% 
									tot_tax+=round(t.amount*invoice_line.price_subtotal,2) 
									tot_tax_2+=round(t.amount*price_subtotal_2,2)
								%>
							%else:
								<% 
									tot_tax+=round(t.tax_amount_kb*invoice_line.price_subtotal,2)
									tot_tax_kb+=round(t.tax_amount_kb*invoice_line.price_subtotal,2)
									tot_tax_2+=round(t.tax_amount_kb*price_subtotal_2,2) 
								%>
							%endif
						%elif t.type == 'fixed':
							%if not t.inside_berikat:
								<% 
									tot_tax+=round(t.amount,2)
									tot_tax_2+=round(t.amount,2)
								%>
							%else:
								<%
									tot_tax+=round(t.tax_amount_kb,2)
									tot_tax_kb+=round(t.tax_amount_kb,2)
									tot_tax_2+=round(t.tax_amount_kb,2)
								%>
							%endif
						%endif
					%endfor
				%else:
					<% #tot_tax+=0.1*invoice_line.price_subtotal 
						tot_tax+=0
						tot_tax_2+=0
					%>
				%endif
			<!-- loop IDR line end-->
			%endfor
			%if not big_line or big_line==0:
				<% 
				min_height=10.5-float(((n-1)*1.6)+1)
				%>
			%else:
				<%
				min_height = 10.5-float(((n-1)*1.6)+1)-(big_line*0.4) 
				%>
			%endif
			<tr class="inv_line" >
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
			</tr>
			<tr>
				<td>&nbsp;</td>
				<td>
					Total Invoice : ${o.currency_id.name} ${formatLang(tot+tot_tax-tot_tax_kb)}<br />
					<% from ad_num2word_id import num2word %>
					${num2word.num2word_id(tot+tot_tax-tot_tax_kb,"en").decode('utf-8')}<br />
					Due Date of Payment : ${formatLang(o.date_due,date=True)}<br />
				</td>
				<td colspan="2">&nbsp;</td>
			</tr>
			<tr>
				<td colspan='2' style="height:0.1mm;">
					<p style="height:-2px;margin-top:0px;margin-bottom:2px;" valign="bottom">
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
				<td style="height:0.1mm;padding-right:30px;text-align:right;">${invoice_line.invoice_id and invoice_line.invoice_id.currency_id and invoice_line.currency_id.name or ''} &nbsp; ${formatLang(tot,digits=get_digits(dp='Faktur'))}</td>
				<td style="height:0.1mm;padding-right:60px;text-align:right;">${formatLang(int(tot*last_cur_tax),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dikurangi potongan harga></a></td>
				<td style="padding-right:30px;text-align:right;">0</td>
				<td style="padding-right:60px;text-align:right;">0</td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dikurangi Uang Muka yang sudah diterima</a></td>
				<td style="padding-right:30px;text-align:right;">0</td>
				<td style="padding-right:60px;text-align:right;">0</td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dasar Pengenaan Pajak</a></td>
				<td style="padding-right:30px;text-align:right;">${invoice_line.invoice_id and invoice_line.invoice_id.currency_id and invoice_line.currency_id.name or ''} &nbsp; ${formatLang(tot,digits=get_digits(dp='Faktur'))}</td>
				<td style="padding-right:60px;text-align:right;">${formatLang(int(tot_2),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>PPN = 10% X Dasar Pengenaan Pajak</a></td>
				<td style="padding-right:30px;text-align:right;">${invoice_line.invoice_id and invoice_line.invoice_id.currency_id and invoice_line.currency_id.name or ''} &nbsp; ${formatLang(tot_tax,digits=get_digits(dp='Faktur'))}</td>
				<td style="padding-right:60px;text-align:right;"> ${formatLang(int(round(tot_tax_2)),digits=get_digits(dp='Faktur'))}</td>
			</tr>
			<tr>
				<td colspan='4'>
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
								dfaktur= o.faktur_pajak_date_entry!='False' and o.faktur_pajak_date_entry or (o.tax_date!='False' and o.tax_date or o.date_invoice)
								%>
								<div align='center' style="position:absolute;width:260px;margin-top:0px;margin-left:-90px;">
									Semarang, ${formatLang(dfaktur,date=True)}<br/>
									for ${o.company_id and o.company_id.name or ''}
								</div>
								&nbsp;
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
							<td rowspan="2" valign="top" width="30%" style="border: 0;padding-left:-110px;padding-right:110px;">
								<div align='center' style="position:absolute;width:260px;margin-top:0px;margin-left:-90px;">${o.authorized_by and o.authorized_by.name.upper() or 'None' }</div>
								<div align='center' style="position:absolute;width:260px;margin-top:27px;margin-left:-90px;">
									${(o.job_position_id and o.job_position_id.name or (o.authorized_by and o.authorized_by.job_id and o.authorized_by.job_id.name or '')).upper()}
								</div>
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
					<p style="padding: 0; margin: 0; margin-top:-33px; padding-left:19mm;">${last_cur_kpmen}</p>
					<p style="padding: 0; margin: 0; padding-left:19mm;">${formatLang(last_cur_tax)}</p>
				</td>
			</tr>
		</table>
		</div>
		%endfor
	%endfor
	</body>
</html>
