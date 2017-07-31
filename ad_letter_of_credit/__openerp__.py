{
    "name": "Letter of Credit",
    "version": "1.0",
    "depends": ["base","sale","account","ad_port","sale_stock","sale_set_to_draft","mrp"],
    "author": "Hendra - Adsoft",
    "category": "Accounting and Finance",
    "description": """
    This Module is use to create an L/C verification document.
    Menu that created by this module are :
        * Letter of Credit on Sales Menu
    """,
    "init_xml": [],
    'update_xml': [
                    "wizard/lc_product_line_wizard_view.xml",
                    "data/label.print.csv",
                    "wizard/wizard_change_label_view.xml",
                    "workflow/sale_wkf.xml",
                    "workflow/purchase_workflow.xml",
                    "letter_of_credit_view.xml",
                    "sale_view.xml",
                    "purchase_order_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}