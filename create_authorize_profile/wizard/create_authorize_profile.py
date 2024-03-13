from odoo import fields, models, _
from odoo.exceptions import UserError
from authorizenet import apicontractsv1
import authorizenet
from authorizenet.apicontrollers import *
import os
import sys
import random
import logging
import datetime

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

pr = '8sLFq96Pv'
tx = '58EELr6g53j7yU7n'
PRODUCTION = 'https://api2.authorize.net/xml/v1/request.api'


class CreateAuthorizeProfilesWizard(models.TransientModel):
    _name = 'create.authorize.profile.wizard'
    _description = 'Create Authorize.net Profile Wizard'

    payment_type = fields.Selection([('creditCard', 'Credit/Debit Card'),
                                     ('bankAccount', 'Electronic Check')])
    first_name = fields.Char()
    last_name = fields.Char()
    street = fields.Char()
    city = fields.Char()
    state = fields.Char()
    zip = fields.Char()
    email = fields.Char()
    code = fields.Char()
    cc_number = fields.Char('Credit Card Number', size=16)
    expiration_date = fields.Char(compute='make_date')
    name = fields.Char(compute='make_name')
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
    
    def make_date(self):
        if self.month and self.year:
            self.expiration_date = self.year + "-" + self.month
        else:
            self.expiration_date = "2020-01"
            print(self.expiration_date)

    def create_customer_profile(self):
        success = False
        try:
            merchantAuth = authorizenet.apicontractsv1.merchantAuthenticationType()
            merchantAuth.name = pr
            merchantAuth.transactionKey = tx

            createCustomerProfile = authorizenet.apicontractsv1.createCustomerProfileRequest()
            createCustomerProfile.merchantAuthentication = merchantAuth
            if self.email:
                createCustomerProfile.profile = authorizenet.apicontractsv1.customerProfileType(
                    self.last_name + " : " + str(random.randint(0, 10000)),
                    self.code, self.email)
            else:
                createCustomerProfile.profile = authorizenet.apicontractsv1.customerProfileType(
                    self.last_name + " : " + str(random.randint(0, 10000)),
                    self.code)

            profile_controller = createCustomerProfileController(createCustomerProfile)
            profile_controller.setenvironment(PRODUCTION)
            profile_controller.execute()

            profile_response = profile_controller.getresponse()

            if profile_response.messages.resultCode == "Ok":
                print("Successfully created a customer profile with id: %s" % profile_response.customerProfileId)
            else:
                print("Failed to create customer payment profile %s" % profile_response.messages.message[0]['text'].text)
                raise UserError(
                    _("Failed to create customer profile %s"))

            if self.payment_type == 'creditCard':
                creditCard = apicontractsv1.creditCardType()
                creditCard.cardNumber = self.cc_number
                creditCard.expirationDate = self.expiration_date

                payment = apicontractsv1.paymentType()
                payment.creditCard = creditCard

                billTo = apicontractsv1.customerAddressType()
                billTo.firstName = self.first_name
                billTo.lastName = self.last_name
                billTo.address = self.street
                billTo.city = self.city
                billTo.state = self.state
                billTo.zip = self.zip

                profile = apicontractsv1.customerPaymentProfileType()
                profile.payment = payment
                profile.billTo = billTo

                createCustomerPaymentProfile = apicontractsv1.createCustomerPaymentProfileRequest()
                createCustomerPaymentProfile.merchantAuthentication = merchantAuth
                createCustomerPaymentProfile.paymentProfile = profile
                print("customerProfileId in create_customer_payment_profile. customerProfileId = %s" % profile_response.customerProfileId)
                createCustomerPaymentProfile.customerProfileId = str(profile_response.customerProfileId)

                payment_controller = createCustomerPaymentProfileController(createCustomerPaymentProfile)
                payment_controller.setenvironment(PRODUCTION)
                payment_controller.execute()

                payment_response = payment_controller.getresponse()

                if payment_response.messages.resultCode == "Ok":
                    success = True
                    _logger.info("Successfully created a customer payment profile for %s with id: %s" % (self.partner_id.name, payment_response.customerPaymentProfileId))
                    token = self.env['payment.token'].create({'name': self.name,
                                                              'partner_id': self.partner_id.id,
                                                              'acquirer_id': 4,
                                                              'acquirer_ref': payment_response.customerPaymentProfileId,
                                                              'authorize_profile': profile_response.customerProfileId})
                else:
                    _logger.info("Failed to create customer payment profile %s" % payment_response.messages.message[0]['text'].text)
                    raise UserError(
                        _("Failed to create customer payment profile."))
                return profile_response, payment_response
            if self.payment_type == 'bankAccount':
                bankAccount = apicontractsv1.bankAccountType()
                bankAccount.accountType = self.account_type
                bankAccount.routingNumber = self.routing_number
                bankAccount.accountNumber = self.account_number
                bankAccount.nameOnAccount = self.name_on_account
                bankAccount.bankName = self.bank_name

                payment = apicontractsv1.paymentType()
                payment.bankAccount = bankAccount

                billTo = apicontractsv1.customerAddressType()
                billTo.firstName = self.first_name
                billTo.lastName = self.last_name
                billTo.address = self.street
                billTo.city = self.city
                billTo.state = self.state
                billTo.zip = self.zip

                profile = apicontractsv1.customerPaymentProfileType()
                profile.payment = payment
                profile.billTo = billTo

                createCustomerPaymentProfile = apicontractsv1.createCustomerPaymentProfileRequest()
                createCustomerPaymentProfile.merchantAuthentication = merchantAuth
                createCustomerPaymentProfile.paymentProfile = profile
                createCustomerPaymentProfile.customerProfileId = str(profile_response.customerProfileId)

                payment_controller = createCustomerPaymentProfileController(createCustomerPaymentProfile)
                payment_controller.setenvironment(PRODUCTION)
                payment_controller.execute()

                payment_response = payment_controller.getresponse()

                if payment_response.messages.resultCode == "Ok":
                    success = True
                    _logger.info("Successfully created a customer payment profile for %s with id: %s" % (
                    self.partner_id.name, payment_response.customerPaymentProfileId))
                    token = self.env['payment.token'].create({'name': self.name,
                                                              'partner_id': self.partner_id.id,
                                                              'acquirer_id': 14,
                                                              'acquirer_ref': payment_response.customerPaymentProfileId,
                                                              'authorize_profile': profile_response.customerProfileId})
                else:
                    _logger.info("Failed to create customer payment profile %s" % payment_response.messages.message[0][
                        'text'].text)
                    raise UserError(
                        _("Failed to create customer payment profile."))
                return profile_response, payment_response
        finally:
            if self.cc_number:
                self.clear_cc()
            if success == True:
                success_animation = {'effect': {'fadeout': 'fast',
                                                'message': 'Profile Created Sucessfully!.'\
                                                           ' Page will reload.',
                                                'img_url': '/web/static/src/img/smile.svg',
                                                'type': 'rainbow_man'}}
                return success_animation


    if os.path.basename(__file__) == os.path.basename(sys.argv[0]):
        create_customer_profile()

    def clear_cc(self):
        self.cc_number = self.name

    def make_name(self):
        if self.payment_type == 'creditCard':
            self.name = "XXXX" + self.cc_number[12:16]
        elif self.payment_type == 'bankAccount':
            self.name = "XXXX" + self.account_number[12:16]




