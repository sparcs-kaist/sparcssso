from django.test import TestCase

from tests.conftest import RequestSettingMixin, FixtureUserSet, FixtureNoticeSet


class TestNoticeViewSet(RequestSettingMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = FixtureUserSet()
        cls.notices = FixtureNoticeSet()

    def test_notice_list(self):
        response = self.http_request(None, "get", "/web-api/notice/")
        assert response.data.get("last_name") ==

    def test_notice_latest(self):
        response = self.http_request(None, "get", "/web-api/notice/latest")

    """
    TODO
    - setUpClass에 공지사항 fixture 추가 v
    - 그냥 목록 가져오기 v
    - 시간 범위가 잘 반영되는지
    - 표출 시작시간 내림차순 정렬 여부 
    - (latest에 대해서도 마찬가지)
    """
