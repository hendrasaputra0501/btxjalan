#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Alam Dewata Utama, PT    
#   Copyright (C) 2010-2013 ADSOft (<http://www.adsoft.co.id>). 
#   All Rights Reserved
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

{
    "name"          : "Indonesian - Chart of Account for Bitratex",
    "version"       : "1.0",
    "author"        : "ADSOFT - OpenERP Partner Indonesia",
    "category"      : "Localization/Account Charts",
    'complexity'    : "easy",    
    "description"   : """
Chart of Account for Indonesia.
===============================

Indonesian accounting chart and localization for Bitratex    
    """,
    "website"       : "http://www.adsoft.co.id",
    'images'        : [
        'images/config_chart_l10n_th.jpeg',
        'images/l10n_th_chart.jpeg',                       
                       ],
    "init_xml"      : [],
    "depends"       : [
        'account', 'account_chart', 'base','ad_account_code'
                       ],
    "data"    : [
        "coa_code2.xml",
        "tax_template.xml",
#         "account_type.xml",
#         "removed_account.xml",
#         "coa.xml",
#         "tax.xml",
                       ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    'certificate'   : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: