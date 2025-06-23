from odoo import models ,fields, api

def tuple_return(cut_list):
    typle_list=''
    for i in cut_list:
        if typle_list == '':
            typle_list += '(' + str(i)
        else:
            typle_list += ',' + str(i)
    typle_list +=')'
    return typle_list

class inheritStockReport(models.Model):
    _inherit="stock.report"
    _description = 'Stock Report'
    
    def opening_stock(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
    
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).opening_stock(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def purchase_order(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).purchase_order(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def purchasebill(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).purchasebill(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def salebill_return(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).salebill_return(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def sale_order(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).sale_order(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def salebill(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).salebill(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def pur_bill_return(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).pur_bill_return(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def issue(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).issue(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def receive(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).receive(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def pln_receive(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).pln_receive(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def new_product_receive(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).new_product_receive(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def inward(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).inward(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def outward(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).outward(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_mill_sent(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_mill_sent(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_mill_receipt(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_mill_receipt(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
   
    def hop_mill_receipt_finish(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_mill_receipt_finish(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_mill_return_grey(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_mill_return_grey(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    

    def hop_greychallan(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_mill_return_grey(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_greybill_return(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_greybill_return(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_grey_sale_challan(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_grey_sale_challan(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def hop_grey_salebill_return(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_grey_salebill_return(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res

    def hop_manufacturing(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_manufacturing(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res


    def hop_manufacturing_line(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 
        fields = " , 0 as replace"
        res = super(inheritStockReport, self).hop_manufacturing_line(from_date,to_date,product_ids,category_ids,company_ids,fields,join_table,condition,group_by)
        return res
    
    def replace_battery(self,from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False): 

        query = """  select COALESCE(c.name,'') as itemname , COALESCE(d.name,'') as category , 0 as op_pcs , 0 as op_meter , 0 as op_weight , 
                   0 as pur_pcs ,0 as pur_meter , 0 as pur_weight , 
                    0 as sale_ret_pcs , 0 as sale_ret_meter , 0 as sale_ret_weight , 
                    0 as sale_order_pcs , 0 as sale_order_meter , 0 as sale_order_weight , 
                    0 as pur_ret_pcs , 0 as pur_ret_meter , 0 as pur_ret_weight , 
                    0 as job_issue_pcs , 0 as job_issue_meter , 0 as job_issue_weight , 
                    0 as job_receive_pcs , 0 as job_receive_meter , 0 as job_receive_weight ,
                    0 as inward_pcs ,0 as inward_meter ,
                    0 as outward_pcs , 0 as outward_meter ,COALESCE(sum(c.minimum_qty),0) as minimum_qty  ,e.name as unit 
                    ,0 as grey_chln_taka,0 as grey_return_taka ,0 as sale_taka,0  as sale_return_taka,
                0 as grey_chln_meter,0 as grey_return_meter ,0 as sale_meter,0  as sale_return_meter ,
                0 as mill_sent_taka ,0 as mill_sent_meter,
                0 as  mill_rec_taka , 0 as mill_rec_meter,
                0 as gr_rt_mill_taka,0 as gr_rt_mill_meter,
                0 as manufacturing_qty,0 as manufacturing_line_qty,
                'replace' as module ,-1 * COALESCE(sum(b.qty),0) as pcs , 0  as meter , 0 as weight ,
                f.name as serial , a.party_id as party_id, b.date as date, b.product_id,COALESCE(sum(b.qty),0) as replace
                    """
        if fields :
            query += fields
        query += """ from hop_replacement_battery as a 
                    inner join hop_replacement_battery_line as b on a.id = b.mst_id 
                    left join hop_product_mst as c on c.id =  b.product_id
                    left join hop_category_mst as d on d.id = c.category_id
                    left join hop_unit_mst as e on e.id = c.unit_id  
                    left join hop_salebill as f on b.salebill_id = f.id """
        if join_table:
            query += join_table

        query += """ where 1=1 """ 
        
        query += " and b.date <=  '"+ str(to_date) +"'"
        query += " and b.date >=  '"+ str(from_date) +"'"
        query += ' and a.company_id in ' + tuple_return(company_ids.ids)
        if product_ids:     
            query += ' and b.product_id in ' + tuple_return(product_ids.ids)
        if category_ids: 
            query += ' and c.category_id in ' + tuple_return(category_ids.ids) 
        
        if condition:
            query += condition
            
            
        query += ' group by '
        query += """ c.name , d.name ,e.name ,b.date,a.party_id, b.product_id,f.name"""
        if group_by:
             query += group_by
        return query
    

    def stock_report_query(self,from_date,to_date,product_ids,category_ids,company_ids):

        query = super(inheritStockReport, self).stock_report_query(from_date,to_date,product_ids,category_ids,company_ids)
        query +=" union all "
        query += self.replace_battery(from_date,to_date,product_ids,category_ids,company_ids,fields=False,join_table=False,condition=False,group_by=False)            
        return query
    
    def stock_report(self,from_date,to_date,product_ids,category_ids,stock_status,stock_wise,company_ids,fields=False,bal_pcs_fields = False,bal_meter_fields = False,bal_weight_fields=False,group_by=False):
        query = self.stock_report_query(from_date,to_date,product_ids,category_ids,company_ids)
        allQuery = """ select x.product_id ,x.itemname  , x.category  ,
                sum(x.op_pcs) as op_pcs  , sum(x.op_meter) as op_meter , sum(x.op_weight) as op_weight , 
                sum(x.pur_pcs) as pur_pcs ,sum(x.pur_meter) as pur_meter , sum(x.pur_weight) as pur_weight , 
                sum(x.sale_ret_pcs) as sale_ret_pcs ,sum(x.sale_ret_meter) as sale_ret_meter ,  sum(x.sale_ret_weight) as sale_ret_weight , 
                sum(x.sale_order_pcs)  as sale_order_pcs ,  sum(x.sale_order_meter) as sale_order_meter , sum(x.sale_order_weight)  as sale_order_weight , 
                sum(x.pur_ret_pcs) as pur_ret_pcs , sum(x.pur_ret_meter) as pur_ret_meter , sum(x.pur_ret_weight) as pur_ret_weight , 
                sum(x.job_issue_pcs) as job_issue_pcs ,sum(x.job_issue_meter) as job_issue_meter , sum(x.job_issue_weight) as job_issue_weight , 
                sum(x.job_receive_pcs) as job_receive_pcs , sum(x.job_receive_meter) as job_receive_meter , sum(x.job_receive_weight) as job_receive_weight, 
                sum(x.inward_pcs) as inward_pcs ,sum(x.inward_meter) as inward_meter,
                sum(x.outward_pcs) as outward_pcs ,sum(x.outward_meter) as outward_meter,x.minimum_qty 
                ,sum(x.grey_chln_taka) as grey_chln_taka,sum(x.grey_return_taka) as grey_return_taka ,sum(x.sale_taka) as sale_taka,sum(x.sale_return_taka)  as sale_return_taka,
                sum(x.grey_chln_meter) as grey_chln_meter,sum(x.grey_return_meter) as grey_return_meter ,sum(x.sale_meter) as sale_meter,sum(x.sale_return_meter)  as sale_return_meter 
                ,sum(x.mill_sent_taka) as mill_sent_taka,sum(x.mill_rec_taka) as mill_rec_taka ,sum(x.gr_rt_mill_taka) as gr_rt_mill_taka,
                sum(x.mill_sent_meter) as mill_sent_meter,sum(x.mill_rec_meter) as mill_rec_meter ,sum(x.gr_rt_mill_meter) as gr_rt_mill_meter,
                sum(x.manufacturing_qty) as manufacturing_qty,sum(x.manufacturing_line_qty) as  manufacturing_line_qty,sum(x.replace) as replace ,"""
        if fields:
            allQuery += fields
        bal_pcs= " sum(x.op_pcs) + sum(x.pur_pcs)+ sum(x.sale_ret_pcs) - sum(x.sale_order_pcs) - sum(x.pur_ret_pcs) - sum(x.job_issue_pcs) + sum(x.job_receive_pcs) + sum(x.inward_pcs) - sum(x.outward_pcs) + sum(x.grey_chln_taka) - sum(x.grey_return_taka) - sum(x.sale_taka) + sum(x.sale_return_taka) - sum(x.mill_sent_taka) + sum(x.mill_rec_taka) + sum(x.gr_rt_mill_taka) + sum(x.manufacturing_qty) - sum(x.manufacturing_line_qty) - sum(x.replace) "
        if bal_pcs_fields:
            bal_pcs += bal_pcs_fields
        allQuery += bal_pcs +  " as bal_pcs, "

        bal_meter = " sum(x.op_meter) + sum(x.pur_meter)+ sum(x.sale_ret_meter) - sum(x.sale_order_meter) - sum(x.pur_ret_meter) - sum(x.job_issue_meter) + sum(x.job_receive_meter) + sum(x.inward_meter) - sum(x.outward_meter) + sum(x.grey_chln_meter) - sum(x.grey_return_meter) - sum(x.sale_meter) + sum(x.sale_return_meter) - sum(x.mill_sent_meter) + sum(x.mill_rec_meter) + sum(x.gr_rt_mill_meter) "
        if bal_meter_fields:
            bal_meter += bal_meter_fields
        allQuery += bal_meter + " as bal_meter, "

        bal_weight = " sum(x.op_weight) + sum(x.pur_weight)+ sum(x.sale_ret_weight) - sum(x.sale_order_weight) - sum(x.pur_ret_weight) - sum(x.job_issue_weight) + sum(x.job_receive_weight) "
        if bal_weight_fields :
            bal_weight += bal_weight_fields

        allQuery += bal_weight + " as bal_weight"
        allQuery += " ,x.unit "
        allQuery +=  """ from (%s) as x  """%query
        allQuery += " where 1=1 "
        allQuery += " group by "
        allQuery += " x.itemname ,x.category,x.unit,x.product_id,x.minimum_qty "
        if group_by:
            allQuery += group_by
        allQuery += " having  1=1 "
        if stock_wise == 'pcswise':
            if stock_status == 'pending':
                allQuery += "  and " + bal_pcs + " > 0 "
            elif stock_status == 'close':
                allQuery += " and " + bal_pcs + " = 0 "
        elif stock_wise == 'meterwise':
            if stock_status == 'pending':
                allQuery += "  and " + bal_meter + " > 0 "
            elif stock_status == 'close':
                allQuery += " and " + bal_meter + " = 0 "
        elif stock_wise == 'weightwise':
            if stock_status == 'pending':
                allQuery += "  and " + bal_weight + " > 0 "
            elif stock_status == 'close':
                allQuery += " and " + bal_weight + " = 0 "      
        elif stock_wise == 'pcsmeterweightwise':
            if stock_status == 'pending':
                allQuery += "  and " + bal_pcs + " > 0 "
                allQuery += "  and " + bal_meter + " > 0 "
                allQuery += "  and " + bal_weight + " > 0 "
            elif stock_status == 'close':
                allQuery += "  and " + bal_pcs + " = 0 "
                allQuery += "  and " + bal_meter + " = 0 "
                allQuery += "  and " + bal_weight + " = 0 "
        # print("*********************---------------------",allQuery)
        return allQuery