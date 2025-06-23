from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError


class ReplacementBattery(models.Model):
    _name = 'hop.replacement.battery'
    _rec_name = 'party_id'

    party_id = fields.Many2one('res.partner',"Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)],required=True,tracking=True,index=True)
    date = fields.Date(string='Date')
    warranty_end_date = fields.Date(string='Warranty Date')
    salebill_id = fields.Integer(string='Sale Id')
    sale_bill_name = fields.Char(string="SaleBill")
    barcode_id = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    product_id = fields.Many2one('hop.product.mst','Product')
    replacement_type = fields.Selection([
        ('self', 'Self'),
        ('distributor', 'Distributor')],
        string='Replacement Type',
        default='self')

    line_ids = fields.One2many('hop.replacement.battery.line',"mst_id")

    def unlink(self):
        barcode_list = []
        for line in self.line_ids:
            barcode_list.append(line.barcode_id.id)
            barcode_list.append(line.replacement_barcode_id.id)
        res = super(ReplacementBattery,self).unlink()
        self.update_status(barcode_list)
        return res
     
    def update_status(self,barcode_list):
        for bar in self.env['hop.purchasebill.line.barcode'].sudo().search([('id','in',barcode_list)]):
            sale_barcode = self.env['hop.salebill.line'].sudo().search([('barcode_ids', 'in', bar.ids)])
            if sale_barcode:
                bar.stage = 'sale'
                bar.origin = sale_barcode.mst_id.name 
                bar.sale_id = sale_barcode.mst_id.mst_id.id 

            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', bar.id)])
            if replacement_line_record:
                bar.stage = 'replace'
                bar.origin = False
                bar.replace_id = replacement_line_record.mst_id.id 

            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('replacement_barcode_id', '=', bar.id)])
            if replacement_line_record:
                bar.stage = 'sale'
                bar.origin = False
            if not sale_barcode  and not replacement_line_record and not replacement_line_record:
                bar.stage = 'new'
                bar.origin = False
        
class ReplacementBatteryLine(models.Model):
    _name = 'hop.replacement.battery.line'

    mst_id = fields.Many2one('hop.replacement.battery',ondelete='cascade')
    date = fields.Date(string='Date')
    barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    salebill_id = fields.Integer(string='Sale Id')
    sale_bill_name = fields.Char(string="SaleBill")
    product_id = fields.Many2one('hop.product.mst','Product')
    qty = fields.Float(string="Quantity")
    replacement_barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Replacement Barcode")

    def unlink(self):
        barcode = self.barcode_id.ids
        replacement_barcode_id = self.replacement_barcode_id.ids
        res = super(ReplacementBatteryLine,self).unlink()
        self.update_status(barcode+ replacement_barcode_id)
        return res
    
    def update_status(self,barcode_list):
        for bar in self.env['hop.purchasebill.line.barcode'].sudo().search([('id','in',barcode_list)]):
            sale_barcode = self.env['hop.salebill.line'].sudo().search([('barcode_ids', 'in', bar.ids)])
            if sale_barcode:
                bar.stage = 'sale'
                bar.origin = sale_barcode.mst_id.name 
                bar.sale_id = sale_barcode.mst_id.id 

            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', bar.id)])
            if replacement_line_record:
                bar.stage = 'replace'
                bar.origin = False
                bar.replace_id = replacement_line_record.mst_id.id 

            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('replacement_barcode_id', '=', bar.id)])
            if replacement_line_record:
                bar.stage = 'sale'
                bar.origin = False
            if not sale_barcode  and not replacement_line_record and not replacement_line_record:
                bar.stage = 'new'
                bar.origin = False