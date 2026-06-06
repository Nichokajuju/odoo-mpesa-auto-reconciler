{
    'name': 'M-Pesa Auto Reconcile',
    'version': '18.0.1.0.0',
    'summary': 'Automatically reconcile M-Pesa transactions against Odoo invoices',
    'author': 'karuaba',
    'category': 'Accounting/Payment',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/mpesa_transaction_views.xml',
        'views/mpesa_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
