from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class HopInheritProduct(models.Model):
    _inherit = "hop.product.mst"

    warranty = fields.Integer(string='Warranty (Months)')
    distributor_warranty = fields.Integer(string='Distributor Warranty (Months)')


class Producthistory(models.TransientModel): 
    _inherit = 'hop.product.history'


    module = fields.Selection(selection_add=[('replace','Replace')])