from odoo import models, _


class ResPartnerExt(models.Model):
    _inherit = 'res.partner'

    def action_authorize_wizard(self):
        view = self.env.ref('create_authorize_profile.authorize_customer_profile_wizard')
        return {
            'name': _('Authorize.net Saved Payment Creation Wizard'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.authorize.profile.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_email': self.email,
                'default_partner_id': self.id,
            }

        }
