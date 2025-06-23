import xml.etree.ElementTree as xee
from odoo import api, models, fields, _
from lxml import etree
class InheritPurchaseBill(models.Model):
    _inherit = 'hop.purchasebill'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        form_view_references = ['transaction.purchasebill_form']
        for form_view_ref in form_view_references:
            form_view = self.env.ref(form_view_ref)
            arch_tree = etree.fromstring(form_view.arch)

            if arch_tree.tag == 'form':
                tree_tag = arch_tree.find(".//tree[@name='line_id']")
                if tree_tag is not None:
                    if 'editable' in tree_tag.attrib:
                        del tree_tag.attrib['editable']
                updated_arch = etree.tostring(arch_tree, pretty_print=True, encoding='unicode')
                form_view.sudo().write({'arch': updated_arch})
        return res
    
class InheritPurchaseBill(models.Model):
    _inherit = 'hop.purchasebill.line'

    barcode_line_id = fields.One2many('hop.purchasebill.line.barcode',"line_mst_id",copy=True)
    barcode = fields.Char(string="Barcode")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            self.barcode_line_id = False
            barcode_list = self.barcode.split(',')  # Split by comma
            barcode_list = [b.strip() for b in barcode_list if b.strip()]  # Remove empty values
            barcode_line_list = []
            for barcode in barcode_list:
                barcode_line_list.append((0,0,{
                    'name':barcode,
                    'stage':'new',
                    'product_id':self.product_id,
                    'purchase_name':self.mst_id.name,
                    'line_mst_id':self.id,
                }))
            self.barcode_line_id = barcode_line_list
        self.pcs = len(self.barcode_line_id)

class purchasebillLineBarcode(models.Model):
    _name = 'hop.purchasebill.line.barcode'

    name = fields.Char(string="Barcode",copy=False,tracking=True)
    stage = fields.Selection([
        ('new', 'New'),
        ('sale', 'Sale')],
        string='Stage',
        readonly=True,
        default='new')
    product_id = fields.Many2one('hop.product.mst','Product')
    origin = fields.Char(string="Sale Origin")
    purchase_name = fields.Char(string="Purchase")
    line_mst_id = fields.Many2one('hop.purchasebill.line','Purchase Bill Line',ondelete='cascade')