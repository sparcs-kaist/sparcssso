import crypto from "crypto";
import querystring from "querystring";

import axios, {AxiosError} from "axios";

/*
SPARCS SSO V2 Client for NodeJS Version 1.0 (verified)
Made by SPARCS SSO Team - appleseed, jungnoh

Dependencies: node ^10, axios ^0.18
*/

interface UserInformation {
  uid: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  birthday?: string;  // Formatted as YYYY-MM-DD
  point: number;
  flags: string[];
  facebook_id: string;
  twitter_id: string;
  kaist_id: string;
  kaist_info: Record<string, string | number>;
  sparcs_id: string;
}


export default class Client {
  private clientId: string;
  private secretKey: Buffer;
  private readonly URLS: Record<string, string> = {};
  private readonly DOMAIN: string;

  constructor(clientId: string, secretKey: string, isBeta = false, serverAddr = "") {
    /*
      Initialize SPARCS SSO Client
      :param clientId: your client id
      :param secretKey: your secret key
      :param isBeta: true iff you want to use SPARCS SSO beta server
      :param serverAddr: SPARCS SSO server addr (only for testing)
    */
    const SERVER_DOMAIN = "https://sparcssso.kaist.ac.kr/";
    const BETA_DOMAIN = "https://ssobeta.sparcs.org/";

    const API_PREFIX = "api/";
    const VERSION_PREFIX = "v2/";

    const URLS = {
      token_require: "token/require/",
      token_info: "token/info/",
      logout: "logout/",
      unregister: "unregister/",
      point: "point/",
      notice: "notice/",
    };
    this.DOMAIN = (serverAddr === "" ? (isBeta ? BETA_DOMAIN : SERVER_DOMAIN) : serverAddr);

    const baseUrl = [this.DOMAIN, API_PREFIX, VERSION_PREFIX].join("");
    for (const [key, url] of Object.entries(URLS)) {
      this.URLS[key] = [baseUrl, url].join("");
    }

    this.clientId = clientId;
    this.secretKey = Buffer.from(secretKey, "utf8");
  }

  private _signPayload(payload: (string | number)[], appendTimestamp = true) {
    const timestamp = Math.floor(new Date().getTime() / 1000);
    if (appendTimestamp) {
      payload.push(timestamp);
    }
    const msg = Buffer.from(payload.join(""), "utf-8");
    const sign = crypto.createHmac("md5", this.secretKey).update(msg).digest("hex");
    return { sign, timestamp };
  }

  private _validateSign(payload: (string | number)[], timestamp: number, sign: Buffer) {
    const clientSign = this._signPayload(payload, false);
    if (Math.abs(clientSign.timestamp - timestamp) > 10) {
      return false;
    }
    if (crypto.timingSafeEqual(Buffer.from(clientSign.sign, "utf-8"), sign)) {
      return false;
    }
    return true;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  static async _postData<ResponseType = any>(url: string, data: any): Promise<ResponseType> {
    try {
      const res = await axios.post(url, querystring.stringify(data));
      return res.data as ResponseType;
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response) {
          if (err.response.status === 400) {
            throw new Error("INVALID_REQUEST");
          } else if (err.response.status === 403) {
            throw new Error("NO_PERMISSION");
          } else if (err.response.status !== 200) {
            throw new Error("UNKNOWN_ERROR");
          }
        } else if (err.request) {
          throw new Error("NO_RESPONSE");
        } else {
          throw new Error("REQUEST_SETUP_ERROR");
        }
      }
      throw new Error("UNKNOWN_ERROR");
    }
  }

  getLoginParams() {
    /*
      Get login parameters for SPARCS SSO login
      :returns: [url, state] where url is a url to redirect user,
          and state is random string to prevent CSRF
    */
    const state = crypto.randomBytes(10).toString("hex");
    const { clientId, URLS: urls } = this;
    const params = {
      client_id: clientId,
      state,
    };
    const url = [urls.token_require, Object.entries(params).map(e => e.join("=")).join("&")].join("?");
    return { url, state };
  }

  async getUserInfo(code: string | number): Promise<UserInformation> {
    /*
      Exchange a code to user information
      :param code: the code that given by SPARCS SSO server
      :returns: a dictionary that contains user information
    */
    const { sign, timestamp } = this._signPayload([code]);
    const params = {
      client_id: this.clientId,
      code,
      timestamp,
      sign,
    };
    try {
      return await Client._postData<UserInformation>(this.URLS.token_info, params);
    } catch (err) {
      throw err;
    }
  }

  getLogoutUrl(sid: string, redirectUri: string) {
    /*
      Get a logout url to sign out a user
      :param sid: the user's service id
      :param redirectUri: a redirect uri after the user sign out
      :returns: the final url to sign out a user
    */
    const { sign, timestamp } = this._signPayload([sid, redirectUri]);
    const params = {
      client_id: this.clientId,
      sid,
      timestamp,
      redirect_uri: redirectUri,
      sign,
    };
    return [this.URLS.logout, Object.entries(params).map(e => e.join("=")).join("&")].join("?");
  }

  async getPoint(sid: string): Promise<number> {
    /*
      Get a user's point
      :param sid: the user's service id
      :returns: the user's point
    */
    const response = await this.modifyPoint(sid, 0, "");
    return response.point as number;
  }

  async modifyPoint(sid: string, delta: number, message: string, lowerBound: number = 0) {
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
      client_id: this.clientId,
      sid,
      delta,
      message,
      lower_bound: lowerBound,
      timestamp,
      sign,
    };
    try {
      return await Client._postData(this.URLS.point, params);
    } catch (err) {
      return err;
    }
  }

  async getNotice(offset = 0, limit = 3, dateAfter = 0) {
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
      date_after: dateAfter,
    };
    try {
      const res = await axios.get(this.URLS.notice, { params });
      return res.data;
    } catch (err) {
      throw err;
    }
  }

  parseUnregisterRequest({
    clientId, sid, timestamp, sign,
  }: {clientId: string, sid: string, timestamp: number, sign: Buffer}) {
    /*
      Parse unregister request from SPARCS SSO server
      :param data_dict: a data dictionary that the server sent
      :returns: the user's service id
      :raises RuntimeError: raise iff the request is invalid
    */
    if (clientId !== this.clientId) {
      throw new Error("INVALID_REQUEST");
    } else if (!this._validateSign([sid], timestamp, sign)) {
      throw new Error("INVALID_REQUEST");
    }
    return sid;
  }
}
