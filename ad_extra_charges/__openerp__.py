{
    "name": "Extra Charges",
    "version": "1.0",
    "depends": ["sale","purchase","account","account_voucher","analytic"],
    "author": "Hendra - Adsoft",
    "category": "Accounting and Finance",
    "description": """
    This module is use to create an extra charges document for Sale or Purchase transaction.
    Menu that created by this module are :
        * Extra Charges on Sales Menu
        * Extra Charges on Purchases Menu
        * Extra Charges on Accounting and Finance Menu
    """,
    "init_xml": [],
    'update_xml': [
                    "extra_charges_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}