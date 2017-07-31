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
<%
rate=get_rate(o)
%>

<div  id="wrapper">
<div id="header">
    <table width="100%">
     <!-- <table style="page-break-before:always;"> -->
        <thead>
            <tr><td colspan="5" class="title">PT. BITRATEX INDUSTRIES</td></tr>
            <tr><td colspan="5" class="title"><a style="border-bottom:1px solid;">SUPPLIER COMPARISON APPROVAL</a></td></tr>
            <tr>
                <td  class="td-title_left" width="7%">Quotation No :</td>
                <td  class=""  width="15%" style="text-align:left;">${o.name or ''}</td>
                <td  class=""  width="56%">&nbsp;</td>
                <td  class="" width="7%">&nbsp;</td>
                <td  class=""  width="15%">&nbsp;</td>
            </tr>
            <tr>
                <td  class="td-title_left" width="7%">Date :</td>
                <td  class="">${o.sca_date!='False' and formatLang(o.sca_date,date=True) or formatLang(time.strftime('%Y-%m-%d'),date=True)}</td>
                <td  class="">&nbsp;</td>
                <td  class="">&nbsp;</td>
                <td  class="">
                    % for k, v in rate.items():
                    1&nbsp;${ o.company_id and o.company_id.currency_id and o.company_id.currency_id.name}&nbsp;=&nbsp;${formatLang(v,digits=2)}&nbsp;${k or ''}<br/>
                    % endfor
                </td>
            </tr>
        </thead>
    </table>

