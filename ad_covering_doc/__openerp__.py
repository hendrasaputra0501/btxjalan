{
    "name": "Covering Document",
    "version": "1.0",
    "depends": ["base",
        "web_ckeditor",
        "ad_container_booking",
        # "ad_sales_contract",
        # "stock",
        # "sale_stock",
        # "sale",
        # "account",
        # "ad_container_booking",
        # "ad_product_info_bitratex",
        ],
    "author": "Jhony - Bitratex",
    "category": "Warehouse",
    "description": """
     This modules is aimed to provide stock report in Bitratex Industries
    """,
    "init_xml": [],
    'update_xml': [
        "data/covering.document.parameter.csv",
		"covering_doc_view.xml",
        "report/covering_document.xml",
        "wizard/covering_doc_onshipping_view.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}