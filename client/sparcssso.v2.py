import requests
import hmac
import time
import os
import urllib


# SPARCS SSO V2 Client Version Alpha 1
# VALID FOR OLNY LOCAL DEVELOPMENT
# Made by SPARCS SSO Team


class Client:
    SERVER_DOMAIN = 'https://sparcssso.kaist.ac.kr/'
    BETA_DOMAIN = 'https://ssobeta.sparcs.org/'

    API_PREFIX = 'api/'
    VERSION_PREFIX = 'v1/'

    URLS = {
        'token_require': 'token/require/',
        'token_info': 'token/info/',
        'logout': 'logout/',
        'point': 'point/',
        'notice': 'notice/',
    }

    def __init__(self, client_id, secret_key, is_beta=False):
        DOMAIN = self.BETA_DOMAIN if is_beta else self.SERVER_DOMAIN
        BASE_URL = '%s%s%s' % (DOMAIN, self.API_PREFIX, self.VERSION_PREFIX)

        for k in self.URLS:
            self.URLS[k] = '%s%s' % (BASE_URL, self.URLS[k])

        self.client_id = client_id
        self.secret_key = secret_key

    def _post_data(self, url, data):
        r = requests.post(url, data, verify=True)
        if r.status_code == 400:
            raise RuntimeError('INVALID_REQUESTI')
        elif r.status_code == 403:
            raise RuntimeError('NO_PERMISSION')
        elif r.status_code != 200:
            raise RuntimeError('UNKNOWN_ERROR')

        try:
            return r.json()
        except:
            raise RuntimeError('NOT_JSON_OBJECT')

    def get_logout_url(self, sid, redirect_uri):
        timestamp = int(time.time())
        sign = hmac.new(str(self.secret_key),
                        str(''.join([sid, redirect_uri, timestamp]))).hexdigest()

        params = {
            'client_id': self.client_id,
            'sid': sid,
            'timestamp': timestamp,
            'redirect_uri': redirect_uri,
            'sign': sign,
        }
        return '%s?%s' % (self.LOGOUT_BASE_URL, urllib.urlencode(params))

    def get_login_params(self):
        state = os.urandom(10).encode('hex')
        params = {
            'client_id': self.client_id,
            'state': state,
        }

        return ['%s?%s' % (self.REQUIRE_BASE_URL, urllib.urlencode(params)), state]

    def get_user_info(self, session, code):
        timestamp = int(time.time())
        sign = hmac.new(str(self.secret_key),
                        str(''.join([code, timestamp]))).hexdigest()

        params = {
            'client_id': self.client_id,
            'code': code,
            'timestamp': timestamp,
            'sign': sign,
        }
        return self._post_data(self.INFO_BASE_URL, params)

    def get_point(self, sid):
        return self.modify_point(sid, 0, '')['point']

    def modify_point(self, sid, delta, message, lower_bound=-100000000):
        timestamp = int(time.time())
        sign = hmac.new(str(self.secret_key),
                        str(''.join([sid, delta, lower_bound, timestamp]))).hexdigest()
        params = {
            'client_id': self.client_id,
            'sid': sid,
            'delta': delta,
            'message': message,
            'lower_bound': lower_bound,
            'timestamp': timestamp,
            'sign': sign,
        }
        return self._post_data(self.POINT_BASE_URL, params)

    def get_notice(self, offset=0, limit=3, date_after=0):
        params = {
            'offset': offset,
            'limit': limit,
            'date_after': date_after,
        }
        r = requests.get(self.NOTICE_BASE_URL, data=params, verify=True)
        return r.json()
