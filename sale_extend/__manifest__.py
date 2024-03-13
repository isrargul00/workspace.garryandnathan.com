# -*- coding: utf-8 -*-
{
    'name': 'Sale Extend',
    'version': '1.0',
    'category': '',
    'sequence': 23,
    'summary': '',
    'license': 'LGPL-3',
    'description': """""",
    'author': "Israr",
    'website': "",

    'depends': ['sale','purchase_stock', 'account', 'delivery','delivery_fedex','stock_delivery'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_data.xml',
        'views/sale_ext.xml',
        'views/so_template.xml',
        'report/purchase_order_templates.xml',
        'report/invoice.xml',
        'report/delivery.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
