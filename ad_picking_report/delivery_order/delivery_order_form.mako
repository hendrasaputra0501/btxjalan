<html>
<head>
<style> 
.fontall{
		font-family:Verdana;
		font-size:11px;

}
.div1{
		margin:0px 0 0 0;
		vertical-align:top;
}
.div2{
		margin:0px 0 0 0;
}
.div3{
		margin:10px 0 0 0;
}
#table1{
		margin:0px 0 0px;
}
#table1 tr td{
		/*font-weight: bold;*/
}
#donumber tr td {
	padding: 0px 2px 0 0;

}
.div5{
		text-align: center;
		font-weight: bold;
		font-size: 14px;
}
#bwhtbl{
		border-top: 1px solid #808080;

}
#bwhtbl2{
		border-bottom: 1px solid #808080;

}
#bwhtb3{
		border-top: 1px solid #808080;
		text-align: center;
}
#bwhtblup{
		border-top: 1px solid #808080;
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
}
#lbl1{

		font-family:Verdana;

		font-weight:bold;
		text-transform: uppercase;
}
#lbl2{

		font-family:Verdana;

		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		padding-left:5px;
}
#lbl3{

		font-family:Verdana;

		font-weight:bold;
		text-align: left;
		text-transform: uppercase;
		padding-left:5px;
}
#lbl4{	


		font-family:Verdana;

		font-weight:bold;
		text-transform: uppercase;
		border-bottom: 1px solid #808080;
}
#txt1{
		text-align: center;
		padding-left:5px;
		font-size:11px;
}
#txt2{
		text-align: left;
		padding-left:5px;
}
#txt3{
		text-align: left;
}
}
.div6{
		margin-top: 30px;
}
#tblinsp tr td{
		border-top: 1px solid #808080;
		padding:0 5px 0 5px;
}

#tablea{
		border-bottom: 1px solid #808080;
		border-right: 1px solid #808080;

		font-family:Verdana;

		font-weight:bold;
		text-transform: uppercase;
}
#tableb{
		border-bottom: 1px solid #808080;
		font-family:Verdana;
		font-weight:bold;
		text-transform: uppercase;
		
}
#tablec{
		border-top: 1px solid #808080;
		border-bottom: 1px solid #808080;

		font-family:Verdana;

		font-weight:bold;
		text-transform: uppercase;
}
#tabled{
		border-right: 1px solid #808080;
}
#bwhtblup1{
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		border-top: 1px solid #808080;
		vertical-align:top;
}
#bwhtblup2{
		padding-bottom:80px;
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
}
#bwhtblup3{
		text-align: center;
	}
#bwhtblup4{
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
}
#bwhtblup5{
		font-weight:bold;
		text-align: left;
		text-transform: uppercase;
		border-top: 1px solid #808080;
		vertical-align:top;

}
#centtext{
		text-align: center;
}
#upbold{
		font-weight:bold;
		text-transform: uppercase;
		text-align: center;
}
#borderwhite{
		border-top:white;
		border-left:white;
}
#boldcap{
		font-weight:bold;
		text-transform: uppercase;
		font-size:8px;
}
html,
body {
	margin:0;
	padding:0;
	height:100%;
}
#wrapper {
	min-height:100%;
	position:relative;
}
#header {
	background:#ededed;
	padding:10px;
}
#content {
	padding-bottom:10px; /* Height of the footer element */
}
#footer {
	/*background:blue;*/
	width:100%;
	height:280px;
	position:absolute;
	bottom:0;
	left:0;
}
#break1{
	position:relative;
	display: block;
}
 #break2{
 		/*background: yellow;*/
 		bottom:60;
 		height:210px;
 }

</style>
</head>
<%
from datetime import datetime
def xdate(x):
	try:
		x1 = x[:10]
	except:
		x1 = ''

	try:
		y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
	except:
		y = x1
	return y
%>

<body  class="fontall">
<div id="wrapper">
<!-- <div style="height:540px;"> -->
	<div class="div5">
		<a>SURAT JALAN</a> <br/>
		<a style="border-top:1px solid">DELIVERY ORDER</a>
	</div>
	</br>
	</br>
