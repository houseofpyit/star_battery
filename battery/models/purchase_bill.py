import xml.etree.ElementTree as xee
from odoo import api, models, fields, _
from lxml import etree
from odoo.exceptions import UserError, ValidationError
import re
from ...transaction import common_file
from datetime import datetime, timedelta


class InheritPurchaseBill(models.Model):
    _inherit = 'hop.purchasebill'

    mobile_no = fields.Char(string="Mobile No",related='party_id.mobile')
    city_id = fields.Many2one('res.city', string="City",related='party_id.city_id')
    due_date = fields.Date(string='Due Date',default=fields.Date.context_today,tracking=True)

    def update_due_date(self):
        for res in self.search([]):
            res.due_date =  res.date + timedelta(days=res.due_days)
            
    @api.onchange('date')
    def _onchange_date(self):
        if self.date:
            self.due_date =  self.date + timedelta(days=self.due_days)
    
    def update_purcgase_id(self):
        purchase_record = self.sudo().search([])

        for purchase in purchase_record:
            for line in purchase.line_id:
                for bar in line.barcode_line_id:
                    bar.purchase_id = purchase.id
                    bar.date = purchase.date
                    if line.product_id != bar.product_id:
                        bar.product_id = line.product_id
        sale_record = self.env['hop.salebill'].sudo().search([])

        for sale in sale_record:
            for line in sale.line_id:
                for bar in  line.barcode_ids:
                    bar.sale_id  = sale.id

        replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([])
        for rep in replacement_line_record:
            rep.barcode_id.replace_id = rep.mst_id.id
            rep.barcode_id.stage = 'replace'

            
        
    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     form_view_references = ['transaction.purchasebill_form']
    #     for form_view_ref in form_view_references:
    #         form_view = self.env.ref(form_view_ref).sudo()
    #         arch_tree = etree.fromstring(form_view.arch)

    #         if arch_tree.tag == 'form':
    #             tree_tag = arch_tree.find(".//tree[@name='line_id']")
    #             if tree_tag is not None:
    #                 if 'editable' in tree_tag.attrib:
    #                     del tree_tag.attrib['editable']
    #             updated_arch = etree.tostring(arch_tree, pretty_print=True, encoding='unicode')
    #             form_view.sudo().write({'arch': updated_arch})
    #     return res
    is_opening_strock  = fields.Boolean(default=True,string="Is Opening Stock")

    @api.onchange('party_id')
    def _party_onchange(self):
        ret = super()._party_onchange()
        if self.party_id:
            self.bill_number = self.party_bill_number(self.party_id)
        if self.date:
            if self.due_days > 0 :
                self.due_date =  self.date + timedelta(days=self.due_days)
        return ret
    
    def party_bill_number(self,party_id,company_id=False):
        company_id = str(self.env.company.id) if self.env.company.id else str(company_id)
        query = ''' Select max(CAST(bill_number AS INTEGER)) From hop_purchasebill Where opening != 'y' and company_id = ''' + str(company_id)
        if party_id:
            query += " and party_id =  " +str(party_id.id)
        if self.env.user.fy_year_id:
            query += " and date >=  " +"'" + str(self.env.user.fy_from_date) +"'"
            query += " and date <=  " +"'" + str(self.env.user.fy_to_date) +"'"
        self.env.cr.execute(query)
        query_result = self.env.cr.dictfetchall()
        if query_result[0]['max'] == None :
            serial = 1
        else:
            serial = 1 + int(query_result[0]['max'] or 0)
        return serial

    
