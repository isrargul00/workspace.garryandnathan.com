# -*- coding: utf-8 -*-

import logging
import os
import shutil
from os import path
from os.path import isdir as is_dir
from os.path import isfile
from os.path import join as path_join

import requests
from odoo import api, exceptions, fields, models, _, tools
from odoo import release
from odoo.tools import config

_logger = logging.getLogger(__name__)
import time
import subprocess
from datetime import datetime
from .module import PARAM_ADDONS_PATH

nlist_path = []
list_of_addons_paths = tools.config['addons_path'].split(",")
for path in list_of_addons_paths:
    nlist_path.append((path, path))

from ..controllers.main import ServerController


class RepositoryRepository(models.Model):
    _name = 'repository.repository'
    _rec_name = 'source'
    _description = 'Repository'

    def _selection_addons_path(self):
        nlist_path = []
        list_of_addons_paths = tools.config['addons_path'].split(",")
        for path in list_of_addons_paths:
            nlist_path.append((path, path))
        return nlist_path

    # @api.depends('module_ids') # no api.depends so it's computed every tyme
    def _compute_modules(self):
        module = self.env['ir.module.module']
        for repo in self:
            if repo.state == 'enabled':
                try:
                    module_names = find_modules(repo.path)
                    repo.module_ids = module.search([('name', 'in', module_names)])
                    repo.module_count = len(repo.module_ids)
                except:
                    repo.module_ids = False
                    repo.module_count = 0
            else:
                repo.module_ids = False
                repo.module_count = 0

    path = fields.Char('Path', required=True)
    source = fields.Char('Source', required=True)
    branch = fields.Char('Branch', default=release.series)
    rev_id = fields.Char('Last Revision', readonly=True)
    rev_date = fields.Datetime('Last Rev. Date', readonly=True)
    dirty = fields.Boolean('Dirty', readonly=True)
    module_ids = fields.Many2many('ir.module.module', string='Modules', compute=_compute_modules)
    module_count = fields.Integer('Modules', compute=_compute_modules)
    state = fields.Selection(string="Estado",
                             selection=[('draft', 'Borrador'), ('cloned', 'Clonado'), ('enabled', 'Enabled'),
                                        ('disabled', 'Disabled')], default='draft', readonly=True, )
    # addons_paths = fields.Selection(selection=_selection_addons_path,
    #                                 string="Add-ons Paths", help="Please choose one of these directories to put "
    #                                                              "your module in", )
    user = fields.Char(string='User', required=False)
    token = fields.Char(string='Token', required=False)
    log = fields.Text(string='Log', required=False, default='Log....')
    auto_pull = fields.Boolean('Auto Update (PULL)')

    def log_(self, mensaje):
        now = datetime.now()
        for record in self:
            if record.log:
                if len(str(record.log)) > 51600:
                    record.write({'log': '\n%s %s ' % (str(now.strftime("%m/%d/%Y, %H:%M:%S")), str(mensaje))})
                else:
                    record.write(
                        {'log': '\n%s %s %s' % (str(now.strftime("%m/%d/%Y, %H:%M:%S")), str(mensaje), str(self.log))})
                self.env.cr.commit()

    requirements = fields.Char(
        string='Requirements',
        required=False)

    @api.onchange('source')
    def _onchange_source(self):
        if self.source:
            self.path = self.get_path('-'.join([chunk.replace('.git', '') for chunk in self.source.split('/')[-2:]]))

    def get_path(self, path=False):
        self.ensure_one()
        conf_parameter = self.env['ir.config_parameter']
        if not path:
            return os.path.join(conf_parameter.get_param(PARAM_ADDONS_PATH, '/mnt/extra-addons'), self.path)
        else:
            return os.path.join(conf_parameter.get_param(PARAM_ADDONS_PATH, '/mnt/extra-addons'), path)

    def copy(self, default=None):
        raise exceptions.UserError(_("The repository cannot be cloned."))

    def unlink(self):
        if self.env.context.get('remove_repository'):
            for rec in self:
                if rec.state == 'enabled':
                    raise exceptions.UserError(_('Unable to remove an enabled repository.'))
                # res = Git(self.get_path())
                res = Git(source=rec.source, branch=rec.branch, path=rec.path, token=rec.token)
                res.load()
                res.remove()
        return super(RepositoryRepository, self).unlink()

    def action_open_modules(self):
        self.ensure_one()
        return {
            'name': self.source,
            'type': 'ir.actions.act_window',
            'res_model': 'ir.module.module',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
            'domain': [('id', 'in', self.module_ids.ids)]
        }

    def install_requirements(self):
        requirement_file = self.path + '/requirements.txt'
        try:
            if os.path.exists(requirement_file):
                subprocess.check_call(["pip3", "install", "-r", requirement_file])
        except Exception as e:
            self.log_("Exception exception occured: {}".format(e))
            try:
                if os.path.exists(requirement_file):
                    subprocess.check_call(["python3", "-m", "pip", "install", "-r", requirement_file])
            except Exception as e:
                self.log_("2do Exception exception occured: {}".format(e))

    def action_enabled(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied
        addons_path = config['addons_path'].split(',')
        if config._is_addons_path(self.path) and self.path not in addons_path:
            # addons_path.insert(0, self.path)
            addons_path.append(self.path)
            config['addons_path'] = ','.join(addons_path)
            config.save()
        self.state = 'enabled'
        requirement_file = self.path + '/requirements.txt'
        if os.path.exists(requirement_file):
            f = open(requirement_file, "r")
            self.requirements = f.read()
            self.install_requirements()

        # self._compute_apps()
        return self.env.ref(
            'base.action_view_base_module_update').read()[0]

    def action_remove(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied
        try:
            self.with_context(remove_repository=True).unlink()
        except Exception as e:
            raise exceptions.UserError(_(" '%s':\n%s") % (self.source, e))
        return {'type': 'ir.actions.act_window_close'}

    def restart(self):
        # /restart_server
        ServerController().restart_server()

    def action_update(self):
        self.ensure_one()
        flags = self.update()
        if any(flags):
            self.restart()

    def update(self):
        repos_updated_flags = []
        for repo in self:
            try:
                res = Git(source=repo.source, branch=repo.branch, path=repo.path, token=repo.token)
                res.load()
                flags = res.update()
                repos_updated_flags.append(flags)
                for l in res.log():
                    repo.log_(l)
                if flags:
                    repo.install_requirements()
                    repo._compute_modules()
                    repo.rev_date = fields.Datetime.now()
            except Exception as e:
                repo.log_("Exception exception occured: {}".format(e))
                raise exceptions.UserError(
                    _("A problem occurred while updating the repository. Review user permissions of the directory and the repository."
                      "\n **Help  Permissions Directory: sudo chown -R odoo:odoo /path/to/odoo/addons "
                      "\n sudo chmod -R u+rwx,g+rwx,o-rwx /path/to/odoo/addons "
                      "\n"
                      "\n **Help  Permissions Repository: Genere a token in github and add in the repository "
                      "\n "
                      "Error System '%s':\n%s") % (repo.source, e))
        return repos_updated_flags

    def update_module(self):
        self.env['ir.module.module'].upgrade_changed_checksum()

    def action_disable(self):
        self.ensure_one()
        self.state = 'disabled'
        if not self.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied
        addons_path = config['addons_path'].split(',')
        if self.path in addons_path:
            if self.module_ids.filtered(lambda r: r.state not in (
                    'uninstalled', 'uninstallable')):
                raise exceptions.UserError(
                    _('Some modules of this repository are installed.'))
            addons_path.remove(self.path)
            config['addons_path'] = ','.join(addons_path)
            config.save()

    def clone(self):
        self.ensure_one()
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError as e:
            try:
                os.makedirs(self.path)
            except Exception as e:
                raise exceptions.UserError(_('Error creating the directory: %s') % e)
        try:
            res = Git(source=self.source, branch=self.branch, path=self.path, token=self.token)
            res.load()
            res.clone()
            self.env.cr.commit()
            # If addons path wasn't selected, must create the config entry
            requirement_file = self.path + '/requirements.txt'
            if os.path.exists(requirement_file):
                f = open(requirement_file, "r")
                self.requirements = f.read()
                self.install_requirements()
            self.write({'state': 'cloned'})
            # self._compute_apps()
            self.env.cr.commit()
            self.restart()
        except Exception as e:
            self.write({'state': 'draft'})
            raise exceptions.UserError(_(
                "An error has occurred while Clone '%s': %s in the branch '%s'.\n"
                "Please check the repository URL and the branch name.") % (
                                           self.source, e, self.branch))

    def create_github_webhook(self):
        # validar que el usuario , token y source no esten vacios
        if not self.user or not self.token or not self.source:
            raise exceptions.UserError(_('The user, token and source fields are required.'))

        repo_name = self.source.split('/')[-1].replace('.git', '')
        github_api_url = 'https://api.github.com/repos/%s/%s/hooks' % (self.user, repo_name)

        # Sustituir 'TU_TOKEN' con tu token de acceso personal de GitHub.
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

        # Definir la configuración del webhook.
        web_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        webhook_endpoint = web_url + '/github_webhook'
        webhook_config = {
            'name': 'web',
            'config': {
                'url': webhook_endpoint,  # Reemplazar con la URL de tu endpoint Odoo.
                'content_type': 'json',
                'insecure_ssl': '0',
            },
            'events': ['push', 'pull_request'],
            'active': True,
        }
        # Realizar una solicitud POST para crear el webhook.
        response = requests.post(github_api_url, headers=headers, json=webhook_config)

        if response.status_code == 201:
            # Webhook creado exitosamente.
            webhook_data = response.json()
            webhook_id = webhook_data['id']

            # Registra el ID del webhook en el registro de Odoo o realiza cualquier otra operación necesaria.
            self.auto_pull = True
            self.log_("********************Webhook creado exitosamente********************************")
        else:
            self.log_("********************Error al crear el webhook********************************")
            self.log_(response.text)

    def delete_github_webhook(self):
        # Validar que el usuario, token y source no estén vacíos
        if not self.user or not self.token or not self.source:
            raise exceptions.UserError(_('The user, token, and source fields are required.'))

        repo_name = self.source.split('/')[-1].replace('.git', '')
        github_api_url = 'https://api.github.com/repos/%s/%s/hooks' % (self.user, repo_name)

        # Sustituir 'TU_TOKEN' con tu token de acceso personal de GitHub.
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        # Obtener la lista de webhooks del repositorio en GitHub
        response = requests.get(github_api_url, headers=headers)

        if response.status_code == 200:
            webhooks = response.json()
            for webhook in webhooks:
                if webhook['config']['url'].endswith('/github_webhook'):
                    # Encontramos el webhook que queremos eliminar
                    webhook_id = webhook['id']
                    # Realizar una solicitud DELETE para eliminar el webhook.
                    delete_url = f'{github_api_url}/{webhook_id}'
                    response = requests.delete(delete_url, headers=headers)
                    if response.status_code == 204:
                        self.log_("********************Webhook eliminado exitosamente********************************")
                        self.auto_pull = False
                    else:
                        # Manejar errores en caso de que la eliminación del webhook falle.
                        error_message = response.text
                        _logger.error(error_message)
                        raise exceptions.UserError(_('Error deleting webhook: %s') % error_message)
                    break
            else:
                # No se encontró el webhook
                raise exceptions.UserError(_('Webhook not found in the repository.'))
        else:
            raise exceptions.UserError(_('Error getting webhooks: %s') % response.text)

    def _default_repository_ids(self):
        res = self.env['repository.repository'].sudo()
        for path in config['addons_path'].split(','):
            git = Git(source=self.source, branch=self.branch, path=path, token=self.token)
            if git.load():
                data = git.info()
                result = res.search([('path', '=', data['path'])])
                if not result:
                    data.update({'state': 'enabled'})
                    result = res.create(data)
                    result._compute_apps()
                    self.env.cr.commit()
                else:
                    if not result.source:
                        result.write(data)
                    self.env.cr.commit()


def find_modules(path):
    return [module for module in os.listdir(path) if any(map(
        lambda f: isfile(path_join(path, module, f)), (
            '__manifest__.py', '__openerp__.py')))]


class Git:
    _source_http = None
    _source_git = None
    _branch = None
    _token = None
    _path = None
    _output_list = []

    def remove(self):
        if self._path and is_dir(self._path):
            shutil.rmtree(self._path)

    def is_initialized(self):
        print("Initializing git")
        if os.system(f"git -C \"{path}\" init") == 0:
            return True
        else:
            return False

    def __init__(self, source=None, branch=None, path=None, token=None):
        self._path = path
        self._token = token
        self._branch = branch
        if not self._token:
            self._source_http = source
            self._source_git = source
        else:
            try:
                source_git = "https://" + self._token + "@" + source.replace('https://', '')
                self._source_http = source
                self._source_git = source_git
            except Exception as e:
                raise exceptions.UserError(_("An error has occurred while cloning '%s':\n%s") % (source, str(e)))

    def load(self):
        if self._path and is_dir(path_join(self._path, '.git')):
            return True
        else:
            return False

    def clone(self):
        command = f"git clone --depth 1 --branch {self._branch} --single-branch {self._source_git} {self._path}"
        subprocess.run(command, shell=True, check=True)

    def info(self):
        data = {
            'path': self._path,
            'branch': self._branch,
            'source': self._source_http,
        }

        # Obtener la información del último commit
        command = f"git --git-dir={self._path}/.git --work-tree={self._path} log -1 --pretty=format:'%h|%ad|%s' --date=short"
        try:
            output = subprocess.check_output(command, shell=True, cwd=self._path)
            output_str = output.decode("utf-8")
            rev_id, rev_date, rev_msg = output_str.split("|")
            data['rev_id'] = rev_id
            data['rev_date'] = rev_date
        except subprocess.CalledProcessError:
            pass

        # Obtener la ruta del repositorio

        try:
            repo_url_command = "git config --get remote.origin.url"
            repo_url = subprocess.check_output(repo_url_command, shell=True, cwd=self._path,
                                               stderr=subprocess.STDOUT).decode().strip()
            data['source'] = repo_url
        except Exception as e:
            cmd = f"git config --global --add safe.directory {self._path}"
            subprocess.run(cmd, shell=True, check=True)
        try:
            repo_url_command = "git config --get remote.origin.url"
            repo_url = subprocess.check_output(repo_url_command, shell=True, cwd=self._path,
                                               stderr=subprocess.STDOUT).decode().strip()
            data['source'] = repo_url
        except Exception as e:
            _logger.error('Error al obtener la ruta del repositorio en la ruta: ' + str(self._path) + " " + str(e))

        # Obtener la rama actual
        try:
            data['branch'] = subprocess.check_output("git rev-parse --abbrev-ref HEAD", stderr=subprocess.STDOUT,
                                                     shell=True, cwd=self._path).decode()
        except Exception as e:

            _logger.error('Error al obtener la rama actual en la ruta: ' + str(self._path) + " " + str(e))

        return data

    def log(self):
        return self._output_list

    def update(self):
        msg = ''
        self._output_list.append(str(time.ctime()) + ": Checking for updates")
        if self.load():
            _logger.error('PULL al repositorio  ++++' + str(self._source_git))
            try:
                res = subprocess.check_output("git remote set-url origin " + self._source_git, stderr=subprocess.STDOUT,
                                              shell=True, cwd=self._path).decode()
                _logger.error('Response PULL al repositorio  ++++' + str(res))
            except Exception as e:
                _logger.error('Error al actualizar el repositorio  ++++' + str(e))

            try:
                res = subprocess.check_output("git reset --hard HEAD", stderr=subprocess.STDOUT, shell=True,
                                              cwd=self._path).decode()
                _logger.error('Response PULL al repositorio  ++++' + str(res))
            except Exception as e:
                _logger.error('Error al actualizar el repositorio  ++++' + str(e))

            result = subprocess.check_output("git pull", stderr=subprocess.STDOUT, shell=True, cwd=self._path).decode()
            msg = str(result) + " " + msg
            self._output_list.append(str(msg))
            if msg:
                if 'Already' in msg:
                    ret_flag = False
                else:
                    ret_flag = True
                _logger.info(str(msg))

            else:
                ret_flag = True

        else:
            ret_flag = False
            _logger.info('Remote repository \'origin\' doesn\'t exsist!')
            self._output_list.append('Remote repository \'origin\' doesn\'t exsist!')
        return ret_flag

    def checkout(self, branch):
        self._output_list.append(str(time.ctime()) + ": Checking out branch " + branch)
        if self.load():
            result = subprocess.check_output("git checkout " + branch, stderr=subprocess.STDOUT, shell=True,
                                             cwd=self._path).decode()
            msg = str(result)
            self._output_list.append(str(msg))
            if msg:
                if 'Already' in msg:
                    ret_flag = False
                else:
                    ret_flag = True
                _logger.info(str(msg))

            else:
                ret_flag = True

        else:
            ret_flag = False
            _logger.info('Remote repository \'origin\' doesn\'t exsist!')
            self._output_list.append('Remote repository \'origin\' doesn\'t exsist!')
        return ret_flag

    def branch(self):
        if self.load():
            result = subprocess.check_output("git branch", stderr=subprocess.STDOUT, shell=True,
                                             cwd=self._path).decode()
            msg = str(result)
            self._output_list.append(str(msg))
            if msg:
                if 'Already' in msg:
                    ret_flag = False
                else:
                    ret_flag = True
                _logger.info(str(msg))

            else:
                ret_flag = True

        else:
            ret_flag = False
            _logger.info('Remote repository \'origin\' doesn\'t exsist!')
            self._output_list.append('Remote repository \'origin\' doesn\'t exsist!')
        return ret_flag
