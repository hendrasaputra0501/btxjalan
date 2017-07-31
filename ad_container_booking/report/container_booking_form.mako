<html>
<head>
	<style>
	.title{
		border-bottom: 3px double #000;
	}
	.ttd{
		border-top: 1px dashed #000;
	}
	.tdbutdob{
		border-width: 0px 0px 3px 0px;
		border-style: none none double none;
		border-color: #000;
	}
	.tdleft{
		border-width: 0px 2px 1px 0px;
		border-style: none dashed dashed none;
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
	<center><h2><a class='title'>CONTAINER BOOKING</a></h2></center>
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
			<td class='tdleft' width='50%' align='left' valign='top'>
				SHIPPER &nbsp;&nbsp;&nbsp; : <br/><br/>
				${(o.shipper.name or '').replace('\n','</br>')} <br/>
				${o.shipper.street or ''} </br/>
				${o.shipper.street2 or ''} <br/>
				${o.shipper.city or ''} &nbsp; ${o.shipper.zip or ''} , &nbsp;${o.shipper.country_id.name or ''}
			</td>
			<td class='tdupbut' width='50%' colspan='2' align='left' valign='top'>
				TO &nbsp;&nbsp;&nbsp; : <br/><br/>
			</td>
		</tr>
		<tr width='100%'>
			<td class='tdleft' width='50%' rowspan='3' align='left' valign='top'>
				CONSIGNEE &nbsp;&nbsp;&nbsp; : 
			</td>
			<td class='tdupbut' width='18%' align='left'>
				STUFFING DATE
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.stuffing_date}
			</td>
		</tr>
		<tr width='50%'>
			<td class='tdupbut' width='18%' align='left'>
				FEEDER VESSEL
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.feeder_vessel or ''}
			</td>
		</tr>
		<tr width='50%'>
			<td class='tdupbut' width='18%' align='left'>
				CONNECT VESSEL
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.connect_vessel or ''}
			</td>
		</tr>
		<tr width='100%'>
			<td class='tdleft' width='50%' rowspan='4' align='left' valign='top'>
				NOTIFY PARTY &nbsp;&nbsp;&nbsp; : 
			</td>
			<td class='tdupbut' width='18%' align='left'>
				FROM
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.port_from.name or ''}
			</td>
		</tr>
		<tr width='50%'>
			<td class='tdupbut' width='18%' align='left'>
				TO
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.port_to.name or ''}
			</td>
		</tr>
		<tr width='50%'>
			<td class='tdupbut' width='18%' align='left'>
				FREIGHT
			</td>
			<td class='tdupbut' documentation='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.freight or ''}
			</td>
		</tr>
		<tr width='50%'>
			<td class='tdupbut' width='18%' align='left'>
				DOCUMENTATION
			</td>
			<td class='tdupbut' width='32%' align='left'>
				: &nbsp;&nbsp;&nbsp;${o.documentation or ''}
			</td>
		</tr>
	</table>
	<table width='100%'>
		<tr width='100%'>
			<td rowspan='2' width='16%' align='center' style='border-right:2px dashed #000;border-bottom:1px dashed #000;'>
				MARKS & NOS
			</td>
			<td rowspan='2' width='44%' align='center' style='border-right:2px dashed #000;border-bottom:1px dashed #000;'>
				DESCRIPTION OF GOODS
			</td>
			<td colspan='2' width='30%' align='center' style='border-bottom:1px dashed #000;'>
				QUANTITY IN KGS
			</td>
			<td rowspan='2' width='10%' align='center' style='border-left:2px dashed #000;border-bottom:1px dashed #000;'>
				VOLUME CBM
			</td>
		</tr>
		<tr>
			<td width='15%' align='center' style='border-bottom:1px dashed #000;'>
				GROSS WEIGHT
			</td>
			<td width='15%' align='center' style='border-left:2px dashed #000;border-bottom:1px dashed #000;'>
				NET WEIGHT
			</td>
		</tr>
	%for line in o.goods_lines:
		<tr width='100%'>
			<td width='16%' align='left' style='border-right:2px dashed #000;'>&nbsp;
			</td>
			<td width='44%' align='left' style='border-right:2px dashed #000;'>		${line.product_desc or ''}
			</td>
			<td width='15%' align='right' style='border-right:2px dashed #000;'>
				${line.gross_weight or ''}
			</td>
			<td width='15%' align='right'>
				${line.net_weight or ''}
			</td>
			<td width='10%' align='right' style='border-left:2px dashed #000;'>
				
			</td>
		</tr>
	%endfor
		<tr width='100%'>
			<td width='16%' style='border-right:2px dashed #000;border-bottom:1px dashed #000;'>&nbsp;
			</td>
			<td width='44%' align='center' style='border-right:2px dashed #000;border-bottom:1px dashed #000;border-top:1px dashed #000;'>
				TOTAL : 
			</td>
			<td width='15%' align='right' style='border-right:2px dashed #000;border-bottom:1px dashed #000;border-top:1px dashed #000;'>a
			</td>
			<td width='15%' align='right' style='border-bottom:1px dashed #000;border-top:1px dashed #000;'>a
			</td>
			<td width='10%' align='right' style='border-left:2px dashed #000;border-bottom:1px dashed #000;border-top:1px dashed #000;'>a
			</td>
		</tr>
		<tr width='100%'>
			<td colspan='3' rowspan='2' align='left' valign='top'>
				<b>
					NOTE :
					%if not o.note:
						
					%else:
						${o.note.replace('\n','<br/>')}
					%endif 
				</b>
			</td>
			<td colspan='2' align='left'>
				&nbsp;
			</td>
		</tr>
		<tr>
			<td colspan='2' align='left'>
				<a class='ttd'>&nbsp;</a>
			</td>
		</tr>
	</table>
%endfor
</body>
</html>	