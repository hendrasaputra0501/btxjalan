<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<!--
<% import base64 %>
<% import mx.DateTime %>
<% import time %>
<% from datetime import datetime %>
<%
def oe_datetime_format(obj,format='%Y-%m-%d %H:%M:%S'):
    if obj.val:
        if hasattr(obj,'name') and (obj.name):
            return mx.DateTime.strptime(obj.name,format)
%>
-->
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>INVENTORY ISSUE (OPENERP)</title>
        <style type="text/css">
            body {
                margin: 0px;
                padding: 0px;
                font-size: 10px;
                font-family: "Arial";
                text-transform: uppercase;
            }
            .head11 {
                display: block;
                text-align: center;
                font-size: 14px;
                font-family: "Arial";
            }
            .head12 {
                /*display: block;
                text-align: center;
                font-size: 22px;
                text-decoration: underline;
                font-family: "Arial";*/

                 text-align: center;
                font-weight: bold;
                font-size: 15px;
                margin-top:5px;
                /*border-bottom:1px solid;*/
            }

            .head13 {
                /*display: block;
                text-align: center;
                font-size: 22px;
                text-decoration: underline;
                font-family: "Arial";*/

                 text-align: center;
                font-weight: bold;
                font-size: 10px;
                /*margin-top:5px;*/
                /*border-bottom:1px solid;*/
            }

            .head2 {
                display: block;
                /*margin-top: -42px;*/
            }

            .hdr2{
                text-align: center;
                /*font-weight: bold;*/
                font-size: 11px;
                /*margin-top:40px;*/
            }
            table {
                border-collapse: collapse;
                margin: 0px;
                padding: 0px;
            }
            .fix-tab {
                table-layout: fixed;
            }
            .main-tab {
                border: 0px; 
            }
            
            .main-tab2 {
                border: .1px solid;
                padding: 5px;
                width: 100%;
                margin-top:50px;
            }
            .main-tab2 th {
                border-top: .1px solid;
                border-bottom: .1px solid;
                padding: 5px;
                /*vertical-align: top; */
            }
            .main-tab2 td {
                padding: 3px 3px 0px 3px;
                /*vertical-align: top; */
            }

            .tengah {
                text-align: center;
            }
            .kanan {
                text-align: right;
            }
        </style>
    </head>
    <body>
        <div class="hdr2">
        <a>PT. BITRATEX INDUSTRIES</a><br/>
    </div>
        % for o in objects:
        %if o.manual_issue:
            <div class="head12"><a style="border-bottom:1px solid;">MANUAL INVENTORY ISSUE</a></div>
        %else:
            <div class="head12"><a style="border-bottom:1px solid;">INVENTORY ISSUE</a></div>
        %endif
        % if o.goods_type=='stores':
            <div class="head13"><a>${o.issue_state and (o.issue_state=='draft_department' and 'Draft Issue' or 'Approved Issue') or 'Not Valid'}</a></div>
        % endif
        <div class="head2">
            &nbsp;<br />
            <div style="float: left;">
                <table class="fix-tab main-tab">
                    <tr>
                        <td>Whse. Loc</td>
                        <td>:</td>
<%
    src_location = [(m.location_id and m.location_id.name or '') for m in o.move_lines][0]
%>
                        <td>${src_location}</td>
                    </tr>
                    <tr>
                        <td>Class Id</td>
                        <td>:</td>
                        <td>
                            %if o.goods_type=="packing":
                                Packing Material
                            %elif o.goods_type=="finish":
                                Finish Goods
                            %elif o.goods_type=="finish_others":
                                Finish Goods(others)
                            %elif o.goods_type=="raw":
                                Raw Material
                            %elif o.goods_type=="service":
                                Services
                            %elif o.goods_type=="stores":
                                Stores
                            %elif o.goods_type=="waste":
                                Waste
                            %elif o.goods_type=="scrap":
                                Scrap
                            %elif o.goods_type=="asset":
                                Fixed Asset
                            %endif
                        </td>
                    </tr>
                    <tr>
                        <td>Dept. Id</td>
                        <td>:</td>
<%
    dept_location = [(m.location_dest_id and m.location_dest_id.location_id and m.location_dest_id.location_id.name or '') for m in o.move_lines][0]
%>
                        <td>${dept_location}</td>
                    </tr>
                </table>
            </div>
            <div style="float: right;">
                <table class="fix-tab main-tab">
                    <tr>
                        <td>ISSUE PASS NO.</td>
                        <td>:</td>
                        <td>${o.name or ''}</td>
                    </tr>
                    <tr>
                        <td>ISSUE PASS DATE</td>
                        <td>:</td>
<%
    issue_date = o.date_done!='False' and datetime.strptime(formatLang(o.date_done,date_time=True), '%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y') or ''
%>
                        <td>${formatLang(o.date, date=True)}</td>
                    </tr>
                    <tr>
                        <td>REF. NO.</td>
                        <td>:</td>
                        <td>${o.origin or ''}</td>
                    </tr>
                    <tr>
                        <td>IR NO.</td>
                        <td>:</td>
                        <td>${o.material_req_id and o.material_req_id.name or '-'}</td>
                    </tr>
                    <tr>
                        <td>IR DATE</td>
                        <td>:</td>
                        <td>${o.material_req_id and o.material_req_id.date_start or '-'}</td>
                    </tr>
                </table>
            </div>
        </div>

        <% 
        secqty_nonzero = false
        secqty = 0.0 
        move_lines = get_move_lines(o)
        %>
        % for key in move_lines:
            <% secqty += move_lines[key][0]['qty2'] %>
        % endfor
        %if secqty != 0.0 :
            <% secqty_nonzero = true %>
        %endif
        <table class="fix-tab main-tab2">
            <thead>
                <tr>
                    <th width="3%">SR<br />NO</th>
                    <th width="10%">ITEM CODE</th>
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <th width="15%">DESCRIPTION</th>
                    %else:
                        <th width="21%">DESCRIPTION</th>
                    %endif
                    <th width="3%">TRAN<br />DATE</th>
                    <th width="5%">DEST<br />LOC</th>
                    <th width="5%">SOURCE<br />LOC</th>
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type:
                    <th width="5%">SECOND<br />UOM</th>
                    %endif
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <th width="6%">SECOND<br />QTY</th>
                    %endif
                    <th width="4%">UOM</th>
                    %if o.goods_type not in ["finish","raw"]  and o.goods_type:
                        <th width="6%">PRICE</th>
                    %endif
                    <th width="5%">QTY<br />ISSUED</th>
                    %if o.goods_type not in ["finish","raw"]  and o.goods_type:
                     <th width="6%">EXTENDED COST</th>
                    %endif
                    %if o.goods_type not in ["stores"]:
                    <th width="6%">QTY<br />IN BALE</th>
                    %endif
                    <th width="5%">QTY ON<br />HAND</th>
                    <th width="6%">ANALYTIC<br />ACCOUNT</th>
                    <th width="5%">REASON<br />CODE</th>
                    %if o.goods_type not in ["stores"]:
                    <th width="5%" style='text-align: center;'>LOT<br />NO</th>
                    %endif
                    <th width="6%">REMARKS</th>
                </tr>
            </thead>
            <tbody>
                <%
                tot = 0.0
                tot1 = 0.0
                tot2 = 0.0
                tot3 = 0.0
                tot4 = 0.0
                #totvol = 0.0
                index = 0
                move_lines = get_move_lines(o)
                nkey = 0
                %>
                % for key in move_lines:
                    <%
                    subtotal = 0.0
                    subtotal1 = 0.0
                    subtotal2 = 0.0
                    subtotal3 = 0.0
                    subtotal4 = 0.0
                    nkey += 1
                    %>
                <tr valign="top"> 
                 <!-- %if o.goods_type!="finish":   -->
                
                 %if move_lines[key][0]['goods_type'] not in ["finish","raw","stores"] and move_lines[key][0]['goods_type']:
                    <td align="left" colspan='16'><b>${key[1]}</b></td>
                %elif move_lines[key][0]['goods_type'] in ["stores"]:
                    <td align="left" colspan='14'><b>${key[1]}</b></td>    
                %else:
                    <td align="left" colspan='15'><b>${key[1]}</b></td>
                %endif
                </tr>
                    % for move in sorted(move_lines[key],key=lambda k:k['sequence']):
                        <% index+=1 %>
                <tr valign="top">   
                    <td class="tengah">${index}</td>
                    <td>${ move['code'] }</td>
                    <td>${ move['desc'] }
                        <!-- <br/> -->
                        <!-- Lot No. &nbsp; ${ move['lot'] or '-' } -->
                        <!-- &nbsp;
                        Reason Code : &nbsp; ${move['reasoncode'] or '-'} -->
                       <!--  &nbsp;
                        Analytic Account : &nbsp; ${move['analytic_account'] or '-'} -->
                    </td>
                    <td class="tengah">${ move['trans_date'] }</td>
                    <td class="tengah">${ move['site_loc'] }</td>
                    <td class="tengah">${ move['source_loc'] }</td>
                    %if o.goods_type in ["finish","raw"] or not o.goods_type:
                        <td class="tengah">${ move['uop'] }</td>
                    %endif
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <td class="kanan">${ formatLang(move['qty2'],digits=2) }</td>
                    %endif
                    <td class="tengah">${ move['uom'] }</td>
                    %if move['goods_type'] not in ["finish","raw"] and move['goods_type']:
                        <td class="kanan">${ formatLang(move['price_unit'],digits=4) }</td>
                    %endif
                    <td class="kanan">${ formatLang(move['qty1'],digits=2) }</td>
                     %if move['goods_type'] not in ["finish","raw"] and move['goods_type']:
                        <td class="kanan">${ formatLang(move['price_unit']*move['qty1'],digits=2) }</td>
                    %endif
                    %if move['goods_type'] not in ["stores"]:
                    <td class="kanan">${ formatLang(move.get('qty_bale',False) and move['qty_bale'],digits=2) or '' }</td>
                    %endif
                    <td class="kanan">${ formatLang(move.get('qty_onhand',False) and move['qty_onhand'],digits=2) or '' }</td>
                    <td class="tengah">${move['analytic_account']  or '-'}</td>
                    <td>${move['reasoncode']  or '-'}</td>
                    %if move['goods_type'] not in ["stores"]:
                     <td>${move['lot']  or '-'}</td>
                     %endif
                    <td>${move['remarks']  or ''}</td>
                </tr>
                        <%
                        subtotal += move['qty2']
                        subtotal1 += move['qty1']
                        subtotal2 += move.get('qty_bale',False) and move['qty_bale'] or 0.0
                        if move['goods_type'] not in ["finish","raw"] and move['goods_type']:
                            subtotal3 +=move['price_unit']*move['qty1']
                        subtotal4 += move.get('qty_onhand',False) and move['qty_onhand'] or 0.0
                        %>
                    % endfor
                <tr style="border-top: .1px solid black;">
                    <td width="3%"></td>
                    <td width="10%"></td>
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <td width="15%"></td>
                    %else:
                        <td width="21%"></td>
                    %endif
                    <td width="3%"></td>
                    <td width="5%"></td>
                    <td width="5%"></td>
                    %if o.goods_type in ["finish","raw"] or not o.goods_type:
                    <td width="5%"></td>
                    %endif
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <td width="6%" class="kanan">${ formatLang(subtotal,digits=2) }</td>
                    %endif
                    <td width="4%"></td>
                    %if o.goods_type not in ["finish","raw"] and o.goods_type:
                    <td width="6%"></td>
                    %endif
                    <td width="5%" class="kanan">${ formatLang(subtotal1,digits=2) }</td>
                    %if o.goods_type not in ["finish","raw"] and o.goods_type:
                    <td width="6%" class="kanan">${ formatLang(subtotal3,digits=2) }</td>
                    %endif
                    %if o.goods_type not in ["stores"]:
                    <td width="6%" class="kanan">${ formatLang(subtotal2,digits=2) }</td>
                    %endif
                    <td width="5%" class="kanan">${ formatLang(subtotal4,digits=2) }</td>
                    <td width="6%"></td>
                    <td width="5%"></td>
                    %if o.goods_type not in ["stores"]:
                    <td width="5%"></td>
                    %endif
                    <td width="6%"></td>
                </tr>
                    <%
                    tot+=subtotal
                    tot1+=subtotal1
                    tot2+=subtotal2
                    if o.goods_type not in ["finish","raw"] and o.goods_type :
                        tot3+=subtotal3
                    tot4+=subtotal4
                    %>
                %endfor

                %if nkey > 1:
                <tr style="border-top: .1px solid black;">
                    <td width="3%"></td>
                    <td width="10%"></td>
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <th width="15%"></th>
                    %else:
                        <th width="21%"></th>
                    %endif
                    <td width="3%"></td>
                    <td width="5%"></td>
                    <td width="5%"></td>
                    %if o.goods_type in ["finish","raw"] or not o.goods_type:
                    <td width="5%"></td>
                    %endif
                    %if o.goods_type in ["finish","raw"]  or not o.goods_type or secqty_nonzero:
                        <td width="6%" class="kanan">${ formatLang(tot,digits=2) }</td>
                    %endif
                    <td width="4%"></td>
                    %if o.goods_type not in ["finish","raw"] and o.goods_type:
                        <td width="6%"></td>
                    %endif
                    <td width="5%" class="kanan">${ formatLang(tot1,digits=2) }</td>
                    %if o.goods_type not in ["finish","raw"] and o.goods_type:
                    <td width="6%" class="kanan">${ formatLang(tot3,digits=2) }</td>
                    %endif
                    %if o.goods_type not in ["stores"]: 
                    <td width="6%" class="kanan">${ formatLang(tot2,digits=2) }</td>
                    %endif
                    <td width="5%" class="kanan">${ formatLang(tot4,digits=2) }</td>
                    <td width="6%"></td>
                    <td width="5%"></td>
                    %if o.goods_type not in ["stores"]:
                    <td width="5%"></td>
                    %endif
                    <td width="6%"></td>
                </tr>
                %endif
            </tbody>
        </table>
        <!-- <hr /> -->
        <!-- <div>Note :<br />
            <% note = o.note or '' %>
            ${ note.replace('\n','<br/>') or '' }
        </div> -->
        % endfor
        <br/> <br/> <br/>
        <table border="0" width="60%">
            <tr>
                <td width="33%" >Approved By : </td>
                <td width="33%" >Issued By : </td>
                <td width="33%" >Receipt By : </td>
            </tr>
            <tr>
                <td height="75px" valign="bottom">Entry By : </td>
            </tr>
        </table>
    </body>
</html>
