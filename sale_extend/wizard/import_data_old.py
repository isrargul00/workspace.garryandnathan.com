from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import Warning, UserError
import tempfile
import binascii
import logging

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class SystemEngineer(models.TransientModel):
    _name = 'system.engineer'

    name = fields.Char(string="Message", required=True)
    file = fields.Binary(string="Select File")
    product_file = fields.Binary(string="Product Select File")

    def action_notify(self):
        self.ensure_one()

        if not self.file:
            raise UserError(_("Please upload file first."))
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise UserError(_("Invalid file"))
        for row_no in range(1, sheet.nrows):
            try:

                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                user_id = self.env['res.users'].search([('name', '=', line[6])], limit=1)
                if not user_id:
                    user_id = self.env.user
                self.env['mail.activity'].create({
                    'display_name': 'text',
                    'summary': '3 Days!',
                    'date_deadline': datetime.datetime.now(),
                    'user_id': user_id.id,
                    'res_id': line[1],
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'crm.lead')]).id,
                    'activity_type_id': 4
                })

            except IndexError:
                raise UserError(_("You have selected wrong option"))
