#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   BITRATEX INDUSTRIES, PT    
#
##############################################################################

{
    "name"          : "Invoice for Sample",
    "version"       : "1.0",
    "author"        : "BITRATEX",
    "category"      : "Marketing",
    'complexity'    : "normal",    
    "description"   : """Invoice Sample\
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
        # 'data/charge.type.csv',
    ],
    "update_xml"    : [
        "invoice_sample_view.xml",
        "wizard/wizard_invoice_sample_view.xml",
        "report/invoice_sample_report_view.xml",
    ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    'certificate'   : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: