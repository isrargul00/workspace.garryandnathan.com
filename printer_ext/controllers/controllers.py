# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.http import request
import json
import base64


class PrinterController(http.Controller):
    @http.route('/printer/report/get', type='http', auth='public')
    def get_reports(self, **kw):
        key = request.params.get('key') or False
        value = request.params.get('value') or False
        auth = request.env['machine.config'].sudo().search([('key', '=', key), ('value', '=', value)])
        if auth:
            report_list = request.env['printer.jobs'].sudo().search([('state', '=', 'waiting')])
            if report_list:
                return json.dumps([
                    {
                        'id': report.id,
                        'data': report.file.datas.decode('utf-8') if report.file else '',
                    }
                    for report in report_list
                ])
            else:
                return json.dumps({
                    "result": "No job found."
                })
        else:
            return json.dumps({
                "result": "auth error"
            })

    @http.route('/printer/report/set', type='http', auth='public')
    def set_reports(self, **kw):
        key = request.params.get('key') or False
        value = request.params.get('value') or False
        auth = request.env['machine.config'].sudo().search([('key', '=', key), ('value', '=', value)])
        if auth:
            id = request.params.get('id') or False
            if id:
                id = json.loads(id)
                job = request.env['printer.jobs'].sudo().search([('id', 'in', id)])
                if job:
                    job.write({'state': 'done'})
                    return json.dumps({
                        "result": "success"
                    })
                else:
                    return json.dumps({
                        "result": "No Found"
                    })
            else:
                return json.dumps({
                    "result": "error"
                })
        else:
            return json.dumps({
                "result": "auth error "
            })
