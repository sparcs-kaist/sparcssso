import datetime
from typing import Tuple

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.test import APIClient

from apps.core.models import SERVICE_TEST, Service, UserProfile

KAIST_USER_INFO = '{"kaist_uid": "00111222", "mail": "jungnoh@kaist.ac.kr", "ku_sex": "M", "ku_acad_prog_code": "0",' \
                  '"ku_kaist_org_id": "1000", "ku_kname": "홍길", "ku_person_type": "Student",' \
                  '"ku_person_type_kor": "학생", "ku_psft_user_status_kor": "학", "ku_born_date": "2000-08-01",' \
                  '"ku_std_no": "20201234", "ku_psft_user_status": "Enrollment", "employeeType": "S",' \
                  '"givenname": "HONG", "displayname": "HONG, GILDONG", "sn": "GILDONG"}'


class RequestSettingMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = APIClient()

    def http_request(self, user, method, path, data=None, querystring='', **kwargs):
        self.api_client.force_authenticate(user=user)
        request_func = {
            'post': self.api_client.post,
            'patch': self.api_client.patch,
            'put': self.api_client.put,
            'get': self.api_client.get,
            'delete': self.api_client.delete,
        }
        url = f'/{path}/?{querystring}'
        return request_func[method](url, data=data, format='json', **kwargs)


def ensure_user(username: str, name: Tuple[str, str], email: str, is_staff=False, password=None, **kwargs) -> User:
    user_defaults = {
        "username": username,
        "first_name": name[0],
        "last_name": name[1],
        "email": email,
        "is_staff": is_staff,
    }
    user, _ = User.objects.filter(Q(username=username) | Q(email=email)).update_or_create(defaults=user_defaults)
    if password is None:
        user.set_unusable_password()
    else:
        user.set_password(password)
    user.save()
    UserProfile.objects.update_or_create(defaults={
        "gender": "*H",
        "email_authed": True,
        **kwargs,
    }, user=user)
    return user


def ensure_service(name: str, alias: str, admin_user: User, **kwargs) -> Service:
    Service.objects.filter(name=name).delete()
    return Service.objects.create(
        name=name,
        alias=alias,
        admin_user=admin_user,
        **{
            "is_shown": True,
            "scope": SERVICE_TEST,
            "main_url": f"http://{name}",
            "login_callback_url": f"http://{name}/callback",
            "unregister_url": f"http://{name}/unregister",
            "secret_key": f"{name}__",
            "cooltime": 0,
            **kwargs,
        },
    )


class FixtureUserSet(object):
    def __init__(self):
        self.admin = ensure_user("admin", ("Admin", "Admin"), "admin@sparcs.org", is_staff=True)
        self.basic = ensure_user(
            "user", ("User", "User"), "user@domain.com",
            gender="*F", birthday=datetime.date(2000, 8, 1),
        )
        self.test = ensure_user("test", ("Test", "Test"), "test@domain.com", test_only=False, test_enabled=True)
        self.test_only = ensure_user(
            "test_only", ("Test", "Only"), "test-only@domain.com",
            test_only=True, test_enabled=True,
        )
        self.sparcs = ensure_user("sparcs", ("SPARCS", "SPARCS"), "jungnoh@sparcs.org", sparcs_id="jungnoh")
        self.email_unauthed = ensure_user("email_unauthed", ("No", "email"), "email@domain.com", email_authed=False)
        self.kaist = ensure_user(
            "kaist", ("KAIST", "user"), "jungnoh@kaist.ac.kr",
            kaist_id="jungnoh", kaist_info=KAIST_USER_INFO, kaist_info_time=datetime.datetime(2018, 10, 29, 12, 1, 0),
            birthday=datetime.date(2000, 9, 1),
        )


class FixtureServiceSet(object):
    def __init__(self, admin: User):
        self.test = ensure_service("test", "Test Service", admin, secret_key="SECRET__", scope="TEST")
        self.sparcs = ensure_service("sparcs", "SPARCS Service", admin, secret_key="SPARCS__", scope="SPARCS")
        self.public = ensure_service("public", "Public Service", admin, secret_key="PUBLIC__", scope="PUBLIC")
