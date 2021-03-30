import hashlib
import hmac
import re
from datetime import timedelta
from typing import Optional, Union

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from tests.conftest import FixtureServiceSet, FixtureUserSet, RequestSettingMixin

from apps.core.models import AccessToken, Service, ServiceMap


class ApiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = FixtureUserSet()
        cls.services = FixtureServiceSet(cls.users.admin)

    def tearDown(self):
        super().tearDown()


class TestTokenRequire(RequestSettingMixin, ApiTestCase):
    def test_unauthorized_access(self):
        response = self.http_request(None, "get", "api/v2/token/require")
        assert response.status_code == status.HTTP_302_FOUND

    def test_invalid_state(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=1234",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # print(str(response.content, "utf-8"))

    def test_bad_method(self):
        response = self.http_request(None, "post", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        response = self.http_request(None, "put", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        response = self.http_request(None, "delete", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_query_validation(self):
        response = self.http_request(self.users.basic, "get", "api/v2/token/require")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = self.http_request(self.users.basic, "get", "api/v2/token/require", querystring="client_id=1029")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = self.http_request(self.users.basic, "get", "api/v2/token/require", querystring="state=1029")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_successful_response(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        assert response.status_code == status.HTTP_302_FOUND
        redirect_url = response.url
        assert redirect_url.startswith(self.services.public.login_callback_url)

        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(redirect_url)
        assert len(url_matches) == 1
        response_code, response_state = url_matches[0]
        assert response_state == "12341234"

        token = AccessToken.objects.get(tokenid=response_code)
        assert token.user == self.users.basic
        assert token.service == self.services.public
        assert token.expire_time < timezone.now() + timedelta(minutes=1)

    def test_flags(self):
        response = self.http_request(
            self.users.admin, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        assert response.status_code == 403
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=sparcs&state=12341234",
        )
        assert response.status_code == 403
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=test&state=12341234",
        )
        assert response.status_code == 403
        response = self.http_request(
            self.users.test_only, "get", "api/v2/token/require", querystring="client_id=sparcs&state=12341234",
        )
        assert response.status_code == 403
        response = self.http_request(
            self.users.email_unauthed, "get", "api/v2/token/require", querystring="client_id=sparcs&state=12341234",
        )
        assert response.status_code == 403


class TestTokenView(RequestSettingMixin, ApiTestCase):
    def _send_request(self, service: Service, code: str, timestamp: Union[int, str], mac: Optional[str] = None):
        if not mac:
            mac = hmac.new(service.secret_key.encode(), (code + str(timestamp)).encode(),
                           digestmod=hashlib.md5).hexdigest()
        return self.http_request(None, "post", "api/v2/token/info", data={
            "client_id": service.name,
            "code": code,
            "timestamp": str(timestamp),
            "sign": mac,
        })

    def test_successful_flow(self):
        for user in [self.users.basic, self.users.sparcs, self.users.kaist]:
            response = self.http_request(
                user, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
            )
            assert response.status_code == status.HTTP_302_FOUND
            redirect_url = response.url
            url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(redirect_url)
            response_code = url_matches[0][0]
            response = self._send_request(self.services.public, response_code, int(timezone.now().timestamp()))

            assert response.status_code == 200
            assert response.data.get("uid") == user.username
            service_map = ServiceMap.objects.get(user=user, service=self.services.public)
            assert response.data.get("sid") == service_map.sid
            assert response.data.get("email") == user.email
            assert response.data.get("first_name") == user.first_name
            assert response.data.get("last_name") == user.last_name
            assert response.data.get("gender") == user.profile.gender
            if user.profile.birthday is not None:
                assert response.data.get("birthday") == user.profile.birthday.strftime("%Y-%m-%d")
            assert response.data.get("kaist_id") == user.profile.kaist_id
            if response.data.get("kaist_id") is not None:
                assert response.data.get("kaist_info_time") == user.profile.kaist_info_time.strftime("%Y-%m-%d")
            assert response.data.get("sparcs_id") == user.profile.sparcs_id

    def test_token_service_mismatch(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=asdf1234",
        )
        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(response.url)
        response = self._send_request(self.services.sparcs, url_matches[0][0], int(timezone.now().timestamp()))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "TOKEN_SERVICE_MISMATCH"

    def test_invalid_service(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=asdf1234",
        )
        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(response.url)
        timestamp = int(timezone.now().timestamp())
        mac = hmac.new(self.services.public.secret_key.encode(), (url_matches[0][0] + str(timestamp)).encode(),
                       digestmod=hashlib.md5).hexdigest()
        response = self.http_request(None, "post", "api/v2/token/info", data={
            "client_id": "foo",
            "code": url_matches[0][0],
            "timestamp": str(timestamp),
            "sign": mac,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "INVALID_SERVICE"

    def test_invalid_sign(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(response.url)
        timestamp = int(timezone.now().timestamp())
        mac = hmac.new((self.services.public.secret_key + "1").encode(), (url_matches[0][0] + str(timestamp)).encode(),
                       digestmod=hashlib.md5).hexdigest()
        response = self.http_request(None, "post", "api/v2/token/info", data={
            "client_id": self.services.public.name,
            "code": url_matches[0][0],
            "timestamp": str(timestamp),
            "sign": mac,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "INVALID_SIGN"

    def test_token_expired(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        assert response.status_code == status.HTTP_302_FOUND
        redirect_url = response.url
        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(redirect_url)
        response_code = url_matches[0][0]

        token = AccessToken.objects.get(tokenid=response_code)
        token.expire_time -= timedelta(minutes=1)
        token.save()

        response = self._send_request(self.services.public, response_code, int(timezone.now().timestamp()))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "TOKEN_EXPIRED"

    def test_bad_timestamp(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        assert response.status_code == status.HTTP_302_FOUND
        redirect_url = response.url
        url_matches = re.compile(r"\?code=([0-9a-f]+)&state=(.*)").findall(redirect_url)
        response_code = url_matches[0][0]
        response = self._send_request(self.services.public, response_code, "foo")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "INVALID_TIMESTAMP"
