# python odoo-bin -r odoo -w 123 --addons-path=addons,technical-training-sandbox/ -d odoo
# python odoo-bin -r odoo2 -w 079910142 --addons-path=addons,technical-training-sandbox/ -d odoo2 -u estate
# python odoo-bin -r odoo -w 123 --addons-path=addons\,technical-training-sandbox/ -d db_odoo -u estate --dev xml

{
    'name': "Real Estate",
    'version': '1.1',
    'depends': ['base'],
    'author': "moath",
    'category': 'Test',
    'description': """
    Description text
    """,
    'data':[
        'security/ir.model.access.csv',

        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
