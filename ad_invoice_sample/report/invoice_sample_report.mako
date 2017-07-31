<html>
<head>
<style type="text/css">
    body{
        font-family:Verdana;
        /*font-family:fontenc;*/
        font-size: 10pt;
    }
    
    td.title{
        font-weight: bold;
        font-size: 15px;
        text-align: center;
    }

     td.title_right{
        /*font-weight: bold;*/
        font-size: 10px;
        text-align: right;
    }

    table
    {
        border-collapse: collapse;
        width: 100%;
    }

    tr.tr-title {
        border-bottom: 1px solid;
        /*border-bottom: 1px solid;*/
    }

    tr.tr-title_ {
        /*border-top: 1px solid;*/
        border-bottom: 1px solid;
    }

    td.td-title {
        text-align: center;
        font-weight: bold;
    }
    td.td-title_border_btm{
        text-align: center;
        font-weight: bold;
        border-bottom:solid #808080 1pt;
        /*border-left:solid 5px white;*/
    }
    td.td-title_left {
        text-align: left;
        /*font-weight: bold;*/
    }

    td.td-title_left_bold {
        text-align: left;
        font-weight: bold;
    }
    td.td-title_center {
        text-align: center;
        font-weight: bold;
    }

    td.td-loc_title {
        font-weight: bold;
        text-decoration: underline;
    }

    tr.tr-subtotal {
        border-top: 1px dashed;
    }

    td.td-subtotal-label {
        text-align: left;
        font-weight: bold;
    }
    
    td.td-subtotal-amount {
        text-align: right;
        font-weight: bold;
    }

    tr.tr-grandtotal {
        border-top: 1px solid;
    }

    td.td-grandtotal {
        font-weight: bold;
    }

    td.td-details {
        vertical-align: top;
    }

    td.td-details-right {
        text-align: right;
        vertical-align: top;
    }

    </style>



