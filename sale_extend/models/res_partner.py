from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    note = fields.Html(string="Terms and conditions")

    has_payment_token = fields.Boolean(compute='_compute_has_payment_token',string="Available Payment")

    def _compute_has_payment_token(self):
        for rec in self:
            rec.has_payment_token = True if rec.payment_token_count else False
