import hashlib
import hmac
import re
from datetime import timedelta, datetime
from typing import Optional, Union

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from tests.conftest import FixtureServiceSet, FixtureUserSet, RequestSettingMixin, ensure_user

from apps.core.models import AccessToken, Service, ServiceMap


class ApiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = FixtureUserSet()
        cls.services = FixtureServiceSet(cls.users.admin)

    def tearDown(self):
        super().tearDown()


class TestWebSudo(RequestSettingMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pw_user = ensure_user("foo", ("foo", "foo"), "foo@sparcs.org", password="123123")
        cls.no_pw_user = ensure_user("bar", ("bar", "bar"), "bar@sparcs.org")

    def test_put(self):
        response = self.http_request(None, "put", "web-api/sudo", {"password": "foo"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "foo"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "123123"})
        assert response.status_code == status.HTTP_200_OK

    def test_unauthorized_get(self):
        response = self.http_request(None, "get", "web-api/sudo")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_no_pw_get(self):
        response = self.http_request(self.no_pw_user, "get", "web-api/sudo")
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("valid") is True
        assert response.data.get("expires_at") is None

    def test_pw_get(self):
        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("valid") is False
        assert response.data.get("expires_at") is None

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "123123"})
        assert response.status_code == status.HTTP_200_OK

        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("valid") is True
        expiry_str = response.data.get("expires_at")
        expiry = datetime.strptime(expiry_str[:-3]+expiry_str[-2:], "%Y-%m-%dT%H:%M:%S%z")
        assert expiry > timezone.now()

    def test_fail_after_success(self):
        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "123123"})
        assert response.status_code == status.HTTP_200_OK

        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.data.get("valid") is True

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "asdf"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.data.get("valid") is False

    def test_400_after_success(self):
        response = self.http_request(self.pw_user, "put", "web-api/sudo", {"password": "123123"})
        assert response.status_code == status.HTTP_200_OK

        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.data.get("valid") is True

        response = self.http_request(self.pw_user, "put", "web-api/sudo", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = self.http_request(self.pw_user, "get", "web-api/sudo")
        assert response.data.get("valid") is False
