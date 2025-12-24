from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class ReplacementBatteryWizard(models.TransientModel):
    _name = 'hop.replacement.battery.wizard'

    party_id = fields.Many2one('res.partner',string="Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)])
    date = fields.Date(string='Date')
    salebill_id = fields.Many2one('hop.salebill',"Sale")
    barcode_id = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    replacement_barcode_id = fields.Many2one('hop.purchasebill.line.barcode' ,string="Replacement Barcode")
    distributor_barcode_id = fields.Many2one('hop.purchasebill.line.barcode' ,string="Distributor Barcode")
    warranty_end_date = fields.Date(string='Warranty Date')
    is_manual = fields.Boolean(default=False,string="Manual")
    replacement_type = fields.Selection([
        ('self', 'Self'),
        ('distributor', 'Distributor')],
        string='Replacement Type',
        default='self')

    line_ids = fields.One2many('hop.replacement.battery.wizard.line',"mst_id",copy=True)


    @api.onchange('replacement_type')
    def onchange_replacement_type(self):
        domain = []
        if self.replacement_type == 'distributor':
            domain.append(('stage', '=', 'sale'))
        else:
             domain.append(('stage', '=', 'new'))

        return {'domain': {'replacement_barcode_id': domain}}
        
    @api.onchange('barcode_id','replacement_barcode_id')
    def _onchange_barcode_id(self):
        if self.barcode_id:
            self.is_manual = self.barcode_id.is_manual
            self.line_ids =  False
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

                            if self.warranty_end_date  and self.warranty_end_date < date.today():
                                if sale_record:
                                    order_date = sale_record.date.strftime('%d-%m-%Y') if sale_record.date else 'N/A'

                                    raise ValidationError(
                                        f"Warranty has expired for customer '{sale_record.party_id.name}'. "
                                        f"Sale Bill: {sale_record.name}, Bill Date: {order_date}."
                                    )
                                else:
                                    raise ValidationError("The warranty has expired.")       
                  
                        else:
                            salebill_date = sale_record.date
                            product_warranty_months = product_id.warranty + product_id.distributor_warranty
                            warranty_end_date = salebill_date + relativedelta(months=product_warranty_months)
                            self.warranty_end_date = warranty_end_date
                            self.date = sale_record.date
                            self.party_id = sale_record.party_id.id
                            self.salebill_id = sale_record.id
                            if self.warranty_end_date  and self.warranty_end_date < date.today():
                                if sale_record:
                                    order_date = sale_record.date.strftime('%d-%m-%Y') if sale_record.date else 'N/A'

                                    raise ValidationError(
                                        f"Warranty has expired for customer '{sale_record.party_id.name}'. "
                                        f"Sale Bill: {sale_record.name}, Bill Date: {order_date}."
                                    )

                                else:
                                    raise ValidationError("The warranty has expired.") 

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
                                                'replacement_barcode_id':line.replacement_barcode_id.id,
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
                                                'replacement_barcode_id':replacement_line_record.replacement_barcode_id.id,
                                                }))
                        
                        self.line_ids = line_list

                else:
                    print("****************")
                    self.replacement_type =  replacement_again_replace.mst_id.replacement_type
                    self.date = replacement_again_replace.date
                    product_id= replacement_again_replace.product_id
                    product_warranty_months = product_id.warranty + product_id.distributor_warranty

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
                                                'replacement_barcode_id':line.replacement_barcode_id.id,
                                                }))
                        self.line_ids = line_list
                        self.party_id = replacement.party_id.id 
                        self.date = replacement.date
                        self.warranty_end_date = replacement.warranty_end_date
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
                                                'replacement_barcode_id':replacement_line_record.replacement_barcode_id.id,
                                                }))
                        
                        self.line_ids = line_list

                        self.party_id = replacement_line_record.mst_id.party_id.id 
                        self.date = replacement_line_record.mst_id.date
                        self.warranty_end_date = replacement_line_record.mst_id.warranty_end_date

        if self.replacement_barcode_id:
            sale_barcode = self.env['hop.salebill.line'].sudo().search([('barcode_ids', 'in', self.replacement_barcode_id.ids)])
            if sale_barcode and self.replacement_type != 'distributor':
                str_error = "This barcode has already been sold in " + sale_barcode.mst_id.name
                raise ValidationError(str_error)
            
            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search(['|',('barcode_id', '=', self.replacement_barcode_id.id),('replacement_barcode_id', '=', self.replacement_barcode_id.id)])
            if replacement_line_record:
                raise ValidationError("This battery has already been replaced.")
            
            replacement = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', self.replacement_barcode_id.id)])
            if replacement:
                raise ValidationError("This battery has already been replaced.")
    
        if self.warranty_end_date  and self.warranty_end_date < date.today():
            raise ValidationError("The warranty has expired.") 
         

    def action_confirm(self):
        if self.barcode_id and self.replacement_barcode_id:
            if self.warranty_end_date < date.today():
                raise ValidationError("The warranty has expired.") 
            
        replacement_record = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', self.barcode_id.id)])
        replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', self.barcode_id.id)])

        if not replacement_record and not replacement_line_record:
            line_list = []
            line_vals={
                                   'date' :date.today(),
                                   'barcode_id' :self.replacement_barcode_id.id,
                                   
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'replacement_barcode_id':self.distributor_barcode_id.id,
                                   'qty':1,
                                }
            if self.salebill_id.sudo():
                line_vals.update({
                'salebill_id':self.salebill_id.sudo().id if self.salebill_id.sudo() else False,
                'sale_bill_name':self.salebill_id.sudo().name if self.salebill_id.sudo() else False,
                })
            line_list.append((0,0,line_vals))
            vals = {
                    'party_id':self.party_id.id,
                    'replacement_type':self.replacement_type,
                    'date':self.date,
                    'warranty_end_date':self.warranty_end_date,
                    
                    'sale_bill_name':self.salebill_id.sudo().name if self.salebill_id.sudo() else False,
                    'barcode_id':self.barcode_id.id,
                    'product_id':self.barcode_id.product_id.id,
                    'line_ids':line_list
                }
            if  self.salebill_id.sudo():
                vals.update({'salebill_id':self.salebill_id.sudo().id if self.salebill_id.sudo() else False,})
            replacement = self.env['hop.replacement.battery'].sudo().create(
               vals 
            )
            
            for line in replacement.line_ids:
                line.barcode_id.origin = self.salebill_id.sudo().name
                line.barcode_id.stage = 'replace'
                line.barcode_id.replace_id = replacement.id
                if line.replacement_barcode_id:
                    line.replacement_barcode_id.stage = 'sale'
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
                                   'salebill_id':self.salebill_id.sudo().id if self.salebill_id.sudo() else False,
                                   'sale_bill_name':self.salebill_id.sudo().name if self.salebill_id.sudo() else False,
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'replacement_barcode_id':self.distributor_barcode_id.id,
                                   'qty':1,
                                }))
            replacement_line_record.sudo().mst_id.line_ids = line_list
            for line in replacement_line_record.mst_id.line_ids:
                line.barcode_id.origin = self.salebill_id.sudo().name
                line.barcode_id.stage = 'replace'
                line.barcode_id.replace_id = replacement_line_record.mst_id.id
                if line.replacement_barcode_id:
                    line.replacement_barcode_id.stage = 'sale'
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
                                   'salebill_id':self.salebill_id.sudo().id if self.salebill_id.sudo() else False,
                                   'sale_bill_name':self.salebill_id.sudo().name if self.salebill_id.sudo() else False,
                                   'product_id':self.replacement_barcode_id.product_id.id,
                                   'replacement_barcode_id':self.distributor_barcode_id.id,
                                   'qty':1,
                                }))

            replacement_record.sudo().line_ids = line_list
            for line in replacement_record.line_ids:
                line.barcode_id.origin = self.salebill_id.sudo().name
                line.barcode_id.stage = 'replace'
                line.barcode_id.replace_id = replacement_record.id
                if line.replacement_barcode_id:
                    line.replacement_barcode_id.stage = 'sale'
            
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
    replacement_barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Replacement Barcode")