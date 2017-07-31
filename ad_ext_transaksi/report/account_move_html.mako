<html>
<head>
    <style type="text/css">
        body {
              	font-family:Arial;
        }

        table #head {
        	width:100%;
        }
        .list_table0 {
			font-size:18px;
			#font-weight:bold;
			padding-top:10px;
			padding-bottom:10px;
			padding-right:15%;
			width:70%;
			border-collapse:collapse;
        	border-top:1px solid white;
        	border-bottom:1px solid white;
        	border-left:1px solid white;
		}
		.list_table1{
			width:100%;
			font-size:9px;
            border-collapse:collapse;
            /*border-left:1px solid black;*/
            /*border-top:1px solid black;*/
            /*border-bottom:1px solid black;*/
            /*border-right:1px solid black;*/
        }

        .list_table1 th{
            /*margin: 0 auto;*/
            border-left:.1px solid black;
            border-top:.1px solid black;
            border-bottom:.1px solid black;
            border-right:.1px solid black;
        }

		.list_table2 {
			font-size:10px;
		}
		.list_table3 {
			font-size:10px;
		}
		.list_table4 {
			font-size:10px;
			padding-top:5px;
			padding-bottom:5px;
		}
		.cust_info
			{
			font-size:10px;
			font-weight:bold;
			border-top:1px solid black;
			border-bottom:1px solid black;
			border-left:1px solid black;
			border-right:1px solid black;
			padding-top:6px;
			padding-bottom:6px;
			}
		.journal_item2
			{
			border-top:.5px solid black;
			}
    </style>
