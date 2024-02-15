# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PrinterConf(models.Model):
    _name = 'machine.config'
    _description = 'machine.config'
    _rec_name = 'value'

    value = fields.Char('value')
    key = fields.Char('key')


class Printer(models.Model):
    _name = 'printer.jobs'
    _description = 'printer.jobs'

    state = fields.Selection([('waiting', 'Waiting'), ('done', 'Done')], default='waiting')
    name = fields.Char(string="name")
    file = fields.Many2one('ir.attachment')
    pdf = fields.Binary('Pdf')
