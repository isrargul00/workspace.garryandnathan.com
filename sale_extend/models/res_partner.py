from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    note = fields.Html(string="Terms and conditions")