</div>
<div id="content">
    <%
        total_all=0.0
        total_all_usd=0.0  
        result_grouped = {}
        for rfq in o.purchase_ids:
            if rfq.state !='cancel':
                key_sup = (rfq.partner_id, rfq.pricelist_id and rfq.pricelist_id.currency_id and rfq.pricelist_id.currency_id.name, rfq.state)
                if key_sup not in result_grouped:
                    result_grouped.update({key_sup:{}})
                for line in rfq.order_line:
                    net_price = line.price_unit
                    if line.discount_ids:
                        for disc in line.discount_ids:
                            # net_price -= (disc.type == 'percentage') and round((disc.discount_amt)*net_price/100,2) or disc.discount_amt
                            net_price -= (disc.type == 'percentage') and (disc.discount_amt)*net_price/100 or disc.discount_amt
                    
                    key_product=(line.product_id, line.product_uom)
                    if key_product not in result_grouped[key_sup]:
                        result_grouped[key_sup].update({key_product:{
                            "price":net_price,
                            "price_usd":get_price_usd(rfq, net_price, o.sca_date!='False' and o.sca_date or time.strftime('%Y-%m-%d')),
                            "currency":rfq.pricelist_id and rfq.pricelist_id.currency_id and rfq.pricelist_id.currency_id.name,
                            "remark":rfq.remark_po,
                            "name2":line.name,
                            "qty" : 0.0,
                        }})
                    result_grouped[key_sup][key_product]['qty']+=line.product_qty
        result_othercost={}
        for rfq_othcost in o.purchase_ids:
            key_purcids_sup=rfq_othcost.partner_id
            if key_purcids_sup not in result_othercost:
                result_othercost.update({key_purcids_sup:{}})
            for line_oth in rfq_othcost.order_line:
                if line_oth.other_cost_type:
                    key_supoth=line_oth.name
                    if key_supoth not in result_othercost[key_purcids_sup]:
                        result_othercost[key_purcids_sup].update({key_supoth:{
                            "price":line_oth.price_unit or 0.00,
                            "price_usd":get_price_usd(rfq_othcost, line_oth.price_unit, o.sca_date!='False' and o.sca_date or time.strftime('%Y-%m-%d')),
                        }})
    %>
    <table width="98%" >
        <thead>
            <tr>
                <td class="td-title">&nbsp;</td>
                <td class="td-title" style="border-right:.5px solid black;" >&nbsp;</td>
                <td class="title" style="border-right:.5px solid black;"  colspan="5">LAST PRICE</td>
                <td class="td-title" colspan="2" style="border-right:.5px solid black;" >&nbsp;</td>
                % for key_supplier in sorted(result_grouped.keys(),key=lambda l:l[0].name):
                    <td class="title" colspan="3"style="border-right:.5px solid black;" >${key_supplier[0].name or ''}</td>
                %endfor
            </tr>
            <tr>
                <td class="td-title" width="8%">ITEM CODE</td>
                <td class="td-title" width="15%" style="border-right:.5px solid black;" >DESCRIPTION</td>
                <td class="td-title" width="5%" style="padding-left:5px;">PO.NO.</td>
                <td class="td-title" width="5%">DATE</td>
                <td class="td-title" width="7%">VENDOR NAME</td>
                <td class="td-title" width="5%">CCY</td>
                <td class="td-title" width="5%" style="border-right:.5px solid black;" >PRICE</td>
                <td class="td-title" width="5%" style="padding-left:5px;">UOM</td>
                <td class="td-title" width="5%" style="border-right:.5px solid black;">QTY</td>
                %for key_supplier in sorted(result_grouped.keys(),key=lambda l:l[0].name):   
                    <td class="td-title" width="5%" style="padding-left:5px;">${key_supplier[1]}</td>
                    <td class="td-title" width="5%">USD</td>
                    <td class="td-title" width="5%" style="border-right:.5px solid black;" >AMT USD</td>
                %endfor
            </tr>
            <tr>
                <td class='grsbwhtbl' colspan="12" width="98%"></td>
            </tr>
        </thead>
        <tbody>
        <%
            lines = get_lines(o)
        %>
        %for line in sorted(lines, key = lambda x:x['seq']):
            <%
            ada_price = False
            for key_supplier in result_grouped.keys():
                for key_product in result_grouped[key_supplier].keys():
                    if line['product_id']==key_product[0].id:
                        ada_price = ada_price or True
            %>
            % if ada_price:
            <tr>
                <td class="td-details">${line['product_code'] or ''}</td>
                <td class="td-details" style="border-right:.5px solid black;" >${line['product_name'] or ''}</td>
                <td class="td-details" style="padding-left:5px;">${line['last_po'] or ''}</td>
                <td class="td-details">${line['last_po_date'] or ''}</td>
                <td class="td-details">${line['last_po_vendor'] or ''}</td>
                <td class="td-details">${line['last_po_currency'] or ''}</td>
                <td class="td-details" style="border-right:.5px solid black;" >${line['last_price'] and formatLang(line['last_price'],digits=2) or ''}</td>

            %for key_supplier in sorted(result_grouped.keys(),key=lambda l:l[0].name):
                %for key_product_id in sorted(result_grouped[key_supplier].keys(),key=lambda m:m[0].default_code):
                    %if line['product_id']==key_product_id[0].id:
                        <td class="td-details" style="padding-left:5px;">${key_product_id[1].name or ''}</td>
                        <td class="td-details-right" style="border-right:.5px solid black;">${formatLang(result_grouped[key_supplier][key_product_id]['qty'] or 0.0,digits=4)}</td>
                        <td class="td-details-right">${formatLang(result_grouped[key_supplier][key_product_id]["price"],digits=2)}</td>
                        <td class="td-details-right">${formatLang(result_grouped[key_supplier][key_product_id]["price_usd"],digits=2)}</td>
                        <td class="td-details-right" style="border-right:.5px solid black;padding-right:10px;" >${formatLang(result_grouped[key_supplier][key_product_id]["price_usd"]*result_grouped[key_supplier][key_product_id]['qty'],digits=2)}</td>
                    <!-- %else:
                        <td class="td-details">&nbsp;</td>
                        <td class="td-details">&nbsp;</td>
                        <td class="td-details" style="border-right:.5px solid black;" >&nbsp;</td> -->
                        <%
                        total_all+=result_grouped[key_supplier][key_product_id]["price"]*result_grouped[key_supplier][key_product_id]['qty']
                        total_all_usd+=result_grouped[key_supplier][key_product_id]["price_usd"]*result_grouped[key_supplier][key_product_id]['qty']
                        %>
                    %endif
                %endfor
                
            %endfor
            </tr>
            %endif
        %endfor
            <tr>
                <td class='grsbwhtbl' colspan="12" width="98%"></td>
            </tr>
        
        % for key_suppothcost in sorted(result_othercost.keys(),key=lambda l:l.name):
            % for cost_line in sorted(result_othercost[key_suppothcost].keys(),key=lambda k:k[0]):
                  <tr>
                        <td class="td-title" colspan="9" width="65%" style="border-right:.5px solid black;text-align:right;padding-right:5px;text-transform:uppercase;">${cost_line}</td>
                         <td class="td-details-right" style="font-weight: bold;" width="5%">${formatLang(result_othercost[key_suppothcost][cost_line]["price"],digits=2)}</td>
                         <td class="td-details-right" width="5%"></td>
                         <td class="td-details-right" width="5%" style="font-weight: bold;padding-right:10px;" >${formatLang(result_othercost[key_suppothcost][cost_line]["price_usd"],digits=2)}</td>
                 </tr>
            <%
                total_all+=result_othercost[key_suppothcost][cost_line]["price"]
                total_all_usd+=result_othercost[key_suppothcost][cost_line]["price_usd"]
            %>
            % endfor
        % endfor


        <tr>
            <td class="td-title" colspan="9" width="65%" style="border-right:.5px solid black;text-align:right;padding-right:5px;">TOTAL</td>
            %for key_supplier in sorted(result_grouped.keys(),key=lambda l:l[0].name):   
                <td class="td-details-right" style="font-weight: bold;" width="5%">${formatLang(total_all,digits=2)}</td>
                <td class="td-details-right" width="5%"></td>
                <td class="td-details-right" width="5%" style="border-right:.5px solid black;padding-right:10px;font-weight: bold;" >${formatLang(total_all_usd,digits=2)}</td>
            %endfor
        </tr>
        </tbody>

    </table>
    </br>
    
        <div style="vertical-align:top;">
            <table>
                %if o.purchase_ids:
                    <%
                        print o.purchase_ids.state,"xazaxzxaxzxaxxaxzxaxzxzxzxzxzxxzxxaxaaxzxzz"
                    %>
                    <tr>
                        <td><a style="vertical-align:top;"><b class="td-title">Remarks :</b></td>
                    </tr>
                    <tr>
                    %for footnote in o.purchase_ids:
                        %if footnote.state !="cancel":
                        
                            <td>
                            ${footnote.partner_id.name} &nbsp; :</br>
                             ${(footnote.remark_po or '').replace('\n','<br/>')}
                            </td>
                        %endif
                    %endfor

                    </tr>
                %endif
            </table>
        </div>
</div>
    <div id="break2" style="vertical-align:top;">&nbsp;</div>
    <div id="break1" style="page-break-before: always;">
    <div id="footer">                   
    <table width="100%" align="top">
    <tr>
        <td id="bwhtblup1" width="20%">MMD</td>
        <td width="20%" style="border-top:none;">&nbsp;</td>
        <td id="bwhtblup1" width="20%">Mr. AKL</td>
        <!-- <td width="5%" style="border-top:none;">&nbsp;</td> -->
        <!-- <td id="bwhtblup1" width="15%">Mr. D Singh</td> -->
        <td width="20%" style="border-top:none;">&nbsp;</td>
        <td id="bwhtblup1" width="20%">President Director</td>
    </tr>
    <tr>
        <td id="bwhtbl2" colspan="9" width="100%"></td>
    </tr>
    </table>                    
    </div>

%endfor
</div>

</body>
</html>