# -*- coding: utf-8 -*-
{
    'name': 'Jordan E-Invoice',
    'summary': """ISTD Jordan E-Invoice """,
    "version": "16.0.1",
    'description': 'This module integrate odoo with jordan ISTD to send invoices',
    'category': "Accounting",
    'author': "",
    'website': "",
    'license': 'OPL-1',
    'depends': ['base',
                'account',
                ],
    'data': [
        # views
        'views/account_move.xml',
        'views/res_company.xml',
        'views/res_config_settings.xml',
        # reports
        'reports/invoice.xml',
        # data
        'data/ir_cron.xml',
    ],
    "images": ["static/description/assets/screenshots/hero.gif", ],
    "auto_install": False,
    "installable": True,
    "application": True,
    'price': 4999.99,
    'currency': 'JOD',
}