<div id="content">
	%for o in objects:
	<div class="div1">
		<table width="100%">
			<tr>
				<td  width="30%" style="vertical-align:top;">
					<table>
						<tr>
							<td><a id="lbl1">TO</a></br>
							<span style="text-transform:uppercase;">
								%if o.sale_type=="local":
									%if o.partner_id and o.partner_id.name:
										${o.partner_id and o.partner_id.name} <br/>
									%endif
									${get_address(o.partner_id) or ''}
								%elif o.sale_type=="export":
									<!-- %if o.container_book_id and o.container_book_id.port_from and o.container_book_id.port_from.name=="Semarang": -->
								 		GUDANG S.O. III </br> PELABUHAN TANJUNG MAS </br> SEMARANG
									<!-- %endif -->
								%endif
								</span>			
							</td>
						</tr>
					</table>
				</td>
				<td width="40%" style="vertical-align:top;">
					<table>
						<tr>
							<td>
							<a id="lbl1">
								%if o.sale_type=="export":
									BUYER / CONSIGNEE
								%endif:
							</a></br>
							<span style="text-transform:uppercase;">
								%if o.sale_type=="export":
									%if o.partner_id and o.partner_id.name:
										${o.partner_id and o.partner_id.name} <br/>
									%endif
									${get_address(o.partner_id) or ''}
								%endif:
							</span>
							</td>
						</tr>
					</table>
				</td>
				<td width="30%">
						<table  id="borderwhite" rules="all" width ="100%" style="margin-bottom:8px;">
						<tr >
							<td id="lbl1" width="60%">SURAT JALAN NO.
							</td>
							<td id="lbl3" width="40%" style="border-right:white;">DATE
							</td>
						</tr>
						<tr>
							<td id="txt3" width="60%" style="border-bottom:white;" >${o.name  or ''}
							</td>
							<td id="txt2" width="40%" style="border-right:white;border-bottom:white;">
								%if o.date_done!='False':
									${xdate(o.date_done)}
								%else:
								%endif:
							</td>
						</tr>
						</table>
						<table id="borderwhite" rules="all" width ="100%">
						<tr>
							<td id="lbl1" width="60%">TRANSPORTER </td><td id="lbl3" width="40%" style="border-right:white;">Truck No.</td>
						</tr>
						<tr>
							<td id="txt3" width="60%" style="border-bottom:white;">${o.trucking_company.name or ''}
							</td>
							<td id="txt2" width="40%" style="border-right:white;border-bottom:white;">
								${o.truck_number or ''}
							</td>
						</tr>
						</table>
						%if o.sale_type=="export":
						<table id="borderwhite" rules="all" width ="100%">
						<tr>
							<td id="lbl1" width="60%">DESTINATION</td><td id="lbl3" width="40%" style="border-right:white;"> </td>
						</tr>
						<tr>
							<td id="txt3" width="60%" style="border-bottom:white;">${o.destination_country and o.destination_country.upper() or ''}
							</td>
							<td id="txt2" width="40%" style="border-right:white;border-bottom:white;">
								${''}
							</td>
						</tr>
						</table>
						%endif
				</td>
			</tr>
		</table>
	</div>
	</br>
	<div class="div2">
		%if o.sale_type=="export":
			<table id="borderwhite" width="100%" rules="all">
				<tr>
					<td id="lbl2" width="18%">Shipping Instruction</td>
					<td id="lbl2" width="20%">INVOICE</td>
					<td id="lbl2" width="21%">
					%if o.sale_type=="local":
						Truck No.
					%elif o.sale_type=="export":
						Container No.
					%endif:
					</td><td id="lbl2" width="20%" style="border-right:white;">Seal No.</td>
				</tr>
				<tr>
					<td  id="txt1" width="18%" style="border-bottom:white;">${o.container_book_id and o.container_book_id.name or ''}</td>
					 <td id="txt1" width="20%" style="border-bottom:white;">${o.invoice_id and o.invoice_id.internal_number or ''}</td>
					<td id="txt1" width="21%" style="border-bottom:white;">${o.container_number  or ''} &nbsp; / &nbsp; ${o.container_size and o.container_size.type and o.container_size.type.name or ''}</td><td id="txt1" width="21%" style="border-right:white;border-bottom:white">${o.seal_number or ''}</td>
				</tr>
			</table>
			</br>
		%endif
		<table width="100%">
			<tr>
				<td colspan="4" >
					<a >Kami mengirimkan barang barang sesuai dengan informasi berikut / We are delivering materials as per the following information :</a>
				</td>
				<td>
				</td>
			</tr>
		</table>
	</div>
		<div class="div3">
			</br>
			<table width="100%">
				<tr>
					<td  id="lbl1" width="3%">&nbsp;</td>
					<td  id="lbl1" width="27%">&nbsp;</td>
					<td  id="lbl1" width="6%">&nbsp;</td>
					<td id="lbl4" colspan="4" width="33%" align="center">QUANTITY</td>
					<td id="lbl1" width="19%" style="padding-left:8px;">&nbsp;</td>
					<td id="lbl1" width="12%" style="padding-left:8px;">&nbsp;</td>
				</tr>
				<tr>
					<td  id="lbl1" width="3%">SN.</td>
					<td  id="lbl1" width="27%">URAIAN / DESCRIPTION</td>
					<td  id="lbl1" width="6%">LOT</td>
					<td  id="lbl1" width="7%" align="center" colspan="2">PACKAGES</td>
					<td  id="lbl1" width="13%" align="right">BALES</td>
					<td  id="lbl1" width="13%" align="right">KGS</td>
					<td  id="lbl1" width="19%" style="padding-left:7px;" >SC NO</td>
					<td  id="lbl1" width="12%" style="padding-left:3px;">
						%if o.sale_id and o.sale_id.lc_ids and o.sale_id.lc_ids[0].lc_number:
							LC NO
						%else:
							&nbsp;
						%endif:
					</td>
				</tr>
				<tr>
					<td id="bwhtbl" colspan="9"></td>
				</tr>
			<%
			index = 0
			total_packages = 0
			%>
				%for baris in get_movelines_group(o.move_lines):
					<% index+=1 %>
				<tr>
					<td  align="center"  style="vertical-align:top;"> 
						${index}
					  </td>
					<td  align="left" style="vertical-align:top;">${baris[5] or ''}</td>
					<td  align="left" style="vertical-align:top;">${baris[1] or ''}</td>
					<td  align="right" style="vertical-align:top;">${formatLang(baris[2],digits=0) or ''} </td>
					<% total_packages+=baris[2] %>
					<td width="6%" align="left" style="text-transform:capitalize;vertical-align:top;">${baris[6] or ''}</td>
					<td  align="right" style="vertical-align:top;">
						%if baris[4]:
							%if baris[4]=="BALES" :
								${formatLang(baris[3],digits=4) or ''}
							%elif baris[4]=="KGS" :
									${formatLang((baris[3]*(2.2046/400)),digits=4) or ''}
							%elif baris[4]=="LBS" :
									${formatLang((baris[3]/400),digits=4) or ''}
							%else:
								${formatLang(baris[3],digits=4) or ''}
							%endif
						%endif:
						</td>
						<td  align="right" style="vertical-align:top;">
						
						%if baris[4]=="KGS" :
								${formatLang(baris[3]) or ''}
							%elif baris[4]=="BALES" :
									${formatLang((baris[3]/(2.2046/400)),digits=3) or ''}
							%elif baris[4]=="LBS" :
									${formatLang((baris[3]/2.2046),digits=3) or ''}
							%else:
								${"-"}
							%endif:

						</td>
						<td  style="padding-left:7px;vertical-align:top;"> ${baris[7] and baris[7] or o.sale_id and o.sale_id.name or ''}</td>
						<td  style="padding-left:3px;vertical-align:top;"> ${o.lc_ids and o.lc_ids[0].lc_number or o.sale_id and o.sale_id.lc_ids and o.sale_id.lc_ids[0].lc_number or ''}</td>
				</tr>
				% if baris[8]:
					<tr><td></td><td colspan="8">
						<table width="40%">
							% for x in baris[8].keys():
								<tr>
									<td width="60%" valign="top">${baris[8][x][0]}</td>
									<td width="2%" valign="top">:</td>
									<td width="28%" align="right" valign="top">${baris[8][x][1]}</td>
									<td width="10%" valign="top">${baris[8][x][2]}</td>
								</tr>
							% endfor
						</table>
					</td><tr>
				% endif
				%endfor
				<tr>	
					<td></td><td></td><td id="bwhtbl" colspan="5"> </td><td></td><td></td>
				</tr>
				<% 
				qtykgs,qtyuop=get_totqty_kgs(o.move_lines)
				qtybales=get_totqty_bales(o.move_lines)
				gross_wt = get_gross_wt(o.move_lines)
				%>
				<tr>
					<!-- <td ></td> -->
					%if o.sale_type=="export":
						<td id="lbl1" colspan="3"  align="right" style="padding-right:14px;">Total Net WT. :</td>
					%else:
						<td id="lbl1" colspan="3"  align="right" style="padding-right:14px;">Total :</td>
					%endif
					<td align="right">${formatLang(total_packages,0)}</td>
					<td align="right"></td>
					<td align="right" style="">${formatLang(qtybales,digits=4) or ''}</td>
					<td align="right" style="">${formatLang(qtykgs,digits=3) or ''}</td>
					<td colspan="2"></td>
				</tr>
				%if o.sale_type=="export":
				<tr>
					<!-- <td ></td> -->
					<td colspan="3" id="lbl1"  align="right" style="padding-right:14px;">TOTAL GROSS WT. :</td>
					<td align="right"></td>
					<td align="right"></td>
					<td align="right" style=""></td>
					<td align="right" style="">${formatLang(gross_wt,digits=3) or ''}</td>
					<td colspan="2"></td>
				</tr>
				<tr>
					<!-- <td ></td> -->
					<td colspan="3" id="lbl1"  align="right" style="padding-right:14px;">CONTAINER TARE WT. :</td>
					<td align="right"></td>
					<td align="right"></td>
					<td align="right" style=""></td>
					<td align="right" style="">${formatLang(o.tare_weight,digits=3) or ''}</td>
					<td colspan="2"></td>
				</tr>
				<tr>
					<!-- <td ></td> -->
					<td colspan="3" id="lbl1" align="right" style="padding-right:14px;">TOTAL WT. :</td>
					<td align="right"></td>
					<td align="right"></td>
					<td align="right" style=""></td>
					<td align="right" style="">${formatLang(gross_wt+o.tare_weight,digits=3) or ''}</td>
					<td colspan="2"></td>
				</tr>
				%endif
				<tr>	
					<td id="bwhtbl" colspan="9"> </td>
				</tr>

			</table>
		</div>
			%if o.note:
				<div style="height:70px;margin-bottom:60px;">
				<table>
					<tr>
						<td >
								<a style="font-weight:bold;vertical-align:top;">Remarks : </a>
								</br>
								${(o.note or '').replace('\n','<br/>')}
						</td>
					</tr>
				</table>
				</div>
			%endif
			</div>
