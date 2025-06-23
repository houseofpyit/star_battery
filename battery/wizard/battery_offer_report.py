from odoo import models ,fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from ... dynamic_report import report_field

class BatteryOfferReportWizard(models.TransientModel):
    _name = 'hop.battery.offer.report.wizard'


    offer_ids = fields.Many2many(
        "hop.battery.offer", string="offers")
    party_ids = fields.Many2many(
        "res.partner", string="Party",domain=['|',('acc_type','=','SALE_PARTY'),('is_common','=',True)])
    
    def tuple_return(self,cut_list):
        typle_list=''
        for i in cut_list:
            if typle_list == '':
                typle_list += '(' + str(i)
            else:
                typle_list += ',' + str(i)
        typle_list +=')'
        return typle_list
    
    def action_report_button(self):
        menu_id = self.env.ref('battery.menu_hop_battery_offer_root').id
        return {
            'name': 'Battery Offer Report',
            'type':'ir.actions.act_url',
            'url': f"/web#action=battery.offer.report&active_id={self.id}&cids={self.company_id.id}&menu_id={menu_id}",
            'target':'new'
        }


    def report_data(self):
        active_offer_records = False
        if not self.offer_ids:
            today = date.today()
            active_offer_records = self.env['hop.battery.offer'].sudo().search([('from_date','<=',today),('to_date','>=',today)])
        else:
            active_offer_records =  self.offer_ids
        results_list = []
        for line in active_offer_records:
            query = """ SELECT 
                    COALESCE(SUM(x.billpcs), 0) as sale, COALESCE(SUM(x.returnpcs), 0) AS sale_return, 
                    x.party_id,x.product_id,x.party_name,x.product_name
                FROM ( """
            query += f""" select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs , a.party_id,b.product_id ,c.name as party_name , d.name as product_name 
                        from hop_salebill as a 
                        inner join hop_salebill_line as b on a.id = b.mst_id 
                        left join res_partner as c on c.id = a.party_id
                        left join hop_product_mst as d on d.id = b.product_id

                        where a.date <=  '{str(self.env.user.fy_to_date)}'
                        and a.date >=  '{str(self.env.user.fy_from_date)}' """
            if self.party_ids:
                query += f""" and a.party_id in {self.tuple_return(self.party_ids.ids)} """
            
            if line.line_ids:
                query += f""" and b.product_id in {self.tuple_return(line.line_ids.mapped('product_id').ids)} """
            query += f""" group by a.party_id,b.product_id ,c.name ,d.name """
                            
            query += f"""   union all 
                            select COALESCE(sum(b.pcs),0) as billpcs ,0 as returnpcs, a.party_id,b.product_id ,c.name as party_name , d.name as product_name
                            from hop_salebillreturn as a 
                            inner join hop_salebillreturn_line as b on a.id = b.mst_id 
                            left join res_partner as c on c.id = a.party_id
                            left join hop_product_mst as d on d.id = b.product_id
                            where a.date <=  '{str(self.env.user.fy_to_date)}'
                            and a.date >=  '{str(self.env.user.fy_from_date)}' """
            
            if self.party_ids:
                query += f""" and a.party_id in {self.tuple_return(self.party_ids.ids)} """
            if line.line_ids:
                query += f""" and b.product_id in {self.tuple_return(line.line_ids.mapped('product_id').ids)} """
            query += f""" group by a.party_id,b.product_id ,c.name ,d.name """

            query += f""" ) x 
                        GROUP BY x.party_id, x.product_id, x.party_name, x.product_name; """

            # Execute query
            self.env.cr.execute(query)
            query_results = self.env.cr.fetchall()  # Fetch all results
            status =  'Pending'
            
            for record in query_results:
                flg = True
                sale ,sale_return, party_id, product_id, party_name, product_name = record
                target_qty = line.line_ids.filtered(lambda l: l.product_id.id == product_id).qty
                total_sale = sale - sale_return
                if target_qty <= total_sale:
                    status = 'Done'
                else:
                    flg = False

                if not flg:
                    status =  'Pending'
                if total_sale > target_qty:
                    status = status + "(+" + str(int(total_sale - target_qty)) +")"
                results_list.append({
                    "offer": line.name,        # Offer Name
                    "offer_from_date": line.from_date,  # Offer From Date
                    "offer_to_date": line.to_date,  # Offer To Date
                    "party": party_name,       # Party Name
                    "product_name": product_name,   # Product Name
                    "product_target_qty" : target_qty,
                    "sale": sale, 
                    "sale_return": sale_return,
                    "total_sale":sale - sale_return,
                    "status": status 
                })
        
        print("Final Result List:", results_list)  # Print final results list
        header = "Battery Offer Report"
        group = ['offer','party']
        return header,results_list,group,self.concise_columns_field()
    


    def concise_columns_field(self):
        columns = []
        # columns.append(report_field.char_field(self,'Offer','offer'))
        columns.append(report_field.char_field(self,'From Date','offer_from_date'))
        columns.append(report_field.char_field(self,'To Date','offer_to_date'))
        columns.append(report_field.char_field(self,'Party','party'))
        columns.append(report_field.char_field(self,'Product','product_name'))
        columns.append(report_field.float_field(self,'Target Qty','product_target_qty'))
        columns.append(report_field.float_field(self,'Sale Qty','sale'))
        columns.append(report_field.float_field(self,'Sale Return Qty','sale_return'))
        columns.append(report_field.float_field(self,'Total Sale','total_sale'))
        columns.append(report_field.char_field(self,'Status','status'))
        return columns
    



