<html>
<head>
    <style type="text/css">
    body{
        font-family:Verdana;
        /*font-family:fontenc;*/
        font-size: 6.5pt;
        margin:0;
        padding-top:0;
        height:90%;
        /*background-color:green;*/
    }

    td.title{
        font-weight: bold;
        font-size: 10px;
        text-align: center;
    }

    table
    {
        border-collapse: collapse;
        /*width: 100%;*/
        /*width:98%;*/
    }

    tr.tr-title {
        border-top: 1px solid;
        border-bottom: 1px solid;
    }

    td.td-title {
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

    .wrapper {
        min-height:100%;
        position:static;
        /*position:relative;*/
        font-family: Arial;
        font-size:11px;
        }
        .header {
        padding:10px;
        background:#5ee;
        }
        .content {
            /*position:absolute;*/
            display: block;
            top:0em;
        /*padding:10px;*/
        width:100%;
        /*height:100%;*/
        /*padding-bottom:150px;  Height of the footer element  */
        /*background:green;*/
        /*height:910px;*/
        }
       

    #footer {
    /*background:blue;*/
    width:100%;
    position:absolute;
    /*position:fixed;*/
    bottom:0;
    left:0;
    /*height:40px;*/
    }
#break1{
    position:relative;
    display: block;
    }
 #break2{
        /*background: yellow;*/
        bottom:60px;
        height:70px;
       /* bottom:20px;
         height:30px;*/
        }
/*html,
        body {
        margin:0;
        padding-top:0;
        height:90%;
        }
thead { display: table-header-group; }
tfoot { display: table-row-group; }
tr { page-break-inside: avoid; }*/
    </style>
