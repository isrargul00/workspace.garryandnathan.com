from odoo import models, fields, api, _


class SOTemplate(models.Model):
    _name = 'so.template'
    _description = 'so.template'

    name = fields.Char(string='Template Name')
    line_ids = fields.One2many('so.template.line', 'so_id', 'Lines')



class SOTemplateLines(models.Model):
    _name = 'so.template.line'
    _description = 'so.template.line'

    so_id = fields.Many2one('so.template', 'so template')
    product_id = fields.Many2one('product.template', 'Product')
    quantity = fields.Float('Quantity')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_template_id = fields.Many2one('so.template')
    has_payment_token = fields.Boolean(related='partner_id.has_payment_token', string="Available Payment")

    @api.onchange('so_template_id')
    def _onnchange_so_template_id(self):
        if self.so_template_id:
            self.order_line = [(5, 0), ]
            self.order_line = [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                })
                for line in self.so_template_id.line_ids
            ]

    @api.depends('partner_id')
    def _compute_note(self):
        for record in self:
            record.note = record.partner_id.note if record.partner_id else False
