{
    'name': 'Visual export',
    'version': '1.0.0',
    'sequence': 150,
    'category': 'Anybox',
    'description': """
    Export data from a list view to an OpenDocument (ODS) file,
    with group_by and corresponding formula
    """,
    'author': 'Anybox',
    'website': 'http://anybox.fr',
    'depends': [
        'base',
        'web',
    ],
    'css': [
        'static/src/css/export.css',
    ],
    'qweb': [
        'static/src/xml/export.xml',
    ],
    'js': [
        'static/src/js/export.js',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
