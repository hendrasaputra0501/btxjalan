<html>
<head>
	<style type='text/css'>
		.fontall{	
				font-family: Arial;
				font-size:11px;
		}
		
		.border1 {
				border:0px solid;
				margin:0 0px 0 0px;
				/*width:1300px;*/
		}
		.jdltbl{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
		}
		.jdltbl2{
				text-transform: uppercase;
				/*text-align: center;*/
				font-family: Arial;
				font-weight: bold;
				padding-left: 7px;
		}
		.isitbl{
				text-align: left;
		}
		.isitblknn{
				text-align: right;
		}
		td {
		vertical-align:top;
		}
		.bwhtbl{text-transform: uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				padding:5px 20px 5px 20px;
				border-bottom: 1pt solid #808080;
		}
		.sumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				text-align: right;
		}
		.sumtbltot{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				text-align: right;
				border-top: 1pt solid #808080;
		}
		.bwhsumtbl{text-transform:uppercase;
				font-family: 'Arial';
				font-size:11px;
				font-weight: bold;
				padding:0px 10px 0px 20px;
				border-bottom: 1pt solid #000000;
		}
		.lbl{
			font-family: 'Arial';
			font-size:11px;
			font-weight: bold;
			padding:0px 10px 0px 20px;
			vertical-align: top;
			text-transform:uppercase;
		}
		.lbl1{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
		}
		#lbl2{
		font-family:Arial;
		font-weight:bold;
		text-align: center;
		text-transform: uppercase;
		padding-left:5px;
}
		.tdtxt{
			font-size:11px;
			padding:0px 20px 0px 10px;
		}
		.borderwhite{
			border-top:white;
			border-left:white;
		}
		.borderwhite_rgt{
			border-right:white;
			padding-left: 3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.borderwhite_rgtbtm{
			border-right:white;
			border-bottom:white;
			padding-left: 3px;	
		}
		.borderwhite_btm{
			border-bottom:white;
			padding-right:3px;
		}
		.lblrght{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
		}
		.lblbtm{
			padding-right:3px;
			font-weight:bold;
			text-transform: uppercase;
			border-bottom: 1px solid #808080;
		}
		.lbl2{
			font-weight: bold;
			vertical-align: top;
			text-transform:uppercase;
			text-align: center;
		}
		.borderwhite_rgt2{
			border-right:white;
			text-align: center;
			font-weight:bold;
			text-transform: uppercase;
		}
		.borderwhite_btm2{
			border-bottom:white;
			text-align: center;
			font-weight:bold;
		}
		.borderwhite_rgtbtm2{
			border-right:white;
			border-bottom:white;
			text-align: center;
		}
		.grsbwhtbl{
			border-bottom: 1px solid #808080;
		}
		.jdltblknn{
				text-transform: uppercase;
				text-align: right;
				font-family: Arial;
				font-weight: bold;
		}
		.jdltblpd7{
				text-transform: uppercase;
				padding-left:7px;
				font-family: Arial;
				font-weight: bold;

		}
		.isitblpd7{
				padding-left: 7px;
		}
		.hdr1{
			font-family: Arial;
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
		}
		.font-capitalize{
		text-transform:capitalize;
		}
		#txt1{
		text-align: center;
		padding-left:5px;
}
#borderwhite{
		border-top:white;
		border-left:white;
}
	/*footer*/
html,
        body {
        margin:0;
        padding:0;
        height:100%;
        }
        .wrapper {
        min-height:100%;
        position:static;
        font-family: Arial;
		font-size:11px;
        }
        .header {
        padding:10px;
        background:#5ee;
        }
        .content {
        padding:10px;
        width:100%;
        padding-bottom:150px; /* Height of the footer element */ 
        /*background:green;*/
        /*height:910px;*/
        }
        .footer {
        width:100%;
        height:150px;
        position:absolute;
        bottom:0;
        left:0;
        /*background:#ee5;*/
        }
        
		h2 {
			text-align: center;
			font-weight: bold;
			font-size: 15px;
			text-transform: uppercase;
			page-break-before: always;
		}
	</style>
</head>
%for o in objects:
<body>
		
		<div class='wrapper'>
			<div class='content'>

				<table width="100%">
					<tr>
						<td colspan="3"><a class="lbl1">Date : </a>&nbsp; ${o.payment_date or ""} </td>
					</tr>
					<tr>
						<td width="30%" class="lbl1">Remit to</td><td width:"1%">:</td>
						<td width="69%">
							${o.remit_to.name or ""}</br>
							${o.remit_to.street or ""}</br>
							${o.remit_to.street2 or ""}</br>
							%if o.remit_to.zip:
								${o.remit_to.zip or ""}</br>
							%endif
							%if o.remit_to and o.remit_to.city:
								${o.remit_to.city or ""}</br>
							%endif
							%if o.remit_to and o.remit_to.state:
								${o.remit_to.state or ""}</br>
							%endif
							%if o.remit_to.country and o.remit_to.country.name:
								${o.remit_to.country.name or ""}</br>
							%endif
							SWIFT CODE : ${o.remit_to.bic} </br>
							ABA :
						</td>
					</tr>
					<tr>
						<td class="lbl1">For Credit to</td><td>:</td>
						<td>
							${o.credit_to.name or ""}</br>
							${o.credit_to.street or ""}</br>
							${o.credit_to.street2 or ""}</br>
							%if o.credit_to.zip:
								${o.credit_to.zip or ""}</br>
							%endif
							%if o.credit_to and o.credit_to.city:
								${o.credit_to.city or ""}</br>
							%endif
							%if o.credit_to and o.credit_to.state:
								${o.credit_to.state or ""}</br>
							%endif
							%if o.credit_to and o.credit_to.country and o.credit_to.country.name:
								${o.credit_to.country.name or ""}</br>
							%endif
							SWIFT CODE : ${o.credit_to.bic}
						</td>
					</tr>
					<tr>
						<td class="lbl1">For Further Credit to</td><td>:</td>
						<td>
							${o.bank_account_dest and o.bank_account_dest.partner_id and o.bank_account_dest.partner_id.name or ""} </br>
						</td>
					</tr>
					<tr>
						<td class="lbl1">Address</td><td>:</td>
						<td>
							%if o.bank_account_dest.street:
								${o.bank_account_dest.street or ""}</br>
							%endif
							
							%if o.bank_account_dest.zip:
								${o.bank_account_dest.zip or ""}</br>
							%endif
							%if o.bank_account_dest.city:
								${o.bank_account_dest.city or ""}</br>
							%endif
							%if o.bank_account_dest and o.bank_account_dest.country_id and o.bank_account_dest.country_id.name:
								${o.bank_account_dest and o.bank_account_dest.country_id and o.bank_account_dest.country_id.name or ""}</br>
							%endif

						</td>
					</tr>
					<tr>
						<td class="lbl1">Account No.</td><td>:</td>
						<td>
							${o.bank_account_dest.acc_number or ""}
						</td>
					</tr>
				</table>

			</div>
		</div>
</body>
%endfor:
</html>	
