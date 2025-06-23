from math import fabs
from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.exceptions import UserError
from num2words import num2words


class salebillreturnmst(models.Model):
    _inherit = "hop.salebillreturn"

    def get_salebill_data(self):
        self.env['hop.fatch.salebill.record'].sudo().search([]).unlink()
        sale_records = self.env['hop.salebill'].sudo().search([('party_id','=',self.party_id.id)])
        # if len(sale_records) >1 :
        #     sale_bill_lines = self.env['hop.salebill.line'].sudo().search([('mst_id','in',tuple(sale_records.ids))])
        # else:
        sale_bill_lines = self.env['hop.salebill.line'].sudo().search([('mst_id','=',sale_records.ids)])
        if sale_bill_lines:
            for line in sale_bill_lines:
                sale_bill_ret_lines = self.env['hop.salebillreturn.line'].sudo().search([('salebill_line_id','=',line.id),('mst_id','!=',None)])
                billreturn_pcs = self.env['hop.unit.mst'].total_pcs_cal(sale_bill_ret_lines)
                billreturn_meter = self.env['hop.unit.mst'].total_meter_cal(sale_bill_ret_lines)
                billreturn_weight=self.env['hop.unit.mst'].total_weight_cal(sale_bill_ret_lines)
                sale_barcode_ids_list = sale_bill_lines.barcode_ids.ids
                sale_return_barcode_ids_list = sale_bill_ret_lines.barcode_ids.ids
                pending_barcode = list(set(sale_barcode_ids_list) - set(sale_return_barcode_ids_list))
                if line.unit_id.check_order_and_bill_zero(line,sale_bill_ret_lines):
                    continue

                self.env['hop.fatch.salebill.record'].create(
                                    {
                                        'barcode_ids':[(6, 0, pending_barcode)],
                                        'date': line.mst_id.date,
                                        'party_id': line.mst_id.party_id.id,
                                        'product_id': line.product_id.id,
                                        'hsn_id': line.hsn_id.id,   
                                        'pcs': line.pcs,
                                        'cut': line.cut,
                                        'meter': line.meter,
                                        'weight':line.weight,
                                        'unit_id': line.unit_id.id,
                                        'rate':line.rate,
                                        'include_rate':line.include_rate,
                                        'amount':line.amount,
                                        'disc_per':line.disc_per,
                                        'disc_per2':line.disc_per2,
                                        'add_amt': line.add_amt,
                                        'pcs':line.pcs ,
                                        'meter':line.meter ,
                                        'weight':line.weight ,
                                        'billreturn_pcs':billreturn_pcs,
                                        'billreturn_meter':billreturn_meter,
                                        'billreturn_weight':billreturn_weight,
                                        'bal_pcs':line.pcs - billreturn_pcs,
                                        'bal_meter':line.meter - billreturn_meter,
                                        'bal_weight':line.weight - billreturn_weight,
                                        'gst_ids': line.gst_ids.ids,
                                        'final_amount':line.final_amt,
                                        # 'order_id':line.order_id.id,
                                        # 'order_line_id':line.order_line_id.id,
                                        'salebill_id':line.mst_id.id,
                                        'salebill_line_id':line.id,
                                        'sale_bill_return_id':self.id,
                                        'is_gst_include':self.is_gst_include,

                                    })   
        salebill_fetch_record = self.env['hop.fatch.salebill.record'].sudo().search([]) 
        if not salebill_fetch_record:
            raise ValidationError("No Record")
        
    def unlink(self):
        list_barcode = []
        for line in self.line_id:
            for barcode in line.barcode_ids:
                list_barcode.append(barcode)
        res = super(salebillreturnmst,self).unlink()
        for barcode in list_barcode:
            sale_bill_lines = self.env['hop.salebill.line'].sudo().search([('barcode_ids','in',barcode.ids)])
            barcode.origin =  sale_bill_lines.mst_id.name
            barcode.stage = 'sale'
            barcode.sale_id = sale_bill_lines.mst_id.id
        return res

class SaleBillreturnLine(models.Model):
    _inherit = "hop.salebillreturn.line"

    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_salebill_return_barcode_id",copy=True)

    @api.onchange('barcode_ids')
    def _onchange_barcode_ids(self):
        self.pcs = len(self.barcode_ids)

    def write(self, vals):
        old_barcode = self.barcode_ids
        for barcode in old_barcode:
            barcode.origin =  False
            barcode.stage = 'new'
            
        ret = super(SaleBillreturnLine, self).write(vals)
        for barcode in self.barcode_ids:
            barcode.origin = False
            barcode.stage = 'new'
        return ret
    
    def unlink(self):
        barcodes = self.barcode_ids
        res = super(SaleBillreturnLine,self).unlink()
        for barcode in barcodes:
            barcode.origin =  False
            barcode.stage = 'new'
        return res

class FatchsalebillRecord(models.TransientModel):
    _inherit = 'hop.fatch.salebill.record'

    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_fatch_salebill_return_barcode_id",copy=True)

    def get_sale_vals(self,line):
        res = super(FatchsalebillRecord, self).get_sale_vals(line)
        res.update({
           'barcode_ids':[(6, 0, line.barcode_ids.ids)] , 
        })
        return res
    

    