from odoo import api, fields, models, tools, service
from .module import PARAM_MY_MODULES_PATH
from io import StringIO
import zipfile
import os

import shutil

nlist_path = []
list_of_addons_paths = tools.config['addons_path'].split(",")
for path in list_of_addons_paths:
    nlist_path.append((path, path))

import logging

_logger = logging.getLogger(__name__)


class upload_module(models.Model):
    _name = 'upload.module'

    name = fields.Char(string='Name')
    panel_id = fields.Many2one(
        comodel_name='panel.tool',
        string='Panel_id',
        required=False)
    # addons_paths = fields.Selection(nlist_path,
    #                                 string="Add-ons Paths", help="Please choose one of these directories to put "
    #                                                              "your module in",
    #                                 required=True)
    data_file = fields.Binary('Detail')
    datas_fname = fields.Char('File Name')
    dir = fields.Char('Dir Name')

    @api.model
    def _check_parent_directory_in_addons_path(self):
        addons_path = tools.config['addons_path'].split(',')
        path = self.get_addons_path()
        try:
            shutil.rmtree(path)
        except FileNotFoundError as e:
            os.makedirs(path)
        if path not in addons_path:
            addons_path.append(path)
        tools.config['addons_path'] = ','.join(addons_path)
        tools.config.save()

    @api.model
    def create(self, values):
        # try:
        # directory_to_extract_to = values['addons_paths']
        self._check_parent_directory_in_addons_path()
        directory_to_extract_to = self.get_addons_path()
        values['name'] = '_'.join(values['datas_fname'].split('.')[:-1])
        # file_content = base64.b64decode(values['data_file'])
        file_path = os.path.join(directory_to_extract_to, '_'.join(values['datas_fname'].split('.')[:-1]))
        # try:
        #     shutil.rmtree(file_path)
        # except FileNotFoundError as e:
        #     os.makedirs(file_path)
        # with open(file_path, "wb") as f:
        #     f.write(file_content)
        zip_ref = zipfile.ZipFile(StringIO(values['data_file']), 'r')
        zip_ref.extractall(directory_to_extract_to)
        dirs = list(set([os.path.dirname(x) for x in zip_ref.namelist()]))
        values['dir'] = dirs[0].split('/')[0]
        zip_ref.close()
        self.deleteFile(file_path)
        service.server.restart()
        # except Exception as e:
        # print(e)
        return super(upload_module, self).create(values)

    @api.model
    def get_addons_path(self):
        return self.env["ir.config_parameter"].get_param(PARAM_MY_MODULES_PATH, '/mnt/extra-addons/my-uploaded-modules')

    def unlink(self):
        try:
            if self.dir:
                shutil.rmtree(os.path.join(self.get_addons_path(), self.dir))
        except:
            print('Error while deleting directory')
        return super(upload_module, self).unlink()

    def deleteDir(self, dirPath):
        deleteFiles = []
        deleteDirs = []
        for root, dirs, files in os.walk(dirPath):
            for f in files:
                deleteFiles.append(os.path.join(root, f))
            for d in dirs:
                deleteDirs.append(os.path.join(root, d))
        for f in deleteFiles:
            os.remove(f)
        for d in deleteDirs:
            os.rmdir(d)
        os.rmdir(dirPath)

    def deleteFile(self, file_path):
        ## If file exists, delete it ##
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:  ## Show an error ##
            print("Error: %s file not found" % file_path)