</head>
<body>
    <%
    result_grouped = {}
    for line in get_result(data):
        key1 = (line['loc_name'],line['loc_alias'])
        if key1 not in result_grouped:
            result_grouped.update({key1:{}})
        # key2 = (line['party_name'],line['party_code'])
        # if key2 not in result_grouped[key1]:
        #     result_grouped[key1].update({key2:{}})
        key3 = (line['mrr_no'],line['mrr_date'],line['po_no'])
        # if key3 not in result_grouped[key1][key2]:
        if key3 not in result_grouped[key1]:
            # result_grouped[key1][key2].update({key3:[]})
            result_grouped[key1].update({key3:[]})
        # result_grouped[key1][key2][key3].append(line)
        result_grouped[key1][key3].append(line)
    %>

    % for key_loc in sorted(result_grouped.keys(),key=lambda l:l[1]):
    <%
        grand_tot_amt=0.0
        grand_tot_amt_usd=0.0
        grand_tot_qty=0.0
    %>
    <div class='wrapper' style="width:100%;">
    <div class='content' style="width:100%;vertical-align:top;">
    <table style="page-break-before:always;vertical-align:top;width:98%;top:0;">
        <thead>
            <tr><td colspan="2">&nbsp;</td><td>&nbsp;</td><td colspan="12" class="title">PT. BITRATEX INDUSTRIES</td><td colspan="2">&nbsp;</td><td>&nbsp;</td></tr>
            <tr><td colspan="2" style="text-transform:uppercase;font-size:8px;">PO. Type: &nbsp; ${data['form']['purchase_type']}</td><td style="text-transform:uppercase;font-size:8px;"></td><td colspan="12" class="title" style="text-transform:uppercase;">PURCHASE RECEIPT RECORD</td><td colspan="2">&nbsp;</td><td>&nbsp;</td></tr>
            % if data['form']['filter_date']=='as_of':
                <tr><td colspan="2" style="text-transform:uppercase;font-size:8px;">Goods Type: &nbsp; ${data['form']['goods_type']}</td><td style="text-transform:uppercase;font-size:8px;"></td><td colspan="12" class="title">AS OF ${formatLang(data['form']['as_of_date'],date=True)}</td><td colspan="2">&nbsp;</td><td>&nbsp;</td></tr>
            % else:
                <tr><td colspan="2" style="text-transform:uppercase;font-size:8px;">Goods Type: &nbsp; ${data['form']['goods_type']}</td><td style="text-transform:uppercase;font-size:8px;"></td><td colspan="12" class="title">FROM ${formatLang(data['form']['start_date'],date=True)} TO ${formatLang(data['form']['end_date'],date=True)}</td><td colspan="2">&nbsp;</td><td>&nbsp;</td></tr>
            % endif
            <tr class="tr-title">
                <td rowspan="2" width="8%" class="td-title">Receipt<br/>No.</td>
                <!-- <td rowspan="2" width="4%" class="td-title">Batch<br/>No.</td> -->
                <td rowspan="2" width="6%" class="td-title">PO<br/>No.</td>
                <td rowspan="2" width="10%" class="td-title">Vendor<br/>Name</td>
                <td colspan="2" class="td-title">SJL</td>
                <td rowspan="2" width="5%" class="td-title">IR<br/>No.</td>
                <td colspan="3" class="td-title">Inventory</td>
                <td rowspan="2" width="4%" class="td-title">Site<br/>ID</td>
                <td rowspan="2" width="3%" class="td-title">Lot<br/>No.</td>
                <td rowspan="2" width="3%" class="td-title">Trans<br/>Curr</td>
                <td rowspan="2" width="7%" class="td-title">&nbsp;<br/>Unit Cost</td>
                <td colspan="3" class="td-title">Receipt</td>
                <td colspan="2" class="td-title">Quantity</td>
            </tr>
            <tr class="tr-title">
                <td width="4%" class="td-title">No</td>
                <td width="6%" class="td-title">Date</td>
                <td width="6%" class="td-title">ID</td>
                <td width="14%" class="td-title">Description</td>
                <td width="3%" class="td-title">UoM</td>
                <td width="6%" class="td-title">Qty.</td>
                <td width="7%" class="td-title">Ext. Cost</td>
                <td width="4%" class="td-title">USD</td>

                <td width="3%" class="td-title">Apprvd</td>
                <td width="3%" class="td-title">Rejtd</td>
            </tr>
        </thead>
        <tfoot>
            <tr width="100%">
                <td colspan="18" width="100%">
                    <!-- <table width="100%">
                        <tr width="100%"> -->
                           <!--  <td valign="bottom" width="10%"><br/><br/><br/><br/><br/>Prepared By : </td> -->
                            <!-- <td valign="bottom" width="10%"><br/><br/><br/><br/><br/>&nbsp;</td>
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td> -->
                            <!-- <td valign="bottom" width="10%">Checked By : </td> -->
                            <!-- <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td> -->
                            <!-- <td valign="bottom" width="10%">Approved By : </td> -->
                            <!-- <td valign="bottom" width="10%">&nbsp; </td>
                            <td valign="bottom" width="10%">&nbsp;</td> -->
                        <!-- </tr>
                    </table> -->
                </td>
            </tr>
        </tfoot>
        <tbody>
            <tr>
                <td colspan="18" class="td-loc_title">${key_loc[0] or ''}</td>
            </tr>
           
                %for key_mrr in sorted(result_grouped[key_loc].keys(),key=lambda m:m[0]):
                    <%
                    total_amount = 0.0
                    total_amt_usd=0.0
                    total_qty=0.0
                    # lines = sorted(result_grouped[key_loc][key_vendor][key_mrr], key=lambda x:x['sm_id'])
                    lines = sorted(result_grouped[key_loc][key_mrr], key=lambda x:x['sm_id'])
                    # get_usd=get_price_usd(lines['currency_idpo'],lines['company_curry_id'],lines['date_order'],lines['amount'])
                    # lines1=sorted(result_grouped[key_loc].keys(),key=lambda m:m[2])
                    
                    %>

                    % for line in lines:
                    <% 
                        # price_unit=line['po_price_unit']-(line['po_price_unit']*line['discount'])
                        price_unit = get_price_unit(line['sm_id'])
                        # price_unit_usd=get_price_usd(line['curry_idpo'],line['company_curyid'],line['date_order'],price_unit)
                        po_price_subtotal = get_price_subtotal_po(line['sm_id'])
                        po_price_subtotal_usd = get_price_usd(line['curry_idpo'],line['company_curyid'],line['mrr_date2'],price_unit)
                    %>

                        <tr>
                        % if lines.index(line)==0:
                            <td class="td-details">${line['mrr_no']}</td>
                        % else:
                            <td class="td-details">&nbsp;</td>
                        % endif
                            <!-- <td class="td-details">${''}</td> -->
                        % if lines.index(line)==0:
                            <td class="td-details">${line['po_no'] or ''}</td>
                        % else:
                            <td class="td-details">&nbsp;</td>
                        % endif
                        % if lines.index(line)==0:
                            <td class="td-details">${line['party_name'] or ''}</td>
                        % else:
                            <td class="td-details">&nbsp;</td>
                        % endif
                        % if lines.index(line)==0:
                            <td class="td-details">${line['sj_no'] or ''}</td>
                        % else:
                            <td class="td-details">&nbsp;</td>
                        % endif
                        % if lines.index(line)==0:
                            <td class="td-details">${line['sj_date'] or ''}</td>
                        % else:
                            <td class="td-details">&nbsp;</td>
                        % endif
                            <td class="td-details">${line['ir_number'] or ''}</td>
                            <td class="td-details">${line['prod_code'] or ''}</td>
                            <td class="td-details">${line['prod_name'] or ''}
                            % if line['part_number']:
                                <br/><b>Part Number : </b>${line['part_number'] or ''}
                            % endif
                            </td>
                            <td class="td-details">${line['uom_name'] or ''}</td>
                            <td class="td-details">${line['loc_alias'] or ''}</td>
                            <td class="td-details">${line['lot_number'] or ''}</td>
                            <td class="td-details">${line['curr_name'] or ''}</td>
                            <td class="td-details" align="right">${formatLang(price_unit,digits=2) or ''}</td>
                            <td class="td-details" align="right">${formatLang(line['qty1'],digits=2) or ''}</td>
                            <td class="td-details" align="right">${formatLang((po_price_subtotal,digits=2) or ''}</td>
                            <td class="td-details" align="right">${formatLang(po_price_subtotal_usd,digits=2)}</td>
                            <td class="td-details">${''}</td>
                            <td class="td-details">${''}</td>
                        </tr>
                        <%
                        total_amount+=po_price_subtotal
                        total_amt_usd+=po_price_subtotal_usd
                        total_qty+=line['qty1']
                        %>
                    % endfor
                    <tr class="tr-subtotal">
                        <td colspan="3" class="td-subtotal-label">&nbsp;</td>
                        <td colspan="10" class="td-subtotal-label">Receipt Subtotal </td>
                        <td colspan="1" class="td-subtotal-amount">${formatLang(total_qty,digits=2) or ''}</td>
                        <td class="td-subtotal-amount">${formatLang(total_amount,digits=2) or ''}</td>
                        <td class="td-subtotal-amount">${formatLang(total_amt_usd,digits=2) or ''}</td>
                        <td colspan="2">&nbsp;</td>
                    </tr>
                    <%
                    grand_tot_amt+=total_amount
                    grand_tot_amt_usd+=total_amt_usd
                    grand_tot_qty+=total_qty
                    %>
                % endfor
          
        <tr class="tr-grandtotal">
            <td colspan="3" class="td-grandtotal">&nbsp;</td>
            <td colspan="10" class="td-grandtotal">Grand Total : </td>
            <td colspan="1" class="td-subtotal-amount" style="padding-right:10px;">${formatLang(grand_tot_qty,digits=2) or ''}</td>
            <td class="td-subtotal-amount" style="padding-right:10px;">${formatLang(grand_tot_amt,digits=2) or ''}</td>
            <td class="td-subtotal-amount">${formatLang(grand_tot_amt_usd,digits=2) or ''}</td>
            <td colspan="2">&nbsp;</td>
        </tr>
        </tbody>
    </table>
    % endfor
        </div><!--  content -->
            <div id="break2" style="vertical-align:top;">&nbsp;</div>
            <div id="break1" style="page-break-before: always;">
            <div id='footer'>   
                <table width="100%">
                        <tr width="100%">
                            <td width="17%"></td>
                            <td valign="bottom" width="10%"><br/><br/><br/>Prepared By : </td>
                            <!-- <td valign="bottom" width="10%"><br/><br/><br/><br/><br/>&nbsp;</td> -->
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td>
                            <td valign="bottom" width="10%">Checked By : </td>
                            <!-- <td valign="bottom" width="10%">&nbsp;</td> -->
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td valign="bottom" width="3%">&nbsp;</td>
                            <td valign="bottom" width="10%">Approved By : </td>
                            <!-- <td valign="bottom" width="10%">&nbsp; </td> -->
                            <td valign="bottom" width="10%">&nbsp;</td>
                            <td width="17%"></td>
                        </tr>
                </table>

            </div>
            </div>
    </div>
</body>
</html>