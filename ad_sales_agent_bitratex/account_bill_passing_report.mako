<html>
<head>
    <style type="text/css">
    body{
        font-family:Verdana;
        /*font-family:fontenc;*/
        font-size: 6.5pt;
    }

    td.title{
        font-weight: bold;
        font-size: 10px;
        text-align: center;
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

    td.td-bottom {
        border-bottom: 1px solid;
        border-top: 1px solid;
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
<%
from datetime import datetime
def xdate(x):
    try:
        x1 = x[:10]
    except:
        x1 = ''

    try:
        y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%y')
    except:
        y = x1
    return y
%>
<body>

%for o in objects:


<table style="page-break-before:always;">
        <thead>
	        <tr>
	        	<td colspan="11" class="title">PT. BITRATEX INDUSTRIES</td>
	        </tr>
	        <tr>
	         	<td colspan="11" class="title">MATERIAL RECEIVING RECORDS</td>
	        </tr>

			<tr class="tr-title">
			    <td width="3%" class="td-title">SR No</td>
			    <td width="7%" class="td-title">Bill Date</td>
			    <td width="15%" class="td-title">Supplier Name</td>
			    <td width="15%" class="td-title">Item</td>
			    <td width="5%" class="td-title_left">UOM</td>
			    <td width="5%" class="td-title_left">Quantity</td>
			    <td width="5%" class="td-title" style="border-bottom:solid 1px ;">CURRY</td>
			    <td width="5%" class="td-title_left">Price</td>
			    <td width="5%" class="td-title_center" style="border-bottom:solid 1px ;">Amount</td>
			    <td width="10%" class="td-title">Dept</td>
			    <td width="10%" class="td-title">Remarks</td> 
			</tr>
        </thead>
        <tfoot>
          
        </tfoot>
        <tbody>
        	<%
        		sr=0
        	%>
        	%for lines in o.bill_lines:
	        	<%
	        		sr+=1
	        	%>
           	<tr>
                <td class="td-details">${sr}</td>
                <td class="td-details">${lines.bill_date or ''}</td>
                <td class="td-details">${lines.partner_id and lines.partner_id.name or ''}</td>
                <td class="td-details">${lines.desciption or ''}</td>
                <td class="td-details">${lines.product_uom or ''}</td>
                <td class="td-details">${lines.qty or ''}</td>
                <td class="td-details">CURRY</td>
                <td class="td-details">${lines.amount or ''}</td>
                <td class="td-details">Amount</td>
                <td class="td-details">Dept</td>
                <td class="td-details">${lines.remark or ''}</td> 
            </tr>
            %endfor
            <tr>
            	<td class="td-bottom">Total</td>
            	<td class="td-bottom" colspan='7'></td>
            	<td class="td-bottom">Amount</td>
            	<td class="td-bottom" colspan='2'></td>
            </tr>
            <tr>
            	<td>&nbsp;</td>
            	<td colspan='7'>&nbsp;</td>
            	<td >&nbsp;</td>
            	<td colspan='2'>&nbsp;</td>
            </tr>

            <tr>
            	<td class="td-details"colspan="3">CHEKED BY:</td>
            	<td class="td-details" colspan='4'>PASSED BY:</td>
            	<td class="td-details" colspan='3'>APPROVED BY:</td>
            	<td class="td-details" ></td>
            </tr>
        </tbody>
        
    </table>
%endfor
</body>
</html>