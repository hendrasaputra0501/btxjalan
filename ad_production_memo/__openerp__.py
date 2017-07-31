{
    "name": "Production Memo",
    "version": "1.0",
    "depends": [
        "sale",
        "mrp",
        "ad_sales_contract",
        "ad_letter_of_credit",
        "ad_partner_info_bitratex",
        "ad_product_info_bitratex",
        #"ad_container_booking",
        ],
    "author": "Hendra - Adsoft",
    "category": "Manufacturing",
    "description": """
     
    """,
    "init_xml": [],
    'update_xml': [
                    # "workflow/stock_wkf.xml",
                    "report/production_memo_form_view.xml",
                    "production_memo_view.xml",
                    "sale_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}