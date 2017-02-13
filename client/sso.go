package sso

import (
	"crypto/hmac"
	"crypto/md5"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"time"
)

type (
	SSOClient struct {
		ClientID  string
		SecretKey string
	}

	SSOLoginParams struct {
		URI   string
		State string
	}
)

const API_ROOT string = "https://sparcssso.kaist.ac.kr/api/v2/"

func randomHex(n int) (string, error) {
	bytes := make([]byte, n)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}

func NewSSOClient(clientID string, secretKey string) *SSOClient {
	return &SSOClient{
		ClientID:  clientID,
		SecretKey: secretKey,
	}
}

func (s SSOClient) postData(uri string, data url.Values) (interface{}, error) {
	data.Add("client_id", s.ClientID)
	resp, err := http.PostForm(uri, data)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	statusCode := resp.StatusCode
	if statusCode != 200 {
		return nil, errors.New(fmt.Sprint(statusCode))
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result interface{}
	err = json.Unmarshal(body, &result)
	return result, err
}

func (s SSOClient) computeMAC(message string) string {
	key := []byte(s.SecretKey)
	h := hmac.New(md5.New, key)
	h.Write([]byte(message))
	return hex.EncodeToString(h.Sum(nil))
}

func (s SSOClient) GetLoginParams() (*SSOLoginParams, error) {
	state, err := randomHex(10)
	if err != nil {
		return nil, err
	}

	params := url.Values{
		"client_id": {s.ClientID},
		"state":     {state},
	}
	return &SSOLoginParams{
		URI:   fmt.Sprintf("%stoken/require/?%s", API_ROOT, params.Encode()),
		State: state,
	}, nil
}

func (s SSOClient) GetUserInfo(code string) (map[string]interface{}, error) {
	timestamp := fmt.Sprint(time.Now().Unix())
	sign := s.computeMAC(fmt.Sprintf("%s%s", code, timestamp))
	uri := fmt.Sprintf("%stoken/info/", API_ROOT)
	data := url.Values{
		"code":      {code},
		"timestamp": {timestamp},
		"sign":      {sign},
	}

	result, err := s.postData(uri, data)
	if err != nil {
		return nil, err
	}
	return result.(map[string]interface{}), nil
}

func (s SSOClient) GetLogoutURI(sid string, redirectURI string) (string, error) {
	timestamp := fmt.Sprint(time.Now().Unix())
	sign := s.computeMAC(fmt.Sprintf("%s%s%s", sid, redirectURI, timestamp))
	params := url.Values{
		"client_id":    {s.ClientID},
		"sid":          {sid},
		"timestamp":    {timestamp},
		"redirect_uri": {redirectURI},
		"sign":         {sign},
	}
	return fmt.Sprintf("%slogout/?%s", API_ROOT, params.Encode()), nil
}

func (s SSOClient) DoUnregister(sid string) (bool, error) {
	timestamp := fmt.Sprint(time.Now().Unix())
	sign := s.computeMAC(fmt.Sprintf("%s%s", sid, timestamp))
	uri := fmt.Sprintf("%sunregister/", API_ROOT)
	data := url.Values{
		"sid":       {sid},
		"timestamp": {timestamp},
		"sign":      {sign},
	}

	result, err := s.postData(uri, data)
	if err != nil {
		return false, err
	}
	return result.(map[string]interface{})["success"].(bool), nil
}
