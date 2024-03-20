# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class RecurringSaleSetting(models.Model):
    _name = 'recurring.sale.setting'
    _description = 'Configuration for Recurring Event'

    def set_next_execution_date(self, base_date):
        if self.interval_type == 'days':
            next_execution_date = base_date + relativedelta(days=+self.interval_number)
        elif self.interval_type == 'weeks':
            next_execution_date = base_date + relativedelta(weeks=+self.interval_number)
        elif self.interval_type == 'months':
            next_execution_date = base_date + relativedelta(months=+self.interval_number)
        elif self.interval_type == 'years':
            next_execution_date = base_date + relativedelta(years=+self.interval_number)
        self.next_execution_date = next_execution_date

    def create_recurring_sale(self):
        new_po_id = self.sale_order_id.copy()
        recurred_orders = self.recurred_sale_order_ids.ids
        recurred_orders.append(new_po_id.id)
        self.recurred_sale_order_ids = [(6, 0, recurred_orders)]
        if self.notification_user_id and self.notification_user_id.partner_id and self.notification_user_id.partner_id.email:
            template_id = self.env.ref('dev_recurring_sale_order.email_template_recurring_sale_order')
            template_id.send_mail(self.id, force_send=True)

    def process_recurring_sale_order_request(self):
        if self.interval_number <= 0:
            raise ValidationError(_('''Execute Every must be positive'''))
        self.set_next_execution_date(self.create_date.date())
        self.write({'state': 'processed'})

    def set_to_new(self):
        self.write({'state': 'new'})

    def get_reoccurred_order_url(self):
        orders_lst = self.recurred_sale_order_ids.ids
        latest_order = 0
        if orders_lst:
            latest_order = max(orders_lst)
        ir_param = self.env['ir.config_parameter'].sudo()
        base_url = ir_param.get_param('web.base.url')
        action_id = self.env.ref('sale.action_orders').id
        menu_id = self.env.ref('sale.menu_sale_order').id
        if base_url:
            base_url += '/web#id=%s&action=%s&model=%s&view_type=form&cids=&menu_id=%s' % (
                int(latest_order), action_id, 'sale.order', menu_id)
        return base_url

    def cron_action_recurring_sale(self):
        valid_recurring_ids = self.env['recurring.sale.setting'].search([('state', '=', 'processed'),
                                                                         ('next_execution_date', '!=', False)])
        print(valid_recurring_ids)
        if valid_recurring_ids:
            for valid_recurring_id in valid_recurring_ids:
                if valid_recurring_id.next_execution_date:
                    next_date = valid_recurring_id.next_execution_date
                    if valid_recurring_id.stop_date:
                        stop_date = valid_recurring_id.stop_date
                        if stop_date != date.today():
                            if next_date == date.today():
                                valid_recurring_id.create_recurring_sale()
                                valid_recurring_id.set_next_execution_date(valid_recurring_id.next_execution_date)

                    else:
                        if next_date == date.today():
                            valid_recurring_id.create_recurring_sale()
                            valid_recurring_id.set_next_execution_date(valid_recurring_id.next_execution_date)

    name = fields.Char(string='Name', required=True)
    state = fields.Selection(selection=[('new', 'New'),
                                        ('processed', 'Processed')], default='new', string='State')
    sale_order_id = fields.Many2one('sale.order', domain=[('state', '!=', 'cancel')], required=True,
                                    string='Sale Order')
    notification_user_id = fields.Many2one('res.users', string='Notify To',
                                           help='This user will be notify when Recurring Event is created')
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    interval_number = fields.Integer(string='Execute Every')
    interval_type = fields.Selection([('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months'),
                                      ('years', 'Years')], string='Interval Type', default='days', required=True)

    partner_id = fields.Many2one('res.partner', string='Organizer', readonly=True,default= lambda self: self.env.user.partner_id)
    stop_date = fields.Date(string='Stop Date', help='Onward this date recurring events will not be created',
                            copy=False)
    next_execution_date = fields.Date(string='Next Execution Date', copy=False)
    recurred_sale_order_ids = fields.Many2many('sale.order', string='Sale Order', copy=False)
    recurred_sale_order_data = fields.Integer(string='Recurred Sale Order', compute='_get_recurred_sale_order_data')

    def view_recurring_sale_orders(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['views'] = [(False, 'form')]
        action.update({'domain': [('id', 'in', self.recurred_sale_order_ids.ids)], })
        if len(self.recurred_sale_order_ids) == 1:
            action['res_id'] = self.sale_order_id.id
        return action

    def _get_recurred_sale_order_data(self):
        for record in self:
            record.recurred_sale_order_data = len(
                record.recurred_sale_order_ids.ids) if record.recurred_sale_order_ids.ids else False

