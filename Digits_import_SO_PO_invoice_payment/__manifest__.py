# -*- coding: utf-8 -*-
{
    'name': "Digits Digits_import_SO_PO_invoice_payment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'base_address_extended', 'stock', 'sale'],

    # always loaded
    'data': [
        'data/seq.xml',
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/views.xml',

        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
