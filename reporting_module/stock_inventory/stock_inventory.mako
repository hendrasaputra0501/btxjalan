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
    td.details {
        /*font-weight: bold;*/
        font-size: 10px;
        text-align: center;
    }
    
    td.title_left{
        font-weight: bold;
        font-size: 10px;
        text-align: left;
    }

    table
    {
        border-collapse: collapse;
        width: 100%;
    }

    tr.tr-title {
        border-top: 1px solid;
        border-bottom: 1px solid;
    }

    td.td-title {
        text-align: left;
        font-weight: bold;
    }
    td.td-title_right {
        text-align: right;
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
    td.td-details-right{
        vertical-align: top;
        text-align: right;
    }
    .grsbwhtbl{
            border-top: .5px solid black;
        }
        /*footer*/
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
        padding-top:40px;
        }
        #header {
        padding:10px;
        /*background:#5ee;*/
        }
        #content {
        padding:10px;
        width:100%;
        padding-bottom:50px; /* Height of the footer element */ 
        /*background:green;*/
        /*height:910px;*/
        }
        #footer {
        width:100%;
        height:20px;
        position:absolute;
        bottom:0;
        left:0;
        /*background:#ee5;*/
        }
#bwhtblup1{
        font-weight:bold;
        text-align: center;
        text-transform: uppercase;
        border-top: 1px solid #808080;
        vertical-align:top;
}
#break1{
    position:relative;
    display: block;
    }
 #break2{
        /*background: yellow;*/
        bottom:60;
        height:100px;
        }


    </style>
</head>
<body>
   
%for o in objects:
    <table width="100%">
     <!-- <table style="page-break-before:always;"> -->
        <thead>
            <tr><td colspan="5" class="title" style="border-bottom:1px solid;">PT. BITRATEX INDUSTRIES</td></tr>
            <tr><td colspan="5" class="title">STOCK INVENTORY</td></tr>
            <tr>
                <td  colspan="3" class="title" width="50%">Inventory</td>
                <td  colspan="2" class="title"  width="50%">Date</td>
            </tr>
            <tr>
                <td  colspan="3" class="details" width="50%">${o.name}</td>
                <td  colspan="2" class="details"  width="50%">${o.date}</td>
            </tr>
            
        </thead>
    </table>

    <table width="98%" >
        <thead>
            <tr>
                <td  class="td-title" width="10%">Location</td>
                <td  class="td-title" width="10%" style="padding-left:5px;">Production Lot</td>
                <td  class="td-title" width="10%">Product</td>
                <td  class="td-title_right" width="10%">Quantity</td>
                <td  class="td-title_right" width="10%">
                    Manual Quantity
                </td>
            </tr>
            
            <tr>
                <td class='grsbwhtbl' colspan="5" width="100%"></td>
            </tr>
        </thead>
        <%totalqty=0.0
        %>
        <tbody>
            %for line in o.inventory_line_id:
            <tr>
                <td class="td-details">${line.location_id.name or ''}</td>
                <td class="td-details" style="padding-left:5px;">${line.pack_id.name or ''}</td>
                <td class="td-details" >${line.product_id.name or ''}</td>
                <td class="td-details-right">${formatLang(line.product_qty,digits=4) or 0.0000}</td>
                <td class="td-details">${}</td>
            </tr>
            <% totalqty+=line.product_qty %>
            %endfor
            <tr>
                <td colspan="3">&nbsp;</td>
                <td colspan="2" class="grsbwhtbl">&nbsp;</td>
            </tr>
            <tr>
                <td colspan="2">&nbsp;</td>
                <td class="td-title_right">Total :</td>
                <td class="td-details-right">${formatLang(totalqty,digits=4) or 0.0000} </td>
                <td></td>
            </tr>
        </tbody>
        <tfoot>
        </tfoot>

    </table>
%endfor
</body>
</html>