</head>
<body>
    %for move in objects :
    <% setLang(company.partner_id.lang) %>
    <table width="100%">
	<tr valign="top">
                <td width="100%" style="font-family:Arial Black;" colspan="4" style="font-size:12" align="center">
			PT. Bitratex Industries
            	</td>
        </tr>
    	<tr valign="top">
    		<td width="100%" style="font-family:Arial Black;" colspan="4" style="font-size:14" align="center"><u>
            % if move.journal_id and (move.journal_id.type=='bank' or move.journal_id.type=='cash'):
                CASH VOUCHER
            % else:
                JOURNAL VOUCHER
            % endif
            </u></td>
    	</tr>
    </table>
    <hr size="2px" color="white">
    <table width="100%">
    	<tr class="list_table1" style="font-family:Arial Black;">
    		<td width="65%">Number. ${move.name or ''|entity}</td>
    		<td width="10%"></td>
    		<td width="2%"></td>
    		<td width="23%"></td>
    	</tr>
    	<tr class="list_table1" style="font-family:Arial Black;">
    		<td width="65%">Jurnal. ${move.journal_id.name or ''|entity}</td>
    		<td width="10%">Tanggal</td>
    		<td width="2%">:</td>
    		<td width="23%">${time.strftime('%d %b %Y', time.strptime(move.date,'%Y-%m-%d')) or ''|entity}</td>
    	</tr>
    	<tr class="list_table1" style="font-family:Arial Black;">
    		<td width="65%">Referensi : ${move.ref or ''|entity}</td>
    		<td width="10%">Periode</td>
    		<td width="2%">:</td>
    		<td width="23%">${move.period_id.name or ''|entity}</td>
    	</tr>
    </table>
    <hr size="2px" color="white">

    <table class="list_table1" width="100%" cellpadding="3">
        <tr style="text-align:center;" style="font-family:Arial Black;">
            <th width="8%">${_("Account Code")}</th>
            <th width="17%">${_("Account Desc")}</th>
            <th width="10%">${_("Reference")}</th>
            <th width="8%">${_("Trans. Date")}</th>
            <th width="20%">${_("Desc")}</th>
            <th width="3%">${_("Curr")}</th>
            <th width="15%">${_("Trans. Amt")}</th>
            <th width="4%">${_("Rate")}</th>
            <th width="15%">${_("USD Amt")}</th>
        </tr>
        <%
        i = 1
        totdebit = total_amt_curr = 0
        %>
        %for line in get_move_lines(move.line_id):
            %if line['type_line']=='dr':
            <tr class='journal_item'>
                <td style="text-align:center;" valign="top">${line['account_code']|entity}</td>
                <td style="text-align:left;" valign="top">${line['account_name']|entity}</td>
                <td style="text-align:left;" valign="top">${line['referense']|entity}</td>
                <td style="text-align:center;" valign="top">${line['date_maturity']|entity}</td>
                <td style="text-align:left;" valign="top">${line['description']|entity}</td>
                <td style="text-align:center;" valign="top">${line['trans_currency']|entity}</td>
                <td style="text-align:right;" valign="top">${formatLang(abs(line['trans_amt']),digits=get_digits(dp='Account')) or 0.0}</td>
                <td style="text-align:right;" valign="top">${formatLang(line['rate_currency'],digits=get_digits(dp='Account')) or 0.0}</td>
                <td style="text-align:right;" valign="top">${line['debit']|entity}</td>
            </tr>
               <% total_amt_curr += abs(line['trans_amt']) %>
            %endif
            <%
            i=i+1
            totdebit += line['debit']
            %>
        %endfor
        
        <tr class='journal_item2'>
            <td style="text-align:left;" colspan="6"><b>Total DR</b></td>
            <td style="text-align:right;"><b>${ formatLang(total_amt_curr,digits=get_digits(dp='Account')) or 0}</b></td>
            <td style="text-align:right;"></td>
            <td style="text-align:right;"><b>${ formatLang(totdebit,digits=get_digits(dp='Account')) or 0}</b></td>
        </tr>
        <%
        i = 1
        totcredit = total_amt_curr = 0
        %>
        %for line in get_move_lines(move.line_id):
            %if line['type_line']=='cr':
            <tr class='journal_item'>
                <td style="text-align:center;" valign="top">${line['account_code']|entity}</td>
                <td style="text-align:left;" valign="top">${line['account_name']|entity}</td>
                <td style="text-align:left;" valign="top">${line['referense']|entity}</td>
                <td style="text-align:center;" valign="top">${line['date_maturity']|entity}</td>
                <td style="text-align:left;" valign="top">${line['description']|entity}</td>
                <td style="text-align:center;" valign="top">${line['trans_currency']|entity}</td>
                <td style="text-align:right;" valign="top">${formatLang(abs(line['trans_amt']),digits=get_digits(dp='Account')) or 0.0}</td>
                <td style="text-align:right;" valign="top">${formatLang(line['rate_currency'],digits=get_digits(dp='Account')) or 0.0}</td>
                <td style="text-align:right;" valign="top">${line['credit']|entity}</td>
            </tr>
               <% total_amt_curr += abs(line['trans_amt']) %>
            %endif
            <%
            i=i+1
            totcredit += line['credit']
            %>
        %endfor
        
        <tr class='journal_item2'>
            <td style="text-align:left;" colspan="6"><b>Total CR</b></td>
            <td style="text-align:right;"><b>${ formatLang(total_amt_curr,digits=get_digits(dp='Account')) or 0}</b></td>
            <td style="text-align:right;"></td>
            <td style="text-align:right;"><b>${ formatLang(totcredit,digits=get_digits(dp='Account')) or 0}</b></td>
        </tr>
    </table>

    %endfor
   <br/><br/>
   <table class="list_table1" border="1" style="border-collapse:collapse;" width="100%" cellpadding="3">
        <tr style="text-align:center;">
            <td width="25%">Prepared By</td>
            <td width="25%">Checked By</td>
            <td width="25%">Approved By</td>
            <td width="25%">Received By</td>
        </tr>
        <tr>
            <td style="text-align:center;"><br/><br/><br/><br/></td>
            <td style="text-align:center;"></td>
            <td style="text-align:center;"></td>
            <td style="text-align:center;"></td>
        </tr>
    </table>    
</body>
</html>
