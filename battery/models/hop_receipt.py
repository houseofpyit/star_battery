from odoo import models ,fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import re
from ...hop_account import ledger

class HopReceipt(models.Model):
    _inherit = "hop.receipt"
    
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
    

class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''
        if partner.acc_type == "BANK":
            if partner.remarks:
                name = name + " (" + partner.remarks + ")"
        if partner.city_id:
             name = name + ' , ' + partner.city_id.name
        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = self._get_contact_name(partner, name)
        if self._context.get('show_address'):
            address =  partner._display_address(without_company=True)
            splitted_names = [n.strip() for n in address.split("\n") if n.strip()]
            cleaned_address = ", ".join(splitted_names)
            name =   name + "\n" + cleaned_address

        if partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if partner.gstno:
            name = "%s ‒ %s" % (name, partner.gstno)
        return name