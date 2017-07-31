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
from datetime import datetime
# date_format = "%m/%d/%Y" "%Y-%m-%d"
date_format = "%Y-%m-%d"
result_group={}
for lines in get_result(data):
    key_dept =(lines['department'] or '')
    if key_dept not in result_group:
        result_group.update({key_dept:{}})
    key_poname=(lines['name'])
    if key_poname not in result_group[key_dept]:
        result_group[key_dept].update({key_poname:[]})
    result_group[key_dept][key_poname].append(lines)

%>

%for key_department in sorted(result_group.keys(),key=lambda l:l):
<table style="page-break-before:always;">
        <thead>
            <tr><td colspan="16" class="title">PT. BITRATEX INDUSTRIES</td></tr>
            <tr><td colspan="16" class="title">PENDING SHIPMENT STATUS REGISTER 
               %if data['form']['purchase_type']=='all':
                    &nbsp;
                %else:
                    %if data['form']['filter_by']=='po_date':
                        <a style="text-transform:uppercase;">${data['form']['purchase_type'][2:-2]}</a>
                    %else:
                        &nbsp;
                    %endif
                %endif

                 - DEPT. WISE</td></tr>
            %if data['form']['filter_by']=='po_date':
                <tr><td colspan="16" class="title">FROM ${formatLang(data['form']['from_date'],date=True)} TO ${formatLang(data['form']['to_date'],date=True)}</td></tr>
            %else:
                        &nbsp;
            %endif

            <tr class="tr-title">
                <td  width="2%" class="td-title_left">Sr</td>
                <td  width="5%" class="td-title"></td>
                <td  width="9%" colspan="2" class="td-title_border_btm" >Indent No.</td>
                <td  width="8%" colspan="3" class="td-title_border_btm">Value</td>
                
                <td  width="5%" colspan="2" class="td-title_border_btm">Payment</td>
                
                <td  width="3%" class="td-title">Ship</td>
                <td  width="8%" colspan="2" class="td-title_border_btm">Shipment</td>
    
                <td  width="10%" colspan="4" class="td-title_border_btm">Arrival</td>
                
            </tr>
            <tr class="tr-title_">
                <td   class="td-title_left">No.</td>
                <td   class="td-title_left">PO.Number</td>
                <td   class="td-title_left">Description</td>
                <td   class="td-title_left">Vendor</td>
                <td   width="2%" class="td-title_left">Ccy</td>
                <td   width="3%" class="td-title">Amount</td>
                <td   width="3%" class="td-title">eqv. USD</td>
                <td   class="td-title_left">Mode</td>
                <td   class="td-title_left">Date</td>
                <td   class="td-title">by</td>
                <td   class="td-title_left">LSD</td>
                <!-- <td   class="td-title_left">ETD Dt</td> -->
                <td   class="td-title_left">Actual</td>
               <!--  <td   class="td-title_left">Harbour</td> -->
                <td   class="td-title_left">Transit</td>
                <td   class="td-title_left">ETA</td>
                <td   class="td-title_left">Doc.Ref.</td>
                <td   class="td-title_left">Remarks</td>
            </tr>
        </thead>
        <tfoot>
            <tr width="100%">
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
            </tr>
        </tfoot>
        <%
                    sn=1 
                    tot_usd=0
        %>
               
                <tr>
                    <td colspan="16" style="font-weight:bold;">${[key_department][0]}</td>
                <tr>
             <!-- %for key_po in sorted(result_group[key_department].keys(),key=lambda m:m[0]): -->
             %for key_po in sorted(result_group[key_department].keys(),key=lambda m:m):
                   <% 
                   
                     #print [key_department][0], key_po,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                     line=result_group[key_department][key_po]
                    %>
                <!-- %for lines in sorted(line,key=lambda m:m['name']): -->
                %for lines in line:
                    <%
                        #sorted(res,key=lambda m:m['po_id'])
                        # net_price=
                    get_usd=get_price_usd(lines['currency_idpo'],lines['company_curry_id'],lines['date_order'],lines['amount'])
                    %>
                <tr>
                    <td   class="td-details">${sn}</td>
                    <td   class="td-details">
                        %if lines['partner_alias']:
                            ${lines['partner_alias']}
                        %else:
                            ${key_po}
                            <!-- ${lines['name']} -->
                        %endif

                    </td>
                    <td   class="td-details">${lines['pending_itemdesc'] or ''}</td>
                    <td   class="td-details">${lines['vendor'] or ''}</td>
                    <td   width="2%" class="td-details">${lines['currency'] or ''}</td>
                    <td   width="3%" class="td-details-right">${formatLang(lines['amount'],digits=2)}</td>
                    <td   width="3%" class="td-details-right">${formatLang(get_usd,digits=2)}</td>
                    <td   class="td-details" style="text-transform:uppercase;">${lines['payment_method'] or ''} </td>
                    <td   class="td-details">${lines['payment_date'] or ''}</td>
                    <td   class="td-details">${lines['divy_by'] or ''}</td>
                    <td   class="td-details">${lines['lsd'] or ''}</td>
                    <td   class="td-details">${lines['actual_date'] or ''}</td>
                    <td   class="td-details">${lines['transit_date'] or ''}</td>
                    <td   class="td-details">
                        % if lines.get('transit_date',False) and lines.get('actual_date',False):
                            ${(datetime.strptime(lines['transit_date'], date_format)-datetime.strptime(lines['actual_date'], date_format)).days}
                        % elif lines.get('transit_date',False) and lines.get('lsd',False):
                            ${(datetime.strptime(lines['transit_date'], date_format)-datetime.strptime(lines['lsd'], date_format)).days}
                        % else:
                            &nbsp;
                        % endif
                    </td>
                    <td   class="td-details">${lines['document_ref'] or ''}</td>
                    <td   class="td-details">${lines['shipment_remarks'] or ''}</td>
                </tr>
                %endfor
                <%
                sn+=1
                tot_usd+=get_usd
                %>
            %endfor
               
                <tr class="tr-grandtotal">
                    <td colspan="4" class="td-grandtotal">&nbsp;</td>
                    <td colspan="2" class="td-grandtotal" style="text-align:right;">Sub Total Dept : </td>
                    <td colspan="1" class="td-grandtotal" style="text-align:right;">${formatLang(tot_usd,digits=2)}</td>
                    <td colspan="9" class="td-grandtotal" style="text-align:right;"></td>
                </tr>
        
            </tbody>
        
    </table>
  %endfor  
</body>
</html>