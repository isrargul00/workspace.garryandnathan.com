import json
import logging
import threading

from odoo import http, service
from odoo.http import request, Response, Controller

_log = logging.getLogger(__name__)


class ServerController(Controller):

    @http.route('/restart_server', auth='user')
    def restart_server(self):
        t = threading.Thread(target=service.server.restart)
        t.daemon = True
        t.start()
        return Response(response="Server is restarting", status=200)

    @http.route('/github_webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def handle_github_webhook(self, **post):
        data = json.loads(request.httprequest.data)
        try:
            repository = data['repository']['name']
            url = data['repository']['url']
            branch = data['ref'].split('/')[-1]
            ssh_url = data['repository']['ssh_url']
            _log.info('Github webhook received for repository %s, branch %s', repository, branch)

            repository_ids = request.env['repository.repository'].sudo().search(
                [('branch', '=', branch), ('source', 'in', [url, ssh_url])])
            _log.info('Found %s repositories', repository_ids)
            for repository in repository_ids:
                repository.sudo().update()
            self.restart_server()
        except Exception as e:
            _log.error('Error while handling webhook: %s', e)
        return Response(response="Webhook received", status=200)