</head>
<body>
<%
	from datetime import datetime
	def xdate(x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%b %d, %Y')
		except:
			y = x1
		return y
%>
% for o in objects:
    <%
        terbilang=call_num2word(o.amount_total,"en")
    %>
	<table width='100%'>
	<tr>
		<td colspan="3" class="title">INVOICE cum PACKING LIST</td>
	</tr>
	<tr>
		<td colspan="3" class="title">${o.name}</td>
	</tr>
	<tr>
		<td colspan="3" class="title_right">DATE &nbsp; &nbsp; : ${xdate(o.date_invoice)}</td>
	</tr>
    <tr>
        <td colspan="3">&nbsp;</td>
    </tr>
    <tr>
        <td colspan="3">&nbsp;</td>
    </tr>
    <!-- <tr>
        <td colspan="3">&nbsp;</td>
    </tr> -->
    <tr>
        <td class="td-title_left" width='30%'>SHIPPER</td><td class="td-title_left" width='2%'>:</td><td class="td-title_left_bold" width='68%' >${o.shipper_id.name}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">${o.shipper_id.street}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">${o.shipper_id.city}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">Telp : ${o.shipper_id.phone}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">Fax : ${o.shipper_id.fax}</td>
    </tr>
    <tr>
        <td cols="3">&nbsp;
        </td>
    </tr>

    <tr>
        <td class="td-title_left" width='30%'>CONSIGNEE</td><td class="td-title_left" width='5%'>:</td><td class="td-title_left_bold" width='65%' >${o.consignee_partner_id.name}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">${o.consignee_partner_id.street}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">${o.consignee_partner_id.street2}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">${o.consignee_partner_id.street3}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">Telp : ${o.consignee_partner_id.phone or ''}</td>
    </tr>
    <tr>
        <td class="td-title_left"></td><td class="td-title_left"></td><td class="td-title_left">Fax : ${o.consignee_partner_id.fax or ''}</td>
    </tr>
    <tr>
        <td cols="3">&nbsp;
        </td>
    </tr>

    <tr>
        <td class="td-title_left" style="vertical-align:top;" >DESCRIPTION OF GOODS</td><td class="td-title_left" style="vertical-align:top;" >:</td>
        <td class="td-title_left" >
        % for x in o.invoice_line:
            ${x.name} </br>
        %endfor
        </td>
    </tr>
    <tr>
        <td cols="3">&nbsp;
        </td>
    </tr>
     <tr>
        <td class="td-title_left" style="vertical-align:top;">VALUE</td><td class="td-title_left" style="vertical-align:top;" >:</td>
        <td class="td-title_left" >
        ${o.currency_id.name} &nbsp; ${o.amount_total}  / &nbsp; ( ${o.currency_id.name} ${terbilang} )
        </td>
    </tr>
     <tr>
        <td class="td-title_left" style="vertical-align:top;"></td><td class="td-title_left" style="vertical-align:top;" ></td>
        <td class="td-title_left_bold" style="font-size:8pt;">
        ( Free Sample for Testing Purpose Only - No Commercial Value )
        </td>
    </tr>
    <tr>
        <td class="td-title_left" style="vertical-align:top;">QUANTITY</td><td class="td-title_left" style="vertical-align:top;" >:</td>
        <td class="td-title_left" >
        <% 
        tot_uop=0
        for x in o.invoice_line:
            packing=x.move_id.product_uop.packing_type.name
            tot_uop+=x.move_id.product_uop_qty
        %>
        ${formatLang(tot_uop,digits=0)} &nbsp; ${packing}
        <%   
        endfor
        %>
        </td>
    </tr>
    <%
    tot_gw=0
    tot_nw=0
    %>
    %for x in o.invoice_line:
    <%        
            packing=x.move_id.product_uop.packing_type.name
            uop=x.move_id.product_uop_qty
            gw=x.move_id.gross_weight
            nw=x.move_id.net_weight
            uom=x.move_id.product_uom.name
            tot_gw+=gw
            tot_nw+=nw
    %>
    <tr>
        <td class="td-title_left" style="vertical-align:top;">

            ${x.name} 
        </td>

            <td class="td-title_left" style="vertical-align:top;" >:</td>
        <td class="td-title_left" >

            <table width="100%">
                    <tr>
                        <td width="30%">${formatLang(uop,digits=0)} &nbsp; ${packing}</td>
                        <td width="35%">GW =&nbsp; ${formatLang(gw,digits=2)} &nbsp;${uom} ,</td>
                        <td width="35%"> NW = &nbsp; ${formatLang(nw,digits=2)} &nbsp; ${uom}</td>
                        
                    </tr>
            </table>
           <!-- ${formatLang(uop,digits=0)} &nbsp; ${packing} &nbsp; GW &nbsp;= &nbsp; ${formatLang(gw,digits=2)} &nbsp; ${uom} &nbsp; , &nbsp; NW &nbsp; = &nbsp; ${formatLang(nw,digits=2)} &nbsp; ${uom} -->
        
        </td>
    </tr>
    
    %endfor
    
    <tr>
        <td class="td-title_left" style="vertical-align:top;">
        </td>

        <td class="td-title_left" style="vertical-align:top;border-top:1px solid black;" ></td>
        <td class="td-title_left" style="border-top:1px solid black;">
            <table width="100%">
                    <tr>
                        <td width="30%">Total</td>
                        <td width="35%">GW =&nbsp; ${formatLang(tot_gw,digits=2)} &nbsp;${uom} ,</td>
                        <td width="35%"> NW = &nbsp; ${formatLang(tot_nw,digits=2)} &nbsp; ${uom}</td>
                    </tr>
            </table>
          <!--  Total &nbsp; GW &nbsp;= &nbsp; ${formatLang(tot_gw,digits=2)} &nbsp; ${uom} &nbsp; , &nbsp; NW &nbsp; = &nbsp; ${formatLang(tot_nw,digits=2)} &nbsp; ${uom} -->
        
        </td>
    </tr>
    <tr>
        <td class="td-title_left" style="vertical-align:top;">
           &nbsp;
        </td>
        <td class="td-title_left" style="vertical-align:top;" >
        &nbsp;
        </td>
        <td class="td-title_left" >
        &nbsp;
        </td>
    </tr>
    <tr>
        <td class="td-title_left" style="vertical-align:top;">
        </td>
            <td class="td-title_left" style="vertical-align:top;" ></td>
        <td class="td-title_left" >
             <table width="100%">
                    <tr>
                        <td width="50%">Grand Total Gross Weight</td>
                        <td width="5%">:</td>
                        <td width="45%">${formatLang(tot_gw,digits=2)} &nbsp; ${uom}</td>
                    </tr>
                    <tr>
                        <td >Grand Total Net Weight</td>
                        <td >:</td>
                        <td >${formatLang(tot_nw,digits=2)} &nbsp; ${uom}</td>
                    </tr>
            </table>
        
        </td>
    </tr>
    <tr>
        <td class="td-title_left" style="vertical-align:top;padding-top:10px;">
            DISPATCH THROUGH
        </td>
            <td class="td-title_left" style="vertical-align:top;" >:</td>
        <td class="td-title_left" >
           By  &nbsp; ${o.trucking_company.partner_id and o.trucking_company.partner_id.name or ''} 
        
        </td>
    </tr>
    <tr>
        <td class="td-title_left" style="vertical-align:top;">
        </td>
            <td class="td-title_left" style="vertical-align:top;" ></td>
        <td class="td-title_left" >
           Dated &nbsp;: &nbsp; ${xdate(o.date_invoice)}
        
        </td>
    </tr>
    <tr>
            <td class="td-title_left" style="vertical-align:top;padding-top:80px;" cols="3">for PT Bitratex Industries</td>
    </tr>
  
    <tr>
            <td class="td-title_left" style="vertical-align:top;padding-top:80px;" cols="3">( Authorised Signatory )</td>
    </tr>
	</table>
% endfor
</body>
</html>