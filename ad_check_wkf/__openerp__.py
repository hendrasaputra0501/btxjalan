{
    "name": "WKF CHECK",
    "version": "1.0",
    "depends": [
        "sale","sale_stock",
        ],
    "author": "Dedi - Adsoft",
    "category": "Technical",
    "description": """
        Functionality :
            Recalculate Workflow
    """,
    'data': [
        # 'data/charge_type.xml',
    ],
    "init_xml": [],
    'update_xml': [
                    "sale_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}