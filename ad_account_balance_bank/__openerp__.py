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
    "name"          : "Account Balance Bank Statement",
    "version"       : "1.0",
    "author"        : "ADSOFT - OpenERP Partner Indonesia",
    "category"      : "Accounting & Finance",
    'complexity'    : "normal",    
    "description"   : """Display balance of account on Bank Statement\
    """,
    "website"       : "http://www.adsoft.co.id",
    'images'        : [],
    "init_xml"      : [],
    "depends"       : [
        "account",
    ],
    "update_xml"    : [
        "account_view.xml",
    ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    'certificate'   : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: