# -*- coding: utf-8 -*-
##############################################################################
#
#    account_optimization module for OpenERP, Account Optimizations
#    Copyright (C) 2011 Thamini S.à.R.L (<http://www.thamini.com) Xavier ALT
#
#    This file is a part of account_optimization
#
#    account_optimization is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_optimization is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Account Optimization",
    "version": "1.1",
    "author": "ADSOFT",
    'complexity': "easy",
    "category": "Account Optimization",
    "description": """
OpenERP Account Optimization reference from account_optimization provided by Thamini S.à.R.L:
======================================================================================================
This module make all report optimization:
* Accounting Reports
    * General Ledger (pdf, excel)
    * Trial Balance (pdf, excel)
    * Balance Sheet (pdf, excel)
    * Profit And Loss (pdf, excel)
    * Financial Report (pdf, excel)
* Journals
    * Sale/Purchase Journals (pdf, excel)
    * Journals (pdf, excel)
    * General Journal (pdf)
    * Centralizating Journal (pdf)
* Partners
    * Partner Balance (pdf, excel)
    * Aged Partner Balance (pdf)
    * Partner Ledger (pdf, excel)
* Taxes
    * Taxes Report
* Journal by Entries (pdf, pdf landscape, excel)
* Full Account Balance (pdf, excel)
* Chart of Accounts (pdf, excel)
    """,
    "website" : "http://www.adsoft.co.id",
    "images" : [],
    'depends': [ 'base', 'account'],
    'init_xml': [
    ],
    'demo_xml': [
    ],
    'update_xml': [
        #'account_bank_statement_view.xml',
        'account_fiscal_position_view.xml',
        'security/ir.model.access.csv',
        'wizard/account_report_account_balance_view.xml',
        'wizard/account_report_partner_balance_view.xml',
#        'wizard/account_report_aged_partner_balance_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_report_partner_ledger_view.xml',
        'wizard/account_financial_report_view.xml',
        'wizard/account_report_print_journal_view.xml',
        'wizard/account_validate_move_view.xml',
#        'wizard/account_report_account_bs_view_i.xml',
#        'wizard/account_report_profit_loss_view_i.xml',
        #'account_report_report.xml',
        #'account_report_wizard.xml',
    ],
    "category" : "Account Report Optimization",
    "init_xml": [],
    "demo_xml" : [],
    'test': [],
    'installable': True,
    #'application': True,
    'auto_install': False,
    'certificate': '',
    "css": [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