<div id="break2" style="vertical-align:top;">&nbsp;</div>
<div id="break1" style="page-break-before: always;">
	<div id="footer">
		<table width="100%" align="top">
				<tr>
					<td align="center" id="boldcap" colspan="9" width="100%" >Jangan mencampur Lots yang berbeda/ Cones warna yang berbeda./ Please do not mix different Lots/Cones of different color tips. </td>
				</tr>
				<tr>
					<td id="bwhtbl" colspan="9" width="100%" height="60px" >&nbsp; </td>
				</tr>
				<tr>
					<td colspan="8" width="84%" >&nbsp; </td><td id="bwhtblup3" width="16%">${o.driver_id and o.driver_id.name or ''}</td>
				</tr>
				<tr>
					<td id="bwhtblup1" width="15%">Prepared By</td>
					<td width="5%" style="border-top:none;">&nbsp;</td>
					<td id="bwhtblup1" width="15%">Checked by</td>
					<td width="5%" style="border-top:none;">&nbsp;</td>
					<td id="bwhtblup1" width="15%">Godown</td>
					<td width="5%" style="border-top:none;">&nbsp;</td>
					<td id="bwhtblup1" width="15%">Security</td>
					<td width="5%" style="border-top:none;">&nbsp;</td>
					<td id="bwhtblup5" width="20%">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Driver </br><a align="left">ID: &nbsp; ${o.driver_id and o.driver_id.id_card or ''}</a>
					</td>
				</tr>
				<tr>
					<td id="bwhtbl2" colspan="9" width="100%"></td>
				</tr>
		</table>
		<table width="100%" >
				<tr>
					<td width="10%" height="70px"></td>
					<td width="25%" style="vertical-align:top;font-weight:bold;">
						for <a id="upbold">${o.company_id and o.company_id.name or ''}</a>
					</td>
					<td width="9%"></td>
					<td width="1%" rowspan="5" style="border-right:1px solid #808080;vertical-align:top;"></td>
					<td id="centtext" colspan="3" width="45%" style="vertical-align:top;">
						Kami telah menerima bahan dalam kondisi baik./ We have received materials in good condition.
					</td>
				</tr>
				<tr>
					<td width="5%"></td>
					<td id="bwhtblup1"  width="35%" style="vertical-align:top;">Authorized Signatory</td>
					<td width="4%"></td>
					<td width="5%"></td>
					<td id="bwhtb3" width="35%" style="vertical-align:top;">
						<a id="bwhtblup4">Customer</a>
						</br>
						<a id="bwhtblup3">(Nama terang & cap perusahaan)</a>
					</td>
					<td width="5%"></td>
				</tr>

		</table>
	<div>
</div>
</div>
%endfor
</body>
</html>