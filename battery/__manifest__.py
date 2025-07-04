
{
    'name': 'Custom Battery',
    'version': '16.0.1.0.0',
    'depends': ['base','transaction','dynamic_report','hop_account'],
    'data': [  
        'data/ledger_sale_data.xml',
        'security/ir.model.access.csv',
        'report/bill_ship_print.xml',
        'report/tax_normal_inv_print.xml',
        'report/purc_bill_print.xml',
        'report/receipt_slip_report.xml',
        'wizard/replacement_wizard.xml',
        'wizard/category_product_wiz.xml',
        'views/purchase_bill.xml',
        'views/salebill_return.xml',
        'views/purchase_bill_return.xml',
        'views/product.xml',
        'views/barcode_mst.xml',
        'views/salebill.xml',
        'views/replacement_battery.xml',
        'views/battery_offer.xml',
        'views/agent_sale.xml',
        'wizard/battery_offer_report.xml',
        'wizard/replacement_report_wiz.xml',
        'wizard/barcode_managemant.xml',
        'wizard/agent_sale_rpt_wiz.xml',
        'views/views.xml',
        'views/res_parnter.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
