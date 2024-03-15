from odoo import api, Command, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.depends('payment_method_line_id')
    def _compute_suitable_payment_token_ids(self):
        for wizard in self:
            if wizard.can_edit_wizard and wizard.use_electronic_payment_method:
                wizard.suitable_payment_token_ids = self.env['payment.token'].sudo().search([
                    *self.env['payment.token']._check_company_domain(wizard.company_id),
                    # ('provider_id.capture_manually', '=', False),
                    ('partner_id', '=', wizard.partner_id.id),
                    ('provider_id', '=', wizard.payment_method_line_id.payment_provider_id.id),
                ])
            else:
                wizard.suitable_payment_token_ids = [Command.clear()]