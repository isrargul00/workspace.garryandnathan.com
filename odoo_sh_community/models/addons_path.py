from odoo import models, fields, api
from odoo.tools import config


class AddonsPath(models.Model):
    _name = 'addons.path'
    _description = 'Addons Path'
    _rec_name = 'path'

    path = fields.Char(required=True)

    def action_reset_path(self):
        addons_path = config['addons_path'].split(',')
        for path in self:
            if path.path and path.path not in addons_path:
                # addons_path.insert(0, self.path)
                addons_path.append(path)
        config['addons_path'] = ','.join(addons_path)
        config.save()

    @api.model
    def create(self, values):
        # On create a new path, must create the path in OS and add it to config
        addons_path = config['addons_path'].split(',')
        path = values.get('path', False)
        # if config._is_addons_path(self.path) and self.path not in addons_path:
        if path and path not in addons_path:
            # addons_path.insert(0, self.path)
            addons_path.append(path)
            config['addons_path'] = ','.join(addons_path)
            config.save()
        return super(AddonsPath, self).create(values)
