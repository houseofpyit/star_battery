from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class Purchasebillreturnmst(models.Model):
    _inherit = "hop.purchasebillreturn"


    def get_purchasebill_data(self):
        self.env['hop.fatch.purchasebill.record'].sudo().search([]).unlink()
        purchase_records = self.env['hop.purchasebill'].sudo().search([('party_id','=',self.party_id.id)])
        # if len(purchase_records) >1 :
        #     purchase_bill_lines = self.env['hop.purchasebill.line'].sudo().search([('mst_id','in',tuple(purchase_records.ids))])
        # else:
        purchase_bill_lines = self.env['hop.purchasebill.line'].sudo().search([('mst_id','=',purchase_records.ids)])
        if purchase_bill_lines:
            for line in purchase_bill_lines:
                purchase_bill_ret_lines = self.env['hop.purchasebillreturn.line'].sudo().search([('purchasebill_line_id','=',line.id),('mst_id','!=',None)])
                billreturn_pcs = self.env['hop.unit.mst'].total_pcs_cal(purchase_bill_ret_lines)
                billreturn_meter = self.env['hop.unit.mst'].total_meter_cal(purchase_bill_ret_lines)
                billreturn_weight=self.env['hop.unit.mst'].total_weight_cal(purchase_bill_ret_lines)
                purchase_barcode_ids_list = purchase_bill_lines.barcode_line_id.ids
                purchase_return_barcode_ids_list = purchase_bill_ret_lines.barcode_ids.ids

                pending_barcode = list(set(purchase_barcode_ids_list) - set(purchase_return_barcode_ids_list))
                if line.unit_id.check_order_and_bill_zero(line,purchase_bill_ret_lines):
                    continue

                self.env['hop.fatch.purchasebill.record'].create(
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
                                        # 'weight':line.weight - billreturn_weight,
                                        'final_amount':line.final_amt,
                                        'gst_ids': line.gst_ids.ids,
                                        # 'order_id':line.order_id.id,
                                        # 'order_line_id':line.order_line_id.id,
                                        'purc_bill_id':line.mst_id.id,
                                        'purchasebill_line_id':line.id,
                                        'purchase_bill_return_id':self.id,
                                    })   
        purchasebill_fetch_record = self.env['hop.fatch.purchasebill.record'].sudo().search([]) 
        if not purchasebill_fetch_record:
            raise ValidationError("No Record")
        
    def unlink(self):
        list_barcode = []
        for line in self.line_id:
            for barcode in line.barcode_ids:
                list_barcode.append(barcode)
        res = super(Purchasebillreturnmst,self).unlink()
        for barcode in list_barcode:
            barcode.origin =  False
            barcode.stage = 'new'
        return res

class PurchaseBillreturnLine(models.Model):
    _inherit = 'hop.purchasebillreturn.line'

    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_purchasebill_return_barcode_id",copy=True)

    @api.onchange('barcode_ids')
    def _onchange_barcode_ids(self):
        self.pcs = len(self.barcode_ids)

    def write(self, vals):
        old_barcode = self.barcode_ids
        for barcode in old_barcode:
            barcode.origin =  False
            barcode.stage = 'new'
        ret = super(PurchaseBillreturnLine, self).write(vals)
        for barcode in self.barcode_ids:
            barcode.origin =  self.mst_id.name
            barcode.stage = 'purchase_return'
        return ret
    
    def unlink(self):
        barcodes = self.barcode_ids
        res = super(PurchaseBillreturnLine,self).unlink()
        for barcode in barcodes:
            barcode.origin =  False
            barcode.stage = 'new'
        return res

    

class FatchPurchasebillRecord(models.TransientModel):
    _inherit = 'hop.fatch.purchasebill.record'

    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_fatch_purchasebill_return_barcode_id",copy=True)

    def get_purcbill_vals(self,line):
        res = super(FatchPurchasebillRecord, self).get_purcbill_vals(line)
        res.update({
           'barcode_ids':[(6, 0, line.barcode_ids.ids)] , 
        })
        return res
    

    