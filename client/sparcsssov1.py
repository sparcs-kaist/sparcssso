import requests
import hmac
import time

# SPARCS SSO Client Version 1.0.0
# VALID ONLY AFTER 2016-05-18T23:59+09:00
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

    def __init__(self, is_test=False, is_beta=False, app_name='', secret_key=''):
        if not is_test and (not app_name or not secret_key):
            raise AssertionError('Need "app_name" and "secret_key"')

        DOMAIN = self.BETA_DOMAIN if is_beta else self.SERVER_DOMAIN
        BASE_URL = '%s%s%s' % (DOMAIN, self.API_PREFIX, self.VERSION_PREFIX)

        for k in self.URLS:
            self.URLS[k] = '%s%s' % (BASE_URL, self.URLS[k])

        self.is_test = is_test
        self.app_name = app_name
        self.secret_key = secret_key

    def _post_data(self, url, data):
        r = requests.post(url, data, verify=True)
        if r.status_code == 403:
            raise ValueError('Invalid secret key')
        elif r.status_code == 404:
            raise ValueError('Invalid / timeout token')
        elif r.status_code != 200:
            raise RuntimeError('Unknown server error')

        try:
            return r.json()
        except:
            raise RuntimeError('Json decode error')

    def get_logout_url(self, sid):
        if self.is_test:
            raise AssertionError('Not supported on test mode')

        timestamp = int(time.time())
        m = hmac.new(str(self.secret_key),
                     str('%s:%s' % (timestamp, sid))).hexdigest()
        return '%s?app=%s&time=%s&m=%s' % (self.LOGOUT_BASE_URL, self.app_name,
                                           timestamp, m)

    def get_login_url(self, callback_url=''):
        if self.is_test and not callback_url:
            raise AssertionError('Need "callback_url"')

        if self.is_test:
            return '%s?url=%s' % (self.REQUIRE_BASE_URL, callback_url)
        return '%s?app=%s' % (self.REQUIRE_BASE_URL, self.app_name)

    def get_user_info(self, tokenid):
        result = self._post_data(self.INFO_BASE_URL,
                                 {
                                     'tokenid': tokenid,
                                     'key': self.secret_key
                                 })
        return result

    def get_point(self, sid):
        if self.is_test:
            raise NotImplementedError('Not supported on test mode')

        result = self._post_data(self.POINT_BASE_URL,
                                 {
                                     'app': self.app_name,
                                     'key': self.secret_key,
                                     'sid': sid
                                 })
        return result['point']

    def modify_point(self, sid, delta, action, lower_bound=-100000000):
        if self.is_test:
            raise NotImplementedError('Not supported on test mode')

        result = self._post_data(self.POINT_BASE_URL,
                                 {
                                     'app': self.app_name,
                                     'key': self.secret_key,
                                     'sid': sid,
                                     'delta': delta,
                                     'action': action,
                                     'lower_bound': lower_bound
                                 })
        return result['changed'], result['point']

    def get_notice(self):
        r = requests.get(self.NOTICE_BASE_URL, verify=True)
        return r.json()
