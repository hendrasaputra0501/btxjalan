#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Alam Dewata Utama, PT    
#   Copyright (C) 2010-2014 ADSOft (<http://www.adsoft.co.id>). 
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
    "name"          : "Invoice for Charges",
    "version"       : "1.0",
    "author"        : "ADSOFT - OpenERP Partner Indonesia",
    "category"      : "Accounting & Finance",
    'complexity'    : "normal",    
    "description"   : """Invoice Charges\
    """,
    "website"       : "http://www.adsoft.co.id",
    'images'        : [],
    "init_xml"      : [],
    "depends"       : [
        "account",
        "ad_faktur_pajak",
        "ad_account_invoice",
        "ad_account_custom",
        "l10n_id_BTRX",
    ],
    'data': [
        # 'data/charge_type_data.xml',
        'data/charge.type.csv',
    ],
    "update_xml"    : [
        "wizard/invoice_print_journal_items_view.xml",
        "wizard/set_picking_related_invoice_view.xml",
        "account_invoice_view.xml",
    ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    'certificate'   : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: