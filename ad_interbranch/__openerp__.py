{
    "name": "Inter Branch Sales and Purchases",
    "version": "1.0",
    "depends": ["base","product","stock","account","sale","purchase"],
    "author": "Dedi - Adsoft",
    "category": "Custom",
    "description": """
    This module provide : Interbranch sales and purchases Transaction for BITRATEX INDUSTRIES
    """,
    "init_xml": [],
    'update_xml': [
                   "interbranch_sale_view.xml",
                   "interbranch_purchase_view.xml",                  
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}