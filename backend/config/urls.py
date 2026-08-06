from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path


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


urlpatterns = [
    path("", root_view),
    path("api/v1/", include("workflow.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
