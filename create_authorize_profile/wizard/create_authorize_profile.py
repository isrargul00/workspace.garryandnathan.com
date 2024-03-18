from odoo import fields, models, _

from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI
import os
import sys
import logging
import datetime
from uuid import uuid4

_logger = logging.getLogger(__name__)

month_list = [('01', 'January'),
              ('02', 'February'),
              ('03', 'March'),
              ('04', 'April'),
              ('05', 'May'),
              ('06', 'June'),
              ('07', 'July'),
              ('08', 'August'),
              ('09', 'September'),
              ('10', 'October'),
              ('11', 'November'),
              ('12', 'December')]


def year_selection():
    year = datetime.date.today().year
    year_list = []
    while year != 2031:  # end year
        year_list.append((str(year), str(year)))
        year += 1
    return year_list
class CreateAuthorizeProfilesWizard(models.TransientModel):
    _name = 'create.authorize.profile.wizard'
    _description = 'Create Authorize.net Profile Wizard'

    payment_type = fields.Selection([('creditCard', 'Credit/Debit Card'),
                                     ('bankAccount', 'Electronic Check')], default='creditCard')
    cc_number = fields.Char('Credit Card Number', size=16)
    expiration_date = fields.Char(compute='make_date')
    name = fields.Char(compute='make_name')
    email = fields.Char()
    partner_id = fields.Many2one('res.partner')

    bank_name = fields.Char()
    account_number = fields.Char()
    routing_number = fields.Char()
    name_on_account = fields.Char()
    account_type = fields.Selection([('checking', 'Personal Checking'),
                                     ('savings', 'Personal Savings'),
                                     ('businessChecking', 'Business Checking')])
    month = fields.Selection(month_list)
    year = fields.Selection(year_selection())

    def _default_payment_method_id(self):
        return [('provider_ids', '=', self.env.ref('payment.payment_provider_authorize').id)]

    payment_method_id = fields.Many2one(
        string="Payment Method", comodel_name='payment.method', required=True,
        domain=_default_payment_method_id, )

    def make_date(self):
        if self.month and self.year:
            self.expiration_date = self.year + "-" + self.month
        else:
            self.expiration_date = "2020-01"
            print(self.expiration_date)

    def create_customer_profile(self):
        try:
            success = False
            provider = self.env['payment.provider'].search(
                [('id', '=', self.env.ref('payment.payment_provider_authorize').id)], limit=1)
            authorize_API = AuthorizeAPI(provider)
            profile_dict = {
                'profile': {
                    'merchantCustomerId': ('ODOO-%s-%s' % (self.partner_id, uuid4().hex[:8]))[:20],
                    'email': self.email or '',
                },
            }
            if self.payment_type == 'creditCard':
                profile_dict['profile'].update(
                    {
                        "paymentProfiles": {
                            "customerType": "individual",
                            "payment": {
                                "creditCard": {
                                    "cardNumber": self.cc_number,
                                    "expirationDate": "%s-%s" % (self.year, self.month),
                                }
                            }
                        },
                    }
                )
            elif self.payment_type == 'bankAccount':
                profile_dict['profile'].update(
                    {
                        "paymentProfiles": {
                            "customerType": "individual",
                            "payment": {
                                "bankAccount": {
                                    "accountType": self.account_type,
                                    "routingNumber": self.routing_number,
                                    "accountNumber": self.account_number,
                                    "nameOnAccount": self.name_on_account
                                }
                            }
                        },
                    }
                )
            else:
                return
            if profile_dict:
                response = authorize_API._make_request('createCustomerProfileRequest', profile_dict)
                if not response.get('customerProfileId'):
                    _logger.warning(
                        "unable to create customer payment profile, data missing from transaction with "
                        "partner id: %(partner_id)s",
                        {
                            'partner_id': self.partner_id.id,
                        },
                    )
                    return False
                res = {
                    'profile_id': response.get('customerProfileId'),
                    'payment_profile_id': response.get('customerPaymentProfileIdList')[0]
                }

                response = authorize_API._make_request('getCustomerPaymentProfileRequest', {
                    'customerProfileId': res['profile_id'],
                    'customerPaymentProfileId': res['payment_profile_id'],
                })

                payment = response.get('paymentProfile', {}).get('payment', {})
                if 'creditCard' in payment:
                    # Authorize.net pads the card and account numbers with X's.
                    res['payment_details'] = payment.get('creditCard', {}).get('cardNumber')[-4:]
                else:
                    res['payment_details'] = payment.get('bankAccount', {}).get('accountNumber')[-4:]
                token = self.env['payment.token'].create({
                    'provider_id': provider.id,
                    'payment_method_id': self.payment_method_id.id,
                    'payment_details': res.get('payment_details'),
                    'partner_id': self.partner_id.id,
                    'provider_ref': res.get('payment_profile_id'),
                    'authorize_profile': res.get('profile_id'),
                })
                success = True
        finally:
            if success == True:
                success_animation = {'effect': {'fadeout': 'fast',
                                                'message': 'Profile Created Sucessfully!.' \
                                                           ' Page will reload.',
                                                'img_url': '/web/static/src/img/smile.svg',
                                                'type': 'rainbow_man'}}
                return success_animation

    if os.path.basename(__file__) == os.path.basename(sys.argv[0]):
        create_customer_profile()
