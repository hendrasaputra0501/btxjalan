<html>
<head>
	
	<style type="text/css">
		
		#title1 {
				font-family: Arial;
				font-size: 13px;
				font-weight: bold;
				text-transform: uppercase;
				text-align: center;
				padding-top:0px;
		}
		.fontall{	
				font-family: Arial;
				font-size:10px;
		}
		
		.border1 {
				border:0px solid;
				margin:0 0px 0 0px;
				/*width:1300px;*/
		}
		#jdltbl{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
		}
		#jdltbl2{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				padding-left: 7px;
		}
		#isitblknn{
				text-align: right;
		}
		td {
		vertical-align:top;
		}
		#bwhtbl{text-transform: uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}
		#sumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
		}
		#bwhsumtbl{text-transform:uppercase;
				font-family: "Arial";
				font-size:10px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		#lbl{
			font-family: "Arial";
			font-size:10px;
			font-weight: bold;
			padding:0px 10px 0px 20px;
			vertical-align: top;
			text-transform:uppercase;
		}
		#lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		#tdtxt{
			font-size:11px;
			padding:0px 20px 0px 10px;
		}
		#borderwhite{
			border-top:white;
			border-left:white;
		}
		#borderwhite_rgt{
			border-right:white;
			padding-left: 3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		#borderwhite_rgtbtm{
			border-right:white;
			border-bottom:white;
			padding-left: 3px;	
		}
		#borderwhite_btm{
			border-bottom:white;
			padding-right:3px;
		}
		#lblrght{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		#lbl2{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			text-align: center;
		}
		#borderwhite_rgt2{
			border-right:white;
			text-align: center;
			font-weight:bold;
			text-transform: uppercase;
		}
		#borderwhite_btm2{
			border-bottom:white;
			text-align: center;
			font-weight:bold;
		}
		#borderwhite_rgtbtm2{
			border-right:white;
			border-bottom:white;
			text-align: center;
		}
		#grsbwhtbl{
			border-bottom: 1px solid #808080;
		}
		#jdltblknn{
				text-transform: uppercase;
				text-align: right;
				font-family: Arial;
				font-weight: bold;
		}
		#jdltblpd7{
				text-transform: uppercase;
				padding-left:7px;
				font-family: Arial;
				font-weight: bold;

		}
		#isitblpd7{
				padding-left: 7px;
		}
		.hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
}
		.grstotal{
			border-top: 1px solid #808080;
		}

.top-margin{
	padding-top:5px;
}

			/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        font-size:10px;
        }
        #wrapper {
        min-height:100%;
        position:static;
        font-family: Arial;
		font-size:10px;
        }
        #header {
        padding:10px;
        background:#5ee;
        }
        #content {
	padding-bottom:10px;padding-top: 10px; /* Height of the footer element */
		}
#footer {
	/*background:blue;*/
	width:100%;
	height:210px;
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
     
        .bank{
        		list-style-type: none;
        		text-decoration: none;
        		vertical-align: bottom;
        }
.btsprg{

			    width:22em; 
			    /*border: 1px solid #000000;*/
			    word-wrap: break-word;
			    vertical-align:top;
			    margin-top:5px;
        }
        table {
        	border-collapse: collapse;
        }
   
		/*h2 {page-break-before: always;}*/


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
		# y = datetime.strptime(x1,'%Y-%m-%d').strftime("%Y-%m-%d")
		y = datetime.strptime(x1,'%Y-%m-%d').strftime("%d %b %Y")
	except:
		y = x1
	return y
%>
% for o in objects:

