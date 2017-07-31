{
    "name": "Packing Report",
    "version": "1.0",
    "depends": [
        "ad_sales_contract",
        #"ad_product_extended",
        "ad_letter_of_credit",
        "ad_partner_info_bitratex",
        "ad_product_info_bitratex",
        "ad_container_booking",
        "stock",
        "delivery"
        ],
    "author": "Hendra - Adsoft",
    "category": "Warehouse",
    "description": """
     
    """,
    "init_xml": [],
    'update_xml': [
                    "packing_list/packing_list_form_view.xml",
                    "surat_jalan/surat_jalan_form_view.xml",
                    "delivery_order/delivery_order_form_view.xml",
                    "purchase_return/purchase_return_form_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}