class InheritPurchaseBill(models.Model):
    _inherit = 'hop.purchasebill.line'

    barcode_line_id = fields.One2many('hop.purchasebill.line.barcode',"line_mst_id",copy=True)
    barcode = fields.Text(string="Barcode")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            self.barcode_line_id = False

            # Updated: Apply regex directly instead of splitting by commas first
            # pattern = r'[A-Za-z]*\(\d{2}-\d{2}\)\d+|[A-Za-z0-9]+'
            # pattern = r'[A-Za-z0-9]*\(\d{2}-\d{2}\)\d+|[A-Za-z0-9]+'
            # pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+'
            pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+|[A-Z0-9]{16,}'
            barcode_list = re.findall(pattern, self.barcode)

            # Remove empty values and strip spaces
            barcode_list = [b.strip() for b in barcode_list if b.strip()]  

            barcode_line_list = []
            duplicate_barcodes = []

            for barcode in barcode_list:
                barcode_record = self.env['hop.purchasebill.line.barcode'].sudo().search([('name', '=', barcode)], limit=1)
                if barcode_record:
                    duplicate_barcodes.append({'barcode':barcode ,'purchase_name':barcode_record.purchase_name})  # Collect duplicate barcodes

                barcode_line_list.append((0, 0, {
                    'name': barcode,  # Keep as string, don't assign search result
                    'stage': 'new',
                    'product_id': self.product_id.id,
                    'purchase_name': self.mst_id.name,
                    'line_mst_id': self.id,
                    'date':self.mst_id.date,
                }))

            if duplicate_barcodes:
                duplicates_msg = "\n".join([f"Barcode: {d['barcode']} (Purchase Bill: {d['purchase_name']})" for d in duplicate_barcodes])
                raise ValidationError(f"The following barcodes are already assigned:\n{duplicates_msg}")

            self.barcode_line_id = barcode_line_list  # Assign the new barcode lines
            self.pcs = len(self.barcode_line_id)  # Update PCS count
            self.barcode = ''
            for line in self.barcode_line_id:
                if self.barcode == '':
                    self.barcode = line.name
                else:
                    self.barcode = self.barcode + ','+ line.name

    def write(self, vals):
        ret = super(InheritPurchaseBill, self).write(vals)
        for bar in self.barcode_line_id:
            if self.product_id != bar.product_id:
                bar.product_id = self.product_id
        return ret

class purchasebillLineBarcode(models.Model):
    _name = 'hop.purchasebill.line.barcode'

    name = fields.Char(string="Barcode",copy=False,tracking=True,required=True)
    stage = fields.Selection([
        ('new', 'New'),
        ('sale', 'Sale'),
        ('purchase_return', 'Purchase Return'),
        ('replace', 'Replace'),],
        string='Stage',
        default='new',required=True)
    product_id = fields.Many2one('hop.product.mst','Product')
    origin = fields.Char(string="Sale Origin")
    purchase_name = fields.Char(string="Purchase")
    is_manual = fields.Boolean(default=False,string="Manual")
    line_mst_id = fields.Many2one('hop.purchasebill.line','Purchase Bill Line',ondelete='cascade')
    date = fields.Date("Date")
    purchase_id = fields.Integer(string='purchase')
    replace_id = fields.Integer(string='Replace')
    sale_id = fields.Integer(string='Sale')

    @api.model
    def create(self, vals):
        if vals.get('name',False):
            barcode = self.env['hop.purchasebill.line.barcode'].sudo().search([('name','=',vals.get('name'))])
            if barcode:
                raise ValidationError("Duplicate barcode is not allowed.")
        ret = super(purchasebillLineBarcode, self).create(vals)
        return ret
    
    def write(self, vals):
        if vals.get('name',False):
            barcode = self.env['hop.purchasebill.line.barcode'].sudo().search([('name','=',vals.get('name'))])
            if barcode:
                raise ValidationError("Duplicate barcode is not allowed.")
        ret = super(purchasebillLineBarcode, self).write(vals)
        return ret
    

    def update_status(self):
        for bar in self.sudo().search([('is_manual','=',False)]):
            sale_barcode = self.env['hop.salebill.line'].sudo().search([('barcode_ids', 'in', bar.ids)])
            if sale_barcode:
                bar.stage = 'sale'
                bar.origin = sale_barcode.mst_id.name 
                bar.sale_id = sale_barcode.mst_id.id
            replacement_line_record = self.env['hop.replacement.battery.line'].sudo().search([('barcode_id', '=', bar.id)])
            if replacement_line_record:
                bar.stage = 'replace'
                bar.origin = replacement_line_record.sale_bill_name 
                bar.replace_id = replacement_line_record.mst_id.id
            replacement_line_salerecord = self.env['hop.replacement.battery.line'].sudo().search([('replacement_barcode_id', '=', bar.id)])
            if replacement_line_salerecord:
                bar.stage = 'sale'
                bar.origin = replacement_line_salerecord.sale_bill_name 
            if not sale_barcode  and not replacement_line_salerecord and not replacement_line_record:
                bar.stage = 'new'
                bar.origin = False

    def barcode_check(self, barcode_list):
        error_messages = []

        for barcode in barcode_list:
            barcode_record = self.env['hop.purchasebill.line.barcode'].sudo().search([('name', '=', barcode)])

            if barcode_record:
                if barcode_record.stage == 'sale':
                    error_messages.append(f"{barcode_record.name} is already sold  {barcode_record.origin}")
                elif barcode_record.stage == 'purchase_return':
                    error_messages.append(f"{barcode_record.name} is already a Purchase Return  {barcode_record.origin}")
                elif barcode_record.stage == 'replace':
                    error_messages.append(f"{barcode_record.name} is already replaced {barcode_record.origin}")
            else:
                error_messages.append(f"{barcode} not found in the system.")

        return "\n".join(error_messages)




        