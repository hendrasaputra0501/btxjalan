{
    "name": "Bea Cukai Form BC",
    "version": "1.0",
    "depends": ['base',"stock","sale","purchase","account","ad_container_booking","ad_product_info_bitratex"],
    "author": "Dedi - ADSOFT",
    "category": "",
    "description": """
        Bea Cukai Form BC Control and Report
    """,
    "init_xml": [],
    'update_xml': [
        "sequence.xml",
        "beacukai_view.xml",
        "product_view.xml",
        "report/bc40_form_view.xml",
        "report/bc41_form_view.xml",
        "report/report_view.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
