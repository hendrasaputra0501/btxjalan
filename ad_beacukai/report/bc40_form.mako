<html>
<head>
	<style type="text/css">
	.title{
		border-bottom: 3px double #000;
		vertical-align: middle;
	}
	.ttd{
		border-top: 1px dashed #000;
		vertical-align: middle;
	}
	.tdbutdob{
		border-width: 0px 0px 3px 0px;
		border-style: none none double none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdleft{
		border-width: 0px 2px 1px 0px;
		border-style: none dashed dashed none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdupbut{
		border-width: 0px 0px 1px 0px;
		border-style: none none dashed none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdupsolid{
		border-width: 1px 0px 0px 0px;
		border-style: solid none none none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdbosolid{
		border-width: 0px 0px 1px 0px;
		border-style: none none solid none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdbodotted{
		border-width: 0px 0px 1px 0px;
		border-style: none none dotted none;
		border-color: #000;
		vertical-align: middle;
	}
	.tdnone{
		border-width: 0px 0px 0px 0px;
		border-style: none none none none;
		border-color: #000;
		vertical-align: middle;
	}
	h2 {page-break-before: always;}
	</style>
</head>
<%
def xupper(x):
	if isinstance(x, basestring):
		return x.upper()
	else:
		return x or ''

def xdate(x):
	try:
		y = datetime.strptime(x,'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
	except:
		y = x
	return y
%>
%for o in objects:
	<body>
		<br>
		<br>
		<br>
		<br>
		<br>
		<br>
		<br>
		<br>
		<br>
		<!-- HEADER -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 19%;"></td>
					<td class="tdnone" style="width: 10%;">${'o.topage'}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 19%;"></td>
					<td class="tdnone" style="width: 10%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.ktr_pabean')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 19%;"></td>
					<td class="tdnone" style="width: 10%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.jns_tpb')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 19%;"></td>
					<td class="tdnone" style="width: 10%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.tuj_pengiriman')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td colspan="2" rowspan="1" class="tdnone" style="width: 19%;">${xupper('o.no_pendaftaran')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 15%;"></td>
					<!-- o.tgl_pendaftaran --> <td colspan="2" rowspan="1" class="tdnone" style="width: 19%;">${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<!-- D. DATA PEMBERITAHUAN -->
		<!-- PENGUSAHA TPB DAN PENERIMA BARANG -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.npwp_pengusaha')}</td>
					<td class="tdnone" style="width: 22%;"></td>
					<td class="tdnone" style="width: 22%;">${xupper('o.npwp_penerima')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.nm_pengusaha')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td colspan="1" rowspan="2" class="tdnone" style="width: 29%; vertical-align: top;">${xupper('o.almt_pengusaha')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.nm_penerima')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 15%;"></td>
					<td colspan="1" rowspan="2" class="tdnone" style="width: 29%; vertical-align: top;">${xupper('o.almt_penerima')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.no_izin_tpb')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<!-- DOKUMEN PELENGKAP PABEAN -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;">${xupper('o.packing_list')}</td>
					<td class="tdnone" style="width: 3%;"></td>
					<!-- o.tgl_packing_list --> <td class="tdnone" style="width: 12%;">${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
					<td class="tdnone" style="width: 28%;"></td>
					<td class="tdnone" style="width: 3%;"></td>
					<td class="tdnone" style="width: 8%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;">${xupper('o.kontrak')}</td>
					<td class="tdnone" style="width: 3%;"></td>
					<!-- o.tgl_kontrak --> <td class="tdnone" style="width: 12%;">${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
					<td class="tdnone" style="width: 28%;">${xupper('o.srt_keputusan')}</td>
					<td class="tdnone" style="width: 3%;"></td>
					<!-- o.tgl_srt_keputusan --> <td class="tdnone" style="width: 8%;">${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 3%;"></td>
					<td class="tdnone" style="width: 12%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
					<td class="tdnone" style="width: 28%;"></td>
					<td class="tdnone" style="width: 3%;"></td>
					<td class="tdnone" style="width: 8%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 3%;"></td>
					<td class="tdnone" style="width: 12%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
					<td class="tdnone" style="width: 28%;">${xupper('o.no_doc_lain')}</td>
					<td class="tdnone" style="width: 3%;"></td>
					<!-- o.tgl_doc_lain --> <td class="tdnone" style="width: 8%;">${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<!-- RIWAYAT BARANG -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 22%;"></td>
					<!-- o.tgl_bc40_asal --> <td class="tdnone" style="width: 69%;">${xupper('o.no_bc40_asal')} ${xdate('2014-12-11')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<br>
		<br>
		<!-- DATA PENGANGKUTAN -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 21%;"></td>
					<td class="tdnone" style="width: 26%;">${xupper('o.jenis_sarana')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.no_polisi')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<!-- DATA PERDAGANGAN -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.hrg_penyerahan')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<!-- DATA PENGEMAS -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.jns_kemasan')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.jml_kemasan')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 29%;">${xupper('o.merk_kemasan')}</td>
					<td class="tdnone" style="width: 15%;"></td>
					<td class="tdnone" style="width: 29%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<!-- DATA BARANG -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 12%;"></td>
					<td class="tdnone" style="width: 18%;">${xupper('o.volume')}</td>
					<td class="tdnone" style="width: 13%;"></td>
					<td class="tdnone" style="width: 18%;">${xupper('o.berat_kotor')}</td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 16%;">${xupper('o.berat_bersih')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 12%;"></td>
					<td class="tdnone" style="width: 18%;">${xupper('o.merk_kemasan')}</td>
					<td class="tdnone" style="width: 13%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 16%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
		<br>
		<br>
		<br>
		<br>
		<br>
		<br>
		<!-- DETAIL DATA BARANG -->
		<table style="text-align: left; width: 100%;" border="0" cellpadding="0" cellspacing="0">
			<tbody>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 1%;"></td>
					<td class="tdnone" style="width: 3%;">${xupper('o.volume')}</td>
					<td class="tdnone" style="width: 13%;"></td>
					<td class="tdnone" style="width: 18%;">${xupper('o.berat_kotor')}</td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 16%;">${xupper('o.berat_bersih')}</td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
				<tr>
					<td class="tdnone" style="width: 4%;"></td>
					<td class="tdnone" style="width: 12%;"></td>
					<td class="tdnone" style="width: 18%;">${xupper('o.merk_kemasan')}</td>
					<td class="tdnone" style="width: 13%;"></td>
					<td class="tdnone" style="width: 18%;"></td>
					<td class="tdnone" style="width: 14%;"></td>
					<td class="tdnone" style="width: 16%;"></td>
					<td class="tdnone" style="width: 5%;"></td>
				</tr>
			</tbody>
		</table>
	</body>
%endfor
</html>	
