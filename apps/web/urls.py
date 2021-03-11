from django.urls import path
from rest_framework import routers

from apps.web.views.notice import NoticeViewSet
from apps.web.views.profile import ProfileView

router = routers.SimpleRouter()
router.register(r'notice',  NoticeViewSet)


urlpatterns = [
    *router.urls,
    path('profile/', ProfileView.as_view()),
]
