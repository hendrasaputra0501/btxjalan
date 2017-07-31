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
	% if (o.picking_ids and o.picking_ids[0].sale_type=="export") or (o.invoice_ids and o.invoice_ids[0].sale_type=='export'):
	<div id="wrapper">
	%else :
	PILIH LAND IN TRANSIT REPORT ATAU SALE TYPE BLANK..HARUS DIISI!!
	<div id="wrapper" style="display:none;">
	%endif
		<div id="title1">
			<span>PT BITRATEX INDUSTRIES</span></br>
			<span>REKAPITULASI LAND IN TRANSIT</span></br>
			<span>SHIPMENT TYPE :  EXPORT</span></br>
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
					<td id="jdltbl" style="padding-left:7px;" width="12%">Container No</td>
					<td id="jdltbl" width="12%">Kota</td>
					<td id="jdltbl" width="12%">Negara</td>
				</tr>
				<tr >
					<td ></td>
					<td ></td>
					<td ></td>
					<td ></td>
					<td id="jdltblknn" >Kgs.</td>
					<td id="jdltblknn" >(${o.currency_id and o.currency_id.name or ''})</td>
					<td id="jdltblknn" >(${o.currency_id and o.currency_id.name or ''})</td>
					<td id="jdltbl" style="padding-left:7px;"></td>
					<td id="jdltbl" >Tujuan</td>
					<td id="jdltbl"></td>
				</tr>
				<tr>
					<td class="grstotal" colspan="10"></td>	
				</tr>
				</thead>
				<%
				picking_obj_ids = []
				if o.invoice_ids:
					for inv in o.invoice_ids:
						if inv.picking_ids:
							for picking in inv.picking_ids:
								if picking.state=='done':
									picking_obj_ids.append(picking)

				totqty,price_total,tot_ins=0.0,0.0,0.0
				%>
				<%sn=0%>
				%for baris in sorted(get_list_transaction(o,picking_obj_ids), key=lambda x:(x[0],x[1])):
				<%
					sn+=1
					totqty+=baris[2]
					price_total+=baris[3]
					tot_ins+=baris[4]
				%>
				<tr>
					<td>${sn}</td>
					<td>${baris[8] and '<br/>'.join(baris[8]) or ''}</td>
					<td>${formatLang(baris[0], date=True) or ''}</td>
					<td>${baris[1] or ''}</td>
					<td id="isitblknn">${formatLang(baris[2],digits=4) or 0}</td>
					<td id="isitblknn">${formatLang(baris[3],digits=2) or 0}</td>
					<td id="isitblknn">${formatLang(baris[4],digits=2) or 0}</td>
					<td style="padding-left:7px;">${baris[5] and '<br/>'.join(baris[5]) or ''}</td>
					<td>${baris[6] or ''}</td>
					<td>${baris[7] or ''}</td>
				</tr>
				%endfor
				<tr>
					<td></td>
					<td></td>
					<td></td>
					<td></td>
					<td class="grstotal" colspan="3"></td>
					<td></td>
					<td></td>
				</tr>

				<tr>
					<td></td>
					<td></td>
					<td></td>
					<td style="text-transform:capitalize;font-weight:bold;text-align:right;padding-right:10px;">Total :</td>
					<td id="isitblknn">${formatLang(totqty,digits=4) or 0}</td>
					<td id="isitblknn">${formatLang(price_total,digits=2) or 0}</td>
					<td id="isitblknn">${formatLang(tot_ins,digits=2) or 0}</td>
					<td></td>
					<td></td>
				</tr>
				<tr>
					<td class="grstotal" colspan="9"></td>	
				</tr>

			</table>

		</div>

	</div>
</body>
%endfor
</html>	

