{
    "name": "Sales Commission",
    "version": "1.0",
    "depends": [
        "sale",
        "stock",
        "account",
        "product",
        "ad_account_invoice",
        "ad_insurance_bitratex",
        "ad_sales_contract",
        "ad_partner_info_bitratex",
        "ad_ext_transaksi",
        "ad_invoice_charge",
        "ad_purchase_order_bitratex",
        "l10n_id_BTRX",
        "account_voucher",
        ],
    "author": "Hendra - Adsoft",
    "category": "Sale",
    "description": """
        Functionality :
        * Sales Agent Commission Entry
        * Agent Commission Outstanding per Invoice
        * Agent Commision Payment, through Extra Transaction or its named BPA Commission by department Marketing
    """,
    'data': [
        # 'data/charge_type.xml',
        'data/precision.xml',
        'data/charge.type.csv',
    ],
    "init_xml": [],
    'update_xml': [
                    "wizard/wizard_bpa_commission_view.xml",
                    "wizard/wizard_knock_off_comm_view.xml",
                    "wizard/wizard_sale_order_agent_view.xml",
                    "wizard/wizard_comm_open_view.xml",
                    "stock_incoterms_view.xml",
                    "sales_agent_view.xml",
                    "sale_view.xml",
                    "account_invoice_wkf.xml",
                    "account_invoice_view.xml",
                    "account_bill_passing_view.xml",
                    "account_voucher_view.xml",
                    "account_bill_passing_report_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}