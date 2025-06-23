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

class HopAgentSaleRptWiz(models.TransientModel):
    _name = 'agent.sale.rpt.wizard'
    _description = "Agent Sale Report"

    from_date = fields.Date("From Date",default=lambda self: self.env.user.fy_from_date)
    to_date = fields.Date("To Date",default=lambda self: self.env.user.fy_to_date)
    agent_ids = fields.Many2many('res.partner','ref_agent_sale_rpt_agent_ids' ,string="Agent")
    product_ids = fields.Many2many('hop.product.mst','ref_agent_sale_rpt_product_ids',string="Product")
    party_ids = fields.Many2many('res.partner','ref_agent_sale_rpt_party_ids' ,string="Partys")
    company_id = fields.Many2one('res.company' ,string="Company", default=lambda self: self.env.company.id)
    type = fields.Selection([
        ('Product', 'Product'),
        ('Party Collection', 'Party Collection'),
        ],
        string='Product / Party Collection',
        default='Product')

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'Product':
            self.party_ids = False
        else:
            self.product_ids =  False

    def get_agent_sale_rpt(self):
        menu_id = self.env.ref('dynamic_report.report_menu').id
        return{
            'name': 'Agent Sale Report',
            'type':'ir.actions.act_url',
            'url': f"/web#action=agent.sale.rpt&active_id={self.id}&cids={self.company_id.id}&menu_id={menu_id}",
            'target':'new'
        }        
    
    def get_agent_sale_report(self, from_date=False, to_date=False, product_ids=False, agent_ids=False, company_id=False, fields=False, table_join=False, condition=False, ordrby=False):
        if self.type == 'Product':
            # Base SELECT
            query = """
                SELECT
                    a.id,
                    a.agent_id,
                    b.name AS agent_name,
                    COALESCE(TO_CHAR(a.date, 'DD-MM-YYYY'), '') AS agent_sale_date,
                    c.mst_id,
                    c.product_id,
                    d.name AS product_name,
                    c.total_qty,
                    c.return_qty,
                    c.sales_qty
            """

            # Add dynamic fields with aliases if provided
            if fields:
                query += fields

            # Base FROM and JOIN
            query += """
                FROM hop_agent_sale AS a
                LEFT JOIN res_partner AS b ON b.id = a.agent_id
                LEFT JOIN hop_agent_sale_line AS c ON c.mst_id = a.id
                LEFT JOIN hop_product_mst AS d ON d.id = c.product_id
            """

            if table_join:
                query += table_join  

            # WHERE clause with dynamic filters
            query += " WHERE "

            if from_date:
                query += "a.date >= '" + str(from_date) + "'"
            if to_date:
                query += " AND a.date <= '" + str(to_date) + "'"
            if product_ids:
                query += " AND c.product_id IN " + tuple_return(product_ids)
            if agent_ids:
                query += " AND a.agent_id IN " + tuple_return(agent_ids)
            if company_id:
                query += " AND a.company_id = '" + str(company_id) + "'"
            if condition:
                query += f" {condition}"

            # Add ordering
            query += " ORDER BY a.date ASC"
            if ordrby:
                query += ordrby

            # Execute the query
            self.env.cr.execute(query)
            results = self.env.cr.dictfetchall()
            business_type = self.env['ir.config_parameter'].sudo().get_param('business_type')
            return results, business_type
        else:
            # Base SELECT
            query = """
                SELECT
                    a.id,
                    a.agent_id,
                    b.name AS agent_name,
                    COALESCE(TO_CHAR(a.date, 'DD-MM-YYYY'), '') AS agent_sale_date,
                    c.mst_id,
                    c.party_id,
                    d.name AS party_name,
                    c.amount
            """

            # Add dynamic fields with aliases if provided
            if fields:
                query += fields

            # Base FROM and JOIN
            query += """
                FROM hop_agent_sale AS a
                LEFT JOIN res_partner AS b ON b.id = a.agent_id
                LEFT JOIN hop_agent_payment_line AS c ON c.mst_id = a.id
                LEFT JOIN res_partner AS d ON d.id = c.party_id
            """

            if table_join:
                query += table_join  

            # WHERE clause with dynamic filters
            query += " WHERE "

            if from_date:
                query += "a.date >= '" + str(from_date) + "'"
            if to_date:
                query += " AND a.date <= '" + str(to_date) + "'"
            if product_ids:
                query += " AND c.party_id IN " + tuple_return(product_ids)
            if agent_ids:
                query += " AND a.agent_id IN " + tuple_return(agent_ids)
            if company_id:
                query += " AND a.company_id = '" + str(company_id) + "'"
            if condition:
                query += f" {condition}"

            # Add ordering
            query += " ORDER BY a.date ASC"
            if ordrby:
                query += ordrby

            # Execute the query
            self.env.cr.execute(query)
            results = self.env.cr.dictfetchall()
            business_type = self.env['ir.config_parameter'].sudo().get_param('business_type')
            return results, business_type



    def get_report_agent_sale(self):

        header = ""
        group = ""
        result = self.get_agent_sale_report(self.from_date, self.to_date, self.product_ids.ids, self.agent_ids.ids, self.company_id.id)
        if self.from_date:
            fm_dt = self.from_date.strftime("%d-%m-%Y")
            to_dt = self.to_date.strftime("%d-%m-%Y")
            header = "Agent Sale Reporting Period Between " + str(fm_dt) + " And " + str(to_dt) 

        business_type =  result[1]
        return header,result[0],group,self.agent_columns_field(business_type)
    
    def agent_columns_field(self,business_type):

        
        decimal_amount = self.env.ref('master.decimal_amount').digits
        decimal_meter = self.env.ref('master.decimal_meter').digits 
        columns = []
        if self.type == 'Product':
            columns.append(report_field.char_field(self,'id','id',visible=False))
            columns.append(report_field.char_field(self,'Agent Name','agent_name'))
            columns.append(report_field.char_field(self,'Date','agent_sale_date'))
            columns.append(report_field.char_field(self,'Product Name','product_name'))
            columns.append(report_field.float_field(self,'Total Quantity','total_qty'))
            columns.append(report_field.float_field(self,'Return Quantity','return_qty'))
            columns.append(report_field.float_field(self,'Sales Quantity','sales_qty'))
        else:
            columns.append(report_field.char_field(self,'id','id',visible=False))
            columns.append(report_field.char_field(self,'Agent Name','agent_name'))
            columns.append(report_field.char_field(self,'Date','agent_sale_date'))
            columns.append(report_field.char_field(self,'Party Name','party_name'))
            columns.append(report_field.float_field(self,'Amount','amount'))
        return columns
    
    