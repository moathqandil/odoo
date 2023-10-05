# python odoo-bin -r odoo2 -w 079910142 --addons-path=addons,technical-training-sandbox/ -d demo_db
# python odoo-bin -r odoo2 -w 079910142 --addons-path=addons,technical-training-sandbox/ -d odoo2 -u estate

{
    'name': "Real Estate",
    'version': '1.0',
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
}
