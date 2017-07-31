{
    "name": "Web Bitratex",
    "version": "1.0",
    "depends": ["base","web",],
    "author": "Dedi - Adsoft",
    "category": "Web",
    "description": """
     Web Themes modification for PT. Bitratex Industries
    """,
    "init_xml": [],
    'update_xml': [
                   ],
    'demo_xml': [],
    'css' : [
        "static/src/css/modified_theme.css",
    ],
    'js' : [
        # "static/src/js/modified_theme.js",
        #"static/src/js/view_form.js",
        "static/src/js/mod_one2many.js"
    ],
    'qweb' : [
        "static/src/xml/modified_theme.xml",
    ],
    'installable': True,
    'active': False,
    'application':True,
}