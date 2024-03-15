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
            'context': {'default_first_name': self.name,
                        'default_last_name': self.name,
                        'default_phone': self.phone,
                        'default_street': self.street,
                        'default_city': self.city,
                        'default_state': self.state_id.name,
                        'default_zip': self.zip,
                        'default_email': self.email,
                        # 'default_code': self.code,
                        'default_partner_id': self.id,
                        'default_country': self.country_id.code,
                        # 'default_cc_number': "4111111111111111",
                        }

        }

# 'context': self.env.context,
