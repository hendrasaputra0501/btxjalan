{
    "name": "MRP Stock Move - Journal",
    "version": "1.0",
    "depends": ["mrp","stock"],
    "author": "Dedi - Adsoft",
    "category": "Manufacturing",
    "description": """
    This Module is use to create Journal Entries when moving stocks from raw material location to production location.
    """,
    "init_xml": [],
    'update_xml': [
                    "mrp_move_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}