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
        border-top: 1px solid;
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




<table style="page-break-before:always;">
        <thead>
            <tr><td>&nbsp;</td><td>&nbsp;</td><td colspan="14" class="title">PT. BITRATEX INDUSTRIES</td><td>&nbsp;</td><td>&nbsp;</td></tr>
            <tr><td>PO Category:</td><td style="text-transform:capitalize;">${data['form']['purchase_type']}</td><td colspan="14"  class="title">PENDING PURCHASE ORDER</td><td>&nbsp;</td><td>&nbsp;</td></tr>
            <tr><td>Class:</td><td style="text-transform:capitalize;">${data['form']['goods_type']}</td><td colspan="14" class="title">Between ${formatLang(data['form']['date_start'],date=True)} and ${formatLang(data['form']['date_stop'],date=True)}</td><td>&nbsp;</td><td>&nbsp;</td></tr>

            <tr class="tr-title">
                <td  width="12%" colspan="2" class="td-title">PO</td>
                <!-- <td   class="td-title_left">Date</td> -->
                <td   width="13%" colspan="2" class="td-title">Vendor</td>
                <!-- <td   class="td-title_left">Name</td> -->
                <td   width="17%" colspan="2" width="2%" class="td-title">Inventory</td>
                <!-- <td   width="3%" class="td-title">Description</td> -->
                <td   width="3%" class="td-title">Item req.</td>
                <td   width="5%" class="td-title_left">Department</td>
                <td   width="3%" class="td-title_left"></td>
                <td   width="25%" colspan="5" class="td-title" style="border-bottom:solid 1px ;">Quantity</td>
                <!-- <td   width="5%" class="td-title_left"></td> -->
                <td   width="3%" class="td-title_left"></td>
                <td   width="10%" colspan="2" class="td-title_center" style="border-bottom:solid 1px ;">Remaining</td>
                <!-- <td   width="5%" class="td-title_left">Remaining</td> -->
                <td   width="10%" colspan="2" class="td-title">Advance</td>
                
                
            </tr>
            <tr class="tr-title_">
                <td   width="8%" class="td-title_left">Nbr.</td>
                <td   width="4%" class="td-title_left">Date</td>
                <td   class="td-title_left">Code</td>
                <td   class="td-title_left">Name</td>
                <td   width="5%" class="td-title_left">Code Inv</td>
                <td   width="12%" class="td-title">Description</td>
                <td   class="td-title">Nbr</td>
                <td   class="td-title_left">User</td>
                <td   class="td-title_left">UOM</td>
                <td   class="td-title">Order</td>
                <td   class="td-title_left">Canceled</td>
                <!-- <td   class="td-title_left">ETD Dt</td> -->
                <td   class="td-title_left">Received</td>
               <!--  <td   class="td-title_left">Harbour</td> -->
                <td   class="td-title_left">Rejected</td>
                <td   class="td-title_left">Remaining</td>
                <td   class="td-title_left">Cury</td>
                <td   class="td-title_left" width="5%">Value</td>
                <td   class="td-title_left" width="5%">USD</td>
                <td   class="td-title_left">Value</td>
                <td   class="td-title_left">Date</td>
            </tr>
        </thead>
        <tfoot>
           <!--  <tr width="100%">
                <td colspan="16" width="100%">
                    <table width="100%">
                        <tr width="100%">
                            <td valign="bottom" width="10%"><br/><br/><br/><br/><br/>Prepared By : </td>
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td>
                            <td valign="bottom" width="10%">Checked By : </td>
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td>
                            <td valign="bottom" width="10%">Approved By : </td>
                            <td valign="bottom" width="10%">&nbsp;</td>
                        </tr>
                    </table>
                </td>
            </tr> -->
        </tfoot>
        <tbody>
            
        %for line in get_result(data):
            <%
                itemrequestnbr=get_itemrequest(line['id_po'])
                itemreceived=get_itemreceived(line['id_po'],line['id_product'],data['form']['date_start'],data['form']['date_stop'])
                itemrejected=get_itemrejected(line['id_po'],line['id_product'],data['form']['date_start'],data['form']['date_stop'])
                itemcanceled=get_itemcanceled(line['id_po'],line['id_product'],data['form']['date_start'],data['form']['date_stop'])
                itemremaining=(line['product_qty']-itemreceived)+itemrejected+itemcanceled
                price_subtotal_usd=get_price_subtotal_usd(line['id_pol'],line['id_po'],line['id_product'])
                advance_value,advance_date=get_advanced(line['id_po'])
                # advance_date=get_advanced(line['id_po'])
                # advance_value=get_advanced(line['id_po'])
                dateorder=xdate(line['date_order'])

            %>
            %if itemremaining >0:
                <tr>
                    <td   class="td-details">${line['po_number']}</td>
                    <td   class="td-details">
                        ${dateorder or ''}

                    </td>
                    <td   class="td-details">${line['partner_code'] or ''}</td>
                    <td   class="td-details">${line['vendor'] or ''}</td>
                    <td   class="td-details">${line['code_product'] or ''}</td>
                    <td   class="td-details">${line['description'] or ''}</td>
                    <td   class="td-details">${itemrequestnbr}</td>
                    <td   class="td-details" style="text-transform:uppercase;">${line['goods_type'] or ''} </td>
                    <td   class="td-details">${line['uom'] or ''}</td>
                    <td   class="td-details-right">${formatLang(line['product_qty'],digits=2) or 0.00}</td>
                    <td   class="td-details-right">${formatLang(itemcanceled,digits=2) or 0.00}</td>
                    <td   class="td-details-right">${formatLang(itemreceived,digits=2) or 0.00}</td>
                    <td   class="td-details-right">${formatLang(itemrejected, digits=2) or 0.00}</td>
                    <td   class="td-details-right">
                        ${itemremaining}

                    </td>
                    <td   class="td-details">${line['currency']}</td>
                    <td   class="td-details-right">${formatLang(line['price']*itemremaining,digits=2) or 0.00}</td>
                    <td   class="td-details-right">${formatLang((price_subtotal_usd/line['product_qty'])*itemremaining,digits=2) or 0.00}</td>
                    <td   class="td-details-right">${formatLang(advance_value,digits=2) or 0.00}</td>
                    <td   class="td-details">${advance_date or ''}</td>
                </tr>
            %endif
               
                <!-- <tr class="tr-grandtotal">
                    <td colspan="4" class="td-grandtotal">&nbsp;</td>
                    <td colspan="2" class="td-grandtotal" style="text-align:right;">Sub Total Dept : </td>
                    <td colspan="1" class="td-grandtotal" style="text-align:right;"></td>
                    <td colspan="9" class="td-grandtotal" style="text-align:right;"></td>
                </tr> -->
          %endfor  
            </tbody>
        
    </table>

</body>
</html>