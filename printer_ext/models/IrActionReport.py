from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval, time
import base64


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document, doc_format = super()._render_qweb_pdf(
            report_ref, res_ids=res_ids, data=data
        )
        if self.env.user.has_group('printer_ext.printer_ext_group_user'):
            attachment = self.env['ir.attachment'].create({
                'name': str(report_ref) + "- %s.pdf" % time.strftime('%Y-%m-%d - %H:%M:%S'),
                'raw': document,
                'type': 'binary',
                'mimetype': 'application/pdf',
            })
            job = self.env['printer.jobs'].create({
                'name': doc_format,
                'file': attachment.id or False,
            })
            attachment.res_id = job.id
            attachment.res_model = job._name
        return document, doc_format
