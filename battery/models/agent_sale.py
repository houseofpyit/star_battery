from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

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


    receipt_count = fields.Integer(string="Receipt Count", compute="_compute_receipt_count")

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
                self.env['hop.receipt'].create({
                        'bill_no':self.env['hop.receipt'].bill_chr_vld(str_order_chr='CSH' if line.payment_type == 'cash' else 'BNK',str_mode='CASH' if line.payment_type == 'cash' else 'CHQ'),
                        'bill_chr':'CSH' if line.payment_type == 'cash' else 'BNK',
                        'mode' : 'CASH' if line.payment_type == 'cash' else 'CHQ',
                        'party_id' : line.party_id.id,
                        'bank_id' : line.bank_id.id,
                        'date':self.date,
                        'net_amt':line.amount,
                        'agent_payment_line_id':line.id,
                        'vchr_type':'AGAINST BILL'
                    })
                
                
    def action_view_receipts(self):
        self.ensure_one()
        receipts = self.env['hop.receipt'].search([('agent_payment_line_id', 'in', self.payment_ids.ids)])
        return {
            'name': _('Receipts'),
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
