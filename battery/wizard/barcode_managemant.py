from odoo import api, models, fields
from datetime import date, datetime, timedelta
from ... dynamic_report import report_field


def tuple_return(cut_list):
    typle_list=''
    for i in cut_list:
        if typle_list == '':
            typle_list += '(' + str(i)
        else:
            typle_list += ',' + str(i)
    typle_list +=')'
    return typle_list

class BarcodeManagemantReport(models.TransientModel):
    _name = 'barcode.managemant.rpt.wizard'
    _description = "Barcode Managemant Report"

    from_date = fields.Date("From Date",default=lambda self: self.env.user.fy_from_date)
    to_date = fields.Date("To Date",default=lambda self: self.env.user.fy_to_date)
    stage = fields.Selection([
        ('New', 'New'),
        ('Sale', 'Sale'),
        ('Replace', 'Replace'),],
        string='Stage')

    product_id = fields.Many2many('hop.product.mst',string="Product")

    def get_barcode_rpt(self):
        menu_id = self.env.ref('dynamic_report.report_menu').id
        return{
            'name': 'Barcode Managemant Report',
            'type':'ir.actions.act_url',
            'url': f"/web#action=barcode.managemant.rpt&active_id={self.id}&cids={self.company_id.id}&menu_id={menu_id}",
            'target':'new'
        }        
    
    def get_barcode_report(self, from_date=False, to_date=False, product_id=False, company_id=False, fields=False, table_join=False, condition=False, ordrby=False):
    # Base SELECT
        query = """
            SELECT
                a.id,
                a.name,
                a.date,
                a.bill_chr,
                a.bill_no,
                a.party_id,
                d.name AS party,
                f.name AS product,
                c.product_id,
                c.name AS barcode,
                CASE
                    WHEN COALESCE(c.sale_id, 0) > 0 THEN 'Sale'
                    WHEN COALESCE(c.replace_id, 0) > 0 THEN 'Replace'
                    ELSE 'New'
                END AS status,  
                COALESCE(sb.id, 0) AS sale_bill_id,
                COALESCE(sb.name, '') AS sale_bill_name,
                COALESCE(TO_CHAR(sb.date, 'DD-MM-YYYY'), '') AS sale_bill_date
        """

        if fields:
            query += f", {fields}"

        # Base FROM and JOIN
        query += """
            FROM hop_purchasebill AS a
            LEFT JOIN hop_purchasebill_line AS b ON b.mst_id = a.id
            LEFT JOIN hop_purchasebill_line_barcode AS c ON c.line_mst_id = b.id
            LEFT JOIN res_partner AS d ON a.party_id = d.id
            LEFT JOIN hop_product_mst AS f ON f.id = c.product_id
            LEFT JOIN hop_salebill AS sb ON sb.id = c.sale_id
        """

        if table_join:
            query += f" {table_join} "

        # WHERE conditions
        where_conditions = ["c.id IS NOT NULL"]

        if from_date:
            where_conditions.append(f"a.date >= '{from_date}'")
        if to_date:
            where_conditions.append(f"a.date <= '{to_date}'")
        if product_id:
            where_conditions.append(f"c.product_id IN {tuple_return(product_id)}")
        if company_id:
            where_conditions.append(f"a.company_id = '{company_id}'")
        if condition:
            where_conditions.append(condition)

        if self.stage:
            where_conditions.append(f"""
                CASE
                    WHEN COALESCE(c.sale_id, 0) > 0 THEN 'Sale'
                    WHEN COALESCE(c.replace_id, 0) > 0 THEN 'Replace'
                    ELSE 'New'
                END = '{self.stage}'
            """)

        # Append WHERE clause
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        # Add ORDER BY
        query += " ORDER BY a.date ASC"
        if ordrby:
            query += f", {ordrby}"

        # Execute the query
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()
        business_type = self.env['ir.config_parameter'].sudo().get_param('business_type')
        return results, business_type


    def get_report_barcode(self):

        header = ""
        group = ""
        result = self.get_barcode_report(self.from_date, self.to_date, self.product_id.ids)
        if self.from_date:
            fm_dt = self.from_date.strftime("%d-%m-%Y")
            to_dt = self.to_date.strftime("%d-%m-%Y")
            header = "Barcode Managemant Reporting Period Between " + str(fm_dt) + " And " + str(to_dt) 

        business_type =  result[1]
        return header,result[0],group,self.barcode_columns_field(business_type)
    
    def barcode_columns_field(self,business_type):
        decimal_amount = self.env.ref('master.decimal_amount').digits
        decimal_meter = self.env.ref('master.decimal_meter').digits 
        columns = []
        columns.append(report_field.char_field(self,'id','id',visible=False))
        columns.append(report_field.char_field(self,'name','Name'))
        columns.append(report_field.char_field(self,'Date','date'))
        columns.append(report_field.char_field(self,'Bill Chr','bill_chr'))
        columns.append(report_field.char_field(self,'Bill No','bill_no'))
        columns.append(report_field.char_field(self,'Party Name','party'))
        columns.append(report_field.char_field(self,'Product Name','product'))
        columns.append(report_field.char_field(self,'Barcode','barcode'))
        columns.append(report_field.char_field(self,'Status','status'))
        columns.append(report_field.char_field(self,'Sale Bill','sale_bill_name'))
        columns.append(report_field.char_field(self,'Sale Bill Date','sale_bill_date'))
        return columns
    
    