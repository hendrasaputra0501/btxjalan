{
    'name': 'Rate Pajak',
    'version': '7.0',
    'author': 'ADSOFT',
    'category': 'Extra Tools',
    'description': """JBU""",
    'depends': [
        'base', 
        'report_webkit',
        'account',
#         'product',
    ],
    'images' : [],
    'update_xml':[
        "res_currency_view.xml"
                  ],
    'data': [
#         'product_view.xml',
    ],
    'demo': [
        'demo/data_demo.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
