from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
import re

class HopAgentSale(models.Model):
    _name = "hop.agent.sale"
    _description = "Agent Sale"
    _rec_name = 'agent_id'

    agent_id = fields.Many2one('res.partner', string="Agent")
    date = fields.Date(string='Date', default=date.today())
    company_id = fields.Many2one('res.company' ,string="Company", default=lambda self: self.env.company.id)
    line_ids = fields.One2many('hop.agent.sale.line', 'mst_id',string="Product Details")
    payment_ids = fields.One2many('hop.agent.payment.line', 'mst_id',string="Payment Details")
    total_amount = fields.Float(string="Total Amount")
    replace_line_ids = fields.One2many('hop.battery.replace', 'mst_id',string="Battery Replacement Details")
    barcode = fields.Text(string="Barcode")


    receipt_count = fields.Integer(string="Receipt Count", compute="_compute_receipt_count")
    replace_count = fields.Integer(string="Receipt Count", compute="_compute_replace_count")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:

            # pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+'
            # pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+|[A-Z0-9]{16,}'
            pattern = rpattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+|[A-Z0-9]{12,16}(?=[A-Z]{3}|$)+||[A-Z]{3}-\d{2,4}|(?=.*[A-Z])(?=.*\d)[A-Z0-9]{7,12}'
            barcode_list = re.findall(pattern, self.barcode)

            # Remove empty values and strip spaces
            barcode_list = [b.strip() for b in barcode_list if b.strip()] 
            barcode_list = sorted(barcode_list, key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else float('inf'))

            error_str = self.env['hop.purchasebill.line.barcode'].barcode_check(barcode_list)
            order_list = []
            if error_str != '':
                raise ValidationError(error_str)
            else:
                print("**********",barcode_list)
                barcodes = self.env['hop.purchasebill.line.barcode'].sudo().search([('name', 'in', barcode_list)])
                print("********",barcodes)
                if barcodes:
                    product_id = barcodes[0].product_id
                
                    line_record = self.line_ids.filtered(lambda l: l.product_id.id == product_id.id)
                    if line_record :
                        barcode_list_all = list(set(line_record.barcode_ids.ids + barcodes.ids))
                        line_record.barcode_ids = [(6, 0, barcode_list_all)]
                        line_record.total_qty = len(line_record.barcode_ids)
                    else:
                        order_list.append((0, 0, {
                                'product_id': product_id.id,
                                'total_qty': len(barcodes.ids),
                                'barcode_ids':[(6, 0, barcodes.ids)]
                            }))

                        self.line_ids = order_list
                    self.barcode = ''
            

    def action_confirm(self):
        for line in self.replace_line_ids:
            if not line.is_working:
                if line.replacement_type == 'distributor':
                    if not line.replacement_barcode_id or not line.distributor_barcode_id:
                        raise ValidationError('Both "Replacement Barcode" and "Distributor Barcode" are required for distributor replacements.')
                elif line.replacement_type == 'self':
                    if not line.replacement_barcode_id:
                        raise ValidationError('"Replacement Barcode" is required for self replacements.')
                        
        for line in  self.replace_line_ids:
            if not line.is_working:
                if line.barcode_id and line.replacement_barcode_id:
                    if line.warranty_end_date < date.today():
                        raise ValidationError("The warranty has expired.") 
                    
                replacement_record = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', line.barcode_id.id)])
                replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', line.barcode_id.id)])

                if not replacement_record and not replacement_line_record:
                    line_list = []
                    line_vals={
                                        'date' :date.today(),
                                        'barcode_id' :line.replacement_barcode_id.id,
                                        
                                        'product_id':line.replacement_barcode_id.product_id.id,
                                        'replacement_barcode_id':line.distributor_barcode_id.id,
                                        'qty':1,
                                        }
                    if line.salebill_id.sudo():
                        line_vals.update({
                        'salebill_id':line.salebill_id.sudo().id if line.salebill_id.sudo() else False,
                        'sale_bill_name':line.salebill_id.sudo().name if line.salebill_id.sudo() else False,
                        })
                    line_list.append((0,0,line_vals))
                    vals = {
                            'party_id':line.party_id.id,
                            'replacement_type':line.replacement_type,
                            'date':line.date,
                            'warranty_end_date':line.warranty_end_date,
                            
                            'sale_bill_name':line.salebill_id.sudo().name if line.salebill_id.sudo() else False,
                            'barcode_id':line.barcode_id.id,
                            'product_id':line.barcode_id.product_id.id,
                            'line_ids':line_list
                        }
                    if  line.salebill_id.sudo():
                        vals.update({'salebill_id':line.salebill_id.sudo().id if line.salebill_id.sudo() else False,})
                    replacement = self.env['hop.replacement.battery'].sudo().create(
                    vals 
                    )
                    
                    for line in replacement.line_ids:
                        line.barcode_id.origin = line.sale_bill_name
                        line.barcode_id.stage = 'replace'
                        line.barcode_id.replace_id = replacement.id
                        if line.replacement_barcode_id:
                            line.replacement_barcode_id.stage = 'sale'

                elif replacement_line_record:
                    line_list = []
                    line_list.append((0,0,{
                                        'date' :date.today(),
                                        'barcode_id' :line.replacement_barcode_id.id,
                                        'salebill_id':line.salebill_id.sudo().id if line.salebill_id.sudo() else False,
                                        'sale_bill_name':line.salebill_id.sudo().name if line.salebill_id.sudo() else False,
                                        'product_id':line.replacement_barcode_id.product_id.id,
                                        'replacement_barcode_id':line.distributor_barcode_id.id,
                                        'qty':1,
                                        }))
                    replacement_line_record.sudo().mst_id.line_ids = line_list
                    for line in replacement_line_record.mst_id.line_ids:
                        line.barcode_id.origin = line.sale_bill_name
                        line.barcode_id.stage = 'replace'
                        line.barcode_id.replace_id = replacement_line_record.mst_id.id
                        if line.replacement_barcode_id:
                            line.replacement_barcode_id.stage = 'sale'
  
            
                elif replacement_record:

                    line_list = []
                    line_list.append((0,0,{
                                        'date' :date.today(),
                                        'barcode_id' :line.replacement_barcode_id.id,
                                        'salebill_id':line.salebill_id.sudo().id if line.salebill_id.sudo() else False,
                                        'sale_bill_name':line.salebill_id.sudo().name if line.salebill_id.sudo() else False,
                                        'product_id':line.replacement_barcode_id.product_id.id,
                                        'replacement_barcode_id':line.distributor_barcode_id.id,
                                        'qty':1,
                                        }))

                    replacement_record.sudo().line_ids = line_list
                    for line in replacement_record.line_ids:
                        line.barcode_id.origin = line.sale_bill_name
                        line.barcode_id.stage = 'replace'
                        line.barcode_id.replace_id = replacement_record.id
                        if line.replacement_barcode_id:
                            line.replacement_barcode_id.stage = 'sale'
                    
            
    @api.depends('replace_line_ids')
    def _compute_replace_count(self):
        for record in self:
            count = 0
            for line in record.replace_line_ids:
                if not line.is_working:
                    barcode_id = line.barcode_id.id
                    if self.env['hop.replacement.battery'].sudo().search_count([('barcode_id', '=', barcode_id)]) > 0:
                        count += 1
                    elif self.env['hop.replacement.battery.line'].sudo().search_count([('barcode_id', '=', barcode_id)]) > 0:
                        count += 1
            record.replace_count = count


    def action_view_replacement(self):
        for record in self:
            ids_list=[]
            for line in record.replace_line_ids:
                if not line.is_working:
                    replacement_record = self.env['hop.replacement.battery'].sudo().search([('barcode_id', '=', line.barcode_id.id)])
                    replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', line.barcode_id.id)])
                    if replacement_record:
                        ids_list.append(replacement_record.id)
                    if replacement_line_record:
                        ids_list.append(replacement_line_record.mst_id.id)

            return {
                'name':"Battery Replacements Tracking",
                'type': 'ir.actions.act_window',
                'res_model': 'hop.replacement.battery',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', ids_list)],
            }


    @api.depends('payment_ids')
    def _compute_receipt_count(self):
        for rec in self:
            rec.receipt_count = self.env['hop.receipt'].search_count([
                ('agent_payment_line_id', 'in', rec.payment_ids.ids)
            ])

    @api.onchange('payment_ids')
    def _onchange_payment_ids(self):
        total_amount =  0 
        for line in self.payment_ids:
           total_amount = total_amount+line.amount
        self.total_amount = total_amount 


    def create_receipt(self):
        for line in self.payment_ids:
            receipts = self.env['hop.receipt'].search([('agent_payment_line_id', '=', line.id)])
            if receipts:
                receipts.write({
                    'party_id' : line.party_id.id,
                        'bank_id' : line.bank_id.id,
                        'date':self.date,
                        'net_amt':line.amount,
                })
            else:
                allQuery = self.env['sale.outstanding'].sale_outstanding_data( self.env.user.fy_from_date , self.env.user.fy_to_date , line.party_id ,
                                                        self.company_id ,adjustment="SALE")
                self.env.cr.execute(allQuery)
                query_result = self.env.cr.dictfetchall()
                line_list = []
                if query_result:
                    adjustment_amt = line.amount
                    for rec in query_result:
                        if adjustment_amt > 0:
                            salebill_rec = self.env['hop.salebill'].sudo().search([('id','=',rec.get('id'))])
                            amount = 0
                            if adjustment_amt > abs(rec.get('balamt',False)):
                                amount = abs(rec.get('balamt',False))
                            else:
                                amount = adjustment_amt
                            line_list.append((0,0,{
                                'module':'sale',
                                'bill_id':rec.get('id'),
                                'bill_no':salebill_rec.name,
                                'bill_date':salebill_rec.date,
                                'adjust_amt': amount,
                                'bill_amt': rec.get('net_amt'),
                                'balance_amt':abs(rec.get('balamt',False)),
                                'taxeble_amt':salebill_rec.tot_taxable,
                                'part_rc_amt':rec.get('adjustamt',False),
                                'ret_amt':abs(rec.get('retamt',False)),
                                'dr_amt':abs(rec.get('dramt',False)),
                                'cr_amt':abs(rec.get('cramt',False)),
                                'jv_amt':abs(rec.get('jvamt',False)),
                                'diff_amt':abs(rec.get('balamt',False)) - amount,
                                'company_id':self.company_id.id,
                            }))
                            adjustment_amt = adjustment_amt - amount
                self.env['hop.receipt'].create({
                        'bill_no':self.env['hop.receipt'].bill_chr_vld(str_order_chr='CSH' if line.payment_type == 'cash' else 'BNK',str_mode='CASH' if line.payment_type == 'cash' else 'CHQ'),
                        'bill_chr':'CSH' if line.payment_type == 'cash' else 'BNK',
                        'mode' : 'CASH' if line.payment_type == 'cash' else 'CHQ',
                        'party_id' : line.party_id.id,
                        'bank_id' : line.bank_id.id,
                        'date':self.date,
                        'net_amt':line.amount,
                        'agent_payment_line_id':line.id,
                        'vchr_type':'AGAINST BILL',
                        'line_id':line_list,
                    })
                
                
    def action_view_receipts(self):
        self.ensure_one()
        receipts = self.env['hop.receipt'].search([('agent_payment_line_id', 'in', self.payment_ids.ids)])
        return {
            'name': 'Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'hop.receipt',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', receipts.ids)],
            'context': {'default_agent_id': self.agent_id.id},
        }
             
    
