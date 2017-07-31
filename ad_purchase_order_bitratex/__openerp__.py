{
    "name": "Purchase Order Bitratex",
    "version": "1.0",
    "depends": [
        "base","ad_ir_sequence_custom","purchase","stock","ad_container_booking","ad_advance_payment","ad_letter_of_credit","delivery","ad_material_requisition","ad_sales_contract", "ad_account_invoice", "account"
        ],
    "author": "Dedi - Adsoft",
    "category": "Purchase",
    "description": """
     Custom module for Bitratex Purchasing Process
    """,
    "init_xml": [],
    'update_xml': [
                    "report/purchase_order_form_view.xml",
                    "wizard/purchase_line_state_view.xml",
                    "sequence.xml",
                    "sequence_purchase.xml",
                    "sequence_mrr.xml",
                    "purchase_order_view.xml",
                    "purchase_order_workflow.xml",
                    "stock_view.xml",
                    "price_discount.xml",
                    "report/rfq_form_view.xml",
                    "report/info_bank_purchase_report_view.xml",
                    "account_invoice_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}