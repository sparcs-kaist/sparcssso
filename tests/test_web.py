from django.test import TestCase

from tests.conftest import RequestSettingMixin, FixtureUserSet


class TestNoticeViewSet(RequestSettingMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = FixtureUserSet()

    def test_notice_list(self):
        pass

    """
    TODO
    - setUpClass에 공지사항 fixture 추가
    - 그냥 목록 가져오기
    - 시간 범위가 잘 반영되는지
    - 표출 시작시간 내림차순 정렬 여부 
    - (latest에 대해서도 마찬가지)
    """