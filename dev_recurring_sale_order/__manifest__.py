# -*- coding: utf-8 -*-
{
    'name': 'Recurring Sale Order',
    'version': '1.0',
    'sequence': 1,
    'category': 'Sale',
    'description':
        """""",
    'summary': '',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_recurring.xml',
        'data/mail_template.xml',
        'views/recurring_setting_views.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
