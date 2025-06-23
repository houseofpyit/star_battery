from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class HopBatteryOffer(models.Model):
    _name = "hop.battery.offer"

    name = fields.Char(string="Name",copy=False)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    company_ids = fields.Many2many(
        "res.company", string="Companies", default=lambda self: self.env.company.ids)
    line_ids = fields.One2many('hop.battery.offer.line', 'mst_id',string="Product Details")
    
class HopBatteryOfferLine(models.Model):
    _name = "hop.battery.offer.line"

    mst_id = fields.Many2one('hop.battery.offer',string="Offer")
    product_id = fields.Many2one('hop.product.mst',string="Product")
    qty = fields.Float(string="Quantity")