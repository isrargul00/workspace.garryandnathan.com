# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import SUPERUSER_ID, api

from .models.module import PARAM_INSTALLED_CHECKSUMS, PARAM_ADDONS_PATH, PARAM_MY_MODULES_PATH


def uninstall_hook(env):
    env["ir.config_parameter"].set_param(PARAM_INSTALLED_CHECKSUMS, False)
    env["ir.config_parameter"].set_param(PARAM_ADDONS_PATH, False)
    env["ir.config_parameter"].set_param(PARAM_MY_MODULES_PATH, False)

    # env = api.Environment(cr, SUPERUSER_ID, {})
    # env["ir.config_parameter"].set_param(PARAM_INSTALLED_CHECKSUMS, False)
    # env["ir.config_parameter"].set_param(PARAM_ADDONS_PATH, False)
    # env["ir.config_parameter"].set_param(PARAM_MY_MODULES_PATH, False)
