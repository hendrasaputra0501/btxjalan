{
    "name" : "Voucher Payment Extra Write Off",
    "version" : "0.1",
    "depends" : ["account_voucher","ad_invoice_charge","ad_account_custom"],
    "author" : "ADSOFT",
    "website" : "http://adsoft.co.id/",
    "description": """
     This Module give additional Multiple Writeoff Account.
    """,
    "init_xml" : [
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
        "voucher_view.xml",
        "account_invoice_view.xml",
        ],
    "installable": True,

}