{
    "name": "Account Custom",
    "version": "1.0",
    "depends": [
        'base',
        'account',
    ],
    "author": "Hendra - ADSOFT",
    "category": "",
    "description": """
        Additional Custom for Modul Account
        * Additional Reference on account.move.line, use to add additional marking on each ledger
    """,
    "init_xml": [],
    'update_xml': [
        'report/report_journal_item_view.xml',
        'account_move_line_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
