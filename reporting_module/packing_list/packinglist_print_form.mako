<html>
<head>
<style>
.fontall{
			font-family: "Times New Roman";
			font-size: 12pt;
}
 
 #title1{	
 			font-family: "Times New Roman";
			border-bottom: 3px double #000;
			font-size: 28px;
			font-weight: bold;
 }
 #div1 {

 }
 #tdtot{
 		font-weight:bold;
 		text-align: right;
 		padding-right: 10px;
 }
 #tdtblhdr{
 			font-weight: bold;
 			text-align: center;
 }
 #tbl1 tr td{
 				padding-left: 10px;
 }
 #tdnum{
 		text-align: right;
 		padding-right: 10px;
 }
 #lbl{
 		font-weight: bold;
 }
 #name{
 		font-weight: bold;
 }
 /*.table1 tr td{
 		padding-left: 5px;

 }*/

</style>

</head>
<body class="fontall" >
<div><center><a id="title1">PACKING LISTsssssst</a></center></div>
%for o in objects:
<div id="div1">
	<table class="table1" width="100%">
		<%
			packinglist_nbr=packing_serial(o.picking_ids[0].invoice_id.internal_number)
		%>
		<tr>
			<td>NO. ${packinglist_nbr}

			</td>
			<td style="text-align:right;padding-right:20px;">Date : </td>
		</tr>
	</table>
</div>
<div>
	<table class="table1" rules="cols" style="border-top:1px solid;" width="100%" >
			<tr>
				<td id="lbl" height="30px" width="50%" >SHIPPER &nbsp :</td>
				<td id="lbl" width="50%">SALES CONFIRMATION  &nbsp &nbsp &nbsp &nbsp &nbsp &nbsp  &nbsp &nbsp &nbsp NO. & DATE : </td>
			</tr>
			<tr>
				<td id="name">${o.shipper and o.shipper.partner_id and o.shipper.partner_id.name or ''} </td>
				<td><table width="100%" style="border-bottom:1px solid;"><tr><td id="name" width="30%">${o.picking_ids[0] and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.name or ''}</td><td width="70%">DD  :&nbsp ${o.picking_ids[0] and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.date_order or ''}</td></tr></table></td>
			</tr>
			<tr>
				<td>${o.shipper and o.shipper.partner_id and o.shipper.partner_id.street or ''} <br/>
					${o.shipper and o.shipper.partner_id and o.shipper.partner_id.street2 or ''}<br/>
				 	${o.shipper and o.shipper.partner_id and o.shipper.partner_id.city or ''} &nbsp ${o.shipper and o.shipper.partner_id and o.shipper.partner_id.zip or ''}  &nbsp
				 	${o.shipper and o.shipper.partner_id and o.shipper.partner_id.country_id.name or ''}</td>
				<td id="lbl" >LETTER OF CREDIT NO. & DATE  :</td>
			</tr>
	</table>
	<table class="table1" rules="cols" style="border-top:1px solid;" width="100%" >
			<tr>
				<td id="lbl" height="30px" width="50%" >BUYER &nbsp :</td>
				<td id="lbl" width="50%"><table width="100%"><tr><td id="lbl" width="20%">PRICE TERM</td><td> :</td><td> ${o.picking_ids[0].sale_id.incoterm.code or ''} &nbsp , ${o.picking_ids[0] and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.payment_term and o.picking_ids[0].sale_id.payment_term.name or ''} </td></tr></table>
			</td>
			</tr>
			<tr>
				<td id="name">&nbsp ${o.consignee and o.consignee.name or ''} <br/>
				</td>

				<td><table width="100%" style="border-bottom:1px solid;border-top:1px solid;"><tr><td id="lbl" width="20%">FROM</td><td>:</td> </td><td>${o.port_from and o.port_from.name or ''}, &nbsp ${o.port_from and o.port_from.country and o.port_from.country.name or ''} </td></tr></table></td>
			</tr>
			<tr>
				<td>${o.consignee and o.consignee.street or ''}<br/>
					${o.consignee and o.consignee.street2 or ''}<br/>
					${o.consignee and o.consignee.street3 or ''} &nbsp ,
					${o.consignee and o.consignee.country_id.name or ''}
				</td>
				<td><table width="100%"><tr><td id="lbl"  width="20%">TO</td><td>:</td></td><td>${o.port_to and o.port_to.name or ''}, &nbsp ${o.port_to and o.port_to.country and o.port_to.country.name or ''}</td></tr></table></td>
			</tr>
	</table>
</div>
<br />
<br />
<div>
	<table id="tbl1" rules="all" style="border:1px solid;" width="100%">
	
		<tr>	
			<td id="tdtblhdr">MARKS & NOS</td><td id="tdtblhdr">DESCRIPTION OF GOODS</td><td id="tdtblhdr">GROSS WEIGHT IN KGS</td><td id="tdtblhdr">NET WEIGHT IN KGS</td><td id="tdtblhdr">VOLUME IN CBM</td>

		</tr>
<%
totgross,totnwt,totvolume=packingtot_line(o.goods_lines)
%>
		%for baris in packingdtl_line(o.goods_lines):
		<tr>	
			<td>${baris[0] or ''}</td><td>${baris[1] or ''}</td><td id="tdnum">${'%.2f' % baris[2] or ''}</td><td id="tdnum">${'%.2f' % baris[3] or ''}</td><td id="tdnum">${'%.2f' % baris[4] or ''}</td>

		</tr>
		%endfor
		<tr>	
			<td id="tdtot"></td><td id="tdtblhdr">TOTAL</td><td id="tdtot">${'%.2f' % totgross} </td><td id="tdtot">${'%.2f' % totnwt} </td><td id="tdtot">${'%.2f' % totvolume}</td>

		</tr>
	</table>
</div>
<br />

<div>
	<table class="table1" width="100%" style="border-bottom:1px solid;">

		%for list in packinglist_line(o.package_details):
		<tr>
			<td width="20%" style="font-weight:bold;text-decoration:underline;">${list[6] or ''}</td><td width="2%"></td><td></td>
		</tr>
		<tr>
			<td width="20%">NET WEIGHT PER CONE</td><td width="2%">:</td><td  id="tdnum" width="5%">${'%.2f' % list[0] or ''}</td><td>KGS</td>
		</tr>
		<tr>
			<td>GROSS WEIGHT PER CONE</td><td>:</td><td id="tdnum">${'%.2f' % list[1] or ''}</td><td>KGS</td>
		</tr>
		<tr>
			<td>NO. OF CONES PER CARTON</td><td>:</td><td id="tdnum">${'%.2f' % list[2] or ''}</td><td>KGS</td>
		</tr>
		<tr>	
			<td>NET WEIGHT PER CARTON</td><td>:</td><td id="tdnum">${'%.2f' % list[3] or ''}</td><td>KGS</td>
		</tr>
		<tr>
			<td>GROSS WEIGHT PER CONE</td><td>:</td><td id="tdnum">${'%.2f' % list[4] or ''}</td><td>KGS</td>
		</tr>
		<tr>
			<td>TOTAL CARTONS</td><td>:</td><td id="tdnum">${'%.2f' % list[5] or ''}</td><td>KGS</td>

		</tr>
		%endfor
	</table>
</div>
<div id="lbl" >Note :</div>
<div>${o.note.replace('\n','<br/>') or ''}</div>
%endfor
<br/>
<br/>
<br/>
<br/>
<div style="width:190px;margin-left:1100px;border-top:1px dotted;">Authorized Signatory :er</div>
</body>
</html>