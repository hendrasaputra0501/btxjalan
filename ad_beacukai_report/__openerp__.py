{
    "name": "Report Bea Cukai",
    "version": "1.0",
    "depends": ['base',"stock","sale","purchase","ad_product_info_bitratex"],
    "author": "Dedi - ADSOFT",
    "category": "",
    "description": """
        Bea Cukai Main Report
    """,
    "init_xml": [],
    'update_xml': [
                   # "stock_view.xml",
                   "product_view.xml",
                   "report_stock_move_pabean.xml",
                   "report_stock_wip.xml",
                   "product_wip_view.xml",
                   "report/report_view.xml",
                   "wizard_company_profile_view.xml",
                   "audit_doc_pabean_view.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
