from odoo import api, models, fields
from datetime import datetime

class CategoryProductWizard(models.TransientModel):
    _name = "category.product.wiz"
    _description= "Category Product"
   
    product_id = fields.Many2one('hop.product.mst',string="Product")
    res_partner_id = fields.Many2one('res.partner',string="Partner")

    def action_save_product(self):
        line_list = []
        for line in self:
            line_list.append((0, 0,
                                {   
                                'product_id': line.product_id.id,
                                }))
        if line_list:
            res_partner = self.env['res.partner'].search([('id','=',self[0].res_partner_id.id)])
            res_partner.price_line_ids = sorted(line_list, key=lambda x: x[0])