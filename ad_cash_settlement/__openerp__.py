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
    "name"          : "Cash Settlement",
    "version"       : "1.0",
    "author"        : "ADSOFT - OpenERP Partner Indonesia",
    "category"      : "Cash Advance & Settlement Menu Multi Currencies Support",
    'complexity'    : "normal",    
    "description"   : """Cash Settlement modules same like Account Voucher\
    \n\nAdded :\
    \n    - Settlemnet Receive Date\
    \n    - Select Method Settlement\
    \n    - Rounding\
    \n    - Cash Advance Pay Administration\
    \n    - xxx
    """,
    "website"       : "http://www.adsoft.co.id",
    'images'        : [],
    "init_xml"      : [],
    "depends"       : [
        "account",
        "hr",
    ],
    "update_xml"    : [
        "partner_view.xml",
        "cash_advance.xml",
        "workflow_advance.xml",
        "cash_settlement.xml",
        "account_cash_settlement_view.xml",
        "workflow_settlement.xml",
        "workflow_account_cash_settlement.xml",
        "base_update.xml",
    ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    'certificate'   : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: