from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from secrets import token_hex
from sparcsssov2 import Client
from urllib.parse import parse_qs, urlparse
import click
import requests


# SPARCS SSO V2 Client Test Server Version 1.2
# VALID ONLY AFTER 2017-05-06
# Made by SPARCS SSO Team


app = Flask(__name__)
storage = {
    'account': {
        'email': '',
        'password': '',
        'sid': 'unknown',
    },
    'client': None,
    'loggedin': False,
    'session': requests.Session(),
}


@app.route('/')
def home():
    return jsonify({
        'account': storage['account'],
        'loggedin': storage['loggedin'],
        'unregister': {
            'accept': '/unregister/accept',
            'deny': '/unregister/deny',
        },
        'urls': {
            'login': '/login',
            'logout': '/logout',
            'point-get': '/point/get',
            'point-modify': '/point/modify?delta=1000',
        },
    })


@app.route('/login')
def login():
    client, session = storage['client'], storage['session']
    if storage['loggedin']:
        return jsonify({
            'success': False,
            'reason': 'already-logged-in',
        })

    r = session.get(f'{client.DOMAIN}account/login/')
    soup = BeautifulSoup(r.text, 'html.parser')
    token = soup.select('input[name=csrfmiddlewaretoken]')[0]['value']

    r = session.post(f'{client.DOMAIN}account/login/', data={
        'email': storage['account']['email'],
        'password': storage['account']['password'],
        'csrfmiddlewaretoken': token
    })
    if 'account/login' in r.url:
        return jsonify({
            'success': False,
            'reason': 'no-such-account',
        })

    login_url, old_state = client.get_login_params()
    r = session.get(login_url, allow_redirects=False)
    if 'Location' not in r.headers:
        return jsonify({
            'success': False,
            'reason': 'no-redirect-maybe-cooltime',
        })

    url = r.headers['Location']
    query_dict = parse_qs(urlparse(url).query)
    state, code = query_dict['state'][0], query_dict['code'][0]
    if state != old_state:
        return jsonify({
            'success': False,
            'reason': 'invalid-state',
        })

    r = client.get_user_info(code)
    storage['account']['sid'] = r['sid']
    storage['loggedin'] = True
    return jsonify({
        'success': True,
        'user': r,
    })


@app.route('/logout')
def logout():
    client, session = storage['client'], storage['session']
    if not storage['loggedin']:
        return jsonify({
            'success': False,
            'reason': 'not-logged-in',
        })

    redirect_uri = f'https://example.com/?args={token_hex(10)}'
    logout_url = client.get_logout_url(storage['account']['sid'], redirect_uri)
    r = session.get(logout_url, allow_redirects=False)
    url = r.headers['Location']
    if redirect_uri != url:
        return jsonify({
            'success': False,
            'reason': 'unknown',
        })

    storage['account']['sid'] = 'unknown'
    storage['loggedin'] = False
    return jsonify({
        'success': True,
    })


@app.route('/point/get')
def point_get():
    client = storage['client']
    if not storage['loggedin']:
        return jsonify({
            'success': False,
            'reason': 'not-logged-in',
        })

    point = client.get_point(storage['account']['sid'])
    return jsonify({
        'success': True,
        'point': point,
    })


@app.route('/point/modify')
def point_modify():
    client = storage['client']
    if not storage['loggedin']:
        return jsonify({
            'success': False,
            'reason': 'not-logged-in',
        })

    delta = request.args.get('delta', 1000)
    result = client.modify_point(
        storage['account']['sid'],
        delta, 'SPARCS SSO Test',
    )
    return jsonify({
        'success': True,
        'result': result,
    })


@app.route('/unregister/accept', methods=['POST', ])
def unregister_accept():
    return jsonify({
        'success': True,
    })


@app.route('/unregister/deny', methods=['POST', ])
def unregister_deny():
    return jsonify({
        'success': False,
        'reason': 'Unregister denied.',
        'link': 'https://example.com/help',
    })


@click.command()
@click.argument('server_addr')
@click.argument('client_id')
@click.argument('secret_key')
@click.argument('user_token')
@click.option('-p', '--port', type=int, default=22224,
              help='port number to open server')
def main(server_addr, client_id, secret_key, user_token, port):
    print('SPARCS SSO Test Server has been Started on 0.0.0.0:{}'.format(port))
    storage['account']['email'] = 'test-{}@sso.sparcs.org'.format(user_token)
    storage['account']['password'] = user_token
    storage['client'] = Client(client_id, secret_key, server_addr=server_addr)
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
