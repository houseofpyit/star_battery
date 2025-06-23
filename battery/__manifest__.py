
{
    'name': 'Custom Battery',
    'version': '16.0.1.0.0',
    'depends': ['base','transaction','dynamic_report'],
    'data': [  
        'security/ir.model.access.csv',
        'wizard/replacement_wizard.xml',
        'views/purchase_bill.xml',
        'views/product.xml',
        'views/barcode_mst.xml',
        'views/salebill.xml',
        'views/replacement_battery.xml',
        'views/battery_offer.xml',
        'wizard/battery_offer_report.xml',
        'views/views.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
