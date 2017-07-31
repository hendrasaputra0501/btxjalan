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
    td.title_left {
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
        /*border-bottom: 1px solid;*/
        border-bottom: 1px solid;
    }

     tr.tr-title_thin {
        border-top: 1px solid #efefef;
        /*border-bottom: 1px solid;*/
        border-bottom: 1px solid #efefef;
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
        result_group={}
        for lines in get_result(data):
            key_source_loc=(lines['source_location'] or '')
            if key_source_loc not in result_group:
                result_group.update({key_source_loc:{}})
            key_fg=(lines['fg_group'] or '')
            if key_fg=='FGY':
                key_fg_group='YARN'
            else:
                key_fg_group='FABRIC'
            # key_fg_group=(lines['fg_group'] or '')
            if key_fg_group not in result_group[key_source_loc]:
                result_group[key_source_loc].update({key_fg_group:[]})
            result_group[key_source_loc][key_fg_group].append(lines)
    %>
    %for key_source_location in sorted(result_group.keys(), key=lambda l:l):
    <table style="page-break-before:always;">
        <thead>
        <tr>
            <td colspan="5" class="title">Bitratex Industries</td>
        </tr>
        <tr>
            <td colspan="5" class="title">WASTE TRANSFER SUMMARY</td>
        </tr>
        <tr>
            <td colspan="5" class="title">From ${formatLang(data['form']['date_start'],date=True)} to ${formatLang(data['form']['date_stop'],date=True)}</td>
        </tr>
        <tr>
            <td colspan="2"> Source : <b>${[key_source_location][0]}</b></td>
            
            <td  colspan="3" ></td>
        </tr>
        <tr class="tr-title">
            <td  width="25%" class="td-title">Item Code</td>
            <td  width="25%" class="td-title">Item Description</td>
            <td  width="25%" colspan="2" class="td-title">Quantity</td>
            <td  width="25%" class="td-title"> </td>
        </tr>
        </thead>
        <tfoot>
        </tfoot>
        <tbody>
        <%
            total_qty=0
            total_uop_qty=0
        %>
        %for key_finishgood in sorted(result_group[key_source_location].keys(), key=lambda m:m):
            <%
                line=sorted(result_group[key_source_location][key_finishgood], key=lambda x:x['default_code'])
                qty=0
                uop_qty=0
            %>
            %for lines in line:
                <tr class="">
                    <td  class="td-details">${lines['default_code']}</td>
                    <td  class="td-details">${lines['name_template']}</td>
                    <td  class="td-details-right">${lines['product_qty']}</td>
                    <td  class="td-details"> ${lines['uom']}</td>
                    <td  class="td-details-right"> ${lines['product_uop_qty']}</td>
                </tr>
                <%
                    qty+=lines['product_qty']
                    uop_qty+=lines['product_uop_qty']
                %>
            %endfor
                <tr class="tr-title_thin">
                    <td class="title" colspan="2">Sub Total Finished Good ${[key_finishgood][0]}</td>
                    <td class="td-subtotal-amount">${qty}</td>
                    <td class="td-subtotal-amount"></td>
                    <td class="td-subtotal-amount" >${uop_qty}</td>
                </tr>
                <%
                    total_qty+=qty
                    total_uop_qty+=uop_qty
                %>
        %endfor
                <tr class="tr-title">
                    <td class="title" colspan="2">Total ${[key_source_location][0]}</td>
                    <td  class="td-subtotal-amount">${total_qty}</td>
                    <td  class="td-subtotal-amount"></td>
                    <td  class="td-subtotal-amount">${total_uop_qty}</td>
                </tr>
        </tbody>
    </table>
    %endfor

</body>
</html>