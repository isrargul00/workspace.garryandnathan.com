# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'

    delivery_package_type_id = fields.Many2one('stock.package.type', 'Delivery Package Type', check_company=True,
                                               default=lambda self: self.env['stock.package.type'].search(
                                                   [('is_default', '=', True)], limit=1))
