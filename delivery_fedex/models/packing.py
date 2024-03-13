# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _, tools

class Packing(models.Model):
    _inherit = 'stock.quant.package'

    tacking_number = fields.Char(string='Tacking Number')
