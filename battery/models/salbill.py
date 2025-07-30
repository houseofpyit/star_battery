from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import re
from ...hop_account import ledger
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class HopInheritSalebill(models.Model):
    _inherit = "hop.salebill"

    mobile_no = fields.Char(string="Mobile No",related='party_id.mobile')
    city_id = fields.Many2one('res.city', string="City",related='party_id.city_id')
    due_date = fields.Date(string='Due Date',default=fields.Date.context_today,tracking=True)
    payment_acc_id = fields.Many2one('res.partner',string="Payment A/C",domain=[('acc_type', 'in', ['BANK', 'CASH'])])
    payment_amt = fields.Float(string="Payment Amount",digits='Amount')
    bank_acc_id = fields.Many2one('res.partner',string="Bank A/C",domain=[('acc_type', 'in', ['BANK', 'CASH'])])
    bank_amt = fields.Float(string="Payment Amount",digits='Amount')

    def update_due_date(self):
        for res in self.search([]):
            res.due_date =  res.date + timedelta(days=res.due_days)
            res._onchange_date()
            
    @api.onchange('date')
    def _onchange_date(self):
        if self.date:
            self.due_date =  self.date + timedelta(days=self.due_days)
        for line  in self.line_id:
            if line.product_id: 
                line.warranty = line.product_id.warranty + line.product_id.distributor_warranty
                line.warranty_end_date = self.date + relativedelta(months=line.warranty or 0)

    @api.model
    def create(self, vals):
        ret = super(HopInheritSalebill, self).create(vals)
        for line  in ret.line_id:
            for barcode in line.barcode_ids:
                barcode.origin = ret.name
                barcode.stage = 'sale'
                barcode.sale_id = ret.id
        return ret
    
    def write(self, vals):
        old_barcode_list = []
        for line  in self.line_id:
            for barcode in line.barcode_ids: 
                old_barcode_list.append(barcode)
        for barcode in old_barcode_list:
            barcode.origin = False
            barcode.stage = 'new'
            barcode.sale_id = 0
        ret = super(HopInheritSalebill, self).write(vals)
        for line  in self.line_id:
            for barcode in line.barcode_ids: 
                barcode.stage = 'sale'
                barcode.origin = self.name
                barcode.sale_id = self.id
                
        return ret

    @api.depends('barcode_active')
    def _compute_barcode_active(self):
        self.sudo().with_context(compute_method=True).barcode_active = True

    @api.model
    def default_get(self, fields):
        res = super(HopInheritSalebill, self).default_get(fields)
        res['barcode_active'] = True
        return res
    
    @api.depends('party_id')
    @api.onchange('party_id')
    def _party_onchange(self):
        res = super(HopInheritSalebill, self)._party_onchange()
        if self.date:
            if self.due_days > 0 :
                self.due_date =  self.date + timedelta(days=self.due_days)
        for line in self.line_id:
            line._onchange_product_id()
        return res
    
    @api.onchange('line_id','tcs_per','compute_final_amt','tot_g_disc_amt','g_disc_amt')
    @api.depends('line_id','tcs_per','compute_final_amt','tot_g_disc_amt','g_disc_amt')
    def _final_amt_calculate(self):
        res = super(HopInheritSalebill, self)._final_amt_calculate()
        if self.party_id :
            self.party_total_purchase()
        return res

    def party_total_purchase(self):
        for i in self.line_id.sudo():
            if i.product_id:
                query = f""" select COALESCE(sum(x.billpcs),0) - COALESCE(sum(x.returnpcs),0) as total_sale from(
                                select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs 
                                from hop_salebill as a 
                                inner join hop_salebill_line as b on a.id = b.mst_id 
                                where a.party_id = {str(self.party_id.id)} and b.product_id = {str(i.product_id.id)}
                                and a.date <=  '{str(self.env.user.fy_to_date)}'
                                and a.date >=  '{str(self.env.user.fy_from_date)}'
                                
                                union all 
                                select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs 
                                from hop_salebillreturn as a 
                                inner join hop_salebillreturn_line as b on a.id = b.mst_id 
                                where a.party_id = {str(self.party_id.id)} and b.product_id = {str(i.product_id.id)}
                                and a.date <=  '{str(self.env.user.fy_to_date)}'
                                and a.date >=  '{str(self.env.user.fy_from_date)}'
                            ) x
                        """
                self.env.cr.execute(query)
                query_result = self.env.cr.dictfetchone()
                if query_result:
                    i.total_sale = query_result.get('total_sale',0)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            # Updated: Apply regex directly instead of splitting by commas first
            # pattern = r'[A-Za-z]*\(\d{2}-\d{2}\)\d+|[A-Za-z0-9]+'
            # pattern = r'[A-Za-z0-9]*\(\d{2}-\d{2}\)\d+|[A-Za-z0-9]+'
            # pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+'
            pattern = r'[A-Za-z0-9]*\(\d{1,2}[-/]\d{1,2}\)\d+|[A-Z0-9]{16,}'
            barcode_list = re.findall(pattern, self.barcode)

            # Remove empty values and strip spaces
            barcode_list = [b.strip() for b in barcode_list if b.strip()] 

            error_str = self.env['hop.purchasebill.line.barcode'].barcode_check(barcode_list)
            order_list = []
            if error_str != '':
                raise ValidationError(error_str)
            else:
                barcodes = self.env['hop.purchasebill.line.barcode'].sudo().search([('name', 'in', barcode_list)])

                product_id = barcodes[0].product_id
                price_rec = self.env['party.price.line'].search([('mst_id','=',self.party_id.id),('product_id','=',product_id.id)],limit=1)
                sale_rate = 0
                if price_rec:
                    sale_rate = price_rec.price
                line_record = self.line_id.filtered(lambda l: l.product_id.id == product_id.id)
                if line_record :
                    barcode_list_all = list(set(line_record.barcode_ids.ids + barcodes.ids))
                    line_record.barcode_ids = [(6, 0, barcode_list_all)]
                    line_record.pcs = len(line_record.barcode_ids)
                else:
                    order_list.append((0, 0, {
                            'product_id': product_id.id,
                            'hsn_id': product_id.hsn_id.id,
                            'pcs': len(barcodes.ids),
                            'cut':product_id.cut,
                            'rate' : sale_rate,
                            'unit_id': product_id.unit_id.id,
                            'barcode_ids':[(6, 0, barcodes.ids)]

                        }))
                    self.line_id = order_list
                self.barcode = ''
            for line in self.line_id:
                line._onchange_hsn_id()
                line.pcs = len(line.barcode_ids)
                line._onchange_calc_amt()
        self._onchange_date()

    def unlink(self):
        list_barcode = []
        for line in self.line_id:
            for barcode in line.barcode_ids:
                list_barcode.append(barcode)
        res = super(HopInheritSalebill,self).unlink()
        for barcode in list_barcode:
            barcode.origin =  False
            barcode.stage = 'new'
            barcode.sale_id = 0
        return res
          
    def print_line_mapped(self):
        line_list =[]
        for product in set(self.line_id.mapped('product_id')):
            barcode_str = ''
            for line in self.line_id.filtered(lambda l: l.product_id.id == product.id):
                for barcode in line.barcode_ids:
                    if barcode_str == '':
                        barcode_str = barcode.name 
                    else :
                        barcode_str = barcode_str + " , " + barcode.name 
            line_list.append({
                'product_name':product.name,
                'hsn_name':product.hsn_id.name if product.hsn_id else '' ,
                'pcs':sum(self.line_id.filtered(lambda l: l.product_id.id == product.id).mapped('pcs')),
                'rate':self.line_id.filtered(lambda l: l.product_id.id == product.id)[0].rate,
                'unit':self.line_id.filtered(lambda l: l.product_id.id == product.id)[0].unit_id.name,
                'amount':sum(self.line_id.filtered(lambda l: l.product_id.id == product.id).mapped('amount')),
                'barcode': barcode_str,
                'warranty':self.line_id.filtered(lambda l: l.product_id.id == product.id)[0].warranty,
                'warranty_end_date':self.line_id.filtered(lambda l: l.product_id.id == product.id)[0].warranty_end_date.strftime('%d/%m/%Y')
            })
        
        return line_list
    
    def party_pre_balance(self):
        self.ensure_one()
        cfromdate = self.env.user.fy_from_date
        ctodate = self.env.user.fy_to_date
 
        bal_amt = ledger.getLedgerData(self,self.party_id.ids,cfromdate,self.date,cfromdate,ctodate,only_party_balance =True)
        colon_index = bal_amt.index(':')
        if bal_amt[:colon_index - 1].strip() == 'CR':
            pvr_amt = - (float(bal_amt[colon_index + 1:]) + self.net_amt)
        else:
            pvr_amt = float(bal_amt[colon_index + 1:]) - self.net_amt
        return pvr_amt
            
