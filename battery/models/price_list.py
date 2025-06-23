from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class HopInheritResPartner(models.Model):
    _inherit = "res.partner"

    price_line_ids = fields.One2many('party.price.line','mst_id',string="Price Line", copy=True)
    partner_id = fields.Many2one('res.partner',string="Partner",domain="[('acc_type','=','SALE_PARTY')]")
    attachment_ids = fields.Many2many(
        'ir.attachment','ref_res_partner_attachment_ids',
        string="Attachments",
        help="Upload and manage related documents or files for this request."
    )


    def get_product_data(self):
        self.env['category.product.wiz'].search([]).unlink()
        domain = []
        if self.price_line_ids:
            item_list=[]
            for line in self.price_line_ids:
                item_list.append(line.product_id.id)
            if item_list:
                domain.append(['id','not in', item_list])
        product_rec = self.env['hop.product.mst'].search(domain)
        if product_rec:
            for line in product_rec:
                self.env['category.product.wiz'].create({
                    'product_id': line.id,
                    'res_partner_id':self.id,
                        })
        else:
            raise ValidationError('This Sub Group Wise Product are all Selected')

    def fetch_product_list(self):
        self.get_product_data()
        return {
            'name':'Category Wise Product',
            'type': 'ir.actions.act_window', 
            'view_mode': 'tree',
            'res_model': 'category.product.wiz', 
            'target': 'new', 
        }

    def fetch_price_list(self):
        if not self.partner_id:
            raise ValidationError('Please select a partner before fetching the price list.')
        party_rec = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        if not party_rec.price_line_ids:
            raise ValidationError('No Data Found.')
        line_list = []
        self.price_line_ids = False
        for i in party_rec.price_line_ids:
            line_list.append((0,0, {
                'product_id': i.product_id.id,
                'price': i.price,
                'disc_per': i.disc_per,
            }))
        self.price_line_ids = line_list

class HopPartyPriceLine(models.Model):
    _name = "party.price.line"
    _description= "Party Price Line"

    mst_id = fields.Many2one('res.partner',string="Partner")
    product_id = fields.Many2one('hop.product.mst',string="Product",required=True)
    price = fields.Float(string="Price",digits='Amount')
    disc_per = fields.Float(string="Disc (%)")

    @api.onchange('product_id')
    def onchange_product_id(self):
        party_rec = self.env['party.price.line'].search([('mst_id.name','=',self.mst_id.name),('product_id','=',self.product_id.id)])
        if party_rec:
            raise ValidationError('Partner Can not Select Same Product!!!')