class HopAgentSaleLine(models.Model):
    _name = "hop.agent.sale.line"

    mst_id = fields.Many2one('hop.agent.sale',string="Offer")
    product_id = fields.Many2one('hop.product.mst',string="Product")
    total_qty = fields.Float(string="Total Qty")
    return_qty = fields.Float(string="Return Qty")
    sales_qty = fields.Float(string="Sales Qty")
    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_agent_barcode_id",copy=True)
    return_barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_return_agent_barcode_id",copy=True)

    @api.onchange('barcode_ids','return_barcode_ids')
    def _onchange_barcode_ids(self):
        if self.barcode_ids:
            self.total_qty = len(self.barcode_ids)
        else:
            self.total_qty = 0
        if self.return_barcode_ids:
            self.return_qty = len(self.return_barcode_ids)
        else:
            self.return_qty = 0

    @api.onchange('total_qty', 'return_qty')
    def _onchange_total_qty(self):
        if self.total_qty and self.return_qty:
            self.sales_qty = self.total_qty - self.return_qty
        else:
            self.sales_qty = self.total_qty


class HopAgentPaymentCollection(models.Model):
    _name = "hop.agent.payment.line"

    mst_id = fields.Many2one('hop.agent.sale',string="Offer")
    party_id = fields.Many2one('res.partner', string="Party")
    payment_type = fields.Selection(
        selection=[('cash', 'Cash'), ('bank', 'Bank')],
        string="Payment Type",
        default="cash"
    )
    trn_char = fields.Char("Trn Type")
    bank_id = fields.Many2one('res.partner',string="Bank/Cash A/C")
    amount = fields.Float(string="Amount")

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type == 'bank':
            self.trn_char = "BANK" 
        else:
            self.trn_char = "CASH" 

