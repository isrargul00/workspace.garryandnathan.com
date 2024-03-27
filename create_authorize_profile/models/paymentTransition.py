import logging
import pprint
import re
import unicodedata
from datetime import datetime

import psycopg2
from dateutil import relativedelta
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import consteq, format_amount, ustr
from odoo.tools.misc import hmac as hmac_tool

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _handle_notification_data(self, provider_code, notification_data):
        tx = super()._handle_notification_data(provider_code, notification_data)
        tx.payment_id.message_post(body=_(notification_data.get('response').get('x_response_reason_text')))
        return tx
