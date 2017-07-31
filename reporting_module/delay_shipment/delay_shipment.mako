<html>
	<head>
	<style type='text/css'>
		body {
                font-size:5px;
                font-family:'calibri';
                margin: 0px;
                padding: 0px;
                /* text-transform: uppercase;
                font-weight: 900; */
            }
            table {
            	font-size:5px;
                font-family:'calibri';
            	width: 100%;
                border-collapse: collapse;
                margin: 0px;
                padding: 0px;
            }
            .header{
                border-top:1px solid black;
                border-bottom:1px solid black;
                padding:5px;
                text-align:center;
            }
            .header-td1{
                border-top:1px dashed black;
                border-bottom:1px solid black;
            }
            .header-td2{
                text-align:center;
                border-bottom:1px solid black;
            }


        </style>
        </head>

        <body>
            <center>PT. BITRATEX INDUSTRIES <br> FORM 201502 TO 201502</center>
        <table class="main-tab">
            <tr class="header">
                <td width="10%" rowspan="2">ITEM CODE</td>
                <td width="10%" rowspan="2">DESCRIPTION</td>
                <td width="10%" rowspan="2">CONTRACT <br> NO.</td>
                <td width="10%" rowspan="2">CUSTOMER</td>
                <td width="10%" colspan="2"> L/C </td>
                <td width="10%" colspan="3"> DELIVERY DATES AS PER</td>
                <td width="10%" colspan="2"> DELAY AS PER </td>
                <td width="10%" rowspan="2"> A/G </td>
                <td width="10%" rowspan="2"> REASON CODE </td>
                <td width="10%" rowspan="2"> REMARKS </td>
            </tr>
            <tr>
                <td class="header-td1">BATCH</td>
                <td class="header-td1">NO.</td>
                <td class="header-td1">CONTRACT</td>
                <td class="header-td1">L/C</td>
                <td class="header-td2">SHIPPED</td>
                <td class="header-td2">CONTRACT</td>
                <td class="header-td1">L/C</td>
            </tr>
            %for o in get_objects(data):
                <tr class="body-1" align="center">
                    <td>${o.product_id.default_code or ''}</td>
                    <td>${o.product_id.name or ''}</td>
                    <td>${o.sale_line_id.order_id.name or ''}</td>
                    <td>${o.sale_line_id.order_id.partner_id.name or ''}</td>
                    <td>${o.lc_product_line_id and o.lc_product_line_id.lc_id and o.lc_product_line_id.lc_id.lc_number or ''}</td>
                    <td>${o.lc_product_line_id and o.lc_product_line_id.lc_id and o.lc_product_line_id.lc_id.name or ''}</td>
                    <td>${o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date or ''}</td>
                    <td>${o.lc_product_line_id.est_delivery_date or ''}</td>
                    <td>${o.date or o.picking_id.date_done or ''}</td>
                    <td>${get_difference(o.sale_line_id.est_delivery_date or o.sale_line_id.order_id.max_est_delivery_date,o.date or o.picking_id.date_done)}</td>
                    <td>${get_difference(o.lc_product_line_id.est_delivery_date,o.date or o.picking_id.date_done)}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
            %endfor
        </table>
    </body>

</html>