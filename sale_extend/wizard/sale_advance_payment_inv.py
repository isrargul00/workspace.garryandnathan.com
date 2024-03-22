from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import format_date, frozendict


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        self._check_amount_is_positive()
        invoices = self._create_invoices(self.sale_order_ids)
        pickings = self.sale_order_ids.picking_ids.filtered(lambda l: l.picking_type_code == 'outgoing')
        if pickings:
            invoices.write({
                'cs_shipping_date': pickings.scheduled_date
            })
        return self.sale_order_ids.action_view_invoice(invoices=invoices)
