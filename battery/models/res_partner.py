from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import re

class ResPartner(models.Model):
    _inherit = "res.partner"


    @api.onchange('city_id')
    def _onchange_city_id(self):
        ret = super()._onchange_city_id()
        if self.city_id:
            record = self.env['res.partner'].sudo().search([('city_id','=',self.city_id.id)] ,limit=1, order='id desc')
            if record:
                self.pincode = record.pincode
        return ret
        