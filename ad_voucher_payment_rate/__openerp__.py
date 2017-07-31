{
    "name"          : "Voucher Payment Rate",
    "version"       : "1.0",
    "author"        : "Dedi - ADSOFT",
    "category"      : "Accounting & Finance",
    'complexity'    : "normal",    
    "description"   : """Enable payment rate for different currency on voucher payment even the AR/AP is not in different currency
    """,
    "website"       : "http://www.adsoft.co.id",
    'images'        : [],
    "init_xml"      : [],
    "depends"       : [
        "account_voucher","account"
    ],
    "update_xml"    : [
        "style.xml",
        "wizard/account_statement_from_invoice_view.xml",
        "wizard/statement_print_journal_items_view.xml",
        "account_voucher_view.xml",
        "account_bank_statement_view.xml",
    ],
    "demo_xml"      : [],
    'test'          : [],
    "active"        : False,
    "installable"   : True,
    'auto_install'  : False,    
    # 'certificate'   : '',
}