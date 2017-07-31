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
        <title>DEPARTEMENT RETURN(OPENERP)</title>
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
        <div class="head12"><a style="border-bottom:1px solid;">DEPARTMENT RETURN</a></div>
        % for o in objects:
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
                        <td>RECEIPT NO.</td>
                        <td>:</td>
                        <td>${o.name or ''}</td>
                    </tr>
                    <tr>
                        <td>RECEIPT DATE</td>
                        <td>:</td>
<%
    issue_date = o.date_done!='False' and datetime.strptime(formatLang(o.date_done,date_time=True), '%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y') or ''
%>
                        <td>${issue_date}</td>
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
        <table class="fix-tab main-tab2">
            <thead>
                <tr>
                    <th width="3%">SR<br />NO</th>
                    <th width="10%">ITEM CODE</th>
                    <th width="39%">DESCRIPTION</th>
                    <th width="5%">TRAN<br />DATE</th>
                    <th width="7%">SOURCE<br />LOC</th>
                    <th width="7%">DEST<br />LOC</th>
                    <!-- <th width="4%">SECOND<br />UOM</th> -->
                    <!-- <th width="6%">SECOND<br />QTY</th> -->
                    <th width="4%">UOM</th>
                    <th width="7%">QTY<br />RECEIPT</th>
                    <!-- <th width="7%">QTY<br />IN BALE</th> -->
                    <th width="18%">REMARKS</th>
                </tr>
            </thead>
            <tbody>
                <%
                tot = 0.0
                tot1 = 0.0
                tot2 = 0.0
                #totvol = 0.0
                index = 0
                move_lines = get_move_lines(o)
                %>
                
                    % for key in move_lines:
                        <%
                        subtotal = 0.0
                        subtotal1 = 0.0
                        subtotal2 = 0.0
                        %>
                    <tr valign="top">   
                        <td align="left" colspan='9'><b>${key[1]}</b></td>
                    </tr>
                        % for move in sorted(move_lines[key],key=lambda k:k['sequence']):
                        <%
                        #     print move['receipt_name'][1:2],"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
                        # %if move['usage']=='inventory' or (move['usage']=='internal' and move['receipt_name'][1]=='BI'):
                        %>
                            <% index+=1 %>
                    <tr valign="top">   
                        <td class="tengah">${index}</td>
                        <td>${ move['code'] }</td>
                        <td>${ move['desc'] }
                            <br/>
                            Lot No. &nbsp; ${ move['lot'] or '-' }
                            &nbsp;
                            Reason Code : &nbsp; ${move['reasoncode'] or '-'}
                            &nbsp;
                            Analytic Account : &nbsp; ${move['analytic_account'] or '-'}
                        </td>
                        <td class="tengah">${ move['trans_date'] }</td>
                        <td class="tengah">${ move['source_loc'] }</td>
                        <td class="tengah">${ move['site_loc'] }</td>
                        <!-- <td class="tengah">${ move['uop'] }</td> -->
                        <!-- <td class="kanan">${ move['qty2'] }</td> -->
                        <td class="tengah">${ move['uom'] }</td>
                        <td class="kanan">${ formatLang(move['qty1'],digits=2) }</td>
                        <!-- <td class="kanan">${ move.get('qty_bale',False) and move['qty_bale'] or '' }</td> -->
                        <td>${move['remarks']  or ''}</td>
                    </tr>
                            <%
                            subtotal += move['qty2']
                            subtotal1 += move['qty1']
                            subtotal2 += move.get('qty_bale',False) and move['qty_bale'] or 0.0
                        # %endif
                            %>
                        % endfor
                    <tr style="border-top: .1px solid black;">
                        <td width="3%"></td>
                        <td width="10%"></td>
                        <td width="39%"></td>
                        <td width="5%"></td>
                        <td width="7%"></td>
                        <td width="7%"></td>
                        <!-- <td width="5%"></td> -->
                        <!-- <td width="7%" class="kanan">${ subtotal }</td> -->
                        <td width="4%"></td>
                        <td width="7%" class="kanan">${ formatLang(subtotal1,digits=2) }</td>
                        <!-- <td width="7%" class="kanan">${ subtotal2 }</td> -->
                        <td width="8%"></td>
                    </tr>
                        <%
                        tot+=subtotal
                        tot1+=subtotal1
                        tot2+=subtotal2
                        %>
                    %endfor
               
                <tr style="border-top: .1px solid black;">
                   <td width="3%"></td>
                    <td width="10%"></td>
                    <td width="39%"></td>
                    <td width="5%"></td>
                    <td width="7%"></td>
                    <td width="7%"></td>
                    <!-- <td width="5%"></td> -->
                    <!-- <td width="7%" class="kanan">${ tot }</td> -->
                    <td width="4%"></td>
                    <td width="7%" class="kanan">${formatLang(tot1,digits=2)}</td>
                    <!-- <td width="7%" class="kanan">${ tot2 }</td> -->
                    <td width="8%"></td>
                </tr>
            </tbody>
        </table>
        <!-- <hr /> -->
        <!-- <div>Note :<br />
            <% note = o.note or '' %>
            ${ note.replace('\n','<br/>') or '' }
        </div> -->
        % endfor
        <table border="0" width="60%">
            <tr>
                <td width="33%" >Approved By : </td>
                <td width="33%" >Entry By : </td>
                <td width="33%" ></td>
            </tr>
            <tr>
                <td height="75px" valign="bottom"></td>
            </tr>
        </table>
    </body>
</html>
