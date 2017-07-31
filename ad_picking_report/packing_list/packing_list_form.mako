<html>
<head>
	<style>
	.title{
		border-bottom: 2px solid #000;
	}
	.ttd{
		border-top: 1px dashed #000;
	}
	.tdbutdob{
		border-width: 0px 0px 1px 0px;
		border-style: none none solid none;
		border-color: #000;
	}
	.tdleft{
		border-width: 0px 1px 1px 0px;
		border-style: none solid solid none;
		border-color: #000;
	}
	.tdupbut{
		border-width: 0px 0px 1px 0px;
		border-style: none none dashed none;
		border-color: #000;
	}
	</style>
</head>
<body>
<%

%>
%for o in objects:
	<center><h2><a class='title'>
			${o.packinglist_title or 'Packing List'}
	</a></h2></center>
	<br/>
	<table width='100%'>
		<tr width='100%'>
			<td class='tdbutdob' width='50%' align='left' valign='top'>
				NO. &nbsp;&nbsp;&nbsp; : ${o.name or ''}
			</td>
			<td class='tdbutdob' colspan='2' width='50%' align='right' valign='top'>
				DATE &nbsp;&nbsp;&nbsp;: ${o.date_instruction} 
			</td>
		</tr>
		<tr width='100%'>
			<td class='tdleft' rowspan='5' width='50%' align='left' valign='top'>
				SHIPPER &nbsp;&nbsp;&nbsp; : <br/><br/>
				${o.shipper.name or ''} <br/>
				${o.shipper.street or ''} </br/>
				${o.shipper.street2 or ''} <br/>
				${o.shipper.city or ''} &nbsp; ${o.shipper.zip or ''} , &nbsp;${o.shipper.country_id.name or ''}
			</td>
			<td width='50%' colspan='2' align='left' valign='top'>
				SALES CONTRACT NO. & DATE : 
			</td>
		</tr>
		<tr width='50%'>
			<td width='18%' align='left' style='border-bottom:1px solid #000;'>
				${}
			</td>
			<td width='32%' align='left' style='border-bottom:1px solid #000;'>
				&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DD:&nbsp;${}
			</td>
		</tr>
		<tr width='50%'>
			<td width='50%' colspan='2' align='left' valign='top'>
				LETTER OF CREDIT NO. & DATE : 
			</td>
		</tr>
		<tr width='50%'>
			<td width='18%' align='left'>
				${}
			</td>
			<td width='32%' align='left'>
				&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DD:&nbsp;${}
			</td>
		</tr>
		<tr width='50%'>
			<td width='18%' align='left' style='border-bottom:1px solid #000;'>
				ISSUED BY
			</td>
			<td width='32%' align='left' style='border-bottom:1px solid #000;'>
				:&nbsp;${}
			</td>
		</tr>
		<tr width='100%'>
			<td class='tdleft' width='50%' rowspan='3' align='left' valign='top'>
				APPLICANT &nbsp;&nbsp;&nbsp; : </br></br>
				${o.shipper.name or ''} <br/>
				${o.shipper.street or ''} </br/>
				${o.shipper.street2 or ''} <br/>
				${o.shipper.city or ''} &nbsp; ${o.shipper.zip or ''} , &nbsp;${o.shipper.country_id.name or ''}
			</td>
			<td width='18%' align='left' style='border-bottom:1px solid #000;'>
				PRICE TERMS
			</td>
			<td width='32%' align='left' style='border-bottom:1px solid #000;'>
				:&nbsp;${}
			</td>
		</tr>
		<tr width='50%'>
			<td width='18%' align='left' style='border-bottom:1px solid #000;'>
				FORM
			</td>
			<td width='32%' align='left' style='border-bottom:1px solid #000;'>
				:&nbsp;${}
			</td>
		</tr>
		<tr width='50%'>
			<td width='18%' align='left' style='border-bottom:1px solid #000;'>
				TO
			</td>
			<td width='32%' align='left' style='border-bottom:1px solid #000;'>
				:&nbsp;${}
			</td>
		</tr>
	</table>
	<table width='100%'>
		<tr width='100%'>
			<td width='16%' align='center' style='border-right:1px solid #000;border-bottom:1px solid #000;border-left:1px solid #000;'>
				MARKS & NOS
			</td>
			<td width='44%' align='center' style='border-right:1px solid #000;border-bottom:1px solid #000;'>
				DESCRIPTION OF GOODS
			</td>
			<td width='15%' align='center' style='border-right:1px solid #000;border-bottom:1px solid #000;'>
				GROSS WEIGHT
			</td>
			<td width='15%' align='center' style='border-right:1px solid #000;border-bottom:1px solid #000;'>
				NET WEIGHT
			</td>
			<td width='10%' align='center' style='border-right:1px solid #000;border-bottom:1px solid #000;'>
				VOLUME CBM
			</td>
		</tr>
	%for line in o.goods_lines:
		<tr width='100%'>
			<td width='16%' align='left' style='border-right:1px solid #000;border-left:1px solid #000;'>&nbsp;
			</td>
			<td width='44%' align='left' style='border-right:1px solid #000;'>		${line.product_desc or ''}
			</td>
			<td width='15%' align='right' style='border-right:1px solid #000;'>
				${line.gross_weight or ''}
			</td>
			<td width='15%' align='right' style='border-right:1px solid #000;'>
				${line.net_weight or ''}
			</td>
			<td width='10%' align='right' style='border-right:1px solid #000;'>
				a
			</td>
		</tr>
	%endfor
		<tr width='100%'>
			<td width='16%' style='border-left:1px solid #000;border-top:1px solid #000;border-right:1px solid #000;border-bottom:1px solid #000;'>&nbsp;
			</td>
			<td width='44%' align='center' style='border-top:1px solid #000;border-right:1px solid #000;border-bottom:1px solid #000;'>
				TOTAL : 
			</td>
			<td width='15%' align='right' style='border-top:1px solid #000;border-right:1px solid #000;border-bottom:1px solid #000;'>a
			</td>
			<td width='15%' align='right' style='border-top:1px solid #000;border-right:1px solid #000;border-bottom:1px solid #000;'>a
			</td>
			<td width='10%' align='right' style='border-top:1px solid #000;border-right:1px solid #000;border-bottom:1px solid #000;'>a
			</td>
		</tr>
	</table>
	<table width='70%'>
		<tr width='100%'>
			<td width='50%'>&nbsp;
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='center' style='border-bottom:1px solid #000;'>
				PALLET
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='center' style='border-bottom:1px solid #000;'>
				CARTON
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				NET WEIGHT PER CONE
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				GROSS WEIGHT PER CONE
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				NO. OF CONES PER CARTON
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				NET WEIGHT PER PALLET/CARTON
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				GROSS WEIGHT PER PALLET/CARTON
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
		<tr width='100%'>
			<td width='50%'>
				TOTAL PALLET/CARTONS
			</td>
			<td width='5%' align='left'>
				:
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
			<td width='5%'>&nbsp;
			</td>
			<td width='20%' align='right'>
				3333&nbsp;KGS
			</td>
		</tr>
	</table>
	<hr>
	<table width='100%'>
		<tr width='100%' align='left' valign='top'>
			<td width='70%'>
				NOTE : </br>
					%if not o.note:
						
					%else:
						${o.note.replace('\n','<br/>')}
					%endif 
			</td>
			<td width='30%' align='center' valign='bottom' height='100'>
				<a class='ttd'>Authorized Signatory</a>
			</td>
		</tr>
	</table>
%endfor
</body>
</html>	