{
    "name": "Container Booking",
    "version": "1.0",
    "depends": [
        "sale",
        "ad_port",
        "product_fifo_lifo",
        "stock",
        "delivery",
        "stock_picking_invoice_link",
        "ad_letter_of_credit",
        "ad_product_info_bitratex",
        "stock_cancel",
        "ad_faktur_pajak",
        "ad_internal_move_cost_center",
        ],
    "author": "Hendra - Adsoft",
    "category": "Warehouse",
    "description": """
    """,
    "init_xml": [],
    'update_xml': [
                    "wizard/picking_split_view.xml",
                    "wizard/si_wizard_change_label_view.xml",
                    "wizard/stuffing_memo_onshipping_view.xml",
                    "wizard/stock_partial_picking_view.xml",
                    "wizard/invoice_number_onshipping_view.xml",
                    "wizard/stock_move_set_location_view.xml",
                    "wizard/stock_picking_return_view.xml",
                    # "report/container_booking_form_view.xml",
                    "report/shipping_instruction_form_view.xml",
                    "report/stuffing_memo_form_view.xml",
                    "workflow/stock_wkf.xml",
                    "container_booking_view.xml",
                    "stock_view.xml",
                    "stuffing_memo_view.xml",
                    "transport_view.xml",
                    "stock_proforma_invoice_view.xml",
                    "container_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'application':True,
    'auto_install': False,
}