from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler, HTTPServer
from secrets import token_hex
from sparcsssov2 import Client
from urllib.parse import parse_qs, urlparse
import requests
import json
import sys


# SPARCS SSO V2 Client Test Server Version 1.2
# VALID ONLY AFTER 2017-05-06
# Made by SPARCS SSO Team


storage = {
    'client': None,
    'session': requests.Session(),
    'loggedin': False,
}


class TestHandler(BaseHTTPRequestHandler):
    def _do_root(self):
        return {
            'test-suites': {
                'login': '/login',
                'logout': '/logout',
                'point-get': '/point-get',
                'point-modify': '/point-modify',
            },
            'target': {
                'user': 'email: test@sso.sparcs.org, pw: asdfasdf',
            },
        }

    def _do_login(self):
        global storage
        client, session = storage['client'], storage['session']

        if storage['loggedin']:
            return {'success': False, 'reason': 'Already Logged In'}

        r = session.get('%saccount/login/' % client.DOMAIN)
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.select("input[name=csrfmiddlewaretoken]")[0]['value']

        data = {
            'email': 'test@sso.sparcs.org',
            'password': 'asdfasdf',
            'csrfmiddlewaretoken': token
        }

        r = session.post('%saccount/login/' % client.DOMAIN, data=data)
        storage['loggedin'] = 'account/login' not in r.url
        if not storage['loggedin']:
            return {'success': False, 'reason': 'Invalid Account'}

        login_url, old_state = client.get_login_params()
        r = session.get(login_url, allow_redirects=False)
        url = r.headers['Location']
        dic = parse_qs(urlparse(url).query)
        state, code = dic['state'][0], dic['code'][0]
        if state != old_state:
            return {'success': False, 'reason': 'Invalid State'}

        r = client.get_user_info(code)
        storage['sid'] = r['sid']
        return {'user': r, 'success': True}

    def _do_logout(self):
        global storage
        client, session = storage['client'], storage['session']

        if not storage['loggedin']:
            return {'success': False, 'reason': 'Not Logged In'}

        redirect_uri = 'https://example.com/?args={}'.format(token_hex(10))
        logout_url = client.get_logout_url(storage['sid'], redirect_uri)
        r = session.get(logout_url, allow_redirects=False)
        url = r.headers['Location']

        if redirect_uri != url:
            return {'success': False, 'reason': 'Unknown'}

        storage['loggedin'] = False
        return {'success': True}

    def _do_unregister(self):
        global storage
        client = storage['client']

        length = int(self.headers['content-length'])
        data_dict = parse_qs(self.rfile.read(length).decode('utf8'))
        sid = client.parse_unregister_request(data_dict)
        return client.get_unregister_response(
            sid, True, 'test', 'https://naver.com'
        )

    def _do_get_point(self):
        global storage
        client = storage['client']

        if not storage['loggedin']:
            return {'success': False, 'reason': 'Not Logged In'}

        point = client.get_point(storage['sid'])
        return {'success': True, 'point': point}

    def _do_modify_point(self, path):
        global storage
        client = storage['client']

        if not storage['loggedin']:
            return {'success': False, 'reason': 'Not Logged In'}

        dic = parse_qs(urlparse(path).query)
        delta = dic.get('delta', ['1000', ])[0].strip()

        result = client.modify_point(storage['sid'], delta, 'SPARCS SSO Test')
        return {'success': True, 'result': result}

    def do_GET(self):
        path = self.path
        if path[-1] == '/':
            path = path[:-1]

        resp = {'success': False, 'reason': 'Invalid URL'}
        if path == '':
            resp = self._do_root()
        elif path == '/login':
            resp = self._do_login()
        elif path == '/logout':
            resp = self._do_logout()
        elif path == '/point-get':
            resp = self._do_get_point()
        elif path.startswith('/point-modify'):
            resp = self._do_modify_point(path)

        self.send_response(200)
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resp), 'utf-8'))

    def do_POST(self):
        path = self.path
        if path[-1] == '/':
            path = path[:-1]

        resp = {'success': False, 'reason': 'Invalid URL'}
        if path == '/unregister':
            resp = self._do_unregister()

        self.send_response(200)
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resp), 'utf-8'))


def main(args):
    if len(args) < 5:
        print('usage: test.v2.py port server_addr client_id secret_key')
        exit(1)

    port = int(args[1])
    server_addr = 'http://{}/'.format(args[2])
    client_id = args[3]
    secret_key = args[4]

    global storage
    storage['client'] = Client(client_id, secret_key, server_addr=server_addr)

    try:
        server = HTTPServer(('0.0.0.0', port), TestHandler)
        print('Start SPARCS SSO Test HTTP Server on 0.0.0.0:{}'.format(port))
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stop Test HTTP Server')
        server.socket.close()


if __name__ == '__main__':
    main(sys.argv)
