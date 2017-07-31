{
    "name": "Advance Payment",
    "version": "1.0",
    "depends": ["base","account"],
    "author": "Hendra - Adsoft",
    "category": "Accounting and Finance",
    "description": """
    This Module is use to create document payment for Advance payment.
    Menu that created by this module are :
        * Advannce Payment
    """,
    "init_xml": [
        "data/sequences.xml",
    ],
    'update_xml': [
                    "advance_payment_view.xml",
                    "voucher_view.xml",
                    "partner_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}