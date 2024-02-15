from odoo import fields, models, api, _
from odoo.tests.common import Form
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'
    cs_shipping_method = fields.Many2one('delivery.carrier', string="Shipping method",
                                         default=lambda self: self.env['delivery.carrier'].search(
                                             [('fedex_service_type', '=', 'FEDEX_GROUND')], limit=1) or False)
    cs_shipping_date = fields.Date(string="Shipping Date")
    cs_invoice_number = fields.Char(string="Invoice Number")

    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        self.cs_shipping_date = self.invoice_date

    def action_invoice_register_payment(self):
        invoices = self.search(
            [('state', '=', 'posted'), ('payment_state', '=', 'not_paid'), ('cs_invoice_number', '!=', False)],
            limit=300)
        if not invoices:
            raise UserError(_('No More Invoices.'))
        for rec in invoices:
            action_data = rec.action_register_payment()
            wizard = Form(self.env['account.payment.register'].with_context(action_data['context'])).save()
            wizard.payment_date = rec.invoice_date
            action = wizard.action_create_payments()