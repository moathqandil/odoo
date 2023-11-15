# python odoo-bin -r odoo -w 123 --addons-path=addons,technical-training-sandbox/ -d odoo
# python odoo-bin -r odoo2 -w 079910142 --addons-path=addons,technical-training-sandbox/ -d odoo2 -u estate
# python odoo-bin -r odoo -w 123 --addons-path=addons\,technical-training-sandbox/ -d odoo3 -u estate --dev xml

{
    'name': "Estate Account",
    'version': '1.1',
    'depends': [
        "estate",
        "account"],
    'author': "moath",
    'category': 'Test',
    'description': """
    Description text
    """,
    'data':[
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
