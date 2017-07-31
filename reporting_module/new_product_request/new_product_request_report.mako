<html>
<head>
	<style type="text/css">
/*a,
abbr,
acronym,
address,
applet,
article,
aside,
audio,
b,
big,
blockquote,
body,
canvas,
caption,
center,
cite,
code,
dd,
del,
details,
dfn,
dialog,
div,
dl,
dt,
em,
embed,
fieldset,
figcaption,
figure,
font,
footer,
form,
h1,
h2,
h3,
h4,
h5,
h6,
header,
hgroup,
hr,
html,
i,
iframe,
img,
ins,
kbd,
label,
legend,
li,
main,
mark,
menu,
meter,
nav,
object,
ol,
output,
p,
pre,
progress,
q,
rp,
rt,
ruby,
s,
samp,
section,
small,
span,
strike,
strong,
sub,
summary,
sup,
table,
tbody,
td,
tfoot,
th,
thead,
time,
tr,
tt,
u,
ul,
var,
video,
xmp {
  /*border: 0;*/
 /* margin: 0;
  padding: 0;
  font-size: 100%;
}*/

html,
body {
  height: 100%;
}

article,
aside,
details,
figcaption,
figure,
footer,
header,
hgroup,
main,
menu,
nav,
section {
/*
  Override the default (display: inline) for
  browsers that do not recognize HTML5 tags.

  IE8 (and lower) requires a shiv:
  http://ejohn.org/blog/html5-shiv
*/
  display: block;
}

b,
strong {
/*
  Makes browsers agree.
  IE + Opera = font-weight: bold.
  Gecko + WebKit = font-weight: bolder.
*/
  font-weight: bold;
}

img {
  color: transparent;
  font-size: 0;
  vertical-align: middle;
/*
  For IE.
  http://css-tricks.com/ie-fix-bicubic-scaling-for-images
*/
  -ms-interpolation-mode: bicubic;
}

ol,
ul {
  list-style: none;
}

li {
/*
  For IE6 + IE7:

  "display: list-item" keeps bullets from
  disappearing if hasLayout is triggered.
*/
  display: list-item;
}

table {
  border-collapse: collapse;
  border-spacing: 0;
}

th,
td,
caption {
  font-weight: normal;
  vertical-align: top;
  text-align: left;
}

q {
  quotes: none;
}

q:before,
q:after {
  content: "";
  content: none;
}

sub,
sup,
small {
  font-size: 75%;
}

sub,
sup {
  line-height: 0;
  position: relative;
  vertical-align: baseline;
}

sub {
  bottom: -0.25em;
}

sup {
  top: -0.5em;
}

svg {
/*
  For IE9. Without, occasionally draws shapes
  outside the boundaries of <svg> rectangle.
*/
  overflow: hidden;
}
/* end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset end of reset */

html,
	body {
		margin:0;
		padding:0;
		height:100%;
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
		padding:10px;
		width:100%;
		padding-bottom:50px; /* Height of the footer element */ 
		/*background:green;*/
		/*height:910px;*/
	}



	#title1 {
		font-family: Arial;
		font-size: 15px;
		font-weight: bold;
	}
	.fontall{	
		font-family: Arial;
		font-size:10px;
	}
	
	.border1 {
		/*border:0px solid;*/
		border:0px ;
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
		text-align: left;
	}
	#borderwhite_btm{
		border-bottom:white;
		padding-right:3px;
	}
	#lblrght{
		padding-right:3px;
		font-weight:bold;
		text-transform: uppercase;
		border-bottom:white;
		border-right:white;
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
	#hdr1{
		text-align: center;
		font-weight: bold;
		font-size: 15px;
	}
	#font-capitalize{
		text-transform:capitalize;
	}
	/*footer*/
	
	
	#footer {
		width:100%;
		height:50px;
		position:absolute;
		bottom:0;
		left:0;
		/*background:#ee5;*/
	}
	#bwhtblup1{
		/*font-weight:bold;*/
		text-align: left;
		/*text-transform: uppercase;*/
		/*border-top: 1px solid #808080;*/
		vertical-align:top;
	}
	#bwhtblup2{
		/*font-weight:bold;*/
		text-align: left;
		vertical-align:top;
		text-transform: uppercase;
		border-bottom:white;
	}
	#bwhtblup3{
		/*font-weight:bold;*/
		text-align: center;
		vertical-align:top;
		text-transform: uppercase;
		border-bottom:white;
	}
	.bottomonly{
		border-bottom: 0.5px solid grey;
	}
	.bottomonly:nth-last-child(1),.bottomonly:nth-last-child(2) {
    	border-bottom: none;
    	/*background-color: red*/
	}

	table{
		border-collapse: collapse;
		border-spacing: 0;
	}
	tr
	{
		page-break-inside:avoid;
		page-break-after:auto;
		page-break-before:auto;
	}
	</style>
