{
    "name": "Shipment Document",
    "version": "1.0",
    "depends": ["base",
        "web_ckeditor",
        "ad_letter_of_credit",
        "ad_sales_contract",
        "stock",
        "sale_stock",
        "sale",
        "account",
        "ad_container_booking",
        "ad_product_info_bitratex",
        ],
    "author": "Hendra - Adsoft",
    "category": "Sales",
    "description": """
     This modules is aimed to provide stock report in Bitratex Industries
    """,
    "init_xml": [],
    'update_xml': [
        "data/quality.certificate.yarn.parameter.csv",
        "report/declaration_form_report_view.xml",
        "report/certificate_fumigation_report_view.xml",
        "quality_certificate_form_view.xml",
        "declaration_form_view.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}