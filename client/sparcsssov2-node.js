const crypto = require('crypto');
const axios = require('axios');

const SERVER_DOMAIN = 'https://sparcssso.kaist.ac.kr/';
const BETA_DOMAIN = 'https://ssobeta.sparcs.org/';

const API_PREFIX = 'api/';
const VERSION_PREFIX = 'v2/';

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

Dependencies: node ^10.15.2, axios ^0.18.0
*/

export default class Client {
  constructor(clientId, secretKey, isBeta = false, serverAddr = '') {
    /*
      Initialize SPARCS SSO Client
      :param clientId: your client id
      :param secretKey: your secret key
      :param isBeta: true iff you want to use SPARCS SSO beta server
      :param serverAddr: SPARCS SSO server addr (only for testing)
    */
    this.DOMAIN = (isBeta ? BETA_DOMAIN : SERVER_DOMAIN);
    this.DOMAIN = (serverAddr === '' ? this.DOMAIN : serverAddr);

    const baseUrl = [this.DOMAIN, API_PREFIX, VERSION_PREFIX].join('');
    this.URLS = {};
    for (const [key, url] of Object.entries(URLS)) {
      this.URLS[key] = [baseUrl, url].join('');
    }

    this.clientId = clientId;
    this.secretKey = Buffer.from(secretKey, 'utf8');
  }

  _signPayload(payload, appendTimestamp = true) {
    const d = new Date();
    const n = d.getTime();
    const timestamp = Math.floor(n / 1000);
    if (appendTimestamp) {
      payload.push(timestamp);
    }
    const msg = Buffer.from(payload.join(''), 'utf8');
    const sign = crypto.createHmac('md5', this.secretKey).update(msg).digest('hex');
    return { sign, timestamp };
  }

  static _validateSign(payload, timestamp, sign) {
    const { signClient, timeClient } = this._signPayload(payload, false);
    if (Math.abs(timeClient - Number(timestamp)) > 10) {
      return false;
    }
    if (crypto.timingSafeEqual(signClient, sign)) {
      return false;
    }
    return true;
  }

  static async _postData(url, data) {
    try {
      const res = await axios.post(url, data);
      return res.data;
    } catch (err) {
      if (err.response) {
        if (err.response.status === 400) {
          throw new Error('INVALID_REQUEST');
        } else if (err.response.status === 403) {
          throw new Error('NO_PERMISSION');
        } else if (err.response.status !== 200) {
          throw new Error('UNKNOWN_ERROR');
        }
      } else if (err.request) {
        throw new Error('NO_RESPONSE');
      } else {
        throw new Error('REQUEST_SETUP_ERROR');
      }
      return undefined;
    }
  }

  getLoginParams() {
    /*
      Get login parameters for SPARCS SSO login
      :returns: [url, state] where url is a url to redirect user,
          and state is random string to prevent CSRF
    */
    const state = crypto.randomBytes(10).toString('hex');
    const params = {
      clientId: this.clientId,
      state,
    };
    const url = [this.URLS.token_require, Object.entries(params).map(e => e.join('=')).join('&')].join('?');
    return { url, state };
  }

  getUserInfo(code) {
    /*
      Exchange a code t;o user information
      :param code: the code that given by SPARCS SSO server
      :returns: a dictionary that contains user information
    */
    const { sign, timestamp } = this._signPayload([code]);
    const params = {
      clientId: this.clientId,
      code,
      timestamp,
      sign,
    };
    return this._postData(this.URLS.token_info, params);
  }

  getLogoutUrl(sid, redirectUri) {
    /*
      Get a logout url to sign out a user
      :param sid: the user's service id
      :param redirectUri: a redirect uri after the user sign out
      :returns: the final url to sign out a user
    */
    const { sign, timestamp } = this._signPayload([sid, redirectUri]);
    const params = {
      clientId: this.clientId,
      sid,
      timestamp,
      redirectUri,
      sign,
    };
    return [this.URLS.logout, Object.entries(params).map(e => e.join('=')).join('&')].join('?');
  }

  getPoint(sid) {
    /*
      Get a user's point
      :param sid: the user's service id
      :returns: the user's point
    */
    return this.modifyPoint(sid, 0, '').point;
  }

  modifyPoint(sid, delta, message, lowerBound = 0) {
    /*
      Modify a user's point
      :param sid: the user's service id
      :param delta: an increment / decrement point value
      :param message: a message that displayed to the user
      :param lowerBound: a minimum point value that required
      :returns: a server response; check the full docs
    */
    const { sign, timestamp } = this._signPayload([sid, delta, message, lowerBound]);
    const params = {
      clientId: this.clientId,
      sid,
      delta,
      message,
      lowerBound,
      timestamp,
      sign,
    };
    return this._postData(this.URLS.point, params);
  }

  static async getNotice(offset = 0, limit = 3, date_after = 0) {
    /*
      Get some notices from SPARCS SSO
      :param offset: a offset to fetch from
      :param limit: a number of notices to fetch
      :param date_after: an oldest date; YYYYMMDD formated string
      :returns: a server response; check the full docs
    */
    const params = {
      offset,
      limit,
      date_after,
    };
    try {
      const res = await axios.get(this.URLS.notice, { params });
      return res.data;
    } catch (err) {
      throw new Error(err.message);
    }
  }

  parseUnregisterRequest({
    clientId, sid, timestamp, sign,
  }) {
    /*
      Parse unregister request from SPARCS SSO server
      :param data_dict: a data dictionary that the server sent
      :returns: the user's service id
      :raises RuntimeError: raise iff the request is invalid
    */
    if (clientId !== this.clientId) {
      throw new Error('INVALID_REQUEST');
    } else if (!this._validateSign([sid], timestamp, sign)) {
      throw new Error('INVALID_REQUEST');
    }
    return sid;
  }
}