<body>
	% if (o.picking_ids and o.picking_ids[0].sale_type=="local") or (o.invoice_ids and o.invoice_ids[0].sale_type=='local') or (o.picking_ids and o.picking_ids[0].purchase_type=="local"):
	<div id="wrapper">
	%else:
	PILIH LAND IN TRANSIT EXPORT REPORT ATAU SALE/PURCHASE TYPE BLANK..HARUS DIISI!!
	<div id="wrapper" style="display:none;">
	%endif
	
		<div id="title1">
			<span>PT BITRATEX INDUSTRIES</span></br>
			<span>REKAPITULASI LAND IN TRANSIT</span></br>
			<span>SHIPMENT TYPE :  ${o.type=='sale' and 'LOCAL' or 'LOCAL'}</span></br>
			<span>Period :  ${o.period_id and o.period_id.name or ''}</span></br>
		</div>
		<div id="content">
			<table width="100%">
				<thead>
				<tr>
					<td id="jdltbl" width="4%">No.</td>
					<td id="jdltbl" width="10%">Invoice</td>
					<td id="jdltbl" width="8%">Tgl.Kirim</td>
					<td id="jdltbl" width="20%">
					%if o.type=="sale":
						Dikirim kepada
					%else:
						Supplier
					%endif
					</td>
					<td id="jdltblknn" width="10%">Qty Kgs.</td>
					<td id="jdltblknn"  width="10%">Total Value</td>
					<td id="jdltblknn"  width="10%">Sum Insured</td>
					<td id="jdltbl" style="padding-left:7px;" width="8%">Truck No</td>
					<td id="jdltbl" width="24%">Kota</td>
				</tr>
				<tr >
					<td ></td>
					<td ></td>
					<td ></td>
					<td ></td>
					<td id="jdltblknn" >Kgs.</td>
					<td id="jdltblknn" > &nbsp; </td>
					<td id="jdltblknn" > &nbsp; </td>
					<td id="jdltbl" style="padding-left:7px;"></td>
					<td id="jdltbl" >Tujuan</td>
				</tr>
				<tr>
					<td class="grstotal" colspan="9"></td>	
				</tr>
				</thead>
				<%
				picking_obj_ids = []
				if o.type=='sale':
					if o.invoice_ids:
						for inv in o.invoice_ids:
							if inv.picking_ids:
								for picking in inv.picking_ids:
									if picking.state=='done':
										picking_obj_ids.append(picking)
				else:
					picking_obj_ids=[x for x in o.picking_ids]
				sn=0
				summary_total = {} 
				grand_total_qty, grand_total_value, grand_total_sum = 0.0, 0.0, 0.0
				%>
				<% 
				print ":::::::::::::::::::::::::::::"
				%>
				%for baris in sorted(get_list_transaction(o,picking_obj_ids), key=lambda x:(x[0],x[1])):
				<%
					sn+=1
					if baris[11] not in summary_total:
						summary_total.update({baris[11]:{
							'total_qty' : 0.0,
							'total_value' : 0.0,
							'total_sum_insured' : 0.0,
							'total_value_ins' : 0.0,
							'total_sum_insured_ins' : 0.0,
							'rate' : baris[10],
							}})
					summary_total[baris[11]]['total_qty']+=baris[2]
					summary_total[baris[11]]['total_value']+=baris[8]
					summary_total[baris[11]]['total_sum_insured']+=baris[9]
					summary_total[baris[11]]['total_value_ins']+=baris[3]
					summary_total[baris[11]]['total_sum_insured_ins']+=baris[4]
				%>
				<tr>
					<td>${sn}</td>
					<td >${baris[7] and '<br/>'.join(baris[7]) or ''}</td>
					<td>${formatLang(baris[0], date=True) or ''}</td>
					<td>${baris[1] or ''}</td>
					<td id="isitblknn">${formatLang(baris[2],digits=4) or 0}</td>
					<td id="isitblknn">${formatLang(baris[8],digits=2) or 0}</td>
					<td id="isitblknn">${formatLang(baris[9],digits=2) or 0}</td>
					<td style="padding-left:7px;">${baris[5] or ''}</td>
					<td>${baris[6] or ''}</td>
				</tr>
				%endfor
				% for k in summary_total.keys():
					<tr>
						<td></td>
						<td></td>
						<td></td>
						<td style="border-top:1px solid #808080; text-transform:capitalize;font-weight:bold;text-align:right;padding-right:10px;">Total ${k and k.name or ''} : </td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(summary_total[k]['total_qty'],digits=4) or 0}</td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(summary_total[k]['total_value'],digits=2) or 0}</td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(summary_total[k]['total_sum_insured'],digits=2) or 0}</td>
						<td></td>
						<td></td>
					</tr>
					% if k and o.currency_id and k.id!=o.currency_id.id:
					<tr>
						<td></td>
						<td></td>
						<td></td>
						<td style="border-top:1px solid #808080;text-transform:capitalize;text-align:right;padding-right:10px;">Rate ${k and o.currency_id and o.currency_id.name+' to '+k.name or ''}:</td>
						<td style="border-top:1px solid #808080;" id="isitblknn"></td>
						<td style="border-top:1px solid #808080;" id="isitblknn">${formatLang(summary_total[k]['rate'],digits=2) or 0}</td>
						<td style="border-top:1px solid #808080;" id="isitblknn">${formatLang(summary_total[k]['rate'],digits=2) or 0}</td>
						<td></td>
						<td></td>
					</tr>
					<tr class>
						<td></td>
						<td></td>
						<td></td>
						<td style="border-top:1px solid #808080;text-transform:capitalize;font-weight:bold;text-align:right;padding-right:10px;">Total ${k and o.currency_id and o.currency_id.name+' of Total '+k.name or ''} :</td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn"></td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(summary_total[k]['total_value_ins'],digits=2) or 0}</td>
						<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(summary_total[k]['total_sum_insured_ins'],digits=2) or 0}</td>
						<td></td>
						<td></td>
					</tr>
					% endif
					<%
					grand_total_qty+=summary_total[k]['total_qty']
					grand_total_value+=summary_total[k]['total_value_ins']
					grand_total_sum+=summary_total[k]['total_sum_insured_ins']
					%>
				% endfor
				<tr class>
					<td></td>
					<td></td>
					<td></td>
					<td style="border-top:1px solid #808080;text-transform:capitalize;font-weight:bold;text-align:right;padding-right:10px;">Grand Total ${o.currency_id and o.currency_id.name or ''} :</td>
					<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(grand_total_qty,digits=4) or 0}</td>
					<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(grand_total_value,digits=2) or 0}</td>
					<td style="border-top:1px solid #808080;font-weight:bold;" id="isitblknn">${formatLang(grand_total_sum,digits=2) or 0}</td>
					<td></td>
					<td></td>
				</tr>
				<tr>
					<td class="grstotal" colspan="8"></td>	
				</tr>
			</table>
		</div>
	</div>
</body>
%endfor
</html>	

