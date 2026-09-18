from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse({
        "status": "ok",
        "message": "BloodLink API is running"
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),

    path("accounts/", include("accounts.urls")),
    path("donors/", include("donors.urls")),
    path("requests/", include("blood_requests.urls")),
    path("matching/", include("matching.urls")),
    path("notifications/", include("notifications.urls")),

    path("", home, name="home"),
]