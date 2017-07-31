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
    "name": "Report For Accounting",
    "version": "1.1",
    "author": "Hendra - ADSOFT",
    "category": "Reporting",
    "description": """
    This module use for Sales Order
    """,
    "website" : "http://www.adsoft.co.id",
    "license" : "GPL-3",
    "depends": [
                "account",
                "base",
                ],
    "init_xml": [],
    'update_xml': [
                   "payment_overdue_wizard_view.xml",
                   "advance_report_wizard_view.xml",
                   "aging_report_wizard_view.xml",
                   "payment_realisation_wizard_view.xml",
                   "general_ledger_wizard_view.xml",
                   "negotiation_report_wizard_view.xml",
                   "apvendor_report_wizard_view.xml",
                   "detail_insurance_report_wizard_view.xml",
                   "outstanding_advance_report_wizard_view.xml",
                   "om_tally_wizard_view.xml",
                   "neraca_lajur_wizard_view.xml",
                   "ledger_cashbank_wizard_view.xml",
                   "partner_balance_detail_wizard_view.xml",
                   "ledger_gainloss_wizard_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
