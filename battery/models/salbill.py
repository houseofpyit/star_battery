from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date

class HopInheritSalebill(models.Model):
    _inherit = "hop.salebill"

    @api.model
    def create(self, vals):
        ret = super(HopInheritSalebill, self).create(vals)
        for line  in ret.line_id:
            line._onchange_product_id()
        return ret
    
    def write(self, vals):
        ret = super(HopInheritSalebill, self).write(vals)
        for line  in self.line_id:
            line._onchange_product_id()
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
            barcode = self.env['hop.purchasebill.line.barcode'].search([('name','=',self.barcode)])
            if not  barcode :
                raise ValidationError('No Barcode Found !!!')
            order_list = []
            sale_barcode = self.env['hop.salebill.line'].search([('barcode_id', '=', barcode.id)])
            if sale_barcode:
                str_error = "This barcode has already been sold in " + sale_barcode.mst_id.name
                raise ValidationError(str_error)
            
            replacement = self.env['hop.replacement.battery'].search([('barcode_id', '=', barcode.id)])
            if replacement:
                raise ValidationError("This battery has already been replaced.")
            replacement_line_record = self.env['hop.replacement.battery.line'].search([('barcode_id', '=', barcode.id)])
            if replacement_line_record:
                raise ValidationError("This battery has already been replaced.")
            if barcode :
                product = self.env['hop.product.mst'].search([('id','=',barcode.product_id.id)])
                if not product:
                    self.barcode = ''
                    raise ValidationError('No Barcode Found !!!')
                flag = True
                for i in self.line_id:
                    if i.product_id.id == product.id:
                        self.barcode = ''
                        raise ValidationError("Duplicate barcode is not allowed.")
                        i.pcs += 1
                        flag = False
                        break
                if flag:
                    order_list.append((0, 0, {
                        'product_id': product.id,
                        'hsn_id': product.hsn_id.id,
                        'pcs': 1,
                        'cut':product.cut,
                        'rate' : product.sale_rate,
                        'unit_id': product.unit_id.id,
                        'barcode_id':barcode.id,

                    }))
                    self.line_id = order_list
                self.barcode = ''
                for line in self.line_id:
                    line._onchange_calc_amt()
                    line._onchange_hsn_id()
                    line.barcode_id.origin = self.name
            else:
                raise ValidationError('No Barcode Found !!!')

class InheritSaleBillLine(models.Model):
    _inherit = 'hop.salebill.line'

    barcode_id = book_id = fields.Many2one('hop.purchasebill.line.barcode',string="Barcode")
    total_sale = fields.Float("Total Sale")
    offer_status = fields.Text(string="Offer Status",copy=False)
    

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
                active_offer_records = self.env['hop.battery.offer'].search([('from_date','<=',self.mst_id.date),('to_date','>=',self.mst_id.date)])

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
        return res

    def unlink(self):
        barcode = self.barcode_id
        res = super(InheritSaleBillLine,self).unlink()
        barcode.origin =  False
        return res
    
