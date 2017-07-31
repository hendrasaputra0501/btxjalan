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
# def _get_rate(self, line):
#         cr=self.cr
#         uid=self.uid
#         curr_obj = self.pool.get('res.currency')

#         ctx={'date':line.date_order!='False' and line.date_order or time.strftime('%Y-%m-%d')}
#         curry_id=line.company_curry_id
#         cury_id_po=line.currency_id
#         rate=curr_obj._get_conversion_rate(curry_id,cury_id_po ,  context=ctx)
        # rate_dict = {}
        # for rfq in purc_req_obj.purchase_ids:
        #     cury_id2= rfq.pricelist_id and rfq.pricelist_id.currency_id
        #     if rfq not in rate_dict:
        #         rate=curr_obj._get_conversion_rate(cr, uid,curry_id,cury_id2 ,  context=ctx)
        #         rate_dict.update({cury_id2.name : rate})
        # return rate_dict


result_grouped = {}
for line in get_result(data):
    # print "+++++++++++++++++++++++++++++++++++++++++++++++++++++",line['price_unit']
    net_priceu=line['price_unit']
    # print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++",line['semua_diskon']
    if line['semua_diskon']:
        for x in line['semua_diskon'].split('|'):
            # print x
            y=x.split(',')
            try:
                discount_amt = float(y[1])
            except:
                discount_amt = 0.0
            
            if y[0]=='percentage':
                net_priceu-=net_priceu*discount_amt/100
            else:
                net_priceu-=discount_amt
    line.update({'net_priceu':net_priceu})
    key_dept=(line['department'] or "")
    # print  line['department']
    if key_dept not in result_grouped:
        result_grouped.update({key_dept:{}})
    key_po=line['po_line_id']
    if key_po not in result_grouped[key_dept]:
        result_grouped[key_dept].update({key_po:[]})
    result_grouped[key_dept][key_po].append(line)
    
%>
   
 %for key_department in sorted(result_grouped.keys(),key=lambda l:key_dept):  
<table style="page-break-before:always;">
        <thead>
            <tr><td colspan="15" class="title">PT. BITRATEX INDUSTRIES</td></tr>
            <tr><td colspan="15" class="title">PENDING DETAIL SHIPMENT STATUS REGISTER 
                %if data['form']['purchase_type']=='all':
                    &nbsp;
                %else:
                    <a style="text-transform:uppercase;">${data['form']['purchase_type']}</a>
                %endif
                 - DEPT. WISE</td></tr>
            <tr><td colspan="15" class="title">FROM ${formatLang(data['form']['date_start'],date=True)} TO ${formatLang(data['form']['date_stop'],date=True)}</td></tr>

            <tr class="tr-title">
                <td  width="2%" class="td-title_left">Sr</td>
                <td  width="5%" class="td-title"></td>
                <td  width="9%" colspan="2" class="td-title_border_btm" >Indent No.</td>
                <td  width="8%" colspan="3" class="td-title_border_btm">Value</td>
                
                <td  width="5%" colspan="2" class="td-title_border_btm">Payment</td>
                
                <td  width="3%" class="td-title">Divy</td>
                <td  width="8%" colspan="2" class="td-title_border_btm">Shipment</td>
    
                <td  width="10%" colspan="3" class="td-title_border_btm">Arrival</td>
                
            </tr>
            <tr class="tr-title_">
                <td   class="td-title_left">No.</td>
                <td   class="td-title_left">PO.Number</td>
                <td   class="td-title_left">Description</td>
                <td   class="td-title_left">Vendor</td>
                <td   width="2%" class="td-title_left">Ccy</td>
                <td   width="3%" class="td-title">Amount</td>
                <td   width="3%" class="td-title">eqv. USD</td>
                <td   class="td-title_left">Paid Type </td>
                <td   class="td-title_left">Nbr. </td>
                <td   class="td-title">by</td>
                <td   class="td-title_left">Doc. Number</td>
                <td   class="td-title_left">ETD Dt</td>
                <td   class="td-title_left">Harbour</td>
                <td   class="td-title_left">Factory</td>
                <td   class="td-title_left">Remarks</td>
            </tr>
        </thead>
        <tfoot>
            <tr width="100%">
                <td colspan="18" width="100%">
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
            </tr>
        </tfoot>
        <%
            sn=1
            tot_usd=0
        %>
            ${[key_department][0]}
        
            <tbody>
        %for key_psr in sorted(result_grouped[key_department].keys(),key=lambda m:key_po):    
            <%

                line_psr=sorted(result_grouped[key_department][key_psr],key=lambda z:z['po_line_id'])
                # lines = sorted(result_grouped[key_loc][key_mrr], key=lambda x:x['sm_id'])
               
            %>
            %for lines in line_psr:
                <% 
                    # net_price=
                    get_usd=get_price_usd(lines['currency_idpo'],lines['company_curry_id'],lines['date_order'],lines['net_priceu'])
                %>
                
                <tr>
                    <td   class="td-details">${sn}</td>
                    <td   class="td-details">${lines['po_number'] or ''}</td>
                    <td   class="td-details">
                            %if lines['indent_no']:
                                ${lines['indent_no'] or ''}</br>${lines['description'] or ''}
                            % else:
                                ${lines['description'] or ''}
                            % endif
                    </td>
                    <td   class="td-details">${lines['vendor'] or ''}</td>
                    <td   class="td-details">${lines['currency'] or ''}</td>
                    <td   class="td-details-right">${formatLang(lines['net_priceu']*lines['product_qty'],digits=2)}</td>
                    <td   class="td-details-right">${formatLang(get_usd*lines['product_qty'],digits=2)}</td>
                    <td   class="td-details" style="text-transform:uppercase;">${lines['payment_method'] or ''}</td>
                    <!-- <td   class="td-details">Nbr. </td> -->
                    <td   class="td-details"></td>
                    <!-- <td   class="td-details">by</td> -->
                    <td   class="td-details"></td>
                    <!-- <td   class="td-details">Doc. Number</td> -->
                    <td   class="td-details"></td>
                    <td   class="td-details">${lines['etd_date'] or ''}</td>
                    <!-- <td   class="td-details">Harbour</td> -->
                    <td   class="td-details"></td>
                    <td   class="td-details">${lines['date_approve'] or ''}</td>
                    <td   class="td-details">${lines['remark'] or ''}</td>
                </tr>
                <!-- tot_usd=get_usd*lines['product_qty'] -->
                <%
                tot_usd+=get_usd*lines['product_qty']
                sn+=1   
                
                %>
            %endfor
        %endfor
               
                <tr class="tr-grandtotal">
                    <td colspan="5" class="td-grandtotal">&nbsp;</td>
                    <td colspan="1" class="td-grandtotal" style="text-align:right;">Sub Total Dept : </td>
                    <td colspan="1" class="td-grandtotal" style="text-align:right;">${formatLang(tot_usd,digits=2)} </td>
                    <td colspan="8" class="td-grandtotal" style="text-align:right;"></td>
                </tr>
            </tbody>
        
    </table>
 %endfor
</body>
</html>