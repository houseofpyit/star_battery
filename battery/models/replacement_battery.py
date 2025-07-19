from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


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

    @api.onchange('barcode_id')
    def _onchange_barcode_id(self):
        if self.barcode_id:
            replacement = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', self.barcode_id.id)])
            sale = self.env['hop.salebill.line'].sudo().search([('barcode_ids', 'in', self.barcode_id.ids)])
            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', self.barcode_id.id)])

            replacement_again_replace =  self.env['hop.replacement.battery.line'].sudo().search([('replacement_barcode_id', '=', self.barcode_id.id)])
            if not replacement_again_replace:
                if not self.barcode_id.is_manual :
                    if not replacement and not sale and  not replacement_line_record:
                        raise ValidationError('No Barcode Found !!!')
            sale_barcode =  False
            product_id = False
            if not self.barcode_id.is_manual :
                if not  replacement_again_replace:
                    if replacement or sale or  replacement_line_record:
                        if replacement:
                            sale_barcode = replacement.salebill_id
                            product_id = replacement.barcode_id.product_id
                            self.replacement_type =  replacement.replacement_type
                        elif replacement_line_record:
                            sale_barcode = replacement_line_record.mst_id.salebill_id
                            product_id = replacement_line_record.barcode_id.product_id
                            self.replacement_type =  replacement_line_record.mst_id.replacement_type
                            self.party_id = replacement_line_record.mst_id.party_id.id
                        elif sale:
                            sale_barcode = sale.mst_id.id
                            product_id= sale.product_id
                        sale_record  = self.env['hop.salebill'].sudo().search([('id', '=', sale_barcode)])
                        if not sale_record:
                            replacement_again_replace = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', self.barcode_id.id)])
                            self.replacement_type =  replacement_again_replace.mst_id.replacement_type
                            self.date = replacement_again_replace.mst_id.date
                            product_id= replacement_again_replace.product_id
                            product_warranty_months = product_id.warranty + product_id.distributor_warranty

                            salebill_date = replacement_again_replace.mst_id.date
                            warranty_end_date = salebill_date + relativedelta(months=product_warranty_months)
                            self.warranty_end_date = warranty_end_date

                            sale_record  = self.env['hop.salebill'].sudo().search([('id', '=', replacement_again_replace.salebill_id)])
                            if sale_record:
                                self.party_id = sale_record.party_id.id
                            self.salebill_id = False
                        else:
                            salebill_date = sale_record.date
                            product_warranty_months = product_id.warranty + product_id.distributor_warranty
                            warranty_end_date = salebill_date + relativedelta(months=product_warranty_months)
                            self.warranty_end_date = warranty_end_date
                            self.date = sale_record.date
                            self.party_id = sale_record.party_id.id
                            self.salebill_id = sale_record.id
                            self.product_id = product_id.id
                            self.sale_bill_name = sale_record.name

                else:
                    self.replacement_type =  replacement_again_replace.mst_id.replacement_type
                    self.date = replacement_again_replace.date
                    product_id= replacement_again_replace.product_id
                    product_warranty_months = product_id.warranty + product_id.distributor_warranty
                    self.product_id = product_id.id

                    salebill_date = replacement_again_replace.date
                    warranty_end_date = salebill_date + relativedelta(months=product_warranty_months)
                    self.warranty_end_date = warranty_end_date

                    sale_record  = self.env['hop.salebill'].sudo().search([('id', '=', replacement_again_replace.salebill_id)])
                    self.party_id = sale_record.party_id.id
                    self.salebill_id = False
            else:
                replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', self.barcode_id.id)])
                replacement_again_replace =  self.env['hop.replacement.battery.line'].sudo().search([('replacement_barcode_id', '=', self.barcode_id.id)])
                replacement = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', self.barcode_id.id)])

                if replacement :
                        self.party_id = replacement.party_id.id 
                        self.date = replacement.date
                        self.warranty_end_date = replacement.warranty_end_date
                elif replacement_line_record:
                        self.party_id = replacement_line_record.mst_id.party_id.id 
                        self.date = replacement_line_record.mst_id.date
                        self.warranty_end_date = replacement_line_record.mst_id.warranty_end_date

            if self.barcode_id:
         
                
                replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search(['|',('barcode_id', '=', self.barcode_id.id),('replacement_barcode_id', '=', self.barcode_id.id)])
                if replacement_line_record:
                    raise ValidationError("This battery has already been replaced.")
                
                replacement = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', self.barcode_id.id)])
                if replacement:
                    raise ValidationError("This battery has already been replaced.")
        
            if self.warranty_end_date  and self.warranty_end_date < date.today():
                raise ValidationError("The warranty has expired.") 

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
    
    @api.onchange('barcode_id')
    def _onchange_barcode_id(self):
        if self.barcode_id:
            self.salebill_id = self.mst_id.salebill_id
            self.sale_bill_name = self.mst_id.sale_bill_name
            self.product_id = self.mst_id.product_id.id
    
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