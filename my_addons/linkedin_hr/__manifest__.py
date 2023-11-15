# python odoo-bin -r odoo -w 123 --addons-path=addons,technical-training-sandbox/ -d odoo
# python odoo-bin -r odoo2 -w 079910142 --addons-path=addons,technical-training-sandbox/ -d odoo2 -u estate
# python odoo-bin -r odoo -w 123 --addons-path=addons\,technical-training-sandbox/ -d odoo3 -u estate --dev xml

{
    'name': "LinkedIn HR",
    'version': '1.1',
    'depends': [
        "hr_recruitment",
        ],
    'author': "moath",
    'category': 'Test',
    'description': """
    Description text
    """,
    'data':[
        'views/linkedin_view.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
