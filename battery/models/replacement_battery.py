from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError


class ReplacementBattery(models.Model):
    _name = 'hop.replacement.battery'
    _rec_name = 'salebill_id'

    party_id = fields.Many2one('res.partner',"Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)],required=True,tracking=True,index=True)
    date = fields.Date(string='Date')
    warranty_end_date = fields.Date(string='Warranty Date')
    salebill_id = fields.Many2one('hop.salebill',"Salebill")
    barcode_id = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    product_id = fields.Many2one('hop.product.mst','Product')

    line_ids = fields.One2many('hop.replacement.battery.line',"mst_id")

    def unlink(self):
        barcode_list = []
        for line in self.line_ids:
            barcode_list.append(line.barcode_id)
        res = super(ReplacementBattery,self).unlink()
        for line in barcode_list:
            line.origin =  False
        return res
        
class ReplacementBatteryLine(models.Model):
    _name = 'hop.replacement.battery.line'

    mst_id = fields.Many2one('hop.replacement.battery',ondelete='cascade')
    date = fields.Date(string='Date')
    barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    salebill_id = fields.Many2one('hop.salebill',"Salebill")
    product_id = fields.Many2one('hop.product.mst','Product')
    qty = fields.Float(string="Quantity")

    def unlink(self):
        barcode = self.barcode_id
        res = super(ReplacementBatteryLine,self).unlink()
        barcode.origin =  False
        return res