</head>
<body>
<%
	import time
	from datetime import datetime
%>
% for o in objects:
<div  id="wrapper">
	<div id="hdr1">
		<a style="border-bottom:1px solid;">REQUISITION FOR NEW ITEM CODE</a> <br/>
	</div>
	<div id="content">
		<!-- ###############################Detail atas#################################################### -->
		<table width="100%" >
			<tr>
				<td width="35%" style="vertical-align:top;">
					<table id="borderwhite" width="80%"  style="margin-top:5px;">
						<tr>
							<td id="borderwhite_rgt" width="20%">From :</td><td id="borderwhite_rgtbtm" width="80%">${o.source_dept_id.name or ''}</td>
				    	</tr>
						<tr>
							<td id="borderwhite_rgt">To :</td> <td id="borderwhite_rgtbtm">${o.dest_dept_id.name or ''} </td>
						</tr>
					</table>
				</td>
				<td width="35%" style="vertical-align:top;"></td>
				<td width="30%">
					<table id="borderwhite"  width="100%"  rules="all">
						<tr>
							<td id="lblrght" width="35%" >Vendor's Name : </td>
							<td id="borderwhite_rgtbtm" width="65%">${o.partner_id.name or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
		<!-- ###############################Detail atas#################################################### -->
		<!-- ###############################Detail header#################################################### -->
		<table class='border1'  width='98%' cellspacing="0">
			<tr>
				<td id='jdltbl' width='2%'>SN.</td>
				<td id='jdltbl' style="padding-left:0;" width='15%'>Item Name</td>
				<td id='jdltbl' width='3%'>UOM</td>
				<td id='jdltbl' width='15%'>Catalogue No.</td>
				<td id='jdltbl' width='10%'>Part No.</td>
				<td id='jdltbl' width='10%'>Sugested Code</td>
				<td id='jdltbl' width='18%'>Itemcode By MMD</td>
				
			</tr>
			<%lines=1%>
		<!-- ###############################End Detail header#################################################### -->
			<tr>
				<td id='grsbwhtbl' width='98%'  colspan="7" height='5'></td>
			</tr>
		<!-- ###############################isi Detail#################################################### -->
		%for baris in o.requisition_lines:
		<tr>
			<td>${lines}</td>
			<td>${baris.name or''}</td>
			<td>${baris.product_uom.name or''}</td>
			<td>${baris.catalogue or''}</td>
			<td>${baris.part_number or ''}</td>
			<td>${baris.suggested_code or ''}</td>
			<td>${baris.default_code or ''}</td>
		</tr>
		<%lines+=1%>
		%endfor
		
		<!-- ###############################end isi Detail#################################################### -->	
			<tr>	
				<td id='grsbwhtbl' width='98%'  colspan="7" height='5'></td><!--  garis dibawah detail -->
			</tr>	
		</table>
		<!-- ###############################Summary#################################################### -->
		
	<!-- end of content -->

	<div id="footer">					
		<table width="100%" align="top">
			<tr>
				<td id="bwhtblup3" style="border-bottom:none;"  width="15%">
					<span >To be entered and circulated within 2 full working days</span>
				</td>
				<td width="5%" style="border-top:none;" width="40%">&nbsp;</td>
				<td id="bwhtblup2" width="10%">
					<span style='text-transform: capitalize;'>Requisition Departement</span>
				</td>
				<td width="5%" style="border-top:none;" width="10%">MMD</td>
				
			</tr>
			<tr>
				<td id="bwhtblup1">&nbsp;</td>
				<td style="border-top:none;">&nbsp;</td>
				<td id="bwhtblup1" >
					<span style='text-transform: capitalize;'>Date : ${o.date_entry or ''}</span>
					</td>
				<td style="border-top:none;">Date :</td>
			</tr>
			<tr style="page-break-after:always;">
				<td id="bwhtbl2" colspan="9" width="100%"></td>
			</tr>
		</table>					
	</div>
</div> <!-- end of wrapper -->
%endfor
</body>
</html>
