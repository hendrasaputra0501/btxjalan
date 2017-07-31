<html>
<head>
	<style>
		.head1{ font-family: "Times New Roman";
				font-size:25px;
				font-weight:bold;
				width:100%;
				text-align: center;
				border:1px solid;
				border-bottom: 0px;
				height:60px;
		}
		.div1{
				width:100%;
				border:1px solid;
				border-top: 0px;
		}
		.div1 tr td{
					font-family: "Times New Roman";
					font-size:18px;
		}
		#lbl{
				width:20%;
				font-weight: bold;
				padding-left: 10px;
				height: 28px;
		}
		#lbl1{
				width:20%;
				font-weight: bold;
				padding-left: 10px;
		}
		#txt{
				width:29%;
				padding-left: 10px;
		}
		#headtbl{font-weight: bold;
				text-align: center;

		}
		#txttbl{
				padding:2px 0 2px 5px;
		}
		/*h2 {page-break-before: always;}*/
		
	</style>

</head>
%for o in objects:
<body>
<div class="head1">PACKING LIST</div>
<div class="div1">
<table id="table1"  width="98%" rules="rows" align="center">
	<tr>
		<td id="lbl">CONTRACT NO.</td><td>:</td><td id="txt">${o.picking_ids[0] and o.picking_ids[0].sale_id and o.picking_ids[0].sale_id.name or ''}</td><td id="lbl1">STUFFING DATE</td><td>:</td><td id="txt">isi Stuffdate</>
	</tr>
	<tr>
		<td id="lbl">CUSTOMER</td><td>:</td><td id="txt">${o.consignee.name or ''}</td><td id="lbl1">CONTAINER NO.</td><td>:</td><td id="txt">isi container no</>
	</tr>
	<tr>
		<td id="lbl">PRODUCT</td><td>:</td><td id="txt">${o.goods_lines[0] and o.goods_lines[0].product_id and o.goods_lines[0].product_id.name or ''}</td><td id="lbl1">CONDITION</td><td>:</td><td id="txt">isi condition 1</>
	</tr>
	<tr>
		<td id="lbl">LOT NO.</td><td>:</td><td id="txt">isi LOT</td><td id="lbl1"></td><td>:</td><td id="txt">isi condition 2</>
	</tr>
	<tr>
		<td id="lbl">INVOICE NO.</td><td>:</td><td id="txt">isi inv</td><td id="lbl1">STRIPPING COLOUR</td><td>:</td><td id="txt">isi STRIP</>
	</tr>
	<tr>
		<td id="lbl">TOTAL PALET</td><td>:</td><td id="txt">isi tot Plt</td><td id="lbl1">NW/PALLET</td><td>:</td><td id="txt">isi nwpalet</>
	</tr>
	<tr>
		<td id="lbl"></td><td></td><td></td><td id="lbl1">CONDITION PLT</td><td>:</td><td id="txt">isi condition</>
	</tr>
	<tr>
		<td id="lbl"></td><td></td><td></td><td id="lbl1">CHECKED BY</td><td>:</td><td id="txt">isi Chkek</>
	</tr>
</table>
</br>
</div>
<table class="div1" rules="all" > 
<tr>
	<td id="headtbl" width="5%">SN</td><td id="headtbl" width="25%">PALLET NO.</td><td id="headtbl" width="30%">ISPM 15 NO.</td><td id="headtbl" width="40%"></td>
</tr>
<tr>
	<td id="txttbl">1</td><td id="txttbl">isi Palet</td><td id="txttbl">isi ISPM 15 NO.</td><td id="txttbl"></td>
</tr>
</table>
<br/>
<br/>
<br/>
<br/>
<br/>
<div><table width="100%">
	<tr>
		<td width="35%" style="padding-left:20px;">PREPARED BY</td><td align="center" width="30%">GODOWN KEEPER</td><td align="right" style="padding-right:20px;" width="35%">MARKETING</td>
	</tr>
</table></div>
</body>
%endfor
</html>