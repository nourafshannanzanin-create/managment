from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as static_serve


def root_view(_request):
    return JsonResponse(
        {
            "ok": True,
            "service": "carnomand-api",
            "api": "/api/v1/",
            "message": "این سرور فقط API است. فرانت‌اند را روی Vite (معمولاً http://127.0.0.1:5173) باز کنید.",
        },
        json_dumps_params={"ensure_ascii": False},
    )


def _media_url_prefix() -> str:
    media = str(getattr(settings, "MEDIA_URL", "/uploads/") or "/uploads/").strip() or "/uploads/"
    if not media.startswith("/"):
        media = f"/{media}"
    return media.rstrip("/") + "/"


media_prefix = _media_url_prefix()
# Always expose uploaded profiles/files (Django's static() helper only works when DEBUG=True).
media_patterns = [
    re_path(
        rf"^{media_prefix.lstrip('/')}(?P<path>.*)$",
        static_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

urlpatterns = [
    path("", root_view),
    path("api/v1/", include("workflow.urls")),
    *media_patterns,
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
