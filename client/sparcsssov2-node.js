const crypto = require('crypto');
const axios = require('axios');

const SERVER_DOMAIN = 'https://sparcssso.kaist.ac.kr/';
const BETA_DOMAIN = 'https://ssobeta.sparcs.org/';
const DOMAIN = undefined

const API_PREFIX = 'api/';
const VERSION_PREFIX = 'v2/';
const TIMEOUT = 60;

const URLS = {
  token_require: 'token/require/',
  token_info: 'token/info/',
  logout: 'logout/',
  unregister: 'unregister/',
  point: 'point/',
  notice: 'notice/',
};

/*
SPARCS SSO V2 Client for NodeJS Version 0.1 (Unstable)
Made by SPARCS SSO Team - appleseed

Dependencies: axios ^0.18.0
*/

class Client {
  constructor(client_id, secret_key, is_beta = false, server_addr = '') {
    /*
      Initialize SPARCS SSO Client
      :param client_id: your client id
      :param secret_key: your secret key
      :param is_beta: true iff you want to use SPARCS SSO beta server
      :param server_addr: SPARCS SSO server addr (only for testing)
    */
    this.DOMAIN = (is_beta ? BETA_DOMAIN : SERVER_DOMAIN);
    this.DOMAIN = (server_addr === '' ? this.DOMAIN : server_addr);

    const base_url = [this.DOMAIN, API_PREFIX, VERSION_PREFIX].join('');
    this.URLS = {};
    for (var key in URLS) {
      this.URLS[key] = [base_url, URLS[key]].join('');
    }

    this.client_id = client_id;
    this.secret_key = Buffer.from(secret_key, 'utf8');
  }

  _sign_payload(payload, append_timestamp = true) {
    const d = new Date();
    const n = d.getTime();
    const timestamp = Math.floor(n/1000);
    if (append_timestamp) {
      payload.push(timestamp);
    }
    const msg = Buffer.from(payload.join(''), 'utf8');
    const sign = crypto.createHmac('md5', this.secret_key).update(msg).digest('hex');
    return [sign, timestamp];
  };

  _validate_sign(payload, timestamp, sign) {
    const result = _sign_payload(payload, false);
    if (Math.abs(result[1] - Number(timestamp)) > 10) {
      return false;
    }
    else if (crypto.timingSafeEqual(result[0], sign)) {
      return false;
    }
    return true;
  }

  _post_data(url, data) {
    axios.post(url, data)
    .then((res) => {
      return res.data;
    })
    .catch((err) => {
      if (err.response) {
        if (err.response.status === 400) {
          throw 'INVALID_REQUEST';
        }
        else if (err.response.status === 403) {
          throw 'NO_PERMISSION';
        }
        else if (err.response.status !== 200) {
          throw 'UNKNOWN_ERROR';
        }
      }
      else if (err.request) {
        throw 'NO_RESPONSE';
      }
      else {
        throw 'REQUEST_SETUP_ERROR';
      }
    });
  }

  _generate_random_hex(len) {
    const candidates = '0123456789abcdef';
    var text = '';
    for (var i = 0; i < len; i++) {
      text += candidates.charAt(Math.floor(Math.random() * candidates.length));
    }
    return text;
  }

  get_login_params() {
    /*
      Get login parameters for SPARCS SSO login
      :returns: [url, state] where url is a url to redirect user,
          and state is random string to prevent CSRF
    */
    const state = this._generate_random_hex(20);
    const params = {
      client_id: this.client_id,
      state: state,
    }
    const url = [this.URLS.token_require, Object.entries(params).map(e => e.join('=')).join('&')].join('?');
    console.log([url, state]);
    return [url, state]
  }

  get_user_info(code) {
    /*
      Exchange a code to user information
      :param code: the code that given by SPARCS SSO server
      :returns: a dictionary that contains user information
    */
    const result = this._sign_payload([code]);
    const params = {
      client_id: this.client_id,
      code: code,
      timestamp: result[1],
      sign: result[0],
    }
    return this._post_data(this.URLS.token_info, params);
  }

  get_logout_url(sid, redirect_uri) {
    /*
      Get a logout url to sign out a user
      :param sid: the user's service id
      :param redirect_uri: a redirect uri after the user sign out
      :returns: the final url to sign out a user
    */
    const result = this._sign_payload([sid, redirect_uri]);
    const params = {
      client_id: this.client_id,
      sid: sid,
      timestamp: result[1],
      redirect_uri: redirect_uri,
      sign: result[0],
    }
    return [this.URLS.logout, Object.entries(params).map(e => e.join('=')).join('&')].join('?');
  }

  get_point(sid) {
    /*
      Get a user's point
      :param sid: the user's service id
      :returns: the user's point
    */
    return this.modify_point(sid, 0, '').point;
  }

  modify_point(sid, delta, message, lower_bound = 0) {
    /*
      Modify a user's point
      :param sid: the user's service id
      :param delta: an increment / decrement point value
      :param message: a message that displayed to the user
      :param lower_bound: a minimum point value that required
      :returns: a server response; check the full docs
    */
    const result = this._sign_payload([sid, delta, message, lower_bound]);
    const params = {
      client_id: this.client_id,
      sid: sid,
      delta: delta,
      message: message,
      lower_bound: lower_bound,
      timestamp: result[1],
      sign: result[0],
    };
    return this._post_data(this.URLS.point, params);
  }

  get_notice(offset = 0, limit = 3, date_after = 0) {
    /*
      Get some notices from SPARCS SSO
      :param offset: a offset to fetch from
      :param limit: a number of notices to fetch
      :param date_after: an oldest date; YYYYMMDD formated string
      :returns: a server response; check the full docs
    */
    params = {
      offset: offset,
      limit: limit,
      date_after: date_after,
    }
    axios.get(self.URLS.notice, { params: params })
    .then((res) => {
      return res.data;
    })
    .catch((err) => {
      throw err;
    });
  }

  parse_unregister_request(data_dict) {
    /*
      Parse unregister request from SPARCS SSO server
      :param data_dict: a data dictionary that the server sent
      :returns: the user's service id
      :raises RuntimeError: raise iff the request is invalid
    */
    const client_id = data_dict.client_id;
    const sid = data_dict.sid;
    const timestamp = data_dict.timestamp;
    const sign = data_dict.sign;
    if (client_id !== this.client_id) {
      throw 'INVALID_REQUEST';
    }
    else if (!this._validate_sign([sid], timestamp, sign)) {
      throw 'INVALID_REQUEST';
    }
    return sid
  }
}
