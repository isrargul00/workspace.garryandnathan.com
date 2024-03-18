from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
import tempfile
import binascii
import logging

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class QuickBook(models.TransientModel):
    _name = 'quick.book.invoice'

    name = fields.Char(string="Message", required=True)
    file = fields.Binary(string="Select File")

    def _get_or_create_product(self, product_name,sale):
        product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
        if not product:
            product = self.env['product.product'].create({'name': product_name,'list_price':sale})
        return product.id

    def action_notify(self):
        self.ensure_one()
        data = dict()
        if not self.file:
            raise UserError(_("Please upload file first."))
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(2)
        except Exception:
            raise UserError(_("Invalid file"))
        for row_no in range(1, sheet.nrows):
            try:

                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                if line[1] == '' and line[2] == '' and line[3] == '':
                    continue
                if line[2] in data:
                    row = data[line[2]]
                    date = xlrd.xldate.xldate_as_datetime(sheet.row(row_no)[1].value,workbook.datemode)
                    name = line[3]
                    partner_id = line[4]
                    product = line[3]
                    product_item = line[5]
                    qty = line[6]
                    sale_price = line[7]
                    row.append({
                        'date': date,
                        'memo': name,
                        'partner_id': partner_id,
                        'product': product_item,
                        'qty': qty,
                        'price_unit': sale_price,
                    })
                else:
                    data[line[2]] = list()
                    date = xlrd.xldate.xldate_as_datetime(sheet.row(row_no)[1].value, workbook.datemode)
                    name = line[3]
                    partner_id = line[4]
                    product = line[3]
                    product_item = line[5]
                    qty = line[6]
                    sale_price = line[7]
                    data[line[2]].append({
                        'date': date,
                        'memo': name,
                        'partner_id': partner_id,
                        'product': product_item,
                        'qty': qty,
                        'price_unit': sale_price,
                    })
            except IndexError:
                raise UserError(_("You have selected wrong option"))

        invoices = list()
        for key, value in data.items():
            partner = self.env['res.partner'].search([('name', '=', value[0]['partner_id'])], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': value[0]['partner_id']})
            invoice = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date':value[0]['date'] or fields.Date.today(),
                'cs_invoice_number': key,
                'invoice_line_ids': [
                    (0, None, {
                        'name': val.get('memo', ''),
                        'product_id': self._get_or_create_product(val.get('product'),val.get('price_unit', 0.0)),
                        'price_unit': val.get('price_unit', 0.0),
                        'quantity': val.get('qty', 1.0),
                    }) for val in value
                ]

            }
            invoices.append(invoice)
            print('invoice --', key)
        invs = self.env['account.move'].create(invoices)
        seq = 1000
        invs.action_post()
        for inv in invs:
            inv.sudo().write({'name':'INV/2024/1000'})
        success_animation = {'effect': {'fadeout': 'fast',
                                        'message': 'Invoice import Sucessfully!.' \
                                                   ' Page will reload.',
                                        'img_url': '/web/static/src/img/smile.svg',
                                        'type': 'rainbow_man'}}
        return success_animation
