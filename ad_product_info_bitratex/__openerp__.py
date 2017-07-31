{
    "name": "Product Information Bitratex",
    "version": "7.0",
    "depends": ["base","purchase","product","stock","sale_stock","product_fifo_lifo","mrp","product_manufacturer"],
    "author": "Dedi - Adsoft",
    "category": "Sales",
    "description": """
     This modules is aimed to provide information for Products Data in Bitratex
    """,
    "init_xml": [],
    'update_xml': [
        "wizard/stock_split_move_view.xml",
        "wizard/wizard_rematch_stock_move_view.xml",
        'product_view.xml',
        "mrp_bom_view.xml",
        "stock_view.xml",
        "sale_view.xml",
        "stock_inventory_view.xml",
        "product_requisition_view.xml",
        "stock_move_composition_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application':True,
}