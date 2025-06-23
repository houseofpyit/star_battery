from odoo import api, models, fields
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from ...hop_account import ledger
from ...hop_account import os_adjustment
from ... dynamic_report import report_field

FETCH_RANGE = 2000

class ReplacementReportWizard(models.TransientModel):
    _name = "hop.replacement.report.wiz"
    _description= "Replacement Report Wizard"


    from_date = fields.Date("From Date",default=lambda self: self.env.user.fy_from_date)
    to_date = fields.Date("To Date",default=lambda self: self.env.user.fy_to_date)
    
    party_ids = fields.Many2many('res.partner',string="Party")
    company_ids = fields.Many2many("res.company", string="Companies", default=lambda self: self.env.company.ids)

    def tuple_return(self,cut_list):
        typle_list=''
        for i in cut_list:
            if typle_list == '':
                typle_list += '(' + str(i)
            else:
                typle_list += ',' + str(i)
        typle_list +=')'
        return typle_list

    def action_generate(self):
        menu_id = self.env.ref('battery.menu_hop_replacement_battery_root').id
        return {
            'name': 'Replacement Report',
            'type':'ir.actions.act_url',
            'url': f"/web#action=replace.battery&active_id={self.id}&cids={self.company_id.id}&menu_id={menu_id}",
            'target':'new'
        }
    
    
    def report_data(self):
        results_list = []
        query = f""" 
                    select c.name as party, d.name as product,TO_CHAR(b.date,'DD-MM-YYYY') as rep_date,e.name as barcode,a.id
                    from hop_replacement_battery as a
                    inner join hop_replacement_battery_line b on b.mst_id = a.id
                    left join res_partner c on c.id = a.party_id
                    left join hop_product_mst d on d.id = a.product_id
                    left join hop_purchasebill_line_barcode e on e.id = b.barcode_id

                    where b.date >=  '{str(self.from_date)}'
                    and b.date <=  '{str(self.to_date)}'
                """

        if self.party_ids:
            query += f""" and a.party_id in {self.tuple_return(self.party_ids.ids)} """


        self.env.cr.execute(query)
        query_result = self.env.cr.dictfetchall()

        for record in query_result:
            results_list.append({
                "rep_date":record.get('rep_date'), 
                "party":record.get('party'),
                "product":record.get('product'),
                "barcode":record.get('barcode'),
                "id":record.get('id')
            })

        print("Final Result List:", results_list)  # Print final results list
        header = "Battery Replacement Report"
        group = ['party']
        return header,results_list,group,self.concise_columns_field()
    


    def concise_columns_field(self):
        columns = []
        columns.append(report_field.char_field(self,'Replacement Date','rep_date'))
        columns.append(report_field.char_field(self,'Party','party'))
        columns.append(report_field.char_field(self,'Product','product'))
        columns.append(report_field.char_field(self,'Barcode','barcode'))
        return columns
