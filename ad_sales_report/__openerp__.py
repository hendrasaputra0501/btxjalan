##############################################################################
#
#    Alam Dewata Utama, PT
#    Copyright (c) 2011 - 2012 ADSOFT <http://www.adsoft.co.id>
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "Report For Sales Order",
    "version": "1.1",
    "author": "Deby - ADSOFT",
    "category": "Reporting",
    "description": """
    This module use for Sales Order
    """,
    "website" : "http://www.adsoft.co.id",
    "license" : "GPL-3",
    "depends": [
                "report_xls",
                "sale",
                "base",
                "product",
                "ad_sales_contract",
                "ad_bank_loan",
                "ad_insurance_bitratex"
                ],
    "init_xml": [],
    'update_xml': [
                   "sales_report_view.xml",
                   "pending_sales_report_view.xml",
                   "booked_order_sales_report_view.xml",
                   "shipment_pending_sales_report_view.xml",
                   "lc_tt_position_wizard_view.xml",
                   "net_fob_price_wizard_view.xml",
                   "production_planning_report_view.xml",
                   "commision_detail_wizard_view.xml",
                   "outstanding_commision_wizard_view.xml",
                   "priorities_report_view.xml",
                   "sales_summary_report_view.xml",
                   "sale_report_view_sql.xml",
                   "sale_order_line_view.xml",
                   "sales_summary_customer_count_report_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
