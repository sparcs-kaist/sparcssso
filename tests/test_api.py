import re
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from tests.conftest import FixtureServiceSet, FixtureUserSet, RequestSettingMixin

from apps.core.models import AccessToken


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

    def test_bad_method(self):
        response = self.http_request(None, "post", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        response = self.http_request(None, "put", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        response = self.http_request(None, "delete", "api/v2/token/require")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_query_validation(self):
        response = self.http_request(self.users.basic, "get", "api/v2/token/require")
        assert response.status_code == 400

        response = self.http_request(self.users.basic, "get", "api/v2/token/require", querystring="client_id=1029")
        assert response.status_code == 400

        response = self.http_request(self.users.basic, "get", "api/v2/token/require", querystring="state=1029")
        assert response.status_code == 400

    def test_successful_response(self):
        response = self.http_request(
            self.users.basic, "get", "api/v2/token/require", querystring="client_id=public&state=12341234",
        )
        assert response.status_code == 302
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
