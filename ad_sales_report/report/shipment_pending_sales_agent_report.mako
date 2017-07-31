<html>
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type"/>
	<style type="text/css">
		td {
		    word-break: break-all;
		}
		body {
		  font-family: "times new roman";
		}
		.title1 {
		    text-transform:uppercase;
		    font-size: 15px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.title2 {
		    font-size: 12px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.title3 {
		    font-size: 10px;
		    font-weight: bold;
		    vertical-align:middle;
		    height: 1px;
		}
		.header1{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    border-bottom: 1px solid #000000;
		    height: 1px;
		}
		.header2{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    border-bottom: 1px dotted #000000;
		    height: 1px;
		}
		.header3{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px solid #000000;
		    height: 1px;
		}
		.header4{
		    font-size:9px;
		    font-weight: bold;
		    border-top: 1px solid #000000;
		    height: 1px;
		}
		.detail{
		    font-size: 8px;
		    vertical-align:top;
		    height: 1px;
		}
		.detailcap{
		    text-transform:uppercase;
		    font-size: 8px;
		    vertical-align:top;
		    height: 1px;
		}
		.group{
		    font-weight: bold;
		    font-size: 9px;
		    vertical-align:top;
		    height: 1px;
		}
		.space{
		    font-size: 6px;
		    height: 1px;
		}
		.subtotal{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px dotted #000000;
		    vertical-align:middle;
		    height: 1px;
		}
		.grandtotal{
		    font-size:9px;
		    font-weight: bold;
		    border-bottom: 1px solid #000000;
		    vertical-align:middle;
		    height: 1px;
		}
		h2 {
		    font-size: 6px;
		    height: 1px;
			page-break-before: always;
		}
		
		
	</style>
</head>
	<body style='border:0; margin: 0;'>
        <%uom_base_name = get_uom_base(data)%>
       
			<%
				
				grand_uom_base_qty = 0
				grand_amount=0
				
				result_grouped={}
				for details in get_view(data):
					key1_agent=details['agent']
					if key1_agent not in result_grouped:
						result_grouped.update({key1_agent:{}})
					# print key1_agent,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
					key2_customer=details['cust_name']
					if key2_customer not in result_grouped[key1_agent]:
						result_grouped[key1_agent].update({key2_customer:{}})
					# print key2_customer	,"hahahahahaha"
					key3_rpt_group=details['report_group']
					if key3_rpt_group not in result_grouped[key1_agent][key2_customer]:
						result_grouped[key1_agent][key2_customer].update({key3_rpt_group:{}})
						# group_name=None
						# if key3_rpt_group==1:
						# 	group_name="SHIPMENTS:"
						# if else key3_rpt_group==2:
						# 	group_name="PENDING ORDERS:"
						# else:
							# group_name="none"
					# print key3_rpt_group,"xaxaxaxaxaxaxaxaxaxaxa"
					key4_curr=details['curr_name']
					if key4_curr not in result_grouped[key1_agent][key2_customer][key3_rpt_group]:
						result_grouped[key1_agent][key2_customer][key3_rpt_group].update({key4_curr:[]})
					# print key4_curr,"nininininininininininin"
					result_grouped[key1_agent][key2_customer][key3_rpt_group][key4_curr].append(details)
					# print result_grouped[key1_agent][key2_customer][key3_rpt_group],"jajajajajajajajajajajajajaja"
					agent_qty=0
					agent_amount=0
					
				# len_agen=len(key1_agent)
				# print len_agen,"gaggsagagsgggagsgagagsgaggsgsgagagsgsgagsgsgagagsgsggagsgs"
			%>
			<% no=0 %>
			%for key_agen in sorted(result_grouped.keys(),key=lambda l:l):
			
				<% 
				 no=no+1
				 # print no,"lalilalilalilalilalilalilalilalilalilalilalilalilalilalilali"
				%>
				<table  width='100%' cellspacing='0' cellpadding='1'>
					<tr>
					 
						<td colspan="22" class='group' align='left' >${key_agen or ''}</td>
					</tr>
				</table>
					<%
					cust_qty=0
					cust_amount=0
					no_cust=0
					%>
				%for key_customer in sorted(result_grouped[key_agen].keys(),key=lambda m:m):
					<!-- lines = sorted(result_grouped[key_agent][key_customer], key=lambda x:x[0]) -->
					<%
					no_cust=no_cust+1
					%>
				<table width='100%' cellspacing='0' cellpadding='1'>
					<tr class='group' >
						<td class='group' align='left'>&nbsp;</td>
						<td colspan="21" class='group' align='left'>${key_customer}</td>
					</tr>
					<%
					report_qty=0
					report_amount=0
					%>

					%for key_rpt_group in sorted(result_grouped[key_agen][key_customer].keys(), key=lambda n:n):
						<% report_name="None" %>
						%if key_rpt_group==1:
							<% report_name="SHIPMENT :" %>
						%elif key_rpt_group==2:
							<% report_name="PENDING ORDERS:" %>
						%elif key_rpt_group==3:
							<% report_name = "AMMENDED ORDERS:" %>
						%else:
							<% report_name = "CANCELLED ORDERS:" %>
						%endif			
						<tr class='group' >
							<td class='group' align='left'>&nbsp;</td>
							<td class='group' align='left'>&nbsp;</td>
							<td colspan="20" class='group' align='left'>${report_name}</td>
						</tr>
						<%
							cury_qty=0
							cury_amount=0
						%>
						%for key_curr in sorted(result_grouped[key_agen][key_customer][key_rpt_group].keys(), key=lambda o:o):

							<tr class='group' >
								<td class='group' align='left'>&nbsp;</td>
								<td class='group' align='left'>&nbsp;</td>
								<td colspan="10" class='group' align='left'>${key_curr}</td>
							</tr>
								<% 
									lines= sorted(result_grouped[key_agen][key_customer][key_rpt_group][key_curr],key=lambda x:x['lc_no']) 
								%>
							<!-- % for k in sorted(line_cr_summary.keys(), key=lambda k:(k[1],k[0])): -->
							 % for line in sorted(lines, key=lambda line:(line['invc_no'],line['invc_dt'],line['sc_no'],line['sc_date'])):
									<tr class='detail'>
						               	<td class='detail' width='1%' align='left'>&nbsp;</td>
						               	<td class='detail' width='1%' align='left'>&nbsp;</td>
						               	<td class='detail' width='1%' align='left'>&nbsp;</td>
										<td class='detailcap' width='6%' align='left'>${line['sc_no']}</td>
										<td class='detail' width='4%' align='left'>${line['sc_date']}</td>
										<td class='detailcap' width='9%' align='left'>${line['prod_name']}</td>
										<td class='detailcap' width='7%' align='left'>${line['destination']}</td>
										<td class='detailcap'  width='3%' align='left'>${line['curr_name']}</td>
										<td class='detailcap'   width='3%' align='right'>${formatLang(line['uom_base_price_unit'],digits=2)}</td>
										<td class='detailcap' width='3%' align='left'>${line['lc_terms']}</td>
										<td class='detailcap' width='9%' align='left'>${line['lc_no']}</td>
										<td class='detail'  width='5%' align='right'>${formatLang(line['uom_base_qty'] or 0.00,dp='Product Unit of Measure')}</td>
										<td class='detail' width='5%' align='right'>${formatLang(line['amount'] or 0.00,dp='Account')}</td>
										<td class='detail' width='7%' align='left'>${line['delivery']}</td>
										<td class='detailcap' width='5%' align='left'>${line['invc_no']}</td>
										<td class='detail' width='4%' align='left'>${line['invc_dt']}</td>
										<td class='detailcap' width='5%' align='left'>${line['container']}</td>
										<td class='detailcap' width='7%' align='left'>${line['bl_no']}</td>
										<td class='detail' width='4%' align='left'>${line['bl_dt']}</td>
										<td class='detail' width='4%' align='left'>${line['eta']}</td>
										<td class='detail' width='3%' align='left'>${line['lot_no']}</td>
					                    <td class='detail' width='4%' align='left'>${line['tpi']}</td>
									</tr>
									<%
									cury_qty=cury_qty+line['uom_base_qty']
									cury_amount=cury_amount+line['amount']
									 %>
							%endfor
							<tr class='group' >
								<td class='group' align='left'>&nbsp;</td>
								<td class='group' align='left'>&nbsp;</td>
								<td colspan="9" class='subtotal' align='left'>Total of ${key_curr}</td>
								<td class='subtotal' align='right'>${formatLang(cury_qty or 0.00,dp='Product Unit of Measure')}</td>
								<td class='subtotal' align='right'>${formatLang(cury_amount or 0.00,dp='Account')}</td>
								<td colspan="9" class='subtotal' align='left'>&nbsp;</td>
							</tr>
									<%
									report_qty=report_qty+cury_qty
									report_amount=report_amount+cury_amount
									 %>
						%endfor
						<tr class='group' >
							<td class='group' align='left'>&nbsp;</td>
							<td class='group' align='left'>&nbsp;</td>
							<td colspan="9" class='subtotal' align='left'>Total of ${report_name}</td>
							<td class='subtotal' align='right'>${formatLang(report_qty or 0.00,dp='Product Unit of Measure')}</td>
							<td class='subtotal' align='right'>${formatLang(report_amount or 0.00,dp='Account')}</td>
							<td colspan="9" class='subtotal' align='left'>&nbsp;</td>
						</tr>

							<%
								cust_qty=cust_qty+report_qty
								cust_amount=cust_amount+report_amount
							%>
					%endfor
					<tr class='group' >
						<td class='group' align='left'>&nbsp;</td>
						<td colspan="10" class='subtotal' align='left'>Total of ${key_customer}</td>
						<td class='subtotal' align='right'>${formatLang(cust_qty or 0.00,dp='Product Unit of Measure')} </td>
						<td class='subtotal' align='right'>${formatLang(cust_amount or 0.00,dp='Account')}</td>
						<td colspan="9" class='subtotal' align='left'>&nbsp;</td>
					</tr>
				</table>
						<%
							agent_qty=agent_qty+cust_qty
							agent_amount=agent_amount+cust_amount
						%>
						<%
							len_cust= len(result_grouped[key_agen].keys())
							# print no_cust,"nobobobobobnonononononono"
							# print len_cust,"bababababababababababababbababababababababababababababababa"
						%>
						%if no_cust!=len_cust:
							<h2>&nbsp;</h2>
						%endif
				%endfor
			<table width='100%' cellspacing='0' cellpadding='1'>
				<tr class='group'>
					<td class='subtotal' align='left' colspan='11'> Total Agent of ${key_agen or ''}</td>
					<td class='subtotal' width='6%' align='right'>${formatLang(agent_qty or 0.00,dp='Product Unit of Measure')} </td>
					<td class='subtotal'width='6%' align='right'>${formatLang(agent_amount or 0.00,dp='Account')} </td>
					<td colspan="9" class='subtotal'  width='42%' align='right' colspan='9'>&nbsp;</td>

				</tr>
				<!-- <tr style="page-break-inside:avoid; page-break-after:auto;"><td colspan="22">&nbsp;</td></tr> -->
				<%
				grand_uom_base_qty = grand_uom_base_qty+agent_qty
				grand_amount=grand_amount+agent_amount
				%>
			</table>
			<%
				len_agen= len(result_grouped.keys())
				# print len_agen,"bababababababababababababbababababababababababababababababa"
			%>
			%if no!=len_agen:
				<h2>&nbsp;</h2>
			%endif
			%endfor
			
			<table  width='100%' cellspacing='0' cellpadding='1'>

				<tr>
					<td class='grandtotal' width:'46%' align='left' colspan='11'>GRAND TOTAL</td>
					<td class='grandtotal'   width='6%' align='right'>${formatLang(grand_uom_base_qty or 0.0,dp='Product Unit of Measure')}</td>
					<td class='grandtotal'   width='6%' align='right'>${formatLang(grand_amount or 0.0,dp='Account')}</td>
					<td class='grandtotal' width='42%' align='right' colspan='9'>&nbsp;</td>
				</tr>
			</table>		
		
	</body>
</html>