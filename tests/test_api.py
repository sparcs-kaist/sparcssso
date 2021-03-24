from django.test import TestCase
from tests.conftest import FixtureServiceSet, FixtureUserSet, RequestSettingMixin


class ApiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = FixtureUserSet()
        cls.services = FixtureServiceSet(cls.users.admin)

    def tearDown(self):
        super().tearDown()


class ExampleTest(RequestSettingMixin, ApiTestCase):
    def test_addition(self):
        assert 1+1 == 2

    def test_server(self):
        response = self.http_request(None, "get", "")
        assert response.status_code == 200
