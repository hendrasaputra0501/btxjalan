{
    "name": "Tax Return",
    "version": "1.0",
    "depends": ["base","account","account_voucher"],
    "author": "Dedi - Adsoft",
    "category": "Account",
    "description": """
        Tax Return/Payment to Government
    """,
    "init_xml": [],
    "data":[
        "data/sequence.xml",
    ],
    'update_xml': [
        "wizard/wizard_add_taxes_view.xml",
        "partner_view.xml",
        "tax_payment_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}