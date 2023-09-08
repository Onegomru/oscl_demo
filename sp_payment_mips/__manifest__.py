{
    'name': 'Mips Payment Acquirer',
    'version': '0.1',
    'sequence': -10,
    'category': 'Accounting/Payment Providers',
    'license': 'OPL-1',
    'author': 'Vidurath',
    'description': """Mips Payment Acquirer""",
    'summary': """""",
    'depends': ['payment', 'website_sale'],
    'data': [
        'views/paystack_view.xml',
        'views/payment_acquirer.xml',
        'data/paystack_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook',
    'price': 40,
    'currency': 'USD',
    'images': ['static/description/odoo_paystack_banner.png']
}
