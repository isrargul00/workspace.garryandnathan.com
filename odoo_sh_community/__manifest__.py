# -*- coding: utf-8 -*-

{
    'name': 'Alternative to Odoo.sh for Odoo Community',
    'summary': 'Manage Repositories.',
     "version": "17.0.8.0",
    'category': 'Extra Tools',
    'website': "https://odoonext.com/",
    'author': 'David Montero Crespo',
    'installable': True,
     'depends': [
        'base','mail'
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/repository_repository_view.xml',
        'views/panel_tool.xml',
        'views/ir_module_module.xml',
        'views/upload_module.xml',
    ],
    'application': True,
    'price': 100,
    "uninstall_hook": "uninstall_hook",
    'images': ['static/description/imagen.png'],
    'currency': 'EUR',
    'license': 'AGPL-3',

}
