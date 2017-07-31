##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from report import report_sxw
from osv import osv,fields
from report.render import render
from ad_num2word_id import num2word
import pooler
from tools.translate import _

class declaration_form_report_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(declaration_form_report_parser, self).__init__(cr, uid, name, context=context)        
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'fill_the_parameters': self._fill_the_parameters,
        })

    def _fill_the_parameters(self,obj,html_text):
        html_text = html_text.replace('{invoice}',obj.invoice_id and obj.invoice_id.internal_number or ' ')
        html_text = html_text.replace('{date_invoice}',obj.invoice_id and datetime.strptime(obj.invoice_id.date_invoice,"%Y-%m-%d").strftime("%B %d, %Y") or ' ')
        html_text = html_text.replace('{buyer_name}',obj.invoice_id and obj.invoice_id.show_buyer_address and self._get_partner_name(obj.invoice_id.address_text) or (obj.invoice_id.buyer and obj.invoice_id.buyer.name or ''))
        html_text = html_text.replace('{consignee_name}',obj.invoice_id and obj.invoice_id.show_consignee_address and self._get_partner_name(obj.invoice_id.c_address_text) or (obj.invoice_id.consignee and obj.invoice_id.consignee.name or ''))
        html_text = html_text.replace('{buyer_address}',obj.invoice_id and obj.invoice_id.show_buyer_address and self._get_partner_address(obj.invoice_id.address_text) or '')
        html_text = html_text.replace('{consignee_address}',obj.invoice_id and obj.invoice_id.show_consignee_address and self._get_partner_address(obj.invoice_id.c_address_text) or '')

        html_text = html_text.replace('{city}',obj.city.upper() or ' ')
        html_text = html_text.replace('{date}',datetime.strptime(obj.date_declaration,"%Y-%m-%d").strftime("%B %d, %Y").upper() or ' ')
        html_text = html_text.replace('{title}',obj.declaration_title or ' ')

        if obj.invoice_id:
            html_text = html_text.replace('{lc_number}',self._get_lc_numbers(obj.invoice_id))
            html_text = html_text.replace('{lc_date}',self._get_lc_dates(obj.invoice_id))
            html_text = html_text.replace('{do_number}',self._get_picking_numbers(obj.invoice_id))
            html_text = html_text.replace('{date_deliver}',self._get_picking_dates(obj.invoice_id))
            html_text = html_text.replace('{container_number}',self._get_container_numbers(obj.invoice_id))
            html_text = html_text.replace('{so_number}',self._get_contract_numbers(obj.invoice_id))
            html_text = html_text.replace('{so_date}',self._get_contract_dates(obj.invoice_id))
        return html_text

    def _get_partner_name(self, address_text):
        if address_text:
            lines = address_text.split('\n')
            return lines[0]
        return ''

    def _get_partner_address(self, address_text):
        if address_text:
            lines = address_text.split('\n')
            if len(lines) > 1:
                lines.pop(0)
                addrs_result = ', '.join([str(x) for x in lines])
            else:
                addrs_result = address_text
            return addrs_result
        return ''        

    def _get_contract_numbers(self,invoice_obj):
        contract_numbers = []
        for sale in invoice_obj.sale_ids:
            contract_numbers.append(sale.name)
        return contract_numbers and ', '.join(list(set(contract_numbers))) or ''

    def _get_contract_dates(self,invoice_obj):
        contract_dates = []
        for sale in invoice_obj.sale_ids:
            if sale.date_order!='False':
                contract_dates.append(datetime.strptime(sale.date_order,"%Y-%m-%d").strftime("%B %d, %Y").upper())
        print contract_dates, contract_dates and ', '.join(list(set(contract_dates))) or ''
        return contract_dates and ', '.join(list(set(contract_dates))) or ''

    def _get_picking_numbers(self,invoice_obj):
        picking_numbers = []
        for picking in invoice_obj.picking_ids:
            picking_numbers.append(picking.name)
        return picking_numbers and ', '.join(list(set(picking_numbers))) or ''

    def _get_container_numbers(self,invoice_obj):
        container_numbers = []
        for picking in invoice_obj.picking_ids:
            if picking.container_number:
                container_numbers.append(picking.container_number)
        return container_numbers and ', '.join(list(set(container_numbers))) or ''

    def _get_picking_dates(self,invoice_obj):
        picking_dates = []
        for picking in invoice_obj.picking_ids:
            if picking.date_done!='False':
                picking_dates.append(datetime.strptime(picking.date_done,"%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y"))
        return picking_dates and ', '.join(list(set(picking_dates))) or ''

    def _get_lc_numbers(self,invoice_obj):
        lc_numbers = []
        for picking in invoice_obj.picking_ids:
            if picking.lc_ids:
                for lc in picking.lc_ids:
                    lc_numbers.append("L/C No. "+lc.lc_number)
        return lc_numbers and ', '.join(list(set(lc_numbers))) or ''

    def _get_lc_dates(self,invoice_obj):
        lc_dates = []
        for picking in invoice_obj.picking_ids:
            if picking.lc_ids:
                for lc in picking.lc_ids:
                    if lc.lc_expiry_date!='False':
                        lc_dates.append(datetime.strptime(lc.lc_expiry_date,"%Y-%m-%d").strftime("%B %d, %Y"))
        return lc_dates and ', '.join(list(set(lc_dates))) or ''

report_sxw.report_sxw('report.declaration.form.report', 'declaration.form', 'addons/ad_shipment_certificate/report/declaration_form_report.mako', parser=declaration_form_report_parser,header=False)