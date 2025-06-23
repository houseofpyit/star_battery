from odoo import api, models, fields
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from ... dynamic_report import report_field



class ItemWiseStock(models.TransientModel):
    _inherit = 'itemwise.stock.wizard'


    def create_vals(self,i):
        res = super(ItemWiseStock, self).create_vals(i)
        res.update({
            "replace": i.get('replace') if i.get('replace') else 0,
        })
        return res
    
    def columns_field(self ,business_type ):
        columns = []
        if business_type == 'normal_business':
            columns.append(report_field.char_field(self,'Itemname','itemname'))
            columns.append(report_field.char_field(self,'Category','category'))
            columns.append(report_field.char_field(self,'Unit','unit'))

            columns.append(report_field.float_field(self,'OpeningQty','op_pcs'))
            columns.append(report_field.float_field(self,'PurQty','pur_pcs'))
            columns.append(report_field.float_field(self,'SaleRetQty','sale_ret_pcs'))
            columns.append(report_field.float_field(self,'SaleQty','sale_order_pcs'))
            columns.append(report_field.float_field(self,'PurRetQty','pur_ret_pcs'))
            columns.append(report_field.float_field(self,'Replace','replace'))

            if self.env['ir.model'].sudo().search([('model', '=', 'hop.manufacturing')]): 
                columns.append(report_field.float_field(self,'Manu Qty','manufacturing_qty'))
                columns.append(report_field.float_field(self,'Manu Conp Qty','manufacturing_line_qty'))
            columns.append(report_field.float_field(self,'BalanceQty','bal_pcs'))

        elif business_type == 'textile_business':
            columns.append(report_field.char_field(self,'Itemname','itemname'))
            columns.append(report_field.char_field(self,'Category','category'))
            columns.append(report_field.char_field(self,'Unit','unit'))
            columns.append(report_field.float_field(self,'MinimumQty','minimum_qty'))
            columns = columns + self.pcs_columns()
            columns = columns + self.meter_columns()
            columns = columns + self.weight_columns()
        return columns