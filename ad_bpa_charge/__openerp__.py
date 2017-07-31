{
    "name": "BPA Charge",
    "version": "1.0",
    "depends": [
        "sale",
        "account",
        "stock",
        "ad_sales_contract",
        "ad_sales_report",
        "ad_container_booking",
        "ad_ext_transaksi",
        "ad_invoice_charge",
        "ad_beacukai_ok",
        ],
    "author": "Hendra - Adsoft",
    "category": "Sale",
    "description": """
        Functionality :
        * Freight Invoice batch, from each Delivery Order or Manually create in Invoice Charge base on Debit Note received
        * Trucking/EMKL Invoice batch, from each Delivery Order or Manually create in Invoice Charge
    """,
    'data': [
        # 'data/charge_type.xml',
    ],
    "init_xml": [],
    'update_xml': [
                    "wizard/wizard_freight_charge_onshipment_view.xml",
                    "wizard/wizard_trucking_charge_onshipment_view.xml",
                    "wizard/wizard_lifton_charge_onshipment_view.xml",
                    "wizard/wizard_kbkb_charge_onshipment_view.xml",
                    "stock_view.xml",
                    "wizard_bpa_report_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}