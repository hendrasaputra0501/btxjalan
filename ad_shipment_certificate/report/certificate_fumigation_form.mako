<html>
<head>
	<style>

	body {
		font-family: "Courier New", Courier, monospace;
		font-size: 10pt;
		width: 95%;
	}
	
	td {
		vertical-align: top;
	}
	
	.main-tab{
		border-collapse: collapse;
	}

	.main-tab tr {
		border: 1px solid;
	}

	.ins-tab {
		border: 0px;
	}

	</style>
</head>
<body>
<%
	from datetime import datetime
%>
% for obj in objects:
	% if obj.invoice_id:
		<% 
		date = datetime.strptime(obj.date_declaration,"%Y-%m-%d").strftime("%d.%m.%Y")
		o = obj.invoice_id
		label = get_label(o)
		%>
		<br/>
		<br/>
		<table width="100%" class="main-tab">
			<tr width="100%">
				<td width="100%">
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="15%">FAX</td>
							<td width="1%">:</td>
							<td width="84">${obj.fax or ''}</td>
						</tr>
						<tr>
							<td>TO</td>
							<td>:</td>
							<td>${obj.to or ''}</td>
						</tr>
						<tr>
							<td>ATTN</td>
							<td>:</td>
							<td>${obj.attn and obj.attn.upper() or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="15%">FROM</td>
							<td width="1%">:</td>
							<td width="84">${obj.source_person  and obj.source_person.upper() or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="15%">SN</td>
							<td width="1%">:</td>
							<td width="34">${obj.sn or ''}</td>
							<td width="5%">DT</td>
							<td width="1%">:</td>
							<td width="44">${date}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="15%">SUB</td>
							<td width="1%">:</td>
							<td width="84">${obj.fumigation_title or ''}</td>
						</tr>
					</table>
				</td>
			</tr>
			<tr>
				<td>
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="30%">&nbsp;</td>
							<td width="5%">&nbsp;</td>
							<td width="65">&nbsp;</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('shipper','SHIPPER')}</td>
							<td>:</td>
							<td>
							%if o.sale_ids and o.sale_ids[0].payment_method=="cash":
								PT BITRATEX INDUSTRIES</br>
								Menara Kadin Indonesia,12th Fl, </br>
								Jl HR Rasuna Said, Blok X-5 Kav 2&3, </br>
								Jakarta 12950, Indonesia
							%else:
								%if o.show_shipper_address==True:
									${o.s_address_text or ''} 
								% else:
									%if o.company_id and o.company_id.name:
										${o.company_id and o.company_id.name or ''} <br/>
									%endif
									%if o.company_id and o.company_id.street:
										${o.company_id and o.company_id.street or ''} <br/>
									%endif
									%if o.company_id and o.company_id.street2:
										${o.company_id and o.company_id.street2 or ''}  <br/>
									%endif
									%if o.company_id and o.company_id.city:
										${o.company_id and o.company_id.city or ''} </br>
									%elif o.company_id and o.company_id.zip and o.company_id and o.company_id.country_id and o.company_id.country_id.name:
										${o.company_id and o.company_id.zip or ''},${o.company_id and o.company_id.country_id and o.company_id.country_id.name or ''} </br>
									%endif
								%endif
							%endif
							</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('applicant','APPLICANT')}</td>
							<td>:</td>
							<td>${(o.c_address_text or '').replace('\n','<br/>')}</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('port_from','PORT OF LOADING')}</td>
							<td>:</td>
							<td>
							% if o.picking_ids and o.picking_ids[0].container_book_id and o.picking_ids[0].container_book_id.port_from_desc:
								${o.picking_ids[0].container_book_id.port_from_desc or ''}
							% elif o.picking_ids and o.picking_ids[0].container_book_id and o.picking_ids[0].container_book_id.port_from:
								${o.picking_ids[0].container_book_id.port_from.name or ''}
							% else:
								&nbsp;
							%endif
							</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('port_to','DESTINATION')}</td>
							<td>:</td>
							<td>
							% if o.picking_ids and o.picking_ids[0].container_book_id and o.picking_ids[0].container_book_id.port_to_desc:
								${o.picking_ids[0].container_book_id.port_to_desc or ''}
							% elif o.picking_ids and o.picking_ids[0].container_book_id and o.picking_ids[0].container_book_id.port_to:
								${o.picking_ids[0].container_book_id.port_to.name or ''}
							% else:
								&nbsp;
							%endif
							</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">CONTAINER NO.</td>
							<td>:</td>
							<td>
							<% 
							container_nos = [picking.container_number for picking in o.picking_ids if picking.container_number]
							%>
							${container_nos and "<br/>".join(set(container_nos)) or ""}
							</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('invoice','INVOICE NO.')}</td>
							<td>:</td>
							<td>
							${o.internal_number or o.number or ""}
							</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">${label.get('lc_number','L/C NO.')}</td>
							<td>:</td>
							<td>${ get_lc_number(o)}</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">TYPE OF WOOD PACKAGING</td>
							<td>:</td>
							<td>${obj.type_of_wood_packaging or ''}</td>
						</tr>
						<tr>
							<td style="padding-left:6px;">QUANTITY</td>
							<td>:</td>
							<td>
							<% 
								move_lines = []
								for line in o.invoice_line:
									if line.move_line_ids:
										move_lines += [move for move in line.move_line_ids if move.product_uop and move.product_uop.packing_type and move.product_uop.packing_type.name == 'Pallets']
								total_pallets = 0
								if move_lines:
									total_pallets = sum([move.product_uop_qty for move in move_lines])
							%>
							${total_pallets}
							</td>
						</tr>
					</table>
					<br/>
					<br/>
					<br/>
					<table width="100%" class="ins-tab">
						<tr width="100%">
							<td width="75%"></td>
							<td width="25" align="center">
								REGARDS,
								<br/>
								<br/>
								<br/>
								${obj.source_person and obj.source_person.upper() or ''}
							</td>
						</tr>
						<tr>
							<td>&nbsp;</td>
							<td>&nbsp;</td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
	% endif
% endfor
</body>
</html>
