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
    # from datetime import datetime
    # from datetime import date, timedelta
    import datetime
    # from datetime import datetime
    def xdate(x):
        try:
            x1 = x[:10]
        except:
            x1 = ''

        try:
            y = datetime.datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            y = ''
        return y
%>
%for o in objects:
<%

    sale_line_ids=[]
    for x in o.priority_lines_ids+o.sale_line_ids:
        sale_line_ids.append(x.id)
    data_pending =get_pending_qty_data(sale_line_ids,o.as_on_date,o.sale_type)
    
%>
<body>



    <table style="page-break-before:always;" width="100%" >
        <thead >
            <tr>
                <td colspan="19" class="title">PT. BITRATEX INDUSTRIES</td>

            </tr>
            <tr>
                <td colspan="19" class="title">Sale Order Priority Report</td>
            </tr>
            <tr>
                <td colspan="19" class="title">As On Date ${o.as_on_date}</td>
            </tr>
            <tr class="tr-title" >
                <td width="8%" class="td-title">Product</td>
                <td width="7%" class="td-title">SC No.</td>
                <td width="4%" class="td-title">SC</td>
                <td width="8%" class="td-title">Customer</td>
                <td width="5%" class="td-title">Bales</td>
                <td width="2%" class="td-title">P/C</td>
                <td width="4%" class="td-title">Cn Wt</td>
                <td width="4%" class="td-title">LSD</td>
                <td width="4%" class="td-title">LSD</td>
                <td width="4%" class="td-title">LSD</td>
                <td width="2%" class="td-title">TT/LC</td>
                <td width="2%" class="td-title">Priority</td>
                <td width="7%" class="td-title">Ready By</td>
                <td width="4%" class="td-title">Good</td>
                <td width="4%" class="td-title">Shipped</td>
                <td width="4%" class="td-title">Shipped</td>
                <td width="6%" class="td-title">Bitra</td>
                <td width="7%" class="td-title">Internal</td>
                <td width="4%" class="td-title">Country</td>
            </tr>
            <tr class="tr-title_">
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title">Date</td>
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title">(SC)</td>
                <td  class="td-title">(LC)</td>
                <td  class="td-title">5 DAY</td>
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title"></td>
                <td  class="td-title">Actual Date</td>
                <td  class="td-title">ETD</td>
                <td  class="td-title">ETA</td>
                <td  class="td-title">Remark</td>
                <td  class="td-title">Remark</td>
                <td  class="td-title"></td>
            </tr>
        </thead>
        <tfoot>
        </tfoot>
        <tbody>
        <%
        result_group={}
        for lines in o.priority_lines_ids+o.sale_line_ids:
            key_unit=lines.production_location.name or ''
            # print key_unit,"cxcxcxcxcxcxcxcxcxcxcxcxcx"
            if key_unit not in result_group:
                result_group.update({key_unit:{}})
            key2_product=lines.product_id.id or ''
            if key2_product not in result_group[key_unit]:
                result_group[key_unit].update({key2_product:[]})
            result_group[key_unit][key2_product].append(lines)
            # print result_group,"dadadadadaaaaaaaaaaaaaaaa"
        %>
        %for unit in sorted(result_group.keys(),key=lambda l:l):
            <% 
                # print unit,"zazazazazazazazazazaaz" 
                # xy=result_group[unit]
            %>
        <tr>
            <td colspan="19" style="font-weight:bold;">${unit}</td>
        </tr>
        <!-- %for line in xy: -->
        %for key_product in sorted(result_group[unit].keys(),key=lambda k:k):
            <%
                xy=sorted(result_group[unit][key_product],key=lambda j:j.product_id.id)
            %>
            %for line in xy :
                <% 
                    
                    # import timedelta
                    # print line.id,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
                    # eta,etd=get_date(line.id)
                    lsd_str=line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date
                    # print lsd_str,"xaxaxaxaxaxa"
                    lsd=datetime.datetime.strptime(lsd_str,'%Y-%m-%d')
                    # print lsd,"lsdsdlsldlsldsllldllaa"

                    date_5=datetime.timedelta(days=5)
                    # print date_5,"mamamamama"
                    date5=lsd-date_5
                    # print date5,"AGAGAGAGAGAGAGAGAGAGA"
                    lsd_5=datetime.datetime.strftime(date5,'%d/%m/%Y')
                    # print line.product_uom.id, "AGAGAGAGAGAGAGAGAGAGA"
                    # qty_bale=uom_to_base(line.product_uom_qty,line.product_uom.id)
                    # shipped_eta=datetime.datetime.strftime(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_arriv_date,'%d/%m/%Y')
                    # qty_balance=pending_bale_qty(line.id,line.product_id.id)
                    # bale_qty=sorted(result_group.keys(),key=lambda l:line.id).value()
                    qty_bale=data_pending[line.id]
                    # print qty_bale,"qoqoqoqoqoqoqoqoqoqoqoqoq"

                %>
            <tr>
                <td class="td-details">${line.product_id and line.product_id.name or ''}</td>
                <td class="td-details">${line.sequence_line or ''}</td>
                <td class="td-details">${line.order_id and line.order_id.date_order or ''}</td>
                <td class="td-details">${line.order_id and line.order_id.partner_id and line.order_id.partner_id.name or ''}</td>
                <td class="td-details">${formatLang(qty_bale,digits=2) or ''}</td>
                <td class="td-details">${line.packing_type.alias}</td>
                <td class="td-details">${line.cone_weight}</td>
                <td class="td-details">${line.reschedule_date and line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''}</td>
                <td class="td-details">${line.est_delivery_date and line.order_id and line.order_id.max_est_delivery_date or ''}</td>
                <td class="td-details">${lsd_5}</td>
                <td class="td-details">${line.order_id and line.order_id.payment_method or ''}</td>
                <td class="td-details">${line.priority or ''}</td>
                <td class="td-details">${line.ready_by or ''}</td>
                <td class="td-details">${line.goods_actual_date or ''}</td>
                <td class="td-details">${xdate(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_deliv_date)}</td>
                <td class="td-details">${xdate(line.move_ids and line.move_ids[0].picking_id and line.move_ids[0].picking_id.estimation_arriv_date)}</td>
                <td class="td-details">${line.remark_priorities or ''}</td>
                <td class="td-details">${line.other_description or ''}</td>
                <td class="td-details">${line.order_id and line.order_id.dest_country_id and line.order_id.dest_country_id.name or ''}</td>
            </tr>
            %endfor
        %endfor
        %endfor
        </tbody>

    </table>
</body>
%endfor
</html>