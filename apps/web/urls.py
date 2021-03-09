from rest_framework import routers

from apps.web.views.notice import NoticeViewSet

router = routers.SimpleRouter()
router.register(r'notice',  NoticeViewSet)


urlpatterns = [
    *router.urls
]
