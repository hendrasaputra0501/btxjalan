<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<%
import math
from datetime import datetime
import time
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
	.main-div{
		page-break-before: always;
		padding-top: 10px;
	}
	</style>
</head>
<body>
	<%
	i=1
	%>
	%for x in objects:
		<%
		invoice_lines = [line for line in x.invoice_line]
		n_data_barang = len(invoice_lines)
		next_i = 0
		max_i = next_i + 4
		tot=0
		tot_tax=0
		tot_tax_kb=0
		%>
		% while next_i < n_data_barang:
	<div class="main-div">
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
				<td colspan='3' height="3.7mm"></td>
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
				<td style='width:50%' align="center" rowspan="2"><a>Nama Barang Kena Pajak / Jasa Kena Pajak</a></td>
				<td align="center" width="45%" colspan="2"><a>Harga Jual /Penggantian /Uang Muka /Termin *)</a></td>
			</tr>
			<tr>
				<td width='20%'><a>Valas*)</a></td>
				<td width='25%'><a>(Rp.)</a></td>
			</tr>
			<% 
			last_cur_tax = get_rate_tax(o)
			last_cur_kpmen = get_rate_kpmen(o) 
			tot1=0
			n=1 
			if n_data_barang < max_i :
				max_i = n_data_barang
			%>
			%for x in range(next_i,max_i):
				%if invoice_lines[x].product_id.type != 'service':
			<tr class='inv_line' style="">
				<td style="padding-top:12px" align='left' valign='top'>${x+1}</td>
				<td style="padding-top:12px">
					<div style="position:absolute;width:430px;margin-top:0px,margin-left:0px;" align="left" valign="top">
						${get_desc_line(invoice_lines[x]) or ""}
					</div>
					&nbsp;<br/>&nbsp;<br/>&nbsp;
				</td>
				<td style="padding-right:85px;padding-top:12px;" valign='top' align='right' > &nbsp; </td>
				<td style="padding-right:60px;padding-top:12px;" valign='top' align='right' >${formatLang((invoice_lines[x].price_subtotal) or "",digits=get_digits(dp='Faktur'))}</td>
			</tr>
					<% tot+=invoice_lines[x].price_subtotal %>
					<% n+=1 %>
				%endif
				%if invoice_lines[x].invoice_line_tax_id:
					%for t in invoice_lines[x].invoice_line_tax_id:
						%if t.type == 'percent':
							%if not t.inside_berikat:
								<% tot_tax+=round(t.amount*invoice_lines[x].price_subtotal,2) %>
							%else:
								<% tot_tax+=round(t.tax_amount_kb*invoice_lines[x].price_subtotal,2) %>
								<% tot_tax_kb+=round(t.tax_amount_kb*invoice_lines[x].price_subtotal,2) %>
							%endif
						%elif t.type == 'fixed':
							%if not t.inside_berikat:
								<% tot_tax+=round(t.amount,2) %>
							%else:
								<% tot_tax+=round(t.tax_amount_kb,2) %>
								<% tot_tax_kb+=round(t.tax_amount_kb,2) %>
							%endif
						%endif
					%endfor
				%else:
					<% #tot_tax+=0.1*invoice_line.price_subtotal 
						tot_tax+=0
					%>
				%endif
			<!-- loop IDR line end-->
			%endfor
			<%
			next_i = max_i
			max_i = next_i + 4
			min_height=10.5-float(((n-1)*1.6)+1)
			%>
			<tr class="inv_line" >
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
				<td style="height:${min_height}cm">&nbsp;</td>
			</tr>
			<tr>
				<td>&nbsp;</td>
				<td>
					% if (max_i-4)==n_data_barang:
						<% opacity = 1 %>
					% else:
						<% opacity = 0 %>
					% endif
					<div style="position:absolute;width:550px;margin-top:-20px,margin-left:0px;" align="left" valign="top">
					<a style="opacity:${opacity};">
					Total Invoice : ${o.currency_id.name} ${formatLang(round(tot+tot_tax-tot_tax_kb))}<br />
					<% from ad_num2word_id import num2word %>
					${num2word.num2word_id(round(tot+tot_tax-tot_tax_kb),"en").decode('utf-8')}<br />
					Due Date of Payment : ${formatLang(o.date_due,date=True)}<br />
					</a>
					</div>
					&nbsp;<br/>&nbsp;<br/>&nbsp;
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
				<td style="height:0.1mm;padding-right:85px;text-align:right;"> &nbsp; </td>
				<td style="height:0.1mm;padding-right:60px;text-align:right;"><a style="opacity:${opacity};">${formatLang(round(tot),digits=get_digits(dp='Faktur'))}</a></td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dikurangi potongan harga></a></td>
				<td style="padding-right:85px;text-align:right;">&nbsp;</td>
				<td style="padding-right:60px;text-align:right;"><a style="opacity:${opacity};">0</a></td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dikurangi Uang Muka yang sudah diterima</a></td>
				<td style="padding-right:85px;text-align:right;">&nbsp;</td>
				<td style="padding-right:60px;text-align:right;"><a style="opacity:${opacity};">0</a></td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>Dasar Pengenaan Pajak</a></td>
				<td style="padding-right:85px;text-align:right;"> &nbsp; </td>
				<td style="padding-right:60px;text-align:right;"><a style="opacity:${opacity};">${formatLang(round(tot),digits=get_digits(dp='Faktur'))}</a></td>
			</tr>
			<tr>
				<td colspan='2' style=""><a>PPN = 10% X Dasar Pengenaan Pajak</a></td>
				<td style="padding-right:85px;text-align:right;"> &nbsp; </td>
				<td style="padding-right:60px;text-align:right;"><a style="opacity:${opacity};">${formatLang(round(tot_tax),digits=get_digits(dp='Faktur'))}</a></td>
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
							<td rowspan="2" valign='top' width="30%" style="border: 0;padding-left:-110px;padding-right:110p;">
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
					<p style="padding: 0; margin: 0; margin-top:-33px; padding-left:19mm;">&nbsp;</p>
					<p style="padding: 0; margin: 0; padding-left:19mm;">&nbsp;</p>
				</td>
			</tr>
		</table>
		</div>
			%endfor
		</div>
		%endwhile
	%endfor
	</body>
</html>
