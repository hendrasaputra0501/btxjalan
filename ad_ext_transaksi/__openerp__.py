{
    "name": "Extra Transaksi",
    "version": "1.0",
    "depends": [
        'base',
        'account',
        'hr',
        # 'ad_amount2text_idr',
        "ad_account_custom",
        "ad_faktur_pajak",
        "ad_container_booking",
        "ad_invoice_charge",
        'ad_advance_payment',
    ],
    "author": "ADSOFT",
    "category": "",
    "description": """
       Extra Transaksi
    """,
    "init_xml": [],
    'update_xml': [
            "wizard/wizard_tax_oncharge_view.xml",
            "wizard/extra_transaksi_print_journal_items_view.xml",
            "wizard/wizard_set_picking_related_view.xml",
            "ext_transaksi_view.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
