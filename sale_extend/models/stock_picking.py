from odoo import api, fields, models


class DeliveryMethod(models.Model):
    _inherit = 'delivery.carrier'

    is_default = fields.Boolean('Is Default')

    _sql_constraints = [('is_default_con', 'UNIQUE (is_default)', 'already selected one'), ]


class StcckPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_id = fields.Many2one("delivery.carrier")
    load_carrier = fields.Boolean(compute='_compute_load_carrier')

    def _compute_load_carrier(self):
        for rec in self:
            rec.load_carrier = False
            if not rec.carrier_id:
                rec.carrier_id = self.env['delivery.carrier'].search([('is_default', '=', True)], limit=1)


    def should_print_delivery_address(self):
        self.ensure_one()
        return self.move_ids and self.move_ids[0].partner_id and (self._is_to_external_location() or self.picking_type_code == 'internal')