class HopReceipt(models.Model):
    _inherit = "hop.receipt"

    agent_id = fields.Many2one('res.partner', string="Agent", domain=[('acc_type','=','AGENT')],tracking=True)
    agent_payment_line_id = fields.Many2one('hop.agent.payment.line', string="Agent payment")


class Battery_replace(models.Model):
    _name = "hop.battery.replace"

    mst_id = fields.Many2one('hop.agent.sale',string="Offer")

    barcode_id  = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    is_working  = fields.Boolean(string="Is Working")
    party_id = fields.Many2one('res.partner',string="Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)])
    date = fields.Date(string='Date')
    salebill_id = fields.Many2one('hop.salebill',"Sale")
    replacement_barcode_id = fields.Many2one('hop.purchasebill.line.barcode' ,string="Replacement Barcode")
    distributor_barcode_id = fields.Many2one('hop.purchasebill.line.barcode' ,string="Distributor Barcode")
    warranty_end_date = fields.Date(string='Warranty Date')
    is_manual = fields.Boolean(default=False,string="Manual")
    replacement_type = fields.Selection([
        ('self', 'Self'),
        ('distributor', 'Distributor')],
        string='Replacement Type',
        default='self')

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

                else:
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
                        self.party_id = replacement.party_id.id 
                        self.date = replacement.date
                        self.warranty_end_date = replacement.warranty_end_date
                elif replacement_line_record:
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
        