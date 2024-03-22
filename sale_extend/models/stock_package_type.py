from odoo import models, fields, _, api


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    is_default = fields.Boolean("Default")
