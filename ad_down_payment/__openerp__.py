{
    "name": "Down Payment",
    "version": "1.0",
    "depends": ['base','purchase','sale','account', 'account_voucher', 'analytic'],
    "author": "ADSOFT",
    "category": "",
    "description": """
        Down Payment PTGBU
        Added :
        - Information DP in Purchase Order
        - Information DP in Supplier Invoice
        - Landed Cost
        - Merge with ad_downpayment
        - Penghitungan PPh Retention DPP - Retention - (DP / 1.1)*3%
    """,
    "init_xml": [],
    'update_xml': [
                   "base_update.xml",
                   "workflow.xml",
                   "downpayment_view.xml",
                   "purchase_view.xml",
                   "voucher_payment_receive.xml",
                   "sale_view.xml",
                   "account_invoice_view.xml",
                   #"downpayment_view.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
