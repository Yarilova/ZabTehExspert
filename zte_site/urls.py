from django.conf import settings
from django.views.static import serve
from django.contrib import admin
from django.urls import include, path, re_path
urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]
0
handler404 = "main.views.custom_404"

