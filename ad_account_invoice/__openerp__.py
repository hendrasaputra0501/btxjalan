{
    "name": "Account Invoice",
    "version": "1.0",
    "depends": ["base","account","ad_faktur_pajak","ad_sales_contract","ad_container_booking","ad_letter_of_credit"],
    "author": "Hendra - Adsoft",
    "category": "Accounting and Finance",
    "description": """
    
    """,
    "init_xml": [
        # "data/sequences.xml",
    ],
    'update_xml': [
                    "wizard/account_invoice_default_expense_view.xml",
                    "wizard/ai_wizard_change_label_view.xml",
                    "wizard/set_desc_invoice_line_view.xml",
                    "wizard/wizard_purchase_price_variance_entry_view.xml",
                    "report/invoice_for_released_view.xml",
                    "account_view.xml",
                    "account_invoice_view.xml",
                    "account_invoice_wkf.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}