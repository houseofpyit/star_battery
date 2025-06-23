from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class ReplacementBatteryWizard(models.TransientModel):
    _name = 'hop.replacement.battery.wizard'

    party_id = fields.Many2one('res.partner',string="Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)])
    date = fields.Date(string='Date')
    salebill_id = fields.Many2one('hop.salebill',"Party")
    barcode_id = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    replacement_barcode_id = fields.Many2one('hop.purchasebill.line.barcode' ,string="Replacement Barcode")
    warranty_end_date = fields.Date(string='Warranty Date')

    line_ids = fields.One2many('hop.replacement.battery.wizard.line',"mst_id",copy=True)
        
    @api.onchange('barcode_id','replacement_barcode_id')
    def _onchange_barcode_id(self):
        if self.barcode_id:
            replacement = self.env['hop.replacement.battery'].search([('barcode_id', '=', self.barcode_id.id)])
            sale = self.env['hop.salebill.line'].search([('barcode_id', '=', self.barcode_id.id)])
            replacement_line_record = self.env['hop.replacement.battery.line'].search([('barcode_id', '=', self.barcode_id.id)])
            if not replacement and not sale and  not replacement_line_record:
                raise ValidationError('No Barcode Found !!!')
            sale_barcode =  False
            product_id = False
            if replacement:
                sale_barcode = replacement.salebill_id
                product_id = replacement.barcode_id.product_id
            elif replacement_line_record:
                sale_barcode = replacement_line_record.mst_id.salebill_id
                product_id = replacement_line_record.barcode_id.product_id
            elif sale:
                sale_barcode = sale.mst_id
                product_id= sale.product_id
            
            salebill_date = sale_barcode.date
            product_warranty_months = product_id.warranty + product_id.distributor_warranty
            warranty_end_date = salebill_date + relativedelta(months=product_warranty_months)
            self.warranty_end_date = warranty_end_date
            self.date = sale_barcode.date
            self.party_id = sale_barcode.party_id.id
            self.salebill_id = sale_barcode.id

            if replacement :
                self.line_ids =  False
                line_list = []
                line_list.append((0,0,{
                                        'date' :replacement.date,
                                        'barcode_id' :replacement.barcode_id.id,
                                        }))
                for line in replacement.line_ids:
                     
                    line_list.append((0,0,{
                                        'date' :line.date,
                                        'barcode_id' :line.barcode_id.id,
                                        }))
                
                self.line_ids = line_list
            elif replacement_line_record:
                self.line_ids =  False
                line_list = []
                line_list.append((0,0,{
                                        'date' :replacement_line_record.mst_id.date,
                                        'barcode_id' :replacement_line_record.mst_id.barcode_id.id,
                                        }))
                for line in replacement_line_record.mst_id.line_ids:
                     
                    line_list.append((0,0,{
                                        'date' :line.date,
                                        'barcode_id' :line.barcode_id.id,
                                        }))
                
                self.line_ids = line_list
            

        if self.replacement_barcode_id:
            sale_barcode = self.env['hop.salebill.line'].search([('barcode_id', '=', self.replacement_barcode_id.id)])
            if sale_barcode:
                str_error = "This barcode has already been sold in " + sale_barcode.mst_id.name
                raise ValidationError(str_error)
            
            replacement_line_record = self.env['hop.replacement.battery.line'].search([('barcode_id', '=', self.replacement_barcode_id.id)])
            if replacement_line_record:
                raise ValidationError("This battery has already been replaced.")
            
            replacement = self.env['hop.replacement.battery'].search([('barcode_id', '=', self.replacement_barcode_id.id)])
            if replacement:
                raise ValidationError("This battery has already been replaced.")
    
        if self.warranty_end_date  and self.warranty_end_date < date.today():
            raise ValidationError("The warranty has expired.") 
         

    def action_confirm(self):
        if self.barcode_id and self.replacement_barcode_id:
            if self.warranty_end_date < date.today():
                raise ValidationError("The warranty has expired.") 
            
        replacement_record = self.env['hop.replacement.battery'].search([('barcode_id', '=', self.barcode_id.id)])
        replacement_line_record = self.env['hop.replacement.battery.line'].search([('barcode_id', '=', self.barcode_id.id)])

        if not replacement_record and not replacement_line_record:
            line_list = []
            line_list.append((0,0,{
                                   'date' :date.today(),
                                   'barcode_id' :self.replacement_barcode_id.id,
                                   'salebill_id':self.salebill_id.id,
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'qty':1,
                                }))
            replacement = self.env['hop.replacement.battery'].create(
                {
                    'party_id':self.party_id.id,
                    'date':self.date,
                    'warranty_end_date':self.warranty_end_date,
                    'salebill_id':self.salebill_id.id,
                    'barcode_id':self.barcode_id.id,
                    'product_id':self.barcode_id.product_id.id,
                    'line_ids':line_list
                }
            )

            for line in replacement.line_ids:
                line.barcode_id.origin = self.salebill_id.name
            return {
            'name':"Battery Replacements Tracking",
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hop.replacement.battery',
            'res_id':replacement.id,
            }

        elif replacement_line_record:
            line_list = []
            line_list.append((0,0,{
                                   'date' :date.today(),
                                   'barcode_id' :self.replacement_barcode_id.id,
                                   'salebill_id':self.salebill_id.id,
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'qty':1,
                                }))
            replacement_line_record.mst_id.line_ids = line_list
            for line in replacement_line_record.mst_id.line_ids:
                line.barcode_id.origin = self.salebill_id.name
            return {
            'name':"Battery Replacements Tracking",
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hop.replacement.battery',
            'res_id':replacement_line_record.mst_id.id,
            }
    
        elif replacement_record:

            line_list = []
            line_list.append((0,0,{
                                   'date' :date.today(),
                                   'barcode_id' :self.replacement_barcode_id.id,
                                   'salebill_id':self.salebill_id.id,
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'qty':1,
                                }))
            replacement_record.line_ids = line_list

            replacement_record.line_ids = line_list
            for line in replacement_record.line_ids:
                line.barcode_id.origin = self.salebill_id.name
            
            return {
            'name':"Battery Replacements Tracking",
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hop.replacement.battery',
            'res_id':replacement_record.id,
            }
        
class ReplacementBatteryLineWizard(models.TransientModel):
    _name = 'hop.replacement.battery.wizard.line'

    mst_id = fields.Many2one('hop.replacement.battery.wizard',ondelete='cascade')
    date = fields.Date(string='Date')
    barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")