class InheritSaleBillLine(models.Model):
    _inherit = 'hop.salebill.line'

    warranty = fields.Integer(string='Warranty (Months)')
    warranty_end_date = fields.Date(string='Warranty Date')

    @api.model
    def create(self,vals):
        res =  super(InheritSaleBillLine,self).create(vals)
        price_rec = self.env['party.price.line'].search([('mst_id','=',res.mst_id.party_id.id),('product_id','=',res.product_id.id)],limit=1)
        if price_rec:
            price_rec.price = res.rate
        else:
            vals = {
                'mst_id': res.mst_id.party_id.id,
                'product_id': res.product_id.id,
                'price': res.rate,   
                'company_id':res.company_id.id
                }
            self.env['party.price.line'].create(vals)
        return res

    barcode_ids = fields.Many2many('hop.purchasebill.line.barcode',"ref_salebill_barcode_id",copy=True)

    total_sale = fields.Float("Total Sale")
    offer_status = fields.Text(string="Offer Status",copy=False)

    @api.onchange('barcode_ids')
    def _onchange_barcode_ids(self):
        self.pcs = len(self.barcode_ids)
        # barcode_list = []
        # for bar in self.barcode_ids:
        #     barcode_list.append(bar.name)
        # if barcode_list:
        #     error_str = self.env['hop.purchasebill.line.barcode'].barcode_check(barcode_list)
        #     if error_str != '':
        #         error_str =  error_str + "kavin"
        #         raise ValidationError(error_str)
    
    def tuple_return(self,cut_list):
        typle_list=''
        for i in cut_list:
            if typle_list == '':
                typle_list += '(' + str(i)
            else:
                typle_list += ',' + str(i)
        typle_list +=')'
        return typle_list
    

    @api.onchange('product_id','pcs')
    def _onchange_product_id(self):
        res = super(InheritSaleBillLine, self)._onchange_product_id()
        if self.product_id and self.mst_id.party_id:
            offer_tital = ''
            if self.mst_id.date:
                active_offer_records = self.env['hop.battery.offer'].sudo().search([('from_date','<=',self.mst_id.date),('to_date','>=',self.mst_id.date)])

                for line in active_offer_records:
                    query = """ SELECT 
                            COALESCE(SUM(x.billpcs), 0) as sale, COALESCE(SUM(x.returnpcs), 0) AS sale_return, 
                            x.party_id,
                            x.product_id,
                            x.party_name,
                            x.product_name
                        FROM ( """
                    query += f""" select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs , a.party_id,b.product_id ,c.name as party_name , d.name as product_name 
                                    from hop_salebill as a 
                                    inner join hop_salebill_line as b on a.id = b.mst_id 
                                    left join res_partner as c on c.id = a.party_id
                                    left join hop_product_mst as d on d.id = b.product_id

                                    where a.date <=  '{str(self.env.user.fy_to_date)}'
                                    and a.date >=  '{str(self.env.user.fy_from_date)}' """
                    if self.mst_id.party_id:
                        query += f""" and a.party_id in {self.tuple_return(self.mst_id.party_id.ids)} """
                    
                    if line.line_ids:
                        query += f""" and b.product_id in {self.tuple_return(line.line_ids.mapped('product_id').ids)} """
                    query += f""" group by a.party_id,b.product_id ,c.name ,d.name """
                                    
                    query += f"""                union all 
                                    select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs, a.party_id,b.product_id ,c.name as party_name , d.name as product_name
                                    from hop_salebillreturn as a 
                                    inner join hop_salebillreturn_line as b on a.id = b.mst_id 
                                    left join res_partner as c on c.id = a.party_id
                                    left join hop_product_mst as d on d.id = b.product_id
                                    where a.date <=  '{str(self.env.user.fy_to_date)}'
                                    and a.date >=  '{str(self.env.user.fy_from_date)}' """
                    
                    if self.mst_id.party_id:
                        query += f""" and a.party_id in {self.tuple_return(self.mst_id.party_id.ids)} """
                    if line.line_ids:
                        query += f""" and b.product_id in {self.tuple_return(line.line_ids.mapped('product_id').ids)} """
                    query += f""" group by a.party_id,b.product_id ,c.name ,d.name """

                    query += f""" ) x 
                                GROUP BY x.party_id, x.product_id, x.party_name, x.product_name; """

                    # Execute query
                    self.env.cr.execute(query)
                    query_results = self.env.cr.fetchall()  # Fetch all results
                    status =  'Pending'
                    flg = True
                    for record in query_results:
                        sale ,sale_return, party_id, product_id, party_name, product_name = record
                        target_qty = line.line_ids.filtered(lambda l: l.product_id.id == product_id).qty
                        if self.product_id.name  == product_name:
                            total_sale = sale - sale_return + self.pcs
                        else:
                            total_sale = sale - sale_return 
                        if target_qty <= total_sale:
                                status = 'Done'
                        else:
                            flg = False

                        if not flg:
                            status =  'Pending'

                    if  status == 'Done':
                        if offer_tital == '':
                            offer_tital = line.name + " : " + " Done "
                        else:
                            offer_tital =  offer_tital + " , " + line.name + " : " + " Done "
                    flg = True        
            self.offer_status = offer_tital
        self.rate = 0
        price_rec = self.env['party.price.line'].search([('mst_id','=',self.mst_id.party_id.id),('product_id','=',self.product_id.id)],limit=1)
        if price_rec:
            self.rate = price_rec.price

        if self.product_id: 
            self.warranty = self.product_id.warranty + self.product_id.distributor_warranty
            self.warranty_end_date = self.mst_id.date + relativedelta(months=self.warranty or 0)

        return res

    def unlink(self):
        barcode = self.barcode_ids
        res = super(InheritSaleBillLine,self).unlink()
        barcode.origin =  False
        barcode.stage = 'new'
        barcode.sale_id = 0
        return res
    
